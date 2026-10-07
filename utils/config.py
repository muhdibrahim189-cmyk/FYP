"""Application configuration and shared constants."""

import base64
from io import BytesIO
from pathlib import Path

from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATABASE_PATH = DATA_DIR / "emissions.db"
CARBON_EMISSION_DATA_PATH = PROJECT_ROOT / "Carbon_Emission_Data.xlsx"

APP_NAME = "Sistem Pemantauan Karbon"
APP_SHORT_NAME = "SPK"  # browser-tab titles
APP_LOGO_PATH = PROJECT_ROOT / "assets" / "Logo.png"


def _load_logo() -> Image.Image:
    """The logo with its transparent margin trimmed, so CSS sizes the emblem itself."""
    logo = Image.open(APP_LOGO_PATH).convert("RGBA")
    return logo.crop(logo.getchannel("A").getbbox())


_LOGO = _load_logo()
APP_PAGE_ICON = _LOGO  # browser-tab icon
# Inline copy for the HTML brand blocks (sidebar, login), which can't reference a local file.
_logo_png = BytesIO()
_LOGO.save(_logo_png, format="PNG")
APP_LOGO_DATA_URI = "data:image/png;base64," + base64.b64encode(_logo_png.getvalue()).decode()

# ── Navigation ────────────────────────────────────────────────────────────────
PAGE_ROUTES = {
    "Main Dashboard": "pages/Main_Dashboard.py",
    "What-If Simulator": "pages/What_If_Simulator.py",
    "Sustainability": "pages/Sustainability.py",
    "Data Centre": "pages/Data_Centre.py",
}
# Default page of the router in app.py: where users land after signing in.
DEFAULT_PAGE = "Main Dashboard"
NAVIGATION_OPTIONS = tuple(PAGE_ROUTES)

# ── AI (Google Gemini) ────────────────────────────────────────────────────────
# Secrets come from the environment only; never hard-code the key.
GEMINI_API_KEY_ENV = "GEMINI_API_KEY"
GEMINI_MODEL_NAME = "gemini-2.5-flash"
GEMINI_MODEL_LABEL = "Gemini 2.5 Flash"
CHAT_SUGGESTIONS = (
    "What is the most impactful lever to reduce Scope 2 emissions?",
    "How can we achieve a 30% carbon reduction in 2 years?",
    "What is the payback period for solar PV installation in Malaysia?",
    "Explain the difference between carbon credits and carbon tax.",
)

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
STIRPAT_TRAIN_SHARE = 0.8    # chronological 80/20 train/test split (Kong et al., 2023)
STIRPAT_RIDGE_ALPHA = 0.005  # ridge penalty chosen by Kong et al. (2023)
DATA_TABLE_PAGE_SIZE = 25
ACTIVITY_LOG_DISPLAY_LIMIT = 100
RECENT_SUBMISSIONS_LIMIT = 10
