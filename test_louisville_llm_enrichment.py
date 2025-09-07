#!/usr/bin/env python3
"""
Test LLM enrichment for Louisville Country Club
"""

import json
import requests
from crm_agent.agents.specialized.company_llm_enrichment_agent import create_company_llm_enrichment_agent

# MCP server configuration
MCP_URL = "http://localhost:8081/mcp"

def call_mcp_tool(tool_name, arguments=None):
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
            return {"error": result["error"]}
        
        content = result["result"]["content"][0]["text"]
        return json.loads(content)
        
    except Exception as e:
        return {"error": str(e)}

def test_louisville_llm_enrichment():
    """Test LLM enrichment for Louisville Country Club."""
    
    print("🧠 Testing LLM Enrichment for Louisville Country Club")
    print("=" * 60)
    
    # Get Louisville Country Club data
    print("📋 Fetching Louisville Country Club data...")
    company_result = call_mcp_tool("get_company_details", {"company_id": "15537372824"})
    
    if "error" in company_result:
        print(f"❌ Error: {company_result['error']}")
        return
    
    company = company_result.get("company", {})
    props = company.get("properties", {})
    
    print(f"✅ Company: {props.get('name', 'Unknown')}")
    print(f"📍 Location: {props.get('city', 'Unknown')}, {props.get('state', 'Unknown')}")
    print(f"🌐 Website: {props.get('website', 'Not set')}")
    print(f"🏢 Current Industry: {props.get('industry', 'Not set')}")
    print(f"💰 Current Revenue: {props.get('annualrevenue', 'Not set')}")
    print(f"📝 Description Length: {len(str(props.get('description', '')))}")
    
    # Show current field values for target fields
    print(f"\n📊 Current Target Field Values:")
    target_fields = ["club_info", "company_type", "annualrevenue", "has_pool", "has_tennis_courts", "number_of_holes", "industry", "description"]
    
    for field in target_fields:
        value = props.get(field, "Not set")
        if isinstance(value, str) and len(value) > 100:
            display_value = value[:100] + "..."
        else:
            display_value = str(value)
        print(f"   • {field}: {display_value}")
    
    # Create LLM enrichment agent
    print(f"\n🤖 Creating LLM Enrichment Agent...")
    try:
        llm_agent = create_company_llm_enrichment_agent()
        print("✅ Agent created successfully")
    except Exception as e:
        print(f"❌ Error creating agent: {e}")
        return
    
    print(f"\n🔍 Running LLM enrichment analysis...")
    print("This will use web search + Google Gemini LLM to enrich fields")
    
    try:
        # Test with specific fields that likely need enrichment
        test_fields = ["Club Info", "Company Type", "Has Pool", "Has Tennis Courts", "Number of Holes"]
        
        result = llm_agent.enrich_company_fields(company, test_fields)
        
        print(f"\n📊 LLM Enrichment Results:")
        print("=" * 40)
        print(f"Status: {result['status']}")
        print(f"Fields Processed: {result.get('total_fields_processed', 0)}")
        print(f"Successful Enrichments: {result.get('successful_enrichments', 0)}")
        print(f"Search Query: {result.get('search_query', 'N/A')}")
        
        enriched_fields = result.get("enriched_fields", {})
        if enriched_fields:
            print(f"\n✅ Enriched Fields:")
            for field, value in enriched_fields.items():
                if isinstance(value, str) and len(value) > 150:
                    display_value = value[:150] + "..."
                else:
                    display_value = str(value)
                print(f"   • {field}: {display_value}")
        else:
            print(f"\n❓ No fields were enriched")
        
        # Show field-level results
        field_results = result.get("field_results", {})
        if field_results:
            print(f"\n📋 Field-by-Field Results:")
            for field_name, field_result in field_results.items():
                status = field_result.get("status", "unknown")
                reason = field_result.get("reason", "No reason provided")
                print(f"   • {field_name}: {status} - {reason}")
        
        # If we got enrichments, ask about applying them
        if enriched_fields:
            print(f"\n🔄 Would you like to apply these enrichments to HubSpot? (y/n): ", end="")
            try:
                response = input().strip().lower()
                if response in ['y', 'yes']:
                    apply_enrichments(enriched_fields)
                else:
                    print("   ℹ️  Enrichments not applied")
            except KeyboardInterrupt:
                print("\n   ℹ️  Enrichments not applied")
        
    except Exception as e:
        print(f"❌ Error during enrichment: {e}")
        import traceback
        traceback.print_exc()

def apply_enrichments(enriched_fields):
    """Apply enrichments to HubSpot."""
    print(f"\n🔄 Applying {len(enriched_fields)} field enrichments to Louisville Country Club...")
    
    update_result = call_mcp_tool("update_company", {
        "company_id": "15537372824",
        "properties": enriched_fields
    })
    
    if "error" in update_result:
        print(f"❌ Failed to apply enrichments: {update_result['error']}")
    else:
        print(f"✅ Successfully applied {len(enriched_fields)} field enrichments!")
        print("🎯 Check your HubSpot record to see the improvements!")

if __name__ == "__main__":
    test_louisville_llm_enrichment()
