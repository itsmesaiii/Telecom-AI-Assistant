"""
Sidebar Component
Handles login/logout functionality and navigation menu.
"""

import streamlit as st

def render_sidebar():
    """Render the sidebar with login form or user info."""
    with st.sidebar:
        st.header("Login")
        
        if not st.session_state.logged_in:
            email = st.text_input("Email", placeholder="user@example.com")
            user_type = st.selectbox("Login as", ["Customer", "Admin"])
            
            if st.button("Login", type="primary", use_container_width=True):
                if email:
                    st.session_state.logged_in = True
                    st.session_state.user_email = email
                    st.session_state.user_type = user_type
                    st.rerun()
                else:
                    st.error("Please enter your email")
        else:
            st.success(f"Logged in as **{st.session_state.user_type}**")
            st.write(f"{st.session_state.user_email}")
            
            if st.button("Logout", use_container_width=True):
                # Clear all session state on logout
                st.session_state.logged_in = False
                st.session_state.user_email = ""
                st.session_state.messages = {}
                st.session_state.graph_initialized = False
                st.session_state.graph = None
                if "account_data" in st.session_state:
                    del st.session_state.account_data
                st.rerun()
        
        st.divider()
        
        if st.session_state.logged_in:
            st.header("Services")
            st.markdown("""
            - Billing
            - Network
            - Plans
            - Knowledge
            """)
