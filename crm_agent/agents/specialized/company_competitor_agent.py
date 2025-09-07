#!/usr/bin/env python3
"""
Company Competitor Field Enrichment Agent

Specialized subagent for enriching the 'Competitor' field by analyzing company websites
to detect mentions of specific competitors (Jonas, Club Essentials, etc.) on their homepage.
"""

import requests
import json
import re
import time
from typing import Dict, Any, List, Optional, ClassVar
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import logging

from ...core.base_agents import SpecializedAgent

logger = logging.getLogger(__name__)


class CompanyCompetitorAgent(SpecializedAgent):
    """Agent specialized in detecting competitors by scraping company websites."""
    
    # Known competitors to detect (based on field profile data)
    KNOWN_COMPETITORS: ClassVar[Dict[str, str]] = {
        "jonas": "Jonas",
        "club essentials": "Club Essentials", 
        "clubessentials": "Club Essentials",
        "arcis": "Arcis",
        "foretees": "ForeTees",
        "callus": "Callus",
        "pacesetter": "Pacesetter",
        "club app": "Club App",
        "in-house app": "In-House App"
    }
    
    def __init__(self, **kwargs):
        instruction = """
You are a Company Competitor Field Enrichment Agent specialized in detecting competitors 
by analyzing company websites.

🎯 YOUR MISSION: 
Scrape company homepages to find mentions of specific competitors (Jonas, Club Essentials, 
etc.) and update the Competitor field with accurate information.

🔍 DETECTION PROCESS:
1. Get the company's website URL from existing data
2. Scrape the homepage content 
3. Search for mentions of known competitors
4. Look for technology/software mentions in context
5. Return the detected competitor or "Unknown" if none found

🏌️ GOLF INDUSTRY CONTEXT:
- Jonas: Golf management software
- Club Essentials: Club management platform
- Arcis: Golf course management
- ForeTees: Tee time booking system
- Pacesetter: Golf POS/management system

🔍 SEARCH PATTERNS:
- Direct mentions: "powered by Jonas", "using Club Essentials"
- Technology credits: footer mentions, "built with", "managed by"
- Navigation/login hints: "Jonas login", "Club Essentials portal"
- Meta tags and hidden content

⚡ EFFICIENCY:
- Focus on homepage only (fastest detection)
- Use multiple detection methods
- Handle website errors gracefully
- Return "Unknown" if no clear detection

🛡️ VALIDATION:
- Ensure detected competitor is from known list
- Avoid false positives from generic mentions
- Prefer explicit technology/software context
- Log confidence level of detection
"""
        
        super().__init__(
            name="CompanyCompetitorAgent",
            domain="company_competitor_enrichment",
            specialized_tools=["web_search", "get_company_details"],
            model="gemini-2.5-flash",
            instruction=instruction,
            **kwargs
        )
        
        # Initialize instance variables using object.__setattr__ to bypass Pydantic validation
        object.__setattr__(self, 'session', requests.Session())
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
    
    def enrich_competitor_field(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main method to enrich the competitor field for a company.
        
        Args:
            company_data: Company data including properties
            
        Returns:
            Dict with enrichment result
        """
        properties = company_data.get('properties', {})
        company_name = properties.get('name', 'Unknown Company')
        current_competitor = properties.get('competitor', '').strip()
        website_url = properties.get('website', '') or properties.get('domain', '')
        
        logger.info(f"🔍 Analyzing competitor for {company_name}")
        
        # Skip if already has specific competitor (not Unknown/empty)
        if current_competitor and current_competitor.lower() not in ['unknown', 'not sure', '']:
            return {
                'status': 'skipped',
                'reason': f'Already has competitor: {current_competitor}',
                'current_value': current_competitor,
                'new_value': current_competitor
            }
        
        # Need website URL to proceed
        if not website_url:
            return {
                'status': 'failed',
                'reason': 'No website URL available',
                'current_value': current_competitor,
                'new_value': 'Unknown'
            }
        
        # Scrape website and detect competitor
        detected_competitor = self._scrape_and_detect_competitor(website_url, company_name)
        
        if detected_competitor and detected_competitor != current_competitor:
            return {
                'status': 'enriched',
                'reason': f'Detected competitor from website analysis',
                'current_value': current_competitor or 'Unknown',
                'new_value': detected_competitor,
                'confidence': 'high' if detected_competitor != 'Unknown' else 'low',
                'source': 'website_scraping'
            }
        else:
            return {
                'status': 'no_change',
                'reason': 'No competitor detected or same as current',
                'current_value': current_competitor or 'Unknown',
                'new_value': detected_competitor or 'Unknown'
            }
    
    def _scrape_and_detect_competitor(self, website_url: str, company_name: str) -> Optional[str]:
        """
        Scrape website homepage and detect competitor mentions.
        
        Args:
            website_url: URL to scrape
            company_name: Company name for context
            
        Returns:
            Detected competitor name or None
        """
        try:
            # Normalize URL
            if not website_url.startswith(('http://', 'https://')):
                website_url = f'https://{website_url}'
            
            logger.info(f"   🌐 Scraping: {website_url}")
            
            # Request homepage with timeout
            response = self.session.get(website_url, timeout=10, allow_redirects=True)
            response.raise_for_status()
            
            # Parse HTML content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract text content for analysis
            page_text = self._extract_page_text(soup)
            
            # Detect competitor from content
            competitor = self._detect_competitor_from_text(page_text, soup)
            
            if competitor:
                logger.info(f"   ✅ Detected competitor: {competitor}")
                return competitor
            else:
                logger.info(f"   ❓ No specific competitor detected")
                return "Unknown"
                
        except requests.exceptions.Timeout:
            logger.warning(f"   ⏰ Timeout accessing {website_url}")
            return "Unknown"
        except requests.exceptions.RequestException as e:
            logger.warning(f"   ❌ Error accessing {website_url}: {e}")
            return "Unknown"
        except Exception as e:
            logger.error(f"   💥 Unexpected error scraping {website_url}: {e}")
            return "Unknown"
    
    def _extract_page_text(self, soup: BeautifulSoup) -> str:
        """Extract relevant text content from page for analysis."""
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text content
        text = soup.get_text()
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text.lower()
    
    def _detect_competitor_from_text(self, page_text: str, soup: BeautifulSoup) -> Optional[str]:
        """
        Detect competitor from page text and HTML elements.
        
        Args:
            page_text: Cleaned page text (lowercase)
            soup: BeautifulSoup object for additional analysis
            
        Returns:
            Detected competitor name or None
        """
        # Method 1: Direct text mentions with context
        for competitor_key, competitor_name in self.KNOWN_COMPETITORS.items():
            # Look for contextual mentions
            context_patterns = [
                f"powered by {competitor_key}",
                f"using {competitor_key}",
                f"built with {competitor_key}",
                f"managed by {competitor_key}",
                f"{competitor_key} software",
                f"{competitor_key} system",
                f"{competitor_key} platform",
                f"{competitor_key} login",
                f"{competitor_key} portal",
                f"©.*{competitor_key}",  # Copyright mentions
            ]
            
            for pattern in context_patterns:
                if re.search(pattern, page_text, re.IGNORECASE):
                    logger.info(f"   🎯 Found context pattern: '{pattern}' -> {competitor_name}")
                    return competitor_name
        
        # Method 2: Check HTML attributes and meta tags
        competitor = self._check_html_attributes(soup)
        if competitor:
            return competitor
        
        # Method 3: Check footer and credits sections
        competitor = self._check_footer_credits(soup)
        if competitor:
            return competitor
        
        # Method 4: Check for JavaScript/CSS references
        competitor = self._check_script_references(soup)
        if competitor:
            return competitor
        
        # Method 5: Simple keyword presence (lower confidence)
        for competitor_key, competitor_name in self.KNOWN_COMPETITORS.items():
            if competitor_key in page_text:
                # Additional validation to avoid false positives
                if self._validate_competitor_mention(competitor_key, page_text):
                    logger.info(f"   🔍 Found keyword mention: {competitor_key} -> {competitor_name}")
                    return competitor_name
        
        return None
    
    def _check_html_attributes(self, soup: BeautifulSoup) -> Optional[str]:
        """Check HTML attributes for competitor mentions."""
        # Check meta tags
        meta_tags = soup.find_all('meta')
        for meta in meta_tags:
            content = str(meta).lower()
            for competitor_key, competitor_name in self.KNOWN_COMPETITORS.items():
                if competitor_key in content:
                    return competitor_name
        
        # Check data attributes
        elements_with_data = soup.find_all(attrs={'data-provider': True})
        elements_with_data.extend(soup.find_all(attrs={'data-system': True}))
        elements_with_data.extend(soup.find_all(attrs={'data-platform': True}))
        
        for element in elements_with_data:
            attrs_text = ' '.join(str(v).lower() for v in element.attrs.values())
            for competitor_key, competitor_name in self.KNOWN_COMPETITORS.items():
                if competitor_key in attrs_text:
                    return competitor_name
        
        return None
    
    def _check_footer_credits(self, soup: BeautifulSoup) -> Optional[str]:
        """Check footer and credits sections for competitor mentions."""
        # Find footer elements
        footers = soup.find_all(['footer', 'div'], class_=re.compile(r'footer|credit|copyright', re.I))
        footers.extend(soup.find_all('div', id=re.compile(r'footer|credit', re.I)))
        
        for footer in footers:
            footer_text = footer.get_text().lower()
            for competitor_key, competitor_name in self.KNOWN_COMPETITORS.items():
                if competitor_key in footer_text:
                    # Look for technology/software context in footer
                    if any(tech_word in footer_text for tech_word in 
                          ['powered', 'software', 'system', 'platform', 'technology', 'solution']):
                        return competitor_name
        
        return None
    
    def _check_script_references(self, soup: BeautifulSoup) -> Optional[str]:
        """Check JavaScript and CSS references for competitor mentions."""
        # Check script sources
        scripts = soup.find_all('script', src=True)
        links = soup.find_all('link', href=True)
        
        for element in scripts + links:
            src = element.get('src', '') or element.get('href', '')
            src_lower = src.lower()
            
            for competitor_key, competitor_name in self.KNOWN_COMPETITORS.items():
                if competitor_key.replace(' ', '') in src_lower.replace('-', '').replace('_', ''):
                    return competitor_name
        
        return None
    
    def _validate_competitor_mention(self, competitor_key: str, page_text: str) -> bool:
        """
        Validate that a competitor mention is likely legitimate.
        
        Args:
            competitor_key: The competitor keyword found
            page_text: Full page text
            
        Returns:
            True if mention seems legitimate
        """
        # Get context around the mention
        competitor_index = page_text.find(competitor_key)
        if competitor_index == -1:
            return False
        
        # Extract context (50 chars before and after)
        start = max(0, competitor_index - 50)
        end = min(len(page_text), competitor_index + len(competitor_key) + 50)
        context = page_text[start:end]
        
        # Look for technology/software indicators in context
        tech_indicators = [
            'software', 'system', 'platform', 'technology', 'solution',
            'powered', 'using', 'built', 'managed', 'login', 'portal',
            'management', 'booking', 'reservation', 'pos', 'point of sale'
        ]
        
        return any(indicator in context for indicator in tech_indicators)
    
    def batch_enrich_competitors(self, companies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Enrich competitor field for multiple companies.
        
        Args:
            companies: List of company data dictionaries
            
        Returns:
            List of enrichment results
        """
        results = []
        
        for i, company in enumerate(companies, 1):
            company_name = company.get('properties', {}).get('name', f'Company {i}')
            logger.info(f"🔄 Processing {i}/{len(companies)}: {company_name}")
            
            try:
                result = self.enrich_competitor_field(company)
                result['company_name'] = company_name
                result['company_id'] = company.get('id')
                results.append(result)
                
                # Rate limiting - be respectful to websites
                if i < len(companies):
                    time.sleep(2)  # 2 second delay between requests
                    
            except Exception as e:
                logger.error(f"   💥 Error processing {company_name}: {e}")
                results.append({
                    'company_name': company_name,
                    'company_id': company.get('id'),
                    'status': 'error',
                    'reason': str(e),
                    'current_value': 'Unknown',
                    'new_value': 'Unknown'
                })
        
        return results


def create_company_competitor_agent(**kwargs):
    """Factory function to create the company competitor agent."""
    return CompanyCompetitorAgent(**kwargs)


def main():
    """Demo the company competitor agent."""
    print("🏆 Company Competitor Field Enrichment Agent Demo")
    print("=" * 60)
    print("This agent scrapes company websites to detect competitor software")
    print()
    
    # Create the agent
    agent = create_company_competitor_agent()
    
    # Test with sample company data
    test_companies = [
        {
            'id': '12345',
            'properties': {
                'name': 'Test Golf Club',
                'website': 'https://example-golf-club.com',
                'competitor': 'Unknown'
            }
        }
    ]
    
    print("🔍 Testing competitor detection...")
    results = agent.batch_enrich_competitors(test_companies)
    
    print("\n📊 Results:")
    print("=" * 40)
    for result in results:
        print(f"Company: {result['company_name']}")
        print(f"Status: {result['status']}")
        print(f"Current: {result['current_value']}")
        print(f"New: {result['new_value']}")
        if 'reason' in result:
            print(f"Reason: {result['reason']}")
        print("-" * 40)
    
    print("\n💡 This agent can be integrated with the field enrichment workflow")
    print("   to automatically detect competitors from website analysis!")


if __name__ == "__main__":
    main()
