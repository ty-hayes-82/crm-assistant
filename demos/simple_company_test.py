#!/usr/bin/env python3
"""
Simple test script to ask questions about companies using the HubSpot MCP server.
This bypasses the complex agent setup and directly calls the MCP tools.
"""

import requests
import json
from typing import Dict, Any

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
        
        # Extract the actual content from MCP response
        content = result["result"]["content"][0]["text"]
        return json.loads(content)
    
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}

def search_company(query: str, limit: int = 5) -> Dict[str, Any]:
    """Search for companies by name or domain."""
    print(f"🔍 Searching for companies matching: '{query}'")
    return call_mcp_tool("search_companies", {"query": query, "limit": limit})

def get_company_report(company_id: str = None, domain: str = None) -> Dict[str, Any]:
    """Generate a comprehensive company report."""
    if company_id:
        print(f"📊 Generating report for company ID: {company_id}")
        return call_mcp_tool("generate_company_report", {"company_id": company_id})
    elif domain:
        print(f"📊 Generating report for domain: {domain}")
        return call_mcp_tool("generate_company_report", {"domain": domain})
    else:
        return {"error": "Either company_id or domain must be provided"}

def ask_about_company(company_name: str):
    """Ask questions about a company - the main function."""
    print(f"\n🏢 Asking about: {company_name}")
    print("=" * 50)
    
    # Step 1: Search for the company
    search_results = search_company(company_name)
    
    if "error" in search_results:
        print(f"❌ Error searching: {search_results['error']}")
        return
    
    if not search_results.get("results"):
        print(f"❌ No companies found matching '{company_name}'")
        return
    
    # Step 2: Show search results
    print(f"✅ Found {len(search_results['results'])} companies:")
    for i, company in enumerate(search_results['results'], 1):
        props = company.get('properties', {})
        print(f"   {i}. {props.get('name', 'Unknown')} - {props.get('domain', 'No domain')}")
        print(f"      Industry: {props.get('industry', 'Unknown')}")
        print(f"      Location: {props.get('city', '')}, {props.get('state', '')}, {props.get('country', '')}")
        print()
    
    # Step 3: Generate detailed report for the first company
    first_company = search_results['results'][0]
    company_id = first_company['id']
    
    print(f"📊 Generating detailed report for: {first_company['properties'].get('name', 'Unknown')}")
    print("-" * 40)
    
    report = get_company_report(company_id=company_id)
    
    if "error" in report:
        print(f"❌ Error generating report: {report['error']}")
        return
    
    # Step 4: Display the comprehensive report
    display_company_report(report)

def display_company_report(report: Dict[str, Any]):
    """Display a formatted company report."""
    
    # Company Overview
    company = report.get('company_overview', {})
    if company:
        props = company.get('properties', {})
        print("🏢 COMPANY OVERVIEW")
        print(f"   Name: {props.get('name', 'Unknown')}")
        print(f"   Domain: {props.get('domain', 'Unknown')}")
        print(f"   Industry: {props.get('industry', 'Unknown')}")
        print(f"   Website: {props.get('website', 'Unknown')}")
        print(f"   Phone: {props.get('phone', 'Unknown')}")
        print(f"   Location: {props.get('city', '')}, {props.get('state', '')}, {props.get('country', '')}")
        print(f"   Description: {props.get('description', 'No description')[:200]}...")
        print()
    
    # Contacts
    contacts = report.get('contacts', {})
    if contacts:
        print(f"👥 ASSOCIATED CONTACTS ({contacts.get('total_count', 0)} total)")
        for contact in contacts.get('contacts', [])[:5]:  # Show first 5
            props = contact.get('properties', {})
            print(f"   • {props.get('firstname', '')} {props.get('lastname', '')} - {props.get('email', '')}")
            print(f"     Title: {props.get('jobtitle', 'Unknown')}")
        if contacts.get('total_count', 0) > 5:
            print(f"   ... and {contacts.get('total_count') - 5} more contacts")
        print()
    
    # Deals
    deals = report.get('deals', {})
    if deals:
        print(f"💰 ASSOCIATED DEALS ({deals.get('total_count', 0)} total)")
        for deal in deals.get('deals', [])[:5]:  # Show first 5
            props = deal.get('properties', {})
            amount = props.get('amount', '0')
            print(f"   • {props.get('dealname', 'Unknown Deal')} - ${amount}")
            print(f"     Stage: {props.get('dealstage', 'Unknown')}")
            print(f"     Close Date: {props.get('closedate', 'Unknown')}")
        if deals.get('total_count', 0) > 5:
            print(f"   ... and {deals.get('total_count') - 5} more deals")
        print()
    
    # Analysis
    analysis = report.get('analysis', {})
    if analysis:
        print("📈 ANALYSIS & INSIGHTS")
        
        # Deal Summary
        deal_summary = analysis.get('deal_summary', {})
        if deal_summary:
            print(f"   Total Deal Value: ${deal_summary.get('total_deal_value', 0):,.2f}")
            print(f"   Open Deals: {deal_summary.get('open_deals_count', 0)}")
            print(f"   Won Deals: {deal_summary.get('won_deals_count', 0)}")
            print(f"   Total Deals: {deal_summary.get('total_deals_count', 0)}")
        
        # Company Profile
        profile = analysis.get('company_profile', {})
        if profile:
            print(f"   Data Completeness: {profile.get('data_completeness', 0):.1f}%")
            print(f"   Has Website: {'✅' if profile.get('has_website') else '❌'}")
            print(f"   Has Phone: {'✅' if profile.get('has_phone') else '❌'}")
            print(f"   Has Industry: {'✅' if profile.get('has_industry') else '❌'}")
        print()
    
    print("✅ Company analysis complete!")

def main():
    """Main function - test the company intelligence."""
    print("🚀 Simple Company Intelligence Test")
    print("=" * 40)
    print("This script directly calls the HubSpot MCP server to ask questions about companies.")
    print()
    
    # Test with a few companies
    test_companies = [
        "Google",
        "Microsoft", 
        "HubSpot"
    ]
    
    print("🔧 Make sure your MCP server is running:")
    print("   python mcp_wrapper/simple_hubspot_server.py")
    print()
    
    # Test server connectivity
    try:
        health_response = requests.get("http://localhost:8081/health")
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"✅ MCP Server Status: {health_data.get('status', 'unknown')}")
            print(f"✅ HubSpot Token: {'Configured' if health_data.get('hubspot_token_configured') else 'Missing'}")
        else:
            print("❌ MCP Server not responding")
            return
    except Exception as e:
        print(f"❌ Cannot connect to MCP server: {e}")
        print("Make sure to start it with: python mcp_wrapper/simple_hubspot_server.py")
        return
    
    print()
    
    # Ask about each test company
    for company in test_companies:
        ask_about_company(company)
        print("\n" + "="*50 + "\n")
    
    print("🎯 WHAT YOU CAN DO:")
    print("   • Modify the test_companies list to ask about other companies")
    print("   • Call ask_about_company('Your Company Name') for specific queries")
    print("   • Use search_company('query') to find companies by name/domain")
    print("   • Use get_company_report(company_id='123') for detailed reports")
    print()
    print("✅ Testing complete! Your HubSpot company intelligence is working!")

if __name__ == "__main__":
    main()
