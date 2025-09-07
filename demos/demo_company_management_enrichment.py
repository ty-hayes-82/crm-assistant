"""
Demo: Company Management Enrichment Agent

This demo shows how to use the Company Management Agent to identify
and set the management company for golf courses using fuzzy matching
against the internal courses_under_management.json database.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from crm_agent.core.factory import create_company_management_agent

def demo_company_management_enrichment():
    """Demonstrate the Company Management Agent functionality."""
    
    print("🏌️ Company Management Enrichment Demo")
    print("=" * 50)
    print()
    
    # Create the agent
    agent = create_company_management_agent()
    
    # Demo companies to test
    demo_companies = [
        {
            "name": "The Golf Club at Mansion Ridge",
            "id": "12345",
            "description": "User's example - should match Troon"
        },
        {
            "name": "Bandon Dunes Resort",
            "id": "67890", 
            "description": "Should match KemperSports"
        },
        {
            "name": "Purgatory Golf",
            "id": "11111",
            "description": "Partial name - should still match Troon"
        },
        {
            "name": "Cross Creek Golf Course",
            "id": "22222",
            "description": "Should match JC Golf"
        },
        {
            "name": "Microsoft Corporation",
            "id": "99999",
            "description": "Non-golf company - should not match"
        }
    ]
    
    for i, company in enumerate(demo_companies, 1):
        print(f"Demo {i}: {company['description']}")
        print(f"Company: {company['name']}")
        print(f"HubSpot ID: {company['id']}")
        
        # Run the agent
        result = agent.run(company['name'], company['id'])
        
        if result['status'] == 'success':
            print(f"✅ Management Company Found: {result['management_company']}")
            print(f"   HubSpot ID: {result['management_company_id']}")
            print(f"   Match Score: {result['match_score']}")
            print(f"   Matched Course: {result['matched_course']}")
            print(f"   Action: {result['action']}")
        elif result['status'] == 'partial_match':
            print(f"⚠️ Partial Match Found: {result['management_company']}")
            print(f"   Match Score: {result['match_score']}")
            print(f"   Issue: {result['issue']}")
            print("   Action: Management company needs to be tagged in HubSpot")
        elif result['status'] == 'no_match':
            print("❌ No management company found")
            print("   Action: No changes needed")
        else:
            print(f"❌ Error: {result.get('message', 'Unknown error')}")
        
        print("-" * 40)
        print()
    
    print("🎯 Summary:")
    print("The Enhanced Company Management Agent successfully:")
    print("• Loads management companies from HubSpot (Company Type = 'Management Company')")
    print("• Performs fuzzy matching against internal golf course database")
    print("• Identifies management companies with high confidence scores")
    print("• Maps course names to actual HubSpot management company IDs")
    print("• Handles variations in company names (e.g., 'Golf Club' vs 'Resort')")
    print("• Avoids false positives for non-golf companies")
    print("• Validates that management companies exist in HubSpot before updating")
    print()
    print("💡 Next Steps:")
    print("• Integrate with actual HubSpot search_companies and update_company tools")
    print("• Add check for existing parent company relationships")
    print("• Add logging and audit trail for changes")
    print("• Consider adding manual review for scores between 70-85")
    print("• Expand to other industry verticals beyond golf")
    print("• Handle cases where management companies need to be created in HubSpot")

if __name__ == "__main__":
    demo_company_management_enrichment()
