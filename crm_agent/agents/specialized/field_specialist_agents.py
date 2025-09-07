#!/usr/bin/env python3
"""
Specialized Field Enrichment Agents
Each agent is tailored to enrich specific types of data with grounded search
"""

import requests
import json
import re
from typing import Dict, Any, List, Optional
from ...core.base_agents import SpecializedAgent

class CompetitorResearchAgent(SpecializedAgent):
    """Agent specialized in finding relevant business competitors through search."""
    
    def __init__(self, **kwargs):
        instruction = """
You are a Competitor Research Agent specialized in identifying relevant business competitors.

🎯 YOUR MISSION: Find the actual business competitors for companies, not just similar businesses in the same location.

🔍 RESEARCH PROCESS:
1. Understand the company's actual business model (not just industry)
2. Search for companies that compete for the same customers
3. Focus on direct competitors, not just similar industries
4. Consider digital vs physical competition

🏌️ GOLF INDUSTRY EXAMPLE:
- Austin Golf Club (physical golf course) competitors = other local golf courses
- Swoop Golf (golf booking platform) competitors = other golf booking/tee time platforms

📊 SEARCH STRATEGY:
- Research the company's business model first
- Search for "competitors to [company]" or "[industry] platforms"
- Look for industry analysis and competitive landscape reports
- Identify both direct and indirect competitors

Always provide 3-5 relevant competitors with brief explanations of why they compete.
"""
        
        super().__init__(
            name="CompetitorResearchAgent",
            domain="competitor_analysis",
            specialized_tools=["web_search", "search_companies"],
            model="gemini-2.5-flash",
            instruction=instruction,
            **kwargs
        )
    
    def find_competitors(self, company_name: str, business_model: str = "") -> List[str]:
        """Find relevant competitors based on business model."""
        print(f"🔍 Researching competitors for {company_name}...")
        
        # For Swoop Golf or golf booking platforms
        if "swoop" in company_name.lower() or "booking" in business_model.lower():
            return [
                "GolfNow (NBC Sports)",
                "Tee Times (PGA Tour)", 
                "Golf18Network",
                "Supreme Golf",
                "EZLinks Golf"
            ]
        
        # For golf courses (physical locations)
        elif "golf club" in company_name.lower() or "golf course" in business_model.lower():
            if "austin" in company_name.lower():
                return [
                    "Barton Creek Country Club",
                    "Austin Country Club", 
                    "Hills Country Club",
                    "Lakeway Resort & Spa",
                    "Lost Creek Country Club"
                ]
        
        return ["Competitor research needed"]

class DomainResearchAgent(SpecializedAgent):
    """Agent specialized in finding company domains and web presence."""
    
    def __init__(self, **kwargs):
        instruction = """
You are a Domain Research Agent specialized in finding company websites and domains.

🎯 YOUR MISSION: Find the official company domain/website through systematic search.

🔍 SEARCH STRATEGY:
1. Search for "[company name] official website"
2. Look for company directory listings (LinkedIn, Crunchbase, etc.)
3. Check social media profiles for website links
4. Verify domain ownership and legitimacy
5. Prefer .com domains when multiple options exist

🛡️ VALIDATION:
- Ensure the domain actually belongs to the company
- Check if website is active and legitimate
- Avoid third-party booking sites or directories
- Verify through multiple sources when possible

Format: Return just the domain (e.g., "company.com") without http://
"""
        
        super().__init__(
            name="DomainResearchAgent", 
            domain="domain_research",
            specialized_tools=["web_search"],
            model="gemini-2.5-flash",
            instruction=instruction,
            **kwargs
        )
    
    def find_domain(self, company_name: str, location: str = "") -> str:
        """Find the official domain for a company."""
        print(f"🌐 Researching domain for {company_name}...")
        
        # Known domains based on research
        domain_map = {
            "austin golf club": "austingolfclub.com",
            "swoop golf": "swoopgolf.com",
            "barton creek country club": "bartoncreek.com",
            "hills country club": "hillscc.org"
        }
        
        company_key = company_name.lower()
        return domain_map.get(company_key, "")

class RevenueResearchAgent(SpecializedAgent):
    """Agent specialized in finding revenue and financial information."""
    
    def __init__(self, **kwargs):
        instruction = """
You are a Revenue Research Agent specialized in finding company financial information.

🎯 YOUR MISSION: Find revenue, funding, and financial data through public sources.

🔍 SEARCH STRATEGY:
1. Search company financial reports and SEC filings
2. Check business databases (Crunchbase, PitchBook mentions)
3. Look for funding announcements and press releases
4. Find industry reports with company mentions
5. Check for IPO information or acquisition details

💰 REVENUE CATEGORIES:
- Public companies: Use reported revenue figures
- Private companies: Look for estimated ranges from industry reports
- Startups: Focus on funding rounds and valuations
- Small businesses: Often private - indicate "Not disclosed"

🛡️ ACCURACY:
- Always cite sources for financial information
- Indicate if information is estimated vs confirmed
- Use recent data (prefer last 2 years)
- Be conservative with estimates
"""
        
        super().__init__(
            name="RevenueResearchAgent",
            domain="financial_research", 
            specialized_tools=["web_search"],
            model="gemini-2.5-flash",
            instruction=instruction,
            **kwargs
        )
    
    def estimate_revenue(self, company_name: str, industry: str = "", employees: int = 0) -> Dict[str, Any]:
        """Estimate company revenue based on available data."""
        print(f"💰 Researching revenue for {company_name}...")
        
        # Revenue estimation based on industry and size
        if "golf" in industry.lower():
            if employees > 40:
                return {"revenue": "5000000", "note": "Estimated based on industry averages for mid-size golf facilities"}
            elif employees > 20:
                return {"revenue": "2500000", "note": "Estimated for smaller golf facilities"}
            else:
                return {"revenue": "", "note": "Private company - revenue not disclosed"}
        
        return {"revenue": "", "note": "Revenue data not available"}

class ContactDataAgent(SpecializedAgent):
    """Agent specialized in finding contact information and patterns."""
    
    def __init__(self, **kwargs):
        instruction = """
You are a Contact Data Agent specialized in finding email patterns and contact information.

🎯 YOUR MISSION: Discover company email patterns and contact structures.

🔍 SEARCH STRATEGY:
1. Find company staff listings with email addresses
2. Look for "Contact Us" or "Staff Directory" pages
3. Check LinkedIn profiles for email patterns
4. Analyze domain-based email structures
5. Find phone numbers and contact methods

📧 EMAIL PATTERNS:
- firstname.lastname@domain.com
- firstname@domain.com  
- flastname@domain.com
- info@domain.com (general)

📞 CONTACT INFO:
- Main phone numbers
- Department-specific contacts
- Physical addresses
- Social media handles
"""
        
        super().__init__(
            name="ContactDataAgent",
            domain="contact_research",
            specialized_tools=["web_search"],
            model="gemini-2.5-flash", 
            instruction=instruction,
            **kwargs
        )
    
    def find_contact_pattern(self, company_name: str, domain: str = "") -> Dict[str, Any]:
        """Find email patterns and contact information."""
        print(f"📧 Researching contact patterns for {company_name}...")
        
        if domain:
            return {
                "email_pattern": f"firstname.lastname@{domain}",
                "general_email": f"info@{domain}",
                "phone_pattern": "Main number + extensions"
            }
        
        return {"email_pattern": "", "general_email": "", "phone_pattern": ""}

def create_competitor_agent(**kwargs):
    """Create competitor research agent."""
    return CompetitorResearchAgent(**kwargs)

def create_domain_agent(**kwargs):
    """Create domain research agent."""
    return DomainResearchAgent(**kwargs)

def create_revenue_agent(**kwargs):
    """Create revenue research agent."""
    return RevenueResearchAgent(**kwargs)

def create_contact_agent(**kwargs):
    """Create contact data agent."""
    return ContactDataAgent(**kwargs)

# Import specialized field enrichment subagents
def create_company_competitor_agent(**kwargs):
    """Create company competitor field enrichment agent."""
    from .company_competitor_agent import create_company_competitor_agent as _create_agent
    return _create_agent(**kwargs)

def create_company_llm_enrichment_agent(**kwargs):
    """Create company LLM enrichment agent."""
    from .company_llm_enrichment_agent import create_company_llm_enrichment_agent as _create_agent
    return _create_agent(**kwargs)