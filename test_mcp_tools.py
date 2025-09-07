#!/usr/bin/env python3
"""
Test MCP server tools and web search availability
"""

import requests
import json

def test_mcp_server():
    """Test MCP server connection and available tools."""
    
    mcp_url = "http://localhost:8081/mcp"
    
    print("🔍 Testing MCP server connection...")
    
    # Test 1: List available tools
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {}
    }
    
    try:
        response = requests.post(mcp_url, json=payload, timeout=10)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ MCP server is responding")
            
            if "result" in result and "tools" in result["result"]:
                tools = result["result"]["tools"]
                print(f"📋 Available tools ({len(tools)}):")
                for tool in tools:
                    name = tool.get("name", "Unknown")
                    description = tool.get("description", "No description")[:60] + "..."
                    print(f"  • {name}: {description}")
                
                # Check if web_search is available
                web_search_available = any(tool.get("name") == "web_search" for tool in tools)
                print(f"\n🔍 Web search tool available: {'✅ Yes' if web_search_available else '❌ No'}")
                
            else:
                print("No tools list found in response")
                print(f"Response: {json.dumps(result, indent=2)}")
        else:
            print(f"❌ Server error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False
    
    # Test 2: Try a simple tool call (get_account_info)
    print(f"\n🧪 Testing simple tool call...")
    payload = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "call_tool",
        "params": {
            "name": "get_account_info",
            "arguments": {}
        }
    }
    
    try:
        response = requests.post(mcp_url, json=payload, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if "error" not in result:
                print("✅ Basic tool calling works")
            else:
                print(f"❌ Tool call error: {result['error']}")
        else:
            print(f"❌ Tool call failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Tool call error: {e}")
    
    # Test 3: Try web search if available
    print(f"\n🌐 Testing web search...")
    payload = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "call_tool",
        "params": {
            "name": "web_search",
            "arguments": {
                "query": "Louisville Country Club golf",
                "num_results": 3
            }
        }
    }
    
    try:
        response = requests.post(mcp_url, json=payload, timeout=15)
        if response.status_code == 200:
            result = response.json()
            if "error" not in result:
                print("✅ Web search works!")
                # Try to parse the result
                if "result" in result and "content" in result["result"]:
                    content = result["result"]["content"][0].get("text", "{}")
                    try:
                        search_data = json.loads(content)
                        if "results" in search_data:
                            print(f"   Found {len(search_data['results'])} search results")
                            for i, res in enumerate(search_data["results"][:2], 1):
                                title = res.get("title", "No title")[:50]
                                print(f"   {i}. {title}...")
                        else:
                            print(f"   Search response format: {list(search_data.keys())}")
                    except json.JSONDecodeError:
                        print(f"   Raw response: {content[:100]}...")
            else:
                print(f"❌ Web search error: {result['error']}")
        else:
            print(f"❌ Web search failed: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Web search error: {e}")

if __name__ == "__main__":
    test_mcp_server()
