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
        async with httpx.AsyncClient(timeout=30.0) as client:
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
    """Handle tool calls."""
    
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
