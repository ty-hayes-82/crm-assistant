"""CRM FastMCP Server for multi-agent CRM enrichment and cleanup.

This server provides tools for:
- HubSpot CRM integration via official MCP server
- Web search and content extraction
- LinkedIn/company data retrieval
- Email verification
- Slack notifications and approvals
"""

import os
import json
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

import httpx
from fastmcp import FastMCP
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class CRMFastMCPServer:
    """FastMCP server for CRM enrichment tools."""
    
    def __init__(self):
        self.mcp = FastMCP("CRM Tool Server")
        self.hubspot_mcp_url = os.getenv("HUBSPOT_MCP_URL", "https://mcp.hubspot.com/")
        self.hubspot_access_token = os.getenv("HUBSPOT_ACCESS_TOKEN")
        self.hubspot_client_id = os.getenv("HUBSPOT_CLIENT_ID")
        self.search_api_key = os.getenv("SEARCH_API_KEY")
        self.slack_bot_token = os.getenv("SLACK_BOT_TOKEN")
        self.email_verify_api_key = os.getenv("EMAIL_VERIFY_API_KEY")
        
        # Initialize HTTP client for external requests
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        self._register_tools()
    
    def _register_tools(self):
        """Register all CRM tools."""
        self._register_hubspot_tools()
        self._register_web_tools()
        self._register_company_data_tools()
        self._register_email_tools()
        self._register_slack_tools()
    
    def _register_hubspot_tools(self):
        """Register HubSpot integration tools (proxy to official MCP server)."""
        
        @self.mcp.tool()
        async def query_hubspot_crm(query: str, object_type: str = "contacts") -> str:
            """Natural language query to HubSpot official MCP server.
            
            Args:
                query: Natural language query (e.g., "find all contacts from ACME Corp")
                object_type: CRM object type (contacts, companies, deals, tickets, etc.)
            
            Returns:
                JSON string with query results
            """
            if not self.hubspot_access_token:
                return json.dumps({"error": "HubSpot access token not configured"})
            
            try:
                headers = {
                    "Authorization": f"Bearer {self.hubspot_access_token}",
                    "X-Client-ID": self.hubspot_client_id,
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "query": query,
                    "object_type": object_type
                }
                
                response = await self.http_client.post(
                    f"{self.hubspot_mcp_url}/query",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                
                return json.dumps(response.json())
                
            except Exception as e:
                logger.error(f"HubSpot query error: {e}")
                return json.dumps({"error": str(e)})
        
        @self.mcp.tool()
        async def get_hubspot_contact(contact_id: str = None, email: str = None) -> str:
            """Get contact details via HubSpot MCP server.
            
            Args:
                contact_id: HubSpot contact ID
                email: Contact email address
            
            Returns:
                JSON string with contact details
            """
            if not contact_id and not email:
                return json.dumps({"error": "Either contact_id or email must be provided"})
            
            if not self.hubspot_access_token:
                return json.dumps({"error": "HubSpot access token not configured"})
            
            try:
                headers = {
                    "Authorization": f"Bearer {self.hubspot_access_token}",
                    "X-Client-ID": self.hubspot_client_id
                }
                
                # Use MCP server's get_contact tool
                if contact_id:
                    endpoint = f"{self.hubspot_mcp_url}/tools/get_contact"
                    params = {"contact_id": contact_id}
                else:
                    endpoint = f"{self.hubspot_mcp_url}/tools/search_contacts"
                    params = {"email": email}
                
                response = await self.http_client.get(
                    endpoint,
                    headers=headers,
                    params=params
                )
                response.raise_for_status()
                
                return json.dumps(response.json())
                
            except Exception as e:
                logger.error(f"HubSpot contact lookup error: {e}")
                return json.dumps({"error": str(e)})
        
        @self.mcp.tool()
        async def get_hubspot_company(company_id: str = None, domain: str = None) -> str:
            """Get company details via HubSpot MCP server.
            
            Args:
                company_id: HubSpot company ID
                domain: Company domain name
            
            Returns:
                JSON string with company details
            """
            if not company_id and not domain:
                return json.dumps({"error": "Either company_id or domain must be provided"})
            
            if not self.hubspot_access_token:
                return json.dumps({"error": "HubSpot access token not configured"})
            
            try:
                headers = {
                    "Authorization": f"Bearer {self.hubspot_access_token}",
                    "X-Client-ID": self.hubspot_client_id
                }
                
                if company_id:
                    endpoint = f"{self.hubspot_mcp_url}/tools/get_company"
                    params = {"company_id": company_id}
                else:
                    endpoint = f"{self.hubspot_mcp_url}/tools/search_companies"
                    params = {"domain": domain}
                
                response = await self.http_client.get(
                    endpoint,
                    headers=headers,
                    params=params
                )
                response.raise_for_status()
                
                return json.dumps(response.json())
                
            except Exception as e:
                logger.error(f"HubSpot company lookup error: {e}")
                return json.dumps({"error": str(e)})
    
    def _register_web_tools(self):
        """Register web search and content extraction tools."""
        
        @self.mcp.tool()
        async def web_search(query: str, num_results: int = 10) -> str:
            """General web search using SERP API.
            
            Args:
                query: Search query
                num_results: Number of results to return (default: 10)
            
            Returns:
                JSON string with search results
            """
            if not self.search_api_key:
                return json.dumps({"error": "Search API key not configured"})
            
            try:
                # Example using SerpAPI (adjust for your provider)
                params = {
                    "q": query,
                    "api_key": self.search_api_key,
                    "num": num_results,
                    "format": "json"
                }
                
                response = await self.http_client.get(
                    "https://serpapi.com/search",
                    params=params
                )
                response.raise_for_status()
                
                results = response.json()
                
                # Extract relevant information
                organic_results = results.get("organic_results", [])
                formatted_results = []
                
                for result in organic_results:
                    formatted_results.append({
                        "title": result.get("title"),
                        "url": result.get("link"),
                        "snippet": result.get("snippet"),
                        "position": result.get("position")
                    })
                
                return json.dumps({
                    "query": query,
                    "results": formatted_results,
                    "total_results": len(formatted_results)
                })
                
            except Exception as e:
                logger.error(f"Web search error: {e}")
                return json.dumps({"error": str(e)})
        
        @self.mcp.tool()
        async def fetch_url(url: str) -> str:
            """Fetch and extract content from a URL.
            
            Args:
                url: URL to fetch
            
            Returns:
                JSON string with extracted content
            """
            try:
                response = await self.http_client.get(url)
                response.raise_for_status()
                
                # Basic content extraction (could be enhanced with BeautifulSoup)
                content = response.text
                
                # Extract basic metadata
                title = ""
                if "<title>" in content:
                    title_start = content.find("<title>") + 7
                    title_end = content.find("</title>", title_start)
                    if title_end > title_start:
                        title = content[title_start:title_end].strip()
                
                return json.dumps({
                    "url": url,
                    "title": title,
                    "content": content[:5000],  # Limit content size
                    "content_length": len(content),
                    "status_code": response.status_code
                })
                
            except Exception as e:
                logger.error(f"URL fetch error for {url}: {e}")
                return json.dumps({"error": str(e), "url": url})
    
    def _register_company_data_tools(self):
        """Register company data enrichment tools."""
        
        @self.mcp.tool()
        async def linkedin_company_lookup(name: str = None, domain: str = None) -> str:
            """Lookup company metadata from LinkedIn or similar provider.
            
            Args:
                name: Company name
                domain: Company domain
            
            Returns:
                JSON string with company metadata
            """
            # Placeholder - implement based on available LinkedIn API access
            # This would require LinkedIn API credentials and proper authentication
            
            if not name and not domain:
                return json.dumps({"error": "Either name or domain must be provided"})
            
            # For now, return a mock response indicating the feature needs implementation
            return json.dumps({
                "message": "LinkedIn company lookup not yet implemented",
                "suggestion": "Use web_search with 'site:linkedin.com/company' for manual lookup",
                "name": name,
                "domain": domain
            })
        
        @self.mcp.tool()
        async def get_company_metadata(domain: str) -> str:
            """Get company metadata from various sources.
            
            Args:
                domain: Company domain
            
            Returns:
                JSON string with aggregated company data
            """
            try:
                # Combine multiple sources of company data
                results = {
                    "domain": domain,
                    "sources": [],
                    "metadata": {}
                }
                
                # 1. Basic web search for company info
                search_query = f"site:{domain} OR \"{domain}\" company about"
                web_results = await web_search(search_query, 5)
                web_data = json.loads(web_results)
                
                if not web_data.get("error"):
                    results["sources"].append("web_search")
                    results["metadata"]["web_results"] = web_data["results"]
                
                # 2. Try to get basic domain info (could be enhanced with whois, etc.)
                try:
                    domain_response = await self.http_client.get(f"https://{domain}")
                    if domain_response.status_code == 200:
                        results["sources"].append("domain_check")
                        results["metadata"]["domain_accessible"] = True
                        
                        # Extract title from homepage
                        content = domain_response.text
                        if "<title>" in content:
                            title_start = content.find("<title>") + 7
                            title_end = content.find("</title>", title_start)
                            if title_end > title_start:
                                results["metadata"]["homepage_title"] = content[title_start:title_end].strip()
                except:
                    results["metadata"]["domain_accessible"] = False
                
                return json.dumps(results)
                
            except Exception as e:
                logger.error(f"Company metadata lookup error for {domain}: {e}")
                return json.dumps({"error": str(e), "domain": domain})
    
    def _register_email_tools(self):
        """Register email verification tools."""
        
        @self.mcp.tool()
        async def verify_email(email: str) -> str:
            """Verify email deliverability and risk assessment.
            
            Args:
                email: Email address to verify
            
            Returns:
                JSON string with verification results
            """
            if not self.email_verify_api_key:
                return json.dumps({
                    "error": "Email verification API key not configured",
                    "email": email,
                    "suggestion": "Configure EMAIL_VERIFY_API_KEY environment variable"
                })
            
            try:
                # Example using a hypothetical email verification service
                # Adjust based on your chosen provider (e.g., ZeroBounce, EmailHunter, etc.)
                
                params = {
                    "email": email,
                    "api_key": self.email_verify_api_key
                }
                
                # Placeholder URL - replace with actual service
                response = await self.http_client.get(
                    "https://api.emailverification.service/verify",
                    params=params
                )
                response.raise_for_status()
                
                result = response.json()
                
                return json.dumps({
                    "email": email,
                    "valid": result.get("valid", False),
                    "deliverable": result.get("deliverable", "unknown"),
                    "risk": result.get("risk", "unknown"),
                    "provider": result.get("provider"),
                    "catch_all": result.get("catch_all", False),
                    "verified_at": datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Email verification error for {email}: {e}")
                return json.dumps({
                    "error": str(e),
                    "email": email,
                    "verified_at": datetime.now().isoformat()
                })
    
    def _register_slack_tools(self):
        """Register Slack integration tools."""
        
        @self.mcp.tool()
        async def notify_slack(message: str, channel: str = None) -> str:
            """Send a Slack notification to the configured channel.
            
            Args:
                message: Message to send
                channel: Slack channel (optional, uses default if not provided)
            
            Returns:
                JSON string with send status
            """
            if not self.slack_bot_token:
                return json.dumps({
                    "error": "Slack bot token not configured",
                    "suggestion": "Configure SLACK_BOT_TOKEN environment variable"
                })
            
            try:
                from slack_sdk.web.async_client import AsyncWebClient
                
                slack_client = AsyncWebClient(token=self.slack_bot_token)
                
                response = await slack_client.chat_postMessage(
                    channel=channel or "#crm-assistant",
                    text=message
                )
                
                return json.dumps({
                    "success": True,
                    "channel": response["channel"],
                    "timestamp": response["ts"],
                    "message": message
                })
                
            except Exception as e:
                logger.error(f"Slack notification error: {e}")
                return json.dumps({"error": str(e), "message": message})
        
        @self.mcp.tool()
        async def await_human_approval(
            proposed_changes: List[Dict[str, Any]], 
            context: str = "CRM Updates"
        ) -> str:
            """Post to Slack and await approval decision.
            
            Args:
                proposed_changes: List of proposed changes to approve
                context: Context description for the approval request
            
            Returns:
                JSON string with approval results (approved changes)
            """
            if not self.slack_bot_token:
                return json.dumps({
                    "error": "Slack bot token not configured",
                    "approved_changes": []  # Fail safe - no changes approved
                })
            
            try:
                # Format changes for human review
                changes_text = f"*{context} - Approval Required*\n\n"
                for i, change in enumerate(proposed_changes):
                    changes_text += f"{i+1}. {change.get('description', 'Update')}\n"
                    changes_text += f"   Field: {change.get('field')}\n"
                    changes_text += f"   Current: {change.get('current_value')}\n"
                    changes_text += f"   Proposed: {change.get('proposed_value')}\n"
                    changes_text += f"   Confidence: {change.get('confidence', 'N/A')}\n\n"
                
                changes_text += "React with ✅ to approve all, ❌ to reject all, or reply with specific change numbers to approve."
                
                # Send to Slack
                await self.notify_slack(changes_text)
                
                # For now, return a placeholder response
                # In a real implementation, this would wait for user interaction
                return json.dumps({
                    "status": "pending_approval",
                    "message": "Approval request sent to Slack",
                    "approved_changes": [],  # Would be populated based on user response
                    "total_proposed": len(proposed_changes)
                })
                
            except Exception as e:
                logger.error(f"Approval request error: {e}")
                return json.dumps({
                    "error": str(e),
                    "approved_changes": []  # Fail safe
                })
    
    async def close(self):
        """Close the HTTP client."""
        await self.http_client.aclose()


# Create server instance
server = CRMFastMCPServer()

if __name__ == "__main__":
    import uvicorn
    
    # Run the MCP server
    uvicorn.run(server.mcp.app, host="0.0.0.0", port=8001)
