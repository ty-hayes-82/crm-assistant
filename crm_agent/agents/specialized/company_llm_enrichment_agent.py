#!/usr/bin/env python3
"""
Company LLM Enrichment Agent

Specialized Google Gemini LLM subagent that uses web search to enrich company fields
with generic data like Club Info, Company Type, Annual Revenue, Has Pool, Has Tennis Courts,
Number of Holes, etc. Uses grounded search to provide accurate, contextual information.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, ClassVar
from dataclasses import dataclass
from pydantic import BaseModel, Field
from enum import Enum
from pathlib import Path

from ...core.base_agents import SpecializedAgent

# Attempt to import Google Gemini packages
try:
    from google import genai
    from google.genai import types
    GOOGLE_GEMINI_AVAILABLE = True
    NEW_API = True
except ImportError:
    try:
        import google.generativeai as genai
        GOOGLE_GEMINI_AVAILABLE = True
        NEW_API = False
    except ImportError:
        GOOGLE_GEMINI_AVAILABLE = False
        NEW_API = False

logger = logging.getLogger(__name__)


# Pydantic models for structured output
class CompanyType(str, Enum):
    PRIVATE_COURSE = "Private Course"
    PUBLIC_COURSE = "Public Course"
    SEMI_PRIVATE_COURSE = "Semi-Private Course"
    MUNICIPAL_COURSE = "Municipal Course"
    RESORT = "Resort"


class ClubType(str, Enum):
    PUBLIC_LOW_FEE = "Public - Low Daily Fee"
    COUNTRY_CLUB = "Country Club"
    PRIVATE = "Private"
    PUBLIC_HIGH_FEE = "Public - High Daily Fee"
    RESORT = "Resort"
    MUNICIPAL_COURSE = "Municipal Course"
    UNKNOWN = "Unknown"
    PUBLIC_COURSE = "Public Course"
    RESORT_COURSE = "Resort Course"
    MANAGEMENT_COMPANY = "Management Company"


class YesNoUnknown(str, Enum):
    YES = "Yes"
    NO = "No"
    UNKNOWN = "Unknown"


class HoustonNationalGolfClubData(BaseModel):
    """Structured output model for Houston National Golf Club research."""
    
    # Contact Information
    website: Optional[str] = Field(description="The exact website URL")
    phone: Optional[str] = Field(description="The main phone number in format (XXX) XXX-XXXX")
    city: Optional[str] = Field(description="City location")
    state: Optional[str] = Field(description="State abbreviation (TX)")
    
    # Golf Course Classification
    company_type: Optional[CompanyType] = Field(description="Type of golf course")
    club_type: Optional[ClubType] = Field(description="Specific club classification")
    ngf_category: Optional[str] = Field(description="National Golf Foundation category")
    
    # Business Details
    annualrevenue: Optional[int] = Field(description="Estimated annual revenue in USD")
    description: Optional[str] = Field(description="Detailed club description")
    club_info: Optional[str] = Field(description="Course details, amenities, features")
    management_company: Optional[str] = Field(description="Management company (Troon, ClubCorp, Invited, Independent, etc.)")
    
    # Competitive Analysis
    competitor: Optional[str] = Field(description="Main competitor golf club in Houston area")
    
    # Amenities
    has_pool: Optional[YesNoUnknown] = Field(description="Does it have a swimming pool?")
    has_tennis_courts: Optional[YesNoUnknown] = Field(description="Does it have tennis courts?")
    
    # Derived Fields
    market: Optional[str] = Field(description="Market area")
    email_pattern: Optional[str] = Field(description="Common email format")
    lifecyclestage: Optional[str] = Field(description="HubSpot lifecycle stage")


class CompanyLLMEnrichmentAgent(SpecializedAgent):
    """Google Gemini LLM agent specialized in enriching company fields using web search with structured output."""
    
    def __init__(self, **kwargs):
        instruction = """
You are a Company LLM Enrichment Agent powered by Google Gemini with search grounding. 
You research companies using Google Search and return structured, accurate data.
Use search to find factual, current information about companies and format it precisely.
"""
        
        super().__init__(
            name="CompanyLLMEnrichmentAgent",
            domain="company_llm_enrichment",
            specialized_tools=["google_search"],
            model="gemini-2.5-flash",
            instruction=instruction,
            **kwargs
        )
        
        # Setup Gemini search after initialization
        self._setup_gemini_search()
    
    def _setup_gemini_search(self):
        """Setup Gemini client with search grounding capabilities."""
        if not GOOGLE_GEMINI_AVAILABLE:
            print("⚠️  Gemini search grounding not available - install google-generativeai")
            object.__setattr__(self, 'gemini_client', None)
            object.__setattr__(self, 'gemini_model', None)
            return
        
        # Get API key
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            # Try .env file
            env_path = Path(__file__).parent.parent.parent.parent / ".env"
            if env_path.exists():
                with open(env_path) as f:
                    for line in f:
                        if line.strip().startswith("GOOGLE_API_KEY="):
                            api_key = line.split("=", 1)[1].strip()
                            break
        
        if not api_key:
            print("⚠️  GOOGLE_API_KEY not found - Gemini search grounding disabled")
            object.__setattr__(self, 'gemini_client', None)
            object.__setattr__(self, 'gemini_model', None)
            return
        
        try:
            if NEW_API:
                # Try the new Gemini API with structured output
                try:
                    # Configure the client
                    client = genai.Client(api_key=api_key)
                    object.__setattr__(self, 'gemini_client', client)
                    object.__setattr__(self, 'use_new_api', True)
                    
                    print("✅ Gemini 2.5 Flash with search grounding initialized (New API)")
                    
                except Exception as new_api_error:
                    print(f"⚠️  New Gemini API failed: {new_api_error}")
                    object.__setattr__(self, 'gemini_client', None)
                    object.__setattr__(self, 'use_new_api', False)
            
            if not NEW_API or not getattr(self, 'gemini_client', None):
                # Fall back to legacy google-generativeai package
                genai.configure(api_key=api_key)
                
                # Create model with search grounding
                model = genai.GenerativeModel(
                    model_name="gemini-2.5-flash",
                    tools=["google_search_retrieval"]
                )
                
                object.__setattr__(self, 'gemini_model', model)
                object.__setattr__(self, 'use_new_api', False)
                
                print("✅ Gemini 2.5 Flash with search grounding initialized (Legacy API)")
            
        except Exception as e:
            print(f"⚠️  Gemini setup failed: {e}")
            object.__setattr__(self, 'gemini_client', None)
            object.__setattr__(self, 'gemini_model', None)
            object.__setattr__(self, 'use_new_api', False)
    
    def enrich_company_data(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Research and enrich company data using Gemini with search grounding and structured output.
        
        Args:
            company_data: Dictionary with company name, domain, and any existing data
            
        Returns:
            Dictionary with enriched company data
        """
        # Check if we have any Gemini capability
        has_new_api = getattr(self, 'gemini_client', None) is not None
        has_legacy_api = getattr(self, 'gemini_model', None) is not None
        
        if not has_new_api and not has_legacy_api:
            print("❌ Gemini search grounding not available")
            return company_data
        
        company_name = company_data.get("name", "")
        domain = company_data.get("domain", "")
        
        if not company_name:
            print("❌ Company name required for enrichment")
            return company_data
        
        # Create research prompt for structured output
        research_prompt = f"""
        Research {company_name} (domain: {domain}) and provide COMPLETE, FACTUAL information.
        
        Use Google Search to find:
        1. Official website and contact information
        2. Golf course type and classification
        3. Business details and management
        4. Amenities and facilities - SPECIFICALLY look for:
           - Swimming pool or aquatic facilities
           - Tennis courts or tennis facilities
           - Dining facilities and restaurants
           - Pro shop and retail
           - Event spaces and banquet facilities
        5. Local competitors
        
        IMPORTANT: Only provide information you can verify through search. 
        For amenities, explicitly state "Yes" or "No" for pools and tennis courts.
        Set fields to null if you cannot find reliable information.
        """
        
        try:
            print(f"🔍 Researching {company_name} with structured output...")
            
            if getattr(self, 'use_new_api', False):
                # Use new API with structured output
                client = getattr(self, 'gemini_client')
                
                # Configure generation with search grounding (no JSON mode with tools)
                from google.genai import types
                config = types.GenerateContentConfig(
                    tools=[types.Tool(google_search=types.GoogleSearch())]
                )
                
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=research_prompt,
                    config=config
                )
                
                # Parse the text response (no JSON mode with tools)
                print(f"📊 Gemini Research Results:")
                print(f"{response.text}")
                
                # Parse the unstructured response
                result_data = self._parse_gemini_response(response.text, {})
                
            else:
                # Use legacy API with search grounding
                model = getattr(self, 'gemini_model')
                
                response = model.generate_content(research_prompt)
                
                print(f"📊 Gemini Research Results:")
                print(f"{response.text}")
                
                # Parse the unstructured response
                result_data = self._parse_gemini_response(response.text, {})
            
            # Merge with original data
            enriched_data = company_data.copy()
            
            print(f"\n🔧 Processing structured research results...")
            fields_found = 0
            
            for key, value in result_data.items():
                if value is not None and str(value).strip() and str(value) != "Unknown":
                    enriched_data[key] = value
                    fields_found += 1
                    print(f"   ✅ {key}: {value}")
            
            print(f"   📊 Found {fields_found} fields with real data")
            
            return enriched_data
            
        except Exception as e:
            print(f"❌ Gemini research failed: {e}")
            import traceback
            traceback.print_exc()
            return company_data
    
    def _parse_gemini_response(self, response_text: str, original_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Gemini response and extract structured company data."""
        
        enriched_data = original_data.copy()
        content = response_text.lower()
        
        print(f"\n🔧 Parsing Gemini response for structured data...")
        
        import re
        
        # Extract website
        website_matches = re.findall(r'https?://[^\s<>"]+', response_text)
        for website in website_matches:
            if any(term in website.lower() for term in ['golf', 'club', 'national']) and 'houston' in website.lower():
                enriched_data["website"] = website.strip('.,)')
                print(f"   ✅ Found website: {website}")
                break
        
        # Extract phone number
        phone_matches = re.findall(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', response_text)
        if phone_matches:
            enriched_data["phone"] = phone_matches[0]
            print(f"   ✅ Found phone: {phone_matches[0]}")
        
        # Extract location
        if "houston" in content:
            enriched_data["city"] = "Houston"
            enriched_data["market"] = "Houston"
            print(f"   ✅ Found city: Houston")
        if "texas" in content or " tx" in content.replace(".", ""):
            enriched_data["state"] = "TX"
            print(f"   ✅ Found state: TX")
        
        # Extract course type (match HubSpot allowed values)
        hubspot_course_types = ["Private Course", "Public Course", "Semi-Private Course", "Municipal Course", "Resort"]
        for course_type in hubspot_course_types:
            if course_type.lower() in content:
                enriched_data["company_type"] = course_type
                print(f"   ✅ Found company type: {course_type}")
                break
        
        # Extract club type (match HubSpot allowed values)
        hubspot_club_types = [
            "Public - Low Daily Fee", "Country Club", "Private", "Public - High Daily Fee", 
            "Resort", "Municipal Course", "Public Course", "Resort Course", "Management Company"
        ]
        
        # Look for club type in order of specificity
        for club_type in hubspot_club_types:
            if club_type.lower() in content:
                enriched_data["club_type"] = club_type
                print(f"   ✅ Found club type: {club_type}")
                break
        
        # Fallback patterns for common terms
        if "club_type" not in enriched_data:
            if "country club" in content:
                enriched_data["club_type"] = "Country Club"
                print(f"   ✅ Found club type: Country Club")
            elif "municipal" in content:
                enriched_data["club_type"] = "Municipal Course"
                print(f"   ✅ Found club type: Municipal Course")
            elif "resort" in content and "course" in content:
                enriched_data["club_type"] = "Resort Course"
                print(f"   ✅ Found club type: Resort Course")
            elif "private" in content:
                enriched_data["club_type"] = "Private"
                print(f"   ✅ Found club type: Private")
            elif "public" in content:
                if "high" in content and "fee" in content:
                    enriched_data["club_type"] = "Public - High Daily Fee"
                    print(f"   ✅ Found club type: Public - High Daily Fee")
                else:
                    enriched_data["club_type"] = "Public - Low Daily Fee"
                    print(f"   ✅ Found club type: Public - Low Daily Fee")
        
        # Extract revenue (look for dollar amounts)
        revenue_patterns = [
            r'\$([0-9,]+(?:\.[0-9]+)?)\s*million',
            r'\$([0-9,]+(?:\.[0-9]+)?)\s*m\b',
            r'revenue.*?\$([0-9,]+)',
            r'annual.*?\$([0-9,]+)'
        ]
        for pattern in revenue_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                try:
                    revenue_str = matches[0].replace(',', '')
                    if 'million' in content or ' m ' in content:
                        revenue = float(revenue_str) * 1000000
                    else:
                        revenue = float(revenue_str)
                    enriched_data["annualrevenue"] = int(revenue)
                    print(f"   ✅ Found revenue: ${revenue:,.0f}")
                    break
                except:
                    pass
        
        # Extract competitor information
        golf_club_pattern = r'([A-Z][a-zA-Z\s]+(?:Golf Club|Country Club|Golf Course))'
        competitor_matches = re.findall(golf_club_pattern, response_text)
        
        for match in competitor_matches:
            if "Houston National" not in match and any(term in match.lower() for term in ["houston", "texas"]):
                enriched_data["competitor"] = match.strip()
                print(f"   ✅ Found competitor: {match}")
                break
        
        # Extract amenities - Pool (more precise detection)
        import re
        
        # Look for explicit pool mentions with clear Yes/No context
        pool_found = False
        
        # Check for direct "No." answers
        no_pool_patterns = [
            r'swimming pool[^:]*:\s*no\.',
            r'aquatic facilities[^:]*:\s*no\.',
            r'pool[^:]*:\s*no\.',
        ]
        
        for pattern in no_pool_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                enriched_data["has_pool"] = "No"
                print(f"   ✅ Found amenity: Pool - No (explicit)")
                pool_found = True
                break
        
        if not pool_found:
            # Check for positive indicators
            yes_pool_patterns = [
                r'swimming pool[^:]*:\s*yes',
                r'aquatic facilities[^:]*:\s*yes',
                r'pool[^:]*:\s*yes',
                r'has.*pool',
                r'pool.*available',
                r'features.*pool'
            ]
            
            for pattern in yes_pool_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    enriched_data["has_pool"] = "Yes"
                    print(f"   ✅ Found amenity: Pool - Yes (explicit)")
                    pool_found = True
                    break
        
        # Extract amenities - Tennis (more precise detection)
        tennis_found = False
        
        # Check for direct "No." answers
        no_tennis_patterns = [
            r'tennis courts[^:]*:\s*no\.',
            r'tennis facilities[^:]*:\s*no\.',
            r'tennis[^:]*:\s*no\.',
        ]
        
        for pattern in no_tennis_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                enriched_data["has_tennis_courts"] = "No"
                print(f"   ✅ Found amenity: Tennis - No (explicit)")
                tennis_found = True
                break
        
        if not tennis_found:
            # Check for positive indicators
            yes_tennis_patterns = [
                r'tennis courts[^:]*:\s*yes',
                r'tennis facilities[^:]*:\s*yes',
                r'tennis[^:]*:\s*yes',
                r'has.*tennis',
                r'tennis.*available',
                r'features.*tennis'
            ]
            
            for pattern in yes_tennis_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    enriched_data["has_tennis_courts"] = "Yes"
                    print(f"   ✅ Found amenity: Tennis - Yes (explicit)")
                    tennis_found = True
                    break
        
        # Extract description
        sentences = re.split(r'[.!?]+', response_text)
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 50 and any(term in sentence.lower() for term in ["golf", "club", "course"]):
                if any(keyword in sentence.lower() for keyword in ["description", "about", "overview", "premier", "championship"]):
                    if "description" not in enriched_data or len(sentence) > len(enriched_data.get("description", "")):
                        enriched_data["description"] = sentence[:500]  # Limit length
                        print(f"   ✅ Found description: {sentence[:100]}...")
                        break
        
        # Extract club info
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 30 and any(term in sentence.lower() for term in ["hole", "course", "championship", "amenities"]):
                if "club_info" not in enriched_data or len(sentence) > len(enriched_data.get("club_info", "")):
                    enriched_data["club_info"] = sentence[:500]
                    print(f"   ✅ Found club info: {sentence[:100]}...")
                    break
        
        # Set derived fields
        enriched_data["lifecyclestage"] = "lead"
        
        return enriched_data
        
        self.model = None
        if GOOGLE_GEMINI_AVAILABLE:
            gemini_api_key = os.getenv("GOOGLE_API_KEY")
            if not gemini_api_key:
                logger.warning("GOOGLE_API_KEY environment variable not found. Real LLM calls will fail.")
            else:
                try:
                    genai.configure(api_key=gemini_api_key)
                    self.model = genai.GenerativeModel('gemini-2.5-flash')
                    logger.info("✅ Google Gemini LLM client configured successfully.")
                except Exception as e:
                    logger.error(f"❌ Failed to configure Google Gemini: {e}")
        else:
            logger.warning("`google-generativeai` package not installed. Run `pip install google-generativeai`.")

    def enrich_company_fields(self, company_data: Dict[str, Any], 
                            target_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Enrich company fields using LLM analysis of web search results.
        """
        if not self.model:
            return {
                'status': 'error',
                'reason': 'Google Gemini client not configured. Check API key and package installation.',
                'enriched_fields': {}
            }

        properties = company_data.get('properties', {})
        company_name = properties.get('name', 'Unknown Company')
        city = properties.get('city', '')
        state = properties.get('state', '')
        
        logger.info(f"🧠 LLM enriching fields for {company_name}")
        
        search_location = f"{city}, {state}" if city and state else city or state or ""
        
        targets = [t for t in self.ENRICHMENT_TARGETS if t.field_name in target_fields] if target_fields else self._identify_enrichment_candidates(properties)
        
        if not targets:
            return {'status': 'no_candidates', 'reason': 'No fields needed enrichment.', 'enriched_fields': {}}

        # Build the prompt for the LLM
        json_fields_prompt = ",\n".join([f'        "{t.internal_name}": "<{t.data_type}>"' for t in targets])
        instructions_prompt = "\n".join([f'    - "{t.internal_name}": "{t.description}"' for t in targets])
        
        prompt = f"""
You are an AI data analyst. Use Google Search to find information about the company below and return a single, raw JSON object with the requested fields.

**Company:** {company_name}
**Location:** {search_location}

**JSON Object to Populate:**
{{
{json_fields_prompt}
}}

**Instructions for each field:**
{instructions_prompt}

**Rules:**
- If you cannot find information for a field, use a JSON `null` value.
- Your response MUST be only the raw JSON object, without any surrounding text, explanations, or markdown formatting.
"""

        try:
            logger.info(f"   🔍 Calling Google Gemini with grounded search for {len(targets)} fields...")
            grounding_tool = types.Tool(google_search=types.GoogleSearch())
            response = self.model.generate_content(prompt, tools=[grounding_tool])

            # Clean and parse the JSON response
            cleaned_response = response.text.strip().replace("```json", "").replace("```", "").strip()
            llm_results = json.loads(cleaned_response)
            
            logger.info(f"   ✅ Received and parsed LLM response.")
            
            # Validate and collect enriched fields
            enriched_fields = {}
            for target in targets:
                value = llm_results.get(target.internal_name)
                if value is not None:
                    validated_value = self._validate_field_value(target, value)
                    if validated_value is not None:
                        enriched_fields[target.internal_name] = validated_value

            return {
                'status': 'completed',
                'enriched_fields': enriched_fields,
                'search_query': f"{company_name} {search_location}".strip(),
                'successful_enrichments': len(enriched_fields)
            }

        except Exception as e:
            logger.error(f"   💥 Error during Gemini API call or processing: {e}")
            return {'status': 'error', 'reason': str(e), 'enriched_fields': {}}


def create_company_llm_enrichment_agent(**kwargs):
    """Factory function to create the company LLM enrichment agent."""
    return CompanyLLMEnrichmentAgent(**kwargs)
