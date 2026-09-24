"""Google Gemini integration with an offline-friendly fallback."""

import os
from importlib.util import find_spec

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

_GENAI_AVAILABLE = find_spec("google.generativeai") is not None
genai = None

_model = None


def _get_model():
    global _model
    if _model is None and _GENAI_AVAILABLE:
        import google.generativeai as genai_module

        genai = genai_module
        genai.configure(api_key=GEMINI_API_KEY)
        _model = genai.GenerativeModel("gemini-1.5-flash")
    return _model


def is_api_configured() -> bool:
    return _GENAI_AVAILABLE and bool(GEMINI_API_KEY)


def _unavailable_message(feature: str) -> str:
    return (
        f"⚠️ {feature} is unavailable because Gemini is not configured. "
        "Set the `GEMINI_API_KEY` environment variable to enable it."
    )


# ── System prompt shared across features ───────────────────────────────────────
SYSTEM_CONTEXT = """
You are CarbonTrack AI, an expert sustainability analyst specialising in GHG accounting
(Scope 1 & 2 under the GHG Protocol), Malaysia's carbon regulatory landscape, and
industrial energy efficiency. Your role is to provide clear, actionable, plain-language
explanations that prevent "black-box confusion" (Teknologi Tenung) — meaning you always
explain WHY something happened, not just WHAT happened.

Key facts:
- Malaysia carbon tax: MYR 35 / tonne CO₂e (2026)
- Peninsular Malaysia grid factor: 0.585 kg CO₂e/kWh
- Scope 1 = direct emissions (combustion, fleet, fugitives)
- Scope 2 = indirect from purchased electricity/heat

Always be concise, professional, and grounded in data provided.
"""


def get_dashboard_insight(summary_text: str) -> str:
    """
    Generate a narrative AI insight for the main dashboard.
    summary_text: a JSON/text summary of the current emission data.
    """
    if not is_api_configured():
        return _unavailable_message("AI insights")
    try:
        model = _get_model()
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
        response = model.generate_content(prompt)
        return response.text
    except Exception:
        return "⚠️ AI insights could not be generated right now. Please try again later."


def get_whatif_recommendation(scenario_text: str) -> str:
    """Generate a recommendation for a what-if scenario."""
    if not is_api_configured():
        return _unavailable_message("AI scenario analysis")
    try:
        model = _get_model()
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
        response = model.generate_content(prompt)
        return response.text
    except Exception:
        return "⚠️ AI scenario analysis could not be generated right now. Please try again later."


def chat_response(conversation_history: list, user_message: str) -> str:
    """
    Multi-turn chatbot for the What-If Simulator.
    conversation_history: list of dicts with 'role' and 'parts' keys.
    """
    if not is_api_configured():
        return _unavailable_message("The AI chatbot")
    try:
        model = _get_model()
        chat = model.start_chat(history=conversation_history)
        response = chat.send_message(
            f"{SYSTEM_CONTEXT}\n\nUser question: {user_message}"
        )
        return response.text
    except Exception:
        return "⚠️ The AI chatbot could not respond right now. Please try again later."
