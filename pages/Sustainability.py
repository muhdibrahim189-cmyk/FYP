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

from data.emission_factors import (
    ALL_FACTORS, COMPANIES, ENERGY_SCOPE, ENERGY_SOURCES, SCOPE1_SOURCES, SCOPE2_SOURCES, UNIT_NAMES,
)
from utils.analytics import search_rows, to_safe_csv
from utils.auth import current_user, current_username, has_permission, own_rows
from utils.carbon_calculator import carbon_tax, kg_to_tonnes
from utils.charts import BLUE
from utils.config import ACTIVITY_LOG_DISPLAY_LIMIT, ALL_OPTION, RECENT_SUBMISSIONS_LIMIT, STATUS_LABELS
from utils.data_manager import (
    approve_submission, load_activity_log, load_all_pending, load_database_emissions,
    load_pending, reject_submission, submit_emission, withdraw_submission,
)
from utils.ui import Page, two_decimals

logger = logging.getLogger(__name__)

SUBMISSION_STATUS_ICONS = {"approved": "✅", "pending": "⏳", "rejected": "❌"}
ACTION_STYLES = {                       # action -> (colour, icon)
    "SUBMITTED_APPROVED": ("var(--ct-ok-text)", "✅"),
    "SUBMITTED_PENDING":  ("var(--ct-alert-text)", "⚠️"),
    "APPROVED":           ("#2563EB", "👍"),
    "REJECTED":           ("#b91c1c", "🚫"),
    "WITHDRAWN":          ("var(--ct-muted)", "↩️"),
    "LOGIN":              ("#7c3aed", "🔑"),
    "LOGOUT":             ("var(--ct-muted)", "🚪"),
}
DEFAULT_ACTION_STYLE = ("var(--ct-muted)", "•")
# Entry types: scope -> (label, sources). Power consumption is activity data with no CO₂e.
ENTRY_TYPES = {
    1: ("Scope 1 (Direct)", SCOPE1_SOURCES),
    2: ("Scope 2 (Indirect)", SCOPE2_SOURCES),
    ENERGY_SCOPE: ("Power Consumption", ENERGY_SOURCES),
}


class Sustainability(Page):
    name = "Sustainability"
    nav_label = "Sustainability"

    def render(self) -> None:
        self.username = current_username()
        self.can_approve = has_permission("approve")
        self.pending_records = own_rows(load_pending())
        if not self.pending_records.empty and self.can_approve:
            st.warning(f"**{len(self.pending_records)} submission(s) awaiting your approval**  \n"
                       "Review and authorize or reject flagged entries in the Approval Queue tab below.", icon="⚠️")

        tab_entry, tab_approval, tab_log = st.tabs(["Data Entry", "Approval Queue", "Activity Log"])
        with tab_entry:
            self.render_entry_tab()
        with tab_approval:
            self.render_approval_tab()
        with tab_log:
            self.render_log_tab()

    # ── TAB 1 – Data Entry ──────────────────────────────────────────────────────
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

            Your submission has been flagged and is pending approval.

            **Reason:** {result['reason']}

            Review it in the Approval Queue tab: it is recorded only once approved.
            """)
        elif data["scope"] == ENERGY_SCOPE:
            st.success(f"✅ **Power consumption recorded:** {data['quantity']:,.2f} {unit_label} "
                       f"for {data['facility']}.")
        else:
            st.success(f"""
            ✅ **Emission Record Submitted Successfully**

            - Source: **{data['source']}**
            - Quantity: **{data['quantity']:,.2f} {unit_label}**
            - CO₂e: **{result['co2e_kg']:,.2f} kg ({kg_to_tonnes(result['co2e_kg']):,.2f} tonnes)**
            - Carbon Tax: **MYR {carbon_tax(result['co2e_kg']):,.2f}**
            """)

    def render_recent_submissions(self) -> None:
        self.section_title("📋 Your Recent Submissions (Table)")
        ledger = load_database_emissions()
        mine = ledger[ledger["submitted_by"] == self.username] if not ledger.empty else ledger
        if mine.empty:
            self.muted_text("No submissions from your account yet.")
            return
        recent = mine.sort_values("submitted_at", ascending=False).head(RECENT_SUBMISSIONS_LIMIT)
        table = recent[["id", "date", "facility", "scope", "source", "quantity", "co2e_kg", "status",
                        "submitted_at"]].reset_index(drop=True)
        table["status"] = table["status"].map(SUBMISSION_STATUS_ICONS).fillna("?")
        self.muted_text("Submitted something by mistake? Select its row, then click Undo.")
        # A new key after each undo clears the selection, so the next row is not selected for undo.
        event = st.dataframe(two_decimals(table, ["quantity", "co2e_kg"]), width="stretch", hide_index=True,
                             on_select="rerun", selection_mode="single-row",
                             key=f"recent_submissions_{st.session_state.get('undo_count', 0)}")
        if not event.selection.rows:
            return
        row = table.iloc[event.selection.rows[0]]
        st.button(f"↩️ Undo entry #{row['id']}: {row['source']}, {row['facility']} {row['date']:%Y-%m-%d} "
                  f"({row['quantity']:,.2f})", key="undo_submission",
                  on_click=self.undo_submission, args=(int(row["id"]),))

    def undo_submission(self, record_id: int) -> None:
        """Button callback: runs before the rerun, so its toast is not lost."""
        if withdraw_submission(record_id, self.username):
            st.session_state["undo_count"] = st.session_state.get("undo_count", 0) + 1
            st.toast(f"Entry #{record_id} withdrawn. It no longer counts in any total.", icon="↩️")
        else:
            st.toast("That entry could not be undone (it may already have been withdrawn).", icon="❌")

    def render_entry_tab(self) -> None:
        if not has_permission("submit"):
            self.restricted("Emission data is entered by each company (and the IT team).")
            return
        self.section_title("📝 Submit New Emission Record")
        st.write(
            "Standardized GHG emission logging interface. Submissions are dynamically benchmarked against historical baselines. "
            "Inputs deviating significantly from historical distributions are held for verification in the Approval Queue."
        )
        st.info("**Validation Protocol:** All entries are automatically scored against historical standard deviations. "
                "Outlier quantities will be **flagged as potential anomalies** and routed to the Approval Queue "
                "for sign-off.", icon="ℹ️")

        # Not wrapped in st.form: the source list and CO₂e preview must react to
        # the scope/source/quantity choices as they change.
        col1, col2 = st.columns(2)
        with col1:
            entry_date = st.date_input("Activity Date", value=date.today(), max_value=date.today(), key="entry_date",
                                       help="One entry per source per company per month; a second one for the "
                                            "same month is flagged as a duplicate.")
            # A company user can only enter data for their own company.
            own_company = current_user().get("company")
            facility = st.selectbox("Company", [own_company] if own_company else COMPANIES, key="entry_facility")
            scope_choice = st.radio("Entry Type", list(ENTRY_TYPES), horizontal=True, key="entry_scope",
                                    format_func=lambda x: ENTRY_TYPES[x][0])
        with col2:
            source = st.selectbox("Source", ENTRY_TYPES[scope_choice][1], key=f"entry_source_{scope_choice}")
            unit_label = ALL_FACTORS[source]["unit"]
            quantity = st.number_input(f"Quantity ({unit_label})", min_value=0.0, value=100.0,
                                       step=10.0, format="%.2f", key="entry_quantity",
                                       help=f"Unit: {UNIT_NAMES[unit_label]}")
            if scope_choice == ENERGY_SCOPE:
                st.info("Activity data: no CO₂e of its own. It is the energy behind the STIRPAT "
                        "energy-intensity driver (T = energy ÷ production).")
            else:
                co2e_kg = quantity * ALL_FACTORS[source]["factor"]
                self.highlight_box("Estimated CO₂e Calculation", f"{co2e_kg:,.2f} kg",
                                   f"{kg_to_tonnes(co2e_kg):,.2f} tonnes · Tax ≈ MYR {carbon_tax(co2e_kg):,.2f}", BLUE)

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
          <div style='color:var(--ct-heading);font-weight:700;font-size:1.05rem;font-family:Poppins,sans-serif;'>
            {escape(str(row['source']))} — {escape(str(row['facility']))}
          </div>
          <div style='color:var(--ct-text-soft);font-size:0.84rem;margin-top:0.25rem;'>
            {escape(ENTRY_TYPES.get(int(row['scope']), (f"Scope {int(row['scope'])}",))[0])} · <strong>{row['quantity']:,.2f} {escape(str(row['unit']))}</strong> ·
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
        self.section_title("⏳ Pending Submissions Requiring Authorization")
        st.write(
            "Review transactions flagged by the automated outlier detection filter. "
            "Examine reported volumes against operational logs prior to approving or rejecting."
        )
        if not self.can_approve:
            self.muted_text("View only: each company verifies its own flagged entries.")
        if self.pending_records.empty:
            st.success("**All clear! No pending submissions.**  \n"
                       "All submitted records have been verified and processed into the carbon ledger.")
        else:
            for _, row in self.pending_records.iterrows():
                self.render_pending_card(row)
                if self.can_approve:
                    self.render_pending_actions(int(row["id"]))
                st.markdown("<hr>", unsafe_allow_html=True)

        self.observation("Approved entries immediately impact the official corporate ESG reporting totals and tax estimations.", title="Observations & Protocol")

        self.section_title("📋 Submission History – All Records (Table)")
        history = own_rows(load_all_pending())
        if not history.empty:
            table = history[["id", "date", "facility", "scope", "source", "quantity", "co2e_kg",
                             "submitted_by", "submitted_at", "status", "anomaly_reason"]].copy()
            table["status"] = table["status"].map(STATUS_LABELS).fillna(table["status"])
            st.dataframe(two_decimals(table, ["quantity", "co2e_kg"]), width="stretch", hide_index=True, height=300)

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
        if not has_permission("audit_log"):
            self.restricted("The activity and audit log is managed by the IT team.")
            return
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
            self.muted_text(f"Showing {len(shown)} of {len(filtered)} log entries", size="0.75rem", align="right")

            st.download_button(
                "⬇️ Export Log CSV", to_safe_csv(filtered),
                file_name=f"audit_log_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
            )

        self.observation("Security and governance logs cannot be deleted through the interface. Use CSV export for regulatory ESG reporting packages.")


Sustainability().run()
