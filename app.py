"""
app.py – Fiscal Green entry point and page router.
Run with:  streamlit run app.py

Every request passes through here first: shared styles, database set-up and
the login wall run once, then the requested page is executed. After signing
in, users land on the default page (Main Dashboard).
"""
import streamlit as st

from utils.config import APP_NAME, APP_PAGE_ICON, DEFAULT_PAGE, PAGE_ROUTES
from utils.ui import init_app

init_app(APP_NAME, APP_PAGE_ICON)

pages = [st.Page(path, default=(label == DEFAULT_PAGE)) for label, path in PAGE_ROUTES.items()]
# The sidebar uses our own selectbox (see utils.ui.render_navigation).
st.navigation(pages, position="hidden").run()
