#!/usr/bin/env python3
"""
A simple HubSpot MCP-compatible server that directly calls HubSpot APIs.
This bypasses the complexity of the official @hubspot/mcp-server subprocess.
"""

import os
import requests
import json
from datetime import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)

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

# Load environment variables at startup
ENV_VARS = load_env()
HUBSPOT_TOKEN = ENV_VARS.get('PRIVATE_APP_ACCESS_TOKEN')

def make_hubspot_request(method, endpoint, data=None):
    """Make a request to HubSpot API"""
    if not HUBSPOT_TOKEN:
        return {"error": "No HubSpot access token found"}
    
    headers = {
        'Authorization': f'Bearer {HUBSPOT_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    url = f'https://api.hubapi.com{endpoint}'
    
    try:
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers, params=data)
        elif method.upper() == 'POST':
            response = requests.post(url, headers=headers, json=data)
        elif method.upper() == 'PUT':
            response = requests.put(url, headers=headers, json=data)
        elif method.upper() == 'DELETE':
            response = requests.delete(url, headers=headers)
        else:
            return {"error": f"Unsupported method: {method}"}
        
        if response.status_code in [200, 201]:
            return response.json()
        else:
            return {"error": f"HubSpot API error: {response.status_code} - {response.text}"}
    
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}

@app.route('/mcp', methods=['POST'])
def handle_mcp_request():
    """Handle MCP-style JSON-RPC requests"""
    data = request.json
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400
    
    method = data.get('method')
    params = data.get('params', {})
    request_id = data.get('id', 1)
    
    # Handle different MCP methods
    if method == 'list_tools':
        tools = [
            {
                "name": "get_contacts",
                "description": "Get contacts from HubSpot",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "limit": {"type": "number", "description": "Number of contacts to retrieve (max 100)"}
                    }
                }
            },
            {
                "name": "get_companies", 
                "description": "Get companies from HubSpot",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "limit": {"type": "number", "description": "Number of companies to retrieve (max 100)"}
                    }
                }
            },
            {
                "name": "search_companies",
                "description": "Search for companies by name or domain",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query (company name or domain)"},
                        "limit": {"type": "number", "description": "Number of results to retrieve (max 100)"}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_company_details",
                "description": "Get comprehensive company information including contacts",
                "inputSchema": {
                    "type": "object", 
                    "properties": {
                        "company_id": {"type": "string", "description": "HubSpot company ID"},
                        "domain": {"type": "string", "description": "Company domain"}
                    }
                }
            },
            {
                "name": "create_contact",
                "description": "Create a new contact in HubSpot",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "email": {"type": "string", "description": "Contact email (required)"},
                        "firstname": {"type": "string", "description": "First name"},
                        "lastname": {"type": "string", "description": "Last name"},
                        "company": {"type": "string", "description": "Company name"},
                        "phone": {"type": "string", "description": "Phone number"},
                        "jobtitle": {"type": "string", "description": "Job title"},
                        "additional_properties": {"type": "object", "description": "Additional custom properties"}
                    },
                    "required": ["email"]
                }
            },
            {
                "name": "update_contact",
                "description": "Update an existing contact",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "contact_id": {"type": "string", "description": "HubSpot contact ID"},
                        "properties": {"type": "object", "description": "Properties to update"}
                    },
                    "required": ["contact_id", "properties"]
                }
            },
            {
                "name": "create_company",
                "description": "Create a new company in HubSpot",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Company name (required)"},
                        "domain": {"type": "string", "description": "Company domain"},
                        "industry": {"type": "string", "description": "Industry"},
                        "city": {"type": "string", "description": "City"},
                        "state": {"type": "string", "description": "State"},
                        "country": {"type": "string", "description": "Country"},
                        "phone": {"type": "string", "description": "Phone number"},
                        "additional_properties": {"type": "object", "description": "Additional custom properties"}
                    },
                    "required": ["name"]
                }
            },
            {
                "name": "send_email",
                "description": "Send an email through HubSpot",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "to_email": {"type": "string", "description": "Recipient email"},
                        "subject": {"type": "string", "description": "Email subject"},
                        "html_body": {"type": "string", "description": "HTML email body"},
                        "contact_id": {"type": "string", "description": "HubSpot contact ID (optional)"}
                    },
                    "required": ["to_email", "subject", "html_body"]
                }
            },
            {
                "name": "create_task",
                "description": "Create a task in HubSpot",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "subject": {"type": "string", "description": "Task subject"},
                        "body": {"type": "string", "description": "Task description"},
                        "due_date": {"type": "string", "description": "Due date (ISO format)"},
                        "task_type": {"type": "string", "description": "Task type (CALL, EMAIL, TODO)"},
                        "contact_id": {"type": "string", "description": "Associated contact ID"},
                        "company_id": {"type": "string", "description": "Associated company ID"}
                    },
                    "required": ["subject"]
                }
            },
            {
                "name": "get_deals",
                "description": "Get deals from HubSpot", 
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "limit": {"type": "number", "description": "Number of deals to retrieve (max 100)"}
                    }
                }
            },
            {
                "name": "create_deal",
                "description": "Create a new deal in HubSpot",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "dealname": {"type": "string", "description": "Deal name"},
                        "amount": {"type": "number", "description": "Deal amount"},
                        "dealstage": {"type": "string", "description": "Deal stage"},
                        "pipeline": {"type": "string", "description": "Pipeline ID"},
                        "closedate": {"type": "string", "description": "Close date (ISO format)"},
                        "contact_ids": {"type": "array", "items": {"type": "string"}, "description": "Associated contact IDs"},
                        "company_ids": {"type": "array", "items": {"type": "string"}, "description": "Associated company IDs"}
                    },
                    "required": ["dealname"]
                }
            },
            {
                "name": "generate_company_report",
                "description": "Generate comprehensive company analysis report",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "company_id": {"type": "string", "description": "HubSpot company ID"},
                        "domain": {"type": "string", "description": "Company domain"},
                        "include_contacts": {"type": "boolean", "description": "Include associated contacts", "default": True},
                        "include_deals": {"type": "boolean", "description": "Include associated deals", "default": True}
                    }
                }
            },
            {
                "name": "get_custom_properties",
                "description": "Get custom properties for an object type",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "object_type": {"type": "string", "description": "Object type (contacts, companies, deals)"}
                    },
                    "required": ["object_type"]
                }
            },
            {
                "name": "create_webhook",
                "description": "Create a webhook subscription",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "event_type": {"type": "string", "description": "Event type to subscribe to"},
                        "webhook_url": {"type": "string", "description": "URL to receive webhook notifications"},
                        "object_type": {"type": "string", "description": "Object type (contacts, companies, deals)"}
                    },
                    "required": ["event_type", "webhook_url", "object_type"]
                }
            },
            {
                "name": "get_account_info",
                "description": "Get HubSpot account information",
                "inputSchema": {"type": "object", "properties": {}}
            }
        ]
        
        return jsonify({
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {"tools": tools}
        })
    
    elif method == 'call_tool':
        tool_name = params.get('name')
        tool_args = params.get('arguments', {})
        
        if tool_name == 'get_contacts':
            limit = tool_args.get('limit', 10)
            result = make_hubspot_request('GET', f'/crm/v3/objects/contacts?limit={limit}')
            
        elif tool_name == 'get_companies':
            limit = tool_args.get('limit', 10) 
            result = make_hubspot_request('GET', f'/crm/v3/objects/companies?limit={limit}')
            
        elif tool_name == 'search_companies':
            query = tool_args.get('query')
            limit = tool_args.get('limit', 10)
            if not query:
                result = {"error": "Query parameter is required"}
            else:
                # Search companies by name or domain
                search_data = {
                    "filterGroups": [{
                        "filters": [
                            {
                                "propertyName": "name",
                                "operator": "CONTAINS_TOKEN",
                                "value": query
                            }
                        ]
                    }, {
                        "filters": [
                            {
                                "propertyName": "domain",
                                "operator": "CONTAINS_TOKEN", 
                                "value": query
                            }
                        ]
                    }],
                    "limit": limit,
                    "properties": ["name", "domain", "industry", "city", "state", "country", "phone", "website", "description"]
                }
                result = make_hubspot_request('POST', '/crm/v3/objects/companies/search', search_data)
        
        elif tool_name == 'get_company_details':
            company_id = tool_args.get('company_id')
            domain = tool_args.get('domain')
            
            if company_id:
                # Get company by ID with all properties
                company_result = make_hubspot_request('GET', f'/crm/v3/objects/companies/{company_id}?properties=name,domain,industry,city,state,country,phone,website,description,founded_year,num_employees,annual_revenue,type,timezone,hubspot_owner_id')
                
                if 'error' not in company_result:
                    # Get associated contacts
                    contacts_result = make_hubspot_request('GET', f'/crm/v3/objects/companies/{company_id}/associations/contacts')
                    
                    # Get associated deals
                    deals_result = make_hubspot_request('GET', f'/crm/v3/objects/companies/{company_id}/associations/deals')
                    
                    result = {
                        "company": company_result,
                        "associated_contacts": contacts_result,
                        "associated_deals": deals_result
                    }
                else:
                    result = company_result
                    
            elif domain:
                # Search by domain first
                search_data = {
                    "filterGroups": [{
                        "filters": [{
                            "propertyName": "domain",
                            "operator": "EQ",
                            "value": domain
                        }]
                    }],
                    "limit": 1,
                    "properties": ["name", "domain", "industry", "city", "state", "country", "phone", "website", "description", "founded_year", "num_employees", "annual_revenue"]
                }
                search_result = make_hubspot_request('POST', '/crm/v3/objects/companies/search', search_data)
                
                if 'error' not in search_result and search_result.get('results'):
                    company = search_result['results'][0]
                    company_id = company['id']
                    
                    # Get associated contacts and deals
                    contacts_result = make_hubspot_request('GET', f'/crm/v3/objects/companies/{company_id}/associations/contacts')
                    deals_result = make_hubspot_request('GET', f'/crm/v3/objects/companies/{company_id}/associations/deals')
                    
                    result = {
                        "company": company,
                        "associated_contacts": contacts_result,
                        "associated_deals": deals_result
                    }
                else:
                    result = {"error": f"Company with domain '{domain}' not found"}
            else:
                result = {"error": "Either company_id or domain must be provided"}
        
        elif tool_name == 'generate_company_report':
            company_id = tool_args.get('company_id')
            domain = tool_args.get('domain')
            include_contacts = tool_args.get('include_contacts', True)
            include_deals = tool_args.get('include_deals', True)
            
            # First get company details
            if company_id:
                company_result = make_hubspot_request('GET', f'/crm/v3/objects/companies/{company_id}?properties=name,domain,industry,city,state,country,phone,website,description,founded_year,num_employees,annual_revenue,type,timezone,hubspot_owner_id,createdate,lastmodifieddate')
            elif domain:
                search_data = {
                    "filterGroups": [{
                        "filters": [{
                            "propertyName": "domain",
                            "operator": "EQ", 
                            "value": domain
                        }]
                    }],
                    "limit": 1,
                    "properties": ["name", "domain", "industry", "city", "state", "country", "phone", "website", "description", "founded_year", "num_employees", "annual_revenue", "type", "timezone", "hubspot_owner_id", "createdate", "lastmodifieddate"]
                }
                search_result = make_hubspot_request('POST', '/crm/v3/objects/companies/search', search_data)
                if 'error' not in search_result and search_result.get('results'):
                    company_result = search_result['results'][0]
                    company_id = company_result['id']
                else:
                    result = {"error": f"Company with domain '{domain}' not found"}
                    return jsonify({
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}
                    })
            else:
                result = {"error": "Either company_id or domain must be provided"}
                return jsonify({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}
                })
            
            if 'error' not in company_result:
                report = {
                    "company_overview": company_result,
                    "report_generated": json.dumps(datetime.now().isoformat()),
                    "analysis": {}
                }
                
                # Get associated contacts with details
                if include_contacts:
                    contacts_associations = make_hubspot_request('GET', f'/crm/v3/objects/companies/{company_id}/associations/contacts')
                    if 'error' not in contacts_associations and contacts_associations.get('results'):
                        contact_ids = [assoc['id'] for assoc in contacts_associations['results']]
                        contacts_details = []
                        
                        for contact_id in contact_ids[:20]:  # Limit to 20 contacts
                            contact_detail = make_hubspot_request('GET', f'/crm/v3/objects/contacts/{contact_id}?properties=firstname,lastname,email,phone,jobtitle,lastmodifieddate,createdate,hubspot_owner_id')
                            if 'error' not in contact_detail:
                                contacts_details.append(contact_detail)
                        
                        report['contacts'] = {
                            "total_count": len(contact_ids),
                            "retrieved_count": len(contacts_details),
                            "contacts": contacts_details
                        }
                
                # Get associated deals with details
                if include_deals:
                    deals_associations = make_hubspot_request('GET', f'/crm/v3/objects/companies/{company_id}/associations/deals')
                    if 'error' not in deals_associations and deals_associations.get('results'):
                        deal_ids = [assoc['id'] for assoc in deals_associations['results']]
                        deals_details = []
                        
                        for deal_id in deal_ids[:20]:  # Limit to 20 deals
                            deal_detail = make_hubspot_request('GET', f'/crm/v3/objects/deals/{deal_id}?properties=dealname,amount,dealstage,pipeline,closedate,createdate,lastmodifieddate,hubspot_owner_id')
                            if 'error' not in deal_detail:
                                deals_details.append(deal_detail)
                        
                        report['deals'] = {
                            "total_count": len(deal_ids),
                            "retrieved_count": len(deals_details),
                            "deals": deals_details
                        }
                        
                        # Calculate deal analytics
                        if deals_details:
                            total_amount = sum(float(deal.get('properties', {}).get('amount', 0) or 0) for deal in deals_details)
                            open_deals = [deal for deal in deals_details if deal.get('properties', {}).get('dealstage', '').lower() not in ['closed won', 'closed lost']]
                            won_deals = [deal for deal in deals_details if deal.get('properties', {}).get('dealstage', '').lower() == 'closed won']
                            
                            report['analysis']['deal_summary'] = {
                                "total_deal_value": total_amount,
                                "open_deals_count": len(open_deals),
                                "won_deals_count": len(won_deals),
                                "total_deals_count": len(deals_details)
                            }
                
                # Add company analysis
                props = company_result.get('properties', {})
                report['analysis']['company_profile'] = {
                    "has_website": bool(props.get('website')),
                    "has_phone": bool(props.get('phone')),
                    "has_industry": bool(props.get('industry')),
                    "has_employee_count": bool(props.get('num_employees')),
                    "has_revenue": bool(props.get('annual_revenue')),
                    "location": f"{props.get('city', '')}, {props.get('state', '')}, {props.get('country', '')}".strip(', '),
                    "data_completeness": len([v for v in [props.get('website'), props.get('phone'), props.get('industry'), props.get('description')] if v]) / 4 * 100
                }
                
                result = report
            else:
                result = company_result
            
        elif tool_name == 'get_deals':
            limit = tool_args.get('limit', 10)
            result = make_hubspot_request('GET', f'/crm/v3/objects/deals?limit={limit}')
            
        elif tool_name == 'get_account_info':
            result = make_hubspot_request('GET', '/account-info/v3/details')
            
        else:
            result = {"error": f"Unknown tool: {tool_name}"}
        
        return jsonify({
            "jsonrpc": "2.0", 
            "id": request_id,
            "result": {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}
        })
    
    else:
        return jsonify({
            "jsonrpc": "2.0",
            "id": request_id, 
            "error": {"code": -32601, "message": f"Method not found: {method}"}
        })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "hubspot_token_configured": bool(HUBSPOT_TOKEN)})

if __name__ == '__main__':
    print(f"🚀 Starting Simple HubSpot MCP Server...")
    print(f"   HubSpot Token: {'✅ Configured' if HUBSPOT_TOKEN else '❌ Missing'}")
    app.run(host='0.0.0.0', port=8081, debug=True)
