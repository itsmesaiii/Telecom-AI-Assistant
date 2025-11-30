import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestration.graph import create_graph
from agents.billing_agents import process_billing_query

def test_direct_billing_agent():
    print("--- Testing Direct Billing Agent ---")
    query = "Why is my bill so high this month?"
    try:
        response = process_billing_query(query, customer_id="CUST001")
        print("\nResponse:\n", response)
    except Exception as e:
        print(f"Error: {e}")

def test_graph_flow():
    print("\n--- Testing Graph Flow (Billing) ---")
    graph = create_graph()
    
    initial_state = {
        "query": "I have a question about my bill charges",
        "chat_history": [],
        "classification": None,
        "intermediate_responses": {},
        "final_response": None
    }
    
    try:
        result = graph.invoke(initial_state)
        print("\nFinal State Classification:", result.get("classification"))
        print("Final Response:\n", result.get("final_response"))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_direct_billing_agent()
    test_graph_flow()
