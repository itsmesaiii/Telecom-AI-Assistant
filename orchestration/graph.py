"""
LangGraph Orchestrator - Routes queries to specialized agents.
Classifies intent and coordinates multi-agent responses.
"""

from langgraph.graph import StateGraph
from .state import TelecomState

from agents.billing_agents import process_billing_query
from agents.network_agents import process_network_query
from agents.service_agents import process_plan_query
from agents.knowledge_agents import process_knowledge_query

from openai import OpenAI
from dotenv import load_dotenv
import os
from .state import TelecomState 

load_dotenv()

try:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    VALID_CATEGORIES = ["billing", "network", "plan", "knowledge"]
except Exception:
    client = None

def classify_query(state: TelecomState):
    """Uses LLM to classify query for LangGraph routing."""
    if not client:
        state["classification"] = "knowledge"
        return state

    q = state.get("query", "")
    prompt = f"""
    Classify the user query into exactly one of these categories:
    {', '.join(VALID_CATEGORIES)}

    Query: "{q}"

    Respond with ONLY the category name, nothing else. Response must be lowercase.
    """

    # 1. API Call
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a classifier and must only output one word from the list."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=10,
            temperature=0
        )
        category = resp.choices[0].message.content.strip().lower()

    except Exception:
        # Fallback on API failure
        category = "knowledge"
        
    # 2. Validation and State Update
    if category in VALID_CATEGORIES:
        state["classification"] = category
    else:
        # Fallback on invalid LLM output
        state["classification"] = "knowledge"
    
    return state

def run_billing_agent(state: TelecomState):
    from utils.database import db
    
    query = state.get("query")
    
    # Get customer email from state
    customer_info = state.get("customer_info", {})
    customer_email = customer_info.get("email", "")
    
    # Look up customer_id from email
    customer_id = "CUST001"  # Default fallback
    if customer_email:
        email_query = "SELECT customer_id FROM customers WHERE email = ?"
        result = db.query_one(email_query, [customer_email])
        if result:
            customer_id = result[0]
    
    response = process_billing_query(query, customer_id=customer_id)
    state["intermediate_responses"] = {"result": response}
    return state

def run_network_agent(state: TelecomState):
    query = state.get("query")
    # Get customer email from state
    customer_info = state.get("customer_info", {})
    customer_email = customer_info.get("email", "")  # No hardcoded fallback
    
    response = process_network_query(query, customer_email)
    state["intermediate_responses"] = {"result": response}
    return state

def run_plan_agent(state: TelecomState):
    from utils.database import db
    
    query = state.get("query")
    
    # Get customer email from state
    customer_info = state.get("customer_info", {})
    customer_email = customer_info.get("email", "")
    
    # Look up customer_id from email
    customer_id = "CUST001"  # Default fallback
    if customer_email:
        email_query = "SELECT customer_id FROM customers WHERE email = ?"
        result = db.query_one(email_query, [customer_email])
        if result:
            customer_id = result[0]
    
    response = process_plan_query(query, customer_id=customer_id)
    state["intermediate_responses"] = {"result": response}
    return state

def run_knowledge_agent(state: TelecomState):
    query = state.get("query")
    response = process_knowledge_query(query)
    state["intermediate_responses"] = {"result": response}
    return state

def make_placeholder(name):
    def node(state: TelecomState):
        state["intermediate_responses"] = {
            "result": f"{name} processed — {state['query']}"
        }
        return state
    return node

def finalize(state: TelecomState):
    state["final_response"] = list(state["intermediate_responses"].values())[0]
    return state

def create_graph():
    sg = StateGraph(TelecomState)

    sg.add_node("classify_query", classify_query)
    sg.add_node("billing_node", run_billing_agent)
    sg.add_node("network_node", run_network_agent)
    sg.add_node("plan_node", run_plan_agent)
    sg.add_node("knowledge_node", run_knowledge_agent)
    sg.add_node("finalize", finalize)

    def router(state: TelecomState):
        return {
            "billing": "billing_node",
            "network": "network_node",
            "plan": "plan_node",
            "knowledge": "knowledge_node",
        }.get(state["classification"], "knowledge_node")

    sg.add_conditional_edges(
        "classify_query",
        router,
        {
            "billing_node": "billing_node",
            "network_node": "network_node",
            "plan_node": "plan_node",
            "knowledge_node": "knowledge_node",
        }
    )

    sg.add_edge("billing_node", "finalize")
    sg.add_edge("network_node", "finalize")
    sg.add_edge("plan_node", "finalize")
    sg.add_edge("knowledge_node", "finalize")

    sg.set_entry_point("classify_query")

    return sg.compile()
