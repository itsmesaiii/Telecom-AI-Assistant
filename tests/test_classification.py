import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestration.graph import create_graph

def test_classification():
    """Test query classification accuracy."""
    
    graph = create_graph()
    
    test_cases = [
        # Billing queries
        ("My bill is too high", "billing"),
        ("Why am I being charged extra?", "billing"),
        ("Explain my payment", "billing"),
        
        # Network queries
        ("No signal on my phone", "network"),
        ("Internet keeps dropping", "network"),
        ("Slow data connection", "network"),
        ("Call quality is poor", "network"),
        
        # Plan queries
        ("I want to upgrade my plan", "plan"),
        ("Recommend a better plan", "plan"),
        ("Should I downgrade?", "plan"),
        
        # Knowledge queries
        ("What is 5G?", "knowledge"),
        ("How does VoLTE work?", "knowledge"),
        ("Explain APN settings", "knowledge"),
    ]
    
    print("=" * 80)
    print("CLASSIFICATION ACCURACY TESTS")
    print("=" * 80)
    
    passed = 0
    failed = 0
    
    for query, expected in test_cases:
        try:
            initial_state = {
                "query": query,
                "chat_history": [],
                "classification": None,
                "intermediate_responses": {},
                "final_response": None
            }
            
            result = graph.invoke(initial_state)
            actual = result.get("classification")
            
            if actual == expected:
                print(f"✅ '{query}' -> {actual}")
                passed += 1
            else:
                print(f"❌ '{query}' -> Expected: {expected}, Got: {actual}")
                failed += 1
                
        except Exception as e:
            print(f"❌ '{query}' -> Error: {str(e)}")
            failed += 1
    
    print(f"\n{'=' * 80}")
    accuracy = (passed / len(test_cases)) * 100
    print(f"ACCURACY: {accuracy:.1f}% ({passed}/{len(test_cases)} correct)")
    print("=" * 80)
    
    return passed, failed

if __name__ == "__main__":
    passed, failed = test_classification()
    sys.exit(0 if failed == 0 else 1)
