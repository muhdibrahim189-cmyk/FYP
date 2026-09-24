"""
Page 2 – What-If Simulator
Interactive sliders to explore emission reduction scenarios + AI chatbot.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from utils.auth import require_login, render_sidebar_user
from utils.data_manager import init_db, load_emissions, source_summary
from utils.carbon_calculator import kg_to_tonnes, carbon_tax
from utils.ai_helper import get_whatif_recommendation, chat_response, is_api_configured
from data.emission_factors import ALL_FACTORS
from utils.ui import render_base_styles, render_navigation, render_sidebar_brand

st.set_page_config(page_title="What-If Simulator · Fiscal Green", page_icon="🔬", layout="wide")
init_db()
require_login()

# CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap');

* { font-family: 'Inter', sans-serif; }

.reportview-container, [data-testid="stAppViewContainer"] {
    background: #f0f2f6;
    min-height: 100vh;
}
.main .block-container {
    padding-top: 1.8rem;
    padding-bottom: 2rem;
}

h1 {
    color: #1E3A8A !important;
    font-family: 'Outfit', 'Inter', sans-serif !important;
    font-weight: 700 !important;
}
h2 {
    color: #2563EB !important;
    font-family: 'Outfit', 'Inter', sans-serif !important;
    font-weight: 600 !important;
}
h3 {
    color: #1e293b !important;
    font-family: 'Outfit', 'Inter', sans-serif !important;
    font-weight: 600 !important;
}

[data-testid="stSidebar"] {
    background: #ffffff !important;
    border-right: 1px solid #e2e8f0 !important;
}
[data-testid="stSidebarNav"] { display: none !important; }
[data-testid="stSidebar"] * { color: #1e293b !important; }
[data-testid="stSidebarNav"] a {
    border-radius: 8px;
    margin: 3px 0;
    color: #334155 !important;
    transition: all 0.15s ease;
}
[data-testid="stSidebarNav"] a:hover {
    background: #eff6ff !important;
    color: #2563EB !important;
}
[data-testid="stSidebarNav"] a[aria-selected="true"] {
    background: #dbeafe !important;
    border-left: 3px solid #2563EB;
    color: #1e40af !important;
    font-weight: 600 !important;
}

.stAlert, [data-testid="stAlert"] {
    border-radius: 8px !important;
}

.ct-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1.1rem 1.3rem;
    transition: all 0.2s ease;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.ct-card:hover {
    border-color: #93c5fd;
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(37,99,235,0.08);
}
.ct-section-title {
    font-size: 1.15rem;
    font-weight: 700;
    color: #1E3A8A;
    border-left: 4px solid #2563EB;
    padding-left: 0.7rem;
    margin: 1.3rem 0 0.7rem;
    font-family: 'Outfit', sans-serif;
}
.sim-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 1rem 1.2rem;
    margin: 0.4rem 0;
    box-shadow: 0 1px 2px rgba(0,0,0,0.02);
}
.ai-insight-box {
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    border-radius: 12px;
    padding: 1.3rem 1.5rem;
    margin-top: 1rem;
}
.ai-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #dbeafe;
    border: 1px solid #93c5fd;
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 0.75rem;
    font-weight: 600;
    color: #1e40af;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.7rem;
}
[data-testid="stTabs"] [role="tab"] {
    color: #64748b;
    font-weight: 500;
    font-family: 'Outfit', sans-serif;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    color: #1E3A8A !important;
    border-bottom-color: #2563EB !important;
    font-weight: 700;
}
hr { border-color: #e2e8f0 !important; }
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 3px; }
.stButton > button[kind="primary"] {
    background: #2563EB !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    color: white !important;
    box-shadow: 0 2px 4px rgba(37,99,235,0.2) !important;
}
.stButton > button[kind="primary"]:hover {
    background: #1d4ed8 !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(37,99,235,0.3) !important;
}
.stButton > button[kind="secondary"] {
    background: #ffffff !important;
    border: 1px solid #cbd5e1 !important;
    border-radius: 8px !important;
    color: #334155 !important;
}
.stChatMessage {
    background: #ffffff !important;
    border-radius: 12px !important;
    border: 1px solid #e2e8f0 !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.03);
}
</style>
""", unsafe_allow_html=True)
render_base_styles()

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    render_sidebar_brand()
    st.markdown("### 🧭 Navigation")
    render_navigation("🔬 What-If Simulator")
    render_sidebar_user()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style='margin-bottom:1.2rem;'>
  <h1 style='color:#1E3A8A;font-size:2rem;font-weight:800;margin:0;font-family:Outfit,sans-serif;'>🔬 What-If Emission Scenario Simulator</h1>
  <p style='color:#64748b;font-size:0.9rem;margin:0.2rem 0 0;'>
    Dynamic Decarbonization Modeling · Multi-lever Sensitivity Projections · Automated Tax Impact Calculation
  </p>
</div>
""", unsafe_allow_html=True)

# ── Load baseline ─────────────────────────────────────────────────────────────
df = load_emissions()
if df.empty:
    st.warning("No data available. Please check the database.")
    st.stop()

# Baseline: last 12 months average monthly totals per source
df_sorted = df.sort_values("date")
baseline_src = df.groupby("source")["co2e_kg"].mean().to_dict()   # avg per record
baseline_qty = df.groupby("source")["quantity"].mean().to_dict()

# Aggregate totals for the full dataset
total_baseline_kg = df["co2e_kg"].sum()
s1_baseline = df[df["scope"] == 1]["co2e_kg"].sum()
s2_baseline = df[df["scope"] == 2]["co2e_kg"].sum()

# ── Simulator UI ───────────────────────────────────────────────────────────────
st.markdown("<div class='ct-section-title'>⚙️ Adjust Emission Levers</div>", unsafe_allow_html=True)

left_col, right_col = st.columns([1.1, 1], gap="large")

with left_col:
    st.markdown("""
    <div class='sim-card'>
      <div style='color:#f59e0b;font-size:0.78rem;font-weight:600;letter-spacing:0.06em;text-transform:uppercase;'>
        🔥 Scope 1 — Direct Emissions
      </div>
    </div>""", unsafe_allow_html=True)

    nat_gas_red    = st.slider("🔵 Natural Gas Reduction (%)",   0, 100, 0, key="ng_red")
    diesel_red     = st.slider("🟤 Diesel Reduction (%)",        0, 100, 0, key="d_red")
    petrol_red     = st.slider("⚫ Petrol Reduction (%)",        0, 100, 0, key="p_red")
    lpg_red        = st.slider("🟡 LPG Reduction (%)",           0, 100, 0, key="l_red")
    fleet_ev_pct   = st.slider("⚡ Fleet EV Adoption (%)",       0, 100, 0, key="ev_pct",
                                help="% of fleet vehicles replaced with EVs (zero direct Scope 1 emission)")
    refrigerant_red = st.slider("❄️ Refrigerant Leak Reduction (%)", 0, 100, 0, key="ref_red")

    st.markdown("""
    <div class='sim-card' style='margin-top:0.8rem;'>
      <div style='color:#60a5fa;font-size:0.78rem;font-weight:600;letter-spacing:0.06em;text-transform:uppercase;'>
        ⚡ Scope 2 — Indirect Emissions
      </div>
    </div>""", unsafe_allow_html=True)

    elec_red       = st.slider("💡 Electricity Consumption Reduction (%)", 0, 100, 0, key="e_red")
    renewable_pct  = st.slider("☀️ Renewable Energy Share (%)",            0, 100, 0, key="re_pct",
                                help="% of electricity from renewables (zero Scope 2 emission factor)")
    steam_red      = st.slider("💨 Steam/Heat Reduction (%)",              0, 100, 0, key="st_red")
    efficiency_gain = st.slider("🏭 Overall Energy Efficiency Gain (%)",   0, 50, 0, key="eff")

with right_col:
    # ── Simulate ──────────────────────────────────────────────────────────────
    scope1_factors_map = {
        "Natural Gas":  nat_gas_red / 100,
        "Diesel":       diesel_red  / 100,
        "Petrol":       (petrol_red + fleet_ev_pct) / 200,   # combine
        "LPG":          lpg_red    / 100,
        "Refrigerants (R410A)": refrigerant_red / 100,
        "Refrigerants (R134a)": refrigerant_red / 100,
        "Fuel Oil":     0.0,
        "Coal":         0.0,
    }
    scope2_factors_map = {
        "Electricity (Peninsular Malaysia)": (elec_red + renewable_pct + efficiency_gain) / 300,
        "Electricity (Sabah)":               (elec_red + renewable_pct + efficiency_gain) / 300,
        "Electricity (Sarawak)":             (elec_red + renewable_pct + efficiency_gain) / 300,
        "Steam / Heat":   steam_red / 100,
        "Chilled Water":  efficiency_gain / 100,
    }

    sim_rows = []
    for _, row in df.iterrows():
        source = row["source"]
        scope  = row["scope"]
        red_frac = 0.0
        if scope == 1:
            red_frac = scope1_factors_map.get(source, 0.0)
        else:
            red_frac = scope2_factors_map.get(source, 0.0)
        red_frac = min(red_frac, 1.0)
        new_co2e = row["co2e_kg"] * (1 - red_frac)
        sim_rows.append(new_co2e)

    df_sim = df.copy()
    df_sim["co2e_kg_sim"] = sim_rows

    sim_total_kg = df_sim["co2e_kg_sim"].sum()
    sim_s1 = df_sim[df_sim["scope"] == 1]["co2e_kg_sim"].sum()
    sim_s2 = df_sim[df_sim["scope"] == 2]["co2e_kg_sim"].sum()

    reduction_kg  = total_baseline_kg - sim_total_kg
    reduction_pct = (reduction_kg / total_baseline_kg * 100) if total_baseline_kg > 0 else 0
    tax_saved_myr = carbon_tax(reduction_kg)
    sim_tax_myr   = carbon_tax(sim_total_kg)

    # ── Summary Cards ─────────────────────────────────────────────────────────
    st.markdown("<div class='ct-section-title'>📊 Simulation Results</div>", unsafe_allow_html=True)

    arrow = "▼" if reduction_kg > 0 else ("▲" if reduction_kg < 0 else "—")
    arrow_color = "#16a34a" if reduction_kg > 0 else "#dc2626"

    results = [
        ("Simulated Total CO₂e", f"{kg_to_tonnes(sim_total_kg):,.1f} t",
         f"Baseline: {kg_to_tonnes(total_baseline_kg):,.1f} t", "#1E3A8A"),
        ("Emission Reduction", f"{arrow} {reduction_pct:.1f}%",
         f"{kg_to_tonnes(abs(reduction_kg)):,.1f} tonnes saved", arrow_color),
        ("New Tax Liability", f"MYR {sim_tax_myr:,.0f}",
         f"Saving MYR {tax_saved_myr:,.0f}", "#2563EB"),
        ("Scope 1 Simulated", f"{kg_to_tonnes(sim_s1):,.1f} t",
         f"Down from {kg_to_tonnes(s1_baseline):,.1f} t", "#d97706"),
        ("Scope 2 Simulated", f"{kg_to_tonnes(sim_s2):,.1f} t",
         f"Down from {kg_to_tonnes(s2_baseline):,.1f} t", "#2563EB"),
    ]
    for label, value, sub, color in results:
        st.markdown(f"""
        <div class='ct-card' style='margin-bottom:0.4rem;padding:0.9rem 1.2rem;'>
          <div style='display:flex;justify-content:space-between;align-items:center;'>
            <div>
              <div style='color:#64748b;font-size:0.72rem;font-weight:600;text-transform:uppercase;letter-spacing:0.06em;'>{label}</div>
              <div style='color:{color};font-size:1.35rem;font-weight:700;margin-top:0.15rem;font-family:Outfit,sans-serif;'>{value}</div>
            </div>
            <div style='color:#64748b;font-size:0.75rem;text-align:right;'>{sub}</div>
          </div>
        </div>""", unsafe_allow_html=True)

    # ── Waterfall Chart ────────────────────────────────────────────────────────
    PLOT_LAYOUT = dict(
        paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
        font=dict(family="Inter, sans-serif", color="#334155"),
        margin=dict(t=45, b=25, l=10, r=10),
    )

    src_sim = df_sim.groupby("source")[["co2e_kg", "co2e_kg_sim"]].sum().reset_index()
    src_sim["reduction"] = src_sim["co2e_kg"] - src_sim["co2e_kg_sim"]
    src_sim = src_sim[src_sim["reduction"] != 0].sort_values("reduction", ascending=False)

    if not src_sim.empty:
        fig_wf = go.Figure(go.Bar(
            x=src_sim["source"],
            y=src_sim["reduction"] / 1000,
            marker_color=["#16a34a" if v > 0 else "#dc2626" for v in src_sim["reduction"]],
        ))
        fig_wf.update_layout(
            **PLOT_LAYOUT,
            title="Emission Reduction by Source (tonnes CO₂e)",
            yaxis_title="Reduction (tonnes)",
            height=260,
            xaxis=dict(tickangle=-30, gridcolor="#f1f5f9"),
            yaxis=dict(gridcolor="#f1f5f9"),
        )
        st.plotly_chart(fig_wf, width="stretch")

# ── Comparison Chart ──────────────────────────────────────────────────────────
st.markdown("<div class='ct-section-title'>📈 Baseline vs Simulation Comparison</div>", unsafe_allow_html=True)
st.write(
    "Visualizes the timeline variance between baseline historical emissions and the simulated reduction scenario over all recorded monthly periods."
)

df_sim["month"] = df_sim["date"].dt.to_period("M").astype(str)
monthly_baseline = df_sim.groupby("month")["co2e_kg"].sum() / 1000
monthly_simulated = df_sim.groupby("month")["co2e_kg_sim"].sum() / 1000

fig_comp = go.Figure()
fig_comp.add_trace(go.Scatter(
    x=monthly_baseline.index, y=monthly_baseline.values,
    name="Baseline", line=dict(color="#94a3b8", width=2.5, dash="dash"),
    fill="tozeroy", fillcolor="rgba(148,163,184,0.06)",
    mode="lines+markers", marker=dict(size=5),
))
fig_comp.add_trace(go.Scatter(
    x=monthly_simulated.index, y=monthly_simulated.values,
    name="Simulation", line=dict(color="#2563EB", width=2.5),
    fill="tozeroy", fillcolor="rgba(37,99,235,0.07)",
    mode="lines+markers", marker=dict(size=5),
))
fig_comp.update_layout(
    **PLOT_LAYOUT,
    title="Monthly CO₂e: Baseline vs Simulated Scenario (tonnes)",
    yaxis_title="Tonnes CO₂e",
    height=350,
    legend=dict(bgcolor="rgba(255,255,255,0.9)", bordercolor="#e2e8f0", borderwidth=1),
    xaxis=dict(gridcolor="#f1f5f9"),
    yaxis=dict(gridcolor="#f1f5f9"),
)
st.plotly_chart(fig_comp, width="stretch")
st.info("💡 **Observations:** Notice how Scope 2 levers (Renewable Energy Share and Efficiency Gains) produce compound reductions during peak operational months.")

# ── Scenario Summary Text ─────────────────────────────────────────────────────
changes_applied = []
if nat_gas_red:   changes_applied.append(f"Natural Gas -{nat_gas_red}%")
if diesel_red:    changes_applied.append(f"Diesel -{diesel_red}%")
if petrol_red:    changes_applied.append(f"Petrol -{petrol_red}%")
if fleet_ev_pct:  changes_applied.append(f"Fleet EV Adoption {fleet_ev_pct}%")
if lpg_red:       changes_applied.append(f"LPG -{lpg_red}%")
if refrigerant_red: changes_applied.append(f"Refrigerant Leaks -{refrigerant_red}%")
if elec_red:      changes_applied.append(f"Electricity -{elec_red}%")
if renewable_pct: changes_applied.append(f"Renewable Energy {renewable_pct}%")
if steam_red:     changes_applied.append(f"Steam/Heat -{steam_red}%")
if efficiency_gain: changes_applied.append(f"Energy Efficiency +{efficiency_gain}%")

scenario_text = (
    f"Applied changes: {', '.join(changes_applied) if changes_applied else 'No changes (baseline)'}\n"
    f"Baseline Total CO₂e: {kg_to_tonnes(total_baseline_kg):,.1f} tonnes\n"
    f"Simulated Total CO₂e: {kg_to_tonnes(sim_total_kg):,.1f} tonnes\n"
    f"Reduction: {reduction_pct:.1f}% ({kg_to_tonnes(abs(reduction_kg)):,.1f} tonnes)\n"
    f"Carbon Tax Saving: MYR {tax_saved_myr:,.0f}\n"
    f"Scope 1 Reduction: {kg_to_tonnes(s1_baseline - sim_s1):,.1f} tonnes\n"
    f"Scope 2 Reduction: {kg_to_tonnes(s2_baseline - sim_s2):,.1f} tonnes"
)

# ── AI Recommendation ─────────────────────────────────────────────────────────
st.markdown("<div class='ct-section-title'>🤖 AI Scenario Analysis</div>", unsafe_allow_html=True)
st.markdown("<div class='ai-insight-box'>", unsafe_allow_html=True)
st.markdown("<div class='ai-badge'>✨ Gemini 1.5 Flash · Scenario Analysis</div>", unsafe_allow_html=True)

if changes_applied:
    btn_ai = st.button("🔍 Analyse This Scenario", type="primary", key="analyse_scenario")
    if btn_ai or st.session_state.get("sim_ai_cache") is None:
        with st.spinner("🤖 Analysing your scenario…"):
            ai_text = get_whatif_recommendation(scenario_text)
            st.session_state["sim_ai_cache"] = ai_text
    if st.session_state.get("sim_ai_cache"):
        st.markdown(
            f"<div style='color:#d1fae5;font-size:0.88rem;line-height:1.8;'>"
            f"{st.session_state['sim_ai_cache']}</div>",
            unsafe_allow_html=True,
        )
else:
    st.markdown(
        "<div style='color:#6b7280;font-size:0.88rem;'>👆 Adjust the sliders above to explore "
        "emission reduction scenarios, then click Analyse to get AI recommendations.</div>",
        unsafe_allow_html=True,
    )
st.markdown("</div>", unsafe_allow_html=True)

# ── AI Chatbot ────────────────────────────────────────────────────────────────
st.markdown("<div class='ct-section-title'>💬 AI Sustainability Chatbot</div>", unsafe_allow_html=True)

with st.expander("🤖 Ask the AI Chatbot for Recommendations", expanded=True):
    st.markdown("""
    <div style='color:#9ca3af;font-size:0.82rem;margin-bottom:0.8rem;'>
    Ask about emission reduction strategies, efficiency benchmarks, carbon market options,
    Malaysia regulations, or anything related to your sustainability journey.
    </div>""", unsafe_allow_html=True)

    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "chat_gemini_history" not in st.session_state:
        st.session_state.chat_gemini_history = []

    # Suggested questions
    suggestions = [
        "What is the most impactful lever to reduce Scope 2 emissions?",
        "How can we achieve a 30% carbon reduction in 2 years?",
        "What is the payback period for solar PV installation in Malaysia?",
        "Explain the difference between carbon credits and carbon tax.",
    ]
    st.markdown("<div style='color:#6b7280;font-size:0.75rem;margin-bottom:0.4rem;'>💡 Suggested questions:</div>", unsafe_allow_html=True)
    sug_cols = st.columns(2)
    for i, sug in enumerate(suggestions):
        with sug_cols[i % 2]:
            if st.button(f"↗ {sug}", key=f"sug_{i}", width="stretch"):
                st.session_state.chat_history.append({"role": "user", "content": sug})
                with st.spinner("🤖 Thinking…"):
                    reply = chat_response(st.session_state.chat_gemini_history, sug)
                st.session_state.chat_history.append({"role": "assistant", "content": reply})
                st.session_state.chat_gemini_history.append({"role": "user", "parts": [sug]})
                st.session_state.chat_gemini_history.append({"role": "model", "parts": [reply]})
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Display messages
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Input
    user_input = st.chat_input("Ask the AI anything about carbon reduction…")
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)
        with st.chat_message("assistant"):
            with st.spinner("🤖 Thinking…"):
                reply = chat_response(st.session_state.chat_gemini_history, user_input)
            st.markdown(reply)
        st.session_state.chat_history.append({"role": "assistant", "content": reply})
        st.session_state.chat_gemini_history.append({"role": "user", "parts": [user_input]})
        st.session_state.chat_gemini_history.append({"role": "model", "parts": [reply]})

    if st.session_state.chat_history:
        if st.button("🗑️ Clear Chat", key="clear_chat"):
            st.session_state.chat_history = []
            st.session_state.chat_gemini_history = []
            st.rerun()
