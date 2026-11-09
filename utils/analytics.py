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

from data.emission_factors import ENERGY_SCOPE
from utils.carbon_calculator import KG_PER_MT, KG_PER_TONNE, share_pct, yoy_change
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
    submitted_by: Iterable[str] = (),
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
    for column, selected in (("scope", scopes), ("source", sources), ("facility", facilities),
                             ("submitted_by", submitted_by)):
        selected = list(selected)
        if selected:
            mask &= df[column].isin(selected)
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
def period_over_period_change(df: pd.DataFrame, value_column: str = "co2e_kg") -> float:
    """
    Split the covered months into an earlier and a later half and return the
    percentage change in ``value_column`` (total CO₂e by default) between them.
    """
    months = sorted(df["month"].unique())
    midpoint = len(months) // 2
    prior = df.loc[df["month"].isin(months[:midpoint]), value_column].sum()
    current = df.loc[df["month"].isin(months[midpoint:]), value_column].sum()
    return yoy_change(current, prior)


def monthly_ledger_summary(ledger: pd.DataFrame) -> pd.DataFrame:
    """
    Combine the per-source ledger entries into one row per company-month:
    Scope 1, Scope 2 and their total in tonnes CO₂e, plus power consumption.
    """
    if ledger.empty:
        return pd.DataFrame()
    keys = ["month", "facility"]
    tonnes = ledger.pivot_table(index=keys, columns="scope", values="co2e_kg", aggfunc="sum") / KG_PER_TONNE
    energy = ledger[ledger["scope"] == ENERGY_SCOPE].groupby(keys)["quantity"].sum() / 1000  # kWh → MWh
    summary = pd.DataFrame(index=tonnes.index.union(energy.index))
    summary["Scope 1 (t CO₂e)"] = tonnes.get(1)
    summary["Scope 2 (t CO₂e)"] = tonnes.get(2)
    summary = summary.fillna(0)
    summary["Total (t CO₂e)"] = summary.sum(axis=1)
    summary["Power Consumption (MWh)"] = energy.reindex(summary.index).fillna(0)
    return (summary.reset_index().rename(columns={"month": "Month", "facility": "Company"})
            .sort_values(["Month", "Company"], ascending=[False, True], ignore_index=True))


STIRPAT_DRIVERS = ("P", "A", "T")
# Targets that get a company-specific time trend (extended STIRPAT). Scope 2
# follows each company's electricity sourcing (renewable purchases, grid mix;
# Stachelscheid & Dutzi, 2025), which P, A and T do not capture.
STIRPAT_TREND_TARGETS = frozenset({"S2"})


@dataclass(frozen=True)
class StirpatResult:
    test: pd.DataFrame       # Month, Actual, Predicted – held-out months, selected companies
    forecast: pd.DataFrame   # Month, Predicted – the months after the data, selected companies
    train_end: str           # last training month (YYYY-MM)
    train_r2: float
    test_r2: float
    test_mape_pct: float
    test_wape_pct: float     # Σ|actual − predicted| / Σ actual; robust to tiny company totals
    test_rmse: float
    coefficients: dict[str, float]  # elasticities of I to P, A, T
    trend_pct_per_year: dict[str, float]  # company → yearly % change from the trend term (trend targets only)


def _stirpat_design(panel: pd.DataFrame, companies: list[str], trend_origin: pd.Timestamp | None = None) -> pd.DataFrame:
    """
    ln P, ln A, ln T plus one dummy per company (company-specific ln α) and,
    when ``trend_origin`` is given, one time trend per company (years since it).
    """
    company = pd.Categorical(panel["company"], categories=companies)
    dummies = pd.get_dummies(company, drop_first=True, dtype=float)
    dummies.index = panel.index
    columns = [np.log(panel[list(STIRPAT_DRIVERS)]), dummies]
    if trend_origin is not None:
        years = (panel["date"] - trend_origin).dt.days / 365.25
        trends = pd.get_dummies(company, dtype=float).mul(years.to_numpy(), axis=0)
        trends.index = panel.index
        columns.append(trends.add_prefix("trend_"))
    return pd.concat(columns, axis=1)


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
    Targets in STIRPAT_TREND_TARGETS use the extended form (York et al., 2003)
    with a company-specific trend δ_company·t, t in years.
    Only reported months fit the model: the first STIRPAT_TRAIN_SHARE of them
    train it and the rest test it (chronological split, so the test months are
    truly unseen). Synthetic months only supply their drivers as a scenario
    path. The model is then refitted on every reported month and projects
    ``periods`` months past the last month of the panel, each future driver
    growing at its own same-month year-on-year rate.
    Totals are summed over ``companies``. None when there is too little data.
    """
    if panel.empty or periods > 12:
        return None
    panel = panel.sort_values(["company", "date"]).reset_index(drop=True)
    all_companies = sorted(panel["company"].unique())
    reported = panel[~panel["synthetic"]]
    months = sorted(reported["date"].unique())
    if len(months) < 24 + 2:  # two years of history to project drivers year-on-year
        return None
    cut = months[int(len(months) * STIRPAT_TRAIN_SHARE)]
    train, test = reported[reported["date"] < cut], reported[reported["date"] >= cut]
    origin = pd.Timestamp(months[0]) if target in STIRPAT_TREND_TARGETS else None

    def design(frame: pd.DataFrame) -> pd.DataFrame:
        return _stirpat_design(frame, all_companies, origin)

    def fit(frame: pd.DataFrame) -> Ridge:
        return Ridge(alpha=STIRPAT_RIDGE_ALPHA).fit(design(frame), np.log(frame[target]))

    model = fit(train)
    train_pred = np.exp(model.predict(design(train)))
    test = test.assign(pred=np.exp(model.predict(design(test))))

    # Future drivers: ln X(m) = 2·ln X(m − 12) − ln X(m − 24), i.e. last year's
    # value grown by its own year-on-year change (keeps the seasonal pattern).
    logs = np.log(panel.set_index(["company", "date"])[list(STIRPAT_DRIVERS)])
    future_rows = []
    for step in range(1, periods + 1):
        month = panel["date"].max() + pd.DateOffset(months=step)
        year_ago = logs.xs(month - pd.DateOffset(years=1), level="date")
        two_years_ago = logs.xs(month - pd.DateOffset(years=2), level="date")
        future_rows.append(np.exp(2 * year_ago - two_years_ago).assign(date=month))
    future = pd.concat(future_rows).reset_index()

    final = fit(reported)
    future["pred"] = np.exp(final.predict(design(future)))

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
        test_wape_pct=float((test[target] - test["pred"]).abs().sum() / test[target].sum() * 100),
        test_rmse=float(np.sqrt(mean_squared_error(test[target], test["pred"]))),
        coefficients=dict(zip(STIRPAT_DRIVERS, map(float, final.coef_[:len(STIRPAT_DRIVERS)]))),
        trend_pct_per_year={name.removeprefix("trend_"): float(np.expm1(coef) * 100)
                            for name, coef in zip(final.feature_names_in_, final.coef_)
                            if name.startswith("trend_")},
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
    # The model is fitted on every company; totals cover only the companies in ``df``.
    companies = [c for c in df["facility"].unique() if not panel.empty and c in set(panel["company"])]
    if companies:
        for target, label in (("S1", "Scope 1"), ("S2", "Scope 2"), ("I", "Total")):
            result = stirpat_forecast(panel, companies, target=target)
            if result is not None:
                months = result.forecast["Month"]
                lines.append(
                    f"STIRPAT {label} forecast {months.iloc[0]} to {months.iloc[-1]}: "
                    f"{result.forecast['Predicted'].sum():.2f} Mt; test R² {result.test_r2:.3f}, "
                    f"WAPE {result.test_wape_pct:.1f}%, MAPE {result.test_mape_pct:.1f}%"
                )
    lines.append("Note: 2026 figures are synthetic projections, not reported data.")
    return "\n".join(lines)


def _pct(current: float, previous: float) -> str:
    return f"{yoy_change(current, previous):+.1f}%" if previous else "n/a"


def dashboard_context(df: pd.DataFrame, filters: dict[str, object], change_pct: float,
                      forecasts: dict[str, "StirpatResult"], tax_rate_myr: float) -> str:
    """
    Plain-text brief of exactly what the Main Dashboard shows for the user's
    current filters, so the AI chatbot can analyse it instead of answering in
    general terms. ``df`` is the filtered emission records (co2e_kg).
    """
    if df.empty:
        return "Main Dashboard: no data for the current filters."
    mt = df.assign(mt=df["co2e_kg"] / KG_PER_MT, year=df["date"].dt.year)
    lines = ["PAGE: Main Dashboard",
             "CURRENT FILTERS: " + "; ".join(f"{k}: {v}" for k, v in filters.items())]

    totals = mt.pivot_table(index="year", columns="scope", values="mt", aggfunc="sum").fillna(0)
    totals["total"] = totals.sum(axis=1)
    total = float(totals["total"].sum())
    scope_parts = ", ".join(f"Scope {c} {totals[c].sum():,.2f} Mt = {share_pct(totals[c].sum(), total):.1f}%"
                            for c in (1, 2) if c in totals)
    lines.append(f"KPI CARDS: total {total:,.2f} Mt ({scope_parts}); change {change_pct:+.1f}% "
                 "(later half of the selected months vs the earlier half)")

    yearly = []
    for year, row in totals.iterrows():
        prev = totals["total"].get(year - 1)
        parts = ", ".join(f"S{c} {row[c]:.2f}" for c in (1, 2) if c in totals)
        yearly.append(f"{year}: {parts}, total {row['total']:.2f}"
                      + (f" ({_pct(row['total'], prev)} vs {year - 1})" if prev is not None else ""))
    lines.append("BY YEAR (Mt): " + "; ".join(yearly))

    by_company = mt.pivot_table(index="facility", columns="year", values="mt", aggfunc="sum").fillna(0)
    years = list(by_company.columns)
    company_lines = []
    for company, row in by_company.sum(axis=1).sort_values(ascending=False).items():
        trend = (f", {years[0]}→{years[-1]} {_pct(by_company.loc[company, years[-1]], by_company.loc[company, years[0]])}"
                 if len(years) > 1 else "")
        company_lines.append(f"{company} {row:.2f} ({share_pct(row, total):.1f}%{trend})")
    lines.append("BY COMPANY (Mt, share of selection): " + "; ".join(company_lines))
    lines.append("BY COMPANY AND YEAR (Mt): " + "; ".join(
        f"{company}: " + ", ".join(f"{year} {value:.2f}" for year, value in row.items())
        for company, row in by_company.iterrows()))

    monthly = mt.groupby("month")["mt"].sum()
    lines.append(f"MONTHLY (line chart): {len(monthly)} months {monthly.index[0]}–{monthly.index[-1]}, "
                 f"average {monthly.mean():.2f} Mt; highest {monthly.idxmax()} ({monthly.max():.2f}); "
                 f"lowest {monthly.idxmin()} ({monthly.min():.2f}); last 12 months: "
                 + ", ".join(f"{m} {v:.2f}" for m, v in monthly.tail(12).items()))
    by_calendar_month = monthly.groupby(monthly.index.str[5:]).mean()
    high, low = (date(2000, int(mm), 1).strftime("%B") for mm in (by_calendar_month.idxmax(), by_calendar_month.idxmin()))
    lines.append(f"SEASONALITY (average by calendar month): highest {high}, lowest {low}")

    by_scope = mt.pivot_table(index="month", columns="scope", values="mt", aggfunc="sum")
    history = {"Scope 1": by_scope.get(1), "Scope 2": by_scope.get(2), "Total (Scope 1 + 2)": monthly}
    for label, result in forecasts.items():
        fc = result.forecast
        months = fc["Month"].tolist()
        text = (f"STIRPAT {label} FORECAST {months[0]}–{months[-1]}: "
                + ", ".join(f"{m} {v:.2f}" for m, v in zip(months, fc["Predicted"]))
                + f"; sum {fc['Predicted'].sum():.2f} Mt")
        past, year_before = history.get(label), [f"{int(m[:4]) - 1}{m[4:]}" for m in months]
        if past is not None and all(m in past.index for m in year_before):
            text += f" ({_pct(fc['Predicted'].sum(), past[year_before].sum())} vs the same months a year earlier)"
        text += (f"; test accuracy (2025, all five companies) {100 - result.test_wape_pct:.1f}% "
                 f"(WAPE {result.test_wape_pct:.1f}%, "
                 f"MAPE {result.test_mape_pct:.1f}%), test R² {result.test_r2:.3f}; elasticities "
                 + ", ".join(f"{k} {v:.2f}" for k, v in result.coefficients.items()))
        selected = set(df["facility"])
        if result.trend_pct_per_year:
            text += ("; company trend terms %/yr (model correction terms that offset the elasticities, "
                     "NOT forecast growth rates; only BP's matches a real fall) " + ", ".join(
                f"{c} {v:+.1f}" for c, v in result.trend_pct_per_year.items() if c in selected))
        lines.append(text)

    tax = df["co2e_kg"].sum() / KG_PER_TONNE * tax_rate_myr
    lines.append(f"CARBON TAX at MYR {tax_rate_myr:.0f}/t: total MYR {tax:,.0f} over all {len(monthly)} "
                 f"selected months (not per year), average MYR {tax / len(monthly) * 12:,.0f} per year "
                 f"and MYR {tax / len(monthly):,.0f} per month")
    lines.append("DATA NOTES: 2021–2025 monthly values are disaggregated from annual company reports; 2026 is "
                 "synthetic (assumption-based), not reported, and is not used to fit STIRPAT. Scope 2 is "
                 "location-based; Chevron's is market-based and rounded to whole Mt, so its year-to-year changes "
                 "are coarse. STIRPAT is fitted on all five companies; forecasts sum the selected companies. In the "
                 "Scope 2 model the company trends and the elasticities overlap and partly offset each other (e.g. "
                 "a positive trend can offset a driver-based decline), so they explain the forecast together but "
                 "should not be read one by one as real growth rates or sensitivities; only BP's trend clearly "
                 "matches its reported fall (2.4 to 0.7 Mt, 2021–2025). Scope 1 and total elasticities are "
                 "interpretable.")
    return "\n".join(lines)


# ── Anomaly detection ──────────────────────────────────────────────────────────
def detect_anomaly(history: Sequence[float], value: float, source: str,
                   unit: str = "kg CO₂e") -> tuple[bool, str]:
    """
    Flag ``value`` when it lies more than ANOMALY_Z_THRESHOLD standard
    deviations from the historical mean for the same source.
    Returns (is_anomaly, human-readable reason).
    """
    if len(history) < ANOMALY_MIN_HISTORY:
        return False, ""
    mean = float(np.mean(history))
    std = float(np.std(history))
    if std == 0:
        return False, ""
    z = abs(value - mean) / std
    if z <= ANOMALY_Z_THRESHOLD:
        return False, ""
    direction = "high" if value > mean else "low"
    reason = (
        f"Value {value:,.1f} {unit} is {z:.1f}σ {direction} of historical mean "
        f"({mean:,.1f} ± {std:,.1f} {unit}) for '{source}'. Requires approval."
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
