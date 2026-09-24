"""Application configuration and shared constants."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATABASE_PATH = DATA_DIR / "emissions.db"
CARBON_EMISSION_DATA_PATH = PROJECT_ROOT / "Carbon_Emission_Data.xlsx"

APP_NAME = "Fiscal Green"
APP_PAGE_ICON = "🌿"

# ── Navigation ────────────────────────────────────────────────────────────────
PAGE_ROUTES = {
    "Main Dashboard": "pages/Main_Dashboard.py",
    "What-If Simulator": "pages/What_If_Simulator.py",
    "Data Centre": "pages/Data_Centre.py",
    "Sustainability": "pages/Sustainability.py",
}
# Default page of the router in app.py: where users land after signing in.
DEFAULT_PAGE = "Main Dashboard"
NAVIGATION_OPTIONS = tuple(PAGE_ROUTES)

# ── AI (Google Gemini) ────────────────────────────────────────────────────────
# Secrets come from the environment only; never hard-code the key.
GEMINI_API_KEY_ENV = "GEMINI_API_KEY"
GEMINI_MODEL_NAME = "gemini-2.5-flash"
GEMINI_MODEL_LABEL = "Gemini 2.5 Flash"

# ── Database ──────────────────────────────────────────────────────────────────
DB_TIMEOUT_SECONDS = 10
ACTIVITY_LOG_LIMIT = 200

# ── Anomaly detection ─────────────────────────────────────────────────────────
ANOMALY_MIN_HISTORY = 5       # records needed before a source can be scored
ANOMALY_Z_THRESHOLD = 2.5     # |z| above this routes a submission to approval

# ── Shared labels ─────────────────────────────────────────────────────────────
ALL_OPTION = "All"            # "no filter" choice in select boxes
STATUS_LABELS = {"approved": "✅ Approved", "pending": "⏳ Pending", "rejected": "❌ Rejected"}

# ── Page settings ─────────────────────────────────────────────────────────────
FORECAST_MONTHS = 6
FORECAST_MIN_POINTS = 4
DATA_TABLE_PAGE_SIZE = 25
ACTIVITY_LOG_DISPLAY_LIMIT = 100
RECENT_SUBMISSIONS_LIMIT = 10
