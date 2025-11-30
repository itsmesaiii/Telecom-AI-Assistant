import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestration.graph import create_graph
from agents.knowledge_agents import process_knowledge_query

def test_direct_knowledge_agent():
    print("--- Testing Direct Knowledge Agent ---")
    query = "What is VoLTE?"
    try:
        response = process_knowledge_query(query)
        print("\nResponse:\n", response)
    except Exception as e:
        print(f"Error: {e}")

def test_graph_flow():
    print("\n--- Testing Graph Flow (Knowledge) ---")
    graph = create_graph()
    
    initial_state = {
        "query": "Explain 5G network deployment",
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
    test_direct_knowledge_agent()
    test_graph_flow()
