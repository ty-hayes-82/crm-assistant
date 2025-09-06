#!/usr/bin/env python3
"""
Company Intelligence Demo

This script demonstrates how to use the enhanced CRM system to ask questions 
about companies and get comprehensive analysis including all contacts and deals.

Usage:
    python company_intelligence_demo.py

Make sure you have your HubSpot access token configured in the .env file.
"""

import requests
import json
import os

def demo_company_analysis_interactive():
    """Interactive demo of company analysis using MCP server."""
    
    print("🚀 Interactive Company Intelligence Demo")
    print("=" * 50)
    
    mcp_url = "http://localhost:8081/mcp"
    
    # Example company queries
    example_queries = [
        "HubSpot",
        "Salesforce", 
        "microsoft.com",
        "Apple Inc"
    ]
    
    print("\n📋 Example Company Searches:")
    for i, query in enumerate(example_queries, 1):
        print(f"{i}. {query}")
    
    print("\n" + "=" * 50)
    
    # Interactive mode
    while True:
        print("\n🔍 Company Intelligence Assistant")
        print("Enter a company name or domain to analyze.")
        print("Type 'quit' to exit, 'examples' to see sample queries, 'test' for a quick test.")
        
        user_input = input("\n❓ Company to analyze: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("👋 Goodbye!")
            break
            
        if user_input.lower() == 'examples':
            print("\n📋 Example searches:")
            for query in example_queries:
                print(f"  • {query}")
            continue
            
        if user_input.lower() == 'test':
            user_input = "test"  # Use test company
            
        if not user_input:
            continue
        
        print(f"\n🔎 Analyzing: {user_input}")
        print("⏳ Searching HubSpot and generating report...")
        
        try:
            # Call the generate_company_report tool
            payload = {
                "jsonrpc": "2.0",
                "method": "call_tool",
                "params": {
                    "name": "generate_company_report",
                    "arguments": {"domain": user_input} if "." in user_input else {"company_id": user_input}
                },
                "id": 1
            }
            
            response = requests.post(mcp_url, json=payload)
            if response.status_code == 200:
                result = response.json()
                if "result" in result and "content" in result["result"]:
                    content = result["result"]["content"][0]["text"]
                    data = json.loads(content)
                    
                    if "error" in data:
                        print(f"⚠️  {data['error']}")
                        print("💡 Try searching first with: search_companies")
                    else:
                        print_company_report(data)
                else:
                    print(f"❌ Unexpected response: {result}")
            else:
                print(f"❌ Server error: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print("❌ Cannot connect to MCP server")
            print("💡 Make sure the server is running: python mcp_wrapper/simple_hubspot_server.py")
        except Exception as e:
            print(f"❌ Error during analysis: {str(e)}")

def print_company_report(data):
    """Print a formatted company report."""
    print(f"\n" + "=" * 60)
    
    if "company_overview" in data:
        company = data["company_overview"]
        props = company.get("properties", {})
        
        print(f"# 🏢 Company Analysis: {props.get('name', 'Unknown Company')}")
        print("=" * 60)
        
        print(f"\n## 🏗️ Company Profile")
        print(f"• Name: {props.get('name', 'N/A')}")
        print(f"• Domain: {props.get('domain', 'N/A')}")
        print(f"• Industry: {props.get('industry', 'N/A')}")
        print(f"• Location: {props.get('city', 'N/A')}, {props.get('state', 'N/A')}")
        print(f"• Website: {props.get('website', 'N/A')}")
    
    if "contacts" in data:
        contacts = data["contacts"]
        print(f"\n## 👥 Associated Contacts ({contacts.get('total_count', 0)} total)")
        for contact in contacts.get("contacts", [])[:5]:  # Show first 5
            contact_props = contact.get("properties", {})
            name = f"{contact_props.get('firstname', '')} {contact_props.get('lastname', '')}".strip()
            email = contact_props.get('email', 'No email')
            title = contact_props.get('jobtitle', 'No title')
            print(f"• {name or 'No name'} - {title} - {email}")
    
    if "deals" in data:
        deals = data["deals"]
        print(f"\n## 💼 Associated Deals ({deals.get('total_count', 0)} total)")
        for deal in deals.get("deals", [])[:5]:  # Show first 5
            deal_props = deal.get("properties", {})
            name = deal_props.get('dealname', 'No name')
            amount = deal_props.get('amount', '0')
            stage = deal_props.get('dealstage', 'No stage')
            print(f"• {name} - ${amount} - {stage}")
    
    if "analysis" in data:
        analysis = data["analysis"]
        if "company_profile" in analysis:
            profile = analysis["company_profile"]
            completeness = profile.get("data_completeness", 0)
            print(f"\n## 📊 Data Quality")
            print(f"• Profile Completeness: {completeness:.1f}%")
            print(f"• Has Website: {'✅' if profile.get('has_website') else '❌'}")
            print(f"• Has Industry: {'✅' if profile.get('has_industry') else '❌'}")
        
        if "deal_summary" in analysis:
            deal_summary = analysis["deal_summary"]
            print(f"\n## 💰 Deal Summary")
            print(f"• Total Deal Value: ${deal_summary.get('total_deal_value', 0):,.2f}")
            print(f"• Open Deals: {deal_summary.get('open_deals_count', 0)}")
            print(f"• Won Deals: {deal_summary.get('won_deals_count', 0)}")
    
    print(f"\n" + "=" * 60)


def demo_mcp_server():
    """Demonstrate the MCP server functionality."""
    
    print("\n🔧 MCP Server Integration Demo")
    print("=" * 50)
    
    print("""
The enhanced MCP server now provides these company analysis tools:

🔍 SEARCH TOOLS:
  • search_companies - Find companies by name or domain
  • get_company_details - Get comprehensive company info + contacts
  • generate_company_report - Full analysis with insights

📊 ANALYSIS FEATURES:
  • Company profile with all HubSpot fields
  • Associated contacts with roles and contact info
  • Deal history and pipeline analysis
  • Data quality assessment
  • Strategic recommendations

🚀 USAGE EXAMPLES:

1. Search for a company:
   POST /mcp with:
   {
     "method": "call_tool",
     "params": {
       "name": "search_companies",
       "arguments": {"query": "HubSpot", "limit": 5}
     }
   }

2. Get detailed company analysis:
   POST /mcp with:
   {
     "method": "call_tool", 
     "params": {
       "name": "generate_company_report",
       "arguments": {"domain": "hubspot.com"}
     }
   }

3. Get company with all contacts:
   POST /mcp with:
   {
     "method": "call_tool",
     "params": {
       "name": "get_company_details",
       "arguments": {"company_id": "12345"}
     }
   }
""")


if __name__ == "__main__":
    print("🎯 Company Intelligence System Demo")
    print("This system helps you ask questions about companies and get comprehensive answers.")
    
    # Check if HubSpot token is configured
    env_file = ".env"
    if not os.path.exists(env_file):
        print(f"\n⚠️  Warning: {env_file} file not found.")
        print("Create a .env file with your HubSpot access token:")
        print("PRIVATE_APP_ACCESS_TOKEN=your_hubspot_token_here")
    
    print("\n📋 Choose demo mode:")
    print("1. Interactive Company Analysis (requires HubSpot setup)")
    print("2. MCP Server Integration Overview")
    print("3. Both")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice in ['1', '3']:
        print("\n🚀 Starting Interactive Company Analysis Demo...")
        demo_company_analysis_interactive()
    
    if choice in ['2', '3']:
        demo_mcp_server()
    
    print("\n✅ Demo completed!")
    print("💡 To use this system:")
    print("  1. Configure your HubSpot access token in .env")
    print("  2. Run: python mcp_wrapper/simple_hubspot_server.py")
    print("  3. Use the MCP tools to analyze companies")
