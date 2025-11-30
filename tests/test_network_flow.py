import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestration.graph import create_graph
from agents.network_agents import process_network_query

def test_direct_network_agent():
    print("--- Testing Direct Network Agent ---")
    query = "My internet is very slow and keeps dropping."
    try:
        response = process_network_query(query)
        print("\nResponse:\n", response)
    except Exception as e:
        print(f"Error: {e}")

def test_graph_flow():
    print("\n--- Testing Graph Flow (Network) ---")
    graph = create_graph()
    
    initial_state = {
        "query": "I have bad signal reception",
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
    test_direct_network_agent()
    test_graph_flow()
