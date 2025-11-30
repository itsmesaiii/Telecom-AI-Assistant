"""
Dashboard Component
Renders the 'My Account' dashboard with customer metrics and billing history.
"""

import streamlit as st
import pandas as pd
from services.customer_service import get_customer_profile, get_usage_history

def render_dashboard():
    """Render the customer account dashboard."""
    st.markdown("### My Account Dashboard")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Refresh Account Details", type="secondary", use_container_width=True):
            try:
                # Fetch data using service layer
                customer_id, customer_data = get_customer_profile(st.session_state.user_email)
                usage_data = get_usage_history(customer_id)
                
                st.session_state.account_data = {"customer": customer_data, "usage": usage_data}
                st.success("Account details loaded!")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    if "account_data" in st.session_state and st.session_state.account_data:
        cd = st.session_state.account_data["customer"]
        ud = st.session_state.account_data["usage"]
        
        if cd:
            st.divider()
            
            # Color-coded account status badge
            status = cd[5]
            if status == "Active":
                st.success(f"Account Status: **{status}**")
            elif status == "Suspended":
                st.error(f"Account Status: **{status}**")
            else:
                st.warning(f"Account Status: **{status}**")
            
            col1, col2 = st.columns(2)
            with col1:
                with st.container(border=True):
                    st.markdown("#### Personal Information")
                    st.write(f"**Name:** {cd[1]}")
                    st.write(f"**Email:** {cd[2]}")
                    st.write(f"**Phone:** {cd[3]}")
                    st.write(f"**Address:** {cd[4]}")
            
            with col2:
                with st.container(border=True):
                    st.markdown("#### Current Plan")
                    st.write(f"**Plan:** {cd[8]}")
                    st.write(f"**Cost:** \\${cd[9]}/month")
                    st.write(f"**Data:** {'Unlimited' if cd[13] else f'{cd[10]} GB'}")
                    st.write(f"**Voice:** {'Unlimited' if cd[14] else f'{cd[11]} min'}")
                    st.write(f"**SMS:** {'Unlimited' if cd[15] else f'{cd[12]}'}")
            
            st.divider()
            
            # Usage metrics with delta indicators
            if ud:
                st.markdown("### Recent Usage & Billing")
                latest = ud[0]
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        "Data Usage", 
                        f"{latest[2]:.1f} GB",
                        delta=f"{latest[2] - (cd[10] or 0):.1f} GB" if not cd[13] else "Unlimited",
                        delta_color="inverse"
                    )
                
                with col2:
                    st.metric(
                        "Voice Usage", 
                        f"{latest[3]} min",
                        delta=f"{latest[3] - (cd[11] or 0)} min" if not cd[14] else "Unlimited",
                        delta_color="inverse"
                    )
                
                with col3:
                    st.metric(
                        "SMS Usage", 
                        f"{latest[4]}",
                        delta=f"{latest[4] - (cd[12] or 0)}" if not cd[15] else "Unlimited",
                        delta_color="inverse"
                    )
                
                with col4:
                    st.metric(
                        "Latest Bill", 
                        f"\\${latest[6]:.2f}",
                        delta=f"\\${latest[5]:.2f} extra" if latest[5] > 0 else "No extras",
                        delta_color="inverse"
                    )
                
                st.write("")
                
                # Billing History Table
                with st.container(border=True):
                    st.markdown("#### Billing History")
                    df = pd.DataFrame(ud, columns=[
                        "Period Start", "Period End", "Data (GB)", 
                        "Voice (min)", "SMS", "Extra Charges", "Total Bill"
                    ])
                    df["Extra Charges"] = df["Extra Charges"].apply(lambda x: f"\\${x:.2f}")
                    df["Total Bill"] = df["Total Bill"].apply(lambda x: f"\\${x:.2f}")
                    st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Click the button above to load your account details")
