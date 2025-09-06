#!/usr/bin/env python3
"""
Production AI Agent Template for HubSpot Integration
Use this as a starting point for your internal AI agent team.
"""

import requests
import json
from datetime import datetime

class HubSpotProductionAgent:
    def __init__(self, agent_name, mcp_server_url="http://localhost:8081/mcp"):
        self.agent_name = agent_name
        self.mcp_server_url = mcp_server_url
        self.request_id = 1
    
    def _call_hubspot_tool(self, tool_name, arguments=None):
        """Call a HubSpot tool via the MCP server"""
        payload = {
            "jsonrpc": "2.0",
            "method": "call_tool",
            "params": {
                "name": tool_name,
                "arguments": arguments or {}
            },
            "id": self.request_id
        }
        self.request_id += 1
        
        try:
            response = requests.post(self.mcp_server_url, json=payload)
            if response.status_code == 200:
                result = response.json()
                if "result" in result:
                    content = result["result"]["content"][0]["text"]
                    return json.loads(content)
            return None
        except Exception as e:
            print(f"❌ {self.agent_name}: Error calling {tool_name}: {str(e)}")
            return None

    def analyze_recent_deals(self):
        """Example: Analyze recent deals for insights"""
        print(f"🤖 {self.agent_name}: Analyzing recent deals...")
        
        deals = self._call_hubspot_tool("get_deals", {"limit": 20})
        if not deals or "results" not in deals:
            return "No deals found"
        
        total_value = 0
        deal_stages = {}
        
        for deal in deals["results"]:
            props = deal.get("properties", {})
            
            # Calculate total value
            amount = props.get("amount")
            if amount:
                try:
                    total_value += float(amount)
                except:
                    pass
            
            # Count stages
            stage = props.get("dealstage", "unknown")
            deal_stages[stage] = deal_stages.get(stage, 0) + 1
        
        analysis = {
            "total_deals": len(deals["results"]),
            "total_value": total_value,
            "average_deal_size": total_value / len(deals["results"]) if deals["results"] else 0,
            "deals_by_stage": deal_stages,
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"📊 Analysis complete: ${total_value:,.2f} across {len(deals['results'])} deals")
        return analysis

    def find_high_value_contacts(self, min_company_employees=100):
        """Example: Find contacts from large companies"""
        print(f"🤖 {self.agent_name}: Finding high-value contacts...")
        
        companies = self._call_hubspot_tool("get_companies", {"limit": 50})
        if not companies or "results" not in companies:
            return []
        
        high_value_companies = []
        for company in companies["results"]:
            props = company.get("properties", {})
            employees = props.get("numberofemployees")
            
            if employees:
                try:
                    if int(employees) >= min_company_employees:
                        high_value_companies.append({
                            "name": props.get("name", "Unknown"),
                            "domain": props.get("domain", ""),
                            "employees": employees,
                            "id": company["id"]
                        })
                except:
                    pass
        
        print(f"🎯 Found {len(high_value_companies)} high-value companies")
        return high_value_companies

    def generate_daily_report(self):
        """Example: Generate a daily CRM report"""
        print(f"🤖 {self.agent_name}: Generating daily report...")
        
        # Get account info
        account = self._call_hubspot_tool("get_account_info")
        
        # Analyze deals
        deal_analysis = self.analyze_recent_deals()
        
        # Find high-value contacts
        high_value = self.find_high_value_contacts()
        
        report = {
            "report_date": datetime.now().strftime("%Y-%m-%d"),
            "agent": self.agent_name,
            "account_id": account.get("portalId") if account else "Unknown",
            "deal_analysis": deal_analysis,
            "high_value_companies": len(high_value),
            "recommendations": [
                "Focus on deals in early stages",
                f"Prioritize outreach to {len(high_value)} large companies",
                "Review stalled deals for follow-up opportunities"
            ]
        }
        
        print("📋 Daily report generated successfully!")
        return report

# Example usage
def main():
    """Example of how to use the production agent"""
    
    # Create different agents for different purposes
    sales_agent = HubSpotProductionAgent("SalesAnalyzer")
    marketing_agent = HubSpotProductionAgent("MarketingIntel")
    
    print("🏢 Starting AI Agent Team...")
    print("=" * 60)
    
    # Sales agent analyzes deals
    deal_analysis = sales_agent.analyze_recent_deals()
    
    print("\n" + "=" * 60)
    
    # Marketing agent finds high-value prospects
    prospects = marketing_agent.find_high_value_contacts()
    
    print("\n" + "=" * 60)
    
    # Generate daily report
    report = sales_agent.generate_daily_report()
    
    print("\n🎉 AI Agent Team execution complete!")
    print("\nYour agents can now:")
    print("• Run automated analysis on HubSpot data")
    print("• Generate insights and recommendations") 
    print("• Identify high-value prospects")
    print("• Create daily/weekly reports")
    print("• Scale to handle multiple workflows simultaneously")

if __name__ == "__main__":
    main()
