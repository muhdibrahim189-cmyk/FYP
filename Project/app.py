"""
app.py – CarbonTrack Pro: entry point and landing page.
Run with:  streamlit run app.py
"""
import streamlit as st
import sys, os

sys.path.insert(0, os.path.dirname(__file__))
from utils.auth import require_login, render_sidebar_user, init_session
from utils.data_manager import init_db

# ── Page config (must be FIRST streamlit call) ─────────────────────────────────
st.set_page_config(
    page_title="CarbonTrack Pro",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap');

* { font-family: 'Inter', sans-serif; }

/* Lab3.py Background & Container */
.reportview-container, [data-testid="stAppViewContainer"] {
    background: #f0f2f6;
    min-height: 100vh;
}
.main .block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}

/* Headings in Lab3.py Style */
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

/* Clean Cards */
.ct-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1.3rem 1.5rem;
    transition: all 0.2s ease;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
.ct-card:hover {
    border-color: #93c5fd;
    transform: translateY(-2px);
    box-shadow: 0 6px 18px rgba(37,99,235,0.08);
}
.ct-card-value {
    font-size: 2rem;
    font-weight: 700;
    color: #1E3A8A;
    margin: 0.25rem 0;
    line-height: 1.1;
    font-family: 'Outfit', sans-serif;
}
.ct-card-label {
    font-size: 0.75rem;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    font-weight: 600;
}
.ct-card-delta {
    font-size: 0.82rem;
    font-weight: 500;
    margin-top: 0.35rem;
}
.delta-up   { color: #dc2626; }
.delta-down { color: #16a34a; }
.delta-neu  { color: #64748b; }

/* Section headers */
.ct-section-title {
    font-size: 1.15rem;
    font-weight: 700;
    color: #1E3A8A;
    border-left: 4px solid #2563EB;
    padding-left: 0.7rem;
    margin: 1.5rem 0 0.8rem;
    font-family: 'Outfit', sans-serif;
}

/* AI Insight panel */
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
    margin-bottom: 0.8rem;
}

/* Streamlit metric overrides */
[data-testid="stMetric"] {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 0.8rem 1rem;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04);
}
[data-testid="stMetricValue"] {
    color: #1E3A8A !important;
    font-weight: 700 !important;
    font-family: 'Outfit', sans-serif !important;
}
[data-testid="stMetricLabel"] {
    color: #64748b !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
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

/* Buttons */
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
.stButton > button[kind="secondary"]:hover {
    background: #f8fafc !important;
    border-color: #94a3b8 !important;
}

/* Inputs */
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

/* Table styling */
.stDataFrame { border-radius: 10px; overflow: hidden; border: 1px solid #e2e8f0; }
[data-testid="stDataFrame"] th {
    background: #f1f5f9 !important;
    color: #1E3A8A !important;
    font-weight: 600 !important;
}

/* Divider */
hr { border-color: #e2e8f0 !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 3px; }

/* Chat messages */
[data-testid="stChatMessage"] {
    background: #ffffff !important;
    border-radius: 12px !important;
    border: 1px solid #e2e8f0 !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.03);
}
</style>
""", unsafe_allow_html=True)

# ── Bootstrap ──────────────────────────────────────────────────────────────────
init_session()
init_db()
require_login()

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding:0.5rem 0 1rem;text-align:center;'>
      <span style='font-size:2.2rem;'>🌿</span>
      <div style='font-size:1.15rem;font-weight:700;color:#1E3A8A;font-family:Outfit,sans-serif;'>CarbonTrack Pro</div>
      <div style='font-size:0.75rem;color:#64748b;'>Scope 1 & 2 GHG Accounting</div>
    </div>
    """, unsafe_allow_html=True)
    render_sidebar_user()

# ── Home content ───────────────────────────────────────────────────────────────
st.markdown("""
<div style='text-align:center;padding:2.5rem 0 1.5rem;'>
  <span style='font-size:3.5rem;'>🌿</span>
  <h1 style='color:#1E3A8A;font-size:2.4rem;font-weight:800;margin:0.3rem 0;font-family:Outfit,sans-serif;'>
    CarbonTrack <span style='color:#2563EB;'>Pro</span>
  </h1>
  <p style='color:#475569;font-size:1.05rem;max-width:650px;margin:0.2rem auto 0;'>
    Digital Carbon Accounting, Tracking & Reporting Platform<br>
    <span style='color:#64748b;font-size:0.88rem;'>Scope 1 & Scope 2 · GHG Protocol Compliant · AI-Powered Insights</span>
  </p>
</div>
""", unsafe_allow_html=True)

# Navigation cards
cols = st.columns(4, gap="medium")
nav_items = [
    ("📊", "Main Dashboard",    "Real-time KPIs, emission trends, carbon tax liability & AI-powered insights",      "pages/1_📊_Main_Dashboard.py"),
    ("🔬", "What-If Simulator", "Explore emission reduction scenarios and get AI chatbot recommendations",            "pages/2_🔬_What_If_Simulator.py"),
    ("🗄️",  "Data Centre",       "Full data transparency — filter, explore and export all emission records",          "pages/3_🗄️_Data_Centre.py"),
    ("♻️",  "Sustainability",    "Governance, data entry, anomaly detection & manager approval workflow",             "pages/4_♻️_Sustainability.py"),
]
for col, (icon, title, desc, _) in zip(cols, nav_items):
    with col:
        st.markdown(f"""
        <div class='ct-card' style='text-align:center;min-height:160px;'>
          <div style='font-size:2rem;margin-bottom:0.5rem;'>{icon}</div>
          <div style='font-size:1.05rem;font-weight:700;color:#1E3A8A;margin-bottom:0.4rem;font-family:Outfit,sans-serif;'>{title}</div>
          <div style='font-size:0.8rem;color:#64748b;line-height:1.5;'>{desc}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Quick stats strip
from utils.data_manager import load_emissions
from utils.carbon_calculator import carbon_tax

df = load_emissions()
if not df.empty:
    total_co2e = df["co2e_kg"].sum() / 1000
    s1 = df[df["scope"] == 1]["co2e_kg"].sum() / 1000
    s2 = df[df["scope"] == 2]["co2e_kg"].sum() / 1000
    tax = carbon_tax(df["co2e_kg"].sum())

    st.markdown("<div class='ct-section-title'>📈 Platform Overview</div>", unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(f"""<div class='ct-card'>
            <div class='ct-card-label'>Total CO₂e (18 months)</div>
            <div class='ct-card-value'>{total_co2e:,.0f}</div>
            <div style='color:#64748b;font-size:0.75rem;'>tonnes</div></div>""",
            unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class='ct-card'>
            <div class='ct-card-label'>Scope 1 Emissions</div>
            <div class='ct-card-value' style='color:#d97706;'>{s1:,.0f}</div>
            <div style='color:#64748b;font-size:0.75rem;'>tonnes CO₂e</div></div>""",
            unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class='ct-card'>
            <div class='ct-card-label'>Scope 2 Emissions</div>
            <div class='ct-card-value' style='color:#2563EB;'>{s2:,.0f}</div>
            <div style='color:#64748b;font-size:0.75rem;'>tonnes CO₂e</div></div>""",
            unsafe_allow_html=True)
    with c4:
        st.markdown(f"""<div class='ct-card'>
            <div class='ct-card-label'>Carbon Tax Liability</div>
            <div class='ct-card-value' style='color:#dc2626;'>MYR {tax:,.0f}</div>
            <div style='color:#64748b;font-size:0.75rem;'>@ MYR 35/t</div></div>""",
            unsafe_allow_html=True)
    with c5:
        st.markdown(f"""<div class='ct-card'>
            <div class='ct-card-label'>Data Records</div>
            <div class='ct-card-value' style='color:#7c3aed;'>{len(df):,}</div>
            <div style='color:#64748b;font-size:0.75rem;'>emission entries</div></div>""",
            unsafe_allow_html=True)

st.markdown("""
<br>
<div style='text-align:center;color:#64748b;font-size:0.75rem;padding:1rem 0;'>
  CarbonTrack Pro · GHG Protocol Compliant · Malaysia Grid Factor 0.585 kg CO₂e/kWh · Carbon Tax MYR 35/t
</div>
""", unsafe_allow_html=True)
