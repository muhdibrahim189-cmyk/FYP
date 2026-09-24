"""Application configuration and shared constants."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATABASE_PATH = DATA_DIR / "emissions.db"
CARBON_EMISSION_DATA_PATH = PROJECT_ROOT / "Carbon_Emission_Data.xlsx"

APP_NAME = "Fiscal Green"
APP_PAGE_ICON = "🌿"

PAGE_ROUTES = {
    "📊 Main Dashboard": "pages/1_📊_Main_Dashboard.py",
    "🔬 What-If Simulator": "pages/2_🔬_What_If_Simulator.py",
    "🗄️ Data Centre": "pages/3_🗄️_Data_Centre.py",
    "♻️ Sustainability": "pages/4_♻️_Sustainability.py",
}
NAVIGATION_OPTIONS = ("Overview", *PAGE_ROUTES)

