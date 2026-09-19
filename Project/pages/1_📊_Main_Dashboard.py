"""
Page 1 – Main Dashboard
Scope 1 & 2 KPI cards, trend charts, carbon tax, prediction, AI insight.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.linear_model import LinearRegression
from datetime import datetime

from utils.auth import require_login, render_sidebar_user
from utils.data_manager import init_db, load_emissions, monthly_summary, source_summary, facility_summary
from utils.carbon_calculator import carbon_tax, yoy_change, kg_to_tonnes, emission_intensity_revenue, emission_intensity_employee
from utils.ai_helper import get_dashboard_insight
from data.emission_factors import CARBON_TAX_RATE_MYR, REVENUE_MYR, EMPLOYEES

# ── Bootstrap ──────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Dashboard · CarbonTrack Pro", page_icon="📊", layout="wide")
init_db()
require_login()

# Re-inject global CSS
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

/* Headings */
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

/* Sidebar styling */
[data-testid="stSidebar"] {
    background: #ffffff !important;
    border-right: 1px solid #e2e8f0 !important;
}
[data-testid="stSidebar"] * { color: #1e293b !important; }

/* Sidebar nav links */
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

/* Lab3.py Alerts */
.stAlert, [data-testid="stAlert"] {
    border-radius: 8px !important;
}

/* Cards */
.ct-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1.1rem 1.2rem;
    transition: all 0.2s ease;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.ct-card:hover {
    border-color: #93c5fd;
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(37,99,235,0.08);
}
.ct-card-value {
    font-size: 1.85rem;
    font-weight: 700;
    color: #1E3A8A;
    margin: 0.2rem 0;
    line-height: 1.1;
    font-family: 'Outfit', sans-serif;
}
.ct-card-label {
    font-size: 0.72rem;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    font-weight: 600;
}
.ct-card-delta {
    font-size: 0.78rem;
    font-weight: 500;
    margin-top: 0.3rem;
}
.delta-up   { color: #dc2626; }
.delta-down { color: #16a34a; }
.delta-neu  { color: #64748b; }

.ct-section-title {
    font-size: 1.15rem;
    font-weight: 700;
    color: #1E3A8A;
    border-left: 4px solid #2563EB;
    padding-left: 0.7rem;
    margin: 1.4rem 0 0.8rem;
    font-family: 'Outfit', sans-serif;
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

/* Tabs */
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
::-webkit-scrollbar { width: 6px; height: 6px; }
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

.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stSelectbox > div > div,
.stDateInput > div > div > input,
.stTextArea > div > div > textarea {
    background: #ffffff !important;
    border: 1px solid #cbd5e1 !important;
    border-radius: 8px !important;
    color: #0f172a !important;
}
</style>
""", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding:0.3rem 0 0.8rem;text-align:center;'>
      <span style='font-size:1.8rem;'>🌿</span>
      <div style='font-size:1.1rem;font-weight:700;color:#1E3A8A;font-family:Outfit,sans-serif;'>CarbonTrack Pro</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("### ⚙️ Filters")
    df_all = load_emissions()

    years = sorted(df_all["date"].dt.year.unique(), reverse=True) if not df_all.empty else [datetime.now().year]
    sel_year = st.selectbox("📅 Year", options=["All"] + [str(y) for y in years], index=0)

    facilities_list = sorted(df_all["facility"].unique().tolist()) if not df_all.empty else []
    sel_fac = st.multiselect("🏭 Facilities", options=facilities_list, default=facilities_list)

    scope_opts = st.multiselect("🔍 Scope", options=[1, 2], default=[1, 2])

    tax_rate = st.number_input("💰 Carbon Tax (MYR/t)", min_value=0.0, value=float(CARBON_TAX_RATE_MYR), step=1.0)

    render_sidebar_user()

# ── Data filtering ─────────────────────────────────────────────────────────────
df = df_all.copy()
if sel_year != "All":
    df = df[df["date"].dt.year == int(sel_year)]
if sel_fac:
    df = df[df["facility"].isin(sel_fac)]
if scope_opts:
    df = df[df["scope"].isin(scope_opts)]

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style='margin-bottom:1.2rem;'>
  <h1 style='color:#1E3A8A;font-size:2rem;font-weight:800;margin:0;font-family:Outfit,sans-serif;'>
    📊 Emission Dashboard
  </h1>
  <p style='color:#64748b;font-size:0.9rem;margin:0.2rem 0 0;'>
    Scope 1 & 2 GHG Protocol Monitoring · Real-time Operational Insights · Carbon Tax Liability
  </p>
</div>
""", unsafe_allow_html=True)

# ── KPI Cards ─────────────────────────────────────────────────────────────────
if df.empty:
    st.warning("No data available for the selected filters.")
    st.stop()

total_co2e_kg = df["co2e_kg"].sum()
s1_kg = df[df["scope"] == 1]["co2e_kg"].sum()
s2_kg = df[df["scope"] == 2]["co2e_kg"].sum()
total_t  = kg_to_tonnes(total_co2e_kg)
s1_t     = kg_to_tonnes(s1_kg)
s2_t     = kg_to_tonnes(s2_kg)
tax_liab = (total_co2e_kg / 1000) * tax_rate
intensity_rev  = emission_intensity_revenue(total_co2e_kg, REVENUE_MYR)
intensity_emp  = emission_intensity_employee(total_co2e_kg, EMPLOYEES)

# YoY for current vs prior period
df_sorted_months = sorted(df["month"].unique())
mid = len(df_sorted_months) // 2
prior_months = df_sorted_months[:mid]
curr_months  = df_sorted_months[mid:]
prior_kg = df[df["month"].isin(prior_months)]["co2e_kg"].sum()
curr_kg  = df[df["month"].isin(curr_months)]["co2e_kg"].sum()
change_pct = yoy_change(curr_kg, prior_kg)
delta_class = "delta-up" if change_pct > 0 else ("delta-down" if change_pct < 0 else "delta-neu")
delta_icon  = "▲" if change_pct > 0 else ("▼" if change_pct < 0 else "—")

c1, c2, c3, c4, c5, c6 = st.columns(6, gap="small")
cards = [
    (c1, "Total CO₂e", f"{total_t:,.1f}", "tonnes", f"{delta_icon} {abs(change_pct):.1f}% vs prior period", delta_class, "#1E3A8A"),
    (c2, "Scope 1", f"{s1_t:,.1f}", "tonnes CO₂e", f"{s1_t/total_t*100:.1f}% of total", "delta-neu", "#d97706"),
    (c3, "Scope 2", f"{s2_t:,.1f}", "tonnes CO₂e", f"{s2_t/total_t*100:.1f}% of total", "delta-neu", "#2563EB"),
    (c4, "Carbon Tax", f"MYR {tax_liab:,.0f}", f"@ MYR {tax_rate:.0f}/t", "Estimated liability", "delta-neu", "#dc2626"),
    (c5, "Revenue Intensity", f"{intensity_rev:.2f}", "tCO₂e / MYR 1M", "Economic intensity", "delta-neu", "#7c3aed"),
    (c6, "Per Employee", f"{intensity_emp:.2f}", "tCO₂e / employee", f"{EMPLOYEES} employees", "delta-neu", "#ea580c"),
]
for col, label, val, sub, delta_txt, d_cls, color in cards:
    with col:
        st.markdown(f"""
        <div class='ct-card'>
          <div class='ct-card-label'>{label}</div>
          <div class='ct-card-value' style='color:{color};'>{val}</div>
          <div style='color:#64748b;font-size:0.72rem;'>{sub}</div>
          <div class='ct-card-delta {d_cls}'>{delta_txt}</div>
        </div>""", unsafe_allow_html=True)

# ── Trend Charts ──────────────────────────────────────────────────────────────
st.markdown("<div class='ct-section-title'>📈 Emission Trends & Analytical Breakdown</div>", unsafe_allow_html=True)

monthly = monthly_summary(df)

tab1, tab2, tab3, tab4 = st.tabs(["📉 Monthly Trend & Forecast", "🥧 By Source", "🏭 Facility Heatmap & Trellis", "💰 Carbon Tax Analysis"])

# Light theme plot configuration aligned with Lab3.py
PLOT_LAYOUT = dict(
    paper_bgcolor="#ffffff",
    plot_bgcolor="#ffffff",
    font=dict(family="Inter, sans-serif", color="#334155"),
    margin=dict(t=45, b=25, l=10, r=10),
    legend=dict(bgcolor="rgba(255,255,255,0.9)", bordercolor="#e2e8f0", borderwidth=1),
    xaxis=dict(gridcolor="#f1f5f9", showgrid=True, zeroline=False),
    yaxis=dict(gridcolor="#f1f5f9", showgrid=True, zeroline=False),
)

with tab1:
    st.write(
        "Traces monthly GHG emissions across **Scope 1 (Direct)** and **Scope 2 (Indirect Electricity)**, "
        "alongside an automated linear regression projection for the upcoming 6 months."
    )
    if not monthly.empty:
        pivot = monthly.pivot_table(index="month", columns="scope", values="co2e_tonnes", fill_value=0).reset_index()
        pivot.columns = ["Month", "Scope 1", "Scope 2"] if 2 in pivot.columns.tolist() else ["Month", "Scope 1"]

        # Add prediction
        all_months = sorted(df_all["month"].unique())
        monthly_all = monthly_summary(df_all)
        total_by_month = monthly_all.groupby("month")["co2e_tonnes"].sum().reset_index()
        total_by_month["idx"] = range(len(total_by_month))

        if len(total_by_month) >= 4:
            X = total_by_month[["idx"]]
            y = total_by_month["co2e_tonnes"]
            lr = LinearRegression().fit(X, y)
            future_idx = list(range(len(total_by_month), len(total_by_month) + 6))
            future_vals = lr.predict([[i] for i in future_idx])

            last_month = pd.Period(total_by_month["month"].iloc[-1], freq="M")
            future_months = [(last_month + i + 1).strftime("%Y-%m") for i in range(6)]
            pred_df = pd.DataFrame({"Month": future_months, "Predicted": future_vals})
        else:
            pred_df = pd.DataFrame()

        fig = go.Figure()
        for scope_num, color, name in [(1, "#d97706", "Scope 1"), (2, "#2563EB", "Scope 2")]:
            col_name = f"Scope {scope_num}"
            if col_name in pivot.columns:
                fig.add_trace(go.Scatter(
                    x=pivot["Month"], y=pivot[col_name], name=name,
                    line=dict(color=color, width=2.5),
                    fill="tozeroy",
                    fillcolor="rgba(37,99,235,0.06)" if scope_num == 2 else "rgba(217,119,6,0.06)",
                    mode="lines+markers",
                    marker=dict(size=6),
                ))

        if not pred_df.empty:
            fig.add_trace(go.Scatter(
                x=pred_df["Month"], y=pred_df["Predicted"],
                name="AI Prediction (6M)",
                line=dict(color="#059669", width=2.2, dash="dash"),
                mode="lines+markers",
                marker=dict(size=6, symbol="diamond"),
            ))

        fig.update_layout(
            **PLOT_LAYOUT,
            title="Monthly CO₂e Emissions by Scope (tonnes) + 6-Month Trajectory",
            yaxis_title="Tonnes CO₂e",
            height=400,
        )
        st.plotly_chart(fig, use_container_width=True)
        st.info(
            f"💡 **Observations:** Scope 2 emissions comprise {s2_t/total_t*100:.1f}% of your organization's footprint. "
            "Notice peak consumption cycles and compare with the upcoming 6-month forecast trajectory."
        )

with tab2:
    st.write(
        "Shows proportional breakdown of carbon emissions categorized by origin activity source. "
        "Hover over individual sectors for exact tonnage and percentage contributions."
    )
    src = source_summary(df)
    if not src.empty:
        fig2 = px.pie(
            src, values="co2e_tonnes", names="source",
            color_discrete_sequence=px.colors.qualitative.Tableau10,
            hole=0.45,
            title="CO₂e Distribution by Emission Source",
        )
        fig2.update_layout(**PLOT_LAYOUT, height=430)
        fig2.update_traces(textposition="outside", textinfo="percent+label",
                           textfont_color="#1e293b")
        c_left, c_right = st.columns([1.2, 1])
        with c_left:
            st.plotly_chart(fig2, use_container_width=True)
        with c_right:
            st.markdown("<div class='ct-section-title' style='margin-top:1rem;'>Top Emission Sources</div>", unsafe_allow_html=True)
            for _, row in src.head(6).iterrows():
                pct = row["co2e_tonnes"] / src["co2e_tonnes"].sum() * 100
                scope_badge_color = "#d97706" if row["scope"] == 1 else "#2563EB"
                st.markdown(f"""
                <div style='display:flex;justify-content:space-between;align-items:center;
                    padding:0.6rem 0.9rem;margin:0.35rem 0;border-radius:8px;
                    background:#ffffff;border:1px solid #e2e8f0;box-shadow:0 1px 2px rgba(0,0,0,0.03);'>
                  <div>
                    <span style='background:{scope_badge_color}18;color:{scope_badge_color};font-size:0.7rem;font-weight:700;padding:2px 6px;border-radius:4px;'>S{row["scope"]}</span>
                    <span style='color:#1e293b;font-size:0.84rem;font-weight:600;margin-left:0.4rem;'>{row["source"]}</span>
                  </div>
                  <div style='text-align:right;'>
                    <span style='color:#1E3A8A;font-weight:700;font-size:0.88rem;'>{row["co2e_tonnes"]:,.1f}t</span>
                    <span style='color:#64748b;font-size:0.75rem;margin-left:0.3rem;'>({pct:.1f}%)</span>
                  </div>
                </div>""", unsafe_allow_html=True)
        st.info("💡 **Observations:** Identify the largest contributing sources to prioritize for targeted decarbonization measures.")

with tab3:
    st.write(
        "Multi-dimensional facility comparison: horizontal rankings display aggregate site burdens, "
        "while the monthly matrix heatmap pinpoints temporal intensity variations across operations."
    )
    fac = facility_summary(df)
    if not fac.empty:
        fac_total = fac.groupby("facility")["co2e_tonnes"].sum().reset_index().sort_values("co2e_tonnes", ascending=True)
        fig3 = px.bar(
            fac_total, x="co2e_tonnes", y="facility", orientation="h",
            color="co2e_tonnes",
            color_continuous_scale=px.colors.sequential.Blues,
            title="Total CO₂e by Facility (tonnes)",
            labels={"co2e_tonnes": "Tonnes CO₂e", "facility": ""},
        )
        fig3.update_layout(**PLOT_LAYOUT, height=360, coloraxis_showscale=False)
        st.plotly_chart(fig3, use_container_width=True)

        # Heatmap
        fac_pivot = fac.pivot_table(index="facility", columns="month", values="co2e_tonnes", fill_value=0)
        fig4 = px.imshow(
            fac_pivot,
            color_continuous_scale=px.colors.sequential.Blues,
            title="Emission Heatmap: Facility × Month (tonnes CO₂e)",
            aspect="auto",
        )
        fig4.update_layout(**PLOT_LAYOUT, height=320)
        st.plotly_chart(fig4, use_container_width=True)
        st.info("💡 **Observations:** Darker blue cells indicate higher monthly facility output. Monitor sites with sudden spikes across consecutive months.")

with tab4:
    st.write(
        "Quantifies financial exposure under carbon pricing frameworks. "
        "Dual-axis projection correlates monthly recurring fees against cumulative tax accumulation."
    )
    if not monthly.empty:
        monthly_total = monthly.groupby("month")["co2e_tonnes"].sum().reset_index()
        monthly_total["tax_myr"] = monthly_total["co2e_tonnes"] * tax_rate
        monthly_total["cumulative_tax"] = monthly_total["tax_myr"].cumsum()

        fig5 = make_subplots(specs=[[{"secondary_y": True}]])
        fig5.add_trace(go.Bar(
            x=monthly_total["month"], y=monthly_total["tax_myr"],
            name="Monthly Tax (MYR)", marker_color="#f87171", opacity=0.85,
        ), secondary_y=False)
        fig5.add_trace(go.Scatter(
            x=monthly_total["month"], y=monthly_total["cumulative_tax"],
            name="Cumulative Tax (MYR)", line=dict(color="#1E3A8A", width=2.5),
            mode="lines+markers",
        ), secondary_y=True)
        fig5.update_layout(
            **PLOT_LAYOUT,
            title=f"Carbon Tax Liability @ MYR {tax_rate:.0f}/tonne CO₂e",
            height=380,
        )
        fig5.update_yaxes(title_text="Monthly MYR", secondary_y=False,
                          gridcolor="#f1f5f9")
        fig5.update_yaxes(title_text="Cumulative MYR", secondary_y=True,
                          gridcolor="#f1f5f9")
        st.plotly_chart(fig5, use_container_width=True)

        total_tax_str = f"MYR {monthly_total['tax_myr'].sum():,.2f}"
        st.markdown(f"""
        <div style='background:#ffffff;border:1px solid #fecaca;border-left:4px solid #dc2626;
            border-radius:10px;padding:1rem 1.4rem;margin-top:0.5rem;box-shadow:0 1px 3px rgba(0,0,0,0.03);'>
          <div style='color:#dc2626;font-size:0.75rem;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;'>
            Total Estimated Carbon Tax Liability
          </div>
          <div style='color:#1E3A8A;font-size:1.8rem;font-weight:700;margin-top:0.2rem;font-family:Outfit,sans-serif;'>{total_tax_str}</div>
          <div style='color:#64748b;font-size:0.75rem;'>Based on filtered period · Statutory reference rate: MYR {tax_rate:.0f} / tonne CO₂e</div>
        </div>""", unsafe_allow_html=True)
        st.info("💡 **Observations:** Financial liability scales linearly with tonnage. Early decarbonization initiatives directly mitigate bottom-line tax risks.")

# ── AI Insight Panel ──────────────────────────────────────────────────────────
st.markdown("<div class='ct-section-title'>🤖 AI Insights & Recommendations</div>", unsafe_allow_html=True)
st.markdown("<div class='ai-insight-box'>", unsafe_allow_html=True)
st.markdown("<div class='ai-badge'>✨ AI Powered · Gemini 1.5 Flash</div>", unsafe_allow_html=True)

src_summary = source_summary(df)
summary_text = f"""
Period: {df['date'].min().strftime('%b %Y')} to {df['date'].max().strftime('%b %Y')}
Total CO₂e: {total_t:,.1f} tonnes
Scope 1: {s1_t:,.1f} t ({s1_t/total_t*100:.1f}%)
Scope 2: {s2_t:,.1f} t ({s2_t/total_t*100:.1f}%)
Carbon Tax Liability: MYR {tax_liab:,.0f}
Period-on-Period Change: {change_pct:+.1f}%
Revenue Intensity: {intensity_rev:.3f} tCO₂e/MYR 1M
Employee Intensity: {intensity_emp:.3f} tCO₂e/employee
Top 3 Sources: {', '.join(src_summary['source'].head(3).tolist()) if not src_summary.empty else 'N/A'}
Facilities monitored: {len(sel_fac)}
"""

if "ai_insight_cache" not in st.session_state:
    st.session_state.ai_insight_cache = None
if "ai_insight_params" not in st.session_state:
    st.session_state.ai_insight_params = None

col_btn, col_sp = st.columns([1, 4])
with col_btn:
    gen_btn = st.button("🔄 Generate Insight", type="primary", key="gen_insight_btn")

if gen_btn or (st.session_state.ai_insight_cache is None):
    with st.spinner("🤖 AI is analysing your emission data…"):
        insight = get_dashboard_insight(summary_text)
        st.session_state.ai_insight_cache = insight
        st.session_state.ai_insight_params = sel_year

if st.session_state.ai_insight_cache:
    st.markdown(
        f"<div style='color:#1e3a8a;font-size:0.92rem;line-height:1.75;margin-top:0.5rem;'>"
        f"{st.session_state.ai_insight_cache}</div>",
        unsafe_allow_html=True,
    )

st.markdown("</div>", unsafe_allow_html=True)

st.markdown("""
<div style='text-align:center;color:#64748b;font-size:0.75rem;padding:1.5rem 0 0;'>
  Data sourced from internal records · GHG Protocol Scope 1 & 2 · Malaysia Grid 0.585 kg CO₂e/kWh
</div>""", unsafe_allow_html=True)
