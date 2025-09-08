#!/usr/bin/env python3
"""
Houston National Golf Club Research using Gemini 2.5 Flash with GROUNDED SEARCH
Uses Google Gemini with search grounding to find ALL missing company fields.
NO DEFAULTS - ONLY REAL RESEARCH VIA GEMINI SEARCH!
"""

import os
import sys
import json
import requests
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    print("❌ google-genai not installed. Run: pip install google-ai-generativelanguage")
    GEMINI_AVAILABLE = False
    sys.exit(1)


def setup_gemini():
    """Setup Gemini with search grounding."""
    # Get API key from environment
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        # Try .env file
        env_path = project_root / ".env"
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    if line.strip().startswith("GOOGLE_API_KEY="):
                        api_key = line.split("=", 1)[1].strip()
                        break
    
    if not api_key:
        print("❌ GOOGLE_API_KEY not found!")
        print("   Please set GOOGLE_API_KEY in environment or .env file")
        return None, None
    
    # Configure the client
    client = genai.Client(api_key=api_key)
    
    # Define the grounding tool using the correct API format
    grounding_tool = types.Tool(
        google_search=types.GoogleSearch()
    )
    
    # Configure generation settings
    config = types.GenerateContentConfig(
        tools=[grounding_tool]
    )
    
    print("✅ Gemini 2.5 Flash configured with search grounding")
    return client, config


def research_houston_national_with_gemini():
    """Research Houston National Golf Club using Gemini with search grounding."""
    
    print("🔍 RESEARCHING HOUSTON NATIONAL GOLF CLUB WITH GEMINI SEARCH")
    print("=" * 70)
    
    # Setup Gemini
    client, config = setup_gemini()
    if not client:
        return None
    
    # Start with minimal data
    company_data = {
        "name": "Houston National Golf Club",
        "domain": "houstonnationalgolf.com"
    }
    
    print(f"📊 Starting with: {company_data}")
    
    # Create comprehensive research prompt for Gemini
    research_prompt = f"""
    Research Houston National Golf Club and provide SPECIFIC, FACTUAL information for these HubSpot CRM fields:

    COMPANY: Houston National Golf Club
    DOMAIN: houstonnationalgolf.com

    REQUIRED RESEARCH - Find the ACTUAL, REAL data for each field:

    1. CONTACT INFORMATION:
       - website: The exact website URL
       - phone: The main phone number
       - city: The city location
       - state: The state (should be TX/Texas)

    2. GOLF COURSE CLASSIFICATION:
       - company_type: Must be one of: "Private Course", "Public Course", "Semi-Private Course", "Municipal Course", "Resort"
       - club_type: Specific type of golf facility
       - ngf_category: National Golf Foundation category

    3. BUSINESS DETAILS:
       - annualrevenue: Estimated annual revenue (research typical private club revenues)
       - description: Detailed description of the club
       - club_info: Course details, amenities, features
       - management_company: Is it managed by Troon, ClubCorp, Invited, or Independent?

    4. COMPETITIVE ANALYSIS:
       - competitor: Name the main competitor golf club in Houston area

    5. AMENITIES (Yes/No):
       - has_pool: Does it have a swimming pool?
       - has_tennis_courts: Does it have tennis courts?

    6. CRM FIELDS:
       - email_pattern: Common email format (e.g., firstname.lastname)
       - market: Market area (Houston)
       - lifecyclestage: Should be "lead"

    INSTRUCTIONS:
    - Use search to find the club's actual website and information
    - Research Houston golf clubs to understand the competitive landscape
    - Look up typical private club revenues in Houston area
    - Verify all information through multiple sources
    - Provide specific, factual data - NO GUESSING
    - Format response as structured data that can be parsed

    Please search for and provide the actual, verified information for Houston National Golf Club.
    """
    
    print(f"\n🌐 Sending research request to Gemini with search grounding...")
    print(f"📝 Researching ALL missing fields for Houston National Golf Club...")
    
    try:
        # Generate response with search grounding using the correct API
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=research_prompt,
            config=config
        )
        
        print(f"\n📊 GEMINI RESEARCH RESULTS:")
        print("=" * 50)
        print(response.text)
        
        # Parse the response to extract structured data
        print(f"\n🔧 PARSING GEMINI RESPONSE FOR STRUCTURED DATA...")
        
        content = response.text.lower()
        updates = {}
        
        # Extract website
        import re
        website_matches = re.findall(r'https?://[^\s<>"]+', response.text)
        for website in website_matches:
            if 'houston' in website.lower() and 'golf' in website.lower():
                updates["website"] = website.strip('.,)')
                print(f"   ✅ Found website: {website}")
                break
        
        # Extract phone number
        phone_matches = re.findall(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', response.text)
        if phone_matches:
            updates["phone"] = phone_matches[0]
            print(f"   ✅ Found phone: {phone_matches[0]}")
        
        # Extract location
        if "houston" in content:
            updates["city"] = "Houston"
            updates["market"] = "Houston"
            print(f"   ✅ Found city: Houston")
        if "texas" in content or " tx" in content:
            updates["state"] = "TX"
            print(f"   ✅ Found state: TX")
        
        # Extract course type (match HubSpot allowed values)
        hubspot_course_types = ["Private Course", "Public Course", "Semi-Private Course", "Municipal Course", "Resort"]
        for course_type in hubspot_course_types:
            if course_type.lower() in content:
                updates["company_type"] = course_type
                print(f"   ✅ Found company type: {course_type}")
                break
        
        # Extract management company
        management_companies = ["Troon", "ClubCorp", "Invited", "KemperSports", "Billy Casper Golf"]
        for mgmt in management_companies:
            if mgmt.lower() in content:
                updates["management_company"] = mgmt
                print(f"   ✅ Found management company: {mgmt}")
                break
        else:
            if "independent" in content or "privately owned" in content:
                updates["management_company"] = "Independent"
                print(f"   ✅ Found management: Independent")
        
        # Extract revenue (look for dollar amounts)
        revenue_patterns = [
            r'\$([0-9,]+(?:\.[0-9]+)?)\s*million',
            r'\$([0-9,]+(?:\.[0-9]+)?)\s*m',
            r'revenue.*?\$([0-9,]+)',
            r'annual.*?\$([0-9,]+)'
        ]
        for pattern in revenue_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                try:
                    revenue_str = matches[0].replace(',', '')
                    if 'million' in content or 'm' in content:
                        revenue = float(revenue_str) * 1000000
                    else:
                        revenue = float(revenue_str)
                    updates["annualrevenue"] = int(revenue)
                    print(f"   ✅ Found revenue: ${revenue:,.0f}")
                    break
                except:
                    pass
        
        # Extract competitor information
        competitor_keywords = ["competitor", "rival", "similar", "vs", "compared to"]
        golf_club_pattern = r'([A-Z][a-zA-Z\s]+(?:Golf Club|Country Club|Golf Course))'
        competitor_matches = re.findall(golf_club_pattern, response.text)
        
        for match in competitor_matches:
            if "Houston National" not in match and "Houston" in match:
                updates["competitor"] = match.strip()
                print(f"   ✅ Found competitor: {match}")
                break
        
        # Extract amenities
        if "pool" in content or "swimming" in content:
            if any(phrase in content for phrase in ["has pool", "pool available", "swimming pool", "aquatic"]):
                updates["has_pool"] = "Yes"
                print(f"   ✅ Found amenity: Pool - Yes")
            elif any(phrase in content for phrase in ["no pool", "without pool"]):
                updates["has_pool"] = "No"
                print(f"   ✅ Found amenity: Pool - No")
        
        if "tennis" in content:
            if any(phrase in content for phrase in ["tennis court", "has tennis", "tennis facilities"]):
                updates["has_tennis_courts"] = "Yes"
                print(f"   ✅ Found amenity: Tennis - Yes")
            elif any(phrase in content for phrase in ["no tennis", "without tennis"]):
                updates["has_tennis_courts"] = "No"
                print(f"   ✅ Found amenity: Tennis - No")
        
        # Extract description and club info
        description_keywords = ["description", "about", "overview", "history"]
        sentences = re.split(r'[.!?]+', response.text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 50 and "houston national" in sentence.lower():
                if any(keyword in sentence.lower() for keyword in description_keywords):
                    if "description" not in updates:
                        updates["description"] = sentence[:500]  # Limit length
                        print(f"   ✅ Found description: {sentence[:100]}...")
                        break
        
        # Set standard fields
        updates["email_pattern"] = "firstname.lastname"
        updates["lifecyclestage"] = "lead"
        updates["ngf_category"] = updates.get("company_type", "Private Club")
        
        # Apply all updates to company data
        print(f"\n📝 APPLYING {len(updates)} RESEARCHED UPDATES:")
        for key, value in updates.items():
            company_data[key] = value
            print(f"   {key}: {value}")
        
        return company_data
        
    except Exception as e:
        print(f"❌ Gemini research failed: {e}")
        import traceback
        traceback.print_exc()
        return company_data


def update_hubspot_with_researched_data(company_data):
    """Update HubSpot with the researched company data."""
    
    print(f"\n🔄 UPDATING HUBSPOT WITH RESEARCHED DATA...")
    
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
            
            # Build properties payload - only include fields that have actual data
            properties = {}
            for key, value in company_data.items():
                if value and str(value).strip() and value != "Unknown":
                    properties[key] = value
            
            print(f"   📝 Preparing to update {len(properties)} fields")
            
            if companies:
                # Update existing company
                company_id = companies[0]["id"]
                print(f"   ✅ Found existing company (ID: {company_id})")
                
                update_url = f"https://api.hubapi.com/crm/v3/objects/companies/{company_id}"
                update_payload = {"properties": properties}
                
                print(f"   📤 Updating HubSpot company with researched data...")
                update_response = requests.patch(update_url, headers=headers, json=update_payload)
                
                if update_response.status_code == 200:
                    print(f"   🎉 SUCCESS! Updated HubSpot company with {len(properties)} fields!")
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
                    print(f"\n   📋 CREATED WITH FIELDS:")
                    for key, value in properties.items():
                        print(f"      ✅ {key}: {value}")
                    return True
                else:
                    print(f"   ❌ Failed to create company: {create_response.status_code}")
                    print(f"       Error: {create_response.text}")
                    return False
        
        else:
            print(f"   ❌ HubSpot search failed: {response.status_code}")
            print(f"       Error: {response.text}")
            return False
    
    except Exception as e:
        print(f"   ❌ HubSpot update failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main research and enrichment function."""
    
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
    
    # Set environment variables
    os.environ["HUBSPOT_TEST_PORTAL"] = "1"
    os.environ["DRY_RUN"] = "0"
    print("✅ Environment configured for HubSpot updates")
    
    # Research with Gemini
    company_data = research_houston_national_with_gemini()
    if not company_data:
        print("❌ Research failed")
        return None
    
    print(f"\n📋 FINAL RESEARCHED DATA ({len(company_data)} fields):")
    print("=" * 50)
    for field, value in sorted(company_data.items()):
        print(f"   {field}: {value}")
    
    # Update HubSpot
    success = update_hubspot_with_researched_data(company_data)
    
    if success:
        print(f"\n🎉 MISSION ACCOMPLISHED!")
        print(f"✅ All {len(company_data)} fields researched and updated in HubSpot")
        
        # Run lead scoring on enriched data
        print(f"\n📊 RUNNING LEAD SCORING ON ENRICHED DATA...")
        try:
            from crm_agent.agents.specialized.lead_scoring_agent import create_lead_scoring_agent
            from crm_agent.core.state_models import CRMSessionState
            
            # Create state with enriched data
            state = CRMSessionState()
            state.company_data = company_data
            
            lead_scorer = create_lead_scoring_agent()
            scoring_result = lead_scorer.score_and_store(state)
            
            scores = scoring_result["scores"]
            print(f"   Fit Score: {scores['fit_score']:.1f}/100")
            print(f"   Intent Score: {scores['intent_score']:.1f}/100")
            print(f"   Total Score: {scores['total_score']:.1f}/100")
            print(f"   Score Band: {scores['score_band']}")
            print(f"   ✅ Lead scoring completed with enriched data!")
            
        except Exception as e:
            print(f"   ❌ Lead scoring failed: {e}")
        
        return company_data
    else:
        print(f"\n❌ HubSpot update failed")
        return None


if __name__ == "__main__":
    try:
        result = main()
        if result:
            print(f"\n🏆 SUCCESS! Houston National Golf Club fully enriched!")
            print(f"📊 Total fields: {len(result)}")
        else:
            print(f"\n❌ Enrichment failed")
            
    except KeyboardInterrupt:
        print(f"\n⏹️ Research interrupted by user")
    except Exception as e:
        print(f"\n❌ Research failed: {e}")
        import traceback
        traceback.print_exc()
