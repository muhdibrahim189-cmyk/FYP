"""
analytics.py – Pure pandas/numpy logic shared by the pages.

Nothing here touches Streamlit or the database, so every function can be
unit-tested with an in-memory DataFrame.
"""
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import date

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_percentage_error, mean_squared_error, r2_score

from utils.carbon_calculator import KG_PER_MT, yoy_change
from utils.config import (
    ANOMALY_MIN_HISTORY, ANOMALY_Z_THRESHOLD, FORECAST_MONTHS, STIRPAT_RIDGE_ALPHA, STIRPAT_TRAIN_SHARE,
)

# Leading characters that make spreadsheet apps evaluate a cell as a formula.
_CSV_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


# ── Totals ─────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class ScopeTotals:
    total_kg: float
    scope1_kg: float
    scope2_kg: float


def scope_totals(df: pd.DataFrame, value_column: str = "co2e_kg") -> ScopeTotals:
    return ScopeTotals(
        total_kg=float(df[value_column].sum()),
        scope1_kg=float(df.loc[df["scope"] == 1, value_column].sum()),
        scope2_kg=float(df.loc[df["scope"] == 2, value_column].sum()),
    )


def grouped_mt(df: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    """Sum ``co2e_kg`` per group and add a ``co2e_mt`` column (million tonnes)."""
    grp = df.groupby(keys)["co2e_kg"].sum().reset_index()
    grp["co2e_mt"] = grp["co2e_kg"] / KG_PER_MT
    return grp


def monthly_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Return monthly totals by scope."""
    if df.empty:
        return pd.DataFrame()
    return grouped_mt(df, ["month", "scope"])


def facility_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Return total CO₂e by facility and month."""
    if df.empty:
        return pd.DataFrame()
    return grouped_mt(df, ["facility", "month"])


# ── Filtering & search ─────────────────────────────────────────────────────────
def filter_emissions(
    df: pd.DataFrame,
    *,
    years: Iterable[int] = (),
    date_range: tuple[date, date] | None = None,
    scopes: Iterable[int] = (),
    sources: Iterable[str] = (),
    facilities: Iterable[str] = (),
    submitted_by: str | None = None,
) -> pd.DataFrame:
    """
    Apply the optional filters used across pages.
    An empty selection means "do not filter on this dimension".
    """
    mask = pd.Series(True, index=df.index)
    years = list(years)
    if years:
        mask &= df["date"].dt.year.isin(years)
    if date_range is not None:
        start, end = date_range
        day = df["date"].dt.date
        mask &= (day >= start) & (day <= end)
    for column, selected in (("scope", scopes), ("source", sources), ("facility", facilities)):
        selected = list(selected)
        if selected:
            mask &= df[column].isin(selected)
    if submitted_by is not None:
        mask &= df["submitted_by"] == submitted_by
    return df[mask]


def search_rows(df: pd.DataFrame, term: str) -> pd.DataFrame:
    """Case-insensitive literal substring search across every column."""
    term = term.strip()
    if not term or df.empty:
        return df
    as_text = df.astype(str)
    mask = np.zeros(len(df), dtype=bool)
    for column in as_text.columns:
        mask |= as_text[column].str.contains(term, case=False, regex=False).to_numpy()
    return df[mask]


# ── Trends & forecasting ───────────────────────────────────────────────────────
def period_over_period_change(df: pd.DataFrame) -> float:
    """
    Split the covered months into an earlier and a later half and return the
    percentage change in total CO₂e between them.
    """
    months = sorted(df["month"].unique())
    midpoint = len(months) // 2
    prior_kg = df.loc[df["month"].isin(months[:midpoint]), "co2e_kg"].sum()
    current_kg = df.loc[df["month"].isin(months[midpoint:]), "co2e_kg"].sum()
    return yoy_change(current_kg, prior_kg)


STIRPAT_DRIVERS = ("P", "A", "T")


@dataclass(frozen=True)
class StirpatResult:
    test: pd.DataFrame       # Month, Actual, Predicted – held-out months, selected companies
    forecast: pd.DataFrame   # Month, Predicted – the months after the data, selected companies
    train_end: str           # last training month (YYYY-MM)
    train_r2: float
    test_r2: float
    test_mape_pct: float
    test_rmse: float
    coefficients: dict[str, float]  # elasticities of I to P, A, T


def _stirpat_design(panel: pd.DataFrame, companies: list[str]) -> pd.DataFrame:
    """ln P, ln A, ln T plus one dummy per company (company-specific ln α)."""
    dummies = pd.get_dummies(pd.Categorical(panel["company"], categories=companies),
                             drop_first=True, dtype=float)
    dummies.index = panel.index
    return pd.concat([np.log(panel[list(STIRPAT_DRIVERS)]), dummies], axis=1)


def _monthly_totals(frame: pd.DataFrame, companies: Iterable[str], column: str) -> pd.Series:
    picked = frame[frame["company"].isin(list(companies))]
    totals = picked.groupby("date")[column].sum()
    totals.index = totals.index.strftime("%Y-%m")
    return totals


def stirpat_forecast(panel: pd.DataFrame, companies: Iterable[str], target: str = "I",
                     periods: int = FORECAST_MONTHS) -> StirpatResult | None:
    """
    STIRPAT model (Dietz & Rosa, 1994) on the company-month panel, where I is
    the ``target`` column (e.g. Scope 1, Scope 2 or their total):

        ln I = ln α_company + a·ln P + b·ln A + c·ln T + ln e

    fitted by ridge regression for the collinear drivers (Kong et al., 2023).
    The first STIRPAT_TRAIN_SHARE of months train the model and the rest test
    it (chronological split, so the test months are truly unseen). The model
    is then refitted on every month and projects ``periods`` months ahead,
    each future driver growing at its own same-month year-on-year rate.
    Totals are summed over ``companies``. None when there is too little data.
    """
    if panel.empty or periods > 12:
        return None
    panel = panel.sort_values(["company", "date"]).reset_index(drop=True)
    all_companies = sorted(panel["company"].unique())
    months = sorted(panel["date"].unique())
    if len(months) < 24 + 2:  # two years of history to project drivers year-on-year
        return None
    cut = months[int(len(months) * STIRPAT_TRAIN_SHARE)]
    train, test = panel[panel["date"] < cut], panel[panel["date"] >= cut]

    def fit(frame: pd.DataFrame) -> Ridge:
        return Ridge(alpha=STIRPAT_RIDGE_ALPHA).fit(_stirpat_design(frame, all_companies), np.log(frame[target]))

    model = fit(train)
    train_pred = np.exp(model.predict(_stirpat_design(train, all_companies)))
    test = test.assign(pred=np.exp(model.predict(_stirpat_design(test, all_companies))))

    # Future drivers: ln X(m) = 2·ln X(m − 12) − ln X(m − 24), i.e. last year's
    # value grown by its own year-on-year change (keeps the seasonal pattern).
    logs = np.log(panel.set_index(["company", "date"])[list(STIRPAT_DRIVERS)])
    future_rows = []
    for step in range(1, periods + 1):
        month = months[-1] + pd.DateOffset(months=step)
        year_ago = logs.xs(month - pd.DateOffset(years=1), level="date")
        two_years_ago = logs.xs(month - pd.DateOffset(years=2), level="date")
        future_rows.append(np.exp(2 * year_ago - two_years_ago).assign(date=month))
    future = pd.concat(future_rows).reset_index()

    final = fit(panel)
    future["pred"] = np.exp(final.predict(_stirpat_design(future, all_companies)))

    actual = _monthly_totals(test, companies, target)
    predicted = _monthly_totals(test, companies, "pred")
    forecast = _monthly_totals(future, companies, "pred")
    return StirpatResult(
        test=pd.DataFrame({"Month": actual.index, "Actual": actual.values, "Predicted": predicted.values}),
        forecast=pd.DataFrame({"Month": forecast.index, "Predicted": forecast.values}),
        train_end=pd.Timestamp(months[months.index(cut) - 1]).strftime("%Y-%m"),
        train_r2=float(r2_score(train[target], train_pred)),
        test_r2=float(r2_score(test[target], test["pred"])),
        test_mape_pct=float(mean_absolute_percentage_error(test[target], test["pred"]) * 100),
        test_rmse=float(np.sqrt(mean_squared_error(test[target], test["pred"]))),
        coefficients=dict(zip(STIRPAT_DRIVERS, map(float, final.coef_[:len(STIRPAT_DRIVERS)]))),
    )


def emissions_snapshot(df: pd.DataFrame, panel: pd.DataFrame) -> str:
    """
    A compact plain-text summary of the dashboard figures (Mt CO₂e) for the
    AI chatbot, so its answers rest on this system's data.
    """
    if df.empty:
        return "No emission data is loaded."
    years = df.assign(year=df["date"].dt.year)
    by_year = years.pivot_table(index="year", columns="scope", values="co2e_kg", aggfunc="sum") / KG_PER_MT
    lines = ["Emissions by year (Mt CO₂e): " + "; ".join(
        f"{year}: S1 {row.get(1, 0):.2f}, S2 {row.get(2, 0):.2f}" for year, row in by_year.iterrows())]
    latest = int(years["year"].max())
    company = (years[years["year"] == latest].pivot_table(index="facility", columns="scope",
                                                          values="co2e_kg", aggfunc="sum") / KG_PER_MT)
    lines.append(f"By company in {latest} (Mt CO₂e): " + "; ".join(
        f"{name}: S1 {row.get(1, 0):.2f}, S2 {row.get(2, 0):.2f}" for name, row in company.iterrows()))
    if not panel.empty:
        companies = panel["company"].unique()
        for target, label in (("S1", "Scope 1"), ("S2", "Scope 2"), ("I", "Total")):
            result = stirpat_forecast(panel, companies, target=target)
            if result is not None:
                months = result.forecast["Month"]
                lines.append(
                    f"STIRPAT {label} forecast {months.iloc[0]} to {months.iloc[-1]}: "
                    f"{result.forecast['Predicted'].sum():.2f} Mt; test R² {result.test_r2:.3f}, "
                    f"MAPE {result.test_mape_pct:.1f}%"
                )
    lines.append("Note: 2026 figures are synthetic projections, not reported data.")
    return "\n".join(lines)


# ── Anomaly detection ──────────────────────────────────────────────────────────
def detect_anomaly(history_kg: Sequence[float], co2e_kg: float, source: str) -> tuple[bool, str]:
    """
    Flag ``co2e_kg`` when it lies more than ANOMALY_Z_THRESHOLD standard
    deviations from the historical mean for the same source.
    Returns (is_anomaly, human-readable reason).
    """
    if len(history_kg) < ANOMALY_MIN_HISTORY:
        return False, ""
    mean = float(np.mean(history_kg))
    std = float(np.std(history_kg))
    if std == 0:
        return False, ""
    z = abs(co2e_kg - mean) / std
    if z <= ANOMALY_Z_THRESHOLD:
        return False, ""
    direction = "high" if co2e_kg > mean else "low"
    reason = (
        f"Value {co2e_kg:.1f} kg CO₂e is {z:.1f}σ {direction} of historical mean "
        f"({mean:.1f} ± {std:.1f} kg CO₂e) for '{source}'. Requires manager approval."
    )
    return True, reason


# ── Export ─────────────────────────────────────────────────────────────────────
def to_safe_csv(df: pd.DataFrame) -> str:
    """
    Serialise to CSV, neutralising text cells that a spreadsheet would run as
    a formula (CSV injection). Numeric columns are left untouched.
    """
    safe = df.copy()
    for column in safe.columns:
        if safe[column].dtype == object or pd.api.types.is_string_dtype(safe[column]):
            safe[column] = safe[column].map(_neutralise_formula)
    return safe.to_csv(index=False)


def _neutralise_formula(value: object) -> object:
    if isinstance(value, str) and value.startswith(_CSV_FORMULA_PREFIXES):
        return "'" + value
    return value
