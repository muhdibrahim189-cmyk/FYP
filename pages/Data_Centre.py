"""
Page 3 – Data Centre
Full emission records with filtering, search, and export.
"""
import math
from datetime import datetime

import pandas as pd
import streamlit as st

from data.emission_factors import CARBON_TAX_RATE_MYR
from utils.analytics import filter_emissions, scope_totals, search_rows, to_safe_csv
from utils.carbon_calculator import KG_PER_TONNE, carbon_tax, share_pct
from utils.charts import AMBER, BLUE, HEADING, RED
from utils.config import ALL_OPTION, DATA_TABLE_PAGE_SIZE, STATUS_LABELS
from utils.ui import Page

PAGE_KEY = "dc_page"
DISPLAY_COLUMNS = {
    "id": "ID", "date": "Date", "facility": "Facility",
    "scope": "Scope", "source": "Source", "unit": "Unit",
    "quantity": "Quantity", "co2e_kg": "CO₂e (kg)",
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
        self.df_raw = self.load_emissions_or_stop("No data found in the database.")
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
        with f2:
            scope_filter = st.multiselect("Scope", [1, 2], default=[1, 2], key="dc_scope")
        with f3:
            all_sources = sorted(df_raw["source"].unique().tolist())
            source_filter = st.multiselect("Source", all_sources, default=all_sources, key="dc_source")
        with f4:
            facilities = sorted(df_raw["facility"].unique().tolist())
            facility_filter = st.multiselect("Company", facilities, default=facilities, key="dc_fac")
        with f5:
            user_options = [ALL_OPTION] + sorted(df_raw["submitted_by"].unique().tolist())
            user_filter = st.selectbox("Submitted By", user_options, key="dc_user")

        return filter_emissions(
            df_raw,
            # While the user is still picking the end date the widget returns one date.
            date_range=tuple(date_range) if len(date_range) == 2 else None,
            scopes=scope_filter,
            sources=source_filter,
            facilities=facility_filter,
            submitted_by=None if user_filter == ALL_OPTION else user_filter,
        )

    # ── Stats strip ────────────────────────────────────────────────────────────
    def render_stats(self) -> None:
        totals = scope_totals(self.df)
        s1_pct = share_pct(totals.scope1_kg, totals.total_kg)
        stats = (
            ("Records Found", f"{len(self.df):,}", f"of {len(self.df_raw):,} total", HEADING),
            ("Filtered CO₂e", f"{totals.total_kg / KG_PER_TONNE:,.1f} t", "tonnes CO₂e", BLUE),
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
        table["CO₂e (kg)"] = table["CO₂e (kg)"].round(2)
        table["Quantity"] = table["Quantity"].round(3)
        table["Anomaly Flag"] = table["Anomaly Flag"].map({0: "—", 1: "⚠️ Yes"})
        table["Status"] = table["Status"].map(STATUS_LABELS).fillna(table["Status"])
        return table

    def render_data_tab(self) -> None:
        search = st.text_input("🔎 Search records (source, facility, submitted by…)", "", key="dc_search")
        table = self.build_display_table(search_rows(self.df, search))
        self.muted_text(f"Showing {len(table):,} of {len(self.df_raw):,} records", size="0.78rem")

        total_pages = max(1, math.ceil(len(table) / DATA_TABLE_PAGE_SIZE))
        # Narrower filters can leave a stale page number above the new maximum.
        if st.session_state.get(PAGE_KEY, 1) > total_pages:
            st.session_state[PAGE_KEY] = total_pages
        page = st.number_input("Page", min_value=1, max_value=total_pages, step=1,
                               key=PAGE_KEY, label_visibility="collapsed")
        start = (page - 1) * DATA_TABLE_PAGE_SIZE
        st.dataframe(table.iloc[start:start + DATA_TABLE_PAGE_SIZE].reset_index(drop=True),
                     width="stretch", height=450)
        st.markdown(f"<div style='color:var(--ct-muted);font-size:0.75rem;text-align:right;'>Page {page} of {total_pages}</div>",
                    unsafe_allow_html=True)
        self.observation("Use column headers to sort tabular data. All records are verifiable against audit log events.")

    # ── Export ─────────────────────────────────────────────────────────────────
    @staticmethod
    def build_export_frame(records: pd.DataFrame) -> pd.DataFrame:
        export = records.copy()
        export["co2e_tonnes"] = export["co2e_kg"] / KG_PER_TONNE
        export["carbon_tax_myr"] = (export["co2e_tonnes"] * CARBON_TAX_RATE_MYR).round(2)
        return export[[c for c in EXPORT_COLUMNS if c in export.columns]]

    def render_export_tab(self) -> None:
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
                {export_df['co2e_tonnes'].sum():,.1f} tCO₂e ·
                {export_df['date'].min()} to {export_df['date'].max()}
              </div>
            </div>""", unsafe_allow_html=True)

        self.section_title("Preview (first 10 rows)")
        st.dataframe(export_df.head(10), width="stretch")


DataCentre().run()
