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
from sklearn.linear_model import LinearRegression

from utils.carbon_calculator import KG_PER_TONNE, yoy_change
from utils.config import (
    ANOMALY_MIN_HISTORY, ANOMALY_Z_THRESHOLD, FORECAST_MIN_POINTS, FORECAST_MONTHS,
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


def grouped_tonnes(df: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    """Sum ``co2e_kg`` per group and add a ``co2e_tonnes`` column."""
    grp = df.groupby(keys)["co2e_kg"].sum().reset_index()
    grp["co2e_tonnes"] = grp["co2e_kg"] / KG_PER_TONNE
    return grp


def monthly_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Return monthly totals by scope."""
    if df.empty:
        return pd.DataFrame()
    return grouped_tonnes(df, ["month", "scope"])


def source_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Return total CO₂e by source, largest first."""
    if df.empty:
        return pd.DataFrame()
    return grouped_tonnes(df, ["source", "scope"]).sort_values("co2e_kg", ascending=False)


def facility_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Return total CO₂e by facility and month."""
    if df.empty:
        return pd.DataFrame()
    return grouped_tonnes(df, ["facility", "month"])


# ── Filtering & search ─────────────────────────────────────────────────────────
def filter_emissions(
    df: pd.DataFrame,
    *,
    year: int | None = None,
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
    if year is not None:
        mask &= df["date"].dt.year == year
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


def forecast_monthly_totals(df: pd.DataFrame, periods: int = FORECAST_MONTHS) -> pd.DataFrame:
    """
    Fit a linear trend to monthly totals and project ``periods`` months ahead.
    Returns columns ``Month`` and ``Predicted`` (tonnes), or an empty frame
    when there is too little history.
    """
    monthly = monthly_summary(df)
    if monthly.empty:
        return pd.DataFrame()
    totals = monthly.groupby("month")["co2e_tonnes"].sum().reset_index()
    if len(totals) < FORECAST_MIN_POINTS:
        return pd.DataFrame()

    totals["idx"] = range(len(totals))
    model = LinearRegression().fit(totals[["idx"]], totals["co2e_tonnes"])
    future_idx = pd.DataFrame({"idx": range(len(totals), len(totals) + periods)})

    last_month = pd.Period(totals["month"].iloc[-1], freq="M")
    future_months = [(last_month + step).strftime("%Y-%m") for step in range(1, periods + 1)]
    return pd.DataFrame({"Month": future_months, "Predicted": model.predict(future_idx)})


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
