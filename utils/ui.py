"""Reusable Streamlit presentation helpers."""

import streamlit as st

from utils.config import APP_NAME, NAVIGATION_OPTIONS, PAGE_ROUTES


BASE_CSS = """
* { font-family: 'Inter', sans-serif; }
.reportview-container, [data-testid='stAppViewContainer'] {
    background: #f0f2f6;
    min-height: 100vh;
}
.main .block-container { padding-top: 1.8rem; padding-bottom: 2rem; }
h1, h2, h3 { font-family: 'Outfit', 'Inter', sans-serif !important; }
h1 { color: #1E3A8A !important; font-weight: 700 !important; }
h2 { color: #2563EB !important; font-weight: 600 !important; }
h3 { color: #1e293b !important; font-weight: 600 !important; }
[data-testid='stSidebar'] {
    background: #ffffff !important;
    border-right: 1px solid #e2e8f0 !important;
}
[data-testid='stSidebarNav'] { display: none !important; }
[data-testid='stSidebar'] * { color: #1e293b !important; }
.stAlert, [data-testid='stAlert'] { border-radius: 8px !important; }
[data-testid='stTabs'] [role='tab'] {
    color: #64748b;
    font-family: 'Outfit', sans-serif;
    font-weight: 500;
}
[data-testid='stTabs'] [role='tab'][aria-selected='true'] {
    color: #1E3A8A !important;
    border-bottom-color: #2563EB !important;
    font-weight: 700;
}
.stButton > button[kind='primary'] {
    background: #2563EB !important;
    border: none !important;
    border-radius: 8px !important;
    color: white !important;
    font-weight: 600 !important;
}
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
hr { border-color: #e2e8f0 !important; }
"""


def render_base_styles() -> None:
    """Inject the shared application styles once per Streamlit rerun."""
    st.markdown(
        f"<style>{BASE_CSS}</style>",
        unsafe_allow_html=True,
    )


def render_sidebar_brand() -> None:
    """Render the common product identity in the sidebar."""
    st.markdown(
        f"""
        <div style='padding:0.3rem 0 0.8rem;text-align:center;'>
          <span style='font-size:1.8rem;'>🌿</span>
          <div style='font-size:1.1rem;font-weight:700;color:#1E3A8A;font-family:Outfit,sans-serif;'>{APP_NAME}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_data_quality_notice(df) -> None:
    """Tell users which dimensions are unavailable in the workbook source."""
    for issue in df.attrs.get("data_quality_issues", []):
        st.warning(f"Data limitation: {issue}")


def render_navigation(current: str = "Overview") -> None:
    """Render the only application-level page navigation control."""
    if current not in NAVIGATION_OPTIONS:
        current = "Overview"

    selected = st.sidebar.selectbox(
        "Choose a workspace",
        NAVIGATION_OPTIONS,
        index=NAVIGATION_OPTIONS.index(current),
        label_visibility="collapsed",
    )
    if selected in PAGE_ROUTES and selected != current:
        st.switch_page(PAGE_ROUTES[selected])
