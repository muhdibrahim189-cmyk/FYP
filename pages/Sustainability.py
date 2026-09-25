"""
Page 4 – Sustainability
Data entry, anomaly detection, approval workflow, activity log, audit trail.

Everything on this page works on the operational SQLite ledger (where data
entry lands), not on the read-only workbook used by the analytics pages.
"""
import logging
import sqlite3
from datetime import date, datetime
from html import escape

import pandas as pd
import streamlit as st

from data.emission_factors import ALL_FACTORS, COMPANIES, SCOPE1_SOURCES, SCOPE2_SOURCES
from utils.analytics import search_rows, to_safe_csv
from utils.auth import current_username, has_permission
from utils.carbon_calculator import carbon_tax, kg_to_tonnes
from utils.config import ACTIVITY_LOG_DISPLAY_LIMIT, ALL_OPTION, RECENT_SUBMISSIONS_LIMIT, STATUS_LABELS
from utils.data_manager import (
    approve_submission, load_activity_log, load_all_pending, load_database_emissions,
    load_pending, reject_submission, submit_emission,
)
from utils.ui import Page

logger = logging.getLogger(__name__)

SUBMISSION_STATUS_ICONS = {"approved": "✅", "pending": "⏳", "rejected": "❌"}
ACTION_STYLES = {                       # action -> (colour, icon)
    "SUBMITTED_APPROVED": ("var(--ct-ok-text)", "✅"),
    "SUBMITTED_PENDING":  ("var(--ct-alert-text)", "⚠️"),
    "APPROVED":           ("#2563EB", "👍"),
    "REJECTED":           ("#b91c1c", "🚫"),
    "LOGIN":              ("#7c3aed", "🔑"),
    "LOGOUT":             ("var(--ct-muted)", "🚪"),
}
DEFAULT_ACTION_STYLE = ("var(--ct-muted)", "•")


class Sustainability(Page):
    name = "Sustainability"
    icon = "♻️"
    nav_label = "Sustainability"

    def render(self) -> None:
        self.username = current_username()
        self.can_approve = has_permission("approve")
        self.pending_records = load_pending()
        if not self.pending_records.empty and self.can_approve:
            st.markdown(f"""
            <div style='background:var(--ct-warn-bg);border:1px solid var(--ct-warn-border);border-left:4px solid #ca8a04;
                border-radius:10px;padding:0.75rem 1.1rem;margin-bottom:1.2rem;display:flex;align-items:center;gap:0.8rem;'>
              <span style='font-size:1.3rem;'>⚠️</span>
              <div>
                <span style='color:var(--ct-warn-text);font-weight:700;'>{len(self.pending_records)} submission(s) awaiting your approval</span>
                <div style='color:var(--ct-warn-text-soft);font-size:0.8rem;'>Review and authorize or reject flagged entries in the Approval Queue tab below.</div>
              </div>
            </div>""", unsafe_allow_html=True)

        tab_entry, tab_approval, tab_log = st.tabs(["Data Entry", "Approval Queue", "Activity Log"])
        with tab_entry:
            self.render_entry_tab()
        with tab_approval:
            self.render_approval_tab()
        with tab_log:
            self.render_log_tab()

    # ── TAB 1 – Data Entry ──────────────────────────────────────────────────────
    @staticmethod
    def render_co2e_preview(co2e_kg: float) -> None:
        st.markdown(f"""
        <div style='background:var(--ct-surface-alt);border:1px solid var(--ct-border);border-left:4px solid #2563EB;
            border-radius:8px;padding:0.7rem 0.9rem;margin-top:0.25rem;box-shadow:0 1px 2px rgba(0,0,0,0.02);'>
          <div style='color:var(--ct-muted);font-size:0.72rem;font-weight:600;text-transform:uppercase;'>Estimated CO₂e Calculation</div>
          <div style='color:var(--ct-heading);font-size:1.35rem;font-weight:700;font-family:Outfit,sans-serif;'>{co2e_kg:,.2f} kg</div>
          <div style='color:var(--ct-muted);font-size:0.75rem;'>{kg_to_tonnes(co2e_kg):.4f} tonnes ·
            Tax ≈ MYR {carbon_tax(co2e_kg):,.2f}</div>
        </div>""", unsafe_allow_html=True)

    def handle_submission(self, data: dict, unit_label: str) -> None:
        try:
            result = submit_emission(data, self.username)
        except ValueError as exc:
            st.error(f"❌ {exc}")
            return
        except sqlite3.Error:
            logger.exception("Could not save emission submission")
            st.error("❌ The record could not be saved. Please try again.")
            return

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

            - Source: **{data['source']}**
            - Quantity: **{data['quantity']:,.2f} {unit_label}**
            - CO₂e: **{result['co2e_kg']:,.2f} kg ({kg_to_tonnes(result['co2e_kg']):.4f} tonnes)**
            - Carbon Tax: **MYR {carbon_tax(result['co2e_kg']):,.2f}**
            """)

    def render_recent_submissions(self) -> None:
        self.section_title("📋 Your Recent Submissions")
        ledger = load_database_emissions()
        mine = ledger[ledger["submitted_by"] == self.username] if not ledger.empty else ledger
        if mine.empty:
            self.muted_text("No submissions from your account yet.")
            return
        recent = mine.sort_values("submitted_at", ascending=False).head(RECENT_SUBMISSIONS_LIMIT)
        table = recent[["date", "facility", "scope", "source", "quantity", "co2e_kg", "status", "submitted_at"]].copy()
        table["co2e_kg"] = table["co2e_kg"].round(2)
        table["status"] = table["status"].map(SUBMISSION_STATUS_ICONS).fillna("?")
        st.dataframe(table, width="stretch", hide_index=True)

    def render_entry_tab(self) -> None:
        self.section_title("📝 Submit New Emission Record")
        st.write(
            "Standardized GHG emission logging interface. Submissions are dynamically benchmarked against facility baselines. "
            "Inputs deviating significantly from historical distributions are intercepted for managerial verification."
        )
        st.markdown("""
        <div style='background:var(--ct-info-bg);border:1px solid var(--ct-info-border);border-left:4px solid #2563EB;
            border-radius:10px;padding:0.85rem 1.1rem;margin-bottom:1.2rem;color:var(--ct-text-body);font-size:0.84rem;'>
        ℹ️ <strong>Validation Protocol:</strong> All entries are automatically scored against historical standard deviations.
        Outlier quantities will be <strong style='color:var(--ct-alert-text);'>flagged as potential anomalies</strong> and routed to an authorized supervisor for audit sign-off.
        </div>""", unsafe_allow_html=True)

        # Not wrapped in st.form: the source list and CO₂e preview must react to
        # the scope/source/quantity choices as they change.
        col1, col2 = st.columns(2)
        with col1:
            entry_date = st.date_input("Emission Date", value=date.today(), max_value=date.today(), key="entry_date")
            facility = st.selectbox("Company", COMPANIES, key="entry_facility")
            scope_choice = st.radio("Scope", [1, 2], horizontal=True, key="entry_scope",
                                    format_func=lambda x: f"Scope {x} ({'Direct' if x == 1 else 'Indirect'})")
        with col2:
            sources = SCOPE1_SOURCES if scope_choice == 1 else SCOPE2_SOURCES
            source = st.selectbox("Emission Source", sources, key=f"entry_source_{scope_choice}")
            unit_label = ALL_FACTORS[source]["unit"]
            quantity = st.number_input(f"Quantity ({unit_label})", min_value=0.0, value=100.0,
                                       step=10.0, format="%.2f", key="entry_quantity")
            self.render_co2e_preview(quantity * ALL_FACTORS[source]["factor"])

        notes = st.text_area("Notes (optional)", placeholder="Add any relevant context…", height=80, key="entry_notes")

        submit_col, _ = st.columns([1, 3])
        with submit_col:
            submitted = st.button("✅ Submit Record", type="primary", width="stretch", key="entry_submit")

        if submitted:
            if quantity <= 0:
                st.error("❌ Quantity must be greater than zero.")
            else:
                self.handle_submission({
                    "date": entry_date.strftime("%Y-%m-%d"),
                    "facility": facility,
                    "scope": scope_choice,
                    "source": source,
                    "quantity": quantity,
                    "notes": notes,
                }, unit_label)

        self.render_recent_submissions()
        self.observation("Ensure utility invoices and fuel metering tickets are retained for 7 years to comply with statutory GHG Protocol audit guidelines.", title="Observations & Compliance Guidance")

    # ── TAB 2 – Approval Queue ──────────────────────────────────────────────────
    @staticmethod
    def render_pending_card(row: pd.Series) -> None:
        notes_html = (
            f"<div style='color:var(--ct-text-soft);font-size:0.75rem;margin-top:0.4rem;'>📄 Notes: {escape(str(row['notes']))}</div>"
            if row.get("notes") else ""
        )
        st.markdown(f"""
        <div class='approval-card'>
          <div style='display:flex;align-items:center;gap:0.6rem;margin-bottom:0.5rem;'>
            <div class='anomaly-badge'>⚠️ Anomaly Flagged</div>
            <span style='color:var(--ct-muted);font-size:0.75rem;font-weight:600;'>Entry ID #{int(row['id'])}</span>
          </div>
          <div style='color:var(--ct-heading);font-weight:700;font-size:1.05rem;font-family:Outfit,sans-serif;'>
            {escape(str(row['source']))} — {escape(str(row['facility']))}
          </div>
          <div style='color:var(--ct-text-soft);font-size:0.84rem;margin-top:0.25rem;'>
            Scope {int(row['scope'])} · <strong>{row['quantity']:,.2f} {escape(str(row['unit']))}</strong> ·
            <span style='color:var(--ct-heading);font-weight:700;'>{row['co2e_kg']:,.2f} kg CO₂e</span> ·
            Tax Exposure: <strong>MYR {carbon_tax(row['co2e_kg']):,.2f}</strong>
          </div>
          <div style='color:var(--ct-muted);font-size:0.75rem;margin-top:0.35rem;'>
            📅 Date of Activity: <strong>{escape(str(row['date']))}</strong> · 👤 Submitted by
            <strong style='color:#2563EB;'>{escape(str(row['submitted_by']))}</strong>
            at {escape(str(row['submitted_at'])[:16])}
          </div>
          <div style='background:var(--ct-alert-bg);border:1px solid var(--ct-alert-border);border-left:4px solid #ea580c;
              border-radius:8px;padding:0.6rem 0.85rem;margin-top:0.6rem;'>
            <span style='color:var(--ct-alert-text);font-size:0.78rem;font-weight:600;'>
              🔍 Anomaly Reason: {escape(str(row['anomaly_reason']))}
            </span>
          </div>
          {notes_html}
        </div>""", unsafe_allow_html=True)

    def render_pending_actions(self, record_id: int) -> None:
        approve_col, reject_col, _ = st.columns([1, 1, 4])
        with approve_col:
            if st.button("✅ Approve", key=f"approve_{record_id}", type="primary", width="stretch"):
                approve_submission(record_id, self.username)
                st.rerun()
        with reject_col:
            if st.button("❌ Reject", key=f"reject_{record_id}", width="stretch"):
                reject_submission(record_id, self.username)
                st.rerun()

    def render_approval_tab(self) -> None:
        if not self.can_approve:
            st.markdown("""
            <div style='text-align:center;padding:3rem;'>
              <span style='font-size:3rem;'>🔒</span>
              <h3 style='color:var(--ct-muted);'>Access Restricted</h3>
              <p style='color:#94a3b8;'>Only managers and administrators can approve submissions.</p>
            </div>""", unsafe_allow_html=True)
            return

        self.section_title("⏳ Pending Submissions Requiring Authorization")
        st.write(
            "Review transactions flagged by the automated outlier detection filter. "
            "Examine reported volumes against operational logs prior to approving or rejecting."
        )
        if self.pending_records.empty:
            st.markdown("""
            <div style='text-align:center;padding:2.5rem;background:var(--ct-ok-bg);
                border:1px solid var(--ct-ok-border-soft);border-radius:12px;'>
              <span style='font-size:2.5rem;'>✅</span>
              <p style='color:var(--ct-ok-text);font-weight:700;font-size:1.05rem;margin:0.5rem 0 0;'>All clear! No pending submissions.</p>
              <span style='color:var(--ct-muted);font-size:0.8rem;'>All submitted records have been verified and processed into the carbon ledger.</span>
            </div>""", unsafe_allow_html=True)
        else:
            for _, row in self.pending_records.iterrows():
                self.render_pending_card(row)
                self.render_pending_actions(int(row["id"]))
                st.markdown("<hr>", unsafe_allow_html=True)

        self.observation("Approved entries immediately impact the official corporate ESG reporting totals and tax estimations.", title="Observations & Protocol")

        self.section_title("📋 Submission History (All Records)")
        history = load_all_pending()
        if not history.empty:
            table = history[["id", "date", "facility", "scope", "source", "quantity", "co2e_kg",
                             "submitted_by", "submitted_at", "status", "anomaly_reason"]].copy()
            table["status"] = table["status"].map(STATUS_LABELS).fillna(table["status"])
            table["co2e_kg"] = table["co2e_kg"].round(2)
            st.dataframe(table, width="stretch", hide_index=True, height=300)

    # ── TAB 3 – Activity Log ────────────────────────────────────────────────────
    @staticmethod
    def render_log_row(row: pd.Series) -> None:
        color, icon = ACTION_STYLES.get(row["action"], DEFAULT_ACTION_STYLE)
        st.markdown(f"""
        <div class='log-row'>
          <span class='log-timestamp'>🕐 {escape(str(row['timestamp'])[:16])}</span>
          <span class='log-user'>👤 {escape(str(row['username']))}</span>
          <span class='log-action' style='color:{color};'>{icon} {escape(row['action'].replace('_', ' '))}</span>
          <span class='log-details'>{escape(str(row.get('details') or ''))}</span>
        </div>""", unsafe_allow_html=True)

    def render_log_tab(self) -> None:
        self.section_title("📜 Activity & Audit Log")
        st.write(
            "Complete, immutable audit trail documenting all user actions, authentication events, "
            "and data modifications to satisfy ISO 14064 corporate transparency requirements."
        )
        log_df = load_activity_log()
        if log_df.empty:
            self.muted_text("No activity logged yet.", size="1rem")
        else:
            lf1, lf2, lf3 = st.columns([1.5, 1, 2])
            with lf1:
                user_filter = st.selectbox("👤 User", [ALL_OPTION] + sorted(log_df["username"].unique().tolist()),
                                           key="log_user")
            with lf2:
                action_filter = st.selectbox("🔹 Action", [ALL_OPTION] + sorted(log_df["action"].unique().tolist()),
                                             key="log_action")
            with lf3:
                log_search = st.text_input("🔎 Search details…", "", key="log_search")

            filtered = log_df
            if user_filter != ALL_OPTION:
                filtered = filtered[filtered["username"] == user_filter]
            if action_filter != ALL_OPTION:
                filtered = filtered[filtered["action"] == action_filter]
            filtered = search_rows(filtered, log_search)

            shown = filtered.head(ACTIVITY_LOG_DISPLAY_LIMIT)
            for _, row in shown.iterrows():
                self.render_log_row(row)
            st.markdown(f"<div style='color:var(--ct-muted);font-size:0.75rem;text-align:right;margin-top:0.5rem;'>"
                        f"Showing {len(shown)} of {len(filtered)} log entries</div>", unsafe_allow_html=True)

            st.download_button(
                "⬇️ Export Log CSV", to_safe_csv(filtered),
                file_name=f"audit_log_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
            )

        self.observation("Security and governance logs cannot be deleted through the interface. Use CSV export for regulatory ESG reporting packages.")


Sustainability().run()
