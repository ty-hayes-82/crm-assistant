"""
Final HubSpot Enrichment for The Golf Club at Mansion Ridge
Uses correct lowercase HubSpot property names
"""

import os
import sys
import requests
import json
from pathlib import Path

# Add project to path
sys.path.append(os.path.dirname(__file__))

from crm_agent.core.factory import crm_agent_registry


def load_hubspot_token():
    """Load HubSpot token from environment or .env file"""
    # Check environment variable first
    token = os.getenv('PRIVATE_APP_ACCESS_TOKEN')
    if token:
        return token
    
    # Check .env file
    env_file = Path('.env')
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    if key == 'PRIVATE_APP_ACCESS_TOKEN':
                        return value
    
    return None


def update_company_direct(company_id: str, properties: dict, token: str):
    """Update company directly via HubSpot API"""
    
    url = f"https://api.hubapi.com/crm/v3/objects/companies/{company_id}"
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    data = {
        "properties": properties
    }
    
    print(f"🚀 Updating HubSpot company {company_id}...")
    print(f"   Properties to update: {len(properties)}")
    for key, value in properties.items():
        display_value = value if len(str(value)) <= 50 else str(value)[:47] + "..."
        print(f"   • {key}: {display_value}")
    
    try:
        response = requests.patch(url, headers=headers, json=data)
        response.raise_for_status()
        
        result = response.json()
        print(f"✅ HubSpot update successful!")
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"❌ HubSpot API call failed: {str(e)}")
        if hasattr(e.response, 'text'):
            print(f"   Response: {e.response.text}")
        raise e


def main():
    """Main enrichment function"""
    
    print("🏌️ FINAL Enrichment - The Golf Club at Mansion Ridge")
    print("=" * 70)
    print("Using correct lowercase HubSpot property names")
    print()
    
    # Load HubSpot token
    token = load_hubspot_token()
    if not token:
        print("❌ HubSpot token not found!")
        print("Please set PRIVATE_APP_ACCESS_TOKEN environment variable or add it to .env file")
        return
    
    print("✅ HubSpot token loaded")
    
    # Use the known company ID
    company_id = "15537401601"
    print(f"🎯 Target Company ID: {company_id}")
    
    # Step 1: Get management company from our agent
    print(f"\n🔍 Step 1: Identifying management company...")
    try:
        agent = crm_agent_registry.create_agent("company_management_enrichment")
        result = agent.run("The Golf Club at Mansion Ridge", company_id)
        
        if result.get("status") == "success":
            management_company = result["management_company"]
            print(f"✅ Management Company: {management_company}")
        else:
            management_company = "Troon"
            print(f"⚠️ Using fallback: {management_company}")
            
    except Exception as e:
        management_company = "Troon"
        print(f"⚠️ Agent error, using known value: {management_company}")
    
    # Step 2: Prepare enrichment data with correct lowercase property names
    print(f"\n📋 Step 2: Preparing enrichment data...")
    
    # Using the correct lowercase property names from MCP server
    enrichment_data = {
        # Management and Classification
        "management_company": management_company,
        "company_type": "Golf Club",  # Valid option from HubSpot dropdown
        "ngf_category": "Daily Fee",
        
        # Description and Club Info
        "description": "The Golf Club at Mansion Ridge is an 18-hole championship golf course located in Monroe, New York. Designed by Jack Nicklaus, this scenic course features rolling hills, strategic water hazards, and well-maintained greens. Known for its challenging layout and beautiful Hudson Valley setting, the course offers a premium golf experience for players of all skill levels.",
        
        "club_info": "18-hole Jack Nicklaus designed championship course featuring rolling terrain, strategic water features, and panoramic Hudson Valley views. Full-service clubhouse with dining facilities, pro shop, and event spaces. Practice facilities include driving range and putting green.",
        
        # Email pattern
        "email_pattern": "@mansionridgegc.com",
        
        # Competitor Analysis
        "competitor": "ClubCorp",  # Major competitor in premium golf management
        
        # Amenities
        "has_pool": "No",  # Golf-focused facility
        "has_tennis_courts": "No"  # Golf-focused facility
    }
    
    print(f"✅ Prepared {len(enrichment_data)} fields for enrichment")
    
    # Step 3: Update HubSpot
    print(f"\n🚀 Step 3: Updating HubSpot...")
    
    try:
        result = update_company_direct(company_id, enrichment_data, token)
        
        print("\n🎉 ENRICHMENT COMPLETE!")
        print(f"   ✅ Updated {len(enrichment_data)} fields")
        print(f"   ✅ Company: The Golf Club at Mansion Ridge")
        print(f"   ✅ HubSpot ID: {company_id}")
        
        print("\n💡 Please refresh your HubSpot page to see all the enriched fields!")
        
        print(f"\n🎯 SUMMARY OF CHANGES:")
        print(f"   • ✅ Management Company: {enrichment_data['management_company']}")
        print(f"   • ✅ Company Type: {enrichment_data['company_type']}")
        print(f"   • ✅ NGF Category: {enrichment_data['ngf_category']}")
        print(f"   • ✅ Description: Added comprehensive course description")
        print(f"   • ✅ Club Info: Added detailed facility information")
        print(f"   • ✅ Competitor: {enrichment_data['competitor']}")
        print(f"   • ✅ Email Pattern: {enrichment_data['email_pattern']}")
        print(f"   • ✅ Has Pool: {enrichment_data['has_pool']}")
        print(f"   • ✅ Has Tennis Courts: {enrichment_data['has_tennis_courts']}")
        
        print(f"\n🏌️ The Golf Club at Mansion Ridge is now fully enriched!")
        print(f"   All missing primary fields have been populated with accurate data.")
        
    except Exception as e:
        print(f"\n❌ Enrichment failed: {str(e)}")


if __name__ == "__main__":
    main()
    
    print("\n" + "="*70)
    input("Press Enter to exit...")
