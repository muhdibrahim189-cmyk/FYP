# ============================================================
#  Emission Factors & Carbon Tax Constants
#  Source: SEDG GHG Emissions Calculator User Guide (Capital Markets
#  Malaysia, July 2025), section 2.4 – GHG Protocol "Emission Factors
#  from Cross Sector Tools v2.0" (IPCC AR6 GWPs) for Scope 1 and
#  Suruhanjaya Tenaga "Grid Emission Factor in Malaysia" for Scope 2.
#
#  The guide's factors are already CO₂e (CO₂ + CH₄ + N₂O × GWP), so
#      CO₂e (kg) = activity data × factor
#  The guide lists them in metric tonnes (mt) CO₂e per unit; they are
#  stored here ×1000 as kg CO₂e per unit (e.g. 0.00295 mt/L = 2.95 kg/L).
#  Refrigerant (fugitive) and process emissions are excluded, as in the guide.
# ============================================================

# --------------- SCOPE 1 - Direct Emissions ----------------
SCOPE1_FACTORS = {
    # a. Stationary combustion (boilers, generators, furnaces)
    "Stationary – Natural Gas":        {"unit": "GJ", "factor": 56.2,  "description": "Stationary combustion – natural gas"},
    "Stationary – LPG":                {"unit": "GJ", "factor": 63.2,  "description": "Stationary combustion – liquefied petroleum gas"},
    "Stationary – Coal":               {"unit": "kg", "factor": 1.82,  "description": "Stationary combustion – coal"},
    "Stationary – Residual Fuel Oil":  {"unit": "L",  "factor": 3.04,  "description": "Stationary combustion – residual (bunker) fuel oil"},
    "Stationary – Petrol":             {"unit": "L",  "factor": 2.32,  "description": "Stationary combustion – gasoline (petrol)"},
    "Stationary – Diesel":             {"unit": "L",  "factor": 2.95,  "description": "Stationary combustion – diesel"},
    "Stationary – Diesel B5":          {"unit": "L",  "factor": 2.80,  "description": "Stationary combustion – diesel B5"},
    "Stationary – Diesel B7":          {"unit": "L",  "factor": 2.74,  "description": "Stationary combustion – diesel B7"},
    "Stationary – Diesel B10":         {"unit": "L",  "factor": 2.65,  "description": "Stationary combustion – diesel B10"},
    "Stationary – Diesel B20":         {"unit": "L",  "factor": 2.36,  "description": "Stationary combustion – diesel B20"},
    "Stationary – Biodiesel B100":     {"unit": "kg", "factor": 0.67,  "description": "Stationary combustion – biodiesel B100"},
    # b. Mobile combustion (company-owned vehicles)
    "Mobile – Petrol":                 {"unit": "L",  "factor": 2.288, "description": "Mobile combustion – gasoline (petrol)"},
    "Mobile – Diesel":                 {"unit": "L",  "factor": 2.909, "description": "Mobile combustion – diesel"},
    "Mobile – Diesel B7":              {"unit": "L",  "factor": 2.705, "description": "Mobile combustion – diesel B7"},
    "Mobile – Diesel B10":             {"unit": "L",  "factor": 2.618, "description": "Mobile combustion – diesel B10"},
    "Mobile – Diesel B20":             {"unit": "L",  "factor": 2.327, "description": "Mobile combustion – diesel B20"},
    "Mobile – Biodiesel B100":         {"unit": "L",  "factor": 0.001, "description": "Mobile combustion – biodiesel B100"},
    "Mobile – LPG":                    {"unit": "L",  "factor": 1.473, "description": "Mobile combustion – liquefied petroleum gas"},
    "Mobile – CNG":                    {"unit": "L",  "factor": 1.885, "description": "Mobile combustion – compressed natural gas"},
}

# --------------- SCOPE 2 - Indirect Emissions ---------------
# Grid Emission Factors (2022, used by the guide for 2022–2024):
# mt CO₂e/MWh equals kg CO₂e/kWh.
SCOPE2_FACTORS = {
    "Electricity – Peninsular Malaysia (TNB)":  {"unit": "kWh", "factor": 0.774, "description": "Purchased grid electricity – Tenaga Nasional Bhd"},
    "Electricity – Sabah (SESB)":               {"unit": "kWh", "factor": 0.525, "description": "Purchased grid electricity – Sabah Electricity Sdn Bhd"},
    "Electricity – Sarawak (Sarawak Energy)":   {"unit": "kWh", "factor": 0.199, "description": "Purchased grid electricity – Sarawak Energy Bhd"},
    "Electricity – Kulim Hi-Tech Park (NUR)":   {"unit": "kWh", "factor": 0.540, "description": "Purchased grid electricity – N.U.R Power Sdn Bhd"},
}

# All factors combined for easy lookup
ALL_FACTORS = {**SCOPE1_FACTORS, **SCOPE2_FACTORS}

# Reference grid factor quoted throughout the UI and AI prompts
PENINSULAR_GRID_FACTOR = SCOPE2_FACTORS["Electricity – Peninsular Malaysia (TNB)"]["factor"]

# Scope mapping for convenience
SCOPE1_SOURCES = list(SCOPE1_FACTORS.keys())
SCOPE2_SOURCES = list(SCOPE2_FACTORS.keys())

# --------------- Carbon Tax / Price -------------------------
CARBON_TAX_RATE_MYR = 35.0          # MYR per tonne CO₂e  (Malaysia 2026)

# --------------- Companies ---------------------------------
# The companies in Carbon_Emission_Data.xlsx (a test keeps the two in step).
COMPANIES = ["BP", "Chevron", "ConocoPhillips", "Equinor", "ExxonMobil"]

# --------------- Intensity Denominator ---------------------
REVENUE_MYR = 45_000_000   # placeholder annual revenue for intensity calc
EMPLOYEES   = 850           # placeholder headcount
