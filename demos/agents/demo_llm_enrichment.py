#!/usr/bin/env python3
"""
Demo script for the Company LLM Enrichment Agent

This script demonstrates how the new company_llm_enrichment subagent works by:
1. Fetching companies with missing/incomplete field data
2. Using Google Gemini LLM + web search to enrich fields
3. Updating HubSpot with enriched data
"""

import json
import requests
from typing import Dict, Any, List
from crm_agent.agents.specialized.field_specialist_agents import create_company_llm_enrichment_agent

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

def get_companies_needing_llm_enrichment(limit: int = 5) -> List[Dict[str, Any]]:
    """Get companies that need LLM field enrichment."""
    print("🔍 Finding companies that need LLM field enrichment...")
    
    # Get all companies
    companies_result = call_mcp_tool("get_companies", {"limit": 50})
    
    if "error" in companies_result:
        print(f"❌ Error fetching companies: {companies_result['error']}")
        return []
    
    companies = companies_result.get("results", [])
    
    # Filter companies that need LLM enrichment
    candidates = []
    
    for company in companies:
        props = company.get("properties", {})
        
        # Check for missing/incomplete target fields
        needs_enrichment = (
            not props.get("description") or len(str(props.get("description", ""))) < 50 or
            not props.get("industry") or
            not props.get("annualrevenue") or
            props.get("company_type") in ["", None, "Other"] or
            not props.get("club_info") or len(str(props.get("club_info", ""))) < 50
        )
        
        if needs_enrichment:
            candidates.append(company)
            
        if len(candidates) >= limit:
            break
    
    print(f"   ✅ Found {len(candidates)} companies needing LLM enrichment")
    return candidates

def demo_llm_enrichment():
    """Demo the LLM enrichment functionality."""
    print("🧠 Company LLM Enrichment Agent Demo")
    print("=" * 60)
    print("This demo shows how the company_llm_enrichment agent uses")
    print("Google Gemini LLM + web search to enrich company fields.")
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
    companies = get_companies_needing_llm_enrichment(3)
    
    if not companies:
        print("ℹ️  No companies found that need LLM enrichment")
        return
    
    # Create the LLM enrichment agent
    print("🤖 Creating Company LLM Enrichment Agent...")
    try:
        llm_agent = create_company_llm_enrichment_agent()
        print("   ✅ Agent created successfully")
    except Exception as e:
        print(f"   ❌ Error creating agent: {e}")
        return
    print()
    
    # Process companies
    print(f"🔄 Processing {len(companies)} companies with LLM enrichment...")
    print("=" * 60)
    
    results = []
    updates_to_apply = []
    
    for i, company in enumerate(companies, 1):
        props = company.get("properties", {})
        company_name = props.get("name", f"Company {i}")
        company_id = company.get("id")
        city = props.get("city", "")
        state = props.get("state", "")
        location = f"{city}, {state}" if city and state else city or state or "Unknown"
        
        print(f"\n{i}. {company_name}")
        print(f"   📍 Location: {location}")
        print(f"   🏢 Current Industry: {props.get('industry', 'Not set')}")
        print(f"   💰 Current Revenue: {props.get('annualrevenue', 'Not set')}")
        print(f"   📝 Description Length: {len(str(props.get('description', '')))}")
        
        # Analyze with LLM agent
        try:
            print("   🧠 Analyzing with LLM...")
            
            # For demo, let's focus on a few key fields
            target_fields = ["Industry", "Description", "Annual Revenue", "Club Info"]
            
            result = llm_agent.enrich_company_fields(company, target_fields)
            result["company_name"] = company_name
            result["company_id"] = company_id
            result["location"] = location
            results.append(result)
            
            print(f"   📊 Status: {result['status']}")
            print(f"   🎯 Fields Processed: {result.get('total_fields_processed', 0)}")
            print(f"   ✅ Successful Enrichments: {result.get('successful_enrichments', 0)}")
            
            # Show enriched fields
            enriched_fields = result.get('enriched_fields', {})
            if enriched_fields:
                print("   📋 Enriched Fields:")
                for field, value in enriched_fields.items():
                    display_value = str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
                    print(f"      • {field}: {display_value}")
                
                # Prepare for HubSpot update
                updates_to_apply.append({
                    'company_id': company_id,
                    'company_name': company_name,
                    'enriched_fields': enriched_fields
                })
            else:
                print("   ❓ No fields were enriched")
                
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
    
    total_enrichments = sum(r.get('successful_enrichments', 0) for r in results)
    total_companies = len(companies)
    
    print(f"   Companies Processed: {total_companies}")
    print(f"   Total Field Enrichments: {total_enrichments}")
    print(f"   Companies with Updates: {len(updates_to_apply)}")
    
    # Show field-level summary
    field_counts = {}
    for result in results:
        for field in result.get('enriched_fields', {}):
            field_counts[field] = field_counts.get(field, 0) + 1
    
    if field_counts:
        print(f"\n   📋 Fields Enriched:")
        for field, count in field_counts.items():
            print(f"      • {field}: {count} companies")
    
    # Show updates that would be applied
    if updates_to_apply:
        print(f"\n🔄 Updates Ready to Apply ({len(updates_to_apply)}):")
        print("=" * 60)
        
        for update in updates_to_apply:
            print(f"   • {update['company_name']}")
            for field, value in update['enriched_fields'].items():
                display_value = str(value)[:60] + "..." if len(str(value)) > 60 else str(value)
                print(f"     {field}: {display_value}")
            print()
        
        # Ask if user wants to apply updates
        print(f"❓ Apply these LLM enrichment updates to HubSpot? (y/n): ", end="")
        try:
            response = input().strip().lower()
            if response in ['y', 'yes']:
                apply_llm_updates(updates_to_apply)
            else:
                print("   ℹ️  Updates not applied")
        except KeyboardInterrupt:
            print("\n   ℹ️  Updates not applied")
    else:
        print("\n   ℹ️  No updates ready to apply")
    
    print(f"\n🎉 LLM enrichment demo completed!")

def apply_llm_updates(updates: List[Dict[str, Any]]):
    """Apply LLM enrichment updates to HubSpot."""
    print(f"\n🔄 Applying {len(updates)} LLM enrichment updates...")
    
    successful_updates = 0
    failed_updates = 0
    
    for update in updates:
        company_id = update['company_id']
        company_name = update['company_name']
        enriched_fields = update['enriched_fields']
        
        print(f"   🔄 Updating {company_name}...")
        
        # Update company in HubSpot
        update_result = call_mcp_tool("update_company", {
            "company_id": company_id,
            "properties": enriched_fields
        })
        
        if "error" in update_result:
            print(f"      ❌ Failed: {update_result['error']}")
            failed_updates += 1
        else:
            print(f"      ✅ Updated {len(enriched_fields)} fields")
            successful_updates += 1
    
    print(f"\n📊 Update Results:")
    print(f"   ✅ Successful: {successful_updates}")
    print(f"   ❌ Failed: {failed_updates}")

def test_with_specific_company():
    """Test LLM enrichment with a specific company."""
    print("\n🎯 Testing with Louisville Country Club...")
    
    # Get Louisville Country Club data
    company_result = call_mcp_tool("get_company_details", {"company_id": "15537372824"})
    
    if "error" in company_result:
        print(f"❌ Error fetching company: {company_result['error']}")
        return
    
    company = company_result.get("company", {})
    
    # Create LLM agent and test
    llm_agent = create_company_llm_enrichment_agent()
    
    # Test specific fields
    target_fields = ["Club Info", "Has Pool", "Has Tennis Courts", "Number of Holes"]
    
    result = llm_agent.enrich_company_fields(company, target_fields)
    
    print("📊 Louisville Country Club LLM Enrichment:")
    print(json.dumps(result, indent=2))

def main():
    """Run the LLM enrichment demo."""
    try:
        demo_llm_enrichment()
        
        # Uncomment to test with specific company
        # test_with_specific_company()
        
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")

if __name__ == "__main__":
    main()
