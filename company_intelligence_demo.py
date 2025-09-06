#!/usr/bin/env python3
"""
Company Intelligence Demo

This script demonstrates how to use the enhanced CRM system to ask questions 
about companies and get comprehensive analysis including all contacts and deals.

Usage:
    python company_intelligence_demo.py

Make sure you have your HubSpot access token configured in the .env file.
"""

import asyncio
import json
import os
from datetime import datetime

# Import the company intelligence agent
from crm_agent.agents.specialized.company_intelligence_agent import create_company_intelligence_agent
from crm_agent.core.state_models import CRMSessionState

async def demo_company_analysis():
    """Demonstrate comprehensive company analysis capabilities."""
    
    print("🚀 Company Intelligence Demo")
    print("=" * 50)
    
    # Create the company intelligence agent
    agent = create_company_intelligence_agent()
    
    # Initialize session state
    session_state = CRMSessionState()
    
    # Example company queries
    example_queries = [
        "Tell me everything about HubSpot",
        "What do we know about Salesforce?",
        "Find information about microsoft.com",
        "Analyze our relationship with Apple Inc"
    ]
    
    print("\n📋 Example Company Analysis Queries:")
    for i, query in enumerate(example_queries, 1):
        print(f"{i}. {query}")
    
    print("\n" + "=" * 50)
    
    # Interactive mode
    while True:
        print("\n🔍 Company Intelligence Assistant")
        print("Enter a company name, domain, or question about a company.")
        print("Type 'quit' to exit, 'examples' to see sample queries.")
        
        user_input = input("\n❓ Your question: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("👋 Goodbye!")
            break
            
        if user_input.lower() == 'examples':
            print("\n📋 Example queries:")
            for query in example_queries:
                print(f"  • {query}")
            continue
            
        if not user_input:
            continue
        
        print(f"\n🔎 Analyzing: {user_input}")
        print("⏳ Please wait while I gather comprehensive company information...")
        
        try:
            # In a real implementation, this would use the agent to process the query
            # For demo purposes, we'll show the expected workflow
            
            print("\n📊 Company Analysis Workflow:")
            print("  1. 🔍 Searching HubSpot for company...")
            print("  2. 📋 Retrieving company details...")
            print("  3. 👥 Gathering associated contacts...")
            print("  4. 💼 Analyzing deals and opportunities...")
            print("  5. 🌐 Enriching with external data...")
            print("  6. 📈 Generating insights and recommendations...")
            
            # Simulate the analysis result
            print(f"\n" + "=" * 60)
            print(f"# 🏢 Company Analysis: {user_input}")
            print("=" * 60)
            
            print("""
## 📋 Executive Summary
Based on HubSpot data and external research, here's what we know about this company:

## 🏗️ Company Profile
• Industry: [Retrieved from HubSpot]
• Location: [City, State, Country]
• Size: [Employee count/Revenue range]
• Website: [Company domain]
• Description: [Company description]

## 👥 Key Contacts (X total)
• [Contact Name] - [Job Title] - [Email] - [Phone]
• [Last interaction date and notes]

## 💼 Deal Intelligence
• Active Deals: [Number] worth $[Total Value]
• Deal History: [Won/Lost summary]
• Pipeline Health: [Assessment]
• Average Deal Size: $[Amount]

## 📊 Data Quality & Completeness
• Profile Completeness: [Percentage]%
• Missing Fields: [List of gaps]
• Last Updated: [Date]
• Data Sources: HubSpot CRM, External Research

## 🎯 Strategic Recommendations
• [Specific recommendations based on analysis]
• [Next steps for engagement]
• [Opportunities identified]

## 🔍 Additional Research Opportunities
• [Suggestions for further data enrichment]
""")
            
        except Exception as e:
            print(f"❌ Error during analysis: {str(e)}")
            print("💡 Please check your HubSpot configuration and try again.")


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
        asyncio.run(demo_company_analysis())
    
    if choice in ['2', '3']:
        demo_mcp_server()
    
    print("\n✅ Demo completed!")
    print("💡 To use this system:")
    print("  1. Configure your HubSpot access token in .env")
    print("  2. Run: python mcp_wrapper/simple_hubspot_server.py")
    print("  3. Use the MCP tools to analyze companies")
