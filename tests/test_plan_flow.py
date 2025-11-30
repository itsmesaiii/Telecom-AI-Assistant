import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestration.graph import create_graph
from agents.service_agents import process_plan_query

def test_direct_plan_agent():
    print("--- Testing Direct Plan Agent ---")
    query = "Can you recommend a better plan for me?"
    try:
        response = process_plan_query(query, customer_id="CUST001")
        print("\nResponse:\n", response)
    except Exception as e:
        print(f"Error: {e}")

def test_graph_flow():
    print("\n--- Testing Graph Flow (Plan) ---")
    graph = create_graph()
    
    initial_state = {
        "query": "I want to upgrade my plan",
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
    test_direct_plan_agent()
    test_graph_flow()
