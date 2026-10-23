"""Groq chat completions (OpenAI-compatible API) with an offline-friendly fallback."""

import logging
import os
import time

import requests

from data.emission_factors import CARBON_TAX_RATE_MYR, COMPANY_FULL_NAMES, PENINSULAR_GRID_FACTOR
from utils.config import (
    CHATBOT_NAME, GROQ_API_KEY_ENV, GROQ_API_URL, GROQ_MODEL_NAME, GROQ_RATE_LIMIT_MAX_WAIT_SECONDS,
    GROQ_TIMEOUT_SECONDS,
)

logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv(GROQ_API_KEY_ENV, "").strip()


def is_api_configured() -> bool:
    return bool(GROQ_API_KEY)


def _unavailable_message(feature: str) -> str:
    return (
        f"⚠️ {feature} is unavailable because the Groq API is not configured. "
        f"Set the `{GROQ_API_KEY_ENV}` environment variable to enable it."
    )


# ── System instruction shared across features ──────────────────────────────────
SYSTEM_CONTEXT = f"""
You are {CHATBOT_NAME}, the assistant inside Sistem Pemantauan Karbon (SPK), a Malaysian
government prototype that monitors Scope 1 & 2 GHG emissions of five oil and gas companies
(BP, Chevron, ConocoPhillips, Equinor, ExxonMobil), their carbon tax exposure and STIRPAT
forecasts. Users are government officers, not specialists.

Each question comes with "Page data": the page the user is on, their CURRENT FILTERS and the
exact figures that page shows for those filters. Treat it as what the user is looking at.

How to answer:
- Ground every claim about these companies in the Page data. Quote the actual numbers (Mt, %,
  months, companies). Simple arithmetic on them (differences, shares, % change) is fine; never
  invent figures. If the data needed is not there, say what is missing.
- Speak to the user's selection ("for the 2024–2025 Chevron data you selected…"). If the filters
  limit the answer (e.g. one year only, synthetic 2026 included), say so.
- Never just describe what a chart looks like (titles, colours, dashed lines). Analyse it.
- Match the length to the question:
  - Simple factual question: 1–3 sentences with the number.
  - "Explain", "insight", "what happened", "why", "analyse" questions: bullet points only, at
    most 6 bullets and 120 words in total, each bullet one short sentence with its number.
    Pick only the most important points; leave the rest for follow-up questions. Format:
    - **Key finding:** the headline, with numbers.
    - **What changed:** 1–2 bullets: the overall trend over time, the biggest rise or fall
      (when, by how much), the peak or low month.
    - **Why:** 1–2 bullets: the company or scope driving it (share, change); for forecasts, the
      main STIRPAT driver (elasticity: % change in emissions per 1% change in a driver).
    - **So what:** one implication or next step for a government officer.
    No paragraphs, no headings, no sub-bullets. Check that bullets do not contradict each other.
  - Longer only when the user asks for more detail.
- Flag uncertainty honestly: 2026 is synthetic (assumption-based), and forecasts depend on it.
- For general carbon-reduction questions (solar PV, energy efficiency, carbon markets), answer
  from general knowledge and mark any figure as approximate.
- For questions unrelated to emissions or sustainability, say briefly that you help with
  carbon emissions and the SPK dashboard.

Key facts:
- Company abbreviations: {"; ".join(f"{short} = {full}" for short, full in COMPANY_FULL_NAMES.items())}
- Malaysia carbon tax: MYR {CARBON_TAX_RATE_MYR:.0f} / tonne CO₂e (2026)
- Peninsular Malaysia grid factor: {PENINSULAR_GRID_FACTOR} kg CO₂e/kWh
- Scope 1 = direct emissions (fuel combustion, flaring, fugitives)
- Scope 2 = indirect emissions from purchased electricity/heat
- STIRPAT: ln I = ln α + a·ln P + b·ln A + c·ln T (P production, A revenue, T energy intensity);
  Scope 2 adds + δ·t, a company-specific yearly trend
- MAPE overstates Scope 2 error because Equinor's Scope 2 is tiny; WAPE weights errors by tonnes

SPK pages and charts (use these to explain what a user sees):
- Main Dashboard:
  - KPI cards: total, Scope 1 and Scope 2 emissions (Mt) for the filtered period; the total's
    change compares the later half of the selected months with the earlier half. A fourth card,
    Carbon Tax / Year, is the selection's carbon tax at the sidebar rate per year of selected
    months (total ÷ months × 12), with the period total underneath.
  - Monthly Trend & STIRPAT Forecast (Line Chart): monthly Scope 1, Scope 2 and total emissions
    for the selected years, with dashed STIRPAT forecast lines for Jan–Jun 2027 (shaded area).
  - STIRPAT model accuracy (Table): accuracy = 100% − WAPE, plus MAPE, R², RMSE and elasticities
    a, b, c. Models are fitted on reported 2021–2025 data only (trained on 2021–2024, tested on
    2025); synthetic 2026 only supplies the drivers the forecast continues from. Scope 2 adds a
    company-specific time trend for electricity sourcing (renewable purchases, grid mix).
  - Facility Heatmap & Trellis (Bar Chart & Heatmap): total emissions per company, and a
    company × month heatmap where darker cells mean higher emissions.
  - Carbon Tax Analysis (Bar & Line Chart): monthly carbon tax (bars) and cumulative tax (line) in MYR.
- What-If Simulator: sliders reduce emission levers; Simulation Results (KPI Cards & Bar Chart)
  and Baseline vs Simulation Comparison (Area Chart) show the effect; AI Scenario Analysis comments on it.
- Data Centre: every ledger entry (the workbook's reported totals plus data-entry submissions) in a
  filterable table with CSV export, and below it a Monthly Summary (Table): one row per company and
  month with Scope 1, Scope 2 and total (t CO₂e) and power consumption (MWh).
- Sustainability: data entry form with a live CO₂e estimate (users can undo their own entries),
  approval queue and audit log.
- Sidebar filters (year, company, scope) change what the dashboard charts show.
"""


def _complete(messages: list[dict[str, str]], feature: str) -> str:
    """Send ``messages`` after the system instruction; return the reply or a user-safe message."""
    if not is_api_configured():
        return _unavailable_message(feature)
    def post() -> requests.Response:
        return requests.post(
            GROQ_API_URL,
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            json={"model": GROQ_MODEL_NAME,
                  "messages": [{"role": "system", "content": SYSTEM_CONTEXT}, *messages]},
            timeout=GROQ_TIMEOUT_SECONDS,
        )

    try:
        response = post()
        if response.status_code == 429:  # per-minute token limit: wait as told, then retry once
            wait = float(response.headers.get("retry-after", GROQ_RATE_LIMIT_MAX_WAIT_SECONDS))
            time.sleep(min(wait, GROQ_RATE_LIMIT_MAX_WAIT_SECONDS))
            response = post()
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception:
        # Keep provider details out of the UI but record them for operators.
        logger.exception("Groq request failed for %s", feature)
        return f"⚠️ {feature} could not be generated right now. Please try again later."


def get_whatif_recommendation(scenario_text: str) -> str:
    """Generate a recommendation for a what-if scenario."""
    prompt = (
        f"A user is exploring this what-if emission reduction scenario:\n\n"
        f"{scenario_text}\n\n"
        f"In at most 150 words, give four short bullet points: is it realistic, the expected "
        f"carbon and cost savings, the first implementation step, and the main risk."
    )
    return _complete([{"role": "user", "content": prompt}], "AI scenario analysis")


# Repeated with every question: models follow rules next to the question more
# closely than the system instruction alone.
ANSWER_REMINDER = (
    "Answer rules: ground every company figure in the Page data and speak to the user's filters. "
    "Simple question: 1–3 sentences. Explanation or insight question: bullet points only "
    "(Key finding / What changed / Why / So what), at most 6 one-sentence bullets and 120 words. "
    "Do not present Scope 2 company trend terms as growth rates."
)


def chat_response(conversation_history: list, user_message: str, data_context: str = "") -> str:
    """
    Multi-turn chatbot (the floating chat on every page).
    conversation_history: earlier turns as {'role': 'user' | 'assistant', 'content': str}.
    data_context: current page figures, sent with this question only.
    """
    message = (f"Page data:\n{data_context}\n\nQuestion: {user_message}\n\n{ANSWER_REMINDER}"
               if data_context else user_message)
    return _complete([*conversation_history, {"role": "user", "content": message}], "The AI chatbot")
