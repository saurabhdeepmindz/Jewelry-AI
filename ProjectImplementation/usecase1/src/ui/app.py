"""Jewelry AI — Streamlit application entry point.

Run with:
    streamlit run src/ui/app.py

Registers multi-page navigation and applies global page configuration.
All state is managed via st.session_state — no module-level globals.
"""
import streamlit as st

# ------------------------------------------------------------------
# Page configuration (must be the very first Streamlit call)
# ------------------------------------------------------------------
st.set_page_config(
    page_title="Jewelry AI",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------------------------------------------------
# Navigation
# ------------------------------------------------------------------

pages = {
    "Lead Management": [
        st.Page("pages/upload.py", title="Upload Leads", icon="📤"),
        st.Page("pages/lead_detail.py", title="Lead Detail", icon="🔍"),
    ],
    "Outreach": [
        st.Page("pages/outreach.py", title="Outreach Review", icon="✉️"),
    ],
}

pg = st.navigation(pages)
pg.run()
