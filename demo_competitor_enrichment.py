#!/usr/bin/env python3
"""
Demo script for the Company Competitor Field Enrichment Agent

This script demonstrates how the new company_competitor subagent works by:
1. Fetching companies with Unknown/empty competitor fields
2. Using website scraping to detect competitor software
3. Updating the competitor field with detected values
"""

import json
import requests
from typing import Dict, Any, List
from crm_agent.agents.specialized.field_specialist_agents import create_company_competitor_agent

# MCP server configuration
MCP_URL = "http://localhost:8081/mcp"

def call_mcp_tool(tool_name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
    """Call an MCP tool and return the result."""
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
        response = requests.post(MCP_URL, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        if "error" in result:
            print(f"❌ MCP Error: {result['error']}")
            return {"error": result["error"]}
        
        # Parse the content from MCP response
        content = result["result"]["content"][0]["text"]
        return json.loads(content)
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
        return {"error": str(e)}
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
        return {"error": f"JSON decode error: {e}"}
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return {"error": str(e)}

def get_companies_needing_competitor_enrichment(limit: int = 10) -> List[Dict[str, Any]]:
    """Get companies that need competitor field enrichment."""
    print("🔍 Finding companies that need competitor enrichment...")
    
    # Get all companies
    companies_result = call_mcp_tool("get_companies", {"limit": 100})
    
    if "error" in companies_result:
        print(f"❌ Error fetching companies: {companies_result['error']}")
        return []
    
    companies = companies_result.get("results", [])
    
    # Filter companies that need competitor enrichment
    candidates = []
    
    for company in companies:
        props = company.get("properties", {})
        competitor = props.get("competitor", "").strip().lower()
        website = props.get("website", "") or props.get("domain", "")
        
        # Include if competitor is Unknown, empty, or "Not Sure" AND has a website
        if competitor in ["", "unknown", "not sure"] and website:
            candidates.append(company)
            
        if len(candidates) >= limit:
            break
    
    print(f"   ✅ Found {len(candidates)} companies needing competitor enrichment")
    return candidates

def demo_competitor_detection():
    """Demo the competitor detection functionality."""
    print("🏆 Company Competitor Field Enrichment Demo")
    print("=" * 60)
    print("This demo shows how the company_competitor agent detects")
    print("competitor software by scraping company websites.")
    print()
    
    # Check MCP server connection
    health_check = call_mcp_tool("get_account_info")
    if "error" in health_check:
        print("❌ MCP server not accessible. Please start the server:")
        print("   adk run crm_agent (MCP server starts automatically)")
        return
    
    print("✅ MCP server connected")
    print()
    
    # Get companies needing enrichment
    companies = get_companies_needing_competitor_enrichment(5)
    
    if not companies:
        print("ℹ️  No companies found that need competitor enrichment")
        return
    
    # Create the competitor agent
    print("🤖 Creating Company Competitor Agent...")
    competitor_agent = create_company_competitor_agent()
    print("   ✅ Agent created successfully")
    print()
    
    # Process companies
    print(f"🔄 Processing {len(companies)} companies...")
    print("=" * 60)
    
    results = []
    updates_to_apply = []
    
    for i, company in enumerate(companies, 1):
        props = company.get("properties", {})
        company_name = props.get("name", f"Company {i}")
        company_id = company.get("id")
        website = props.get("website", "") or props.get("domain", "")
        current_competitor = props.get("competitor", "")
        
        print(f"\n{i}. {company_name}")
        print(f"   🌐 Website: {website}")
        print(f"   🏆 Current Competitor: {current_competitor or 'Empty'}")
        
        # Analyze competitor
        try:
            result = competitor_agent.enrich_competitor_field(company)
            result["company_name"] = company_name
            result["company_id"] = company_id
            result["website"] = website
            results.append(result)
            
            print(f"   📊 Status: {result['status']}")
            print(f"   🎯 New Value: {result['new_value']}")
            
            if result['status'] == 'enriched':
                updates_to_apply.append({
                    'company_id': company_id,
                    'company_name': company_name,
                    'field': 'competitor',
                    'old_value': result['current_value'],
                    'new_value': result['new_value']
                })
                print(f"   ✅ Ready to update: {result['current_value']} → {result['new_value']}")
            
            if 'reason' in result:
                print(f"   💭 Reason: {result['reason']}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append({
                'company_name': company_name,
                'company_id': company_id,
                'status': 'error',
                'reason': str(e)
            })
    
    # Summary
    print(f"\n📊 Summary")
    print("=" * 60)
    
    status_counts = {}
    for result in results:
        status = result['status']
        status_counts[status] = status_counts.get(status, 0) + 1
    
    for status, count in status_counts.items():
        print(f"   {status.title()}: {count}")
    
    # Show updates that would be applied
    if updates_to_apply:
        print(f"\n🔄 Updates Ready to Apply ({len(updates_to_apply)}):")
        print("=" * 60)
        
        for update in updates_to_apply:
            print(f"   • {update['company_name']}")
            print(f"     {update['old_value']} → {update['new_value']}")
        
        # Ask if user wants to apply updates
        print(f"\n❓ Apply these {len(updates_to_apply)} competitor updates? (y/n): ", end="")
        try:
            response = input().strip().lower()
            if response in ['y', 'yes']:
                apply_competitor_updates(updates_to_apply)
            else:
                print("   ℹ️  Updates not applied")
        except KeyboardInterrupt:
            print("\n   ℹ️  Updates not applied")
    else:
        print("\n   ℹ️  No updates needed")
    
    print(f"\n🎉 Competitor enrichment demo completed!")

def apply_competitor_updates(updates: List[Dict[str, Any]]):
    """Apply competitor field updates to HubSpot."""
    print(f"\n🔄 Applying {len(updates)} competitor updates...")
    
    successful_updates = 0
    failed_updates = 0
    
    for update in updates:
        company_id = update['company_id']
        company_name = update['company_name']
        new_competitor = update['new_value']
        
        print(f"   🔄 Updating {company_name}...")
        
        # Update company in HubSpot
        update_result = call_mcp_tool("update_company", {
            "company_id": company_id,
            "properties": {
                "competitor": new_competitor
            }
        })
        
        if "error" in update_result:
            print(f"      ❌ Failed: {update_result['error']}")
            failed_updates += 1
        else:
            print(f"      ✅ Updated to: {new_competitor}")
            successful_updates += 1
    
    print(f"\n📊 Update Results:")
    print(f"   ✅ Successful: {successful_updates}")
    print(f"   ❌ Failed: {failed_updates}")

def main():
    """Run the competitor enrichment demo."""
    try:
        demo_competitor_detection()
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")

if __name__ == "__main__":
    main()
