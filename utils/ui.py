"""
ui.py – App bootstrap and the ``Page`` base class every page inherits from.

Every value interpolated into raw HTML that can come from users, the database,
the workbook or the AI model is passed through ``html.escape``.
"""
from collections.abc import Callable
from html import escape

import pandas as pd
import streamlit as st

from data.emission_factors import PENINSULAR_GRID_FACTOR
from utils.auth import render_sidebar_user, require_login
from utils.config import APP_NAME, APP_PAGE_ICON, NAVIGATION_OPTIONS, PAGE_ROUTES
from utils.data_manager import init_db, load_emissions

FONT_IMPORT = (
    "@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800"
    "&family=Inter:wght@300;400;500;600;700&display=swap');"
)

GLOBAL_CSS = """
* { font-family: 'Inter', sans-serif; }
[data-testid='stAppViewContainer'] { background: #f0f2f6; min-height: 100vh; }
.main .block-container { padding-top: 1.8rem; padding-bottom: 2rem; }

h1, h2, h3 { font-family: 'Outfit', 'Inter', sans-serif !important; }
h1 { color: #1E3A8A !important; font-weight: 700 !important; }
h2 { color: #2563EB !important; font-weight: 600 !important; }
h3 { color: #1e293b !important; font-weight: 600 !important; }

/* Sidebar (the default page list is replaced by our own selectbox) */
[data-testid='stSidebar'] { background: #ffffff !important; border-right: 1px solid #e2e8f0 !important; }
[data-testid='stSidebarNav'] { display: none !important; }
[data-testid='stSidebar'] * { color: #1e293b !important; }

.stAlert, [data-testid='stAlert'] { border-radius: 8px !important; }

/* Cards */
.ct-card {
    background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px;
    padding: 1.1rem 1.2rem; transition: all 0.2s ease; box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.ct-card:hover { border-color: #93c5fd; transform: translateY(-2px); box-shadow: 0 6px 16px rgba(37,99,235,0.08); }
.ct-card-value {
    font-size: 1.85rem; font-weight: 700; color: #1E3A8A; margin: 0.2rem 0;
    line-height: 1.1; font-family: 'Outfit', sans-serif;
}
.ct-card-label {
    font-size: 0.72rem; color: #64748b; text-transform: uppercase;
    letter-spacing: 0.06em; font-weight: 600;
}
.ct-card-sub { color: #64748b; font-size: 0.72rem; }
.ct-card-delta { font-size: 0.78rem; font-weight: 500; margin-top: 0.3rem; }
.delta-up   { color: #dc2626; }
.delta-down { color: #16a34a; }
.delta-neu  { color: #64748b; }

.ct-section-title {
    font-size: 1.15rem; font-weight: 700; color: #1E3A8A; border-left: 4px solid #2563EB;
    padding-left: 0.7rem; margin: 1.4rem 0 0.8rem; font-family: 'Outfit', sans-serif;
}
.sim-card {
    background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px;
    padding: 1rem 1.2rem; margin: 0.4rem 0; box-shadow: 0 1px 2px rgba(0,0,0,0.02);
}
.approval-card {
    background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 1.1rem 1.3rem;
    margin: 0.6rem 0; box-shadow: 0 1px 3px rgba(0,0,0,0.04); transition: all 0.2s ease;
}
.approval-card:hover { border-color: #93c5fd; box-shadow: 0 4px 12px rgba(37,99,235,0.06); }

/* AI badge */
.ai-badge {
    display: inline-flex; align-items: center; gap: 6px; background: #dbeafe;
    border: 1px solid #93c5fd; border-radius: 20px; padding: 4px 12px; font-size: 0.75rem;
    font-weight: 600; color: #1e40af; text-transform: uppercase; letter-spacing: 0.05em;
    margin-bottom: 0.7rem;
}

/* Status badges */
.anomaly-badge, .approved-badge, .pending-badge {
    display: inline-flex; align-items: center; gap: 5px; border-radius: 20px;
    padding: 3px 10px; font-size: 0.72rem; font-weight: 600; text-transform: uppercase;
}
.anomaly-badge  { background: #fff7ed; border: 1px solid #fdba74; color: #c2410c; }
.approved-badge { background: #f0fdf4; border: 1px solid #86efac; color: #15803d; }
.pending-badge  { background: #fefce8; border: 1px solid #fde047; color: #a16207; }

/* Activity log rows */
.log-row {
    display: flex; align-items: center; gap: 0.8rem; padding: 0.6rem 0.85rem; margin: 0.25rem 0;
    border-radius: 8px; background: #ffffff; border: 1px solid #e2e8f0; box-shadow: 0 1px 2px rgba(0,0,0,0.02);
}
.log-timestamp { color: #64748b; font-size: 0.74rem; min-width: 130px; font-family: monospace; }
.log-user { color: #2563EB; font-size: 0.78rem; font-weight: 600; min-width: 80px; }
.log-action { font-size: 0.78rem; font-weight: 600; min-width: 140px; }
.log-details { color: #334155; font-size: 0.76rem; flex: 1; }

/* Tabs */
[data-testid='stTabs'] [role='tab'] { color: #64748b; font-family: 'Outfit', sans-serif; font-weight: 500; }
[data-testid='stTabs'] [role='tab'][aria-selected='true'] {
    color: #1E3A8A !important; border-bottom-color: #2563EB !important; font-weight: 700;
}

/* Buttons */
.stButton > button[kind='primary'] {
    background: #2563EB !important; border: none !important; border-radius: 8px !important;
    color: white !important; font-weight: 600 !important; box-shadow: 0 2px 4px rgba(37,99,235,0.2) !important;
}
.stButton > button[kind='primary']:hover {
    background: #1d4ed8 !important; transform: translateY(-1px); box-shadow: 0 4px 12px rgba(37,99,235,0.3) !important;
}
.stButton > button[kind='secondary'] {
    background: #ffffff !important; border: 1px solid #cbd5e1 !important;
    border-radius: 8px !important; color: #334155 !important;
}
.stButton > button[kind='secondary']:hover { background: #f8fafc !important; border-color: #94a3b8 !important; }

/* Inputs */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stSelectbox > div > div,
.stMultiSelect > div > div,
.stDateInput > div > div > input,
.stTextArea > div > div > textarea {
    background: #ffffff !important; border: 1px solid #cbd5e1 !important;
    border-radius: 8px !important; color: #0f172a !important;
}

/* Tables */
.stDataFrame { border-radius: 10px; overflow: hidden; border: 1px solid #e2e8f0; }
[data-testid='stDataFrame'] th { background: #f1f5f9 !important; color: #1E3A8A !important; font-weight: 600 !important; }

/* Chat */
[data-testid='stChatMessage'] {
    background: #ffffff !important; border-radius: 12px !important;
    border: 1px solid #e2e8f0 !important; box-shadow: 0 1px 3px rgba(0,0,0,0.03);
}

hr { border-color: #e2e8f0 !important; }
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 3px; }
"""


# ── App bootstrap ──────────────────────────────────────────────────────────────
def init_app(page_title: str, page_icon: str) -> None:
    """
    Run once per request by the router (app.py): page config, styles,
    database and the login wall (stops the run if signed out).
    """
    st.set_page_config(page_title=page_title, page_icon=page_icon, layout="wide",
                       initial_sidebar_state="expanded")
    st.markdown(f"<style>{FONT_IMPORT}{GLOBAL_CSS}</style>", unsafe_allow_html=True)
    init_db()
    require_login()


# ── Page base class ────────────────────────────────────────────────────────────
class Page:
    """
    Base class for every page. A subclass sets the class attributes, may
    override ``sidebar()``, implements ``render()`` and the page file ends
    with ``MyPage().run()``. The shared UI components below are inherited.
    """

    name: str                               # browser tab: "<name> · Fiscal Green"
    icon: str
    nav_label: str                          # key of PAGE_ROUTES
    header: tuple[str, str] | None = None   # (title, subtitle) shown above render()

    def run(self) -> None:
        st.set_page_config(page_title=f"{self.name} · {APP_NAME}", page_icon=self.icon)
        require_login()  # defence in depth; the router has already checked
        with st.sidebar:
            self._render_brand()
            st.markdown("### 🧭 Navigation")
            self._render_navigation()
            self.sidebar()
            render_sidebar_user()
        if self.header:
            self.page_header(*self.header)
        self.render()

    def sidebar(self) -> None:
        """Page-specific sidebar content, shown above the user badge."""

    def render(self) -> None:
        raise NotImplementedError

    # ── Sidebar chrome ─────────────────────────────────────────────────────────
    @staticmethod
    def _render_brand() -> None:
        st.markdown(
            f"""
            <div style='padding:0.3rem 0 0.8rem;text-align:center;'>
              <span style='font-size:1.8rem;'>{APP_PAGE_ICON}</span>
              <div style='font-size:1.1rem;font-weight:700;color:#1E3A8A;font-family:Outfit,sans-serif;'>{APP_NAME}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    def _render_navigation(self) -> None:
        """The only application-level page navigation control."""
        selected = st.sidebar.selectbox(
            "Choose a workspace",
            NAVIGATION_OPTIONS,
            index=NAVIGATION_OPTIONS.index(self.nav_label),
            label_visibility="collapsed",
        )
        if selected != self.nav_label:
            st.switch_page(PAGE_ROUTES[selected])

    # ── Data ───────────────────────────────────────────────────────────────────
    @staticmethod
    def load_emissions_or_stop(empty_message: str) -> pd.DataFrame:
        """Approved emissions; halts the page with a warning when there are none."""
        df = load_emissions()
        if df.empty:
            st.warning(empty_message)
            st.stop()
        return df

    # ── Content components ─────────────────────────────────────────────────────
    @staticmethod
    def render_data_quality_notice(df: pd.DataFrame) -> None:
        """Tell users which dimensions are unavailable in the workbook source."""
        for issue in df.attrs.get("data_quality_issues", []):
            st.warning(f"Data limitation: {issue}")

    @staticmethod
    def page_header(title: str, subtitle: str) -> None:
        st.markdown(
            f"""
            <div style='margin-bottom:1.2rem;'>
              <h1 style='color:#1E3A8A;font-size:2rem;font-weight:800;margin:0;font-family:Outfit,sans-serif;'>{title}</h1>
              <p style='color:#64748b;font-size:0.9rem;margin:0.2rem 0 0;'>{subtitle}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    @staticmethod
    def section_title(text: str, style: str = "") -> None:
        style_attr = f" style='{style}'" if style else ""
        st.markdown(f"<div class='ct-section-title'{style_attr}>{text}</div>", unsafe_allow_html=True)

    @staticmethod
    def kpi_card(label: str, value: str, caption: str, color: str,
                 delta: str | None = None, delta_class: str = "delta-neu",
                 value_style: str = "") -> None:
        """A metric tile. ``value``/``caption`` are escaped since they may carry data."""
        delta_html = f"<div class='ct-card-delta {delta_class}'>{escape(delta)}</div>" if delta else ""
        st.markdown(
            f"""
            <div class='ct-card'>
              <div class='ct-card-label'>{escape(label)}</div>
              <div class='ct-card-value' style='color:{color};{value_style}'>{escape(value)}</div>
              <div class='ct-card-sub'>{escape(caption)}</div>
              {delta_html}
            </div>""",
            unsafe_allow_html=True,
        )

    @staticmethod
    def muted_text(text: str, size: str = "0.85rem") -> None:
        st.markdown(f"<div style='color:#64748b;font-size:{size};'>{text}</div>", unsafe_allow_html=True)

    @staticmethod
    def observation(text: str, title: str = "Observations") -> None:
        st.info(f"💡 **{title}:** {text}")

    @staticmethod
    def ai_panel_header(badge: str) -> None:
        st.markdown(f"<div class='ai-badge'>{escape(badge)}</div>", unsafe_allow_html=True)

    @staticmethod
    def cached_ai_text(cache_key: str, regenerate: bool, spinner_text: str,
                       generate: Callable[[], str]) -> None:
        """
        Generate AI text once per session (then only when ``regenerate``) and
        show it as Markdown with raw HTML disabled, so a response can never
        inject markup into the page.
        """
        if regenerate or st.session_state.get(cache_key) is None:
            with st.spinner(spinner_text):
                st.session_state[cache_key] = generate()
        if st.session_state[cache_key]:
            st.markdown(st.session_state[cache_key])

    @staticmethod
    def footer() -> None:
        text = (
            f"Data sourced from internal records · GHG Protocol Scope 1 & 2 · "
            f"Malaysia Grid {PENINSULAR_GRID_FACTOR} kg CO₂e/kWh"
        )
        st.markdown(
            f"<div style='text-align:center;color:#64748b;font-size:0.75rem;padding:1.5rem 0 0;'>{text}</div>",
            unsafe_allow_html=True,
        )
