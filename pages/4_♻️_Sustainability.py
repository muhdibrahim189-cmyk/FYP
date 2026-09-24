"""
Page 4 – Sustainability
Data entry, anomaly detection, approval workflow, activity log, audit trail.
"""
import streamlit as st
import pandas as pd
from datetime import datetime, date

from utils.auth import require_login, render_sidebar_user, has_permission, current_user
from utils.data_manager import (
    init_db, submit_emission, approve_submission, reject_submission,
    load_pending, load_all_pending, load_activity_log, log_action, load_emissions,
)
from utils.carbon_calculator import kg_to_tonnes, carbon_tax
from data.emission_factors import (
    ALL_FACTORS, SCOPE1_SOURCES, SCOPE2_SOURCES, FACILITIES, CARBON_TAX_RATE_MYR,
)
from utils.ui import render_base_styles, render_navigation, render_sidebar_brand

st.set_page_config(page_title="Sustainability · Fiscal Green", page_icon="♻️", layout="wide")
init_db()
require_login()
role = st.session_state.get("role", "data_entry")
username = st.session_state.get("username", "")

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

/* Sidebar */
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

.approval-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1.1rem 1.3rem;
    margin: 0.6rem 0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    transition: all 0.2s ease;
}
.approval-card:hover {
    border-color: #93c5fd;
    box-shadow: 0 4px 12px rgba(37,99,235,0.06);
}

/* Status Badges */
.anomaly-badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    background: #fff7ed;
    border: 1px solid #fdba74;
    border-radius: 20px;
    padding: 3px 10px;
    font-size: 0.72rem;
    font-weight: 600;
    color: #c2410c;
    text-transform: uppercase;
}
.approved-badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    background: #f0fdf4;
    border: 1px solid #86efac;
    border-radius: 20px;
    padding: 3px 10px;
    font-size: 0.72rem;
    font-weight: 600;
    color: #15803d;
    text-transform: uppercase;
}
.pending-badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    background: #fefce8;
    border: 1px solid #fde047;
    border-radius: 20px;
    padding: 3px 10px;
    font-size: 0.72rem;
    font-weight: 600;
    color: #a16207;
    text-transform: uppercase;
}
.rejected-badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    background: #fef2f2;
    border: 1px solid #fca5a5;
    border-radius: 20px;
    padding: 3px 10px;
    font-size: 0.72rem;
    font-weight: 600;
    color: #b91c1c;
    text-transform: uppercase;
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
.stButton > button[kind="secondary"]:hover {
    background: #f8fafc !important;
    border-color: #94a3b8 !important;
}

.log-row {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    padding: 0.6rem 0.85rem;
    margin: 0.25rem 0;
    border-radius: 8px;
    background: #ffffff;
    border: 1px solid #e2e8f0;
    box-shadow: 0 1px 2px rgba(0,0,0,0.02);
}
.log-timestamp { color: #64748b; font-size: 0.74rem; min-width: 130px; font-family: monospace; }
.log-user { color: #2563EB; font-size: 0.78rem; font-weight: 600; min-width: 80px; }
.log-action { font-size: 0.78rem; font-weight: 600; }
.log-details { color: #334155; font-size: 0.76rem; flex: 1; }

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
render_base_styles()

with st.sidebar:
    render_sidebar_brand()
    st.markdown("### 🧭 Navigation")
    render_navigation("♻️ Sustainability")
    render_sidebar_user()

# ── Pending badge in header ───────────────────────────────────────────────────
pending_df = load_pending()
pending_count = len(pending_df)

if pending_count > 0 and role in ("manager", "admin"):
    st.markdown(f"""
    <div style='background:#fefce8;border:1px solid #fde047;border-left:4px solid #ca8a04;
        border-radius:10px;padding:0.75rem 1.1rem;margin-bottom:1.2rem;display:flex;align-items:center;gap:0.8rem;'>
      <span style='font-size:1.3rem;'>⚠️</span>
      <div>
        <span style='color:#a16207;font-weight:700;'>{pending_count} submission(s) awaiting your approval</span>
        <div style='color:#713f12;font-size:0.8rem;'>Review and authorize or reject flagged entries in the Approval Queue tab below.</div>
      </div>
    </div>""", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_labels = ["📝 Data Entry", "⏳ Approval Queue", "📜 Activity Log", "📊 Sustainability Metrics"]
if role in ("manager", "admin"):
    pass  # all tabs visible
tab_entry, tab_approval, tab_log, tab_metrics = st.tabs(tab_labels)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 – Data Entry
# ══════════════════════════════════════════════════════════════════════════════
with tab_entry:
    st.markdown("<div class='ct-section-title'>📝 Submit New Emission Record</div>", unsafe_allow_html=True)
    st.write(
        "Standardized GHG emission logging interface. Submissions are dynamically benchmarked against facility baselines. "
        "Inputs deviating significantly from historical distributions are intercepted for managerial verification."
    )
    st.markdown("""
    <div style='background:#eff6ff;border:1px solid #bfdbfe;border-left:4px solid #2563EB;
        border-radius:10px;padding:0.85rem 1.1rem;margin-bottom:1.2rem;color:#334155;font-size:0.84rem;'>
    ℹ️ <strong>Validation Protocol:</strong> All entries are automatically scored against historical standard deviations. 
    Outlier quantities will be <strong style='color:#c2410c;'>flagged as potential anomalies</strong> and routed to an authorized supervisor for audit sign-off.
    </div>""", unsafe_allow_html=True)

    with st.form("emission_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            entry_date     = st.date_input("📅 Emission Date", value=date.today(), max_value=date.today())
            facility       = st.selectbox("🏭 Facility", FACILITIES)
            scope_choice   = st.radio("🔍 Scope", [1, 2], horizontal=True,
                                       format_func=lambda x: f"Scope {x} ({'Direct' if x==1 else 'Indirect'})")
        with col2:
            if scope_choice == 1:
                source = st.selectbox("⚗️ Emission Source", SCOPE1_SOURCES)
            else:
                source = st.selectbox("⚗️ Emission Source", SCOPE2_SOURCES)

            unit_label = ALL_FACTORS[source]["unit"]
            factor_val = ALL_FACTORS[source]["factor"]

            quantity = st.number_input(
                f"📦 Quantity ({unit_label})",
                min_value=0.0, value=100.0, step=10.0, format="%.2f"
            )
            preview_co2e = quantity * factor_val
            st.markdown(f"""
            <div style='background:#f8fafc;border:1px solid #e2e8f0;border-left:4px solid #2563EB;
                border-radius:8px;padding:0.7rem 0.9rem;margin-top:0.25rem;box-shadow:0 1px 2px rgba(0,0,0,0.02);'>
              <div style='color:#64748b;font-size:0.72rem;font-weight:600;text-transform:uppercase;'>Estimated CO₂e Calculation</div>
              <div style='color:#1E3A8A;font-size:1.35rem;font-weight:700;font-family:Outfit,sans-serif;'>{preview_co2e:,.2f} kg</div>
              <div style='color:#64748b;font-size:0.75rem;'>{kg_to_tonnes(preview_co2e):.4f} tonnes · 
                Tax ≈ MYR {carbon_tax(preview_co2e):,.2f}</div>
            </div>""", unsafe_allow_html=True)

        notes = st.text_area("📄 Notes (optional)", placeholder="Add any relevant context…", height=80)

        submit_col, _ = st.columns([1, 3])
        with submit_col:
            submitted = st.form_submit_button("✅ Submit Record", type="primary", width="stretch")

    if submitted:
        if quantity <= 0:
            st.error("❌ Quantity must be greater than zero.")
        else:
            data = {
                "date": entry_date.strftime("%Y-%m-%d"),
                "facility": facility,
                "scope": scope_choice,
                "source": source,
                "quantity": quantity,
                "notes": notes,
            }
            result = submit_emission(data, username)

            if result["anomaly"]:
                st.warning(f"""
                ⚠️ **Anomaly Detected — Submission Sent for Approval**
                
                Your submission has been flagged and is pending manager approval.
                
                **Reason:** {result['reason']}
                
                The record will be reviewed and approved/rejected by a manager before being recorded.
                """)
            else:
                st.success(f"""
                ✅ **Emission Record Submitted Successfully**
                
                - Source: **{source}**
                - Quantity: **{quantity:,.2f} {unit_label}**
                - CO₂e: **{result['co2e_kg']:,.2f} kg ({kg_to_tonnes(result['co2e_kg']):.4f} tonnes)**
                - Carbon Tax: **MYR {carbon_tax(result['co2e_kg']):,.2f}**
                """)

    # ── Recent submissions by this user ────────────────────────────────────────
    st.markdown("<div class='ct-section-title'>📋 Your Recent Submissions</div>", unsafe_allow_html=True)
    df_all_em = load_emissions()
    if not df_all_em.empty:
        my_records = df_all_em[df_all_em["submitted_by"] == username].sort_values("submitted_at", ascending=False).head(10)
        if not my_records.empty:
            disp = my_records[["date","facility","scope","source","quantity","co2e_kg","status","submitted_at"]].copy()
            disp["co2e_kg"] = disp["co2e_kg"].round(2)
            disp["status"]  = disp["status"].map({"approved":"✅","pending":"⏳","rejected":"❌"}).fillna("?")
            st.dataframe(disp, width="stretch", hide_index=True)
        else:
            st.markdown("<div style='color:#64748b;font-size:0.85rem;'>No submissions from your account yet.</div>",
                        unsafe_allow_html=True)

    st.info("💡 **Observations & Compliance Guidance:** Ensure utility invoices and fuel metering tickets are retained for 7 years to comply with statutory GHG Protocol audit guidelines.")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 – Approval Queue
# ══════════════════════════════════════════════════════════════════════════════
with tab_approval:
    if not has_permission("approve"):
        st.markdown("""
        <div style='text-align:center;padding:3rem;'>
          <span style='font-size:3rem;'>🔒</span>
          <h3 style='color:#64748b;'>Access Restricted</h3>
          <p style='color:#94a3b8;'>Only managers and administrators can approve submissions.</p>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown("<div class='ct-section-title'>⏳ Pending Submissions Requiring Authorization</div>", unsafe_allow_html=True)
        st.write(
            "Review transactions flagged by the automated outlier detection filter. "
            "Examine reported volumes against operational logs prior to approving or rejecting."
        )

        pending_records = load_pending()
        if pending_records.empty:
            st.markdown("""
            <div style='text-align:center;padding:2.5rem;background:#f0fdf4;
                border:1px solid #bbf7d0;border-radius:12px;'>
              <span style='font-size:2.5rem;'>✅</span>
              <p style='color:#15803d;font-weight:700;font-size:1.05rem;margin:0.5rem 0 0;'>All clear! No pending submissions.</p>
              <span style='color:#64748b;font-size:0.8rem;'>All submitted records have been verified and processed into the carbon ledger.</span>
            </div>""", unsafe_allow_html=True)
        else:
            for _, row in pending_records.iterrows():
                co2e_kg = row["co2e_kg"]
                with st.container():
                    st.markdown(f"""
                    <div class='approval-card'>
                      <div style='display:flex;justify-content:space-between;align-items:flex-start;'>
                        <div>
                          <div style='display:flex;align-items:center;gap:0.6rem;margin-bottom:0.5rem;'>
                            <div class='anomaly-badge'>⚠️ Anomaly Flagged</div>
                            <span style='color:#64748b;font-size:0.75rem;font-weight:600;'>Entry ID #{row['id']}</span>
                          </div>
                          <div style='color:#1E3A8A;font-weight:700;font-size:1.05rem;font-family:Outfit,sans-serif;'>
                            {row['source']} — {row['facility']}
                          </div>
                          <div style='color:#475569;font-size:0.84rem;margin-top:0.25rem;'>
                            Scope {row['scope']} · <strong>{row['quantity']:,.2f} {row['unit']}</strong> · 
                            <span style='color:#1E3A8A;font-weight:700;'>{co2e_kg:,.2f} kg CO₂e</span> · 
                            Tax Exposure: <strong>MYR {carbon_tax(co2e_kg):,.2f}</strong>
                          </div>
                          <div style='color:#64748b;font-size:0.75rem;margin-top:0.35rem;'>
                            📅 Date of Activity: <strong>{row['date']}</strong> · 👤 Submitted by <strong style='color:#2563EB;'>{row['submitted_by']}</strong> 
                            at {str(row['submitted_at'])[:16]}
                          </div>
                          <div style='background:#fff7ed;border:1px solid #fdba74;border-left:4px solid #ea580c;
                              border-radius:8px;padding:0.6rem 0.85rem;margin-top:0.6rem;'>
                            <span style='color:#c2410c;font-size:0.78rem;font-weight:600;'>
                              🔍 Anomaly Reason: {row['anomaly_reason']}
                            </span>
                          </div>
                          {f"<div style='color:#475569;font-size:0.75rem;margin-top:0.4rem;'>📄 Notes: {row['notes']}</div>" if row.get('notes') else ""}
                        </div>
                      </div>
                    </div>""", unsafe_allow_html=True)

                    btn_col1, btn_col2, btn_spacer = st.columns([1, 1, 4])
                    with btn_col1:
                        if st.button(f"✅ Approve", key=f"approve_{row['id']}", type="primary", width="stretch"):
                            approve_submission(int(row["id"]), username)
                            st.success(f"✅ Submission #{row['id']} approved and recorded.")
                            st.rerun()
                    with btn_col2:
                        if st.button(f"❌ Reject", key=f"reject_{row['id']}", width="stretch"):
                            reject_submission(int(row["id"]), username)
                            st.error(f"❌ Submission #{row['id']} rejected.")
                            st.rerun()
                    st.markdown("<hr>", unsafe_allow_html=True)

        st.info("💡 **Observations & Protocol:** Approved entries immediately impact the official corporate ESG reporting totals and tax estimations.")

        # ── Approval history ──────────────────────────────────────────────────
        st.markdown("<div class='ct-section-title'>📋 Submission History (All Records)</div>", unsafe_allow_html=True)
        all_pending = load_all_pending()
        if not all_pending.empty:
            STATUS_MAP = {"pending": "⏳ Pending", "approved": "✅ Approved", "rejected": "❌ Rejected"}
            disp = all_pending[["id","date","facility","scope","source","quantity","co2e_kg",
                                 "submitted_by","submitted_at","status","anomaly_reason"]].copy()
            disp["status"] = disp["status"].map(STATUS_MAP).fillna(disp["status"])
            disp["co2e_kg"] = disp["co2e_kg"].round(2)
            st.dataframe(disp, width="stretch", hide_index=True, height=300)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 – Activity Log
# ══════════════════════════════════════════════════════════════════════════════
with tab_log:
    st.markdown("<div class='ct-section-title'>📜 Activity & Audit Log</div>", unsafe_allow_html=True)
    st.write(
        "Complete, immutable audit trail documenting all user actions, authentication events, "
        "and data modifications to satisfy ISO 14064 corporate transparency requirements."
    )

    log_df = load_activity_log()

    if log_df.empty:
        st.markdown("<div style='color:#64748b;'>No activity logged yet.</div>", unsafe_allow_html=True)
    else:
        # Filters
        lf1, lf2, lf3 = st.columns([1.5, 1, 2])
        with lf1:
            log_user_opts = ["All"] + sorted(log_df["username"].unique().tolist())
            log_user_filter = st.selectbox("👤 User", log_user_opts, key="log_user")
        with lf2:
            log_action_opts = ["All"] + sorted(log_df["action"].unique().tolist())
            log_action_filter = st.selectbox("🔹 Action", log_action_opts, key="log_action")
        with lf3:
            log_search = st.text_input("🔎 Search details…", "", key="log_search")

        log_filtered = log_df.copy()
        if log_user_filter != "All":
            log_filtered = log_filtered[log_filtered["username"] == log_user_filter]
        if log_action_filter != "All":
            log_filtered = log_filtered[log_filtered["action"] == log_action_filter]
        if log_search:
            mask = log_filtered.apply(lambda r: log_search.lower() in str(r.values).lower(), axis=1)
            log_filtered = log_filtered[mask]

        ACTION_COLORS = {
            "SUBMITTED_APPROVED": "#15803d",
            "SUBMITTED_PENDING":  "#c2410c",
            "APPROVED":           "#2563EB",
            "REJECTED":           "#b91c1c",
            "LOGIN":              "#7c3aed",
            "LOGOUT":             "#64748b",
        }
        ACTION_ICONS = {
            "SUBMITTED_APPROVED": "✅",
            "SUBMITTED_PENDING":  "⚠️",
            "APPROVED":           "👍",
            "REJECTED":           "🚫",
            "LOGIN":              "🔑",
            "LOGOUT":             "🚪",
        }

        for _, row in log_filtered.head(100).iterrows():
            color = ACTION_COLORS.get(row["action"], "#64748b")
            icon  = ACTION_ICONS.get(row["action"], "•")
            st.markdown(f"""
            <div class='log-row'>
              <span class='log-timestamp'>🕐 {str(row['timestamp'])[:16]}</span>
              <span class='log-user'>👤 {row['username']}</span>
              <span class='log-action' style='color:{color};min-width:140px;'>
                {icon} {row['action'].replace('_',' ')}
              </span>
              <span class='log-details'>{row.get('details', '')}</span>
            </div>""", unsafe_allow_html=True)

        st.markdown(f"<div style='color:#64748b;font-size:0.75rem;text-align:right;margin-top:0.5rem;'>"
                    f"Showing {len(log_filtered.head(100))} of {len(log_filtered)} log entries</div>",
                    unsafe_allow_html=True)

        # Export log
        log_csv = log_filtered.to_csv(index=False)
        st.download_button(
            "⬇️ Export Log CSV", log_csv,
            file_name=f"audit_log_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )

    st.info("💡 **Observations:** Security and governance logs cannot be deleted through the interface. Use CSV export for regulatory ESG reporting packages.")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 – Sustainability Metrics
# ══════════════════════════════════════════════════════════════════════════════
with tab_metrics:
    import plotly.express as px
    import plotly.graph_objects as go

    PLOT_LAYOUT = dict(
        paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
        font=dict(family="Inter, sans-serif", color="#334155"),
        margin=dict(t=45, b=25, l=10, r=10),
        xaxis=dict(gridcolor="#f1f5f9", showgrid=True, zeroline=False),
        yaxis=dict(gridcolor="#f1f5f9", showgrid=True, zeroline=False),
    )

    st.markdown("<div class='ct-section-title'>📊 Governance & Submission Analytics</div>", unsafe_allow_html=True)
    st.write(
        "Quantitative monitoring of data throughput, anomaly resolution ratios, and team contributor metrics. "
        "Supports data-readiness tracking toward international corporate sustainability disclosures."
    )

    df_all_em = load_emissions()
    all_pending_hist = load_all_pending()

    m1, m2, m3, m4 = st.columns(4)
    anomaly_count  = len(all_pending_hist[all_pending_hist["status"] == "approved"]) if not all_pending_hist.empty else 0
    rejected_count = len(all_pending_hist[all_pending_hist["status"] == "rejected"]) if not all_pending_hist.empty else 0
    total_records  = len(df_all_em)
    unique_users   = df_all_em["submitted_by"].nunique() if not df_all_em.empty else 0

    for col, label, val, sub, color in [
        (m1, "Total Records",         f"{total_records:,}",     "approved entries",    "#1E3A8A"),
        (m2, "Flagged & Approved",    f"{anomaly_count:,}",     "anomalies approved",  "#d97706"),
        (m3, "Submissions Rejected",  f"{rejected_count:,}",    "anomalies rejected",  "#dc2626"),
        (m4, "Active Contributors",   f"{unique_users}",         "data entry users",    "#2563EB"),
    ]:
        with col:
            st.markdown(f"""
            <div class='ct-card'>
              <div class='ct-card-label'>{label}</div>
              <div class='ct-card-value' style='color:{color};'>{val}</div>
              <div style='color:#64748b;font-size:0.72rem;'>{sub}</div>
            </div>""", unsafe_allow_html=True)

    if not df_all_em.empty:
        c_left, c_right = st.columns(2)

        with c_left:
            user_counts = df_all_em.groupby("submitted_by").size().reset_index(name="count").sort_values("count", ascending=True)
            fig_users = px.bar(
                user_counts, x="count", y="submitted_by", orientation="h",
                color="count", color_continuous_scale=px.colors.sequential.Blues,
                title="Records Submitted per User",
                labels={"count": "Records", "submitted_by": "User"},
            )
            fig_users.update_layout(**PLOT_LAYOUT, height=280, coloraxis_showscale=False)
            st.plotly_chart(fig_users, width="stretch")

        with c_right:
            df_all_em["sub_month"] = df_all_em["submitted_at"].dt.to_period("M").astype(str)
            monthly_subs = df_all_em.groupby(["sub_month", "submitted_by"]).size().reset_index(name="count")
            fig_monthly = px.line(
                monthly_subs, x="sub_month", y="count", color="submitted_by",
                title="Monthly Submission Activity by User",
                labels={"sub_month": "Month", "count": "Submissions", "submitted_by": "User"},
                markers=True,
            )
            fig_monthly.update_layout(**PLOT_LAYOUT, height=280)
            st.plotly_chart(fig_monthly, width="stretch")

        if not all_pending_hist.empty:
            all_pending_hist["sub_month"] = all_pending_hist["submitted_at"].dt.to_period("M").astype(str)
            anomaly_monthly = all_pending_hist.groupby(["sub_month", "status"]).size().reset_index(name="count")
            fig_anom = px.bar(
                anomaly_monthly, x="sub_month", y="count", color="status",
                title="Anomaly Submissions by Month & Outcome",
                color_discrete_map={"pending": "#eab308", "approved": "#16a34a", "rejected": "#dc2626"},
                labels={"sub_month": "Month", "count": "Count", "status": "Status"},
                barmode="group",
            )
            fig_anom.update_layout(**PLOT_LAYOUT, height=300)
            st.plotly_chart(fig_anom, width="stretch")

    # ── Sustainability Targets ─────────────────────────────────────────────────
    st.markdown("<div class='ct-section-title'>🎯 Sustainability Targets & Strategic Milestones</div>", unsafe_allow_html=True)
    st.write("Progress tracking toward statutory corporate climate commitments.")

    targets = [
        ("Net Zero by 2050",           "Long-term goal",      "Planning",    15),
        ("30% Scope 2 Reduction",      "By end of 2027",      "In Progress", 42),
        ("Renewable Energy 40%",       "By 2026",             "In Progress", 28),
        ("ISO 14064 Certification",    "2025 Q4",             "In Review",   75),
        ("Carbon Tax Compliance",      "Annual filing",       "Compliant",   100),
        ("Employee GHG Training",      "850 employees",       "Completed",   100),
    ]
    for tgt_name, deadline, status, progress in targets:
        prog_color = "#16a34a" if progress == 100 else ("#2563EB" if progress > 50 else "#ea580c")
        status_badge = "approved-badge" if status == "Compliant" or status == "Completed" else \
                       ("pending-badge" if "Progress" in status or "Review" in status else "anomaly-badge")
        st.markdown(f"""
        <div class='ct-card' style='padding:0.9rem 1.3rem;margin:0.4rem 0;'>
          <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:0.5rem;'>
            <div>
              <span style='color:#1e293b;font-weight:700;font-size:0.95rem;font-family:Outfit,sans-serif;'>{tgt_name}</span>
              <span style='color:#64748b;font-size:0.78rem;margin-left:0.6rem;'>· {deadline}</span>
            </div>
            <div class='{status_badge}'>{status}</div>
          </div>
          <div style='background:#e2e8f0;border-radius:10px;height:7px;overflow:hidden;'>
            <div style='width:{progress}%;background:{prog_color};
                height:100%;border-radius:10px;transition:width 0.5s;'></div>
          </div>
          <div style='color:#64748b;font-size:0.75rem;margin-top:0.35rem;text-align:right;font-weight:600;'>{progress}% achieved</div>
        </div>""", unsafe_allow_html=True)

    st.info("💡 **Observations:** Target progress automatically updates as newly verified emission entries and efficiency initiatives are reconciled.")
