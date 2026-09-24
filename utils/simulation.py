"""
simulation.py – What-If scenario levers and the reduction model behind them.

Each lever is a percentage slider. ``reduction_fractions`` turns the chosen
lever values into a per-source reduction fraction which is applied to every
emission record of that source.
"""
from collections.abc import Mapping
from dataclasses import dataclass

import pandas as pd


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
    Lever("ref_red", "❄️ Refrigerant Leak Reduction (%)", "Refrigerant Leaks -{value}%"),
)

SCOPE2_LEVERS = (
    Lever("e_red", "💡 Electricity Consumption Reduction (%)", "Electricity -{value}%"),
    Lever("re_pct", "☀️ Renewable Energy Share (%)", "Renewable Energy {value}%",
          help="% of electricity from renewables (zero Scope 2 emission factor)"),
    Lever("st_red", "💨 Steam/Heat Reduction (%)", "Steam/Heat -{value}%"),
    Lever("eff", "🏭 Overall Energy Efficiency Gain (%)", "Energy Efficiency +{value}%", max_value=50),
)

ALL_LEVERS = SCOPE1_LEVERS + SCOPE2_LEVERS


def reduction_fractions(values: Mapping[str, int]) -> dict[str, float]:
    """
    Map each emission source to the fraction (0–1) by which it is reduced.

    Where several levers act on one source their percentages are averaged,
    e.g. petrol is the mean of "Petrol Reduction" and "Fleet EV Adoption".
    """
    def value(key: str) -> int:
        return values.get(key, 0)

    def pct(key: str) -> float:
        return value(key) / 100

    electricity = (value("e_red") + value("re_pct") + value("eff")) / 300
    refrigerant = pct("ref_red")
    return {
        # Scope 1
        "Natural Gas": pct("ng_red"),
        "Diesel": pct("d_red"),
        "Petrol": (value("p_red") + value("ev_pct")) / 200,
        "LPG": pct("l_red"),
        "Refrigerants (R410A)": refrigerant,
        "Refrigerants (R134a)": refrigerant,
        "Fuel Oil": 0.0,
        "Coal": 0.0,
        # Scope 2
        "Electricity (Peninsular Malaysia)": electricity,
        "Electricity (Sabah)": electricity,
        "Electricity (Sarawak)": electricity,
        "Steam / Heat": pct("st_red"),
        "Chilled Water": pct("eff"),
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
