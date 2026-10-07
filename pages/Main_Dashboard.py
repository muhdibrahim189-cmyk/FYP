"""
Page 1 – Main Dashboard
Scope 1 & 2 KPI cards, trend charts with a STIRPAT forecast, carbon tax.
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from data.emission_factors import CARBON_TAX_RATE_MYR
from utils.analytics import (
    facility_summary, filter_emissions, grouped_mt, monthly_summary, period_over_period_change,
    scope_totals, stirpat_forecast,
)
from utils.carbon_calculator import (
    KG_PER_TONNE, kg_to_mt, share_pct,
)
from utils.charts import (
    AMBER, BLUE, GREEN, HEADING, HOVER_FORMAT, SCOPE_COLORS, apply_layout,
)
from utils.config import FORECAST_MONTHS, STIRPAT_TRAIN_SHARE
from utils.data_manager import load_emissions, load_stirpat_panel
from utils.ui import Page

SCOPE_FILL_COLORS = {1: "rgba(217,119,6,0.06)", 2: "rgba(37,99,235,0.06)"}
TOTAL_COLOR = "#64748b"
# STIRPAT models: panel column, label, line colour, scopes it covers.
STIRPAT_TARGETS = (
    ("S1", "Scope 1", SCOPE_COLORS[1], {1}),
    ("S2", "Scope 2", SCOPE_COLORS[2], {2}),
    ("I", "Total (Scope 1 + 2)", TOTAL_COLOR, {1, 2}),
)


class MainDashboard(Page):
    name = "Dashboard"
    nav_label = "Main Dashboard"
    header = (
        "📊 Emission Dashboard",
        "Scope 1 & 2 GHG Protocol Monitoring · Real-time Operational Insights · Carbon Tax Liability",
    )

    # ── Sidebar filters ────────────────────────────────────────────────────────
    def sidebar(self) -> None:
        df_all = self.df_all = load_emissions()
        st.markdown("### ⚙️ Filters")

        years = sorted(df_all["date"].dt.year.unique(), reverse=True) if not df_all.empty else []
        self.sel_years = self.checkbox_filter("Year", years, key="dash_year", expanded=True)
        facilities = sorted(df_all["facility"].unique()) if not df_all.empty else []
        self.sel_fac = self.checkbox_filter("Facilities", facilities, key="dash_fac")
        self.scope_opts = self.checkbox_filter("Scope", [1, 2], key="dash_scope",
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
        self.section_title("📉 Monthly Trend & STIRPAT Forecast")
        self.render_trend_section()
        self.section_title("🏭 Facility Heatmap & Trellis")
        self.render_facility_section()
        self.section_title("💰 Carbon Tax Analysis")
        self.render_tax_section()

        self.footer()

    # ── KPI cards ──────────────────────────────────────────────────────────────
    def render_kpis(self) -> None:
        totals = scope_totals(self.df)
        self.total_t = kg_to_mt(totals.total_kg)
        self.s1_t = kg_to_mt(totals.scope1_kg)
        self.s2_t = kg_to_mt(totals.scope2_kg)
        self.s1_share = share_pct(self.s1_t, self.total_t)
        self.s2_share = share_pct(self.s2_t, self.total_t)

        change_pct = period_over_period_change(self.df)
        if change_pct > 0:
            delta_class, delta_icon = "delta-up", "▲"
        elif change_pct < 0:
            delta_class, delta_icon = "delta-down", "▼"
        else:
            delta_class, delta_icon = "delta-neu", "—"

        cards = (
            ("Total CO₂e", f"{self.total_t:,.2f}", "million tonnes (Mt)",
             f"{delta_icon} {abs(change_pct):.1f}% vs prior period", delta_class, HEADING),
            ("Scope 1", f"{self.s1_t:,.2f}", "Mt CO₂e", f"{self.s1_share:.1f}% of total", "delta-neu", AMBER),
            ("Scope 2", f"{self.s2_t:,.2f}", "Mt CO₂e", f"{self.s2_share:.1f}% of total", "delta-neu", BLUE),
            ("—", "—", "", "Coming soon", "delta-neu", HEADING),  # placeholder slot
        )
        for col, (label, value, caption, delta, d_cls, color) in zip(st.columns(len(cards), gap="small"), cards):
            with col:
                self.kpi_card(label, value, caption, color, delta=delta, delta_class=d_cls)

    # ── Chart sections ─────────────────────────────────────────────────────────
    def render_trend_section(self) -> None:
        st.write(
            "Traces monthly GHG emissions across **Scope 1 (Direct)** and **Scope 2 (Indirect Electricity)**, "
            f"with **STIRPAT** models projecting each scope and the total {FORECAST_MONTHS} months ahead from "
            "production (P), revenue (A) and energy intensity (T)."
        )
        pivot = self.monthly.pivot_table(index="month", columns="scope", values="co2e_mt", fill_value=0)
        actual = {"S1": pivot.get(1), "S2": pivot.get(2), "I": pivot.sum(axis=1)}

        fig = go.Figure()
        for scope_num in (1, 2):
            if scope_num in pivot.columns:
                fig.add_trace(go.Scatter(
                    x=pivot.index, y=pivot[scope_num], name=f"Scope {scope_num}",
                    line=dict(color=SCOPE_COLORS[scope_num], width=2.5),
                    fill="tozeroy", fillcolor=SCOPE_FILL_COLORS[scope_num],
                    mode="lines+markers", marker=dict(size=5),
                ))
        if len(pivot.columns) == 2:
            fig.add_trace(go.Scatter(x=pivot.index, y=actual["I"], name="Total (Scope 1 + 2)",
                                     line=dict(color=TOTAL_COLOR, width=2.5), mode="lines"))

        # One model per selected scope, plus the total when both scopes are shown.
        panel = load_stirpat_panel()
        results = {}
        for target, label, color, scopes in STIRPAT_TARGETS:
            if not scopes <= set(self.scope_opts):
                continue
            result = stirpat_forecast(panel, self.sel_fac, target=target)
            if result is None:
                continue
            results[label] = result
            series = actual[target]
            # Start each forecast at the last actual month so the lines connect.
            fig.add_trace(go.Scatter(
                x=[series.index[-1], *result.forecast["Month"]],
                y=[series.iloc[-1], *result.forecast["Predicted"]],
                name=f"{label} forecast",
                line=dict(color=color, width=2.5, dash="dash"),
                mode="lines+markers", marker=dict(size=6, symbol="diamond"),
            ))
        if results:
            forecast_months = next(iter(results.values())).forecast["Month"]
            fig.add_vrect(x0=pivot.index[-1], x1=forecast_months.iloc[-1],
                          fillcolor=GREEN, opacity=0.06, line_width=0,
                          annotation_text="STIRPAT forecast", annotation_position="top left")

        apply_layout(fig, 450,
                     title=f"Monthly CO₂e Emissions by Scope (Mt) + {FORECAST_MONTHS}-Month STIRPAT Forecast",
                     yaxis_title="Million tonnes CO₂e (Mt)")
        st.plotly_chart(fig, width="stretch")

        if results:
            self.render_stirpat_accuracy(results)
        self.observation(
            f"Scope 2 emissions comprise {self.s2_share:.1f}% of your organization's footprint. "
            f"Notice peak consumption cycles and compare with the upcoming {FORECAST_MONTHS}-month forecast trajectory."
        )

    @staticmethod
    def render_stirpat_accuracy(results: dict) -> None:
        """Test-set accuracy of each STIRPAT model (months it never saw in training)."""
        st.markdown("**STIRPAT model accuracy (test set)**")
        table = pd.DataFrame([
            {
                "Model": label,
                "Train R²": r.train_r2,
                "Test R²": r.test_r2,
                "MAPE (%)": r.test_mape_pct,
                "Accuracy (%)": 100 - r.test_mape_pct,
                "RMSE (Mt)": r.test_rmse,
                "a (ln P)": r.coefficients["P"],
                "b (ln A)": r.coefficients["A"],
                "c (ln T)": r.coefficients["T"],
            }
            for label, r in results.items()
        ])
        st.dataframe(table, hide_index=True, width="stretch",
                     column_config={col: st.column_config.NumberColumn(format="%.4f")
                                    for col in table.columns if col != "Model"})
        first = next(iter(results.values()))
        test_months = first.test["Month"]
        st.caption(
            "ln I = ln α + a·ln P + b·ln A + c·ln T, fitted by ridge regression with a company-specific α. "
            f"Trained on months up to {first.train_end} ({STIRPAT_TRAIN_SHARE:.0%}), tested on "
            f"{test_months.iloc[0]} – {test_months.iloc[-1]}. Accuracy = 100% − MAPE; MAPE and RMSE are per "
            "company-month. Future drivers grow at their year-on-year rate."
        )

    def render_facility_section(self) -> None:
        st.write(
            "Multi-dimensional facility comparison: horizontal rankings display aggregate site burdens, "
            "while the monthly matrix heatmap pinpoints temporal intensity variations across operations."
        )
        fac = facility_summary(self.df)
        fac_total = grouped_mt(fac, ["facility"]).sort_values("co2e_mt")
        fig_bar = px.bar(
            fac_total, x="co2e_mt", y="facility", orientation="h",
            color="co2e_mt", color_continuous_scale=px.colors.sequential.Blues,
            title="Total CO₂e by Facility (Mt)",
            labels={"co2e_mt": "Mt CO₂e", "facility": ""},
        )
        apply_layout(fig_bar, 360, coloraxis_showscale=False)
        fig_bar.update_traces(hovertemplate=f"%{{y}}<br>%{{x:{HOVER_FORMAT}}} Mt CO₂e<extra></extra>")
        st.plotly_chart(fig_bar, width="stretch")

        fac_pivot = fac.pivot_table(index="facility", columns="month", values="co2e_mt", fill_value=0)
        fig_heat = px.imshow(
            fac_pivot, color_continuous_scale=px.colors.sequential.Blues,
            title="Emission Heatmap: Facility × Month (Mt CO₂e)", aspect="auto",
        )
        apply_layout(fig_heat, 320)
        fig_heat.update_traces(hovertemplate=f"%{{y}} · %{{x}}<br>%{{z:{HOVER_FORMAT}}} Mt CO₂e<extra></extra>")
        st.plotly_chart(fig_heat, width="stretch")
        self.observation("Darker blue cells indicate higher monthly facility output. Monitor sites with sudden spikes across consecutive months.")

    def render_tax_section(self) -> None:
        st.write(
            "Quantifies financial exposure under carbon pricing frameworks. "
            "Dual-axis projection correlates monthly recurring fees against cumulative tax accumulation."
        )
        tax_rate = self.tax_rate
        monthly_total = grouped_mt(self.monthly, ["month"])
        monthly_total["tax_myr"] = monthly_total["co2e_kg"] / KG_PER_TONNE * tax_rate
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
          <div style='color:var(--ct-heading);font-size:1.8rem;font-weight:700;margin-top:0.2rem;font-family:Poppins,sans-serif;'>MYR {monthly_total['tax_myr'].sum():,.2f}</div>
          <div style='color:var(--ct-muted);font-size:0.75rem;'>Based on filtered period · Statutory reference rate: MYR {tax_rate:.0f} / tonne CO₂e</div>
        </div>""", unsafe_allow_html=True)
        self.observation("Financial liability scales linearly with tonnage. Early decarbonization initiatives directly mitigate bottom-line tax risks.")


MainDashboard().run()
