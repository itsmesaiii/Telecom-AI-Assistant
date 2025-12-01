"""
Chat Interface Component
Renders the chat UI for interacting with AI agents.
"""

import streamlit as st

def render_chat_tab(tab_name, tab_obj):
    """Render unified chat interface with automatic query routing and agent indicators"""
    with tab_obj:
        # Use unified message history for AI Assistant
        if tab_name == "AI Assistant":
            message_key = "unified"
            placeholder = "Ask me anything about billing, network, plans, or general questions..."
        else:
            # Legacy support for old tab names (if needed)
            message_key = tab_name
            placeholder = f"Ask about {tab_name.lower()}..."
        
        # Initialize message history
        if message_key not in st.session_state.messages:
            st.session_state.messages[message_key] = []
        
        # Display chat history
        for msg in st.session_state.messages[message_key]:
            with st.chat_message(msg["role"]):
                # Escape $ to prevent LaTeX rendering
                st.markdown(msg["content"].replace("$", "\\$"))
        
        # Chat input at bottom
        if prompt := st.chat_input(placeholder, key=f"chat_{message_key}"):
            # Validate non-empty query
            if not prompt.strip():
                st.warning("Please enter a question")
                return
            
            st.session_state.messages[message_key].append({"role": "user", "content": prompt})
            
            try:
                # Build chat history for context (last 10 messages for efficiency)
                chat_history = []
                recent_messages = st.session_state.messages[message_key][-10:]  # Keep last 10 for context
                for msg in recent_messages:
                    # Remove agent indicators from history for cleaner context
                    content = msg["content"]
                    if msg["role"] == "assistant":
                        # Strip agent indicator if present (no emojis version)
                        for indicator in ["**Billing Agent**", "**Network Agent**", 
                                         "**Plan Advisor**", "**Knowledge Base**", "**AI Assistant**"]:
                            if content.startswith(indicator):
                                content = content.replace(indicator, "", 1).strip()
                                break
                    
                    chat_history.append({
                        "role": msg["role"],
                        "content": content
                    })
                
                # Invoke LangGraph with customer context and chat history
                result = st.session_state.graph.invoke({
                    "query": prompt,
                    "chat_history": chat_history,
                    "classification": None,
                    "intermediate_responses": {},
                    "final_response": None,
                    "customer_info": {"email": st.session_state.user_email}
                })
                
                # Get classification and response
                classification = result.get("classification", "knowledge")
                response = result.get("final_response", "No response")
                
                # Add agent indicator for unified chat (NO EMOJIS)
                if tab_name == "AI Assistant":
                    agent_indicators = {
                        "billing": "**Billing Agent**",
                        "network": "**Network Agent**",
                        "plan": "**Plan Advisor**",
                        "knowledge": "**Knowledge Base**"
                    }
                    
                    indicator = agent_indicators.get(classification, "**AI Assistant**")
                    formatted_response = f"{indicator}\n\n{response}"
                else:
                    formatted_response = response
                
                st.session_state.messages[message_key].append({"role": "assistant", "content": formatted_response})
                st.rerun()
            except Exception as e:
                st.session_state.messages[message_key].append({"role": "assistant", "content": f"Error: {str(e)}"})
                st.rerun()
