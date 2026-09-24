"""Google Gemini integration with an offline-friendly fallback."""

import logging
import os
from collections.abc import Callable
from importlib.util import find_spec

from data.emission_factors import CARBON_TAX_RATE_MYR, PENINSULAR_GRID_FACTOR
from utils.config import GEMINI_API_KEY_ENV, GEMINI_MODEL_NAME

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
        _model = genai.GenerativeModel(GEMINI_MODEL_NAME)
    return _model


def is_api_configured() -> bool:
    return _GENAI_AVAILABLE and bool(GEMINI_API_KEY)


def _unavailable_message(feature: str) -> str:
    return (
        f"⚠️ {feature} is unavailable because Gemini is not configured. "
        f"Set the `{GEMINI_API_KEY_ENV}` environment variable to enable it."
    )


# ── System prompt shared across features ───────────────────────────────────────
SYSTEM_CONTEXT = f"""
You are CarbonTrack AI, an expert sustainability analyst specialising in GHG accounting
(Scope 1 & 2 under the GHG Protocol), Malaysia's carbon regulatory landscape, and
industrial energy efficiency. Your role is to provide clear, actionable, plain-language
explanations that prevent "black-box confusion" (Teknologi Tenung) — meaning you always
explain WHY something happened, not just WHAT happened.

Key facts:
- Malaysia carbon tax: MYR {CARBON_TAX_RATE_MYR:.0f} / tonne CO₂e (2026)
- Peninsular Malaysia grid factor: {PENINSULAR_GRID_FACTOR} kg CO₂e/kWh
- Scope 1 = direct emissions (combustion, fleet, fugitives)
- Scope 2 = indirect from purchased electricity/heat

Always be concise, professional, and grounded in data provided.
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


def get_dashboard_insight(summary_text: str) -> str:
    """
    Generate a narrative AI insight for the main dashboard.
    summary_text: a JSON/text summary of the current emission data.
    """
    prompt = (
        f"{SYSTEM_CONTEXT}\n\n"
        f"Based on the following emission data summary, provide a 3-4 paragraph insight covering:\n"
        f"1. What the key trends mean and WHY they occurred\n"
        f"2. Which sources are driving the most emissions and why that matters\n"
        f"3. Any anomalies or concerning patterns\n"
        f"4. 2-3 specific, actionable next steps\n\n"
        f"Data:\n{summary_text}\n\n"
        f"Write in a clear, professional tone suitable for a sustainability report."
    )
    return _generate(prompt, "AI insights")


def get_whatif_recommendation(scenario_text: str) -> str:
    """Generate a recommendation for a what-if scenario."""
    prompt = (
        f"{SYSTEM_CONTEXT}\n\n"
        f"A user is exploring the following what-if emission reduction scenario:\n\n"
        f"{scenario_text}\n\n"
        f"Provide:\n"
        f"1. Assessment of whether this scenario is realistic and achievable\n"
        f"2. Expected carbon and cost savings\n"
        f"3. Implementation steps and typical timeline\n"
        f"4. Potential risks or trade-offs\n"
        f"Keep it concise and practical."
    )
    return _generate(prompt, "AI scenario analysis")


def chat_response(conversation_history: list, user_message: str) -> str:
    """
    Multi-turn chatbot for the What-If Simulator.
    conversation_history: list of dicts with 'role' and 'parts' keys.
    """
    def send(model) -> str:
        chat = model.start_chat(history=conversation_history)
        return chat.send_message(f"{SYSTEM_CONTEXT}\n\nUser question: {user_message}").text

    return _ask("The AI chatbot", send)
