"""
simulation.py – What-If scenario levers and the reduction model behind them.

Each lever is a percentage slider. ``reduction_fractions`` turns the chosen
lever values into a per-source reduction fraction which is applied to every
emission record of that source.
"""
from collections.abc import Mapping
from dataclasses import dataclass

import pandas as pd

from utils.data_manager import WORKBOOK_SCOPE_COLUMNS


@dataclass(frozen=True)
class Lever:
    key: str             # Streamlit widget key; also the lookup key for values
    label: str
    summary: str         # format string for the scenario description, gets {value}
    max_value: int = 100
    help: str | None = None


SCOPE1_LEVERS = (
    Lever("ng_red", "🔵 Natural Gas Reduction (%)", "Natural Gas -{value}%"),
    Lever("d_red", "🟤 Diesel Reduction (%)", "Diesel -{value}%"),
    Lever("p_red", "⚫ Petrol Reduction (%)", "Petrol -{value}%"),
    Lever("l_red", "🟡 LPG Reduction (%)", "LPG -{value}%"),
    Lever("ev_pct", "⚡ Fleet EV Adoption (%)", "Fleet EV Adoption {value}%",
          help="% of fleet vehicles replaced with EVs (zero direct Scope 1 emission)"),
)

SCOPE2_LEVERS = (
    Lever("e_red", "💡 Electricity Consumption Reduction (%)", "Electricity -{value}%"),
    Lever("re_pct", "☀️ Renewable Energy Share (%)", "Renewable Energy {value}%",
          help="% of electricity from renewables (zero Scope 2 emission factor)"),
    Lever("eff", "🏭 Overall Energy Efficiency Gain (%)", "Energy Efficiency +{value}%", max_value=50),
)

ALL_LEVERS = SCOPE1_LEVERS + SCOPE2_LEVERS


# Emission source -> the levers acting on it (see data/emission_factors.py).
# Sources not listed (coal, residual fuel oil) have no lever.
_ELECTRICITY = ("e_red", "re_pct", "eff")
LEVER_SOURCES: dict[str, tuple[str, ...]] = {
    # Scope 1
    "Stationary – Natural Gas": ("ng_red",),
    "Mobile – CNG": ("ng_red",),
    "Stationary – Diesel": ("d_red",),
    "Stationary – Diesel B5": ("d_red",),
    "Stationary – Diesel B7": ("d_red",),
    "Stationary – Diesel B10": ("d_red",),
    "Stationary – Diesel B20": ("d_red",),
    "Stationary – Biodiesel B100": ("d_red",),
    "Mobile – Diesel": ("d_red",),
    "Mobile – Diesel B7": ("d_red",),
    "Mobile – Diesel B10": ("d_red",),
    "Mobile – Diesel B20": ("d_red",),
    "Mobile – Biodiesel B100": ("d_red",),
    "Stationary – Petrol": ("p_red",),
    "Mobile – Petrol": ("p_red", "ev_pct"),
    "Stationary – LPG": ("l_red",),
    "Mobile – LPG": ("l_red",),
    # Scope 2
    "Electricity – Peninsular Malaysia (TNB)": _ELECTRICITY,
    "Electricity – Sabah (SESB)": _ELECTRICITY,
    "Electricity – Sarawak (Sarawak Energy)": _ELECTRICITY,
    "Electricity – Kulim Hi-Tech Park (NUR)": _ELECTRICITY,
    # Workbook rows ("Scope 1", "Scope 2") are scope totals
    # with no fuel breakdown, so every lever of that scope is an equal share.
    # ponytail: equal-share assumption; weight by a real fuel mix if the workbook gains one.
    **{
        source: tuple(lever.key for lever in (SCOPE1_LEVERS if scope == 1 else SCOPE2_LEVERS))
        for scope, _, source in WORKBOOK_SCOPE_COLUMNS
    },
}


def reduction_fractions(values: Mapping[str, int]) -> dict[str, float]:
    """
    Map each emission source to the fraction (0–1) by which it is reduced.

    Where several levers act on one source their percentages are averaged,
    e.g. mobile petrol is the mean of "Petrol Reduction" and "Fleet EV Adoption".
    """
    return {
        source: sum(values.get(key, 0) for key in keys) / (100 * len(keys))
        for source, keys in LEVER_SOURCES.items()
    }


def simulate_emissions(df: pd.DataFrame, values: Mapping[str, int]) -> pd.Series:
    """Return simulated kg CO₂e per record. Unmapped sources are unchanged."""
    fractions = df["source"].map(reduction_fractions(values)).fillna(0.0).clip(upper=1.0)
    return df["co2e_kg"] * (1 - fractions)


def describe_changes(values: Mapping[str, int]) -> list[str]:
    """Human-readable list of the non-zero levers, in slider order."""
    return [
        lever.summary.format(value=values[lever.key])
        for lever in ALL_LEVERS
        if values.get(lever.key)
    ]
