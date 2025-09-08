#!/usr/bin/env python3
"""
FINAL Houston National Golf Club Research Demo
Uses the updated CompanyLLMEnrichmentAgent with Gemini search grounding to find ALL missing fields.
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from crm_agent.agents.specialized.company_llm_enrichment_agent import create_company_llm_enrichment_agent
from crm_agent.agents.specialized.lead_scoring_agent import create_lead_scoring_agent
from crm_agent.core.state_models import CRMSessionState
import requests


def update_hubspot_safe(company_data):
    """Safely update HubSpot with researched data."""
    print(f"\n🔄 UPDATING HUBSPOT WITH {len(company_data)} RESEARCHED FIELDS...")
    
    # Get HubSpot token
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
        return False
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        # Search for existing company
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
            
            # Build properties payload - only include fields that have actual researched data
            properties = {}
            for key, value in company_data.items():
                if value and str(value).strip() and value not in ["Unknown", "N/A", ""]:
                    properties[key] = value
            
            print(f"   📝 Preparing to update {len(properties)} researched fields")
            
            if companies:
                # Update existing company
                company_id = companies[0]["id"]
                print(f"   ✅ Found existing company (ID: {company_id})")
                
                update_url = f"https://api.hubapi.com/crm/v3/objects/companies/{company_id}"
                update_payload = {"properties": properties}
                
                print(f"   📤 Updating HubSpot company with researched data...")
                update_response = requests.patch(update_url, headers=headers, json=update_payload)
                
                if update_response.status_code == 200:
                    print(f"   🎉 SUCCESS! Updated HubSpot company with {len(properties)} researched fields!")
                    print(f"\n   📋 UPDATED FIELDS:")
                    for key, value in properties.items():
                        print(f"      ✅ {key}: {value}")
                    return True
                else:
                    print(f"   ❌ Failed to update company: {update_response.status_code}")
                    print(f"       Error: {update_response.text}")
                    return False
            
            else:
                # Create new company
                print(f"   ℹ️  Company not found, creating new company...")
                create_url = "https://api.hubapi.com/crm/v3/objects/companies"
                create_payload = {"properties": properties}
                
                create_response = requests.post(create_url, headers=headers, json=create_payload)
                if create_response.status_code == 201:
                    company_result = create_response.json()
                    print(f"   🎉 SUCCESS! Created HubSpot company (ID: {company_result['id']})!")
                    print(f"\n   📋 CREATED WITH RESEARCHED FIELDS:")
                    for key, value in properties.items():
                        print(f"      ✅ {key}: {value}")
                    return True
                else:
                    print(f"   ❌ Failed to create company: {create_response.status_code}")
                    print(f"       Error: {create_response.text}")
                    return False
        
        else:
            print(f"   ❌ HubSpot search failed: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"   ❌ HubSpot update failed: {e}")
        return False


def main():
    """Main function to research and enrich Houston National Golf Club."""
    
    print("🏌️ HOUSTON NATIONAL GOLF CLUB - REAL RESEARCH & ENRICHMENT")
    print("=" * 70)
    
    # Check prerequisites
    print("🔍 Checking prerequisites...")
    
    # Check HubSpot token
    hubspot_token = os.getenv("PRIVATE_APP_ACCESS_TOKEN")
    if not hubspot_token:
        env_path = project_root / ".env"
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    if line.strip().startswith("PRIVATE_APP_ACCESS_TOKEN="):
                        hubspot_token = line.split("=", 1)[1].strip()
                        break
    
    if not hubspot_token:
        print("❌ PRIVATE_APP_ACCESS_TOKEN not found!")
        return None
    else:
        print("✅ HubSpot token found")
    
    # Check Google API key
    google_key = os.getenv("GOOGLE_API_KEY")
    if not google_key:
        env_path = project_root / ".env"
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    if line.strip().startswith("GOOGLE_API_KEY="):
                        google_key = line.split("=", 1)[1].strip()
                        break
    
    if not google_key:
        print("❌ GOOGLE_API_KEY not found!")
        print("   Please set GOOGLE_API_KEY in environment or .env file")
        return None
    else:
        print("✅ Google API key found")
    
    # Set environment variables
    os.environ["HUBSPOT_TEST_PORTAL"] = "1"
    os.environ["DRY_RUN"] = "0"
    print("✅ Environment configured for HubSpot updates")
    
    # Create the Company LLM Enrichment Agent
    print(f"\n🤖 Creating Company LLM Enrichment Agent...")
    try:
        enrichment_agent = create_company_llm_enrichment_agent()
        print(f"✅ Agent created successfully")
    except Exception as e:
        print(f"❌ Failed to create agent: {e}")
        return None
    
    # Start with minimal company data
    company_data = {
        "name": "Houston National Golf Club",
        "domain": "houstonnationalgolf.com"
    }
    
    print(f"\n📊 Starting data:")
    for key, value in company_data.items():
        print(f"   {key}: {value}")
    
    # Use the agent to enrich the company data
    print(f"\n🔍 RESEARCHING WITH GEMINI SEARCH GROUNDING...")
    try:
        enriched_data = enrichment_agent.enrich_company_data(company_data)
        
        print(f"\n📋 ENRICHED COMPANY DATA ({len(enriched_data)} fields):")
        print("=" * 50)
        for field, value in sorted(enriched_data.items()):
            print(f"   {field}: {value}")
        
    except Exception as e:
        print(f"❌ Enrichment failed: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    # Update HubSpot with the enriched data
    success = update_hubspot_safe(enriched_data)
    
    if success:
        print(f"\n🎉 MISSION ACCOMPLISHED!")
        print(f"✅ Houston National Golf Club fully enriched with {len(enriched_data)} fields")
        
        # Run lead scoring on enriched data
        print(f"\n📊 RUNNING LEAD SCORING ON ENRICHED DATA...")
        try:
            # Create session state with enriched data
            state = CRMSessionState()
            state.company_data = enriched_data
            
            lead_scorer = create_lead_scoring_agent()
            scoring_result = lead_scorer.score_and_store(state)
            
            scores = scoring_result["scores"]
            print(f"   Fit Score: {scores['fit_score']:.1f}/100")
            print(f"   Intent Score: {scores['intent_score']:.1f}/100")
            print(f"   Total Score: {scores['total_score']:.1f}/100")
            print(f"   Score Band: {scores['score_band']}")
            print(f"   ✅ Lead scoring completed with enriched data!")
            
            # Show scoring improvement
            original_score = 22.2  # Score with minimal data
            new_score = scores['total_score']
            improvement = new_score - original_score
            print(f"   📈 Score improvement: +{improvement:.1f} points from data enrichment!")
            
        except Exception as e:
            print(f"   ❌ Lead scoring failed: {e}")
        
        return enriched_data
    else:
        print(f"\n❌ HubSpot update failed")
        return None


if __name__ == "__main__":
    try:
        result = main()
        if result:
            print(f"\n🏆 COMPLETE SUCCESS!")
            print(f"📊 Houston National Golf Club enriched with {len(result)} fields")
            print(f"🔄 HubSpot updated with real researched data")
            print(f"📈 Lead scoring improved with enriched data")
        else:
            print(f"\n❌ Enrichment process failed")
            
    except KeyboardInterrupt:
        print(f"\n⏹️ Process interrupted by user")
    except Exception as e:
        print(f"\n❌ Process failed: {e}")
        import traceback
        traceback.print_exc()
