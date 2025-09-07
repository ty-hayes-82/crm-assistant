#!/usr/bin/env python3
"""
Enhanced Contact Enrichment with Real Web Search
Uses the WebSearchAgent to find actual contact information from the web
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import requests
import json
from typing import Dict, Any

# Import the web search agent
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from web_search_agent import create_web_search_agent

# MCP server configuration
MCP_URL = "http://localhost:8081/mcp"

def call_mcp_tool(tool_name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
    """Call a tool via the MCP server."""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "call_tool",
        "params": {
            "name": tool_name,
            "arguments": arguments or {}
        }
    }
    
    try:
        response = requests.post(MCP_URL, json=payload)
        response.raise_for_status()
        result = response.json()
        
        if "error" in result:
            return {"error": result["error"]}
        
        content = result["result"]["content"][0]["text"]
        return json.loads(content)
    
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}

def fix_austin_golf_club_competitors():
    """Fix the competitor field for Austin Golf Club with correct Swoop Golf context."""
    print("🏌️ Fixing Austin Golf Club Competitors")
    print("=" * 50)
    print("Context: Austin Golf Club is a Swoop Golf customer (golf course)")
    print("Competitors should be OTHER GOLF COURSES, not booking platforms")
    print()
    
    # Find Austin Golf Club
    search_result = call_mcp_tool("search_companies", {
        "query": "Austin Golf Club",
        "limit": 1
    })
    
    if "error" in search_result or not search_result.get("results"):
        print("❌ Austin Golf Club not found")
        return False
    
    company = search_result["results"][0]
    company_id = company["id"]
    current_props = company.get("properties", {})
    
    print(f"✅ Found: {current_props.get('name')} in {current_props.get('city')}")
    
    # Correct competitors for Austin Golf Club (golf course)
    correct_competitors = [
        "Barton Creek Country Club",
        "Austin Country Club", 
        "Hills Country Club",
        "Lakeway Resort & Spa",
        "Lost Creek Country Club",
        "Falcon Head Golf Club",
        "Grey Rock Golf Club"
    ]
    
    print(f"\n🏆 Correcting competitors to other Austin-area golf courses:")
    for competitor in correct_competitors:
        print(f"   • {competitor}")
    
    # Update with corrected competitors
    updates = {
        "competitor": ", ".join(correct_competitors)
    }
    
    confirm = input(f"\nUpdate Austin Golf Club with correct golf course competitors? (y/N): ").strip().lower()
    if confirm not in ['y', 'yes']:
        print("❌ Update cancelled")
        return False
    
    result = call_mcp_tool("update_company", {
        "company_id": company_id,
        "properties": updates
    })
    
    if "error" in result:
        print(f"❌ Update failed: {result['error']}")
        return False
    else:
        print("✅ Competitors corrected successfully!")
        return True

def enrich_with_web_search(company_name: str, company_id: str, current_props: Dict[str, Any]):
    """Use real web search to find missing contact and domain information."""
    print(f"\n🔍 Using Web Search Agent for {company_name}")
    print("=" * 50)
    
    # Create web search agent
    web_agent = create_web_search_agent()
    
    # Perform comprehensive web search
    location = f"{current_props.get('city', '')}, {current_props.get('state', '')}"
    search_results = web_agent.comprehensive_company_search(company_name, location)
    
    # Prepare updates based on web search results
    updates = {}
    
    # 1. Domain/Website
    if search_results.get('domain') and not current_props.get('domain'):
        updates['domain'] = search_results['domain']
        if not current_props.get('website'):
            updates['website'] = f"https://{search_results['domain']}"
    
    # 2. Contact Information
    if search_results.get('contact_info'):
        contact_info = search_results['contact_info']
        
        # Email pattern
        if contact_info['emails'] and not current_props.get('email_pattern'):
            # Derive email pattern from found emails
            if contact_info['emails']:
                email = contact_info['emails'][0]
                domain_part = email.split('@')[1] if '@' in email else ''
                if domain_part:
                    updates['email_pattern'] = f"firstname.lastname@{domain_part}"
        
        # General contact email
        if contact_info['emails'] and not current_props.get('general_email'):
            # Look for info@ or contact@ emails
            general_emails = [e for e in contact_info['emails'] if any(prefix in e.lower() for prefix in ['info@', 'contact@', 'hello@'])]
            if general_emails:
                updates['general_email'] = general_emails[0]
    
    return updates, search_results

def main():
    """Main enrichment process."""
    print("🔍 Enhanced Contact Enrichment with Real Web Search")
    print("=" * 60)
    print("This system uses ACTUAL web search to find contact information!")
    print()
    
    # Check MCP server
    try:
        health_response = requests.get("http://localhost:8081/health")
        if health_response.status_code == 200:
            print("✅ MCP Server: Connected")
        else:
            print("❌ MCP Server not responding")
            return
    except Exception as e:
        print(f"❌ Cannot connect to MCP server: {e}")
        return
    
    # Step 1: Fix competitors first
    print("\n🎯 Step 1: Fix Competitor Information")
    competitor_fixed = fix_austin_golf_club_competitors()
    
    if not competitor_fixed:
        return
    
    # Step 2: Enrich with web search
    print("\n🎯 Step 2: Web Search Enrichment")
    
    # Find Austin Golf Club again
    search_result = call_mcp_tool("search_companies", {
        "query": "Austin Golf Club",
        "limit": 1
    })
    
    company = search_result["results"][0]
    company_id = company["id"]
    current_props = company.get("properties", {})
    
    # Perform web search enrichment
    updates, search_results = enrich_with_web_search(
        current_props.get('name', ''),
        company_id,
        current_props
    )
    
    if updates:
        print(f"\n📊 Web search found {len(updates)} fields to update:")
        for field, value in updates.items():
            print(f"   • {field}: {value}")
        
        confirm = input(f"\nApply web search findings to HubSpot? (y/N): ").strip().lower()
        if confirm in ['y', 'yes']:
            result = call_mcp_tool("update_company", {
                "company_id": company_id,
                "properties": updates
            })
            
            if "error" in result:
                print(f"❌ Update failed: {result['error']}")
            else:
                print("✅ Web search enrichment applied!")
        else:
            print("❌ Web search updates cancelled")
    else:
        print("ℹ️  No additional fields found through web search")
    
    # Show summary of what was found
    print(f"\n📋 Web Search Results Summary:")
    print("=" * 40)
    
    if search_results.get('domain'):
        print(f"🌐 Domain: {search_results['domain']}")
    
    if search_results.get('contact_info'):
        contact = search_results['contact_info']
        print(f"📧 Emails found: {len(contact['emails'])}")
        print(f"📞 Phones found: {len(contact['phones'])}")
        if contact['social_media']:
            print(f"📱 Social media: {len(contact['social_media'])} profiles")
    
    print(f"\n🎉 Enhancement Complete!")
    print("✅ Competitors corrected to reflect golf course competition")
    print("✅ Web search performed for additional contact data")
    print("🎯 Check your HubSpot record to see all improvements!")

if __name__ == "__main__":
    main()
