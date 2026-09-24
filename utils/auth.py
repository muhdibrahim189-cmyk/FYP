"""
auth.py – Session-based authentication and role management.
Three demo roles: admin, manager, data_entry
"""
import hmac
import logging

import streamlit as st

from utils.config import APP_NAME, APP_PAGE_ICON
from utils.data_manager import log_action

logger = logging.getLogger(__name__)

# ── Demo user credentials ──────────────────────────────────────────────────────
# Demonstration accounts only (they are shown on the login screen). A real
# deployment must replace these with hashed credentials from a secure store.
USERS = {
    "admin": {
        "password": "admin123",
        "role":     "admin",
        "name":     "Ahmad Faris (Admin)",
        "avatar":   "👑",
    },
    "manager": {
        "password": "mgr123",
        "role":     "manager",
        "name":     "Nurul Ain (Manager)",
        "avatar":   "🏢",
    },
    "user": {
        "password": "user123",
        "role":     "data_entry",
        "name":     "Haziq Rahman (Data Entry)",
        "avatar":   "📋",
    },
}

ROLE_LABELS = {
    "admin":      "Administrator",
    "manager":    "Manager",
    "data_entry": "Data Entry Officer",
}

# ── Permission matrix ──────────────────────────────────────────────────────────
PERMISSIONS = {
    "admin":      ["view", "submit", "approve", "reject", "delete", "export"],
    "manager":    ["view", "submit", "approve", "reject", "export"],
    "data_entry": ["view", "submit", "export"],
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
    """Clear auth session."""
    if st.session_state.get("username"):
        _audit(st.session_state.username, "LOGOUT", "User signed out")
    for key, default in _SESSION_DEFAULTS.items():
        st.session_state[key] = default


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


def render_sidebar_user() -> None:
    """Render a user badge + logout button in the sidebar."""
    user = current_user()
    if not user:
        return
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        f"**{user['avatar']} {user['name']}**  \n"
        f"<span style='font-size:0.78rem;color:var(--ct-muted);font-weight:500;'>"
        f"{ROLE_LABELS.get(st.session_state.role, '')}</span>",
        unsafe_allow_html=True,
    )
    if st.sidebar.button("🚪 Logout", width="stretch"):
        logout()
        st.rerun()


# ── Internal – Login UI ────────────────────────────────────────────────────────
def _render_login_page() -> None:
    _, center, _ = st.columns([1, 1.4, 1])
    with center:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown(
            f"""
            <div style='text-align:center;margin-bottom:2rem;'>
              <span style='font-size:3rem;'>{APP_PAGE_ICON}</span>
              <h1 style='color:var(--ct-heading);margin:0;font-size:2rem;font-weight:700;'>{APP_NAME}</h1>
              <p style='color:var(--ct-muted);margin:0.2rem 0 0;font-size:0.92rem;'>Digital Carbon Accounting Platform</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.form("login_form"):
            username = st.text_input("👤 Username", placeholder="admin / manager / user")
            password = st.text_input("🔒 Password", type="password", placeholder="••••••••")
            submitted = st.form_submit_button("Sign In", width="stretch", type="primary")
            if submitted:
                if login(username.strip(), password.strip()):
                    st.rerun()
                else:
                    st.error("❌ Invalid username or password.")

        st.markdown(
            """
            <div style='text-align:center;margin-top:1.5rem;color:var(--ct-muted);font-size:0.78rem;'>
            Demo credentials: &nbsp;
            <code style='background:var(--ct-border);padding:2px 6px;border-radius:4px;color:var(--ct-text);'>admin / admin123</code> &nbsp;|&nbsp;
            <code style='background:var(--ct-border);padding:2px 6px;border-radius:4px;color:var(--ct-text);'>manager / mgr123</code> &nbsp;|&nbsp;
            <code style='background:var(--ct-border);padding:2px 6px;border-radius:4px;color:var(--ct-text);'>user / user123</code>
            </div>
            """,
            unsafe_allow_html=True,
        )
