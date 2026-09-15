"""
main.py  ←  Run with:  streamlit run main.py
Entry point — wires the sidebar, session state, and chat UI together.
"""
import streamlit as st
from tools.dashboard_tools import DEFAULT_CONFIG

# ── Page config ───────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Data Analyst Assistant",
    page_icon="🤖",
    layout="wide",
)
st.title("🤖 AI Data Analysis Agent — Interactive Dashboard Builder")

# ── Session state defaults ────────────────────────────────────────────────
if "data"             not in st.session_state:
    st.session_state.data = None
if "chat_history"     not in st.session_state:
    st.session_state.chat_history = []
if "dashboard_config" not in st.session_state:
    st.session_state.dashboard_config = DEFAULT_CONFIG.copy()

# ── Sidebar (returns api_key and the uploaded file object) ────────────────
from ui.sidebar import render_sidebar
api_key, uploaded_file = render_sidebar()

# ── Main area ─────────────────────────────────────────────────────────────
if st.session_state.data is not None and api_key:
    from ui.chat_interface import render_chat
    render_chat(api_key)
else:
    from ui.welcome import render_welcome
    render_welcome()
