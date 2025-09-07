"""
Specific test for Cross Creek matching issue
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from crm_agent.agents.specialized.company_management_agent import CompanyManagementAgent

def test_cross_creek_matching():
    """Test the specific Cross Creek matching logic using the agent."""
    
    # Test the problematic case
    company_name = "Cross Creek Golf Course"
    
    print(f"🔍 Testing improved matching for: '{company_name}'")
    print("=" * 60)
    
    # Create the agent and run the test
    agent = CompanyManagementAgent()
    result = agent.run(company_name, "test_id")
    
    print(f"Agent Result:")
    print(f"  Status: {result['status']}")
    if result['status'] == 'success':
        print(f"  Management Company: {result['management_company']}")
        print(f"  Match Score: {result['match_score']}")
        print(f"  Matched Course: {result['matched_course']}")
        
        if result['management_company'] == 'JC Golf':
            print("✅ SUCCESS: Correctly matched to JC Golf!")
        else:
            print(f"❌ ISSUE: Expected JC Golf, got {result['management_company']}")
    else:
        print(f"  Message: {result.get('message', 'No message')}")
        print("❌ ISSUE: Expected a successful match")

if __name__ == "__main__":
    test_cross_creek_matching()
