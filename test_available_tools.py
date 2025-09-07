#!/usr/bin/env python3
"""
Test what tools are actually available on the MCP server
"""

import requests
import json

def test_tool_availability():
    """Test which tools are available on the MCP server."""
    
    mcp_url = "http://localhost:8081/mcp"
    
    # Try different tools to see what's available
    tools_to_test = [
        "get_account_info",
        "search_companies", 
        "get_company_details",
        "get_companies",
        "get_contacts",
        "web_search",
        "search_web",
        "google_search",
        "update_company",
        "create_company"
    ]
    
    print("🔍 Testing available MCP tools...")
    available_tools = []
    
    for tool in tools_to_test:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "call_tool",
            "params": {
                "name": tool,
                "arguments": {}
            }
        }
        
        try:
            response = requests.post(mcp_url, json=payload, timeout=5)
            result = response.json()
            
            if "result" in result:
                content = result["result"]["content"][0].get("text", "{}")
                data = json.loads(content)
                if "error" in data:
                    if "Unknown tool" in data["error"]:
                        status = "❌ Not available"
                    else:
                        status = f"⚠️  Available but error: {data['error'][:30]}..."
                        available_tools.append(tool)
                else:
                    status = "✅ Available and working"
                    available_tools.append(tool)
            else:
                error_msg = result.get("error", {}).get("message", "Unknown error")
                status = f"❌ Failed: {error_msg}"
            
            print(f"   {tool}: {status}")
            
        except Exception as e:
            print(f"   {tool}: ❌ Exception: {e}")
    
    print(f"\n📋 Summary:")
    print(f"   Available tools: {len(available_tools)}")
    for tool in available_tools:
        print(f"   ✅ {tool}")

if __name__ == "__main__":
    test_tool_availability()
