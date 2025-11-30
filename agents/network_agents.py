"""
Network Agent - AutoGen multi-agent troubleshooting system.
Checks account status first, then provides diagnostics or reactivation guidance.
"""

import autogen
from utils.database import db
from config.config import config

# Define network troubleshooting agents with database context
config_list = [{"model": "gpt-4o", "api_key": config.OPENAI_API_KEY}]

Diagnostics_Agent = autogen.AssistantAgent(
    name="Diagnostics_Agent",
    system_message="""You are a telecom network diagnostics specialist. 

CRITICAL INSTRUCTION: You will receive customer information including their account status.

**CHECK ACCOUNT STATUS FIRST:**
- If account status is "Suspended" or "Cancelled":
  → IMMEDIATELY inform the customer their account is suspended/cancelled
  → Explain this is WHY they can't make calls/use services  
  → Tell them to contact billing/customer service to reactivate
  → DO NOT provide generic network troubleshooting
  
- If account status is "Active":
  → Proceed with normal network diagnostic steps
  → Check signal, device settings, network outages, etc.

Always prioritize account status before any other troubleshooting!""",
    llm_config={"config_list": config_list, "temperature": 0.7}
)

Solution_Integrator = autogen.AssistantAgent(
    name="Solution_Integrator",
    system_message="""You are a network solution integrator providing final solutions.

Based on the diagnostics:
- If account is suspended → Provide clear steps to reactivate account
- If network issue → Provide step-by-step troubleshooting
- Be concise and actionable""",
    llm_config={"config_list": config_list, "temperature": 0.7}
)

user_proxy = autogen.UserProxyAgent(
    name="User_Proxy",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=0,
    is_termination_msg=lambda x: "TERMINATE" in x.get("content", ""),
    code_execution_config=False
)

# Setup group chat
groupchat = autogen.GroupChat(
    agents=[user_proxy, Diagnostics_Agent, Solution_Integrator],
    messages=[],
    max_round=6
)

manager = autogen.GroupChatManager(groupchat=groupchat, llm_config={"config_list": config_list})

def process_network_query(query, customer_email="user@example.com"):
    """Run the AutoGen network troubleshooting flow with customer context."""
    
    # Get customer info from database
    try:
        customer_query = """
        SELECT c.customer_id, c.name, c.account_status, c.service_plan_id,
               p.name as plan_name
        FROM customers c
        LEFT JOIN service_plans p ON c.service_plan_id = p.plan_id
        WHERE c.email = ?
        """
        customer_data = db.query_one(customer_query, [customer_email])
        
        if customer_data:
            customer_context = f"""
CUSTOMER INFORMATION (CHECK THIS FIRST!):
- Customer Name: {customer_data[1]}
- Account Status: {customer_data[2]} ← **CRITICAL: Check this first!**
- Current Plan: {customer_data[4]}
"""
        else:
            # Fallback to demo customer CUST001
            customer_context = f"Email '{customer_email}' not found. Using demo account.\n"
            customer_query_fallback = """
            SELECT c.customer_id, c.name, c.account_status, c.service_plan_id,
                   p.name as plan_name
            FROM customers c
            LEFT JOIN service_plans p ON c.service_plan_id = p.plan_id
            WHERE c.customer_id = 'CUST001'
            """
            customer_data = db.query_one(customer_query_fallback, [])
            if customer_data:
                customer_context += f"""
CUSTOMER INFORMATION (Demo Account):
- Customer Name: {customer_data[1]}
- Account Status: {customer_data[2]} ← **CRITICAL: Check this first!**
- Current Plan: {customer_data[4]}
"""
    except Exception as e:
        customer_context = f"Error fetching customer data: {str(e)}\nProceeding with generic troubleshooting."
    
    # Reset chat history
    groupchat.messages = []
    
    # Initiate chat with customer context
    chat_result = user_proxy.initiate_chat(
        manager,
        message=f"""{customer_context}

Customer Issue: {query}

IMPORTANT INSTRUCTIONS:
1. READ the account status above CAREFULLY
2. If account is Suspended/Cancelled → Address this IMMEDIATELY as the root cause
3. If account is Active → Then proceed with network diagnostics
4. End your final response with TERMINATE"""
    )
    
    # Extract the final response
    if chat_result.chat_history:
        agent_messages = [m for m in chat_result.chat_history if m['name'] != 'User_Proxy']
        if agent_messages:
            last_msg = agent_messages[-1]['content']
            return last_msg.replace("TERMINATE", "").strip()
    
    return "I'm sorry, I couldn't diagnose the network issue at this time."
