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
    """Uses LLM to classify query for LangGraph routing with multi-intent detection."""
    if not client:
        state["classification"] = "knowledge"
        return state

    q = state.get("query", "")
    
    # Enhanced prompt for multi-intent detection
    prompt = f"""
    Analyze the user query and classify it into categories.
    
    Available categories: {', '.join(VALID_CATEGORIES)}
    
    Query: "{q}"
    
    Category Definitions:
    - billing: Questions about bills, charges, payments, invoices, costs
    - network: Connectivity PROBLEMS (can't connect, slow speed, no signal, not working)
    - plan: Service plan recommendations, upgrades, downgrades, plan comparisons
    - knowledge: General INFORMATION about features, coverage areas, technical specs, how things work
    
    Instructions:
    1. If the query has MULTIPLE intents (e.g., asking about both billing AND network), 
       respond with: "multi-intent: <category1>, <category2>"
    2. If the query has ONE clear intent, respond with just the category name
    3. All responses must be lowercase
    
    Examples:
    - "What's my bill?" -> billing
    - "My internet is slow" -> network
    - "My 5G is not working" -> network
    - "Can't connect to 5G" -> network
    - "What areas have 5G coverage?" -> knowledge
    - "Tell me about 5G" -> knowledge
    - "What is VoLTE?" -> knowledge
    - "Explain APN settings" -> knowledge
    - "Which plan should I choose?" -> plan
    - "I need help with my bill and my network is down" -> multi-intent: billing, network
    
    Respond with ONLY the classification, nothing else.
    """

    # 1. API Call
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a precise classifier. Follow instructions exactly."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=30,
            temperature=0
        )
        result = resp.choices[0].message.content.strip().lower()

    except Exception:
        # Fallback on API failure
        state["classification"] = "knowledge"
        return state
    
    # 2. Handle multi-intent queries
    if result.startswith("multi-intent"):
        # Extract categories
        categories_str = result.replace("multi-intent:", "").strip()
        categories = [cat.strip() for cat in categories_str.split(",")]
        
        # For now, use the first valid category and store multi-intent flag
        primary_category = None
        for cat in categories:
            if cat in VALID_CATEGORIES:
                primary_category = cat
                break
        
        if primary_category:
            state["classification"] = primary_category
            state["multi_intent"] = True
            state["all_intents"] = [cat for cat in categories if cat in VALID_CATEGORIES]
        else:
            # Fallback if no valid category found
            state["classification"] = "knowledge"
            state["multi_intent"] = False
    else:
        # Single intent - validate and set
        if result in VALID_CATEGORIES:
            state["classification"] = result
            state["multi_intent"] = False
        else:
            # Fallback on invalid LLM output
            state["classification"] = "knowledge"
            state["multi_intent"] = False
    
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
    # Add multi-intent notification if detected
    response = list(state["intermediate_responses"].values())[0]
    
    if state.get("multi_intent", False):
        all_intents = state.get("all_intents", [])
        if len(all_intents) > 1:
            other_intents = [intent for intent in all_intents if intent != state.get("classification")]
            if other_intents:
                intent_names = {"billing": "billing", "network": "network issues", "plan": "plan recommendations", "knowledge": "general questions"}
                other_topics = ", ".join([intent_names.get(i, i) for i in other_intents])
                response += f"\n\n💡 *I noticed you also asked about {other_topics}. Feel free to ask about that separately!*"
    
    state["final_response"] = response
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
