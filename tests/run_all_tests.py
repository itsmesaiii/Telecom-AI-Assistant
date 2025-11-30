import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_classification import test_classification
from test_e2e import test_end_to_end

def run_all_tests():
    """Run all test suites."""
    
    print("\n" + "=" * 80)
    print("TELECOM AI SYSTEM - COMPREHENSIVE TEST SUITE")
    print("=" * 80 + "\n")
    
    total_passed = 0
    total_failed = 0
    
    # Test 1: Classification
    print("\n[1/2] Running Classification Tests...")
    passed, failed = test_classification()
    total_passed += passed
    total_failed += failed
    
    # Test 2: End-to-End
    print("\n[2/2] Running End-to-End Tests...")
    passed, failed = test_end_to_end()
    total_passed += passed
    total_failed += failed
    
    # Final Summary
    print("\n" + "=" * 80)
    print("FINAL TEST SUMMARY")
    print("=" * 80)
    print(f"Total Passed: {total_passed}")
    print(f"Total Failed: {total_failed}")
    print(f"Success Rate: {(total_passed / (total_passed + total_failed) * 100):.1f}%")
    print("=" * 80 + "\n")
    
    return total_failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
