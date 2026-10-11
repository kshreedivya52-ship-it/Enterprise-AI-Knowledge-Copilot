import os
import streamlit as st
import httpx
from typing import Optional, List, Dict, Any

# Ensure core fallback modules can be imported if needed
try:
    from app.core.user_store import verify_user, register_user
    from app.core.auth import create_access_token
except ImportError:
    verify_user = None
    register_user = None
    create_access_token = None

# Page Configuration
st.set_page_config(
    page_title="AI Model",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom AI Model Aesthetic CSS
st.markdown("""
<style>
    /* Global styles */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Clean background & eliminate extra padding */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 5rem !important;
        max-width: 820px !important;
    }

    /* Hide standard Streamlit header & footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Sidebar styles */
    section[data-testid="stSidebar"] {
        background-color: #171717 !important;
        border-right: 1px solid #262626 !important;
    }
    section[data-testid="stSidebar"] * {
        color: #ECECEC !important;
    }
    
    /* New Chat button */
    .stButton>button {
        border-radius: 8px !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
    }
    .new-chat-btn>div>button {
        background-color: transparent !important;
        border: 1px solid #333333 !important;
        color: #ECECEC !important;
        width: 100% !important;
        text-align: left !important;
        padding: 0.6rem 0.9rem !important;
    }
    .new-chat-btn>div>button:hover {
        background-color: #212121 !important;
        border-color: #4D4D4D !important;
    }

    /* Conversation thread item */
    .conv-item {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.55rem 0.75rem;
        border-radius: 8px;
        margin-bottom: 3px;
        cursor: pointer;
        color: #ECECEC;
        font-size: 0.88rem;
        transition: background 0.15s ease;
    }
    .conv-item:hover {
        background-color: #212121;
    }
    .conv-item.active {
        background-color: #262626;
        font-weight: 500;
    }

    /* Clean Empty State Hero */
    .empty-hero {
        text-align: center;
        margin-top: 15vh;
        margin-bottom: 2rem;
    }
    .empty-hero-icon {
        width: 44px;
        height: 44px;
        border-radius: 50%;
        background: #10a37f;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 1rem;
        box-shadow: 0 4px 12px rgba(16, 163, 127, 0.25);
    }
    .empty-hero-title {
        font-size: 1.65rem;
        font-weight: 600;
        color: inherit;
        letter-spacing: -0.02em;
    }

    /* Prompt Suggestion Pill */
    .prompt-pill {
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-radius: 12px;
        padding: 0.9rem 1.1rem;
        font-size: 0.86rem;
        color: inherit;
        cursor: pointer;
        transition: all 0.2s ease;
        margin-bottom: 0.6rem;
        height: 100%;
    }
    .prompt-pill:hover {
        border-color: rgba(128, 128, 128, 0.4);
        background-color: rgba(128, 128, 128, 0.05);
    }

    /* Citations footnote pill */
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

    /* Minimalist login card */
    .login-container {
        max-width: 380px;
        margin: 12vh auto 0 auto;
        padding: 2.2rem;
        border-radius: 14px;
        border: 1px solid rgba(128, 128, 128, 0.2);
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.08);
        text-align: center;
    }
    .login-logo {
        width: 44px;
        height: 44px;
        border-radius: 50%;
        background: #10a37f;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 1rem;
    }
    .login-title {
        font-size: 1.35rem;
        font-weight: 600;
        margin-bottom: 0.4rem;
    }
    .login-sub {
        font-size: 0.86rem;
        opacity: 0.7;
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

# Backend default URL
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
            st.session_state.current_session_id = None
            st.session_state.messages = []
            return True
    except Exception:
        pass

    # 2. Local Fallback
    if verify_user and create_access_token:
        user_info = verify_user(username_input, password_input)
        if user_info:
            token = create_access_token({
                "sub": user_info["username"],
                "role": user_info["role"],
                "department": user_info["department"]
            })
            st.session_state.logged_in = True
            st.session_state.username = user_info["username"]
            st.session_state.auth_token = token
            st.session_state.current_session_id = None
            st.session_state.messages = []
            return True

    st.error("Invalid username or password.")
    return False


def register_action(username_input: str, password_input: str) -> bool:
    """Attempts user registration via backend API first, with local store fallback."""
    username_input = username_input.strip().lower()
    if not username_input or not password_input:
        st.error("Please enter both username and password.")
        return False

    # 1. Try Backend API
    try:
        resp = httpx.post(
            f"{st.session_state.backend_url}/auth/register",
            json={"username": username_input, "password": password_input},
            timeout=5.0
        )
        if resp.status_code == 200:
            data = resp.json()
            st.session_state.logged_in = True
            st.session_state.username = data.get("username", username_input)
            st.session_state.auth_token = data.get("access_token")
            st.session_state.current_session_id = None
            st.session_state.messages = []
            return True
    except Exception:
        pass

    # 2. Local Fallback
    if register_user and create_access_token:
        created = register_user(username_input, password_input)
        if created:
            token = create_access_token({
                "sub": username_input,
                "role": "editor",
                "department": "general"
            })
            st.session_state.logged_in = True
            st.session_state.username = username_input
            st.session_state.auth_token = token
            st.session_state.current_session_id = None
            st.session_state.messages = []
            return True
        else:
            st.error("Username already exists. Please choose another.")
            return False

    st.error("Registration failed. Please try again.")
    return False


def logout_action():
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.auth_token = None
    st.session_state.current_session_id = None
    st.session_state.messages = []
    st.session_state.conversations = []
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
            fetch_user_conversations()
            st.rerun()
    except Exception as e:
        st.error(f"Could not delete: {e}")


# ==========================================
# VIEW 1: AUTHENTICATION (LOGIN / SIGN UP)
# ==========================================
if not st.session_state.logged_in:
    col_l, col_m, col_r = st.columns([1, 1.2, 1])
    with col_m:
        st.markdown("""
        <div class="login-container">
            <div class="login-logo">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M2 17L12 22L22 17" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M2 12L12 17L22 12" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </div>
            <div class="login-title">Welcome back</div>
            <div class="login-sub">Log in or create an account to start chatting</div>
        </div>
        """, unsafe_allow_html=True)

        tab_login, tab_register = st.tabs(["Log in", "Sign up"])

        with tab_login:
            with st.form("login_form", clear_on_submit=False):
                l_user = st.text_input("Username", placeholder="e.g. admin or your username", key="l_user")
                l_pass = st.text_input("Password", type="password", placeholder="Enter your password", key="l_pass")
                submit_login = st.form_submit_button("Continue", use_container_width=True, type="primary")

                if submit_login:
                    if login_action(l_user, l_pass):
                        fetch_user_conversations()
                        st.rerun()

            st.caption("Default demo accounts: `admin` / `admin123` or `user` / `user123`")

        with tab_register:
            with st.form("register_form", clear_on_submit=False):
                r_user = st.text_input("Username", placeholder="Choose a username", key="r_user")
                r_pass = st.text_input("Password", type="password", placeholder="Create a password", key="r_pass")
                submit_reg = st.form_submit_button("Create account", use_container_width=True, type="primary")

                if submit_reg:
                    if register_action(r_user, r_pass):
                        fetch_user_conversations()
                        st.rerun()

    st.stop()


# ==========================================
# VIEW 2: CHATBOT INTERFACE (AI MODEL)
# ==========================================

# Auto-fetch conversations on first load
if not st.session_state.conversations and st.session_state.logged_in:
    fetch_user_conversations()

# ----------- SIDEBAR -----------
with st.sidebar:
    # New chat button
    col_new_chat, col_refresh = st.columns([0.82, 0.18])
    with col_new_chat:
        if st.button("＋  New chat", use_container_width=True, type="secondary"):
            st.session_state.current_session_id = None
            st.session_state.messages = []
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
        uploaded_doc = st.file_uploader("Upload file", type=["pdf", "txt", "md", "docx"], label_visibility="collapsed")
        if uploaded_doc and st.button("Index document", use_container_width=True):
            with st.spinner("Indexing..."):
                try:
                    files = {"file": (uploaded_doc.name, uploaded_doc.getvalue(), uploaded_doc.type)}
                    resp = httpx.post(
                        f"{st.session_state.backend_url}/ingest/upload",
                        headers=get_headers(),
                        files=files,
                        timeout=90.0
                    )
                    if resp.status_code == 200:
                        st.success("Indexed successfully!")
                    else:
                        st.error(f"Error {resp.status_code}")
                except Exception as e:
                    st.error(f"Failed: {e}")

    # Bottom User Profile & Logout
    st.markdown("<div style='flex-grow: 1; height: 10vh;'></div>", unsafe_allow_html=True)
    user_initial = (st.session_state.username[0].upper()) if st.session_state.username else "U"
    
    st.markdown(f"""
    <div class="user-profile-bar">
        <div class="user-avatar">{user_initial}</div>
        <div class="user-name">{st.session_state.username}</div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Log out", use_container_width=True):
        logout_action()


# ----------- MAIN CHAT AREA -----------

# Empty State Hero (AI Model)
if not st.session_state.messages:
    st.markdown("""
    <div class="empty-hero">
        <div class="empty-hero-icon">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M2 17L12 22L22 17" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M2 12L12 17L22 12" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
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

# Display Messages
for msg in st.session_state.messages:
    role = msg.get("role", "user")
    content = msg.get("content", "")
    citations = msg.get("citations") or []

    avatar = "👤" if role == "user" else "🧠"
    with st.chat_message(role, avatar=avatar):
        st.markdown(content)
        
        # Clean Footnote Citations (no clunky labels)
        if role == "assistant" and citations:
            with st.expander(f"Sources ({len(citations)})", expanded=False):
                for idx, cit in enumerate(citations, 1):
                    doc_name = cit.get("document_name") or cit.get("source", "Source")
                    quote = cit.get("verbatim_quote") or cit.get("quote", "")
                    st.markdown(f"""
                    <div class="citations-box">
                        <div class="citation-source">[{idx}] {doc_name}</div>
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
                    timeout=60.0
                )

                if resp.status_code == 200:
                    data = resp.json()
                    answer = data.get("answer", "")
                    citations = data.get("citations", [])
                    st.session_state.current_session_id = data.get("session_id", st.session_state.current_session_id)

                    st.markdown(answer)

                    if citations:
                        with st.expander(f"Sources ({len(citations)})", expanded=False):
                            for idx, cit in enumerate(citations, 1):
                                doc_name = cit.get("document_name") or cit.get("source", "Source")
                                quote = cit.get("verbatim_quote") or cit.get("quote", "")
                                st.markdown(f"""
                                <div class="citations-box">
                                    <div class="citation-source">[{idx}] {doc_name}</div>
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
                    err_msg = "Sorry, I encountered an error processing your request."
                    st.error(err_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": err_msg,
                        "citations": None
                    })

            except httpx.ConnectError:
                err_text = "Cannot connect to the server. Please ensure the backend is running (`uvicorn app.main:app --reload`)."
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
