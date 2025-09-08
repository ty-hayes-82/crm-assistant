#!/usr/bin/env python3
"""
Stdio-based MCP Server for HubSpot CRM integration.
This server implements the MCP protocol over stdio for use with ADK.
"""

import asyncio
import json
import sys
import os
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

# Import MCP server components
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)
import mcp.server.stdio
import mcp.types

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
def load_env():
    """Load environment variables from .env file"""
    env_vars = {}
    env_file_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    if os.path.exists(env_file_path):
        with open(env_file_path, 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    env_vars[key] = value
    return env_vars

ENV_VARS = load_env()
HUBSPOT_TOKEN = ENV_VARS.get('PRIVATE_APP_ACCESS_TOKEN') or os.getenv('PRIVATE_APP_ACCESS_TOKEN')
GOOGLE_API_KEY = ENV_VARS.get('GOOGLE_API_KEY') or os.getenv('GOOGLE_API_KEY')

# Debug environment loading
logger.info(f"Environment variables loaded: {list(ENV_VARS.keys())}")
logger.info(f"HubSpot token configured: {bool(HUBSPOT_TOKEN)}")
logger.info(f"Google API key configured: {bool(GOOGLE_API_KEY)}")
if GOOGLE_API_KEY:
    logger.info(f"Google API key starts with: {GOOGLE_API_KEY[:10]}...")

def get_hubspot_field_mappings():
    """Get HubSpot field validation mappings based on actual HubSpot API responses."""
    return {
        "company_type": {
            "allowed_values": ["Public Course", "Private Course", "Municipal Course", "Semi-Private Course", "Golf Club", "Management Company", "Partner", "Other"],
            "mappings": {
                "public golf course": "Public Course",
                "public": "Public Course",
                "daily fee": "Public Course",
                "private golf course": "Private Course", 
                "private": "Private Course",
                "country club": "Private Course",
                "resort": "Private Course",
                "municipal course": "Municipal Course",
                "municipal": "Municipal Course",
                "semi-private": "Semi-Private Course",
                "golf club": "Golf Club",
                "management company": "Management Company",
                "partner": "Partner"
            }
        },
        "club_type": {
            "allowed_values": ["Public - Low Daily Fee", "Public - High Daily Fee", "Private", "Country Club", "Resort", "Municipal Course"],
            "mappings": {
                "public": "Public - Low Daily Fee",
                "public golf course": "Public - Low Daily Fee",
                "private": "Private",
                "country club": "Country Club",
                "resort": "Resort",
                "municipal": "Municipal Course"
            }
        }
    }

def normalize_field_value(field_name: str, raw_value: str) -> str:
    """Normalize a field value to match HubSpot's allowed values."""
    if not raw_value:
        return ""
    
    mappings = get_hubspot_field_mappings()
    
    if field_name not in mappings:
        return raw_value
    
    field_config = mappings[field_name]
    raw_lower = raw_value.lower().strip()
    
    # Check direct mappings first
    for key, mapped_value in field_config["mappings"].items():
        if key in raw_lower:
            return mapped_value
    
    # Check if it's already a valid value
    for allowed_value in field_config["allowed_values"]:
        if allowed_value.lower() == raw_lower:
            return allowed_value
    
    # Return the first allowed value as default if no match
    return field_config["allowed_values"][0]

def normalize_domain_to_website(domain: str) -> str:
    """Convert a domain to a proper website URL."""
    if not domain:
        return ""
    
    # Remove any existing protocol
    domain = domain.replace("http://", "").replace("https://", "").strip()
    
    # Remove trailing slash
    domain = domain.rstrip("/")
    
    # Add https protocol
    return f"https://{domain}"

def is_valid_domain(domain: str) -> bool:
    """Check if a domain appears to be valid."""
    if not domain:
        return False
    
    # Basic domain validation
    domain = domain.replace("http://", "").replace("https://", "").strip().rstrip("/")
    
    # Should contain at least one dot and no spaces
    if "." not in domain or " " in domain:
        return False
    
    # Should not be too short
    if len(domain) < 4:
        return False
        
    return True

def should_populate_website_from_domain(company_data: dict) -> bool:
    """Determine if we should populate website from domain."""
    domain = company_data.get("domain", "")
    website = company_data.get("website", "")
    
    # Only populate if domain exists and is valid, and website is empty or points to social media
    if not is_valid_domain(domain):
        return False
    
    # If website is empty, definitely populate
    if not website:
        return True
    
    # If website points to social media platforms, consider replacing
    social_platforms = ["facebook.com", "twitter.com", "instagram.com", "linkedin.com", "youtube.com"]
    website_lower = website.lower()
    
    for platform in social_platforms:
        if platform in website_lower:
            return True
    
    return False

# Initialize the MCP server
app = Server("hubspot-crm-server")

@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available tools."""
    return [
        Tool(
            name="search_companies",
            description="Search for companies in HubSpot CRM",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (company name, domain, etc.)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 10
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_company",
            description="Get a specific company by ID from HubSpot CRM",
            inputSchema={
                "type": "object",
                "properties": {
                    "company_id": {
                        "type": "string",
                        "description": "HubSpot company ID"
                    },
                    "properties": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of properties to retrieve",
                        "default": ["name", "domain", "city", "state", "country", "website", "phone", "description", "company_type", "club_type", "competitor"]
                    }
                },
                "required": ["company_id"]
            }
        ),
        Tool(
            name="search_contacts",
            description="Search for contacts in HubSpot CRM",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (name, email, company, etc.)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 10
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_contact",
            description="Get a specific contact by ID from HubSpot CRM",
            inputSchema={
                "type": "object",
                "properties": {
                    "contact_id": {
                        "type": "string",
                        "description": "HubSpot contact ID"
                    },
                    "properties": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of properties to retrieve",
                        "default": ["firstname", "lastname", "email", "phone", "company", "jobtitle", "city", "state", "country"]
                    }
                },
                "required": ["contact_id"]
            }
        ),
        Tool(
            name="get_associated_contacts",
            description="Get all contacts associated with a specific company ID from HubSpot CRM",
            inputSchema={
                "type": "object",
                "properties": {
                    "company_id": {
                        "type": "string",
                        "description": "HubSpot company ID"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 100
                    }
                },
                "required": ["company_id"]
            }
        ),
        Tool(
            name="update_company",
            description="Update company properties in HubSpot CRM",
            inputSchema={
                "type": "object",
                "properties": {
                    "company_id": {
                        "type": "string",
                        "description": "HubSpot company ID"
                    },
                    "properties": {
                        "type": "object",
                        "description": "Properties to update (key-value pairs)"
                    }
                },
                "required": ["company_id", "properties"]
            }
        ),
        Tool(
            name="update_contact",
            description="Update contact properties in HubSpot CRM",
            inputSchema={
                "type": "object",
                "properties": {
                    "contact_id": {
                        "type": "string",
                        "description": "HubSpot contact ID"
                    },
                    "properties": {
                        "type": "object",
                        "description": "Properties to update (key-value pairs)"
                    }
                },
                "required": ["contact_id", "properties"]
            }
        ),
        Tool(
            name="update_crm_state",
            description="Update CRM session state with key-value pairs",
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string",
                        "description": "State key to update (e.g., 'detected_gaps', 'search_plan')"
                    },
                    "value": {
                        "type": "object",
                        "description": "Value to store in the state"
                    }
                },
                "required": ["key", "value"]
            }
        ),
        Tool(
            name="get_crm_state",
            description="Get CRM session state value by key",
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string",
                        "description": "State key to retrieve (e.g., 'detected_gaps', 'search_plan')"
                    }
                },
                "required": ["key"]
            }
        ),
        Tool(
            name="normalize_company_data",
            description="Normalize company data by populating website from domain when appropriate",
            inputSchema={
                "type": "object",
                "properties": {
                    "company_data": {
                        "type": "object",
                        "description": "Company data to normalize"
                    }
                },
                "required": ["company_data"]
            }
        ),
        Tool(
            name="determine_company_type_with_gemini",
            description="Use Google Gemini to determine company type with structured output based on company data",
            inputSchema={
                "type": "object",
                "properties": {
                    "company_data": {
                        "type": "object",
                        "description": "Company data including name, description, amenities, etc."
                    }
                },
                "required": ["company_data"]
            }
        ),
        Tool(
            name="detect_competitors_from_website",
            description="Scrape company website to detect competitors like Northstar, Jonas, etc.",
            inputSchema={
                "type": "object",
                "properties": {
                    "website_url": {
                        "type": "string",
                        "description": "Company website URL to scrape"
                    },
                    "company_name": {
                        "type": "string",
                        "description": "Company name for context"
                    }
                },
                "required": ["website_url", "company_name"]
            }
        ),
        Tool(
            name="generate_club_info_with_gemini",
            description="Use Google Gemini with grounded search to generate comprehensive club information including amenities",
            inputSchema={
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "Name of the golf club/course"
                    },
                    "city": {
                        "type": "string",
                        "description": "City location"
                    },
                    "state": {
                        "type": "string",
                        "description": "State location"
                    },
                    "website": {
                        "type": "string",
                        "description": "Company website URL (optional)"
                    }
                },
                "required": ["company_name", "city", "state"]
            }
        )
    ]

async def make_hubspot_request(method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict[str, Any]:
    """Make a request to HubSpot API."""
    if not HUBSPOT_TOKEN:
        return {"error": "HubSpot access token not configured"}
    
    import httpx
    
    headers = {
        'Authorization': f'Bearer {HUBSPOT_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    url = f'https://api.hubapi.com{endpoint}'
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            if method.upper() == 'GET':
                response = await client.get(url, headers=headers, params=params)
            elif method.upper() == 'POST':
                response = await client.post(url, headers=headers, json=data)
            elif method.upper() == 'PUT':
                response = await client.put(url, headers=headers, json=data)
            elif method.upper() == 'PATCH':
                response = await client.patch(url, headers=headers, json=data)
            else:
                return {"error": f"Unsupported HTTP method: {method}"}
            
            response.raise_for_status()
            return response.json()
            
    except httpx.HTTPStatusError as e:
        logger.error(f"HubSpot API error: {e.response.status_code} - {e.response.text}")
        return {"error": f"HubSpot API error: {e.response.status_code}", "details": e.response.text}
    except Exception as e:
        logger.error(f"Request error: {e}")
        return {"error": str(e)}

@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls with timeout protection."""
    
    # Add timeout wrapper for expensive operations
    import asyncio
    
    async def _call_tool_impl():
        return await _handle_tool_call(name, arguments)
    
    try:
        # Use appropriate timeout for operations
        timeout = 45.0 if name in ["determine_company_type_with_gemini", "generate_club_info_with_gemini"] else 30.0
        return await asyncio.wait_for(_call_tool_impl(), timeout=timeout)
    except asyncio.TimeoutError:
        logger.error(f"Tool call timed out: {name}")
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": f"Tool call timed out after {timeout} seconds",
                "tool": name,
                "timeout": timeout
            })
        )]
    except Exception as e:
        logger.error(f"Tool call failed: {name} - {e}")
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": str(e),
                "tool": name
            })
        )]

async def _handle_tool_call(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls implementation."""
    
    if name == "search_companies":
        query = arguments.get("query", "")
        limit = arguments.get("limit", 10)
        
        # Use HubSpot's search API
        search_data = {
            "query": query,
            "limit": limit,
            "sorts": [{"propertyName": "createdate", "direction": "DESCENDING"}],
            "properties": [
                # Primary company identification
                "name", "domain", "website", "phone", "description", "hs_object_id",
                # Location fields
                "city", "state", "country", "postal_code", "street_address",
                # Company classification (removed "industry" per request)
                "company_type", "club_type", "lifecyclestage", "hs_lead_status",
                # Financial and business data
                "annualrevenue", "competitor", "ngf_category", "management_company",
                # Regional and market data
                "state_region_code", "market", "email_pattern",
                # Club-specific amenities
                "club_info", "has_pool", "has_tennis_courts", "number_of_holes"
            ]
        }
        
        result = await make_hubspot_request("POST", "/crm/v3/objects/companies/search", search_data)
        
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
    
    elif name == "get_company":
        company_id = arguments.get("company_id")
        properties = arguments.get("properties", [
            # Primary company identification
            "name", "domain", "website", "phone", "description",
            # Location fields  
            "city", "state", "country", "postal_code", "street_address",
            # Company classification (removed "industry" per request)
            "company_type", "club_type", "lifecyclestage", "hs_lead_status",
            # Financial and business data
            "annualrevenue", "competitor", "ngf_category", "management_company", 
            # Regional and market data
            "state_region_code", "market", "email_pattern",
            # Club-specific amenities
            "club_info", "has_pool", "has_tennis_courts", "number_of_holes"
        ])
        
        params = {"properties": ",".join(properties)}
        result = await make_hubspot_request("GET", f"/crm/v3/objects/companies/{company_id}", params=params)
        
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
    
    elif name == "search_contacts":
        query = arguments.get("query", "")
        limit = arguments.get("limit", 10)
        
        search_data = {
            "query": query,
            "limit": limit,
            "sorts": [{"propertyName": "createdate", "direction": "DESCENDING"}],
            "properties": ["firstname", "lastname", "email", "phone", "company", "jobtitle", "city", "state", "country", "hs_object_id"]
        }
        
        result = await make_hubspot_request("POST", "/crm/v3/objects/contacts/search", search_data)
        
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
    
    elif name == "get_contact":
        contact_id = arguments.get("contact_id")
        properties = arguments.get("properties", ["firstname", "lastname", "email", "phone", "company", "jobtitle", "city", "state", "country"])
        
        params = {"properties": ",".join(properties)}
        result = await make_hubspot_request("GET", f"/crm/v3/objects/contacts/{contact_id}", params=params)
        
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]

    elif name == "get_associated_contacts":
        company_id = arguments.get("company_id")
        limit = arguments.get("limit", 100)
        
        # This endpoint gets the IDs of associated contacts
        association_endpoint = f"/crm/v4/objects/company/{company_id}/associations/contact"
        association_result = await make_hubspot_request("GET", association_endpoint, params={"limit": limit})

        if "results" not in association_result:
            return [TextContent(type="text", text=json.dumps({"contacts": [], "error": "No associated contacts found or API error."}))]

        contact_ids = [item['toObjectId'] for item in association_result['results']]
        
        if not contact_ids:
            return [TextContent(type="text", text=json.dumps({"contacts": []}))]

        # Now, batch-read the details for these contacts
        batch_read_endpoint = "/crm/v3/objects/contacts/batch/read"
        properties = ["firstname", "lastname", "email", "phone", "jobtitle", "company"]
        batch_payload = {
            "inputs": [{"id": contact_id} for contact_id in contact_ids],
            "properties": properties
        }
        
        contacts_details = await make_hubspot_request("POST", batch_read_endpoint, data=batch_payload)

        return [TextContent(
            type="text",
            text=json.dumps(contacts_details, indent=2)
        )]

    elif name == "update_company":
        company_id = arguments.get("company_id")
        properties = arguments.get("properties", {})
        
        update_data = {"properties": properties}
        result = await make_hubspot_request("PATCH", f"/crm/v3/objects/companies/{company_id}", update_data)
        
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
    
    elif name == "update_contact":
        contact_id = arguments.get("contact_id")
        properties = arguments.get("properties", {})
        
        update_data = {"properties": properties}
        result = await make_hubspot_request("PATCH", f"/crm/v3/objects/contacts/{contact_id}", update_data)
        
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
    
    elif name == "update_crm_state":
        key = arguments.get("key")
        value = arguments.get("value")
        
        # Simple in-memory state storage for now
        # In a real implementation, this would persist to a database or session store
        if not hasattr(app, '_crm_state'):
            app._crm_state = {}
        
        app._crm_state[key] = value
        
        result = {
            "success": True,
            "key": key,
            "message": f"Updated CRM state key '{key}'"
        }
        
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
    
    elif name == "get_crm_state":
        key = arguments.get("key")
        
        # Get from in-memory state storage
        if not hasattr(app, '_crm_state'):
            app._crm_state = {}
        
        value = app._crm_state.get(key, {})
        
        result = {
            "key": key,
            "value": value,
            "found": key in app._crm_state
        }
        
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
    
    elif name == "normalize_company_data":
        company_data = arguments.get("company_data", {})
        
        # Create a copy to avoid modifying the original
        normalized_data = company_data.copy()
        changes_made = []
        
        # Check if we should populate website from domain
        if should_populate_website_from_domain(company_data):
            domain = company_data.get("domain", "")
            old_website = company_data.get("website", "")
            new_website = normalize_domain_to_website(domain)
            
            normalized_data["website"] = new_website
            changes_made.append({
                "field": "website",
                "old_value": old_website,
                "new_value": new_website,
                "reason": "Populated from domain field"
            })
        
        # Normalize HubSpot field values to allowed options (removed industry and country per user request)
        hubspot_fields = ["company_type", "club_type"]
        for field in hubspot_fields:
            if field in company_data and company_data[field]:
                old_value = company_data[field]
                new_value = normalize_field_value(field, old_value)
                
                if new_value != old_value:
                    normalized_data[field] = new_value
                    changes_made.append({
                        "field": field,
                        "old_value": old_value,
                        "new_value": new_value,
                        "reason": f"Normalized to HubSpot allowed value"
                    })
        
        result = {
            "normalized_data": normalized_data,
            "changes_made": changes_made,
            "original_data": company_data,
            "hubspot_mappings": get_hubspot_field_mappings()
        }
        
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
    
    elif name == "determine_company_type_with_gemini":
        company_data = arguments.get("company_data", {})
        
        try:
            # Import Google Generative AI
            import google.generativeai as genai
            
            # Configure Gemini
            if not GOOGLE_API_KEY:
                raise Exception(f"Google API key not configured. Found in ENV_VARS: {bool(ENV_VARS.get('GOOGLE_API_KEY'))}, Found in os.getenv: {bool(os.getenv('GOOGLE_API_KEY'))}")
                
            genai.configure(api_key=GOOGLE_API_KEY)
            
            # Prepare company context
            company_name = company_data.get("name", "Unknown Company")
            description = company_data.get("description", "")
            club_info = company_data.get("club_info", "")
            amenities = []
            
            if company_data.get("has_pool") == "Yes":
                amenities.append("swimming pool")
            if company_data.get("has_tennis_courts") == "Yes":
                amenities.append("tennis courts")
            if company_data.get("number_of_holes"):
                amenities.append(f"{company_data.get('number_of_holes')}-hole golf course")
            
            context = f"""
            Company: {company_name}
            Description: {description}
            Club Information: {club_info}
            Amenities: {', '.join(amenities) if amenities else 'None specified'}
            Location: {company_data.get('city', '')}, {company_data.get('state', '')}
            Annual Revenue: {company_data.get('annualrevenue', 'Not specified')}
            """
            
            prompt = f"""
            Based on the following company information, determine the most appropriate company type from these exact HubSpot options:
            - "Public Course" (daily fee golf courses open to the public)
            - "Private Course" (exclusive membership-based golf courses)
            - "Municipal Course" (government-owned golf courses)
            - "Semi-Private Course" (hybrid public/private access)
            - "Golf Club" (traditional golf clubs with memberships)
            - "Management Company" (companies that manage golf facilities)
            - "Partner" (business partners)
            - "Other" (if none of the above fit)
            
            Company Information:
            {context}
            
            Respond with ONLY a JSON object in this exact format:
            {{
                "company_type": "exact_option_from_list",
                "confidence": 0.95,
                "reasoning": "Brief explanation of why this classification was chosen"
            }}
            """
            
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt)
            
            # Parse the response
            response_text = response.text.strip()
            if response_text.startswith("```json"):
                response_text = response_text.replace("```json", "").replace("```", "").strip()
            
            gemini_result = json.loads(response_text)
            
            result = {
                "success": True,
                "company_type": gemini_result.get("company_type"),
                "confidence": gemini_result.get("confidence", 0.0),
                "reasoning": gemini_result.get("reasoning", ""),
                "company_context": context.strip(),
                "method": "gemini-2.5-flash"
            }
            
        except Exception as e:
            result = {
                "success": False,
                "error": str(e),
                "company_type": "Other",
                "confidence": 0.0,
                "reasoning": "Error occurred during Gemini analysis"
            }
        
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
    
    elif name == "detect_competitors_from_website":
        website_url = arguments.get("website_url", "")
        company_name = arguments.get("company_name", "")
        
        # Known competitors from the field_enrichment_rules.json
        known_competitors = [
            "Club Essentials", "Jonas", "ForeTees", "Lightspeed Golf", "ClubProphet", 
            "Supreme Golf", "Northstar", "Club Systems International", "PGA Tour Superstores",
            "Golf Genius", "Club Prophet", "Callus", "Pacesetter", "Club App"
        ]
        
        try:
            import httpx
            from bs4 import BeautifulSoup
            
            # Normalize URL
            if not website_url.startswith(('http://', 'https://')):
                website_url = f"https://{website_url}"
            
            detected_competitors = []
            
            # Add headers to avoid being blocked
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
            }
            
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True, headers=headers) as client:
                try:
                    response = await client.get(website_url)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.text, 'html.parser')
                    page_text = soup.get_text().lower()
                    
                    # Search for competitor mentions
                    for competitor in known_competitors:
                        competitor_lower = competitor.lower()
                        if competitor_lower in page_text:
                            # Get some context around the mention
                            context_start = max(0, page_text.find(competitor_lower) - 100)
                            context_end = min(len(page_text), page_text.find(competitor_lower) + len(competitor_lower) + 100)
                            context = page_text[context_start:context_end].strip()
                            
                            detected_competitors.append({
                                "competitor": competitor,
                                "context": context,
                                "confidence": 0.8
                            })
                
                except httpx.HTTPError as e:
                    logger.warning(f"Failed to fetch {website_url}: {e}")
            
            # Determine final competitor
            final_competitor = "Unknown"
            if detected_competitors:
                # Use the first detected competitor
                final_competitor = detected_competitors[0]["competitor"]
            
            result = {
                "success": True,
                "website_url": website_url,
                "company_name": company_name,
                "detected_competitors": detected_competitors,
                "final_competitor": final_competitor,
                "search_performed": True
            }
            
        except Exception as e:
            result = {
                "success": False,
                "error": str(e),
                "website_url": website_url,
                "company_name": company_name,
                "detected_competitors": [],
                "final_competitor": "Unknown",
                "search_performed": False
            }
        
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
    
    elif name == "generate_club_info_with_gemini":
        company_name = arguments.get("company_name", "")
        city = arguments.get("city", "")
        state = arguments.get("state", "")
        website = arguments.get("website", "")
        
        try:
            # Import Google Generative AI
            import google.generativeai as genai
            from google.genai import types
            
            # Configure Gemini
            if not GOOGLE_API_KEY:
                raise Exception(f"Google API key not configured for club info generation. Found in ENV_VARS: {bool(ENV_VARS.get('GOOGLE_API_KEY'))}, Found in os.getenv: {bool(os.getenv('GOOGLE_API_KEY'))}")
                
            genai.configure(api_key=GOOGLE_API_KEY)
            
            # Create search query
            location = f"{city}, {state}" if city and state else ""
            search_context = f"{company_name} {location}".strip()
            
            prompt = f"""
            Research and provide comprehensive information about {company_name} located in {location}.
            
            I need you to find and provide:
            1. A detailed description of the club/course
            2. Specific amenities available (golf course details, pool, tennis courts, dining, etc.)
            3. Type of club (private, public, semi-private, etc.)
            4. Any unique features or characteristics
            5. Historical information if notable
            
            Format your response as a comprehensive club description similar to this example:
            "The Country Club of Virginia, located in Richmond, VA, is a private club featuring a 36-hole golf course. In addition to golf, the club offers amenities such as a pool and tennis facilities, catering to a variety of recreational interests for its members. The Country Club of Virginia is a traditional, family oriented social club, dedicated to providing its members excellent programs, activities, facilities, and services. One of the largest and finest private clubs in the nation..."
            
            Please provide a JSON response with this structure:
            {{
                "club_info": "Comprehensive description paragraph",
                "has_pool": "Yes/No/Unknown",
                "has_tennis_courts": "Yes/No/Unknown",
                "number_of_holes": "18" or number found,
                "club_type_description": "Private/Public/Semi-Private/Municipal/etc.",
                "key_amenities": ["list", "of", "amenities"],
                "search_confidence": 0.85
            }}
            
            Research: {search_context}
            """
            
            # Use Gemini with grounded search
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            # For now, use regular Gemini without grounded search to avoid API issues
            # TODO: Fix grounded search implementation later
            response = model.generate_content(prompt)
            
            # Parse the response
            response_text = response.text.strip()
            if response_text.startswith("```json"):
                response_text = response_text.replace("```json", "").replace("```", "").strip()
            
            gemini_result = json.loads(response_text)
            
            result = {
                "success": True,
                "company_name": company_name,
                "location": location,
                "club_info": gemini_result.get("club_info", ""),
                "has_pool": gemini_result.get("has_pool", "Unknown"),
                "has_tennis_courts": gemini_result.get("has_tennis_courts", "Unknown"),
                "number_of_holes": gemini_result.get("number_of_holes", ""),
                "club_type_description": gemini_result.get("club_type_description", ""),
                "key_amenities": gemini_result.get("key_amenities", []),
                "search_confidence": gemini_result.get("search_confidence", 0.0),
                "search_query": search_context
            }
            
        except Exception as e:
            # Fallback response structure
            result = {
                "success": False,
                "error": str(e),
                "company_name": company_name,
                "location": location,
                "club_info": f"{company_name}, located in {location}, is a golf facility. Additional information about amenities and services was not available during research.",
                "has_pool": "Unknown",
                "has_tennis_courts": "Unknown", 
                "number_of_holes": "",
                "club_type_description": "Unknown",
                "key_amenities": [],
                "search_confidence": 0.0,
                "search_query": search_context
            }
        
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
    
    else:
        return [TextContent(
            type="text",
            text=json.dumps({"error": f"Unknown tool: {name}"})
        )]

async def main():
    """Run the stdio server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
