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
CHATBOT_LOGO_PATH = PROJECT_ROOT / "assets" / "logo AI Chatbot.png"
CHATBOT_NAME = "SPK AI"


def _load_logo(path: Path) -> Image.Image:
    """A logo with its transparent margin trimmed, so CSS sizes the artwork itself."""
    logo = Image.open(path).convert("RGBA")
    return logo.crop(logo.getchannel("A").getbbox())


def _data_uri(image: Image.Image) -> str:
    """Inline copy for HTML/CSS, which can't reference a local file."""
    png = BytesIO()
    image.save(png, format="PNG")
    return "data:image/png;base64," + base64.b64encode(png.getvalue()).decode()


APP_PAGE_ICON = _load_logo(APP_LOGO_PATH)  # browser-tab icon
APP_LOGO_DATA_URI = _data_uri(APP_PAGE_ICON)
CHATBOT_AVATAR = _load_logo(CHATBOT_LOGO_PATH)  # assistant avatar in the chat panel
CHATBOT_LOGO_DATA_URI = _data_uri(CHATBOT_AVATAR)

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
    "Which company emits the most, and why?",
    "Is the STIRPAT forecast reliable?",
    "How can companies reduce Scope 2 emissions?",
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
