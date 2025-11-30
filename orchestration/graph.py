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

def classify_query(state: TelecomState):
    q = state.get("query", "").lower()

    if any(w in q for w in ["bill", "charge", "payment"]):
        state["classification"] = "billing"
    elif any(w in q for w in ["network", "signal", "data", "call", "internet", "slow"]):
        state["classification"] = "network"
    elif any(w in q for w in ["plan", "recommend", "upgrade", "downgrade"]):
        state["classification"] = "plan"
    else:
        state["classification"] = "knowledge"

    return state

def run_billing_agent(state: TelecomState):
    query = state.get("query")
    # In a real app, we'd get customer_id from state or context
    response = process_billing_query(query, customer_id="CUST001")
    state["intermediate_responses"] = {"result": response}
    return state

def run_network_agent(state: TelecomState):
    query = state.get("query")
    # Get customer email from state, fallback to CUST001's email
    customer_info = state.get("customer_info", {})
    customer_email = customer_info.get("email", "john.doe@example.com")  # CUST001's email
    
    response = process_network_query(query, customer_email)
    state["intermediate_responses"] = {"result": response}
    return state

def run_plan_agent(state: TelecomState):
    query = state.get("query")
    response = process_plan_query(query, customer_id="CUST001")
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
