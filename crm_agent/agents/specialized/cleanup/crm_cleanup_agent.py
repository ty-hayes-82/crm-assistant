#!/usr/bin/env python3
"""
CRM Cleanup and Gap Analysis Agent

This agent helps clean up duplicate information/contacts and identifies the biggest gaps
in your CRM data by analyzing HubSpot data through the MCP server.
"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Tuple, Set, Optional, Any
from dataclasses import dataclass, field
import re
from difflib import SequenceMatcher
from collections import defaultdict, Counter
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DuplicateContact:
    """Represents a potential duplicate contact."""
    primary_id: str
    primary_name: str
    primary_email: str
    duplicate_ids: List[str]
    duplicate_names: List[str]
    duplicate_emails: List[str]
    similarity_score: float
    match_type: str  # 'email', 'name', 'phone', 'combined'
    recommended_action: str

@dataclass
class DuplicateCompany:
    """Represents a potential duplicate company."""
    primary_id: str
    primary_name: str
    primary_domain: str
    duplicate_ids: List[str]
    duplicate_names: List[str]
    duplicate_domains: List[str]
    similarity_score: float
    match_type: str  # 'domain', 'name', 'combined'
    recommended_action: str

@dataclass
class DataGap:
    """Represents a data gap in CRM records."""
    object_type: str  # 'contact' or 'company'
    object_id: str
    object_name: str
    missing_fields: List[str]
    importance_score: float
    suggested_sources: List[str]

@dataclass
class CleanupReport:
    """Comprehensive cleanup and gap analysis report."""
    analysis_timestamp: datetime
    total_contacts_analyzed: int
    total_companies_analyzed: int
    
    # Duplicates
    duplicate_contacts: List[DuplicateContact] = field(default_factory=list)
    duplicate_companies: List[DuplicateCompany] = field(default_factory=list)
    
    # Data gaps
    critical_gaps: List[DataGap] = field(default_factory=list)
    moderate_gaps: List[DataGap] = field(default_factory=list)
    minor_gaps: List[DataGap] = field(default_factory=list)
    
    # Summary statistics
    potential_duplicate_contacts: int = 0
    potential_duplicate_companies: int = 0
    total_data_gaps: int = 0
    data_quality_score: float = 0.0
    
    # Recommendations
    priority_actions: List[str] = field(default_factory=list)
    estimated_cleanup_time: str = ""

class CRMCleanupAgent:
    """
    Advanced CRM cleanup agent that identifies duplicates and data gaps.
    """
    
    def __init__(self, mcp_url: str = "http://localhost:8081/mcp"):
        self.mcp_url = mcp_url
        self.critical_fields = {
            'contact': ['firstname', 'lastname', 'email', 'phone', 'jobtitle', 'company'],
            'company': ['name', 'domain', 'industry', 'city', 'state', 'country', 'phone', 'website']
        }
        self.similarity_threshold = 0.8
        
    def make_mcp_request(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Make a request to the MCP server."""
        payload = {
            "jsonrpc": "2.0",
            "method": "call_tool",
            "params": {
                "name": tool_name,
                "arguments": arguments
            },
            "id": 1
        }
        
        try:
            response = requests.post(self.mcp_url, json=payload)
            if response.status_code == 200:
                result = response.json()
                content = result["result"]["content"][0]["text"]
                return json.loads(content)
            else:
                logger.error(f"MCP request failed: {response.status_code}")
                return {"error": f"Request failed: {response.status_code}"}
        except Exception as e:
            logger.error(f"MCP request error: {str(e)}")
            return {"error": str(e)}
    
    def get_all_contacts(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Retrieve all contacts from HubSpot."""
        contacts = []
        batch_size = 100
        
        for offset in range(0, limit, batch_size):
            current_limit = min(batch_size, limit - offset)
            result = self.make_mcp_request("get_contacts", {"limit": current_limit})
            
            if "error" in result:
                logger.error(f"Error fetching contacts: {result['error']}")
                break
                
            if "results" in result:
                contacts.extend(result["results"])
                if len(result["results"]) < current_limit:
                    break
            else:
                break
                
        logger.info(f"Retrieved {len(contacts)} contacts")
        return contacts
    
    def get_all_companies(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Retrieve all companies from HubSpot."""
        companies = []
        batch_size = 100
        
        for offset in range(0, limit, batch_size):
            current_limit = min(batch_size, limit - offset)
            result = self.make_mcp_request("get_companies", {"limit": current_limit})
            
            if "error" in result:
                logger.error(f"Error fetching companies: {result['error']}")
                break
                
            if "results" in result:
                companies.extend(result["results"])
                if len(result["results"]) < current_limit:
                    break
            else:
                break
                
        logger.info(f"Retrieved {len(companies)} companies")
        return companies
    
    def normalize_string(self, s: str) -> str:
        """Normalize string for comparison."""
        if not s:
            return ""
        # Convert to lowercase, remove extra spaces, special characters
        normalized = re.sub(r'[^\w\s]', '', s.lower().strip())
        return re.sub(r'\s+', ' ', normalized)
    
    def calculate_similarity(self, s1: str, s2: str) -> float:
        """Calculate similarity between two strings."""
        if not s1 or not s2:
            return 0.0
        
        norm_s1 = self.normalize_string(s1)
        norm_s2 = self.normalize_string(s2)
        
        return SequenceMatcher(None, norm_s1, norm_s2).ratio()
    
    def find_duplicate_contacts(self, contacts: List[Dict[str, Any]]) -> List[DuplicateContact]:
        """Find potential duplicate contacts."""
        duplicates = []
        processed_ids = set()
        
        # Group by email first (exact matches)
        email_groups = defaultdict(list)
        for contact in contacts:
            props = contact.get("properties", {})
            email = props.get("email", "").lower().strip()
            if email:
                email_groups[email].append(contact)
        
        # Process email duplicates
        for email, contact_group in email_groups.items():
            if len(contact_group) > 1:
                primary = contact_group[0]
                primary_props = primary.get("properties", {})
                primary_name = f"{primary_props.get('firstname', '')} {primary_props.get('lastname', '')}".strip()
                
                duplicate_ids = [c["id"] for c in contact_group[1:]]
                duplicate_names = []
                duplicate_emails = []
                
                for dup in contact_group[1:]:
                    dup_props = dup.get("properties", {})
                    dup_name = f"{dup_props.get('firstname', '')} {dup_props.get('lastname', '')}".strip()
                    duplicate_names.append(dup_name)
                    duplicate_emails.append(dup_props.get('email', ''))
                    processed_ids.add(dup["id"])
                
                processed_ids.add(primary["id"])
                
                duplicates.append(DuplicateContact(
                    primary_id=primary["id"],
                    primary_name=primary_name,
                    primary_email=email,
                    duplicate_ids=duplicate_ids,
                    duplicate_names=duplicate_names,
                    duplicate_emails=duplicate_emails,
                    similarity_score=1.0,
                    match_type="email",
                    recommended_action="merge_records"
                ))
        
        # Find name-based duplicates for remaining contacts
        remaining_contacts = [c for c in contacts if c["id"] not in processed_ids]
        
        for i, contact1 in enumerate(remaining_contacts):
            if contact1["id"] in processed_ids:
                continue
                
            props1 = contact1.get("properties", {})
            name1 = f"{props1.get('firstname', '')} {props1.get('lastname', '')}".strip()
            
            if not name1 or len(name1) < 3:
                continue
            
            similar_contacts = []
            
            for j, contact2 in enumerate(remaining_contacts[i+1:], i+1):
                if contact2["id"] in processed_ids:
                    continue
                    
                props2 = contact2.get("properties", {})
                name2 = f"{props2.get('firstname', '')} {props2.get('lastname', '')}".strip()
                
                if not name2 or len(name2) < 3:
                    continue
                
                similarity = self.calculate_similarity(name1, name2)
                
                if similarity >= self.similarity_threshold:
                    similar_contacts.append((contact2, similarity))
                    processed_ids.add(contact2["id"])
            
            if similar_contacts:
                processed_ids.add(contact1["id"])
                
                duplicate_ids = [c[0]["id"] for c in similar_contacts]
                duplicate_names = []
                duplicate_emails = []
                
                for contact, sim in similar_contacts:
                    props = contact.get("properties", {})
                    dup_name = f"{props.get('firstname', '')} {props.get('lastname', '')}".strip()
                    duplicate_names.append(dup_name)
                    duplicate_emails.append(props.get('email', ''))
                
                avg_similarity = sum(sim for _, sim in similar_contacts) / len(similar_contacts)
                
                duplicates.append(DuplicateContact(
                    primary_id=contact1["id"],
                    primary_name=name1,
                    primary_email=props1.get('email', ''),
                    duplicate_ids=duplicate_ids,
                    duplicate_names=duplicate_names,
                    duplicate_emails=duplicate_emails,
                    similarity_score=avg_similarity,
                    match_type="name",
                    recommended_action="review_and_merge" if avg_similarity > 0.9 else "manual_review"
                ))
        
        return duplicates
    
    def find_duplicate_companies(self, companies: List[Dict[str, Any]]) -> List[DuplicateCompany]:
        """Find potential duplicate companies."""
        duplicates = []
        processed_ids = set()
        
        # Group by domain first (exact matches)
        domain_groups = defaultdict(list)
        for company in companies:
            props = company.get("properties", {})
            domain = props.get("domain", "").lower().strip()
            if domain and domain != "unknown":
                domain_groups[domain].append(company)
        
        # Process domain duplicates
        for domain, company_group in domain_groups.items():
            if len(company_group) > 1:
                primary = company_group[0]
                primary_props = primary.get("properties", {})
                primary_name = primary_props.get("name", "")
                
                duplicate_ids = [c["id"] for c in company_group[1:]]
                duplicate_names = []
                duplicate_domains = []
                
                for dup in company_group[1:]:
                    dup_props = dup.get("properties", {})
                    duplicate_names.append(dup_props.get('name', ''))
                    duplicate_domains.append(dup_props.get('domain', ''))
                    processed_ids.add(dup["id"])
                
                processed_ids.add(primary["id"])
                
                duplicates.append(DuplicateCompany(
                    primary_id=primary["id"],
                    primary_name=primary_name,
                    primary_domain=domain,
                    duplicate_ids=duplicate_ids,
                    duplicate_names=duplicate_names,
                    duplicate_domains=duplicate_domains,
                    similarity_score=1.0,
                    match_type="domain",
                    recommended_action="merge_records"
                ))
        
        # Find name-based duplicates for remaining companies
        remaining_companies = [c for c in companies if c["id"] not in processed_ids]
        
        for i, company1 in enumerate(remaining_companies):
            if company1["id"] in processed_ids:
                continue
                
            props1 = company1.get("properties", {})
            name1 = props1.get("name", "").strip()
            
            if not name1 or len(name1) < 3:
                continue
            
            similar_companies = []
            
            for j, company2 in enumerate(remaining_companies[i+1:], i+1):
                if company2["id"] in processed_ids:
                    continue
                    
                props2 = company2.get("properties", {})
                name2 = props2.get("name", "").strip()
                
                if not name2 or len(name2) < 3:
                    continue
                
                similarity = self.calculate_similarity(name1, name2)
                
                if similarity >= self.similarity_threshold:
                    similar_companies.append((company2, similarity))
                    processed_ids.add(company2["id"])
            
            if similar_companies:
                processed_ids.add(company1["id"])
                
                duplicate_ids = [c[0]["id"] for c in similar_companies]
                duplicate_names = []
                duplicate_domains = []
                
                for company, sim in similar_companies:
                    props = company.get("properties", {})
                    duplicate_names.append(props.get('name', ''))
                    duplicate_domains.append(props.get('domain', ''))
                
                avg_similarity = sum(sim for _, sim in similar_companies) / len(similar_companies)
                
                duplicates.append(DuplicateCompany(
                    primary_id=company1["id"],
                    primary_name=name1,
                    primary_domain=props1.get('domain', ''),
                    duplicate_ids=duplicate_ids,
                    duplicate_names=duplicate_names,
                    duplicate_domains=duplicate_domains,
                    similarity_score=avg_similarity,
                    match_type="name",
                    recommended_action="review_and_merge" if avg_similarity > 0.9 else "manual_review"
                ))
        
        return duplicates
    
    def analyze_data_gaps(self, contacts: List[Dict[str, Any]], companies: List[Dict[str, Any]]) -> Tuple[List[DataGap], List[DataGap], List[DataGap]]:
        """Analyze data gaps in contacts and companies."""
        critical_gaps = []
        moderate_gaps = []
        minor_gaps = []
        
        # Analyze contact gaps
        for contact in contacts:
            props = contact.get("properties", {})
            missing_fields = []
            
            for field in self.critical_fields['contact']:
                value = props.get(field, "")
                if not value or value.strip() == "":
                    missing_fields.append(field)
            
            if missing_fields:
                # Calculate importance score based on missing fields
                importance_score = self.calculate_gap_importance(missing_fields, 'contact')
                
                name = f"{props.get('firstname', '')} {props.get('lastname', '')}".strip()
                if not name:
                    name = props.get('email', f'Contact {contact["id"]}')
                
                gap = DataGap(
                    object_type='contact',
                    object_id=contact["id"],
                    object_name=name,
                    missing_fields=missing_fields,
                    importance_score=importance_score,
                    suggested_sources=self.suggest_data_sources(missing_fields, 'contact')
                )
                
                if importance_score >= 0.8:
                    critical_gaps.append(gap)
                elif importance_score >= 0.5:
                    moderate_gaps.append(gap)
                else:
                    minor_gaps.append(gap)
        
        # Analyze company gaps
        for company in companies:
            props = company.get("properties", {})
            missing_fields = []
            
            for field in self.critical_fields['company']:
                value = props.get(field, "")
                if not value or value.strip() == "":
                    missing_fields.append(field)
            
            if missing_fields:
                importance_score = self.calculate_gap_importance(missing_fields, 'company')
                
                name = props.get('name', f'Company {company["id"]}')
                
                gap = DataGap(
                    object_type='company',
                    object_id=company["id"],
                    object_name=name,
                    missing_fields=missing_fields,
                    importance_score=importance_score,
                    suggested_sources=self.suggest_data_sources(missing_fields, 'company')
                )
                
                if importance_score >= 0.8:
                    critical_gaps.append(gap)
                elif importance_score >= 0.5:
                    moderate_gaps.append(gap)
                else:
                    minor_gaps.append(gap)
        
        return critical_gaps, moderate_gaps, minor_gaps
    
    def calculate_gap_importance(self, missing_fields: List[str], object_type: str) -> float:
        """Calculate importance score for data gaps."""
        field_weights = {
            'contact': {
                'email': 0.9,
                'firstname': 0.7,
                'lastname': 0.7,
                'company': 0.6,
                'jobtitle': 0.5,
                'phone': 0.4
            },
            'company': {
                'name': 0.9,
                'domain': 0.8,
                'industry': 0.7,
                'website': 0.6,
                'city': 0.4,
                'state': 0.3,
                'country': 0.3,
                'phone': 0.4
            }
        }
        
        weights = field_weights.get(object_type, {})
        total_weight = sum(weights.get(field, 0.1) for field in missing_fields)
        max_possible_weight = sum(weights.values())
        
        return min(total_weight / max_possible_weight if max_possible_weight > 0 else 0, 1.0)
    
    def suggest_data_sources(self, missing_fields: List[str], object_type: str) -> List[str]:
        """Suggest data sources for filling gaps."""
        sources = []
        
        if object_type == 'contact':
            if 'email' in missing_fields:
                sources.extend(['LinkedIn', 'Company website', 'Business cards'])
            if 'jobtitle' in missing_fields:
                sources.extend(['LinkedIn', 'Company website'])
            if 'company' in missing_fields:
                sources.extend(['LinkedIn', 'Email domain'])
            if 'phone' in missing_fields:
                sources.extend(['Company directory', 'LinkedIn'])
        
        elif object_type == 'company':
            if 'domain' in missing_fields:
                sources.extend(['Company website', 'Google search'])
            if 'industry' in missing_fields:
                sources.extend(['LinkedIn company page', 'Clearbit', 'Crunchbase'])
            if 'website' in missing_fields:
                sources.extend(['Google search', 'Domain lookup'])
            if any(field in missing_fields for field in ['city', 'state', 'country']):
                sources.extend(['Company website', 'LinkedIn', 'Google Maps'])
        
        return list(set(sources))
    
    def generate_cleanup_report(self, contacts: List[Dict[str, Any]], companies: List[Dict[str, Any]]) -> CleanupReport:
        """Generate comprehensive cleanup and gap analysis report."""
        logger.info("Starting comprehensive CRM cleanup analysis...")
        
        # Find duplicates
        logger.info("Analyzing duplicate contacts...")
        duplicate_contacts = self.find_duplicate_contacts(contacts)
        
        logger.info("Analyzing duplicate companies...")
        duplicate_companies = self.find_duplicate_companies(companies)
        
        # Analyze data gaps
        logger.info("Analyzing data gaps...")
        critical_gaps, moderate_gaps, minor_gaps = self.analyze_data_gaps(contacts, companies)
        
        # Calculate data quality score
        total_records = len(contacts) + len(companies)
        total_gaps = len(critical_gaps) + len(moderate_gaps) + len(minor_gaps)
        duplicate_penalty = (len(duplicate_contacts) + len(duplicate_companies)) * 0.1
        
        quality_score = max(0.0, 1.0 - (total_gaps / total_records if total_records > 0 else 0) - duplicate_penalty)
        
        # Generate priority actions
        priority_actions = []
        
        if duplicate_contacts:
            priority_actions.append(f"Merge {len(duplicate_contacts)} groups of duplicate contacts")
        if duplicate_companies:
            priority_actions.append(f"Merge {len(duplicate_companies)} groups of duplicate companies")
        if critical_gaps:
            priority_actions.append(f"Fill {len(critical_gaps)} critical data gaps")
        if moderate_gaps:
            priority_actions.append(f"Address {len(moderate_gaps)} moderate data gaps")
        
        # Estimate cleanup time
        total_duplicates = len(duplicate_contacts) + len(duplicate_companies)
        estimated_minutes = (total_duplicates * 5) + (len(critical_gaps) * 2) + (len(moderate_gaps) * 1)
        estimated_cleanup_time = f"{estimated_minutes} minutes" if estimated_minutes < 60 else f"{estimated_minutes // 60}h {estimated_minutes % 60}m"
        
        report = CleanupReport(
            analysis_timestamp=datetime.now(),
            total_contacts_analyzed=len(contacts),
            total_companies_analyzed=len(companies),
            duplicate_contacts=duplicate_contacts,
            duplicate_companies=duplicate_companies,
            critical_gaps=critical_gaps,
            moderate_gaps=moderate_gaps,
            minor_gaps=minor_gaps,
            potential_duplicate_contacts=len(duplicate_contacts),
            potential_duplicate_companies=len(duplicate_companies),
            total_data_gaps=total_gaps,
            data_quality_score=quality_score,
            priority_actions=priority_actions,
            estimated_cleanup_time=estimated_cleanup_time
        )
        
        logger.info("Cleanup analysis completed!")
        return report
    
    def print_cleanup_report(self, report: CleanupReport):
        """Print a formatted cleanup report."""
        print("\n" + "=" * 80)
        print("🧹 CRM CLEANUP & GAP ANALYSIS REPORT")
        print("=" * 80)
        
        print(f"\n📊 ANALYSIS SUMMARY")
        print(f"   Analysis Date: {report.analysis_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Contacts Analyzed: {report.total_contacts_analyzed:,}")
        print(f"   Companies Analyzed: {report.total_companies_analyzed:,}")
        print(f"   Data Quality Score: {report.data_quality_score:.1%}")
        
        print(f"\n🔍 DUPLICATE DETECTION")
        print(f"   Potential Duplicate Contacts: {report.potential_duplicate_contacts}")
        print(f"   Potential Duplicate Companies: {report.potential_duplicate_companies}")
        
        if report.duplicate_contacts:
            print(f"\n👥 DUPLICATE CONTACTS ({len(report.duplicate_contacts)})")
            for i, dup in enumerate(report.duplicate_contacts[:5], 1):
                print(f"   {i}. {dup.primary_name} ({dup.primary_email})")
                print(f"      Duplicates: {len(dup.duplicate_ids)} records")
                print(f"      Match Type: {dup.match_type}")
                print(f"      Similarity: {dup.similarity_score:.1%}")
                print(f"      Action: {dup.recommended_action}")
                print()
            
            if len(report.duplicate_contacts) > 5:
                print(f"   ... and {len(report.duplicate_contacts) - 5} more")
        
        if report.duplicate_companies:
            print(f"\n🏢 DUPLICATE COMPANIES ({len(report.duplicate_companies)})")
            for i, dup in enumerate(report.duplicate_companies[:5], 1):
                print(f"   {i}. {dup.primary_name} ({dup.primary_domain})")
                print(f"      Duplicates: {len(dup.duplicate_ids)} records")
                print(f"      Match Type: {dup.match_type}")
                print(f"      Similarity: {dup.similarity_score:.1%}")
                print(f"      Action: {dup.recommended_action}")
                print()
            
            if len(report.duplicate_companies) > 5:
                print(f"   ... and {len(report.duplicate_companies) - 5} more")
        
        print(f"\n📋 DATA GAPS ANALYSIS")
        print(f"   Critical Gaps: {len(report.critical_gaps)}")
        print(f"   Moderate Gaps: {len(report.moderate_gaps)}")
        print(f"   Minor Gaps: {len(report.minor_gaps)}")
        print(f"   Total Gaps: {report.total_data_gaps}")
        
        if report.critical_gaps:
            print(f"\n🚨 CRITICAL GAPS ({len(report.critical_gaps)})")
            for i, gap in enumerate(report.critical_gaps[:5], 1):
                print(f"   {i}. {gap.object_name} ({gap.object_type})")
                print(f"      Missing: {', '.join(gap.missing_fields)}")
                print(f"      Importance: {gap.importance_score:.1%}")
                print(f"      Sources: {', '.join(gap.suggested_sources)}")
                print()
            
            if len(report.critical_gaps) > 5:
                print(f"   ... and {len(report.critical_gaps) - 5} more")
        
        print(f"\n🎯 PRIORITY ACTIONS")
        for i, action in enumerate(report.priority_actions, 1):
            print(f"   {i}. {action}")
        
        print(f"\n⏱️  ESTIMATED CLEANUP TIME: {report.estimated_cleanup_time}")
        
        print("\n" + "=" * 80)

def main():
    """Main function to run CRM cleanup analysis."""
    print("🧹 Starting CRM Cleanup and Gap Analysis...")
    
    agent = CRMCleanupAgent()
    
    # Fetch data
    print("📥 Fetching contacts and companies...")
    contacts = agent.get_all_contacts(limit=500)  # Adjust limit as needed
    companies = agent.get_all_companies(limit=500)
    
    if not contacts and not companies:
        print("❌ No data retrieved. Make sure the MCP server is running.")
        return
    
    # Generate report
    report = agent.generate_cleanup_report(contacts, companies)
    
    # Print report
    agent.print_cleanup_report(report)
    
    return report

if __name__ == "__main__":
    main()
