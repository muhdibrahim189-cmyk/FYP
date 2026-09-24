"""
carbon_calculator.py – Emission calculation helpers.
"""
import math

from data.emission_factors import ALL_FACTORS, CARBON_TAX_RATE_MYR


def calculate_emission(source: str, quantity: float) -> float:
    """
    Calculate CO₂e in kg given a source name and quantity in native unit.
    Returns kg CO₂e.
    """
    if source not in ALL_FACTORS:
        raise ValueError(f"Unknown emission source: {source}")
    if not math.isfinite(quantity) or quantity < 0:
        raise ValueError("Emission quantity must be a finite, non-negative number")
    return round(quantity * ALL_FACTORS[source]["factor"], 4)


def kg_to_tonnes(kg: float) -> float:
    return round(kg / 1000, 6)


def tonnes_to_kg(t: float) -> float:
    return round(t * 1000, 4)


def carbon_tax(kg_co2e: float, rate_myr: float = CARBON_TAX_RATE_MYR) -> float:
    """Return carbon tax liability in MYR for a given kg CO₂e value."""
    if not math.isfinite(kg_co2e) or kg_co2e < 0:
        raise ValueError("CO₂e must be a finite, non-negative number")
    if not math.isfinite(rate_myr) or rate_myr < 0:
        raise ValueError("Carbon tax rate must be a finite, non-negative number")
    return round(kg_to_tonnes(kg_co2e) * rate_myr, 2)


def emission_intensity_revenue(total_kg: float, revenue_myr: float) -> float:
    """tCO₂e per MYR 1M revenue."""
    if revenue_myr == 0:
        return 0.0
    return round(kg_to_tonnes(total_kg) / (revenue_myr / 1_000_000), 4)


def emission_intensity_employee(total_kg: float, employees: int) -> float:
    """tCO₂e per employee."""
    if employees == 0:
        return 0.0
    return round(kg_to_tonnes(total_kg) / employees, 4)


def yoy_change(current: float, previous: float) -> float:
    """Percentage year-over-year change."""
    if previous == 0:
        return 0.0
    return round((current - previous) / previous * 100, 2)
