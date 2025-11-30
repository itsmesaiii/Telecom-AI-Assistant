"""
Service Plan Agent - LangChain with tool-calling for plan recommendations.
Uses database tools to fetch plans and user usage for personalized suggestions.
"""

from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from config.config import config
from utils.database import db

# 1. Define Tools
@tool
def get_available_plans():
    """Fetch all available service plans from the database."""
    sql = "SELECT plan_id, name, monthly_cost, data_limit_gb, voice_minutes, sms_count FROM service_plans"
    plans = db.query(sql)
    return str(plans)

@tool
def get_user_usage(customer_id: str):
    """Fetch the current usage and plan details for a specific customer."""
    sql = """
    SELECT c.service_plan_id, u.data_used_gb, u.voice_minutes_used, u.sms_count_used, p.name
    FROM customers c
    JOIN customer_usage u ON c.customer_id = u.customer_id
    JOIN service_plans p ON c.service_plan_id = p.plan_id
    WHERE c.customer_id = ?
    ORDER BY u.billing_period_end DESC
    LIMIT 1
    """
    usage = db.query_one(sql, [customer_id])
    if not usage:
        return "No usage data found."
    return str(usage)

# 2. Process Function
def process_plan_query(query, customer_id="CUST001"):
    """Run the plan recommendation logic using LLM with tools."""
    llm = ChatOpenAI(model="gpt-4o", api_key=config.OPENAI_API_KEY, temperature=0)
    
    tools = [get_available_plans, get_user_usage]
    llm_with_tools = llm.bind_tools(tools)
    
    # Get usage data
    usage_data = get_user_usage.invoke({"customer_id": customer_id})
    plans_data = get_available_plans.invoke({})
    
    # Create a prompt with the data
    prompt = f"""You are a helpful telecom service plan advisor.

Customer Query: {query}
Customer ID: {customer_id}

Current Usage Data:
{usage_data}

Available Plans:
{plans_data}

Based on the customer's current usage and available plans, provide a recommendation. 
Analyze if they are on the optimal plan or if they should upgrade/downgrade."""
    
    try:
        response = llm.invoke(prompt)
        return response.content
    except Exception as e:
        return f"Error processing plan query: {str(e)}"
