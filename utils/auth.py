"""
auth.py – Session-based authentication and role management.
Three demo roles: admin, manager, data_entry
"""
import streamlit as st

# ── Demo user credentials ──────────────────────────────────────────────────────
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


def init_session():
    """Initialise auth-related session keys."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "username" not in st.session_state:
        st.session_state.username = None
    if "role" not in st.session_state:
        st.session_state.role = None
    if "user_info" not in st.session_state:
        st.session_state.user_info = None


def login(username: str, password: str) -> bool:
    """Validate credentials and set session state. Returns True on success."""
    u = USERS.get(username.lower())
    if u and u["password"] == password:
        st.session_state.authenticated = True
        st.session_state.username  = username.lower()
        st.session_state.role      = u["role"]
        st.session_state.user_info = u
        return True
    return False


def logout():
    """Clear auth session."""
    for key in ["authenticated", "username", "role", "user_info"]:
        st.session_state[key] = None if key != "authenticated" else False


def require_login():
    """Show login wall if user is not authenticated. Call at top of every page."""
    init_session()
    if not st.session_state.authenticated:
        _render_login_page()
        st.stop()


def has_permission(action: str) -> bool:
    """Check if current user has a given permission."""
    role = st.session_state.get("role", "data_entry")
    return action in PERMISSIONS.get(role, [])


def current_user() -> dict:
    """Return current user info dict."""
    return st.session_state.get("user_info", {})


def render_sidebar_user():
    """Render a user badge + logout button in the sidebar."""
    u = current_user()
    if u:
        st.sidebar.markdown("---")
        st.sidebar.markdown(
            f"**{u['avatar']} {u['name']}**  \n"
            f"<span style='font-size:0.78rem;color:#64748b;font-weight:500;'>"
            f"{ROLE_LABELS.get(st.session_state.role, '')}</span>",
            unsafe_allow_html=True,
        )
        if st.sidebar.button("🚪 Logout", width="stretch"):
            logout()
            st.rerun()


# ── Internal – Login UI ────────────────────────────────────────────────────────
def _render_login_page():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@500;600;700&family=Inter:wght@400;500;600&display=swap');
        [data-testid="stAppViewContainer"] {
            background: #f0f2f6;
            font-family: 'Inter', sans-serif;
        }
        h1, h2 { font-family: 'Outfit', sans-serif !important; }
        .stButton > button[kind="primary"] {
            background: #2563EB !important;
            border: none !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            color: white !important;
        }
        .stTextInput > div > div > input {
            background: #ffffff !important;
            border: 1px solid #cbd5e1 !important;
            border-radius: 8px !important;
            color: #0f172a !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown(
            """
            <div style='text-align:center;margin-bottom:2rem;'>
              <span style='font-size:3rem;'>🌿</span>
              <h1 style='color:#1E3A8A;margin:0;font-size:2rem;font-weight:700;'>Fiscal Green</h1>
              <p style='color:#64748b;margin:0.2rem 0 0;font-size:0.92rem;'>Digital Carbon Accounting Platform</p>
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
            <div style='text-align:center;margin-top:1.5rem;color:#64748b;font-size:0.78rem;'>
            Demo credentials: &nbsp;
            <code style='background:#e2e8f0;padding:2px 6px;border-radius:4px;color:#1e293b;'>admin / admin123</code> &nbsp;|&nbsp;
            <code style='background:#e2e8f0;padding:2px 6px;border-radius:4px;color:#1e293b;'>manager / mgr123</code> &nbsp;|&nbsp;
            <code style='background:#e2e8f0;padding:2px 6px;border-radius:4px;color:#1e293b;'>user / user123</code>
            </div>
            """,
            unsafe_allow_html=True,
        )
