#!/usr/bin/env python3
"""
Test competitor enrichment for Louisville Country Club
"""

from crm_agent.agents.specialized.company_competitor_agent import create_company_competitor_agent
import json

def test_louisville_competitor():
    """Test competitor enrichment for Louisville Country Club."""
    
    # Create the competitor agent
    print("🤖 Creating Company Competitor Agent...")
    agent = create_company_competitor_agent()
    print("   ✅ Agent created successfully")
    print()

    # Test data for Louisville Country Club
    company_data = {
        'id': '15537372824',
        'properties': {
            'name': 'Louisville Country Club',
            'website': 'loucc.net',
            'domain': 'loucc.net',
            'competitor': ''  # Empty/not set
        }
    }

    print('🏆 Testing Competitor Enrichment for Louisville Country Club')
    print('=' * 60)
    print(f'Company: {company_data["properties"]["name"]}')
    print(f'Website: {company_data["properties"]["website"]}')
    print(f'Current Competitor: {company_data["properties"]["competitor"] or "Empty"}')
    print()

    print("🔍 Analyzing website for competitor mentions...")
    print("   This will scrape https://loucc.net to detect competitor software")
    print()

    # Analyze competitor
    try:
        result = agent.enrich_competitor_field(company_data)
        
        print('📊 Enrichment Result:')
        print('=' * 30)
        print(json.dumps(result, indent=2))
        
        if result['status'] == 'enriched':
            print(f"\n✅ SUCCESS: Detected competitor '{result['new_value']}'")
            print(f"   Confidence: {result.get('confidence', 'unknown')}")
            print(f"   Source: {result.get('source', 'unknown')}")
        elif result['status'] == 'no_change':
            print(f"\n❓ NO CHANGE: {result['reason']}")
        else:
            print(f"\n❌ FAILED: {result['reason']}")
            
    except Exception as e:
        print(f"❌ Error during enrichment: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_louisville_competitor()
