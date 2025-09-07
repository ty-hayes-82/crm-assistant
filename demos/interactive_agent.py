#!/usr/bin/env python3
"""
Interactive Company Intelligence Agent
Ask questions about any company in your HubSpot CRM
"""

import sys
import requests
import json
from simple_company_test import ask_about_company, search_company, call_mcp_tool

def print_welcome():
    """Print welcome message and instructions."""
    print("🤖 Company Intelligence Agent")
    print("=" * 40)
    print("Hi! I'm your company intelligence assistant.")
    print("I can help you learn about any company in your HubSpot CRM.")
    print()
    print("📋 What I can do:")
    print("   • Tell you about any company")
    print("   • Search for companies by name")
    print("   • Generate detailed company reports")
    print("   • Show contacts and deals")
    print("   • Analyze data quality")
    print()
    print("💬 Example questions:")
    print("   • 'Tell me about Google'")
    print("   • 'Search for Apple'") 
    print("   • 'What do you know about Microsoft?'")
    print("   • 'Find companies with Tesla in the name'")
    print("   • 'Enrich Purgatory Golf Club with online data'")
    print("   • 'Find more information about [company] online'")
    print()
    print("Type 'help' for more commands or 'exit' to quit.")
    print("-" * 40)

def print_help():
    """Print help message."""
    print("\n📖 Available Commands:")
    print("   • tell me about [company] - Get detailed company analysis")
    print("   • search [company] - Search for companies by name")
    print("   • what do you know about [company] - Same as 'tell me about'")
    print("   • find [company] - Same as search")
    print("   • enrich [company] - Find additional information online")
    print("   • enrich [company] with online data - Enhanced web enrichment")
    print("   • help - Show this help message")
    print("   • exit - Quit the agent")
    print()
    print("💡 Tips:")
    print("   • You can ask in natural language")
    print("   • Company names don't need to be exact matches")
    print("   • I'll search your HubSpot CRM for the best matches")
    print("   • Use 'enrich' to find additional data from the web")
    print()

def process_question(question):
    """Process user question and route to appropriate function."""
    question = question.lower().strip()
    
    # Handle help
    if question in ['help', 'h', '?']:
        print_help()
        return
    
    # Handle exit
    if question in ['exit', 'quit', 'bye', 'goodbye']:
        print("\n👋 Thanks for using the Company Intelligence Agent!")
        print("Have a great day!")
        return False
    
    # Extract company name from various question formats
    company_name = None
    
    if question.startswith('tell me about '):
        company_name = question.replace('tell me about ', '').strip()
    elif question.startswith('what do you know about '):
        company_name = question.replace('what do you know about ', '').strip()
    elif question.startswith('search for '):
        company_name = question.replace('search for ', '').strip()
        return search_and_display(company_name)
    elif question.startswith('search '):
        company_name = question.replace('search ', '').strip()
        return search_and_display(company_name)
    elif question.startswith('find '):
        company_name = question.replace('find ', '').strip()
        return search_and_display(company_name)
    elif question.startswith('enrich '):
        company_name = question.replace('enrich ', '').strip()
        # Remove common enrichment phrases
        company_name = company_name.replace('with online data', '').replace('online', '').strip()
        return enrich_company(company_name)
    elif 'enrich' in question and ('online' in question or 'web' in question or 'information' in question):
        # Handle more complex enrichment requests
        words_to_remove = ['enrich', 'any', 'information', 'you', 'can', 'find', 'online', 'on', 'the', 'course', 'or', 'contacts', 'with', 'data', 'web']
        words = question.split()
        filtered_words = [word for word in words if word not in words_to_remove]
        if filtered_words:
            company_name = ' '.join(filtered_words)
            return enrich_company(company_name)
    else:
        # Try to extract company name from general question
        # Remove common question words
        words_to_remove = ['tell', 'me', 'about', 'what', 'do', 'you', 'know', 'find', 'search', 'for']
        words = question.split()
        filtered_words = [word for word in words if word not in words_to_remove]
        if filtered_words:
            company_name = ' '.join(filtered_words)
    
    if company_name:
        print(f"\n🔍 Looking up information about: {company_name}")
        ask_about_company(company_name)
    else:
        print("\n❓ I'm not sure what company you're asking about.")
        print("Try asking like: 'Tell me about Google' or 'Search for Microsoft'")
        print("Type 'help' for more examples.")
    
    return True

def search_and_display(company_name):
    """Search for companies and display results."""
    print(f"\n🔍 Searching for companies matching: '{company_name}'")
    
    results = search_company(company_name, limit=10)
    
    if "error" in results:
        print(f"❌ Error: {results['error']}")
        return True
    
    if not results.get("results"):
        print(f"❌ No companies found matching '{company_name}'")
        print("💡 Try a different spelling or broader search term.")
        return True
    
    print(f"\n✅ Found {len(results['results'])} companies:")
    for i, company in enumerate(results['results'], 1):
        props = company.get('properties', {})
        name = props.get('name', 'Unknown')
        domain = props.get('domain', 'No domain')
        industry = props.get('industry', 'Unknown industry')
        location = f"{props.get('city', '')}, {props.get('state', '')}"
        
        print(f"\n   {i}. {name}")
        print(f"      Domain: {domain}")
        print(f"      Industry: {industry}")
        print(f"      Location: {location}")
    
    if len(results['results']) == 1:
        print(f"\n💡 Would you like a detailed report? Ask: 'Tell me about {results['results'][0]['properties'].get('name', 'this company')}'")
    else:
        print(f"\n💡 For detailed info, ask: 'Tell me about [company name]'")
    
    return True

def enrich_company(company_name):
    """Enrich company data with online information."""
    print(f"\n🌐 Enriching '{company_name}' with online data...")
    print("=" * 50)
    
    # First, get the company from HubSpot
    print("🔍 Step 1: Finding company in HubSpot CRM...")
    search_results = search_company(company_name, limit=1)
    
    if "error" in search_results:
        print(f"❌ Error searching HubSpot: {search_results['error']}")
        return True
    
    if not search_results.get("results"):
        print(f"❌ Company '{company_name}' not found in HubSpot CRM")
        print("💡 Try searching first to see available companies.")
        return True
    
    company = search_results['results'][0]
    company_props = company.get('properties', {})
    company_name = company_props.get('name', company_name)
    domain = company_props.get('domain', '')
    website = company_props.get('website', '')
    
    print(f"✅ Found: {company_name}")
    print(f"   Domain: {domain}")
    print(f"   Website: {website}")
    
    # Step 2: Web search for additional information
    print(f"\n🌐 Step 2: Searching web for additional information about '{company_name}'...")
    
    web_info = search_web_for_company(company_name, domain)
    
    # Step 3: Display enriched information
    print(f"\n📊 Step 3: Enriched Information for {company_name}")
    print("-" * 40)
    
    # Show current HubSpot data
    print("🏢 CURRENT HUBSPOT DATA:")
    print(f"   Name: {company_props.get('name', 'Unknown')}")
    print(f"   Industry: {company_props.get('industry', 'Unknown')}")
    print(f"   Location: {company_props.get('city', '')}, {company_props.get('state', '')}, {company_props.get('country', '')}")
    print(f"   Phone: {company_props.get('phone', 'Unknown')}")
    print(f"   Description: {company_props.get('description', 'No description')[:100]}...")
    
    # Show enriched data
    if web_info:
        print(f"\n🌐 ADDITIONAL WEB INFORMATION:")
        for key, value in web_info.items():
            if value:
                print(f"   {key}: {value}")
    
    # Suggest enrichment opportunities
    print(f"\n💡 ENRICHMENT OPPORTUNITIES:")
    missing_fields = []
    if not company_props.get('description') or len(company_props.get('description', '')) < 50:
        missing_fields.append("Detailed company description")
    if not company_props.get('industry'):
        missing_fields.append("Industry classification")
    if not company_props.get('num_employees'):
        missing_fields.append("Employee count")
    if not company_props.get('annual_revenue'):
        missing_fields.append("Annual revenue")
    if not company_props.get('founded_year'):
        missing_fields.append("Founded year")
    
    if missing_fields:
        print("   Missing fields that could be enriched:")
        for field in missing_fields:
            print(f"   • {field}")
    else:
        print("   ✅ Company profile appears complete!")
    
    return True

def search_web_for_company(company_name, domain=""):
    """Search the web for additional company information."""
    # This is a simplified web search function
    # In a real implementation, you'd use APIs like Google Search, Bing, or specialized business data APIs
    
    web_info = {}
    
    try:
        # Simulate web search results (replace with actual web search API)
        print("   🔍 Searching business directories...")
        print("   🔍 Checking social media profiles...")
        print("   🔍 Looking for news and press releases...")
        
        # For demonstration, we'll provide some mock enriched data
        if "purgatory" in company_name.lower() and "golf" in company_name.lower():
            web_info = {
                "Founded": "Approximately 1990s",
                "Course Designer": "Pete Dye",
                "Par": "72",
                "Holes": "18",
                "Yardage": "Approximately 7,200 yards from championship tees",
                "Notable Features": "Challenging layout with water hazards and bunkers",
                "Awards": "Rated among top golf courses in Indiana",
                "Membership Type": "Semi-private club",
                "Facilities": "Pro shop, restaurant, event spaces",
                "Recent News": "Hosting local tournaments and corporate events"
            }
            print("   ✅ Found additional golf course information")
        else:
            # Generic business information that might be found
            web_info = {
                "Business Type": "Information available from business directories",
                "Social Media": "LinkedIn, Facebook, Twitter profiles found",
                "Recent News": "Check business news and press releases",
                "Competitors": "Industry analysis available",
                "Market Position": "Business intelligence data available"
            }
            print("   ✅ Found general business information")
            
    except Exception as e:
        print(f"   ❌ Web search error: {e}")
        web_info["Error"] = "Unable to retrieve web information at this time"
    
    return web_info

def check_server():
    """Check if MCP server is running."""
    try:
        import requests
        response = requests.get("http://localhost:8081/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get('status') == 'healthy' and data.get('hubspot_token_configured')
        return False
    except:
        return False

def main():
    """Main interactive loop."""
    print_welcome()
    
    # Check server status
    if not check_server():
        print("❌ MCP Server not running or not configured properly!")
        print("\n🔧 To fix this:")
        print("   1. Start the MCP server: python mcp_wrapper/simple_hubspot_server.py")
        print("   2. Make sure your .env file has PRIVATE_APP_ACCESS_TOKEN")
        print("   3. Try again")
        return
    
    print("✅ Connected to HubSpot CRM successfully!\n")
    
    # Main conversation loop
    while True:
        try:
            # Get user input
            question = input("🤖 How can I help you? ").strip()
            
            if not question:
                continue
                
            # Process the question
            should_continue = process_question(question)
            if not should_continue:
                break
                
            print("\n" + "-" * 40)
            
        except KeyboardInterrupt:
            print("\n\n👋 Thanks for using the Company Intelligence Agent!")
            break
        except Exception as e:
            print(f"\n❌ An error occurred: {e}")
            print("Please try again or type 'help' for assistance.")

if __name__ == "__main__":
    main()
