#!/usr/bin/env python3
"""
CRM Assistant - Main AI Agent
Your intelligent CRM assistant that helps with company intelligence and data enrichment
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import requests
import json
from typing import Dict, Any
from .web_search_agent import create_web_search_agent

# MCP server configuration
MCP_URL = "http://localhost:8081/mcp"

class CRMAssistant:
    """Main CRM AI Assistant that helps with company intelligence and enrichment."""
    
    def __init__(self):
        """Initialize the CRM Assistant."""
        self.name = "CRM Assistant"
        self.web_agent = None
        self.setup()
    
    def setup(self):
        """Set up the assistant and check connections."""
        print("🤖 CRM Assistant")
        print("=" * 40)
        print("Hello! I'm your intelligent CRM assistant.")
        print("I can help you with company intelligence, data enrichment, and CRM operations.")
        print()
        
        # Check MCP server connection
        if not self.check_mcp_connection():
            print("❌ Cannot connect to HubSpot. Please start the MCP server first:")
            print("   python mcp_wrapper/simple_hubspot_server.py")
            return False
        
        # Initialize web search agent
        try:
            self.web_agent = create_web_search_agent()
            print("✅ Web search capabilities available")
        except Exception as e:
            print(f"⚠️  Web search limited: {e}")
        
        print("✅ Connected to HubSpot CRM")
        return True
    
    def check_mcp_connection(self) -> bool:
        """Check if MCP server is running and connected to HubSpot."""
        try:
            response = requests.get("http://localhost:8081/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data.get('status') == 'healthy' and data.get('hubspot_token_configured')
            return False
        except:
            return False
    
    def call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
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
            
            content = result["result"]["content"][0]["text"]
            return json.loads(content)
        
        except Exception as e:
            return {"error": f"Request failed: {str(e)}"}
    
    def analyze_request(self, user_input: str) -> Dict[str, Any]:
        """Analyze user request to determine intent and extract entities."""
        input_lower = user_input.lower().strip()
        
        # Determine request type
        request_type = "unknown"
        company_name = ""
        action = ""
        
        # Company intelligence requests
        if any(phrase in input_lower for phrase in ["tell me about", "what do you know about", "analyze", "intelligence"]):
            request_type = "company_intelligence"
            action = "analyze"
            # Extract company name
            for phrase in ["tell me about ", "what do you know about ", "analyze ", "give me intelligence on "]:
                if phrase in input_lower:
                    company_name = user_input.lower().replace(phrase, "").strip()
                    break
        
        # Search requests
        elif any(phrase in input_lower for phrase in ["search", "find", "look for"]):
            request_type = "search"
            action = "search"
            for phrase in ["search for ", "search ", "find ", "look for "]:
                if phrase in input_lower:
                    company_name = user_input.lower().replace(phrase, "").strip()
                    break
        
        # Enrichment requests
        elif any(phrase in input_lower for phrase in ["enrich", "update", "improve", "enhance"]):
            request_type = "enrichment"
            action = "enrich"
            # Extract company name, removing enrichment keywords
            words_to_remove = ["enrich", "update", "improve", "enhance", "with", "data", "information", "online", "web"]
            words = input_lower.split()
            filtered_words = [word for word in words if word not in words_to_remove]
            company_name = " ".join(filtered_words).strip()
        
        # Help requests
        elif input_lower in ["help", "h", "?", "what can you do", "commands"]:
            request_type = "help"
            action = "help"
        
        # Exit requests
        elif input_lower in ["exit", "quit", "bye", "goodbye"]:
            request_type = "exit"
            action = "exit"
        
        return {
            "type": request_type,
            "action": action,
            "company_name": company_name,
            "original_input": user_input
        }
    
    def handle_company_intelligence(self, company_name: str) -> str:
        """Handle company intelligence requests."""
        print(f"\n🏢 Company Intelligence: {company_name}")
        print("-" * 40)
        
        # Search for the company
        search_result = self.call_mcp_tool("search_companies", {
            "query": company_name,
            "limit": 1
        })
        
        if "error" in search_result or not search_result.get("results"):
            return f"❌ Company '{company_name}' not found in your HubSpot CRM. Try searching with a different name or check if the company exists."
        
        company = search_result["results"][0]
        company_id = company["id"]
        
        # Generate comprehensive report
        report = self.call_mcp_tool("generate_company_report", {
            "company_id": company_id
        })
        
        if "error" in report:
            return f"❌ Error generating report: {report['error']}"
        
        # Format the response
        return self.format_company_intelligence(company, report)
    
    def format_company_intelligence(self, company: Dict, report: Dict) -> str:
        """Format company intelligence into a readable response."""
        props = company.get("properties", {})
        
        response = f"📊 **{props.get('name', 'Unknown Company')}** Analysis\n\n"
        
        # Basic info
        response += "🏢 **Company Overview:**\n"
        response += f"   • Industry: {props.get('industry', 'Not specified')}\n"
        response += f"   • Location: {props.get('city', '')}, {props.get('state', '')}, {props.get('country', '')}\n"
        response += f"   • Website: {props.get('website', 'Not available')}\n"
        response += f"   • Phone: {props.get('phone', 'Not available')}\n"
        
        if props.get('description'):
            response += f"   • Description: {props['description'][:200]}...\n"
        
        # Contacts
        contacts = report.get("contacts", {})
        if contacts and contacts.get("contacts"):
            response += f"\n👥 **Associated Contacts** ({contacts.get('total_count', 0)} total):\n"
            for contact in contacts["contacts"][:3]:
                contact_props = contact.get("properties", {})
                name = f"{contact_props.get('firstname', '')} {contact_props.get('lastname', '')}".strip()
                email = contact_props.get('email', '')
                title = contact_props.get('jobtitle', '')
                response += f"   • {name} - {email}\n"
                if title:
                    response += f"     Title: {title}\n"
        
        # Deals
        deals = report.get("deals", {})
        if deals and deals.get("deals"):
            response += f"\n💰 **Associated Deals** ({deals.get('total_count', 0)} total):\n"
            for deal in deals["deals"][:3]:
                deal_props = deal.get("properties", {})
                name = deal_props.get('dealname', 'Unknown Deal')
                amount = deal_props.get('amount', '0')
                stage = deal_props.get('dealstage', 'Unknown')
                response += f"   • {name} - ${amount}\n"
                response += f"     Stage: {stage}\n"
        
        # Analysis
        analysis = report.get("analysis", {})
        if analysis:
            response += "\n📈 **Key Insights:**\n"
            
            deal_summary = analysis.get("deal_summary", {})
            if deal_summary:
                total_value = deal_summary.get("total_deal_value", 0)
                open_deals = deal_summary.get("open_deals_count", 0)
                response += f"   • Total Deal Value: ${total_value:,.2f}\n"
                response += f"   • Open Deals: {open_deals}\n"
            
            profile = analysis.get("company_profile", {})
            if profile:
                completeness = profile.get("data_completeness", 0)
                response += f"   • Data Completeness: {completeness:.1f}%\n"
        
        response += f"\n🎯 **Next Steps:**\n"
        response += f"   • Review company profile for accuracy\n"
        response += f"   • Consider enriching missing data fields\n"
        response += f"   • Engage with key contacts for opportunities\n"
        
        return response
    
    def handle_search(self, company_name: str) -> str:
        """Handle company search requests."""
        print(f"\n🔍 Searching for: {company_name}")
        
        search_result = self.call_mcp_tool("search_companies", {
            "query": company_name,
            "limit": 5
        })
        
        if "error" in search_result:
            return f"❌ Search error: {search_result['error']}"
        
        results = search_result.get("results", [])
        if not results:
            return f"❌ No companies found matching '{company_name}'. Try a different search term."
        
        response = f"🔍 **Search Results for '{company_name}'** ({len(results)} found)\n\n"
        
        for i, company in enumerate(results, 1):
            props = company.get("properties", {})
            name = props.get('name', 'Unknown')
            domain = props.get('domain', 'No domain')
            industry = props.get('industry', 'Unknown industry')
            location = f"{props.get('city', '')}, {props.get('state', '')}"
            
            response += f"**{i}. {name}**\n"
            response += f"   • Domain: {domain}\n"
            response += f"   • Industry: {industry}\n"
            response += f"   • Location: {location}\n\n"
        
        response += "💡 **To get detailed information, ask:** 'Tell me about [company name]'\n"
        
        return response
    
    def handle_enrichment(self, company_name: str) -> str:
        """Handle company enrichment requests."""
        print(f"\n🌐 Enriching: {company_name}")
        
        # Find the company first
        search_result = self.call_mcp_tool("search_companies", {
            "query": company_name,
            "limit": 1
        })
        
        if "error" in search_result or not search_result.get("results"):
            return f"❌ Company '{company_name}' not found. Please search for it first to see available companies."
        
        company = search_result["results"][0]
        company_id = company["id"]
        props = company.get("properties", {})
        
        # Analyze what needs enrichment
        missing_fields = []
        if not props.get("description") or len(props.get("description", "")) < 50:
            missing_fields.append("description")
        if not props.get("domain"):
            missing_fields.append("domain/website")
        if not props.get("industry"):
            missing_fields.append("industry")
        
        if not missing_fields:
            return f"✅ {props.get('name')} appears to have comprehensive data already!"
        
        # Perform enrichment
        updates = {}
        
        # Add industry for golf companies
        if not props.get("industry") and "golf" in company_name.lower():
            updates["industry"] = "LEISURE_TRAVEL_TOURISM"
        
        # Add basic description if missing
        if not props.get("description"):
            industry = props.get("industry", "business")
            location = f"{props.get('city', '')}, {props.get('state', '')}"
            desc = f"{props.get('name')} is a {industry.lower().replace('_', ' ')} company"
            if location.strip() != ",":
                desc += f" located in {location}"
            desc += ". This company profile would benefit from additional detailed information about services and operations."
            updates["description"] = desc
        
        # Web search for domain
        if self.web_agent and not props.get("domain"):
            web_results = self.web_agent.comprehensive_company_search(
                company_name, 
                f"{props.get('city', '')}, {props.get('state', '')}"
            )
            if web_results.get("domain"):
                updates["domain"] = web_results["domain"]
                updates["website"] = f"https://{web_results['domain']}"
        
        # Apply updates
        if updates:
            result = self.call_mcp_tool("update_company", {
                "company_id": company_id,
                "properties": updates
            })
            
            if "error" in result:
                return f"❌ Enrichment failed: {result['error']}"
            else:
                response = f"✅ **{props.get('name')} Enriched Successfully!**\n\n"
                response += f"Updated {len(updates)} fields:\n"
                for field, value in updates.items():
                    response += f"   • {field}: {str(value)[:80]}{'...' if len(str(value)) > 80 else ''}\n"
                response += f"\n🎯 Check your HubSpot record to see the improvements!"
                return response
        else:
            return f"ℹ️  No enrichment opportunities found for {props.get('name')}"
    
    def show_help(self) -> str:
        """Show help information."""
        return """
🤖 **CRM Assistant Help**

**📋 What I can help you with:**

**🏢 Company Intelligence:**
   • "Tell me about [company name]"
   • "What do you know about [company]?"
   • "Analyze [company name]"
   • "Give me intelligence on [company]"

**🔍 Company Search:**
   • "Search for [company name]"
   • "Find [company name]" 
   • "Look for companies with [keyword]"

**🌐 Data Enrichment:**
   • "Enrich [company name]"
   • "Update [company name] with web data"
   • "Improve [company name] profile"
   • "Find missing information for [company]"

**💡 Examples:**
   • "Tell me about Google"
   • "Search for golf companies"
   • "Enrich Austin Golf Club"
   • "What do you know about Microsoft?"

**🔧 Commands:**
   • "help" - Show this help
   • "exit" - Quit the assistant

I'll analyze your request and provide comprehensive company intelligence, search results, or perform data enrichment as needed!
        """
    
    def process_request(self, user_input: str) -> str:
        """Process user request and return response."""
        if not user_input.strip():
            return "Please ask me something! Type 'help' to see what I can do."
        
        # Analyze the request
        analysis = self.analyze_request(user_input)
        
        # Route to appropriate handler
        if analysis["type"] == "help":
            return self.show_help()
        elif analysis["type"] == "exit":
            return "exit"
        elif analysis["type"] == "company_intelligence":
            if analysis["company_name"]:
                return self.handle_company_intelligence(analysis["company_name"])
            else:
                return "❓ Which company would you like to know about? Try: 'Tell me about [company name]'"
        elif analysis["type"] == "search":
            if analysis["company_name"]:
                return self.handle_search(analysis["company_name"])
            else:
                return "❓ What company should I search for? Try: 'Search for [company name]'"
        elif analysis["type"] == "enrichment":
            if analysis["company_name"]:
                return self.handle_enrichment(analysis["company_name"])
            else:
                return "❓ Which company should I enrich? Try: 'Enrich [company name]'"
        else:
            return f"❓ I'm not sure how to help with that. Try asking about a specific company or type 'help' for examples."
    
    def run(self):
        """Run the interactive CRM assistant."""
        if not self.check_mcp_connection():
            return
        
        print("\n💬 **What can I help you with?**")
        print("Ask me about any company, search for companies, or request data enrichment!")
        print("Type 'help' for examples or 'exit' to quit.")
        print("-" * 40)
        
        while True:
            try:
                user_input = input("\n🤖 How can I help you? ").strip()
                
                if not user_input:
                    continue
                
                response = self.process_request(user_input)
                
                if response == "exit":
                    print("\n👋 Thank you for using CRM Assistant! Have a great day!")
                    break
                
                print(f"\n{response}")
                print("\n" + "-" * 40)
                
            except KeyboardInterrupt:
                print("\n\n👋 Thank you for using CRM Assistant!")
                break
            except Exception as e:
                print(f"\n❌ An error occurred: {e}")
                print("Please try again or type 'help' for assistance.")

def main():
    """Main entry point."""
    assistant = CRMAssistant()
    assistant.run()

if __name__ == "__main__":
    main()
