"""
carbon_calculator.py – Emission calculation helpers.
"""
import math

from data.emission_factors import ALL_FACTORS, CARBON_TAX_RATE_MYR

KG_PER_TONNE = 1000


def _require_non_negative(value: float, message: str) -> None:
    if not math.isfinite(value) or value < 0:
        raise ValueError(message)


def calculate_emission(source: str, quantity: float) -> float:
    """
    Calculate CO₂e in kg given a source name and quantity in native unit.
    Returns kg CO₂e.
    """
    if source not in ALL_FACTORS:
        raise ValueError(f"Unknown emission source: {source}")
    _require_non_negative(quantity, "Emission quantity must be a finite, non-negative number")
    return round(quantity * ALL_FACTORS[source]["factor"], 4)


def kg_to_tonnes(kg: float) -> float:
    return round(kg / KG_PER_TONNE, 6)


def carbon_tax(kg_co2e: float, rate_myr: float = CARBON_TAX_RATE_MYR) -> float:
    """Return carbon tax liability in MYR for a given kg CO₂e value."""
    _require_non_negative(kg_co2e, "CO₂e must be a finite, non-negative number")
    _require_non_negative(rate_myr, "Carbon tax rate must be a finite, non-negative number")
    return round(kg_to_tonnes(kg_co2e) * rate_myr, 2)


def _ratio(numerator: float, denominator: float) -> float:
    """``numerator / denominator``, or 0 when the denominator is zero."""
    return numerator / denominator if denominator else 0.0


def emission_intensity_revenue(total_kg: float, revenue_myr: float) -> float:
    """tCO₂e per MYR 1M revenue."""
    return round(_ratio(kg_to_tonnes(total_kg), revenue_myr / 1_000_000), 4)


def emission_intensity_employee(total_kg: float, employees: int) -> float:
    """tCO₂e per employee."""
    return round(_ratio(kg_to_tonnes(total_kg), employees), 4)


def yoy_change(current: float, previous: float) -> float:
    """Percentage year-over-year change."""
    return round(_ratio(current - previous, previous) * 100, 2)


def share_pct(part: float, total: float) -> float:
    """Percentage share of ``part`` in ``total``; 0 when the total is zero."""
    return _ratio(part, total) * 100
