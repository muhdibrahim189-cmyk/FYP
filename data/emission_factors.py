# ============================================================
#  Emission Factors & Carbon Tax Constants
#  Source: GHG Protocol / IPCC / Malaysia Grid Factor (ST)
# ============================================================

# --------------- SCOPE 1 - Direct Emissions ----------------
SCOPE1_FACTORS = {
    "Natural Gas":          {"unit": "m³",   "factor": 2.202,  "description": "Stationary combustion – natural gas"},
    "Diesel":               {"unit": "L",    "factor": 2.688,  "description": "Mobile / stationary combustion – diesel"},
    "Petrol":               {"unit": "L",    "factor": 2.289,  "description": "Mobile combustion – petrol"},
    "LPG":                  {"unit": "L",    "factor": 1.555,  "description": "Stationary combustion – liquefied petroleum gas"},
    "Coal":                 {"unit": "kg",   "factor": 2.419,  "description": "Stationary combustion – coal"},
    "Fuel Oil":             {"unit": "L",    "factor": 2.959,  "description": "Stationary combustion – fuel oil"},
    "Refrigerants (R410A)": {"unit": "kg",   "factor": 2088.0, "description": "Fugitive – R-410A refrigerant leakage"},
    "Refrigerants (R134a)": {"unit": "kg",   "factor": 1430.0, "description": "Fugitive – R-134a refrigerant leakage"},
}

# --------------- SCOPE 2 - Indirect Emissions ---------------
SCOPE2_FACTORS = {
    "Electricity (Peninsular Malaysia)": {"unit": "kWh", "factor": 0.585, "description": "Grid electricity – Peninsular MY"},
    "Electricity (Sabah)":               {"unit": "kWh", "factor": 0.781, "description": "Grid electricity – Sabah"},
    "Electricity (Sarawak)":             {"unit": "kWh", "factor": 0.291, "description": "Grid electricity – Sarawak"},
    "Steam / Heat":                      {"unit": "kWh", "factor": 0.062, "description": "Purchased steam or heat"},
    "Chilled Water":                     {"unit": "kWh", "factor": 0.057, "description": "District cooling – chilled water"},
}

# All factors combined for easy lookup
ALL_FACTORS = {**SCOPE1_FACTORS, **SCOPE2_FACTORS}

# Reference grid factor quoted throughout the UI and AI prompts
PENINSULAR_GRID_FACTOR = SCOPE2_FACTORS["Electricity (Peninsular Malaysia)"]["factor"]

# Scope mapping for convenience
SCOPE1_SOURCES = list(SCOPE1_FACTORS.keys())
SCOPE2_SOURCES = list(SCOPE2_FACTORS.keys())

# --------------- Carbon Tax / Price -------------------------
CARBON_TAX_RATE_MYR = 35.0          # MYR per tonne CO₂e  (Malaysia 2026)

# --------------- Facilities --------------------------------
FACILITIES = [
    "HQ Building",
    "Plant A – Ipoh",
    "Plant B – Penang",
    "Warehouse – Shah Alam",
    "Data Center – KL",
    "Fleet Operations",
]

# --------------- Intensity Denominator ---------------------
REVENUE_MYR = 45_000_000   # placeholder annual revenue for intensity calc
EMPLOYEES   = 850           # placeholder headcount
