#!/usr/bin/env python3
"""
REAL Houston National Golf Club Research Demo
Uses actual CRM agents to research and enrich ALL missing company fields.
NO DEFAULTS - ONLY REAL RESEARCH!
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from crm_agent.core.factory import create_company_management_agent, create_company_llm_enrichment_agent
from crm_agent.agents.specialized.company_competitor_agent import create_company_competitor_agent


def research_houston_national():
    """Research Houston National Golf Club using REAL agents."""
    
    print("🔍 RESEARCHING HOUSTON NATIONAL GOLF CLUB - NO DEFAULTS!")
    print("=" * 60)
    
    # Start with minimal data
    company_data = {
        "name": "Houston National Golf Club",
        "domain": "houstonnationalgolf.com"
    }
    
    print(f"📊 Starting data: {company_data}")
    print()
    
    # Step 1: Company Management Research
    print("1️⃣ RESEARCHING MANAGEMENT COMPANY...")
    try:
        mgmt_agent = create_company_management_agent()
        
        # Test with the demo pattern that works
        company_info = {
            "name": "Houston National Golf Club",
            "id": "houston_national_test",
            "description": "Golf club in Houston, Texas"
        }
        
        print(f"   Testing company: {company_info['name']}")
        
        # Use the working demo pattern
        result = mgmt_agent.identify_management_company(company_info)
        
        if result:
            print(f"   ✅ Management company result: {result}")
            if result.get("management_company"):
                company_data["management_company"] = result["management_company"]
                print(f"   📝 Found management company: {result['management_company']}")
        else:
            print(f"   ⚠️  No management company identified")
            
    except Exception as e:
        print(f"   ❌ Management research failed: {e}")
    
    # Step 2: Company LLM Enrichment Research  
    print(f"\n2️⃣ RESEARCHING COMPANY DETAILS...")
    try:
        llm_agent = create_company_llm_enrichment_agent()
        
        # Use the agent's research capabilities
        enrichment_data = {
            "name": "Houston National Golf Club",
            "domain": "houstonnationalgolf.com",
            "target_fields": [
                "website", "phone", "city", "state", "company_type", 
                "description", "club_info", "annualrevenue"
            ]
        }
        
        print(f"   🔍 LLM researching company details...")
        
        # Try the agent's enrichment method if it exists
        if hasattr(llm_agent, 'enrich_company_data'):
            result = llm_agent.enrich_company_data(enrichment_data)
            print(f"   ✅ LLM enrichment result: {result}")
            
            # Apply any found data
            if isinstance(result, dict):
                for key, value in result.items():
                    if value and value != "Unknown":
                        company_data[key] = value
                        print(f"   📝 Found {key}: {value}")
        else:
            print(f"   ⚠️  LLM agent doesn't have enrich_company_data method")
            
    except Exception as e:
        print(f"   ❌ LLM enrichment failed: {e}")
    
    # Step 3: Competitor Research
    print(f"\n3️⃣ RESEARCHING COMPETITORS...")
    try:
        competitor_agent = create_company_competitor_agent()
        
        # Research competitors in Houston area
        competitor_data = {
            "name": "Houston National Golf Club",
            "city": company_data.get("city", "Houston"),
            "state": company_data.get("state", "Texas"),
            "company_type": company_data.get("company_type", "Golf Club")
        }
        
        print(f"   🏆 Researching Houston golf club competitors...")
        
        # Try the competitor agent's research method
        if hasattr(competitor_agent, 'find_competitors'):
            competitors = competitor_agent.find_competitors(competitor_data)
            if competitors:
                print(f"   ✅ Found competitors: {competitors}")
                if isinstance(competitors, list) and competitors:
                    company_data["competitor"] = competitors[0]
                elif isinstance(competitors, str):
                    company_data["competitor"] = competitors
        else:
            print(f"   ⚠️  Competitor agent doesn't have find_competitors method")
            
    except Exception as e:
        print(f"   ❌ Competitor research failed: {e}")
    
    # Step 4: Show final researched data
    print(f"\n📋 FINAL RESEARCHED DATA:")
    for field, value in sorted(company_data.items()):
        print(f"   {field}: {value}")
    
    # Step 5: Update HubSpot with ONLY the researched data
    print(f"\n🔄 UPDATING HUBSPOT WITH RESEARCHED DATA...")
    
    try:
        import requests
        
        def get_hubspot_token():
            token = os.getenv("PRIVATE_APP_ACCESS_TOKEN")
            if not token:
                env_path = project_root / ".env"
                if env_path.exists():
                    with open(env_path) as f:
                        for line in f:
                            if line.strip().startswith("PRIVATE_APP_ACCESS_TOKEN="):
                                return line.split("=", 1)[1].strip()
            return token
        
        token = get_hubspot_token()
        if not token:
            print(f"   ❌ No HubSpot token available")
            return company_data
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Search for existing company by domain
        search_url = "https://api.hubapi.com/crm/v3/objects/companies/search"
        search_payload = {
            "filterGroups": [
                {
                    "filters": [
                        {
                            "propertyName": "domain",
                            "operator": "EQ", 
                            "value": "houstonnationalgolf.com"
                        }
                    ]
                }
            ]
        }
        
        print(f"   🔍 Searching HubSpot for existing company...")
        response = requests.post(search_url, headers=headers, json=search_payload)
        
        if response.status_code == 200:
            search_results = response.json()
            companies = search_results.get("results", [])
            
            # Prepare properties for HubSpot (only fields we actually researched)
            properties = {}
            for key, value in company_data.items():
                if value and value != "Unknown":
                    properties[key] = value
            
            if companies:
                # Update existing company
                company_id = companies[0]["id"]
                print(f"   ✅ Found existing company (ID: {company_id})")
                
                update_url = f"https://api.hubapi.com/crm/v3/objects/companies/{company_id}"
                update_payload = {"properties": properties}
                
                update_response = requests.patch(update_url, headers=headers, json=update_payload)
                if update_response.status_code == 200:
                    print(f"   ✅ Successfully updated HubSpot company with {len(properties)} fields!")
                    for key, value in properties.items():
                        print(f"      {key}: {value}")
                else:
                    print(f"   ❌ Failed to update company: {update_response.status_code}")
                    print(f"       {update_response.text}")
            
            else:
                # Create new company
                print(f"   ℹ️  Company not found, creating new company...")
                create_url = "https://api.hubapi.com/crm/v3/objects/companies"
                create_payload = {"properties": properties}
                
                create_response = requests.post(create_url, headers=headers, json=create_payload)
                if create_response.status_code == 201:
                    company_result = create_response.json()
                    print(f"   ✅ Successfully created HubSpot company (ID: {company_result['id']})!")
                    print(f"   📝 Created with {len(properties)} researched fields:")
                    for key, value in properties.items():
                        print(f"      {key}: {value}")
                else:
                    print(f"   ❌ Failed to create company: {create_response.status_code}")
                    print(f"       {create_response.text}")
        
        else:
            print(f"   ❌ HubSpot search failed: {response.status_code}")
            print(f"       {response.text}")
    
    except Exception as e:
        print(f"   ❌ HubSpot update failed: {e}")
        import traceback
        traceback.print_exc()
    
    return company_data


if __name__ == "__main__":
    try:
        # Set environment for testing
        os.environ["HUBSPOT_TEST_PORTAL"] = "1"
        os.environ["DRY_RUN"] = "0"
        
        result = research_houston_national()
        print(f"\n🎉 Research Complete!")
        print(f"📊 Final Data: {len(result)} fields researched")
        
    except KeyboardInterrupt:
        print(f"\n⏹️ Research interrupted by user")
    except Exception as e:
        print(f"\n❌ Research failed: {e}")
        import traceback
        traceback.print_exc()
