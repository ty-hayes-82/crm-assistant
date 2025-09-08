#!/usr/bin/env python3
"""
Demo script to test the COMPLETE CRM enrichment pipeline with Houston National Golf Club.
This demonstrates the full workflow including:
1. Company lookup and data enrichment 
2. Lead scoring
3. Outreach personalization
4. ACTUAL HubSpot updates

REQUIREMENTS:
- Set PRIVATE_APP_ACCESS_TOKEN in environment or .env file
- Set HUBSPOT_TEST_PORTAL=1 to enable writes
- Set DRY_RUN=0 to perform actual updates
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from crm_agent.coordinator import create_crm_coordinator
from crm_agent.core.state_models import CRMSessionState
from crm_agent.agents.workflows.crm_enrichment import create_crm_enrichment_pipeline


def check_prerequisites():
    """Check if all prerequisites are met for HubSpot updates."""
    print("🔍 Checking prerequisites...")
    
    # Check for HubSpot token
    token = os.getenv("PRIVATE_APP_ACCESS_TOKEN")
    if not token:
        # Try .env file
        env_path = project_root / ".env"
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    if line.strip().startswith("PRIVATE_APP_ACCESS_TOKEN="):
                        token = line.split("=", 1)[1].strip()
                        break
    
    if not token:
        print("❌ PRIVATE_APP_ACCESS_TOKEN not found!")
        print("   Please set it in environment or .env file")
        return False
    else:
        print("✅ HubSpot token found")
    
    # Check test portal guard
    test_portal = os.getenv("HUBSPOT_TEST_PORTAL", "").lower()
    if test_portal not in {"1", "true", "yes", "sandbox"}:
        print("❌ HUBSPOT_TEST_PORTAL not set!")
        print("   Please set HUBSPOT_TEST_PORTAL=1 to enable writes")
        return False
    else:
        print("✅ Test portal guard enabled")
    
    # Check dry run mode
    dry_run = os.getenv("DRY_RUN", "1").lower()
    if dry_run in {"1", "true", "yes"}:
        print("ℹ️  DRY_RUN mode enabled - no actual HubSpot writes")
    else:
        print("⚠️  DRY_RUN disabled - WILL MAKE ACTUAL HUBSPOT UPDATES")
    
    return True


def main():
    """Run the Houston National Golf Club COMPLETE enrichment demo."""
    print("🏌️ CRM Assistant Demo: Houston National Golf Club FULL ENRICHMENT")
    print("=" * 70)
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Prerequisites not met. Please fix the issues above.")
        return None
    
    # Create the FULL CRM enrichment pipeline
    print("\n🔧 Creating FULL CRM enrichment pipeline...")
    pipeline = create_crm_enrichment_pipeline()
    print(f"✅ Created pipeline with {len(pipeline.sub_agents)} agents")
    
    # Also create coordinator for additional functionality
    print("Creating CRM coordinator...")
    coordinator = create_crm_coordinator()
    print(f"✅ Created coordinator with {len(coordinator.sub_agents)} sub-agents")
    
    # Initialize session state
    state = CRMSessionState()
    
    # Set MINIMAL initial company data - let agents figure out the rest
    state.company_data = {
        "name": "Houston National Golf Club",
        "domain": "houstonnationalgolf.com"
    }
    
    print(f"\n📊 Initial company data:")
    print(f"  Name: {state.company_data['name']}")
    print(f"  Domain: {state.company_data['domain']}")
    print(f"  Fields to research: website, phone, city, state, company_type, club_type, etc.")
    
    # RUN THE COMPLETE ENRICHMENT PIPELINE
    print(f"\n🚀 RUNNING COMPLETE ENRICHMENT PIPELINE...")
    
    try:
        # Create a comprehensive prompt for the pipeline
        enrichment_prompt = f"""
        Please enrich the company data for Houston National Golf Club with the following requirements:
        
        COMPANY INFORMATION:
        - Name: Houston National Golf Club
        - Domain: houstonnational.com
        - Website: https://houstonnational.com
        
        ENRICHMENT TASKS:
        1. Research and identify missing company properties:
           - Company type (Private/Resort/Semi-Private/Daily Fee/Municipal)
           - Management company (if managed by Troon, ClubCorp, etc.)
           - Annual revenue estimate
           - Number of employees
           - Location details (city, state)
           - Phone number
           - Description and club information
           - Industry classification
        
        2. Perform lead scoring based on enriched data
        
        3. Create personalized outreach content
        
        4. UPDATE HUBSPOT with all enriched data
        
        Please execute the complete 9-step enrichment pipeline and provide detailed results.
        """
        
        print(f"📝 Sending enrichment request to pipeline...")
        print(f"   Request: Enrich Houston National Golf Club data and update HubSpot")
        
        # Execute the pipeline with the enrichment request
        result = pipeline.invoke(enrichment_prompt, state=state)
        
        print(f"✅ Pipeline execution completed!")
        print(f"📊 Pipeline result: {type(result)}")
        
        # Check what was actually updated
        if hasattr(result, 'content'):
            print(f"📝 Pipeline output:\n{result.content}")
        else:
            print(f"📝 Pipeline output: {result}")
            
    except Exception as e:
        print(f"❌ Pipeline execution failed: {e}")
        import traceback
        traceback.print_exc()
        
        # Use the COORDINATOR to enrich the data
        print(f"\n🔄 Using CRM COORDINATOR for REAL enrichment...")
        
        enrichment_request = f"""
        Please enrich all missing company data for Houston National Golf Club:
        
        Current Data:
        - Name: Houston National Golf Club
        - Domain: houstonnationalgolf.com
        
        REQUIRED HubSpot Fields to Research and Fill:
        - website: Full website URL
        - phone: Phone number (format: (281) 304-1400)
        - city: Houston
        - state: TX  
        - company_type: Private/Resort/Semi-Private/Daily Fee/Municipal
        - club_type: Specific golf club classification
        - annualrevenue: Estimated annual revenue (e.g., $10,000,000)
        - ngf_category: National Golf Foundation category
        - competitor: Main local competitor golf club
        - description: Detailed club description
        - club_info: Course details and amenities
        - management_company: Troon/ClubCorp/Invited/Independent/etc.
        - email_pattern: Common email format (e.g., firstname.lastname@domain)
        - market: Houston
        - has_pool: Yes/No
        - has_tennis_courts: Yes/No
        - lifecycle_stage: Lead/MQL/SQL/etc.
        
        Please research Houston National Golf Club and provide ALL missing information.
        """
        
        try:
            print(f"   📝 Sending enrichment request to CRM Coordinator...")
            result = coordinator.invoke(enrichment_request)
            
            print(f"   📊 Coordinator Response:")
            if hasattr(result, 'content'):
                print(f"   {result.content}")
                
                # Try to extract data from the coordinator's response
                content = result.content.lower()
                
                # Parse the response for structured data
                import re
                
                # Website
                website_match = re.search(r'https?://[^\s]+', result.content)
                if website_match:
                    state.company_data["website"] = website_match.group()
                
                # Phone
                phone_match = re.search(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', result.content)
                if phone_match:
                    state.company_data["phone"] = phone_match.group()
                
                # City/State
                if "houston" in content:
                    state.company_data["city"] = "Houston"
                    state.company_data["market"] = "Houston"
                if "texas" in content or " tx" in content:
                    state.company_data["state"] = "TX"
                
                # Company Type
                for ctype in ["private", "resort", "semi-private", "daily fee", "municipal"]:
                    if ctype in content:
                        state.company_data["company_type"] = ctype.title()
                        break
                
                # Management Company
                for mgmt in ["troon", "clubcorp", "invited", "kemper", "billy casper"]:
                    if mgmt in content:
                        state.company_data["management_company"] = mgmt.title()
                        break
                else:
                    if "independent" in content:
                        state.company_data["management_company"] = "Independent"
                
                # Revenue (look for dollar amounts)
                revenue_match = re.search(r'\$([0-9,]+)', result.content)
                if revenue_match:
                    revenue_str = revenue_match.group(1).replace(',', '')
                    try:
                        state.company_data["annualrevenue"] = int(revenue_str)
                    except:
                        pass
                
                # Amenities
                if "pool" in content:
                    state.company_data["has_pool"] = "Yes" if any(word in content for word in ["has pool", "pool available", "swimming"]) else "No"
                if "tennis" in content:
                    state.company_data["has_tennis_courts"] = "Yes" if any(word in content for word in ["tennis court", "has tennis"]) else "No"
                
                # Default values for required fields
                if "lifecycle_stage" not in state.company_data:
                    state.company_data["lifecycle_stage"] = "Lead"
                if "email_pattern" not in state.company_data:
                    state.company_data["email_pattern"] = "firstname.lastname"
                
                print(f"   ✅ Extracted data from coordinator response")
                
            else:
                print(f"   ⚠️  No content in coordinator response")
                
        except Exception as e:
            print(f"   ❌ Coordinator enrichment failed: {e}")
            import traceback
            traceback.print_exc()
        
        # NO DEFAULTS! Let's use REAL web research to find the actual data
        print(f"\n🔍 REAL WEB RESEARCH - No defaults, only actual research...")
        
        try:
            # Create a simple CRM agent for web research
            from crm_agent.coordinator import create_crm_simple_agent
            research_agent = create_crm_simple_agent()
            
            research_request = f"""
            I need you to research Houston National Golf Club and find the REAL, ACTUAL information for these fields:
            
            Company: Houston National Golf Club
            Domain: houstonnationalgolf.com
            
            RESEARCH REQUIREMENTS - Find the ACTUAL data:
            
            1. Visit their website and extract:
               - Exact website URL
               - Phone number
               - Physical address (city, state)
               - Description from their website
               - Course information and amenities
            
            2. Determine the actual:
               - Course type (Private/Public/Semi-Private/Municipal/Resort)
               - Management company (is it managed by Troon, ClubCorp, etc. or independent?)
               - Annual revenue estimate based on course type and location
               - Main local competitor in Houston area
               - Amenities (pool, tennis courts, etc.)
            
            3. Format the response as structured data that I can parse.
            
            DO NOT MAKE UP DATA - only provide information you can verify or reasonably determine from research.
            """
            
            print(f"   🌐 Researching Houston National Golf Club...")
            # Use the correct ADK agent method
            research_result = research_agent.generate_content(research_request)
            
            if hasattr(research_result, 'content'):
                print(f"   📊 Research Results:")
                print(f"   {research_result.content}")
                
                # Parse the research results
                content = research_result.content.lower()
                
                # Extract website
                import re
                website_matches = re.findall(r'https?://[^\s<>"]+', research_result.content)
                for website in website_matches:
                    if 'houston' in website.lower() and 'golf' in website.lower():
                        state.company_data["website"] = website.strip('.,)')
                        break
                
                # Extract phone
                phone_matches = re.findall(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', research_result.content)
                if phone_matches:
                    state.company_data["phone"] = phone_matches[0]
                
                # Extract location info
                if "houston" in content:
                    state.company_data["city"] = "Houston"
                    state.company_data["market"] = "Houston"
                if "texas" in content or " tx" in content.replace(".", ""):
                    state.company_data["state"] = "TX"
                
                # Extract course type
                course_types = ["private course", "public course", "semi-private course", "municipal course", "resort"]
                for ctype in course_types:
                    if ctype in content:
                        state.company_data["company_type"] = ctype.title()
                        break
                
                # Extract management info
                mgmt_companies = ["troon", "clubcorp", "invited", "kemper", "billy casper"]
                for mgmt in mgmt_companies:
                    if mgmt in content:
                        state.company_data["management_company"] = mgmt.title()
                        break
                
                # Look for amenities
                if "pool" in content or "swimming" in content:
                    state.company_data["has_pool"] = "Yes" if any(word in content for word in ["pool", "swimming pool", "aquatic"]) else "Unknown"
                if "tennis" in content:
                    state.company_data["has_tennis_courts"] = "Yes" if "tennis" in content else "Unknown"
                
                # Extract revenue info (look for dollar amounts or revenue indicators)
                revenue_patterns = [r'\$([0-9,]+(?:\.[0-9]+)?)\s*(?:million|m)', r'revenue.*?\$([0-9,]+)']
                for pattern in revenue_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        try:
                            revenue_str = matches[0].replace(',', '')
                            revenue = float(revenue_str) * 1000000 if 'million' in content or 'm' in content else float(revenue_str)
                            state.company_data["annualrevenue"] = int(revenue)
                            break
                        except:
                            pass
                
                print(f"   ✅ Extracted data from research")
            
        except Exception as e:
            print(f"   ❌ Research agent failed: {e}")
            print(f"   Will proceed with only the minimal data we have")
        
        # Only add essential HubSpot compliance fields if absolutely necessary
        if "lifecyclestage" not in state.company_data:
            state.company_data["lifecyclestage"] = "lead"  # Required for HubSpot
        if "email_pattern" not in state.company_data:
            state.company_data["email_pattern"] = "firstname.lastname"  # Common pattern
        
        # Show what we've enriched
        print(f"\n📋 ENRICHED COMPANY DATA:")
        for field, value in sorted(state.company_data.items()):
            print(f"   {field}: {value}")
    
    # Test Lead Scoring with available data
    print(f"\n6️⃣ Testing Lead Scoring...")
    try:
        from crm_agent.agents.specialized.lead_scoring_agent import create_lead_scoring_agent
        
        lead_scorer = create_lead_scoring_agent()
        scoring_result = lead_scorer.score_and_store(state)
        
        scores = scoring_result["scores"]
        print(f"   Fit Score: {scores['fit_score']:.1f}/100")
        print(f"   Intent Score: {scores['intent_score']:.1f}/100") 
        print(f"   Total Score: {scores['total_score']:.1f}/100")
        print(f"   Score Band: {scores['score_band']}")
        print(f"   ✅ Lead scoring completed")
        
    except Exception as e:
        print(f"   ❌ Lead scoring failed: {e}")
        scores = {"fit_score": 0, "intent_score": 0, "total_score": 0, "score_band": "Unknown"}
    
    # Test HubSpot Updates
    print(f"\n🔄 Testing HubSpot Updates...")
    try:
        # Try to update HubSpot with what we have
        print(f"   📤 Attempting to update HubSpot with enriched data...")
        
        # Use the direct HubSpot update script approach
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
        
        def is_dry_run():
            return os.getenv("DRY_RUN", "1").lower() in {"1", "true", "yes"}
        
        token = get_hubspot_token()
        if not token:
            print(f"   ❌ No HubSpot token available")
        else:
            # Search for existing company
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # Search by domain
            search_url = "https://api.hubapi.com/crm/v3/objects/companies/search"
            search_payload = {
                "filterGroups": [
                    {
                        "filters": [
                            {
                                "propertyName": "domain",
                                "operator": "EQ",
                                "value": "houstonnational.com"
                            }
                        ]
                    }
                ],
                "properties": ["name", "domain", "website", "company_type", "annualrevenue", "numberofemployees"]
            }
            
            if is_dry_run():
                print(f"   🔍 DRY RUN: Would search HubSpot for company with domain 'houstonnational.com'")
                print(f"   🔍 DRY RUN: Would update/create company with enriched data")
                print(f"   ✅ DRY RUN: HubSpot update simulation completed")
            else:
                print(f"   🔍 Searching HubSpot for existing company...")
                response = requests.post(search_url, headers=headers, json=search_payload)
                
                if response.status_code == 200:
                    search_results = response.json()
                    companies = search_results.get("results", [])
                    
                    if companies:
                        company_id = companies[0]["id"]
                        print(f"   ✅ Found existing company (ID: {company_id})")
                        
                        # Update the company
                        update_url = f"https://api.hubapi.com/crm/v3/objects/companies/{company_id}"
                        # Build update payload with HubSpot-compliant field names and values
                        properties = {}
                        
                        # Core fields
                        properties["name"] = state.company_data["name"]
                        properties["domain"] = state.company_data["domain"]
                        properties["website"] = state.company_data.get("website", "")
                        
                        # Contact info
                        if "phone" in state.company_data:
                            properties["phone"] = state.company_data["phone"]
                        if "city" in state.company_data:
                            properties["city"] = state.company_data["city"]
                        if "state" in state.company_data:
                            properties["state"] = state.company_data["state"]
                        
                        # Business info - using HubSpot compliant values
                        if "company_type" in state.company_data:
                            properties["company_type"] = state.company_data["company_type"]
                        if "club_type" in state.company_data:
                            properties["club_type"] = state.company_data["club_type"]
                        if "annualrevenue" in state.company_data:
                            properties["annualrevenue"] = state.company_data["annualrevenue"]
                        if "description" in state.company_data:
                            properties["description"] = state.company_data["description"]
                        if "club_info" in state.company_data:
                            properties["club_info"] = state.company_data["club_info"]
                        if "management_company" in state.company_data:
                            properties["management_company"] = state.company_data["management_company"]
                        if "competitor" in state.company_data:
                            properties["competitor"] = state.company_data["competitor"]
                        if "market" in state.company_data:
                            properties["market"] = state.company_data["market"]
                        if "ngf_category" in state.company_data:
                            properties["ngf_category"] = state.company_data["ngf_category"]
                        if "email_pattern" in state.company_data:
                            properties["email_pattern"] = state.company_data["email_pattern"]
                        if "has_pool" in state.company_data:
                            properties["has_pool"] = state.company_data["has_pool"]
                        if "has_tennis_courts" in state.company_data:
                            properties["has_tennis_courts"] = state.company_data["has_tennis_courts"]
                        
                        # Use correct lifecycle stage property name
                        if "lifecyclestage" in state.company_data:
                            properties["lifecyclestage"] = state.company_data["lifecyclestage"]
                        
                        update_payload = {"properties": properties}
                        
                        update_response = requests.patch(update_url, headers=headers, json=update_payload)
                        if update_response.status_code == 200:
                            print(f"   ✅ Successfully updated HubSpot company!")
                        else:
                            print(f"   ❌ Failed to update company: {update_response.status_code}")
                            print(f"       {update_response.text}")
                    
                    else:
                        print(f"   ℹ️  Company not found, would create new company")
                        # Create new company
                        create_url = "https://api.hubapi.com/crm/v3/objects/companies"
                        create_payload = {
                            "properties": {
                                "name": state.company_data["name"],
                                "domain": state.company_data["domain"],
                                "website": state.company_data["website"],
                                **{k: v for k, v in state.company_data.items() if k not in ["name", "domain", "website"]}
                            }
                        }
                        
                        create_response = requests.post(create_url, headers=headers, json=create_payload)
                        if create_response.status_code == 201:
                            company_data = create_response.json()
                            print(f"   ✅ Successfully created HubSpot company (ID: {company_data['id']})!")
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
    
    # Test Outreach Personalization
    print(f"\n7️⃣ Testing Outreach Personalization...")
    
    # Add test contact data
    test_contact = {
        "id": "contact_houston_gm",
        "email": "gm@houstonnational.com",
        "jobtitle": "General Manager", 
        "firstname": "John",
        "lastname": "Smith"
    }
    state.contact_data = test_contact
    
    try:
        from crm_agent.agents.specialized.outreach_personalizer_agent import create_outreach_personalizer_agent
        
        outreach_agent = create_outreach_personalizer_agent()
        outreach_result = outreach_agent.generate_personalized_outreach(state, "cold_outreach")
        
        personalization = outreach_result["personalization"]
        print(f"   Subject Line: {personalization['subject_line']}")
        print(f"   Personalization Score: {personalization['personalization_score']}/100")
        print(f"   Messaging Strategy: {personalization['messaging_strategy']}")
        print(f"   ✅ Email draft created (not sent)")
        print(f"   ✅ Follow-up task scheduled")
        
    except Exception as e:
        print(f"   ❌ Outreach personalization failed: {e}")
    
    # Summary
    print(f"\n🎉 Demo Complete!")
    print(f"=" * 60)
    print(f"Results Summary:")
    print(f"  • Company: {state.company_data['name']}")
    print(f"  • Domain: {state.company_data.get('domain', 'N/A')}")
    print(f"  • Website: {state.company_data.get('website', 'N/A')}")
    print(f"  • Type: {state.company_data.get('company_type', 'Unknown')}")
    print(f"  • Management: {state.company_data.get('management_company', 'Unknown')}")
    print(f"  • Lead Score: {scores['total_score']:.1f} ({scores['score_band']})")
    if 'outreach_result' in locals():
        print(f"  • Outreach: Personalized email draft created")
    else:
        print(f"  • Outreach: Not tested")
    print(f"\n💡 Next Steps:")
    print(f"  1. Review email draft before sending")
    print(f"  2. Complete follow-up task as scheduled")
    print(f"  3. Track engagement metrics")
    
    return state


if __name__ == "__main__":
    try:
        final_state = main()
        print(f"\n✅ Demo completed successfully!")
    except KeyboardInterrupt:
        print(f"\n⏹️ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
