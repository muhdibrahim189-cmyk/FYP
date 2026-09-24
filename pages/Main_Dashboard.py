"""
Page 1 – Main Dashboard
Scope 1 & 2 KPI cards, trend charts, carbon tax, prediction, AI insight.
"""
from html import escape

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from data.emission_factors import CARBON_TAX_RATE_MYR, EMPLOYEES, REVENUE_MYR
from utils.ai_helper import get_dashboard_insight
from utils.analytics import (
    facility_summary, filter_emissions, forecast_monthly_totals, grouped_tonnes, monthly_summary,
    period_over_period_change, scope_totals, source_summary,
)
from utils.carbon_calculator import (
    carbon_tax, emission_intensity_employee, emission_intensity_revenue, kg_to_tonnes, share_pct,
)
from utils.charts import (
    AMBER, BLUE, HEADING, ORANGE, PURPLE, RED, SCOPE_COLORS, apply_layout,
)
from utils.config import FORECAST_MONTHS, GEMINI_MODEL_LABEL
from utils.data_manager import load_emissions
from utils.ui import Page

SCOPE_FILL_COLORS = {1: "rgba(217,119,6,0.06)", 2: "rgba(37,99,235,0.06)"}


class MainDashboard(Page):
    name = "Dashboard"
    icon = "📊"
    nav_label = "Main Dashboard"
    header = (
        "📊 Emission Dashboard",
        "Scope 1 & 2 GHG Protocol Monitoring · Real-time Operational Insights · Carbon Tax Liability",
    )

    # ── Sidebar filters ────────────────────────────────────────────────────────
    def sidebar(self) -> None:
        df_all = self.df_all = load_emissions()
        st.markdown("### ⚙️ Filters")

        # Counts are records per option, like the item counts in an online store.
        year_counts = df_all["date"].dt.year.value_counts() if not df_all.empty else {}
        self.sel_years = self.checkbox_filter("Year", sorted(year_counts.keys(), reverse=True),
                                              key="dash_year", counts=year_counts, expanded=True)

        fac_counts = df_all["facility"].value_counts() if not df_all.empty else {}
        self.sel_fac = self.checkbox_filter("Facilities", sorted(fac_counts.keys()),
                                            key="dash_fac", counts=fac_counts)
        scope_counts = df_all["scope"].value_counts() if not df_all.empty else {}
        self.scope_opts = self.checkbox_filter("Scope", [1, 2], key="dash_scope", counts=scope_counts,
                                               format_func=lambda s: f"Scope {s}")
        self.tax_rate = st.number_input("💰 Carbon Tax (MYR/t)", min_value=0.0,
                                        value=float(CARBON_TAX_RATE_MYR), step=1.0)

    def render(self) -> None:
        # An empty selection would otherwise mean "no filter" and show everything.
        if not self.df_all.empty and not (self.sel_years and self.sel_fac and self.scope_opts):
            st.info("Tick at least one year, facility and scope in the sidebar to see data.")
            st.stop()
        df = self.df = self.df_all if self.df_all.empty else filter_emissions(
            self.df_all,
            years=self.sel_years,
            facilities=self.sel_fac,
            scopes=self.scope_opts,
        )
        if df.empty:
            st.warning("No data available for the selected filters.")
            st.stop()

        self.render_kpis()

        # One scrolling page: every chart section follows the previous one.
        self.monthly = monthly_summary(df)
        self.src_summary = source_summary(df)
        self.section_title("📉 Monthly Trend & Forecast")
        self.render_trend_section()
        self.section_title("🥧 Emissions by Source")
        self.render_source_section(self.src_summary)
        self.section_title("🏭 Facility Heatmap & Trellis")
        self.render_facility_section()
        self.section_title("💰 Carbon Tax Analysis")
        self.render_tax_section()

        self.render_ai_panel()
        self.footer()

    # ── KPI cards ──────────────────────────────────────────────────────────────
    def render_kpis(self) -> None:
        totals = scope_totals(self.df)
        self.total_t = kg_to_tonnes(totals.total_kg)
        self.s1_t = kg_to_tonnes(totals.scope1_kg)
        self.s2_t = kg_to_tonnes(totals.scope2_kg)
        self.s1_share = share_pct(self.s1_t, self.total_t)
        self.s2_share = share_pct(self.s2_t, self.total_t)
        self.tax_liab = carbon_tax(totals.total_kg, self.tax_rate)
        self.intensity_rev = emission_intensity_revenue(totals.total_kg, REVENUE_MYR)
        self.intensity_emp = emission_intensity_employee(totals.total_kg, EMPLOYEES)

        change_pct = self.change_pct = period_over_period_change(self.df)
        if change_pct > 0:
            delta_class, delta_icon = "delta-up", "▲"
        elif change_pct < 0:
            delta_class, delta_icon = "delta-down", "▼"
        else:
            delta_class, delta_icon = "delta-neu", "—"

        cards = (
            ("Total CO₂e", f"{self.total_t:,.1f}", "tonnes",
             f"{delta_icon} {abs(change_pct):.1f}% vs prior period", delta_class, HEADING),
            ("Scope 1", f"{self.s1_t:,.1f}", "tonnes CO₂e", f"{self.s1_share:.1f}% of total", "delta-neu", AMBER),
            ("Scope 2", f"{self.s2_t:,.1f}", "tonnes CO₂e", f"{self.s2_share:.1f}% of total", "delta-neu", BLUE),
            ("Carbon Tax", f"MYR {self.tax_liab:,.0f}", f"@ MYR {self.tax_rate:.0f}/t",
             "Estimated liability", "delta-neu", RED),
            ("Revenue Intensity", f"{self.intensity_rev:.2f}", "tCO₂e / MYR 1M", "Economic intensity", "delta-neu", PURPLE),
            ("Per Employee", f"{self.intensity_emp:.2f}", "tCO₂e / employee", f"{EMPLOYEES} employees", "delta-neu", ORANGE),
        )
        for col, (label, value, caption, delta, d_cls, color) in zip(st.columns(len(cards), gap="small"), cards):
            with col:
                self.kpi_card(label, value, caption, color, delta=delta, delta_class=d_cls)

    # ── Chart sections ─────────────────────────────────────────────────────────
    def render_trend_section(self) -> None:
        st.write(
            "Traces monthly GHG emissions across **Scope 1 (Direct)** and **Scope 2 (Indirect Electricity)**, "
            f"alongside an automated linear regression projection for the upcoming {FORECAST_MONTHS} months."
        )
        pivot = self.monthly.pivot_table(index="month", columns="scope", values="co2e_tonnes", fill_value=0)

        fig = go.Figure()
        for scope_num in (1, 2):
            if scope_num in pivot.columns:
                fig.add_trace(go.Scatter(
                    x=pivot.index, y=pivot[scope_num], name=f"Scope {scope_num}",
                    line=dict(color=SCOPE_COLORS[scope_num], width=2.5),
                    fill="tozeroy", fillcolor=SCOPE_FILL_COLORS[scope_num],
                    mode="lines+markers", marker=dict(size=6),
                ))

        # The forecast deliberately uses the unfiltered history for a stable trend.
        forecast = forecast_monthly_totals(self.df_all)
        if not forecast.empty:
            fig.add_trace(go.Scatter(
                x=forecast["Month"], y=forecast["Predicted"],
                name=f"AI Prediction ({FORECAST_MONTHS}M)",
                line=dict(color="#059669", width=2.2, dash="dash"),
                mode="lines+markers", marker=dict(size=6, symbol="diamond"),
            ))

        apply_layout(fig, 400,
                     title=f"Monthly CO₂e Emissions by Scope (tonnes) + {FORECAST_MONTHS}-Month Trajectory",
                     yaxis_title="Tonnes CO₂e")
        st.plotly_chart(fig, width="stretch")
        self.observation(
            f"Scope 2 emissions comprise {self.s2_share:.1f}% of your organization's footprint. "
            f"Notice peak consumption cycles and compare with the upcoming {FORECAST_MONTHS}-month forecast trajectory."
        )

    @staticmethod
    def render_source_row(row: pd.Series, total_tonnes: float) -> None:
        badge_color = SCOPE_COLORS.get(row["scope"], BLUE)
        st.markdown(f"""
        <div style='display:flex;justify-content:space-between;align-items:center;
            padding:0.6rem 0.9rem;margin:0.35rem 0;border-radius:8px;
            background:var(--ct-surface);border:1px solid var(--ct-border);box-shadow:0 1px 2px rgba(0,0,0,0.03);'>
          <div>
            <span style='background:{badge_color}18;color:{badge_color};font-size:0.7rem;font-weight:700;padding:2px 6px;border-radius:4px;'>S{row["scope"]}</span>
            <span style='color:var(--ct-text);font-size:0.84rem;font-weight:600;margin-left:0.4rem;'>{escape(str(row["source"]))}</span>
          </div>
          <div style='text-align:right;'>
            <span style='color:var(--ct-heading);font-weight:700;font-size:0.88rem;'>{row["co2e_tonnes"]:,.1f}t</span>
            <span style='color:var(--ct-muted);font-size:0.75rem;margin-left:0.3rem;'>({share_pct(row["co2e_tonnes"], total_tonnes):.1f}%)</span>
          </div>
        </div>""", unsafe_allow_html=True)

    def render_source_section(self, sources: pd.DataFrame) -> None:
        st.write(
            "Shows proportional breakdown of carbon emissions categorized by origin activity source. "
            "Hover over individual sectors for exact tonnage and percentage contributions."
        )
        fig = px.pie(
            sources, values="co2e_tonnes", names="source",
            color_discrete_sequence=px.colors.qualitative.T10, hole=0.45,
            title="CO₂e Distribution by Emission Source",
        )
        apply_layout(fig, 430)
        fig.update_traces(textposition="outside", textinfo="percent+label")

        c_left, c_right = st.columns([1.2, 1])
        with c_left:
            st.plotly_chart(fig, width="stretch")
        with c_right:
            self.section_title("Top Emission Sources", style="margin-top:1rem;")
            total_tonnes = sources["co2e_tonnes"].sum()
            for _, row in sources.head(6).iterrows():
                self.render_source_row(row, total_tonnes)
        self.observation("Identify the largest contributing sources to prioritize for targeted decarbonization measures.")

    def render_facility_section(self) -> None:
        st.write(
            "Multi-dimensional facility comparison: horizontal rankings display aggregate site burdens, "
            "while the monthly matrix heatmap pinpoints temporal intensity variations across operations."
        )
        fac = facility_summary(self.df)
        fac_total = grouped_tonnes(fac, ["facility"]).sort_values("co2e_tonnes")
        fig_bar = px.bar(
            fac_total, x="co2e_tonnes", y="facility", orientation="h",
            color="co2e_tonnes", color_continuous_scale=px.colors.sequential.Blues,
            title="Total CO₂e by Facility (tonnes)",
            labels={"co2e_tonnes": "Tonnes CO₂e", "facility": ""},
        )
        apply_layout(fig_bar, 360, coloraxis_showscale=False)
        st.plotly_chart(fig_bar, width="stretch")

        fac_pivot = fac.pivot_table(index="facility", columns="month", values="co2e_tonnes", fill_value=0)
        fig_heat = px.imshow(
            fac_pivot, color_continuous_scale=px.colors.sequential.Blues,
            title="Emission Heatmap: Facility × Month (tonnes CO₂e)", aspect="auto",
        )
        apply_layout(fig_heat, 320)
        st.plotly_chart(fig_heat, width="stretch")
        self.observation("Darker blue cells indicate higher monthly facility output. Monitor sites with sudden spikes across consecutive months.")

    def render_tax_section(self) -> None:
        st.write(
            "Quantifies financial exposure under carbon pricing frameworks. "
            "Dual-axis projection correlates monthly recurring fees against cumulative tax accumulation."
        )
        tax_rate = self.tax_rate
        monthly_total = grouped_tonnes(self.monthly, ["month"])
        monthly_total["tax_myr"] = monthly_total["co2e_tonnes"] * tax_rate
        monthly_total["cumulative_tax"] = monthly_total["tax_myr"].cumsum()

        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Bar(
            x=monthly_total["month"], y=monthly_total["tax_myr"],
            name="Monthly Tax (MYR)", marker_color="#f87171", opacity=0.85,
        ), secondary_y=False)
        fig.add_trace(go.Scatter(
            x=monthly_total["month"], y=monthly_total["cumulative_tax"],
            name="Cumulative Tax (MYR)", line=dict(color=BLUE, width=2.5), mode="lines+markers",
        ), secondary_y=True)
        apply_layout(fig, 380, title=f"Carbon Tax Liability @ MYR {tax_rate:.0f}/tonne CO₂e")
        fig.update_yaxes(title_text="Monthly MYR", secondary_y=False)
        fig.update_yaxes(title_text="Cumulative MYR", secondary_y=True)
        st.plotly_chart(fig, width="stretch")

        st.markdown(f"""
        <div style='background:var(--ct-surface);border:1px solid var(--ct-danger-border);border-left:4px solid #dc2626;
            border-radius:10px;padding:1rem 1.4rem;margin-top:0.5rem;box-shadow:0 1px 3px rgba(0,0,0,0.03);'>
          <div style='color:#dc2626;font-size:0.75rem;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;'>
            Total Estimated Carbon Tax Liability
          </div>
          <div style='color:var(--ct-heading);font-size:1.8rem;font-weight:700;margin-top:0.2rem;font-family:Outfit,sans-serif;'>MYR {monthly_total['tax_myr'].sum():,.2f}</div>
          <div style='color:var(--ct-muted);font-size:0.75rem;'>Based on filtered period · Statutory reference rate: MYR {tax_rate:.0f} / tonne CO₂e</div>
        </div>""", unsafe_allow_html=True)
        self.observation("Financial liability scales linearly with tonnage. Early decarbonization initiatives directly mitigate bottom-line tax risks.")

    # ── AI insight panel ───────────────────────────────────────────────────────
    def render_ai_panel(self) -> None:
        self.section_title("🤖 AI Insights & Recommendations")
        df = self.df
        summary_text = f"""
Period: {df['date'].min().strftime('%b %Y')} to {df['date'].max().strftime('%b %Y')}
Total CO₂e: {self.total_t:,.1f} tonnes
Scope 1: {self.s1_t:,.1f} t ({self.s1_share:.1f}%)
Scope 2: {self.s2_t:,.1f} t ({self.s2_share:.1f}%)
Carbon Tax Liability: MYR {self.tax_liab:,.0f}
Period-on-Period Change: {self.change_pct:+.1f}%
Revenue Intensity: {self.intensity_rev:.3f} tCO₂e/MYR 1M
Employee Intensity: {self.intensity_emp:.3f} tCO₂e/employee
Top 3 Sources: {', '.join(self.src_summary['source'].head(3).tolist())}
Facilities monitored: {len(self.sel_fac)}
"""
        with st.container(border=True):
            self.ai_panel_header(f"✨ AI Powered · {GEMINI_MODEL_LABEL}")
            col_btn, _ = st.columns([1, 4])
            with col_btn:
                regenerate = st.button("🔄 Generate Insight", type="primary", key="gen_insight_btn")
            self.cached_ai_text("ai_insight_cache", regenerate, "🤖 AI is analysing your emission data…",
                                lambda: get_dashboard_insight(summary_text))


MainDashboard().run()
