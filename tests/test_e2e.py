import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestration.graph import create_graph

def test_end_to_end():
    """Test all 4 agent types end-to-end through the graph."""
    
    graph = create_graph()
    
    test_cases = [
        {
            "name": "Billing Query",
            "query": "Why is my bill so high this month?",
            "expected_classification": "billing"
        },
        {
            "name": "Network Query",
            "query": "My internet connection is very slow",
            "expected_classification": "network"
        },
        {
            "name": "Plan Query",
            "query": "Can you recommend a better plan for me?",
            "expected_classification": "plan"
        },
        {
            "name": "Knowledge Query",
            "query": "What is VoLTE and how does it work?",
            "expected_classification": "knowledge"
        }
    ]
    
    print("=" * 80)
    print("END-TO-END INTEGRATION TESTS")
    print("=" * 80)
    
    passed = 0
    failed = 0
    
    for test_case in test_cases:
        print(f"\n{'=' * 80}")
        print(f"Test: {test_case['name']}")
        print(f"Query: {test_case['query']}")
        print(f"Expected Classification: {test_case['expected_classification']}")
        print("-" * 80)
        
        try:
            initial_state = {
                "query": test_case["query"],
                "chat_history": [],
                "classification": None,
                "intermediate_responses": {},
                "final_response": None
            }
            
            result = graph.invoke(initial_state)
            
            classification = result.get("classification")
            response = result.get("final_response")
            
            print(f"Actual Classification: {classification}")
            print(f"Response Length: {len(response)} characters")
            print(f"Response Preview: {response[:200]}...")
            
            if classification == test_case["expected_classification"]:
                print("✅ PASSED - Classification correct")
                passed += 1
            else:
                print(f"❌ FAILED - Expected {test_case['expected_classification']}, got {classification}")
                failed += 1
                
        except Exception as e:
            print(f"❌ FAILED - Error: {str(e)}")
            failed += 1
    
    print(f"\n{'=' * 80}")
    print(f"SUMMARY: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print("=" * 80)
    
    return passed, failed

if __name__ == "__main__":
    passed, failed = test_end_to_end()
    sys.exit(0 if failed == 0 else 1)
