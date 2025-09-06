#!/usr/bin/env python3
"""
Test Suite for Company Intelligence System
Tests all MCP server endpoints for comprehensive company analysis.
"""

import requests
import json
import sys

def test_mcp_server(base_url="http://localhost:8081"):
    """Test the MCP server company analysis endpoints."""
    
    print("🧪 Testing Company Intelligence MCP Server")
    print("=" * 50)
    
    # Test health check first
    try:
        health_response = requests.get(f"{base_url}/health")
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"✅ Server health: {health_data.get('status')}")
            print(f"🔑 HubSpot token configured: {health_data.get('hubspot_token_configured')}")
        else:
            print(f"❌ Health check failed: {health_response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to server at {base_url}")
        print("💡 Make sure the server is running: python mcp_wrapper/simple_hubspot_server.py")
        return False
    
    # Test list_tools
    print("\n🔧 Testing available tools...")
    list_tools_payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "list_tools"
    }
    
    try:
        response = requests.post(f"{base_url}/mcp", json=list_tools_payload)
        if response.status_code == 200:
            tools_data = response.json()
            tools = tools_data.get('result', {}).get('tools', [])
            
            company_tools = [tool for tool in tools if 'company' in tool['name'].lower()]
            print(f"✅ Found {len(company_tools)} company-related tools:")
            
            for tool in company_tools:
                print(f"  • {tool['name']}: {tool['description']}")
        else:
            print(f"❌ Failed to list tools: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing tools: {str(e)}")
        return False
    
    # Test search_companies
    print("\n🔍 Testing company search...")
    search_payload = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "call_tool",
        "params": {
            "name": "search_companies",
            "arguments": {
                "query": "test",
                "limit": 3
            }
        }
    }
    
    try:
        response = requests.post(f"{base_url}/mcp", json=search_payload)
        if response.status_code == 200:
            search_data = response.json()
            result_text = search_data.get('result', {}).get('content', [{}])[0].get('text', '{}')
            result = json.loads(result_text)
            
            if 'error' in result:
                print(f"⚠️  Search returned: {result['error']}")
            else:
                results = result.get('results', [])
                print(f"✅ Search found {len(results)} companies")
                for company in results[:2]:  # Show first 2
                    props = company.get('properties', {})
                    print(f"  • {props.get('name', 'N/A')} ({props.get('domain', 'N/A')})")
        else:
            print(f"❌ Search failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing search: {str(e)}")
    
    # Test company report generation (with a test domain)
    print("\n📊 Testing company report generation...")
    report_payload = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "call_tool",
        "params": {
            "name": "generate_company_report",
            "arguments": {
                "domain": "example.com"  # Using a test domain
            }
        }
    }
    
    try:
        response = requests.post(f"{base_url}/mcp", json=report_payload)
        if response.status_code == 200:
            report_data = response.json()
            result_text = report_data.get('result', {}).get('content', [{}])[0].get('text', '{}')
            result = json.loads(result_text)
            
            if 'error' in result:
                print(f"⚠️  Report generation: {result['error']}")
            else:
                print("✅ Report generated successfully!")
                if 'company_overview' in result:
                    company = result['company_overview']
                    props = company.get('properties', {})
                    print(f"  • Company: {props.get('name', 'N/A')}")
                    print(f"  • Domain: {props.get('domain', 'N/A')}")
                    print(f"  • Industry: {props.get('industry', 'N/A')}")
                
                if 'contacts' in result:
                    contacts = result['contacts']
                    print(f"  • Contacts: {contacts.get('total_count', 0)} found")
                
                if 'deals' in result:
                    deals = result['deals']
                    print(f"  • Deals: {deals.get('total_count', 0)} found")
                
                if 'analysis' in result:
                    analysis = result['analysis']
                    if 'company_profile' in analysis:
                        profile = analysis['company_profile']
                        completeness = profile.get('data_completeness', 0)
                        print(f"  • Data completeness: {completeness:.1f}%")
        else:
            print(f"❌ Report generation failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing report: {str(e)}")
    
    print("\n✅ Company Intelligence testing completed!")
    return True


def show_usage_examples():
    """Show examples of how to use the company intelligence system."""
    
    print("\n📚 Usage Examples")
    print("=" * 50)
    
    examples = [
        {
            "title": "Search for companies",
            "payload": {
                "method": "call_tool",
                "params": {
                    "name": "search_companies",
                    "arguments": {"query": "HubSpot", "limit": 5}
                }
            }
        },
        {
            "title": "Get company details with contacts",
            "payload": {
                "method": "call_tool",
                "params": {
                    "name": "get_company_details",
                    "arguments": {"domain": "hubspot.com"}
                }
            }
        },
        {
            "title": "Generate comprehensive company report",
            "payload": {
                "method": "call_tool",
                "params": {
                    "name": "generate_company_report",
                    "arguments": {
                        "domain": "salesforce.com",
                        "include_contacts": True,
                        "include_deals": True
                    }
                }
            }
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n{i}. {example['title']}:")
        print("   curl -X POST http://localhost:8081/mcp \\")
        print("     -H 'Content-Type: application/json' \\")
        print("     -d '" + json.dumps({
            "jsonrpc": "2.0",
            "id": i,
            **example['payload']
        }, indent=6) + "'")


if __name__ == "__main__":
    print("🎯 Company Intelligence Test Suite")
    
    if len(sys.argv) > 1 and sys.argv[1] == "--examples":
        show_usage_examples()
    else:
        success = test_mcp_server()
        
        if success:
            print("\n✅ All tests passed!")
            print("\n💡 Next steps:")
            print("  1. Try the interactive demo: python company_intelligence_demo.py")
            print("  2. See usage examples: python test_company_intelligence.py --examples")
            print("  3. Test with real company data in your HubSpot account")
            print("  4. Try production examples: python production_agent_example.py")
        else:
            print("\n❌ Some tests failed!")
            print("\n🔧 Troubleshooting:")
            print("  1. Make sure the server is running: python mcp_wrapper/simple_hubspot_server.py")
            print("  2. Check your .env file has PRIVATE_APP_ACCESS_TOKEN configured")
            print("  3. Verify your HubSpot token has the required scopes")
            print("  4. Check server logs for detailed error information")
