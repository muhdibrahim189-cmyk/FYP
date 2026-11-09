"""
Page 3 – Data Centre
Every ledger entry (the workbook's reported figures plus data-entry
submissions) with filtering, search and export, and the monthly summary.
"""
import math
from datetime import datetime

import pandas as pd
import streamlit as st

from data.emission_factors import CARBON_TAX_RATE_MYR, ENERGY_SCOPE, company_display_name
from utils.analytics import filter_emissions, monthly_ledger_summary, scope_totals, search_rows, to_safe_csv
from utils.auth import has_permission, own_rows
from utils.carbon_calculator import KG_PER_MT, KG_PER_TONNE, carbon_tax, share_pct
from utils.charts import AMBER, BLUE, HEADING, RED
from utils.config import DATA_TABLE_PAGE_SIZE, STATUS_LABELS
from utils.data_manager import load_database_emissions
from utils.report import PERIODS, build_statement, statement_months
from utils.ui import Page, two_decimals

PAGE_KEY = "dc_page"
SCOPE_LABELS = {1: "Scope 1", 2: "Scope 2", ENERGY_SCOPE: "Power Consumption"}
DISPLAY_COLUMNS = {
    "id": "ID", "date": "Date", "facility": "Company",
    "scope": "Scope", "source": "Source", "unit": "Unit",
    "quantity": "Quantity", "co2e_kg": "CO₂e (t)",
    "submitted_by": "Submitted By", "submitted_at": "Submitted At",
    "status": "Status", "approved_by": "Approved By",
    "is_anomaly": "Anomaly Flag",
}
EXPORT_COLUMNS = (
    "id", "date", "facility", "scope", "source", "unit", "quantity",
    "co2e_kg", "co2e_tonnes", "carbon_tax_myr",
    "submitted_by", "submitted_at", "status", "approved_by", "approved_at",
    "notes", "is_anomaly",
)


class DataCentre(Page):
    name = "Data Centre"
    nav_label = "Data Centre"
    header = (
        " Emission Data Repository",
        "Complete Historical Emission Ledger · Interactive Multidimensional Filtering · Audit-Ready Data Export",
    )

    def render(self) -> None:
        self.df_raw = self.stop_if_empty(own_rows(load_database_emissions()), "No data found in the database.")
        self.df = self.render_filters()
        self.render_stats()

        tab_data, tab_export = st.tabs(["Data Table", "Export"])
        with tab_data:
            self.render_data_tab()
        with tab_export:
            self.render_export_tab()

    # ── Filters ────────────────────────────────────────────────────────────────
    def render_filters(self) -> pd.DataFrame:
        df_raw = self.df_raw
        self.section_title("🔍 Filters")
        f1, f2, f3, f4, f5 = st.columns([1.5, 1, 1, 1.5, 1])
        with f1:
            min_date = df_raw["date"].min().date()
            max_date = df_raw["date"].max().date()
            date_range = st.date_input("Date Range", value=(min_date, max_date),
                                       min_value=min_date, max_value=max_date, key="dc_date")
        # Dropdowns of checkboxes (all ticked by default) that float over the page.
        with f2:
            scope_filter = self.checkbox_filter("Scope", list(SCOPE_LABELS), "dc_scope",
                                                format_func=SCOPE_LABELS.get, dropdown=True)
        with f3:
            source_filter = self.checkbox_filter("Source", sorted(df_raw["source"].unique()), "dc_source",
                                                 dropdown=True)
        with f4:
            facility_filter = self.checkbox_filter("Company", sorted(df_raw["facility"].unique()), "dc_fac",
                                                   dropdown=True)
        with f5:
            user_filter = self.checkbox_filter("Submitted By", sorted(df_raw["submitted_by"].unique()), "dc_user",
                                               dropdown=True)

        self.require_selection("Tick at least one option in every filter to see records.",
                               scope_filter, source_filter, facility_filter, user_filter)
        return filter_emissions(
            df_raw,
            # While the user is still picking the end date the widget returns one date.
            date_range=tuple(date_range) if len(date_range) == 2 else None,
            scopes=scope_filter,
            sources=source_filter,
            facilities=facility_filter,
            submitted_by=user_filter,
        )

    # ── Stats strip ────────────────────────────────────────────────────────────
    def render_stats(self) -> None:
        totals = scope_totals(self.df)
        s1_pct = share_pct(totals.scope1_kg, totals.total_kg)
        stats = (
            ("Records Found", f"{len(self.df):,}", f"of {len(self.df_raw):,} total", HEADING),
            ("Filtered CO₂e", f"{totals.total_kg / KG_PER_MT:,.2f} Mt", "million tonnes CO₂e", BLUE),
            ("Estimated Carbon Tax", f"MYR {carbon_tax(totals.total_kg):,.0f}", f"@ MYR {CARBON_TAX_RATE_MYR:.0f}/t", RED),
            ("Scope 1 Share", f"{s1_pct:.1f}%", "direct emissions", AMBER),
            ("Scope 2 Share", f"{100 - s1_pct:.1f}%", "indirect emissions", BLUE),
        )
        for col, (label, value, caption, color) in zip(st.columns(len(stats), gap="small"), stats):
            with col:
                self.kpi_card(label, value, caption, color, value_style="font-size:1.5rem;")

    # ── Data table ─────────────────────────────────────────────────────────────
    @staticmethod
    def build_display_table(records: pd.DataFrame) -> pd.DataFrame:
        table = records[list(DISPLAY_COLUMNS)].rename(columns=DISPLAY_COLUMNS)
        table["CO₂e (t)"] = table["CO₂e (t)"] / KG_PER_TONNE
        table["Scope"] = table["Scope"].map(SCOPE_LABELS)
        table["Anomaly Flag"] = table["Anomaly Flag"].map({0: "—", 1: "⚠️ Yes"})
        table["Status"] = table["Status"].map(STATUS_LABELS).fillna(table["Status"])
        return table

    def render_data_tab(self) -> None:
        search = st.text_input("Search records (source, company, submitted by…)", "", key="dc_search")
        table = self.build_display_table(search_rows(self.df, search))
        self.muted_text(f"Showing {len(table):,} of {len(self.df_raw):,} records", size="0.78rem")

        total_pages = max(1, math.ceil(len(table) / DATA_TABLE_PAGE_SIZE))
        # Narrower filters can leave a stale page number above the new maximum.
        if st.session_state.get(PAGE_KEY, 1) > total_pages:
            st.session_state[PAGE_KEY] = total_pages
        page = st.number_input("Page", min_value=1, max_value=total_pages, step=1,
                               key=PAGE_KEY, label_visibility="collapsed")
        start = (page - 1) * DATA_TABLE_PAGE_SIZE
        rows = table.iloc[start:start + DATA_TABLE_PAGE_SIZE].reset_index(drop=True)
        st.dataframe(two_decimals(rows, ["Quantity", "CO₂e (t)"]), width="stretch", height=450)
        self.muted_text(f"Page {page} of {total_pages}", size="0.75rem", align="right")
        self.observation("Use column headers to sort tabular data. All records are verifiable against audit log events.")
        self.render_monthly_summary()

    def render_monthly_summary(self) -> None:
        self.section_title("Monthly Summary (Table)")
        self.muted_text("The entries above combined into one row per company and month: Scope 1 and Scope 2 "
                        "in tonnes CO₂e (the workbook's reported totals plus approved data entries), and power "
                        "consumption. Follows the filters at the top of the page.")
        summary = monthly_ledger_summary(self.df)
        if summary.empty:
            self.muted_text("No entries match the filters.")
            return
        numbers = [col for col in summary.columns if col not in ("Month", "Company")]
        st.dataframe(two_decimals(summary, numbers), width="stretch", hide_index=True, height=450)

    # ── Export ─────────────────────────────────────────────────────────────────
    @staticmethod
    def build_export_frame(records: pd.DataFrame) -> pd.DataFrame:
        export = records.copy()
        export["co2e_tonnes"] = export["co2e_kg"] / KG_PER_TONNE
        export["carbon_tax_myr"] = (export["co2e_tonnes"] * CARBON_TAX_RATE_MYR).round(2)
        return export[[c for c in EXPORT_COLUMNS if c in export.columns]]

    def render_export_tab(self) -> None:
        if has_permission("report"):  # statements are issued by the government, not by companies
            self.render_report_export()

        self.section_title("Export Data (CSV)")
        self.muted_text("Download the filtered dataset for offline analysis, reporting, or audit purposes.")
        export_df = self.build_export_frame(self.df)

        col_dl, col_info = st.columns([1, 2])
        with col_dl:
            st.download_button(
                label="Download CSV",
                data=to_safe_csv(export_df),
                file_name=f"carbontrack_emissions_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                type="primary",
                width="stretch",
            )
        with col_info:
            st.markdown(f"""
            <div class='ct-card' style='padding:0.8rem 1rem;'>
              <div style='color:var(--ct-muted);font-size:0.75rem;'>
                📋 {len(export_df):,} records ·
                {export_df['co2e_kg'].sum() / KG_PER_MT:,.2f} Mt CO₂e ·
                {export_df['date'].min()} to {export_df['date'].max()}
              </div>
            </div>""", unsafe_allow_html=True)

        self.section_title("Preview – first 10 rows (Table)")
        st.dataframe(export_df.head(10), width="stretch")

    def render_report_export(self) -> None:
        """Carbon Emission & Carbon Tax Statement (PDF) for one company and period."""
        self.section_title("Carbon Tax Statement (Report)")
        self.muted_text("A PDF statement in the official format: company details, monthly emissions with a "
                        "chart and summary, and the carbon tax invoice. Uses all records, not the filters above.")
        ledger = self.df_raw
        c1, c2, c3 = st.columns(3)
        with c1:
            company = st.selectbox("Company", sorted(ledger["facility"].unique()), key="report_company",
                                   format_func=company_display_name)
        with c2:
            year = st.selectbox("Year", sorted(ledger["date"].dt.year.unique(), reverse=True), key="report_year")
        with c3:
            period = st.selectbox("Period", list(PERIODS), key="report_period",
                                  format_func=lambda p: "Annual (Jan–Dec)" if p == "Annual" else f"Quarter {p[1]} ({p})")

        months = statement_months(ledger, company, int(year), period)
        if months.empty:
            st.warning(f"No emission data for {company_display_name(company)} in {period} {year}.")
            return
        st.download_button(
            label=f"Download Report ({company} {year} {period}, PDF)",
            # Built only when clicked, not on every page refresh.
            data=lambda: build_statement(ledger, company, int(year), period, CARBON_TAX_RATE_MYR),
            file_name=f"Carbon_Tax_Statement_{company}_{year}_{period}.pdf",
            mime="application/pdf",
            type="primary",
        )
        if (months["Month"].str[:4] == "2026").any():
            self.muted_text("Note: 2026 figures are synthetic (assumption-based), not reported data.", size="0.78rem")


DataCentre().run()
