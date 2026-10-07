"""Google Gemini integration with an offline-friendly fallback."""

import logging
import os
from collections.abc import Callable
from importlib.util import find_spec

from data.emission_factors import CARBON_TAX_RATE_MYR, PENINSULAR_GRID_FACTOR
from utils.config import CHATBOT_NAME, GEMINI_API_KEY_ENV, GEMINI_MODEL_NAME

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv(GEMINI_API_KEY_ENV, "").strip()
_GENAI_AVAILABLE = find_spec("google.generativeai") is not None

_model = None


def _get_model():
    """Create the Gemini client lazily so the app starts without the SDK."""
    global _model
    if _model is None:
        import google.generativeai as genai

        genai.configure(api_key=GEMINI_API_KEY)
        _model = genai.GenerativeModel(GEMINI_MODEL_NAME, system_instruction=SYSTEM_CONTEXT)
    return _model


def is_api_configured() -> bool:
    return _GENAI_AVAILABLE and bool(GEMINI_API_KEY)


def _unavailable_message(feature: str) -> str:
    return (
        f"⚠️ {feature} is unavailable because Gemini is not configured. "
        f"Set the `{GEMINI_API_KEY_ENV}` environment variable to enable it."
    )


# ── System instruction shared across features ──────────────────────────────────
SYSTEM_CONTEXT = f"""
You are {CHATBOT_NAME}, the assistant inside Sistem Pemantauan Karbon (SPK), a Malaysian
government prototype that monitors Scope 1 & 2 GHG emissions of five oil and gas companies
(BP, Chevron, ConocoPhillips, Equinor, ExxonMobil), their carbon tax exposure and STIRPAT
forecasts. Users are government officers, not specialists.

How to answer:
- Keep it short: at most 80 words, or 3 short bullet points. No headings, no long lists.
- Start with the direct answer. Then give one reason WHY, in plain language.
- Finish with one practical next step only when it helps.
- For figures about these companies, use only the dashboard data supplied with the question.
- For general carbon-reduction questions (e.g. solar PV, energy efficiency, carbon markets),
  answer from general knowledge and mark any figure as approximate. Never invent company data.
- Emissions in SPK are in million tonnes CO₂e (Mt).
- Give a longer answer only when the user explicitly asks for more detail.
- For questions unrelated to emissions or sustainability, say briefly that you help with
  carbon emissions and the SPK dashboard.

Key facts:
- Malaysia carbon tax: MYR {CARBON_TAX_RATE_MYR:.0f} / tonne CO₂e (2026)
- Peninsular Malaysia grid factor: {PENINSULAR_GRID_FACTOR} kg CO₂e/kWh
- Scope 1 = direct emissions (fuel combustion, flaring, fugitives)
- Scope 2 = indirect emissions from purchased electricity/heat
- STIRPAT: ln I = ln α + a·ln P + b·ln A + c·ln T (P production, A revenue, T energy intensity)

SPK pages and charts (use these to explain what a user sees):
- Main Dashboard:
  - KPI cards: total, Scope 1 and Scope 2 emissions (Mt) for the filtered period, with change vs prior period.
  - Monthly Trend & STIRPAT Forecast (Line Chart): monthly Scope 1, Scope 2 and total emissions
    Jan 2021 – Dec 2026, with dashed STIRPAT forecast lines for the next 6 months (shaded area).
  - STIRPAT model accuracy (Table): train/test R², MAPE, accuracy, RMSE and elasticities a, b, c
    for the Scope 1, Scope 2 and total models (trained on 80% of months, tested on the last 20%).
  - Facility Heatmap & Trellis (Bar Chart & Heatmap): total emissions per company, and a
    company × month heatmap where darker cells mean higher emissions.
  - Carbon Tax Analysis (Bar & Line Chart): monthly carbon tax (bars) and cumulative tax (line) in MYR.
- What-If Simulator: sliders reduce emission levers; Simulation Results (KPI Cards & Bar Chart)
  and Baseline vs Simulation Comparison (Area Chart) show the effect; AI Scenario Analysis comments on it.
- Data Centre: filterable records table and CSV export.
- Sustainability: data entry form with a live CO₂e estimate, approval queue and audit log.
- Sidebar filters (year, company, scope) change what the dashboard charts show.
"""


def _ask(feature: str, request: Callable[[object], str]) -> str:
    """Run ``request(model)``; return its text or a user-safe message."""
    if not is_api_configured():
        return _unavailable_message(feature)
    try:
        return request(_get_model())
    except Exception:
        # Keep provider details out of the UI but record them for operators.
        logger.exception("Gemini request failed for %s", feature)
        return f"⚠️ {feature} could not be generated right now. Please try again later."


def _generate(prompt: str, feature: str) -> str:
    return _ask(feature, lambda model: model.generate_content(prompt).text)


def get_whatif_recommendation(scenario_text: str) -> str:
    """Generate a recommendation for a what-if scenario."""
    prompt = (
        f"A user is exploring this what-if emission reduction scenario:\n\n"
        f"{scenario_text}\n\n"
        f"In at most 150 words, give four short bullet points: is it realistic, the expected "
        f"carbon and cost savings, the first implementation step, and the main risk."
    )
    return _generate(prompt, "AI scenario analysis")


def chat_response(conversation_history: list, user_message: str, data_context: str = "") -> str:
    """
    Multi-turn chatbot (the floating chat on every page).
    conversation_history: list of dicts with 'role' and 'parts' keys.
    data_context: current dashboard figures, sent with this question only.
    """
    def send(model) -> str:
        chat = model.start_chat(history=conversation_history)
        message = f"Dashboard data:\n{data_context}\n\nQuestion: {user_message}" if data_context else user_message
        return chat.send_message(message).text

    return _ask("The AI chatbot", send)
