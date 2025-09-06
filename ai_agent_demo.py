#!/usr/bin/env python3
"""
Simple AI Agent Demo for HubSpot MCP Server
Shows basic integration with HubSpot CRM data via the MCP server.
"""

import requests
import json
import os

class HubSpotAgent:
    def __init__(self, mcp_server_url="http://localhost:8081/mcp"):
        self.mcp_server_url = mcp_server_url
        self.request_id = 1
    
    def _make_mcp_request(self, method, params=None):
        """Make a JSON-RPC request to the MCP server"""
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "id": self.request_id,
            "params": params or {}
        }
        self.request_id += 1
        
        try:
            response = requests.post(
                self.mcp_server_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}: {response.text}"}
        except Exception as e:
            return {"error": f"Request failed: {str(e)}"}
    
    def list_available_tools(self):
        """Get list of available HubSpot tools"""
        print("🔍 Getting available HubSpot tools...")
        result = self._make_mcp_request("list_tools")
        
        if "result" in result and "tools" in result["result"]:
            tools = result["result"]["tools"]
            print(f"✅ Found {len(tools)} available tools:")
            for tool in tools:
                print(f"   • {tool['name']}: {tool['description']}")
            return tools
        else:
            print(f"❌ Failed to get tools: {result}")
            return []
    
    def call_tool(self, tool_name, arguments=None):
        """Call a specific HubSpot tool"""
        print(f"🛠️  Calling tool: {tool_name}")
        result = self._make_mcp_request("call_tool", {
            "name": tool_name,
            "arguments": arguments or {}
        })
        
        if "result" in result and "content" in result["result"]:
            content = result["result"]["content"][0]["text"]
            data = json.loads(content)
            return data
        else:
            print(f"❌ Tool call failed: {result}")
            return None
    
    def get_account_summary(self):
        """Get a summary of the HubSpot account"""
        print("\n📊 Getting HubSpot account summary...")
        
        # Get account info
        account_info = self.call_tool("get_account_info")
        if account_info and "error" not in account_info:
            print(f"✅ Account: Portal ID {account_info.get('portalId')}")
            print(f"   Type: {account_info.get('accountType')}")
            print(f"   Currency: {account_info.get('companyCurrency')}")
        
        # Get some contacts
        print("\n👥 Getting recent contacts...")
        contacts = self.call_tool("get_contacts", {"limit": 5})
        if contacts and "results" in contacts:
            print(f"✅ Found {len(contacts['results'])} contacts:")
            for contact in contacts["results"][:3]:  # Show first 3
                props = contact.get("properties", {})
                name = f"{props.get('firstname', '')} {props.get('lastname', '')}".strip()
                email = props.get('email', 'No email')
                print(f"   • {name or 'No name'} ({email})")
        
        # Get some companies  
        print("\n🏢 Getting recent companies...")
        companies = self.call_tool("get_companies", {"limit": 5})
        if companies and "results" in companies:
            print(f"✅ Found {len(companies['results'])} companies:")
            for company in companies["results"][:3]:  # Show first 3
                props = company.get("properties", {})
                name = props.get('name', 'No name')
                domain = props.get('domain', 'No domain')
                print(f"   • {name} ({domain})")
        
        # Get some deals
        print("\n💰 Getting recent deals...")
        deals = self.call_tool("get_deals", {"limit": 5})
        if deals and "results" in deals:
            print(f"✅ Found {len(deals['results'])} deals:")
            for deal in deals["results"][:3]:  # Show first 3
                props = deal.get("properties", {})
                name = props.get('dealname', 'No name')
                amount = props.get('amount', 'No amount')
                stage = props.get('dealstage', 'No stage')
                print(f"   • {name} (${amount}) - {stage}")

def main():
    """Demo the HubSpot AI Agent"""
    print("🤖 Simple HubSpot AI Agent Demo")
    print("=" * 50)
    print("This demo shows basic HubSpot CRM integration.")
    print("For advanced company analysis, use: python company_intelligence_demo.py")
    
    # Create agent
    agent = HubSpotAgent()
    
    # List available tools
    tools = agent.list_available_tools()
    
    if tools:
        print("\n" + "=" * 50)
        # Get account summary
        agent.get_account_summary()
        
        print("\n" + "=" * 50)
        print("🎉 Basic demo completed successfully!")
        print("\n💡 Next steps:")
        print("• Try advanced company analysis: python company_intelligence_demo.py")
        print("• Test company intelligence: python test_company_intelligence.py")
        print("• See production examples: python production_agent_example.py")
    else:
        print("❌ Could not connect to HubSpot MCP server")
        print("💡 Make sure the server is running: python mcp_wrapper/simple_hubspot_server.py")

if __name__ == "__main__":
    main()
