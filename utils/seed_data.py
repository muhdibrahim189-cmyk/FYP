"""
seed_data.py – Deterministic synthetic emission records for an empty database.

Generates 18 months of approved records per facility with a seasonal cycle,
a slight downward trend and random noise. The random-number call order is
significant: changing it changes the generated dataset.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta

import numpy as np

from data.emission_factors import ALL_FACTORS, COMPANIES

SEED = 42
SEED_START = datetime(2025, 1, 1)
SEED_MONTHS = 18
DAYS_PER_SEED_MONTH = 30
SEED_USERS = ["admin", "user", "manager"]
SEED_APPROVER = "manager"


@dataclass(frozen=True)
class ScopeProfile:
    scope: int
    base_quantities: dict[str, float]   # source -> typical monthly quantity
    seasonal_amplitude: float
    seasonal_phase_months: int
    monthly_trend: float                # fractional decline per month
    noise_std: float


SEED_PROFILES = (
    ScopeProfile(
        scope=1,
        base_quantities={"Stationary – Natural Gas": 100, "Mobile – Diesel": 1500,
                         "Mobile – Petrol": 600, "Stationary – LPG": 10},
        seasonal_amplitude=0.15, seasonal_phase_months=0, monthly_trend=0.004, noise_std=0.07,
    ),
    ScopeProfile(
        scope=2,
        base_quantities={"Electricity – Peninsular Malaysia (TNB)": 42000, "Electricity – Sabah (SESB)": 8000},
        seasonal_amplitude=0.20, seasonal_phase_months=3, monthly_trend=0.003, noise_std=0.06,
    ),
)

EMISSION_COLUMNS = (
    "date", "facility", "scope", "source", "unit", "quantity", "co2e_kg",
    "submitted_by", "submitted_at", "status", "approved_by", "approved_at", "notes", "is_anomaly",
)


def generate_seed_records() -> list[tuple]:
    """Return rows matching EMISSION_COLUMNS."""
    rng = np.random.default_rng(SEED)
    records = []
    for month_offset in range(SEED_MONTHS):
        month_date = SEED_START + timedelta(days=DAYS_PER_SEED_MONTH * month_offset)
        for facility in COMPANIES:
            for profile in SEED_PROFILES:
                for source, base_qty in profile.base_quantities.items():
                    records.append(
                        _seed_record(rng, profile, source, base_qty, facility, month_date, month_offset)
                    )
    return records


def _seed_record(rng, profile: ScopeProfile, source: str, base_qty: float,
                 facility: str, month_date: datetime, month_offset: int) -> tuple:
    seasonal = 1 + profile.seasonal_amplitude * np.sin(
        2 * np.pi * (month_offset + profile.seasonal_phase_months) / 12
    )
    trend = 1 - profile.monthly_trend * month_offset
    noise = rng.normal(1, profile.noise_std)
    qty = round(max(0, base_qty * seasonal * trend * noise), 2)
    co2e = round(qty * ALL_FACTORS[source]["factor"], 2)
    activity_date = (month_date + timedelta(days=int(rng.integers(0, 5)))).strftime("%Y-%m-%d")
    submitted_at = (month_date + timedelta(days=int(rng.integers(5, 10)))).strftime("%Y-%m-%d %H:%M:%S")
    return (
        activity_date, facility, profile.scope, source,
        ALL_FACTORS[source]["unit"], qty, co2e,
        str(rng.choice(SEED_USERS)), submitted_at, "approved",
        SEED_APPROVER, submitted_at, None, 0,
    )
