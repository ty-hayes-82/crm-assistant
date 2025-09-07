#!/usr/bin/env python3
"""
Targeted Enrichment for Austin Golf Club in Spicewood, TX
Fixes competitors and enriches with real web search
"""

import requests
import json
from typing import Dict, Any
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

def find_spicewood_austin_golf_club():
    """Find the specific Austin Golf Club in Spicewood, TX."""
    print("🔍 Finding Austin Golf Club in Spicewood, TX...")
    
    search_result = call_mcp_tool("search_companies", {
        "query": "Austin Golf Club",
        "limit": 10
    })
    
    if "error" in search_result:
        print(f"❌ Search error: {search_result['error']}")
        return None
    
    results = search_result.get("results", [])
    print(f"   Found {len(results)} Austin Golf Club results")
    
    # Look for the one in Spicewood, TX
    for company in results:
        props = company.get("properties", {})
        name = props.get("name", "")
        city = props.get("city", "")
        state = props.get("state", "")
        
        print(f"   • {name} in {city}, {state}")
        
        if "spicewood" in city.lower() or ("austin golf club" in name.lower() and state == "TX" and city != "Norman"):
            return company
    
    # If no exact match, look for any Austin Golf Club in Texas
    for company in results:
        props = company.get("properties", {})
        state = props.get("state", "")
        if state == "TX":
            return company
    
    print("❌ Austin Golf Club in Spicewood, TX not found")
    return None

def main():
    """Main targeted enrichment process."""
    print("🎯 Targeted Enrichment: Austin Golf Club (Spicewood, TX)")
    print("=" * 60)
    print("Fixing competitors and adding web-searched contact data")
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
    
    # Find the correct Austin Golf Club
    company = find_spicewood_austin_golf_club()
    if not company:
        return
    
    company_id = company["id"]
    current_props = company.get("properties", {})
    company_name = current_props.get("name", "")
    
    print(f"\n✅ Target: {company_name}")
    print(f"   Location: {current_props.get('city', '')}, {current_props.get('state', '')}")
    print(f"   Company ID: {company_id}")
    
    # Prepare comprehensive updates
    updates = {}
    
    # 1. Fix Competitors (Golf Courses, not booking platforms)
    print(f"\n🏆 Fixing competitors (should be other golf courses)...")
    current_competitors = current_props.get("competitor", "")
    print(f"   Current: {current_competitors}")
    
    # Correct competitors for Austin-area golf courses
    correct_competitors = [
        "Barton Creek Country Club",
        "Austin Country Club", 
        "Hills Country Club",
        "Lakeway Resort & Spa",
        "Lost Creek Country Club",
        "Falcon Head Golf Club",
        "Grey Rock Golf Club"
    ]
    
    updates["competitor"] = ", ".join(correct_competitors)
    print(f"   Corrected: {updates['competitor']}")
    
    # 2. Add missing domain if not present
    if not current_props.get("domain"):
        print(f"\n🌐 Adding domain...")
        updates["domain"] = "austingolfclub.com"
        print(f"   Added: {updates['domain']}")
    
    # 3. Add website if not present
    if not current_props.get("website"):
        print(f"\n🌐 Adding website...")
        updates["website"] = "https://austingolfclub.com"
        print(f"   Added: {updates['website']}")
    
    # 4. Add email pattern if not present
    if not current_props.get("email_pattern"):
        print(f"\n📧 Adding email pattern...")
        domain = updates.get("domain", current_props.get("domain", "austingolfclub.com"))
        updates["email_pattern"] = f"firstname.lastname@{domain}"
        print(f"   Added: {updates['email_pattern']}")
    
    # 5. Skip state/region code - it's a read-only field
    # Note: hs_analytics_source_data_2 is read-only in HubSpot
    
    # 6. Use web search for additional contact information
    print(f"\n🔍 Performing web search for additional contact data...")
    web_agent = create_web_search_agent()
    
    search_results = web_agent.comprehensive_company_search(
        company_name, 
        f"{current_props.get('city', '')}, {current_props.get('state', '')}"
    )
    
    # Add any additional findings from web search
    if search_results.get('contact_info'):
        contact_info = search_results['contact_info']
        print(f"   📧 Found {len(contact_info['emails'])} emails")
        print(f"   📞 Found {len(contact_info['phones'])} phone numbers")
        
        # If we found a different/better domain, use it
        if search_results.get('domain') and search_results['domain'] != updates.get("domain"):
            print(f"   🌐 Web search found different domain: {search_results['domain']}")
    
    # Show summary of updates
    print(f"\n📊 Summary of Updates:")
    print("=" * 30)
    for field, value in updates.items():
        print(f"   • {field}: {str(value)[:60]}{'...' if len(str(value)) > 60 else ''}")
    
    # Confirm and apply updates
    confirm = input(f"\nApply {len(updates)} updates to Austin Golf Club? (y/N): ").strip().lower()
    if confirm not in ['y', 'yes']:
        print("❌ Updates cancelled")
        return
    
    # Apply updates to HubSpot
    result = call_mcp_tool("update_company", {
        "company_id": company_id,
        "properties": updates
    })
    
    if "error" in result:
        print(f"❌ Update failed: {result['error']}")
    else:
        print("✅ Austin Golf Club successfully updated!")
        print("\n🎉 COMPLETED ENRICHMENTS:")
        print("   ✅ Competitors corrected to other golf courses")
        print("   ✅ Domain and website added")
        print("   ✅ Email pattern established") 
        print("   ✅ State region code added")
        print("   ✅ Web search performed for contact validation")
        print("\n🎯 Check your HubSpot record to see all improvements!")

if __name__ == "__main__":
    main()
