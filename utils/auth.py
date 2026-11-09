"""
auth.py – Session-based authentication and role management.
Three demo roles:
  * admin      – developer / IT team: every company and every feature.
  * government – regulator: monitors every company and issues carbon tax
                 statements, but cannot enter or approve data or read the audit log.
  * company    – one account per company: sees only its own company's data,
                 enters it and verifies flagged entries (approval queue).
"""
import hmac
import logging

import pandas as pd
import streamlit as st

from data.emission_factors import COMPANIES
from utils.config import APP_LOGO_DATA_URI, APP_NAME, APP_SHORT_NAME
from utils.data_manager import log_action

logger = logging.getLogger(__name__)

# ── Demo user credentials ──────────────────────────────────────────────────────
# Demonstration accounts only (they are shown on the login screen). A real
# deployment must replace these with hashed credentials from a secure store.
USERS = {
    "admin": {
        "password": "admin123",
        "role":     "admin",
        "name":     "Ahmad Faris",
    },
    "user": {
        "password": "user123",
        "role":     "government",
        "name":     "Haziq Rahman",
    },
    # One account per company, e.g. bp / bp123.
    **{
        company.lower(): {
            "password": f"{company.lower()}123",
            "role":     "company",
            "name":     f"{company} Carbon Officer",
            "company":  company,
        }
        for company in COMPANIES
    },
}

ROLE_LABELS = {
    "admin":      "Administrator (IT)",
    "government": "Government Officer",
    "company":    "Company User",
}

# ── Permission matrix ──────────────────────────────────────────────────────────
# Every role may export the data it can see (CSV), so export needs no permission.
PERMISSIONS = {
    "admin":      ["all_companies", "submit", "approve", "report", "audit_log"],
    "government": ["all_companies", "report"],
    "company":    ["submit", "approve"],
}

_SESSION_DEFAULTS = {
    "authenticated": False,
    "username": None,
    "role": None,
    "user_info": None,
}


# ── Pure helpers (no Streamlit) ────────────────────────────────────────────────
def authenticate(username: str, password: str) -> dict | None:
    """Return the user record for valid credentials, otherwise None."""
    user = USERS.get(username.lower())
    if user and hmac.compare_digest(user["password"].encode(), password.encode()):
        return user
    return None


def role_has_permission(role: str | None, action: str) -> bool:
    return action in PERMISSIONS.get(role, [])


def visible_rows(df: pd.DataFrame, user: dict | None, column: str = "facility") -> pd.DataFrame:
    """
    The rows of ``df`` that ``user`` may see: everything for roles with
    "all_companies", otherwise only their own company's rows (none when they
    have no company, so an unknown user sees nothing).
    """
    user = user or {}
    if df.empty or role_has_permission(user.get("role"), "all_companies"):
        return df
    return df[df[column] == user.get("company")]


# ── Session management ─────────────────────────────────────────────────────────
def init_session() -> None:
    """Initialise auth-related session keys."""
    for key, default in _SESSION_DEFAULTS.items():
        st.session_state.setdefault(key, default)


def login(username: str, password: str) -> bool:
    """Validate credentials and set session state. Returns True on success."""
    user = authenticate(username, password)
    if user is None:
        return False
    st.session_state.authenticated = True
    st.session_state.username = username.lower()
    st.session_state.role = user["role"]
    st.session_state.user_info = user
    _audit(st.session_state.username, "LOGIN", "User signed in")
    return True


def logout() -> None:
    """Clear the whole session, so the next user on this browser inherits no data (chat, filters)."""
    if st.session_state.get("username"):
        _audit(st.session_state.username, "LOGOUT", "User signed out")
    st.session_state.clear()
    init_session()


def _audit(username: str, action: str, details: str) -> None:
    # An audit-log failure must not lock users out, but it must be visible.
    try:
        log_action(username, action, details)
    except Exception:
        logger.exception("Could not write %s audit entry for %s", action, username)


def require_login() -> None:
    """Show login wall if user is not authenticated. Call at top of every page."""
    init_session()
    if not st.session_state.authenticated:
        _render_login_page()
        st.stop()


def has_permission(action: str) -> bool:
    """Check if current user has a given permission."""
    return role_has_permission(st.session_state.get("role"), action)


def current_user() -> dict:
    """Return current user info dict (empty when signed out)."""
    return st.session_state.get("user_info") or {}


def current_username() -> str:
    return st.session_state.get("username") or ""


def own_rows(df: pd.DataFrame, column: str = "facility") -> pd.DataFrame:
    """``df`` limited to what the signed-in user may see (see visible_rows)."""
    return visible_rows(df, current_user(), column)


def render_sidebar_user() -> None:
    """Render a user badge + logout button in the sidebar."""
    user = current_user()
    if not user:
        return
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        f"**{user['name']}**  \n"
        f"<span style='font-size:0.78rem;color:var(--ct-muted);font-weight:500;'>"
        f"{ROLE_LABELS.get(st.session_state.role, '')}</span>",
        unsafe_allow_html=True,
    )
    if st.sidebar.button("Logout", width="stretch"):
        logout()
        st.rerun()


def brand_html(logo_px: int, title_rem: float) -> str:
    """Logo emblem with the system name beneath it (sidebar and login page)."""
    # Two lines: "SISTEM PEMANTAUAN" / "KARBON (SPK)".
    first_line, last_word = APP_NAME.rsplit(" ", 1)
    return f"""
      <img src='{APP_LOGO_DATA_URI}' alt='{APP_NAME} logo' style='width:{logo_px}px;max-width:70%;'>
      <div style='font-family:Poppins,sans-serif;font-weight:800;line-height:1.2;margin-top:0.5rem;
          font-size:{title_rem}rem;color:var(--ct-heading);text-transform:uppercase;letter-spacing:0.02em;'>
        {first_line}<br>{last_word} <span style='color:var(--ct-ok-text);'>({APP_SHORT_NAME})</span>
      </div>""".strip()  # a blank line would end the HTML block in Markdown


# ── Internal – Login UI ────────────────────────────────────────────────────────
def _render_login_page() -> None:
    _, center, _ = st.columns([1, 1.4, 1])
    with center:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown(
            f"""
            <div style='text-align:center;margin-bottom:2rem;'>
              {brand_html(logo_px=150, title_rem=1.6)}
              <p style='color:var(--ct-muted);margin:0.6rem 0 0;font-size:0.92rem;'>Digital Carbon Accounting Platform</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="admin / user / bp …")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            submitted = st.form_submit_button("Sign In", width="stretch", type="primary")
            if submitted:
                if login(username.strip(), password.strip()):
                    st.rerun()
                else:
                    st.error("❌ Invalid username or password.")

        code_style = "background:var(--ct-border);padding:2px 6px;border-radius:4px;color:var(--ct-text);"
        accounts = " &nbsp;|&nbsp; ".join(
            f"<code style='{code_style}'>{username} / {user['password']}</code>" for username, user in USERS.items()
        )
        st.markdown(
            f"""
            <div style='text-align:center;margin-top:1.5rem;color:var(--ct-muted);font-size:0.78rem;line-height:2;'>
            Demo credentials (admin = IT, user = government, others = one per company):<br>{accounts}
            </div>
            """,
            unsafe_allow_html=True,
        )
