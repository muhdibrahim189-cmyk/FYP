"""
ui.py – App bootstrap and the ``Page`` base class every page inherits from.

Every value interpolated into raw HTML that can come from users, the database,
the workbook or the AI model is passed through ``html.escape``.
"""
from collections.abc import Callable, Mapping
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

# Colours are tokens resolved with light-dark(): Streamlit sets ``color-scheme``
# on the app root from the viewer's theme (Settings → Light / Dark / System,
# defaulting to the device setting), so every custom style follows it.
GLOBAL_CSS = """
:root {
    --ct-bg: light-dark(#f0f2f6, #0e1117);
    --ct-surface: light-dark(#ffffff, #1a1f2b);
    --ct-surface-alt: light-dark(#f8fafc, #202634);
    --ct-surface-sunken: light-dark(#f1f5f9, #262d3d);
    --ct-border: light-dark(#e2e8f0, #2d3748);
    --ct-border-strong: light-dark(#cbd5e1, #475569);
    --ct-heading: light-dark(#1E3A8A, #93c5fd);
    --ct-text: light-dark(#1e293b, #e2e8f0);
    --ct-text-strong: light-dark(#0f172a, #f8fafc);
    --ct-text-body: light-dark(#334155, #cbd5e1);
    --ct-text-soft: light-dark(#475569, #b6c2d1);
    --ct-muted: light-dark(#64748b, #94a3b8);
    --ct-info-bg: light-dark(#eff6ff, rgba(37,99,235,0.12));
    --ct-info-bg-strong: light-dark(#dbeafe, rgba(37,99,235,0.22));
    --ct-info-border: light-dark(#bfdbfe, rgba(96,165,250,0.35));
    --ct-info-text: light-dark(#1e40af, #bfdbfe);
    --ct-warn-bg: light-dark(#fefce8, rgba(234,179,8,0.12));
    --ct-warn-border: light-dark(#fde047, rgba(234,179,8,0.45));
    --ct-warn-text: light-dark(#a16207, #facc15);
    --ct-warn-text-soft: light-dark(#713f12, #fde68a);
    --ct-alert-bg: light-dark(#fff7ed, rgba(234,88,12,0.12));
    --ct-alert-border: light-dark(#fdba74, rgba(234,88,12,0.45));
    --ct-alert-text: light-dark(#c2410c, #fdba74);
    --ct-ok-bg: light-dark(#f0fdf4, rgba(22,163,74,0.12));
    --ct-ok-border: light-dark(#86efac, rgba(22,163,74,0.45));
    --ct-ok-border-soft: light-dark(#bbf7d0, rgba(22,163,74,0.35));
    --ct-ok-text: light-dark(#15803d, #86efac);
    --ct-danger-border: light-dark(#fecaca, rgba(220,38,38,0.45));
}
* { font-family: 'Inter', sans-serif; }
[data-testid='stAppViewContainer'] { background: var(--ct-bg); min-height: 100vh; }
.main .block-container { padding-top: 1.8rem; padding-bottom: 2rem; }

h1, h2, h3 { font-family: 'Outfit', 'Inter', sans-serif !important; }
h1 { color: var(--ct-heading) !important; font-weight: 700 !important; }
h2 { color: #2563EB !important; font-weight: 600 !important; }
h3 { color: var(--ct-text) !important; font-weight: 600 !important; }

/* Sidebar (the default page list is replaced by our own selectbox) */
[data-testid='stSidebar'] { background: var(--ct-surface) !important; border-right: 1px solid var(--ct-border) !important; }
[data-testid='stSidebarNav'] { display: none !important; }
[data-testid='stSidebar'] * { color: var(--ct-text) !important; }

.stAlert, [data-testid='stAlert'] { border-radius: 8px !important; }

/* Sidebar filters: flat accordion rows (Page.checkbox_filter) */
[class*='st-key-filter_'][data-testid='stExpander'] details,
[class*='st-key-filter_'] [data-testid='stExpander'] details {
    border: none !important; border-bottom: 1px solid var(--ct-border) !important;
    border-radius: 0 !important; background: transparent !important;
}
[class*='st-key-filter_'] summary { padding-left: 0 !important; padding-right: 0 !important; }
[class*='st-key-filter_'] summary p { font-size: 1rem; font-weight: 600; }

/* Cards */
.ct-card {
    background: var(--ct-surface); border: 1px solid var(--ct-border); border-radius: 12px;
    padding: 1.1rem 1.2rem; transition: all 0.2s ease; box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.ct-card:hover { border-color: #93c5fd; transform: translateY(-2px); box-shadow: 0 6px 16px rgba(37,99,235,0.08); }
.ct-card-value {
    font-size: 1.85rem; font-weight: 700; color: var(--ct-heading); margin: 0.2rem 0;
    line-height: 1.1; font-family: 'Outfit', sans-serif;
}
.ct-card-label {
    font-size: 0.72rem; color: var(--ct-muted); text-transform: uppercase;
    letter-spacing: 0.06em; font-weight: 600;
}
.ct-card-sub { color: var(--ct-muted); font-size: 0.72rem; }
.ct-card-delta { font-size: 0.78rem; font-weight: 500; margin-top: 0.3rem; }
.delta-up   { color: #dc2626; }
.delta-down { color: #16a34a; }
.delta-neu  { color: var(--ct-muted); }

.ct-section-title {
    font-size: 1.15rem; font-weight: 700; color: var(--ct-heading); border-left: 4px solid #2563EB;
    padding-left: 0.7rem; margin: 1.4rem 0 0.8rem; font-family: 'Outfit', sans-serif;
}
.sim-card {
    background: var(--ct-surface); border: 1px solid var(--ct-border); border-radius: 10px;
    padding: 1rem 1.2rem; margin: 0.4rem 0; box-shadow: 0 1px 2px rgba(0,0,0,0.02);
}
.approval-card {
    background: var(--ct-surface); border: 1px solid var(--ct-border); border-radius: 12px; padding: 1.1rem 1.3rem;
    margin: 0.6rem 0; box-shadow: 0 1px 3px rgba(0,0,0,0.04); transition: all 0.2s ease;
}
.approval-card:hover { border-color: #93c5fd; box-shadow: 0 4px 12px rgba(37,99,235,0.06); }

/* AI badge */
.ai-badge {
    display: inline-flex; align-items: center; gap: 6px; background: var(--ct-info-bg-strong);
    border: 1px solid #93c5fd; border-radius: 20px; padding: 4px 12px; font-size: 0.75rem;
    font-weight: 600; color: var(--ct-info-text); text-transform: uppercase; letter-spacing: 0.05em;
    margin-bottom: 0.7rem;
}

/* Status badges */
.anomaly-badge, .approved-badge, .pending-badge {
    display: inline-flex; align-items: center; gap: 5px; border-radius: 20px;
    padding: 3px 10px; font-size: 0.72rem; font-weight: 600; text-transform: uppercase;
}
.anomaly-badge  { background: var(--ct-alert-bg); border: 1px solid var(--ct-alert-border); color: var(--ct-alert-text); }
.approved-badge { background: var(--ct-ok-bg); border: 1px solid var(--ct-ok-border); color: var(--ct-ok-text); }
.pending-badge  { background: var(--ct-warn-bg); border: 1px solid var(--ct-warn-border); color: var(--ct-warn-text); }

/* Activity log rows */
.log-row {
    display: flex; align-items: center; gap: 0.8rem; padding: 0.6rem 0.85rem; margin: 0.25rem 0;
    border-radius: 8px; background: var(--ct-surface); border: 1px solid var(--ct-border); box-shadow: 0 1px 2px rgba(0,0,0,0.02);
}
.log-timestamp { color: var(--ct-muted); font-size: 0.74rem; min-width: 130px; font-family: monospace; }
.log-user { color: #2563EB; font-size: 0.78rem; font-weight: 600; min-width: 80px; }
.log-action { font-size: 0.78rem; font-weight: 600; min-width: 140px; }
.log-details { color: var(--ct-text-body); font-size: 0.76rem; flex: 1; }

/* Tabs */
[data-testid='stTabs'] [role='tab'] { color: var(--ct-muted); font-family: 'Outfit', sans-serif; font-weight: 500; }
[data-testid='stTabs'] [role='tab'][aria-selected='true'] {
    color: var(--ct-heading) !important; border-bottom-color: #2563EB !important; font-weight: 700;
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
    background: var(--ct-surface) !important; border: 1px solid var(--ct-border-strong) !important;
    border-radius: 8px !important; color: var(--ct-text-body) !important;
}
.stButton > button[kind='secondary']:hover { background: var(--ct-surface-alt) !important; border-color: #94a3b8 !important; }

/* Inputs */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stSelectbox > div > div,
.stMultiSelect > div > div,
.stDateInput > div > div > input,
.stTextArea > div > div > textarea {
    background: var(--ct-surface) !important; border: 1px solid var(--ct-border-strong) !important;
    border-radius: 8px !important; color: var(--ct-text-strong) !important;
}

/* Tables */
.stDataFrame { border-radius: 10px; overflow: hidden; border: 1px solid var(--ct-border); }
[data-testid='stDataFrame'] th { background: var(--ct-surface-sunken) !important; color: var(--ct-heading) !important; font-weight: 600 !important; }

/* Chat */
[data-testid='stChatMessage'] {
    background: var(--ct-surface) !important; border-radius: 12px !important;
    border: 1px solid var(--ct-border) !important; box-shadow: 0 1px 3px rgba(0,0,0,0.03);
}

hr { border-color: var(--ct-border) !important; }
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--ct-border-strong); border-radius: 3px; }
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
              <div style='font-size:1.1rem;font-weight:700;color:var(--ct-heading);font-family:Outfit,sans-serif;'>{APP_NAME}</div>
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

    # ── Filters ────────────────────────────────────────────────────────────────
    @staticmethod
    def checkbox_filter(label: str, options: list, key: str,
                        format_func: Callable[[object], str] = str,
                        counts: Mapping[object, int] | None = None,
                        expanded: bool = False) -> list:
        """
        Online-store style filter: a collapsible section of checkboxes with a
        "Select All" toggle, all ticked by default. ``counts`` shows a grey
        "(n)" after each option. Returns the ticked options.
        """
        all_key = f"{key}_all"
        item_keys = [f"{key}_{option}" for option in options]
        for item_key in item_keys:
            st.session_state.setdefault(item_key, True)
        # Keep "Select All" in step with boxes the user ticked one by one.
        st.session_state[all_key] = all(st.session_state[k] for k in item_keys)

        def set_all() -> None:
            for item_key in item_keys:
                st.session_state[item_key] = st.session_state[all_key]

        ticked = sum(st.session_state[k] for k in item_keys)
        # Show the selection while collapsed, e.g. "Facilities (2/5)".
        title = label if ticked == len(options) else f"{label} ({ticked}/{len(options)})"
        with st.expander(title, expanded=expanded, key=f"filter_{key}"):
            st.checkbox("Select All", key=all_key, on_change=set_all)
            return [
                option
                for option, item_key in zip(options, item_keys)
                if st.checkbox(
                    format_func(option) + (f" :gray[({counts.get(option, 0)})]" if counts is not None else ""),
                    key=item_key,
                )
            ]

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
              <h1 style='color:var(--ct-heading);font-size:2rem;font-weight:800;margin:0;font-family:Outfit,sans-serif;'>{title}</h1>
              <p style='color:var(--ct-muted);font-size:0.9rem;margin:0.2rem 0 0;'>{subtitle}</p>
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
        st.markdown(f"<div style='color:var(--ct-muted);font-size:{size};'>{text}</div>", unsafe_allow_html=True)

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
            f"<div style='text-align:center;color:var(--ct-muted);font-size:0.75rem;padding:1.5rem 0 0;'>{text}</div>",
            unsafe_allow_html=True,
        )
