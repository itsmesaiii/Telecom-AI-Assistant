"""
Telecom AI Assistant - Multi-agent customer service system.
Integrates CrewAI, AutoGen, LangChain, and LlamaIndex for billing, network, plans, and knowledge base.
"""

import streamlit as st
import sys

# Import UI components
from ui.sidebar import render_sidebar
from ui.dashboard import render_dashboard
from ui.chat_interface import render_chat_tab

print("=" * 80)
print("STREAMLIT APP STARTING")
print("=" * 80)

st.set_page_config(
    page_title="Telecom AI Assistant",
    page_icon="📱",
    layout="wide"
)

print("✓ Page config set")

# Initialize session state variables
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_email" not in st.session_state:
    st.session_state.user_email = ""

if "user_type" not in st.session_state:
    st.session_state.user_type = "Customer"

if "messages" not in st.session_state:
    st.session_state.messages = {}

if "graph_initialized" not in st.session_state:
    st.session_state.graph_initialized = False
    st.session_state.graph = None

print(f"Login status: {st.session_state.logged_in}")

# Render Sidebar
render_sidebar()

# Main application content
if not st.session_state.logged_in:
    st.title("Telecom AI Assistant")
    st.markdown("### Welcome! Please login to continue.")
    st.info("Use the sidebar to login")
else:
    st.title(f"Telecom AI Assistant - {st.session_state.user_type} Portal")
    
    # Lazy-load LangGraph on first use to improve startup time
    if not st.session_state.graph_initialized:
        try:
            with st.spinner("Loading AI system..."):
                from orchestration.graph import create_graph
                st.session_state.graph = create_graph()
                st.session_state.graph_initialized = True
                st.success("AI System Ready!")
                st.rerun()
        except Exception as e:
            st.error(f"Failed to load AI system: {str(e)}")
            st.stop()
    
    # Create tabs
    tab0, tab1, tab2, tab3, tab4 = st.tabs([
        "My Account", "Billing", "Network", "Plans", "Knowledge"
    ])
    
    # My Account Tab
    with tab0:
        render_dashboard()
    
    # Service Tabs
    render_chat_tab("Billing", tab1)
    render_chat_tab("Network", tab2)
    render_chat_tab("Plans", tab3)
    render_chat_tab("Knowledge", tab4)

print("= " * 80)
print("APP RENDER COMPLETE")
print("= " * 80)
