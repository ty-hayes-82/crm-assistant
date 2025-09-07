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

from ...core.base_agents import SpecializedAgent

# Attempt to import Google Gemini packages
try:
    import google.generativeai as genai
    from google.generativeai import types
    GOOGLE_GEMINI_AVAILABLE = True
except ImportError:
    GOOGLE_GEMINI_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class EnrichmentTarget:
    """Configuration for a field to be enriched"""
    field_name: str
    internal_name: str
    data_type: str  # 'string', 'number', 'boolean'
    description: str


class CompanyLLMEnrichmentAgent(SpecializedAgent):
    """Google Gemini LLM agent specialized in enriching company fields using web search."""
    
    ENRICHMENT_TARGETS: ClassVar[List[EnrichmentTarget]] = [
        EnrichmentTarget(
            field_name="Club Info",
            internal_name="club_info",
            data_type="string",
            description="Generate a comprehensive summary including facility type, holes, amenities (pool, tennis), and notable features. Format as a descriptive paragraph."
        ),
        EnrichmentTarget(
            field_name="Company Type",
            internal_name="company_type",
            data_type="string",
            description="Classify the company from these options: Public Course, Private Course, Country Club, Municipal Course, Resort Course, Management Company, Golf Club, Partner, Other. Return only the classification."
        ),
        EnrichmentTarget(
            field_name="Annual Revenue",
            internal_name="annualrevenue",
            data_type="number",
            description="Estimate annual revenue in USD based on company size, industry, and public financial data. Return a single number (e.g., 5000000 for $5M)."
        ),
        EnrichmentTarget(
            field_name="Has Pool",
            internal_name="has_pool",
            data_type="boolean",
            description="Determine if the facility has a swimming pool. Return 'Yes' or 'No'."
        ),
        EnrichmentTarget(
            field_name="Has Tennis Courts",
            internal_name="has_tennis_courts",
            data_type="boolean",
            description="Determine if the facility has tennis courts. Return 'Yes' or 'No'."
        ),
        EnrichmentTarget(
            field_name="Number of Holes",
            internal_name="number_of_holes",
            data_type="number",
            description="Determine the number of golf holes. Common values are 9, 18, 27, 36. Return 0 if not a golf facility."
        ),
        EnrichmentTarget(
            field_name="Industry",
            internal_name="industry",
            data_type="string",
            description="Classify the industry using HubSpot options: RECREATIONAL_FACILITIES_AND_SERVICES, HOSPITALITY, SPORTS_AND_RECREATION, LEISURE_TRAVEL_TOURISM, REAL_ESTATE. Return the classification."
        ),
        EnrichmentTarget(
            field_name="Description",
            internal_name="description",
            data_type="string",
            description="Generate a professional company description (100-300 words) including key services, offerings, and location context."
        )
    ]
    
    def __init__(self, **kwargs):
        instruction = """
You are a Company LLM Enrichment Agent powered by Google Gemini, specialized in enriching company data using grounded web search. Your task is to find information about a company using Google Search and return a structured JSON response. Adhere strictly to the requested JSON format and field instructions.
"""
        
        super().__init__(
            name="CompanyLLMEnrichmentAgent",
            domain="company_llm_enrichment",
            specialized_tools=["google_search"],
            model="gemini-2.5-flash",
            instruction=instruction,
            **kwargs
        )
        
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

    def _identify_enrichment_candidates(self, properties: Dict[str, Any]) -> List[EnrichmentTarget]:
        """Identify which fields need enrichment based on missing or placeholder values."""
        candidates = []
        for target in self.ENRICHMENT_TARGETS:
            current_value = properties.get(target.internal_name)
            if not current_value or str(current_value).lower() in ['unknown', 'not sure', '', '0', 'false']:
                candidates.append(target)
        return candidates

    def _validate_field_value(self, target: EnrichmentTarget, value: Any) -> Optional[Any]:
        """Validate a field value against its data type."""
        if value is None:
            return None
        
        try:
            if target.data_type == 'number':
                return float(str(value).replace('$', '').replace(',', ''))
            elif target.data_type == 'boolean':
                return 'Yes' if str(value).lower() in ['yes', 'true', '1'] else 'No'
            else:  # string
                return str(value).strip()
        except (ValueError, TypeError):
            logger.warning(f"Validation failed for field '{target.field_name}'. Value '{value}' is not a valid {target.data_type}.")
            return None

def create_company_llm_enrichment_agent(**kwargs):
    """Factory function to create the company LLM enrichment agent."""
    return CompanyLLMEnrichmentAgent(**kwargs)


def main():
    """Demo the company LLM enrichment agent."""
    print("🧠 Company LLM Enrichment Agent Demo")
    print("=" * 60)
    print("This agent uses Google Gemini LLM + web search to enrich company fields")
    print()
    
    # Create the agent
    agent = create_company_llm_enrichment_agent()
    
    # Test with sample company data
    test_companies = [
        {
            'id': '12345',
            'properties': {
                'name': 'Pebble Beach Golf Links',
                'city': 'Pebble Beach',
                'state': 'CA',
                'club_info': '',
                'company_type': '',
                'has_pool': '',
                'has_tennis_courts': '',
                'number_of_holes': 0
            }
        }
    ]
    
    print("🔍 Testing LLM enrichment...")
    results = agent.batch_enrich_companies(test_companies)
    
    print("\n📊 Results:")
    print("=" * 40)
    for result in results:
        print(f"Company: {result['company_name']}")
        print(f"Status: {result['status']}")
        print(f"Enriched Fields: {len(result.get('enriched_fields', {}))}")
        
        if result.get('enriched_fields'):
            for field, value in result['enriched_fields'].items():
                print(f"   • {field}: {str(value)[:100]}{'...' if len(str(value)) > 100 else ''}")
        print("-" * 40)
    
    print("\n💡 This agent can be integrated with the field enrichment workflow")
    print("   to provide LLM-powered data enrichment using web search!")


if __name__ == "__main__":
    main()
