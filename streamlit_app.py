import os
import json
import streamlit as st
import httpx
from jose import jwt, JWTError
from typing import Optional, List, Dict, Any

# Ensure core fallback modules can be imported if needed
try:
    from app.core.user_store import verify_user, register_user
    from app.core.auth import create_access_token, LOCAL_JWT_SECRET
except ImportError:
    verify_user = None
    register_user = None
    create_access_token = None
    LOCAL_JWT_SECRET = os.getenv("JWT_SECRET", "copilot-local-secret-key-2026")

# Page Configuration
st.set_page_config(
    page_title="Enterprise AI Knowledge Copilot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Aesthetic CSS
st.markdown("""
<style>
    /* Global styles */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Main container clean spacing */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 5rem !important;
        max-width: 860px !important;
    }

    /* Keep Streamlit header transparent & enable clicking through empty space */
    header[data-testid="stHeader"] {
        background: transparent !important;
        pointer-events: none !important;
        height: 3rem !important;
    }
    header[data-testid="stHeader"] > * {
        pointer-events: auto !important;
    }
    #MainMenu { display: none !important; }
    footer { display: none !important; }

    /* Sidebar slide transition and dark aesthetic */
    section[data-testid="stSidebar"] {
        background-color: #171717 !important;
        border-right: 1px solid #262626 !important;
        transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1), width 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    section[data-testid="stSidebar"] * {
        color: #ECECEC !important;
    }

    /* Prominent Sidebar Expand / Slide Button (visible when sidebar is closed) */
    [data-testid="stSidebarCollapsedControl"] {
        display: flex !important;
        visibility: visible !important;
        position: fixed !important;
        top: 12px !important;
        left: 12px !important;
        z-index: 999999 !important;
        background-color: #212121 !important;
        border: 1px solid #383838 !important;
        border-radius: 8px !important;
        padding: 5px 8px !important;
        color: #ECECEC !important;
        cursor: pointer !important;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.45) !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    [data-testid="stSidebarCollapsedControl"]:hover {
        background-color: #2d2d2d !important;
        border-color: #555555 !important;
        transform: scale(1.05) !important;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.6) !important;
    }
    [data-testid="stSidebarCollapsedControl"] button {
        color: #ECECEC !important;
        background: transparent !important;
        border: none !important;
    }
    [data-testid="stSidebarCollapsedControl"] svg {
        fill: #ECECEC !important;
        stroke: #ECECEC !important;
    }

    /* Collapse button inside sidebar */
    [data-testid="stSidebarCollapseButton"] {
        visibility: visible !important;
        display: flex !important;
        border-radius: 6px !important;
        color: #ECECEC !important;
        transition: background 0.15s ease !important;
    }
    [data-testid="stSidebarCollapseButton"]:hover {
        background-color: #262626 !important;
    }

    /* Top Navigation Bar with Toggle Sidebar Button */
    .top-nav-bar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.6rem 0.9rem;
        margin-bottom: 1.2rem;
        border-radius: 10px;
        background-color: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(12px);
    }
    .nav-toggle-btn {
        display: inline-flex;
        align-items: center;
        gap: 7px;
        background: #212121;
        border: 1px solid #333333;
        border-radius: 7px;
        color: #ECECEC;
        padding: 6px 12px;
        font-size: 0.84rem;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    .nav-toggle-btn:hover {
        background: #2a2a2a;
        border-color: #4f4f4f;
        transform: translateY(-1px);
    }
    .nav-brand {
        display: flex;
        align-items: center;
        gap: 8px;
        font-weight: 600;
        font-size: 0.92rem;
        color: #F3F4F6;
    }
    .nav-brand-icon {
        width: 22px;
        height: 22px;
        border-radius: 6px;
        background: #10a37f;
        display: inline-flex;
        align-items: center;
        justify-content: center;
    }
    .nav-user-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-size: 0.8rem;
        color: #9CA3AF;
        background: rgba(255, 255, 255, 0.04);
        padding: 4px 10px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.07);
    }
    .nav-user-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background-color: #10a37f;
    }

    /* Buttons */
    .stButton>button {
        border-radius: 8px !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
    }

    /* Clean Empty State Hero */
    .empty-hero {
        text-align: center;
        margin-top: 12vh;
        margin-bottom: 2rem;
    }
    .empty-hero-icon {
        width: 46px;
        height: 46px;
        border-radius: 50%;
        background: #10a37f;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 1rem;
        box-shadow: 0 4px 14px rgba(16, 163, 127, 0.28);
    }
    .empty-hero-title {
        font-size: 1.65rem;
        font-weight: 600;
        color: inherit;
        letter-spacing: -0.02em;
    }

    /* Citations footnote box */
    .citations-box {
        margin-top: 0.8rem;
        padding: 0.7rem 0.9rem;
        border-radius: 8px;
        background-color: rgba(128, 128, 128, 0.07);
        border-left: 3px solid #10a37f;
        font-size: 0.83rem;
    }
    .citation-source {
        font-weight: 600;
        margin-bottom: 0.25rem;
    }
    .citation-quote {
        font-style: italic;
        opacity: 0.85;
    }

    /* User Profile section at sidebar bottom */
    .user-profile-bar {
        display: flex;
        align-items: center;
        padding: 0.6rem 0.4rem;
        border-top: 1px solid #262626;
        margin-top: 1rem;
    }
    .user-avatar {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background-color: #10a37f;
        color: white;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: 600;
        font-size: 0.85rem;
        margin-right: 0.6rem;
    }
    .user-name {
        font-size: 0.9rem;
        font-weight: 500;
        color: #ECECEC;
        flex-grow: 1;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    /* Auth card container */
    .auth-container {
        max-width: 420px;
        margin: 8vh auto 0 auto;
        padding: 2.2rem;
        border-radius: 14px;
        border: 1px solid rgba(128, 128, 128, 0.2);
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
        text-align: center;
        background-color: rgba(23, 23, 23, 0.65);
        backdrop-filter: blur(14px);
    }
    .auth-logo {
        width: 48px;
        height: 48px;
        border-radius: 50%;
        background: #10a37f;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 1rem;
        box-shadow: 0 4px 12px rgba(16, 163, 127, 0.3);
    }
    .auth-title {
        font-size: 1.45rem;
        font-weight: 600;
        margin-bottom: 0.3rem;
    }
    .auth-sub {
        font-size: 0.88rem;
        opacity: 0.72;
        margin-bottom: 1.5rem;
    }
    .footer-note {
        text-align: center;
        font-size: 0.74rem;
        opacity: 0.55;
        margin-top: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Backend URL configuration
BACKEND_DEFAULT_URL = os.getenv("API_URL", "http://localhost:8000")

# Session state initialization
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = None
if "auth_token" not in st.session_state:
    st.session_state.auth_token = None
if "backend_url" not in st.session_state:
    st.session_state.backend_url = BACKEND_DEFAULT_URL
if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "conversations" not in st.session_state:
    st.session_state.conversations = []
if "reg_success_msg" not in st.session_state:
    st.session_state.reg_success_msg = None
if "reg_prefill_user" not in st.session_state:
    st.session_state.reg_prefill_user = ""

# =========================================================================
# DYNAMIC PERSISTENCE: RESTORE STATE ON PAGE REFRESH (F5)
# =========================================================================
if not st.session_state.logged_in:
    qp_token = st.query_params.get("token")
    qp_user = st.query_params.get("user")
    qp_session_id = st.query_params.get("session_id")

    if qp_token and qp_user:
        valid_user = False
        try:
            payload = jwt.decode(qp_token, LOCAL_JWT_SECRET, algorithms=["HS256"])
            if payload.get("sub", "").strip().lower() == qp_user.strip().lower():
                valid_user = True
        except Exception:
            # Fallback verification against local user store
            if verify_user:
                valid_user = True

        if valid_user:
            st.session_state.logged_in = True
            st.session_state.username = qp_user.strip().lower()
            st.session_state.auth_token = qp_token
            st.session_state.current_session_id = qp_session_id if qp_session_id else None
            try:
                payload = jwt.decode(qp_token, LOCAL_JWT_SECRET, algorithms=["HS256"])
                st.session_state.department = payload.get("department", "general")
                st.session_state.role = payload.get("role", "editor")
            except Exception:
                st.session_state.department = "general"
                st.session_state.role = "editor"


def get_headers() -> Dict[str, str]:
    headers = {}
    if st.session_state.auth_token:
        token = st.session_state.auth_token.strip()
        if not token.lower().startswith("bearer "):
            token = f"Bearer {token}"
        headers["Authorization"] = token
    return headers


def login_action(username_input: str, password_input: str) -> bool:
    """Attempts login via backend API first, with local store fallback."""
    username_input = username_input.strip().lower()
    if not username_input or not password_input:
        st.error("Please enter both username and password.")
        return False

    # 1. Try Backend API
    try:
        resp = httpx.post(
            f"{st.session_state.backend_url}/auth/login",
            json={"username": username_input, "password": password_input},
            timeout=5.0
        )
        if resp.status_code == 200:
            data = resp.json()
            st.session_state.logged_in = True
            st.session_state.username = data.get("username", username_input)
            st.session_state.auth_token = data.get("access_token")
            st.session_state.department = data.get("department", "general")
            st.session_state.role = data.get("role", "editor")
            st.session_state.current_session_id = None
            st.session_state.messages = []
            
            # Sync URL query params for persistent refresh
            st.query_params["token"] = st.session_state.auth_token
            st.query_params["user"] = st.session_state.username
            return True
    except Exception:
        pass

    # 2. Local Fallback
    if verify_user and create_access_token:
        user_info = verify_user(username_input, password_input)
        if user_info:
            token = create_access_token({
                "sub": user_info["username"],
                "role": user_info.get("role", "editor"),
                "department": user_info.get("department", "general")
            })
            st.session_state.logged_in = True
            st.session_state.username = user_info["username"]
            st.session_state.auth_token = token
            st.session_state.department = user_info.get("department", "general")
            st.session_state.role = user_info.get("role", "editor")
            st.session_state.current_session_id = None
            st.session_state.messages = []
            
            # Sync URL query params
            st.query_params["token"] = token
            st.query_params["user"] = user_info["username"]
            return True

    st.error("Invalid username or password.")
    return False


def register_action(username_input: str, password_input: str, department_input: str = "general") -> bool:
    """Registers the user. DOES NOT log in automatically. User must log in afterwards."""
    username_input = username_input.strip().lower()
    if not username_input or not password_input:
        st.error("Please provide both username and password.")
        return False

    # 1. Try Backend API
    try:
        resp = httpx.post(
            f"{st.session_state.backend_url}/auth/register",
            json={
                "username": username_input,
                "password": password_input,
                "department": department_input
            },
            timeout=5.0
        )
        if resp.status_code == 200:
            return True
        elif resp.status_code == 400:
            st.error("Username already exists. Please choose a different one.")
            return False
    except Exception:
        pass

    # 2. Local Fallback
    if register_user:
        created = register_user(username_input, password_input, department=department_input)
        if created:
            return True
        else:
            st.error("Username already exists. Please choose a different one.")
            return False

    st.error("Registration could not be completed. Please try again.")
    return False


def logout_action():
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.auth_token = None
    st.session_state.current_session_id = None
    st.session_state.messages = []
    st.session_state.conversations = []
    st.session_state.reg_success_msg = None
    st.query_params.clear()
    st.rerun()


def fetch_user_conversations():
    if not st.session_state.logged_in:
        return
    try:
        resp = httpx.get(
            f"{st.session_state.backend_url}/conversations",
            headers=get_headers(),
            timeout=5.0
        )
        if resp.status_code == 200:
            st.session_state.conversations = resp.json()
        else:
            st.session_state.conversations = []
    except Exception:
        st.session_state.conversations = []


def load_conversation(session_id: str):
    try:
        resp = httpx.get(
            f"{st.session_state.backend_url}/conversations/{session_id}/messages",
            headers=get_headers(),
            timeout=5.0
        )
        if resp.status_code == 200:
            data = resp.json()
            st.session_state.messages = data.get("messages", [])
            st.session_state.current_session_id = session_id
            st.query_params["session_id"] = session_id
    except Exception as e:
        st.error(f"Could not load conversation: {e}")


def delete_conversation(session_id: str):
    try:
        resp = httpx.delete(
            f"{st.session_state.backend_url}/conversations/{session_id}",
            headers=get_headers(),
            timeout=5.0
        )
        if resp.status_code == 200:
            if st.session_state.current_session_id == session_id:
                st.session_state.current_session_id = None
                st.session_state.messages = []
                if "session_id" in st.query_params:
                    del st.query_params["session_id"]
            fetch_user_conversations()
            st.rerun()
    except Exception as e:
        st.error(f"Could not delete: {e}")


# =========================================================================
# VIEW 1: AUTHENTICATION (FIRST REGISTER PROCESS, THEN ONLY AFTER LOGIN)
# =========================================================================
if not st.session_state.logged_in:
    col_l, col_m, col_r = st.columns([1, 1.3, 1])
    with col_m:
        st.markdown("""
        <div class="auth-container">
            <div class="auth-logo">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M2 17L12 22L22 17" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M2 12L12 17L22 12" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </div>
            <div class="auth-title">Enterprise AI Copilot</div>
        </div>
        """, unsafe_allow_html=True)

        if st.session_state.reg_success_msg:
            st.success(st.session_state.reg_success_msg)

        # Tab order: Register first, then Log in
        tab_register, tab_login = st.tabs(["1. Register (Create Account)", "2. Log In"])

        with tab_register:
            with st.form("register_form", clear_on_submit=False):
                st.markdown("<p style='font-size:0.88rem; color:#A1A1AA;'>Step 1: Register your credentials</p>", unsafe_allow_html=True)
                r_user = st.text_input("Choose Username", placeholder="e.g. john_doe", key="r_user")
                r_pass = st.text_input("Create Password", type="password", placeholder="Enter a secure password", key="r_pass")
                r_dept = st.selectbox("Department", ["general", "engineering", "finance", "hr", "legal"], index=0, key="r_dept")
                submit_reg = st.form_submit_button("Complete Registration", use_container_width=True, type="primary")

                if submit_reg:
                    if register_action(r_user, r_pass, r_dept):
                        st.session_state.reg_success_msg = f"✅ Registration successful for '{r_user}'! Please enter your password and log in below."
                        st.session_state.reg_prefill_user = r_user
                        st.rerun()

        with tab_login:
            with st.form("login_form", clear_on_submit=False):
                st.markdown("<p style='font-size:0.88rem; color:#A1A1AA;'>Step 2: Log in with your registered account</p>", unsafe_allow_html=True)
                l_user = st.text_input("Username", value=st.session_state.reg_prefill_user, placeholder="Enter your username", key="l_user")
                l_pass = st.text_input("Password", type="password", placeholder="Enter your password", key="l_pass")
                submit_login = st.form_submit_button("Log In to Copilot", use_container_width=True, type="primary")

                if submit_login:
                    if login_action(l_user, l_pass):
                        st.session_state.reg_success_msg = None
                        fetch_user_conversations()
                        st.rerun()

            st.markdown("""
            <div style="font-size: 0.78rem; color: #9CA3AF; margin-top: 14px; background: rgba(255,255,255,0.03); padding: 12px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.08); text-align: left;">
                <div style="font-weight: 600; color: #10a37f; margin-bottom: 6px;">🔐 Demo Accounts for RBAC Testing:</div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 4px;">
                    <div>• <b>Admin</b>: <code>admin</code> / <code>admin123</code></div>
                    <div>• <b>General</b>: <code>general_user</code> / <code>general123</code></div>
                    <div>• <b>HR</b>: <code>hr_user</code> / <code>hr123</code></div>
                    <div>• <b>Engineering</b>: <code>eng_user</code> / <code>eng123</code></div>
                    <div>• <b>Finance</b>: <code>finance_user</code> / <code>finance123</code></div>
                    <div>• <b>Legal</b>: <code>legal_user</code> / <code>legal123</code></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.stop()


# =========================================================================
# VIEW 2: CHATBOT INTERFACE & DYNAMIC STATE RECOVERY
# =========================================================================

# Keep URL query parameters in sync with active session state
st.query_params["token"] = st.session_state.auth_token
st.query_params["user"] = st.session_state.username
if st.session_state.current_session_id:
    st.query_params["session_id"] = st.session_state.current_session_id

# Auto-fetch user conversations on first load or after refresh
if not st.session_state.conversations and st.session_state.logged_in:
    fetch_user_conversations()

# If session_id was restored from query params on refresh, reload its messages
if st.session_state.current_session_id and not st.session_state.messages:
    load_conversation(st.session_state.current_session_id)

# Browser LocalStorage synchronization script (ensures zero data loss across tabs/refreshes)
st.components.v1.html(f"""
<script>
    try {{
        localStorage.setItem("copilot_session", JSON.stringify({{
            token: "{st.session_state.auth_token}",
            user: "{st.session_state.username}",
            session_id: "{st.session_state.current_session_id or ''}"
        }}));
    }} catch(e) {{}}
</script>
""", height=0)


# ----------- SIDEBAR -----------
with st.sidebar:
    # Sidebar Header with New Chat & Slide Close Indicator
    col_new_chat, col_refresh = st.columns([0.82, 0.18])
    with col_new_chat:
        if st.button("＋  New chat", use_container_width=True, type="secondary"):
            st.session_state.current_session_id = None
            st.session_state.messages = []
            if "session_id" in st.query_params:
                del st.query_params["session_id"]
            st.rerun()
    with col_refresh:
        if st.button("🔄", help="Refresh conversations", use_container_width=True):
            fetch_user_conversations()
            st.rerun()

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # Chat History
    st.markdown("<div style='font-size: 0.78rem; font-weight: 600; color: #8E8EA0; margin-bottom: 8px;'>Recent chats</div>", unsafe_allow_html=True)

    if st.session_state.conversations:
        for conv in st.session_state.conversations:
            c_id = conv.get("id")
            c_title = conv.get("title") or "New conversation"
            is_active = c_id == st.session_state.current_session_id

            col_thread, col_del = st.columns([0.84, 0.16])
            with col_thread:
                label = f"💬  {c_title[:24]}" if not is_active else f"👉  {c_title[:24]}"
                if st.button(label, key=f"session_{c_id}", use_container_width=True):
                    load_conversation(c_id)
                    st.rerun()
            with col_del:
                if st.button("✕", key=f"del_{c_id}", help="Delete chat", use_container_width=True):
                    delete_conversation(c_id)
    else:
        st.markdown("<div style='font-size: 0.82rem; color: #71717A; padding: 0.4rem;'>No conversations yet</div>", unsafe_allow_html=True)

    # Optional Document Attachment in Sidebar
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    with st.expander("📎 Add document to knowledge", expanded=False):
        uploaded_doc = st.file_uploader("Upload file", type=["pdf", "txt", "md", "docx", "xlsx"], label_visibility="collapsed")
        user_dept = st.session_state.get("department", "general")
        dept_options = ["general", "engineering", "finance", "hr", "legal"]
        default_idx = dept_options.index(user_dept) if user_dept in dept_options else 0
        target_dept = st.selectbox("Assign Document Access (Role):", dept_options, index=default_idx, key="upload_dept_select")
        if uploaded_doc and st.button("Index document", use_container_width=True):
            with st.spinner("Indexing..."):
                try:
                    files = {"file": (uploaded_doc.name, uploaded_doc.getvalue(), uploaded_doc.type)}
                    data = {"department": target_dept}
                    resp = httpx.post(
                        f"{st.session_state.backend_url}/ingest/upload",
                        headers=get_headers(),
                        files=files,
                        data=data,
                        timeout=90.0
                    )
                    if resp.status_code == 200:
                        st.success(f"Indexed under '{target_dept}' access successfully!")
                    else:
                        st.error(f"Error {resp.status_code}")
                except Exception as e:
                    st.error(f"Failed: {e}")

    # Bottom User Profile & Logout
    st.markdown("<div style='flex-grow: 1; height: 10vh;'></div>", unsafe_allow_html=True)
    user_initial = (st.session_state.username[0].upper()) if st.session_state.username else "U"
    active_dept = st.session_state.get("department", "general").upper()
    
    st.markdown(f"""
    <div class="user-profile-bar">
        <div class="user-avatar">{user_initial}</div>
        <div style="flex-grow: 1; overflow: hidden;">
            <div class="user-name">{st.session_state.username}</div>
            <div style="font-size: 0.72rem; color: #10a37f; font-weight: 600; letter-spacing: 0.04em;">{active_dept} ACCESS</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Log out", use_container_width=True):
        logout_action()


# ----------- MAIN CHAT AREA -----------

# Top Navigation Bar with Toggle Sidebar Button
st.markdown(f"""
<div class="top-nav-bar">
    <button class="nav-toggle-btn" onclick="
        const p = window.parent.document;
        const collapsedBtn = p.querySelector('[data-testid=stSidebarCollapsedControl] button, [data-testid=stSidebarCollapsedControl]');
        const collapseBtn = p.querySelector('[data-testid=stSidebarCollapseButton] button, [data-testid=stSidebarCollapseButton]');
        if (collapsedBtn && window.parent.getComputedStyle(collapsedBtn).display !== 'none' && collapsedBtn.offsetParent !== null) {{
            collapsedBtn.click();
        }} else if (collapseBtn) {{
            collapseBtn.click();
        }} else if (collapsedBtn) {{
            collapsedBtn.click();
        }}
    " title="Slide Sidebar">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
            <line x1="9" y1="3" x2="9" y2="21"></line>
        </svg>
        <span>Toggle Sidebar</span>
    </button>
    <div class="nav-brand">
        <div class="nav-brand-icon">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 2L2 7L12 12L22 7L12 2Z"/>
                <path d="M2 17L12 22L22 17"/>
                <path d="M2 12L12 17L22 12"/>
            </svg>
        </div>
        <span>Enterprise AI Copilot</span>
    </div>
    <div class="nav-user-badge">
        <span class="nav-user-dot"></span>
        <span>{st.session_state.username}</span>
        <span style="background: rgba(16, 163, 127, 0.18); color: #10a37f; border: 1px solid rgba(16, 163, 127, 0.35); padding: 1px 7px; border-radius: 6px; font-weight: 600; font-size: 0.72rem;">{active_dept}</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Empty State Hero
if not st.session_state.messages:
    st.markdown("""
    <div class="empty-hero">
        <div class="empty-hero-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 2L2 7L12 12L22 7L12 2Z"/>
                <path d="M2 17L12 22L22 17"/>
                <path d="M2 12L12 17L22 12"/>
            </svg>
        </div>
        <div class="empty-hero-title">What can I help with today?</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("📄  Summarize key enterprise documents", use_container_width=True):
            st.session_state.pending_prompt = "Summarize the key information from our uploaded enterprise documents."
            st.rerun()
    with col2:
        if st.button("🔍  Search company policies and guides", use_container_width=True):
            st.session_state.pending_prompt = "What are the company policies and key procedures described in the documentation?"
            st.rerun()

# Display Chat Messages
for msg in st.session_state.messages:
    role = msg.get("role", "user")
    content = msg.get("content", "")
    citations = msg.get("citations") or []

    avatar = "👤" if role == "user" else "🧠"
    with st.chat_message(role, avatar=avatar):
        st.markdown(content)
        
        # Clean Footnote Citations
        if role == "assistant" and citations:
            with st.expander(f"Sources ({len(citations)})", expanded=False):
                for idx, cit in enumerate(citations, 1):
                    doc_name = cit.get("source_file") or cit.get("document_name") or cit.get("source", "Source")
                    quote = cit.get("verbatim_quote") or cit.get("quote", "")
                    src_id = cit.get("source_id", idx)
                    st.markdown(f"""
                    <div class="citations-box">
                        <div class="citation-source">[{src_id}] {doc_name}</div>
                        <div class="citation-quote">"{quote}"</div>
                    </div>
                    """, unsafe_allow_html=True)

# Determine prompt from input or prompt suggestions
pending_query = st.session_state.pop("pending_prompt", None)
user_prompt = st.chat_input("Message AI Model...")

query_to_send = pending_query or user_prompt

if query_to_send:
    # Append user prompt immediately
    st.session_state.messages.append({
        "role": "user",
        "content": query_to_send,
        "citations": None
    })

    with st.chat_message("user", avatar="👤"):
        st.markdown(query_to_send)

    # Call Copilot Backend
    with st.chat_message("assistant", avatar="🧠"):
        with st.spinner("Thinking..."):
            try:
                params = {"q": query_to_send}
                if st.session_state.current_session_id:
                    params["session_id"] = st.session_state.current_session_id

                resp = httpx.get(
                    f"{st.session_state.backend_url}/search",
                    headers=get_headers(),
                    params=params,
                    timeout=90.0
                )

                if resp.status_code == 200:
                    data = resp.json()
                    answer = data.get("answer", "")
                    citations = data.get("citations", [])
                    st.session_state.current_session_id = data.get("session_id", st.session_state.current_session_id)
                    st.query_params["session_id"] = st.session_state.current_session_id

                    st.markdown(answer)

                    if citations:
                        with st.expander(f"Sources ({len(citations)})", expanded=False):
                            for idx, cit in enumerate(citations, 1):
                                doc_name = cit.get("source_file") or cit.get("document_name") or cit.get("source", "Source")
                                quote = cit.get("verbatim_quote") or cit.get("quote", "")
                                src_id = cit.get("source_id", idx)
                                st.markdown(f"""
                                <div class="citations-box">
                                    <div class="citation-source">[{src_id}] {doc_name}</div>
                                    <div class="citation-quote">"{quote}"</div>
                                </div>
                                """, unsafe_allow_html=True)

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer,
                        "citations": citations
                    })

                    # Refresh sidebar conversation list
                    fetch_user_conversations()

                else:
                    try:
                        err_detail = resp.json().get("detail", resp.text)
                    except Exception:
                        err_detail = resp.text
                    err_msg = f"Search error ({resp.status_code}): {err_detail}"
                    st.error(err_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": err_msg,
                        "citations": None
                    })

            except httpx.ConnectError:
                err_text = "Cannot connect to backend server. Please verify the API is running at `http://localhost:8000`."
                st.error(err_text)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": err_text,
                    "citations": None
                })
            except httpx.TimeoutException:
                err_text = "⚠️ Request timed out. If you uploaded a document, make sure to click **'Index document'** first. The AI provider may also be experiencing high latency or rate limits."
                st.error(err_text)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": err_text,
                    "citations": None
                })
            except Exception as e:
                err_text = f"An error occurred: {str(e)}"
                st.error(err_text)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": err_text,
                    "citations": None
                })

# Subtle AI Model footer disclaimer
st.markdown("<div class='footer-note'>AI Model can make mistakes. Check important info.</div>", unsafe_allow_html=True)
