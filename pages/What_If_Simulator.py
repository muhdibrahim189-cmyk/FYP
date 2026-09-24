"""
Page 2 – What-If Simulator
Interactive sliders to explore emission reduction scenarios + AI chatbot.
"""
import plotly.graph_objects as go
import streamlit as st

from utils.ai_helper import chat_response, get_whatif_recommendation
from utils.analytics import scope_totals
from utils.carbon_calculator import KG_PER_TONNE, carbon_tax, kg_to_tonnes, share_pct
from utils.charts import AMBER, BLUE, GREEN, GRID_AXIS, HEADING, RED, apply_layout
from utils.config import GEMINI_MODEL_LABEL
from utils.simulation import SCOPE1_LEVERS, SCOPE2_LEVERS, Lever, describe_changes, simulate_emissions
from utils.ui import Page

CHAT_SUGGESTIONS = (
    "What is the most impactful lever to reduce Scope 2 emissions?",
    "How can we achieve a 30% carbon reduction in 2 years?",
    "What is the payback period for solar PV installation in Malaysia?",
    "Explain the difference between carbon credits and carbon tax.",
)


class WhatIfSimulator(Page):
    name = "What-If Simulator"
    icon = "🔬"
    nav_label = "What-If Simulator"
    header = (
        "🔬 What-If Emission Scenario Simulator",
        "Dynamic Decarbonization Modeling · Multi-lever Sensitivity Projections · Automated Tax Impact Calculation",
    )

    def render(self) -> None:
        df = self.load_emissions_or_stop("No data available. Please check the database.")

        # ── Levers ─────────────────────────────────────────────────────────────
        self.section_title("⚙️ Adjust Emission Levers")
        if df["source"].str.startswith("Scope ").any():
            self.muted_text("The emission data holds Scope 1 and Scope 2 totals only, so each slider "
                            "counts as an equal share of its scope (e.g. Diesel −100% cuts Scope 1 by 1/5).",
                            size="0.8rem")
        left_col, right_col = st.columns([1.1, 1], gap="large")
        with left_col:
            self.lever_group_header("🔥 Scope 1 — Direct Emissions", "#f59e0b")
            lever_values = self.lever_sliders(SCOPE1_LEVERS)
            self.lever_group_header("⚡ Scope 2 — Indirect Emissions", "#60a5fa", style="margin-top:0.8rem;")
            lever_values |= self.lever_sliders(SCOPE2_LEVERS)

        # ── Simulation ─────────────────────────────────────────────────────────
        df_sim = df.copy()
        df_sim["co2e_kg_sim"] = simulate_emissions(df_sim, lever_values)
        self.baseline = scope_totals(df_sim)
        self.simulated = scope_totals(df_sim, value_column="co2e_kg_sim")
        self.reduction_kg = self.baseline.total_kg - self.simulated.total_kg
        self.reduction_pct = share_pct(self.reduction_kg, self.baseline.total_kg)
        self.tax_saved_myr = carbon_tax(self.reduction_kg)

        with right_col:
            self.render_results(df_sim)
        self.render_comparison(df_sim)
        self.render_scenario_analysis(describe_changes(lever_values))
        self.render_chatbot()

    @staticmethod
    def lever_group_header(title: str, color: str, style: str = "") -> None:
        st.markdown(f"""
        <div class='sim-card' style='{style}'>
          <div style='color:{color};font-size:0.78rem;font-weight:600;letter-spacing:0.06em;text-transform:uppercase;'>
            {title}
          </div>
        </div>""", unsafe_allow_html=True)

    @staticmethod
    def lever_sliders(levers: tuple[Lever, ...]) -> dict[str, int]:
        return {
            lever.key: st.slider(lever.label, 0, lever.max_value, 0, key=lever.key, help=lever.help)
            for lever in levers
        }

    @staticmethod
    def result_card(label: str, value: str, sub: str, color: str) -> None:
        st.markdown(f"""
        <div class='ct-card' style='margin-bottom:0.4rem;padding:0.9rem 1.2rem;'>
          <div style='display:flex;justify-content:space-between;align-items:center;'>
            <div>
              <div style='color:var(--ct-muted);font-size:0.72rem;font-weight:600;text-transform:uppercase;letter-spacing:0.06em;'>{label}</div>
              <div style='color:{color};font-size:1.35rem;font-weight:700;margin-top:0.15rem;font-family:Outfit,sans-serif;'>{value}</div>
            </div>
            <div style='color:var(--ct-muted);font-size:0.75rem;text-align:right;'>{sub}</div>
          </div>
        </div>""", unsafe_allow_html=True)

    def render_results(self, df_sim) -> None:
        baseline, simulated, reduction_kg = self.baseline, self.simulated, self.reduction_kg
        self.section_title("📊 Simulation Results")
        arrow = "▼" if reduction_kg > 0 else ("▲" if reduction_kg < 0 else "—")
        arrow_color = GREEN if reduction_kg > 0 else RED
        results = (
            ("Simulated Total CO₂e", f"{kg_to_tonnes(simulated.total_kg):,.1f} t",
             f"Baseline: {kg_to_tonnes(baseline.total_kg):,.1f} t", HEADING),
            ("Emission Reduction", f"{arrow} {self.reduction_pct:.1f}%",
             f"{kg_to_tonnes(abs(reduction_kg)):,.1f} tonnes saved", arrow_color),
            ("New Tax Liability", f"MYR {carbon_tax(simulated.total_kg):,.0f}",
             f"Saving MYR {self.tax_saved_myr:,.0f}", BLUE),
            ("Scope 1 Simulated", f"{kg_to_tonnes(simulated.scope1_kg):,.1f} t",
             f"Down from {kg_to_tonnes(baseline.scope1_kg):,.1f} t", AMBER),
            ("Scope 2 Simulated", f"{kg_to_tonnes(simulated.scope2_kg):,.1f} t",
             f"Down from {kg_to_tonnes(baseline.scope2_kg):,.1f} t", BLUE),
        )
        for result in results:
            self.result_card(*result)

        by_source = df_sim.groupby("source")[["co2e_kg", "co2e_kg_sim"]].sum().reset_index()
        by_source["reduction"] = by_source["co2e_kg"] - by_source["co2e_kg_sim"]
        by_source = by_source[by_source["reduction"] != 0].sort_values("reduction", ascending=False)
        if not by_source.empty:
            fig_src = go.Figure(go.Bar(
                x=by_source["source"],
                y=by_source["reduction"] / KG_PER_TONNE,
                marker_color=[GREEN if v > 0 else RED for v in by_source["reduction"]],
            ))
            apply_layout(fig_src, 260,
                         title="Emission Reduction by Source (tonnes CO₂e)", yaxis_title="Reduction (tonnes)",
                         xaxis={**GRID_AXIS, "tickangle": -30})
            st.plotly_chart(fig_src, width="stretch")

    def render_comparison(self, df_sim) -> None:
        self.section_title("📈 Baseline vs Simulation Comparison")
        st.write(
            "Visualizes the timeline variance between baseline historical emissions and the simulated reduction scenario over all recorded monthly periods."
        )
        monthly = df_sim.groupby("month")[["co2e_kg", "co2e_kg_sim"]].sum() / KG_PER_TONNE
        fig_comp = go.Figure()
        fig_comp.add_trace(go.Scatter(
            x=monthly.index, y=monthly["co2e_kg"],
            name="Baseline", line=dict(color="#94a3b8", width=2.5, dash="dash"),
            fill="tozeroy", fillcolor="rgba(148,163,184,0.06)",
            mode="lines+markers", marker=dict(size=5),
        ))
        fig_comp.add_trace(go.Scatter(
            x=monthly.index, y=monthly["co2e_kg_sim"],
            name="Simulation", line=dict(color=BLUE, width=2.5),
            fill="tozeroy", fillcolor="rgba(37,99,235,0.07)",
            mode="lines+markers", marker=dict(size=5),
        ))
        apply_layout(fig_comp, 350,
                     title="Monthly CO₂e: Baseline vs Simulated Scenario (tonnes)", yaxis_title="Tonnes CO₂e")
        st.plotly_chart(fig_comp, width="stretch")
        self.observation("Notice how Scope 2 levers (Renewable Energy Share and Efficiency Gains) produce compound reductions during peak operational months.")

    # ── AI scenario analysis ───────────────────────────────────────────────────
    def render_scenario_analysis(self, changes_applied: list[str]) -> None:
        baseline, simulated = self.baseline, self.simulated
        scenario_text = (
            f"Applied changes: {', '.join(changes_applied) if changes_applied else 'No changes (baseline)'}\n"
            f"Baseline Total CO₂e: {kg_to_tonnes(baseline.total_kg):,.1f} tonnes\n"
            f"Simulated Total CO₂e: {kg_to_tonnes(simulated.total_kg):,.1f} tonnes\n"
            f"Reduction: {self.reduction_pct:.1f}% ({kg_to_tonnes(abs(self.reduction_kg)):,.1f} tonnes)\n"
            f"Carbon Tax Saving: MYR {self.tax_saved_myr:,.0f}\n"
            f"Scope 1 Reduction: {kg_to_tonnes(baseline.scope1_kg - simulated.scope1_kg):,.1f} tonnes\n"
            f"Scope 2 Reduction: {kg_to_tonnes(baseline.scope2_kg - simulated.scope2_kg):,.1f} tonnes"
        )

        self.section_title("🤖 AI Scenario Analysis")
        with st.container(border=True):
            self.ai_panel_header(f"✨ {GEMINI_MODEL_LABEL} · Scenario Analysis")
            if changes_applied:
                analyse = st.button("🔍 Analyse This Scenario", type="primary", key="analyse_scenario")
                self.cached_ai_text("sim_ai_cache", analyse, "🤖 Analysing your scenario…",
                                    lambda: get_whatif_recommendation(scenario_text))
            else:
                self.muted_text("👆 Adjust the sliders above to explore emission reduction scenarios, "
                                "then click Analyse to get AI recommendations.", size="0.88rem")

    # ── AI chatbot ─────────────────────────────────────────────────────────────
    @staticmethod
    def ask_chatbot(question: str) -> str:
        """Send a question with the running history and record both turns."""
        reply = chat_response(st.session_state.chat_gemini_history, question)
        st.session_state.chat_history += [
            {"role": "user", "content": question},
            {"role": "assistant", "content": reply},
        ]
        st.session_state.chat_gemini_history += [
            {"role": "user", "parts": [question]},
            {"role": "model", "parts": [reply]},
        ]
        return reply

    def render_chatbot(self) -> None:
        st.session_state.setdefault("chat_history", [])          # for display
        st.session_state.setdefault("chat_gemini_history", [])   # in Gemini's format

        self.section_title("💬 AI Sustainability Chatbot")
        with st.expander("🤖 Ask the AI Chatbot for Recommendations", expanded=True):
            self.muted_text("Ask about emission reduction strategies, efficiency benchmarks, carbon market options, "
                            "Malaysia regulations, or anything related to your sustainability journey.", size="0.82rem")

            self.muted_text("💡 Suggested questions:", size="0.75rem")
            suggestion_cols = st.columns(2)
            for i, suggestion in enumerate(CHAT_SUGGESTIONS):
                with suggestion_cols[i % 2]:
                    if st.button(f"↗ {suggestion}", key=f"sug_{i}", width="stretch"):
                        with st.spinner("🤖 Thinking…"):
                            self.ask_chatbot(suggestion)
                        st.rerun()

            st.markdown("<br>", unsafe_allow_html=True)
            for message in st.session_state.chat_history:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            user_input = st.chat_input("Ask the AI anything about carbon reduction…")
            if user_input:
                with st.chat_message("user"):
                    st.markdown(user_input)
                with st.chat_message("assistant"):
                    with st.spinner("🤖 Thinking…"):
                        st.markdown(self.ask_chatbot(user_input))

            if st.session_state.chat_history and st.button("🗑️ Clear Chat", key="clear_chat"):
                st.session_state.chat_history = []
                st.session_state.chat_gemini_history = []
                st.rerun()


WhatIfSimulator().run()
