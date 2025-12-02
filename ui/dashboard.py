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
    
    # Quick Bill Summary Card (Feature #2)
    if "account_data" in st.session_state and st.session_state.account_data:
        cd = st.session_state.account_data.get("customer")
        ud = st.session_state.account_data.get("usage")
        
        if cd and ud:
            latest = ud[0]
            bill_amount = latest[6]
            
            # Calculate days until next bill (assuming 30-day cycle)
            from datetime import datetime, timedelta
            try:
                last_bill_date = datetime.strptime(cd[7], "%Y-%m-%d")
                next_bill_date = last_bill_date + timedelta(days=30)
                days_until_bill = (next_bill_date - datetime.now()).days
            except:
                days_until_bill = 0
            
            # Bill summary card
            with st.container(border=True):
                col_bill1, col_bill2, col_bill3 = st.columns([2, 2, 1])
                with col_bill1:
                    st.markdown(f"### 💳 Current Bill: **₹{bill_amount:.2f}**")
                with col_bill2:
                    if days_until_bill > 0:
                        st.markdown(f"📅 Next bill in **{days_until_bill} days**")
                    else:
                        st.markdown(f"📅 Bill due soon")
                with col_bill3:
                    status = cd[5]
                    if status == "Active":
                        st.markdown("✅ **Active**")
                    elif status == "Suspended":
                        st.markdown("🔴 **Suspended**")
                    else:
                        st.markdown(f"⚠️ **{status}**")
            
            st.write("")
    
    # Quick Stats Cards (Feature #3)
    if "account_data" in st.session_state and st.session_state.account_data:
        cd = st.session_state.account_data.get("customer")
        ud = st.session_state.account_data.get("usage")
        
        if cd and ud:
            latest = ud[0]
            
            # Calculate stats
            from datetime import datetime, timedelta
            try:
                last_bill_date = datetime.strptime(cd[7], "%Y-%m-%d")
                next_bill_date = last_bill_date + timedelta(days=30)
                days_left = (next_bill_date - datetime.now()).days
            except:
                days_left = 0
            
            # Data remaining calculation
            if not cd[13]:  # Not unlimited
                data_remaining = cd[10] - latest[2]
            else:
                data_remaining = "∞"
            
            # Display stats
            stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
            
            with stat_col1:
                st.metric("Days Left", f"{days_left}" if days_left > 0 else "Due", 
                         delta=None)
            
            with stat_col2:
                if data_remaining != "∞":
                    st.metric("Data Left", f"{data_remaining:.1f} GB",
                             delta=f"-{latest[2]:.1f} GB used",
                             delta_color="inverse")
                else:
                    st.metric("Data Left", "Unlimited", delta="∞")
            
            with stat_col3:
                st.metric("Current Bill", f"₹{latest[6]:.2f}",
                         delta=f"₹{latest[5]:.2f} extra" if latest[5] > 0 else "No extras",
                         delta_color="inverse" if latest[5] > 0 else "off")
            
            with stat_col4:
                status = cd[5]
                status_emoji = "✅" if status == "Active" else "🔴" if status == "Suspended" else "⚠️"
                st.metric("Status", status_emoji, delta=status, delta_color="off")
            
            st.write("")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Refresh Account Details", type="secondary", use_container_width=True):
            try:
                # Fetch data using service layer
                customer_id, customer_data = get_customer_profile(st.session_state.user_email)
                
                if customer_id is None or customer_data is None:
                    st.error(f"Email '{st.session_state.user_email}' is not registered in our system. Please contact customer service.")
                else:
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
                    st.write(f"**Cost:** ₹{cd[9]}/month")
                    st.write(f"**Data:** {'Unlimited' if cd[13] else f'{cd[10]} GB'}")
                    st.write(f"**Voice:** {'Unlimited' if cd[14] else f'{cd[11]} min'}")
                    st.write(f"**SMS:** {'Unlimited' if cd[15] else f'{cd[12]}'}")
            
            st.divider()
            
            # Usage Progress Bars (Feature #1)
            if ud:
                st.markdown("### Recent Usage & Billing")
                latest = ud[0]
                
                # Calculate days remaining in billing cycle
                from datetime import datetime, timedelta
                try:
                    last_bill_date = datetime.strptime(cd[7], "%Y-%m-%d")
                    next_bill_date = last_bill_date + timedelta(days=30)
                    days_remaining = (next_bill_date - datetime.now()).days
                except:
                    days_remaining = 0
                
                with st.container(border=True):
                    # Data Usage Progress Bar
                    st.markdown("#### 📊 Data Usage")
                    if not cd[13]:  # Not unlimited
                        data_used = latest[2]
                        data_limit = cd[10]
                        data_percent = (data_used / data_limit * 100) if data_limit > 0 else 0
                        data_remaining = data_limit - data_used
                        
                        # Color coding
                        if data_percent < 70:
                            bar_color = "🟢"
                            status_text = "Safe"
                        elif data_percent < 90:
                            bar_color = "🟡"
                            status_text = "Warning"
                        else:
                            bar_color = "🔴"
                            status_text = "High Usage"
                        
                        col_data1, col_data2 = st.columns([3, 1])
                        with col_data1:
                            st.progress(min(data_percent / 100, 1.0))
                        with col_data2:
                            st.markdown(f"**{data_percent:.0f}%**")
                        
                        st.markdown(f"{bar_color} **{data_used:.1f} GB** / {data_limit} GB used • **{data_remaining:.1f} GB** remaining • {days_remaining} days left • *{status_text}*")
                    else:
                        st.markdown("🟢 **Unlimited Data** • No limits!")
                    
                    st.write("")
                    
                    # Voice Usage Progress Bar
                    st.markdown("#### 📞 Voice Usage")
                    if not cd[14]:  # Not unlimited
                        voice_used = latest[3]
                        voice_limit = cd[11]
                        voice_percent = (voice_used / voice_limit * 100) if voice_limit > 0 else 0
                        voice_remaining = voice_limit - voice_used
                        
                        # Color coding
                        if voice_percent < 70:
                            bar_color = "🟢"
                            status_text = "Safe"
                        elif voice_percent < 90:
                            bar_color = "🟡"
                            status_text = "Warning"
                        else:
                            bar_color = "🔴"
                            status_text = "High Usage"
                        
                        col_voice1, col_voice2 = st.columns([3, 1])
                        with col_voice1:
                            st.progress(min(voice_percent / 100, 1.0))
                        with col_voice2:
                            st.markdown(f"**{voice_percent:.0f}%**")
                        
                        st.markdown(f"{bar_color} **{voice_used} min** / {voice_limit} min used • **{voice_remaining} min** remaining • *{status_text}*")
                    else:
                        st.markdown("🟢 **Unlimited Voice** • No limits!")
                    
                    st.write("")
                    
                    # SMS Usage Progress Bar
                    st.markdown("#### 💬 SMS Usage")
                    if not cd[15]:  # Not unlimited
                        sms_used = latest[4]
                        sms_limit = cd[12]
                        sms_percent = (sms_used / sms_limit * 100) if sms_limit > 0 else 0
                        sms_remaining = sms_limit - sms_used
                        
                        # Color coding
                        if sms_percent < 70:
                            bar_color = "🟢"
                            status_text = "Safe"
                        elif sms_percent < 90:
                            bar_color = "🟡"
                            status_text = "Warning"
                        else:
                            bar_color = "🔴"
                            status_text = "High Usage"
                        
                        col_sms1, col_sms2 = st.columns([3, 1])
                        with col_sms1:
                            st.progress(min(sms_percent / 100, 1.0))
                        with col_sms2:
                            st.markdown(f"**{sms_percent:.0f}%**")
                        
                        st.markdown(f"{bar_color} **{sms_used}** / {sms_limit} SMS used • **{sms_remaining}** remaining • *{status_text}*")
                    else:
                        st.markdown("🟢 **Unlimited SMS** • No limits!")
                    
                    st.write("")
                    
                    # Latest Bill Summary
                    st.markdown("#### 💰 Latest Bill")
                    if latest[5] > 0:
                        st.markdown(f"**₹{latest[6]:.2f}** (Base: ₹{cd[9]:.2f} + Extra: ₹{latest[5]:.2f})")
                    else:
                        st.markdown(f"**₹{latest[6]:.2f}** (No additional charges)")
                
                st.write("")
                
                # Billing History Table
                with st.container(border=True):
                    st.markdown("#### Billing History")
                    df = pd.DataFrame(ud, columns=[
                        "Period Start", "Period End", "Data (GB)", 
                        "Voice (min)", "SMS", "Extra Charges", "Total Bill"
                    ])
                    df["Extra Charges"] = df["Extra Charges"].apply(lambda x: f"₹{x:.2f}")
                    df["Total Bill"] = df["Total Bill"].apply(lambda x: f"₹{x:.2f}")
                    st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Click the button above to load your account details")
