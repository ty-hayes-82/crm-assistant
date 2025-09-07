"""
Test for the Company Management Agent
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from crm_agent.agents.specialized.company_management_agent import CompanyManagementAgent

def test_company_management_agent():
    """Test the Company Management Agent with various company names."""
    
    # Create the agent
    agent = CompanyManagementAgent()
    
    # Test cases
    test_cases = [
        {
            "company_name": "The Golf Club at Mansion Ridge",
            "expected_manager": "Troon",
            "description": "Exact match from the user's example"
        },
        {
            "company_name": "Mansion Ridge Golf Club", 
            "expected_manager": "Troon",
            "description": "Slight variation should still match"
        },
        {
            "company_name": "Purgatory Golf Club",
            "expected_manager": "Troon", 
            "description": "Another Troon course"
        },
        {
            "company_name": "Bandon Dunes Golf Resort",
            "expected_manager": "KemperSports",
            "description": "KemperSports course"
        },
        {
            "company_name": "Random Company Inc",
            "expected_manager": None,
            "description": "Non-golf course should not match"
        }
    ]
    
    print("🧪 Testing Company Management Agent")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['description']}")
        print(f"Company: {test_case['company_name']}")
        
        result = agent.run(test_case['company_name'], f"test_id_{i}")
        
        if result['status'] == 'success':
            print(f"✅ Found match: {result['management_company']} (score: {result['match_score']})")
            if test_case['expected_manager'] and result['management_company'] == test_case['expected_manager']:
                print("✅ Expected manager matched!")
            elif test_case['expected_manager']:
                print(f"❌ Expected {test_case['expected_manager']}, got {result['management_company']}")
        elif result['status'] == 'no_match':
            print("❌ No match found")
            if test_case['expected_manager'] is None:
                print("✅ Expected no match - correct!")
            else:
                print(f"❌ Expected {test_case['expected_manager']}, but got no match")
        else:
            print(f"❌ Error: {result.get('message', 'Unknown error')}")

if __name__ == "__main__":
    test_company_management_agent()
