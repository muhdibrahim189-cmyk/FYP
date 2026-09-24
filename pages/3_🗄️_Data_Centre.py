"""
Page 3 – Data Centre
Full emission records with filtering, search, export, and charts.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

from utils.auth import require_login, render_sidebar_user
from utils.data_manager import init_db, load_emissions
from utils.carbon_calculator import carbon_tax, kg_to_tonnes
from data.emission_factors import CARBON_TAX_RATE_MYR
from utils.ui import render_base_styles, render_navigation, render_sidebar_brand, render_data_quality_notice

st.set_page_config(page_title="Data Centre · Fiscal Green", page_icon="🗄️", layout="wide")
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
.stDataFrame { border-radius: 10px; overflow: hidden; border: 1px solid #e2e8f0; }
div[data-testid="stDataFrame"] th {
    background: #f1f5f9 !important;
    color: #1E3A8A !important;
    font-weight: 600 !important;
}
.filter-pill {
    display: inline-block;
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    border-radius: 20px;
    padding: 3px 10px;
    font-size: 0.72rem;
    color: #1e40af;
    font-weight: 600;
    margin: 2px;
}
.stTextInput > div > div > input,
.stSelectbox > div > div,
.stDateInput > div > div > input,
.stMultiSelect > div > div {
    background: #ffffff !important;
    border: 1px solid #cbd5e1 !important;
    border-radius: 8px !important;
    color: #0f172a !important;
}
</style>
""", unsafe_allow_html=True)
render_base_styles()

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    render_sidebar_brand()
    st.markdown("### 🧭 Navigation")
    render_navigation("🗄️ Data Centre")
    render_sidebar_user()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style='margin-bottom:1.2rem;'>
  <h1 style='color:#1E3A8A;font-size:2rem;font-weight:800;margin:0;font-family:Outfit,sans-serif;'>🗄️ Emission Data Repository</h1>
  <p style='color:#64748b;font-size:0.9rem;margin:0.2rem 0 0;'>
    Complete Historical Emission Ledger · Interactive Multidimensional Filtering · Audit-Ready Data Export
  </p>
</div>
""", unsafe_allow_html=True)

# ── Load data ─────────────────────────────────────────────────────────────────
df_raw = load_emissions()
render_data_quality_notice(df_raw)
if df_raw.empty:
    st.warning("No data found in the database.")
    st.stop()

# ── Filter Panel ──────────────────────────────────────────────────────────────
st.markdown("<div class='ct-section-title'>🔍 Filters</div>", unsafe_allow_html=True)

with st.container():
    f1, f2, f3, f4, f5 = st.columns([1.5, 1, 1, 1.5, 1])
    with f1:
        min_date = df_raw["date"].min().date()
        max_date = df_raw["date"].max().date()
        date_range = st.date_input(
            "📅 Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
            key="dc_date",
        )
    with f2:
        scope_filter = st.multiselect("🔍 Scope", [1, 2], default=[1, 2], key="dc_scope")
    with f3:
        all_sources = sorted(df_raw["source"].unique().tolist())
        source_filter = st.multiselect("⚗️ Source", all_sources, default=all_sources, key="dc_source")
    with f4:
        facilities = sorted(df_raw["facility"].unique().tolist())
        facility_filter = st.multiselect("🏭 Company", facilities, default=facilities, key="dc_fac")
    with f5:
        submitted_by_opts = ["All"] + sorted(df_raw["submitted_by"].unique().tolist())
        user_filter = st.selectbox("👤 Submitted By", submitted_by_opts, key="dc_user")

# Apply filters
df = df_raw.copy()
if len(date_range) == 2:
    start_d, end_d = date_range
    df = df[(df["date"].dt.date >= start_d) & (df["date"].dt.date <= end_d)]
if scope_filter:
    df = df[df["scope"].isin(scope_filter)]
if source_filter:
    df = df[df["source"].isin(source_filter)]
if facility_filter:
    df = df[df["facility"].isin(facility_filter)]
if user_filter != "All":
    df = df[df["submitted_by"] == user_filter]

# ── Stats strip ───────────────────────────────────────────────────────────────
total_t  = df["co2e_kg"].sum() / 1000
tax_myr  = carbon_tax(df["co2e_kg"].sum())
s1_pct   = df[df["scope"]==1]["co2e_kg"].sum() / df["co2e_kg"].sum() * 100 if not df.empty else 0
s2_pct   = 100 - s1_pct

k1, k2, k3, k4, k5 = st.columns(5, gap="small")
stats = [
    (k1, "Records Found", f"{len(df):,}", f"of {len(df_raw):,} total", "#1E3A8A"),
    (k2, "Filtered CO₂e", f"{total_t:,.1f} t", "tonnes CO₂e", "#2563EB"),
    (k3, "Estimated Carbon Tax", f"MYR {tax_myr:,.0f}", f"@ MYR {CARBON_TAX_RATE_MYR:.0f}/t", "#dc2626"),
    (k4, "Scope 1 Share", f"{s1_pct:.1f}%", "direct emissions", "#d97706"),
    (k5, "Scope 2 Share", f"{s2_pct:.1f}%", "indirect emissions", "#2563EB"),
]
for col, label, val, sub, color in stats:
    with col:
        st.markdown(f"""
        <div class='ct-card'>
          <div class='ct-card-label'>{label}</div>
          <div class='ct-card-value' style='color:{color};font-size:1.5rem;'>{val}</div>
          <div style='color:#64748b;font-size:0.72rem;'>{sub}</div>
        </div>""", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
PLOT_LAYOUT = dict(
    paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
    font=dict(family="Inter, sans-serif", color="#334155"),
    margin=dict(t=45, b=25, l=10, r=10),
    xaxis=dict(gridcolor="#f1f5f9", showgrid=True, zeroline=False),
    yaxis=dict(gridcolor="#f1f5f9", showgrid=True, zeroline=False),
)

tab_data, tab_charts, tab_export = st.tabs(["📋 Data Table", "📊 Analytics & Visualizations", "📤 Export"])

with tab_data:
    st.write("Browse, search, and inspect individual historical emission records. Filtered rows match your active criteria above.")
    search = st.text_input("🔎 Search records (source, facility, submitted by…)", "", key="dc_search")
    if search:
        mask = df.apply(lambda r: search.lower() in str(r.values).lower(), axis=1)
        df_show = df[mask]
    else:
        df_show = df

    # Prepare display table
    display_cols = {
        "id": "ID", "date": "Date", "facility": "Facility",
        "scope": "Scope", "source": "Source", "unit": "Unit",
        "quantity": "Quantity", "co2e_kg": "CO₂e (kg)",
        "submitted_by": "Submitted By", "submitted_at": "Submitted At",
        "status": "Status", "approved_by": "Approved By",
        "is_anomaly": "Anomaly Flag",
    }
    df_display = df_show[list(display_cols.keys())].rename(columns=display_cols)
    df_display["CO₂e (kg)"] = df_display["CO₂e (kg)"].round(2)
    df_display["Quantity"]  = df_display["Quantity"].round(3)
    df_display["Anomaly Flag"] = df_display["Anomaly Flag"].map({0: "—", 1: "⚠️ Yes"})
    df_display["Status"] = df_display["Status"].map({
        "approved": "✅ Approved",
        "pending":  "⏳ Pending",
        "rejected": "❌ Rejected",
    }).fillna(df_display["Status"])

    st.markdown(f"<div style='color:#64748b;font-size:0.78rem;margin-bottom:0.4rem;'>Showing {len(df_display):,} of {len(df_raw):,} records</div>",
                unsafe_allow_html=True)

    # Pagination
    PAGE_SIZE = 25
    total_pages = max(1, (len(df_display) - 1) // PAGE_SIZE + 1)
    page = st.number_input("Page", min_value=1, max_value=total_pages, value=1, step=1,
                           key="dc_page", label_visibility="collapsed")
    start_idx = (page - 1) * PAGE_SIZE
    end_idx   = start_idx + PAGE_SIZE

    st.dataframe(
        df_display.iloc[start_idx:end_idx].reset_index(drop=True),
        width="stretch",
        height=450,
    )
    st.markdown(f"<div style='color:#64748b;font-size:0.75rem;text-align:right;'>Page {page} of {total_pages}</div>",
                unsafe_allow_html=True)
    st.info("💡 **Observations:** Use column headers to sort tabular data. All records are verifiable against audit log events.")

with tab_charts:
    st.write("Visual exploratory analysis of filtered records across temporal, source, and facility dimensions.")
    c_left, c_right = st.columns(2)

    with c_left:
        # Timeline chart
        if not df.empty:
            daily = df.groupby(["date", "scope"])["co2e_kg"].sum().reset_index()
            daily["co2e_kg"] = daily["co2e_kg"] / 1000
            fig_tl = px.line(
                daily, x="date", y="co2e_kg", color="scope",
                title="Daily CO₂e Over Time (tonnes)",
                labels={"co2e_kg": "Tonnes CO₂e", "date": "Date", "scope": "Scope"},
                color_discrete_map={1: "#d97706", 2: "#2563EB"},
            )
            fig_tl.update_layout(**PLOT_LAYOUT, height=300)
            st.plotly_chart(fig_tl, width="stretch")

        # Source bar
        src_grp = df.groupby("source")["co2e_kg"].sum().reset_index().sort_values("co2e_kg", ascending=False)
        src_grp["co2e_kg"] = src_grp["co2e_kg"] / 1000
        fig_src = px.bar(
            src_grp, x="co2e_kg", y="source", orientation="h",
            color="co2e_kg", color_continuous_scale=px.colors.sequential.Blues,
            title="CO₂e by Source (tonnes)", labels={"co2e_kg": "Tonnes", "source": ""},
        )
        fig_src.update_layout(**PLOT_LAYOUT, height=350, coloraxis_showscale=False)
        st.plotly_chart(fig_src, width="stretch")

    with c_right:
        # Scope donut
        scope_grp = df.groupby("scope")["co2e_kg"].sum().reset_index()
        scope_grp["label"] = scope_grp["scope"].map({1: "Scope 1", 2: "Scope 2"})
        fig_donut = px.pie(
            scope_grp, values="co2e_kg", names="label",
            hole=0.5, title="Scope Distribution",
            color_discrete_map={"Scope 1": "#d97706", "Scope 2": "#2563EB"},
        )
        fig_donut.update_layout(**PLOT_LAYOUT, height=280)
        fig_donut.update_traces(textfont_color="#1e293b")
        st.plotly_chart(fig_donut, width="stretch")

        # Facility treemap
        fac_grp = df.groupby(["facility", "source"])["co2e_kg"].sum().reset_index()
        fac_grp["co2e_t"] = fac_grp["co2e_kg"] / 1000
        fig_tree = px.treemap(
            fac_grp, path=["facility", "source"], values="co2e_t",
            title="Emission Breakdown: Facility → Source",
            color="co2e_t", color_continuous_scale=px.colors.sequential.Blues,
        )
        fig_tree.update_layout(**PLOT_LAYOUT, height=350)
        st.plotly_chart(fig_tree, width="stretch")

    st.info("💡 **Observations:** The treemap hierarchy illustrates how emissions aggregate from individual facility operations up to total corporate burden.")

with tab_export:
    st.markdown("""
    <div style='color:#9ca3af;font-size:0.85rem;margin-bottom:1rem;'>
    Download the filtered dataset for offline analysis, reporting, or audit purposes.
    </div>""", unsafe_allow_html=True)

    # Prepare export
    export_df = df.copy()
    export_df["co2e_tonnes"] = export_df["co2e_kg"] / 1000
    export_df["carbon_tax_myr"] = (export_df["co2e_tonnes"] * CARBON_TAX_RATE_MYR).round(2)

    export_cols = ["id", "date", "facility", "scope", "source", "unit", "quantity",
                   "co2e_kg", "co2e_tonnes", "carbon_tax_myr",
                   "submitted_by", "submitted_at", "status", "approved_by", "approved_at",
                   "notes", "is_anomaly"]
    export_df = export_df[[c for c in export_cols if c in export_df.columns]]

    csv = export_df.to_csv(index=False)

    col_dl, col_info = st.columns([1, 2])
    with col_dl:
        st.download_button(
            label="⬇️ Download CSV",
            data=csv,
            file_name=f"carbontrack_emissions_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            type="primary",
            width="stretch",
        )
    with col_info:
        st.markdown(f"""
        <div class='ct-card' style='padding:0.8rem 1rem;'>
          <div style='color:#9ca3af;font-size:0.75rem;'>
            📋 {len(export_df):,} records · 
            {export_df['co2e_tonnes'].sum():,.1f} tCO₂e · 
            {export_df['date'].min()} to {export_df['date'].max()}
          </div>
        </div>""", unsafe_allow_html=True)

    # Preview
    st.markdown("<div class='ct-section-title'>Preview (first 10 rows)</div>", unsafe_allow_html=True)
    st.dataframe(export_df.head(10), width="stretch")
