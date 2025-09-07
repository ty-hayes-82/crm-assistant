#!/usr/bin/env python3
"""
Web Search Agent - Non-AI agent that performs actual web searches
Specialized in finding contact information through real web search APIs
"""

import requests
import json
import re
from typing import Dict, Any, List, Optional
from urllib.parse import quote_plus
import time

class WebSearchAgent:
    """
    Non-AI web search agent that performs actual web searches to find contact information.
    Uses real search APIs rather than LLM simulation.
    """
    
    def __init__(self):
        """Initialize the web search agent."""
        self.name = "WebSearchAgent"
        self.search_engines = {
            "duckduckgo": "https://api.duckduckgo.com/",
            "serper": "https://google.serper.dev/search",  # Requires API key
            "serpapi": "https://serpapi.com/search"        # Requires API key
        }
        print("🔍 Web Search Agent initialized")
        print("   • DuckDuckGo: Available (no API key required)")
        print("   • Serper/SerpAPI: Available if API keys configured")
    
    def search_duckduckgo(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Search using DuckDuckGo API (free, no API key required)."""
        try:
            # DuckDuckGo Instant Answer API
            params = {
                'q': query,
                'format': 'json',
                'no_html': '1',
                'skip_disambig': '1'
            }
            
            response = requests.get(self.search_engines["duckduckgo"], params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            # Extract relevant results
            if data.get('AbstractText'):
                results.append({
                    'title': data.get('AbstractSource', 'DuckDuckGo'),
                    'snippet': data.get('AbstractText', ''),
                    'url': data.get('AbstractURL', '')
                })
            
            # Add related topics
            for topic in data.get('RelatedTopics', [])[:max_results-1]:
                if isinstance(topic, dict) and 'Text' in topic:
                    results.append({
                        'title': topic.get('FirstURL', '').split('/')[-1] if topic.get('FirstURL') else 'Related',
                        'snippet': topic.get('Text', ''),
                        'url': topic.get('FirstURL', '')
                    })
            
            return results
            
        except Exception as e:
            print(f"   ❌ DuckDuckGo search error: {e}")
            return []
    
    def search_company_contacts(self, company_name: str, domain: str = "") -> Dict[str, Any]:
        """Search for company contact information."""
        print(f"🔍 Searching web for {company_name} contact information...")
        
        # Build comprehensive search queries
        search_queries = [
            f'"{company_name}" contact email phone',
            f'"{company_name}" staff directory',
            f'"{company_name}" "contact us"',
            f'site:{domain} contact' if domain else f'"{company_name}" website contact'
        ]
        
        all_results = []
        contact_info = {
            'emails': [],
            'phones': [],
            'addresses': [],
            'social_media': [],
            'key_contacts': []
        }
        
        for query in search_queries:
            print(f"   🔍 Searching: {query}")
            results = self.search_duckduckgo(query, max_results=3)
            all_results.extend(results)
            time.sleep(1)  # Be respectful to the API
        
        # Extract contact information from search results
        contact_info = self.extract_contact_info(all_results, company_name, domain)
        
        return contact_info
    
    def extract_contact_info(self, search_results: List[Dict[str, Any]], 
                           company_name: str, domain: str = "") -> Dict[str, Any]:
        """Extract contact information from search results."""
        contact_info = {
            'emails': set(),
            'phones': set(), 
            'addresses': [],
            'social_media': set(),
            'key_contacts': [],
            'website': domain
        }
        
        # Email regex patterns
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        phone_pattern = r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b'
        
        for result in search_results:
            text = f"{result.get('title', '')} {result.get('snippet', '')}"
            
            # Extract emails
            emails = re.findall(email_pattern, text)
            for email in emails:
                if domain and domain in email:
                    contact_info['emails'].add(email)
                elif not domain and company_name.lower().replace(' ', '') in email.lower():
                    contact_info['emails'].add(email)
            
            # Extract phone numbers
            phones = re.findall(phone_pattern, text)
            for phone_match in phones:
                phone = f"({phone_match[0]}) {phone_match[1]}-{phone_match[2]}"
                contact_info['phones'].add(phone)
            
            # Look for social media
            if 'linkedin.com' in result.get('url', ''):
                contact_info['social_media'].add(result['url'])
            if 'facebook.com' in result.get('url', ''):
                contact_info['social_media'].add(result['url'])
            if 'twitter.com' in result.get('url', '') or 'x.com' in result.get('url', ''):
                contact_info['social_media'].add(result['url'])
        
        # Convert sets to lists for JSON serialization
        contact_info['emails'] = list(contact_info['emails'])
        contact_info['phones'] = list(contact_info['phones'])
        contact_info['social_media'] = list(contact_info['social_media'])
        
        return contact_info
    
    def find_company_domain(self, company_name: str, location: str = "") -> str:
        """Search for company's official domain/website."""
        print(f"🌐 Searching for {company_name} official website...")
        
        search_query = f'"{company_name}" official website'
        if location:
            search_query += f' {location}'
        
        results = self.search_duckduckgo(search_query, max_results=5)
        
        # Look for official domains in results
        domain_patterns = [
            r'https?://(?:www\.)?([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
            r'(?:www\.)?([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
        ]
        
        potential_domains = set()
        
        for result in results:
            text = f"{result.get('url', '')} {result.get('snippet', '')}"
            
            for pattern in domain_patterns:
                domains = re.findall(pattern, text)
                for domain in domains:
                    # Filter out common non-company domains
                    if not any(exclude in domain.lower() for exclude in 
                             ['google.com', 'facebook.com', 'linkedin.com', 'twitter.com', 
                              'yelp.com', 'wikipedia.org', 'maps.google']):
                        potential_domains.add(domain.lower())
        
        # Return the most likely domain
        if potential_domains:
            # Prefer .com domains
            com_domains = [d for d in potential_domains if d.endswith('.com')]
            if com_domains:
                return com_domains[0]
            return list(potential_domains)[0]
        
        return ""
    
    def research_competitors(self, company_name: str, industry: str = "") -> List[str]:
        """Search for company competitors."""
        print(f"🏆 Searching for {company_name} competitors...")
        
        search_queries = [
            f'"{company_name}" competitors',
            f'{company_name} vs alternatives',
            f'{industry} companies like {company_name}' if industry else f'companies like {company_name}'
        ]
        
        competitors = set()
        
        for query in search_queries:
            results = self.search_duckduckgo(query, max_results=3)
            
            for result in results:
                text = result.get('snippet', '').lower()
                
                # Look for competitor mentions
                competitor_indicators = ['vs', 'versus', 'competitor', 'alternative', 'similar to']
                if any(indicator in text for indicator in competitor_indicators):
                    # Extract potential company names (basic extraction)
                    words = text.split()
                    for i, word in enumerate(words):
                        if word in competitor_indicators and i < len(words) - 1:
                            potential_competitor = words[i + 1].strip('.,!?')
                            if len(potential_competitor) > 2:
                                competitors.add(potential_competitor.title())
            
            time.sleep(1)
        
        return list(competitors)[:5]  # Return top 5
    
    def comprehensive_company_search(self, company_name: str, location: str = "") -> Dict[str, Any]:
        """Perform comprehensive web search for company information."""
        print(f"\n🔍 Comprehensive web search for: {company_name}")
        print("=" * 50)
        
        results = {}
        
        # 1. Find domain
        domain = self.find_company_domain(company_name, location)
        if domain:
            results['domain'] = domain
            print(f"   ✅ Domain found: {domain}")
        else:
            print("   ❌ Domain not found")
        
        # 2. Find contact information
        contact_info = self.search_company_contacts(company_name, domain)
        if contact_info['emails'] or contact_info['phones']:
            results['contact_info'] = contact_info
            print(f"   ✅ Found {len(contact_info['emails'])} emails, {len(contact_info['phones'])} phones")
        else:
            print("   ❌ No contact information found")
        
        # 3. Find competitors
        competitors = self.research_competitors(company_name)
        if competitors:
            results['competitors'] = competitors
            print(f"   ✅ Found {len(competitors)} potential competitors")
        
        return results

def create_web_search_agent():
    """Factory function to create the web search agent."""
    return WebSearchAgent()

def main():
    """Demo the web search agent."""
    print("🔍 Web Search Agent Demo")
    print("=" * 40)
    print("This agent performs REAL web searches to find contact information")
    print()
    
    # Create the web search agent
    search_agent = WebSearchAgent()
    
    # Test with Austin Golf Club
    company_name = "Austin Golf Club"
    location = "Spicewood TX"
    
    results = search_agent.comprehensive_company_search(company_name, location)
    
    print(f"\n📊 Search Results for {company_name}:")
    print("=" * 40)
    
    if results.get('domain'):
        print(f"🌐 Website: {results['domain']}")
    
    if results.get('contact_info'):
        contact = results['contact_info']
        if contact['emails']:
            print(f"📧 Emails: {', '.join(contact['emails'])}")
        if contact['phones']:
            print(f"📞 Phones: {', '.join(contact['phones'])}")
        if contact['social_media']:
            print(f"📱 Social: {', '.join(contact['social_media'])}")
    
    if results.get('competitors'):
        print(f"🏆 Competitors: {', '.join(results['competitors'])}")
    
    print("\n💡 This agent can be integrated with the field enrichment system")
    print("   to provide real web search capabilities for contact discovery!")

if __name__ == "__main__":
    main()
