#!/usr/bin/env python3
"""
Data Quality Analyzer
Scrutinizes company and contact information to identify gaps and cleanup opportunities.
"""

import requests
import json
import re
from datetime import datetime
from collections import defaultdict, Counter


class DataQualityAnalyzer:
    """Analyzes HubSpot data quality and provides cleanup recommendations."""
    
    def __init__(self, mcp_url="http://localhost:8081/mcp"):
        self.mcp_url = mcp_url
        self.request_id = 1
        
        # Data quality scoring weights
        self.field_weights = {
            'companies': {
                'name': 10,      # Critical
                'domain': 9,     # Very important
                'industry': 8,   # Important for segmentation
                'phone': 7,      # Important for contact
                'city': 6,       # Good for targeting
                'state': 6,      # Good for targeting
                'website': 5,    # Nice to have
                'description': 4 # Nice to have
            },
            'contacts': {
                'email': 10,     # Critical
                'firstname': 9,  # Very important
                'lastname': 9,   # Very important
                'phone': 8,      # Important
                'jobtitle': 7,   # Important for targeting
                'company': 6     # Important for context
            }
        }
    
    def _call_mcp_tool(self, tool_name, arguments=None):
        """Call an MCP tool and return the result."""
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
            response = requests.post(self.mcp_url, json=payload)
            if response.status_code == 200:
                result = response.json()
                if "result" in result and "content" in result["result"]:
                    content = result["result"]["content"][0]["text"]
                    return json.loads(content)
            return None
        except Exception as e:
            print(f"❌ Error calling {tool_name}: {str(e)}")
            return None
    
    def analyze_companies(self, limit=50):
        """Analyze company data quality."""
        print("🏢 Analyzing company data quality...")
        
        companies_data = self._call_mcp_tool("get_companies", {"limit": limit})
        if not companies_data or "results" not in companies_data:
            return {"error": "Failed to retrieve companies"}
        
        companies = companies_data["results"]
        analysis = {
            "total_companies": len(companies),
            "completeness_scores": [],
            "field_gaps": defaultdict(int),
            "format_issues": [],
            "critical_gaps": [],
            "industry_distribution": Counter(),
            "domain_issues": [],
            "duplicate_candidates": []
        }
        
        # Analyze each company
        for company in companies:
            props = company.get("properties", {})
            company_name = props.get("name", f"Company {company['id']}")
            
            # Calculate completeness score
            completeness_score = self._calculate_completeness_score(props, 'companies')
            analysis["completeness_scores"].append({
                "name": company_name,
                "id": company["id"],
                "score": completeness_score
            })
            
            # Identify field gaps
            for field, weight in self.field_weights['companies'].items():
                if not props.get(field) or str(props.get(field)).strip() == "":
                    analysis["field_gaps"][field] += 1
                    
                    # Critical gaps (high weight fields missing)
                    if weight >= 8:
                        analysis["critical_gaps"].append({
                            "company": company_name,
                            "id": company["id"],
                            "missing_field": field,
                            "priority": "CRITICAL" if weight >= 9 else "HIGH"
                        })
            
            # Check data format issues
            self._check_company_format_issues(props, company_name, company["id"], analysis)
            
            # Track industry distribution
            industry = props.get("industry", "Unknown")
            analysis["industry_distribution"][industry] += 1
        
        return analysis
    
    def analyze_contacts(self, limit=50):
        """Analyze contact data quality."""
        print("👥 Analyzing contact data quality...")
        
        contacts_data = self._call_mcp_tool("get_contacts", {"limit": limit})
        if not contacts_data or "results" not in contacts_data:
            return {"error": "Failed to retrieve contacts"}
        
        contacts = contacts_data["results"]
        analysis = {
            "total_contacts": len(contacts),
            "completeness_scores": [],
            "field_gaps": defaultdict(int),
            "format_issues": [],
            "critical_gaps": [],
            "email_issues": [],
            "phone_format_issues": [],
            "duplicate_candidates": []
        }
        
        # Analyze each contact
        for contact in contacts:
            props = contact.get("properties", {})
            contact_name = f"{props.get('firstname', '')} {props.get('lastname', '')}".strip()
            if not contact_name:
                contact_name = props.get('email', f"Contact {contact['id']}")
            
            # Calculate completeness score
            completeness_score = self._calculate_completeness_score(props, 'contacts')
            analysis["completeness_scores"].append({
                "name": contact_name,
                "id": contact["id"],
                "score": completeness_score
            })
            
            # Identify field gaps
            for field, weight in self.field_weights['contacts'].items():
                if not props.get(field) or str(props.get(field)).strip() == "":
                    analysis["field_gaps"][field] += 1
                    
                    # Critical gaps
                    if weight >= 8:
                        analysis["critical_gaps"].append({
                            "contact": contact_name,
                            "id": contact["id"],
                            "missing_field": field,
                            "priority": "CRITICAL" if weight >= 9 else "HIGH"
                        })
            
            # Check email format
            email = props.get("email")
            if email and not self._is_valid_email(email):
                analysis["email_issues"].append({
                    "contact": contact_name,
                    "id": contact["id"],
                    "email": email,
                    "issue": "Invalid format"
                })
            
            # Check phone format
            phone = props.get("phone")
            if phone and not self._is_valid_phone(phone):
                analysis["phone_format_issues"].append({
                    "contact": contact_name,
                    "id": contact["id"],
                    "phone": phone,
                    "issue": "Inconsistent format"
                })
        
        return analysis
    
    def _calculate_completeness_score(self, props, record_type):
        """Calculate data completeness score for a record."""
        total_weight = sum(self.field_weights[record_type].values())
        achieved_weight = 0
        
        for field, weight in self.field_weights[record_type].items():
            if props.get(field) and str(props.get(field)).strip():
                achieved_weight += weight
        
        return round((achieved_weight / total_weight) * 100, 1)
    
    def _check_company_format_issues(self, props, company_name, company_id, analysis):
        """Check for company data format issues."""
        
        # Check domain format
        domain = props.get("domain")
        if domain:
            if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]*\.[a-zA-Z]{2,}$', domain):
                analysis["domain_issues"].append({
                    "company": company_name,
                    "id": company_id,
                    "domain": domain,
                    "issue": "Invalid domain format"
                })
        
        # Check phone format
        phone = props.get("phone")
        if phone and not self._is_valid_phone(phone):
            analysis["format_issues"].append({
                "company": company_name,
                "id": company_id,
                "field": "phone",
                "value": phone,
                "issue": "Inconsistent phone format"
            })
    
    def _is_valid_email(self, email):
        """Check if email format is valid."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _is_valid_phone(self, phone):
        """Check if phone format is reasonable."""
        # Remove common formatting
        clean_phone = re.sub(r'[\s\-\(\)\+\.]', '', phone)
        # Should have 10-15 digits
        return len(clean_phone) >= 10 and len(clean_phone) <= 15 and clean_phone.isdigit()
    
    def generate_quality_report(self, company_limit=50, contact_limit=50):
        """Generate comprehensive data quality report."""
        
        print("🔍 Starting comprehensive data quality analysis...")
        print("=" * 70)
        
        # Analyze companies and contacts
        company_analysis = self.analyze_companies(company_limit)
        contact_analysis = self.analyze_contacts(contact_limit)
        
        # Generate report
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": self._generate_summary(company_analysis, contact_analysis),
            "companies": company_analysis,
            "contacts": contact_analysis,
            "recommendations": self._generate_recommendations(company_analysis, contact_analysis)
        }
        
        self._print_quality_report(report)
        return report
    
    def _generate_summary(self, company_analysis, contact_analysis):
        """Generate executive summary of data quality."""
        
        # Calculate average completeness scores
        company_scores = [c["score"] for c in company_analysis.get("completeness_scores", [])]
        contact_scores = [c["score"] for c in contact_analysis.get("completeness_scores", [])]
        
        avg_company_score = sum(company_scores) / len(company_scores) if company_scores else 0
        avg_contact_score = sum(contact_scores) / len(contact_scores) if contact_scores else 0
        
        # Count critical issues
        critical_company_issues = len(company_analysis.get("critical_gaps", []))
        critical_contact_issues = len(contact_analysis.get("critical_gaps", []))
        
        return {
            "overall_health": "POOR" if avg_company_score < 60 or avg_contact_score < 60 else 
                             "FAIR" if avg_company_score < 80 or avg_contact_score < 80 else "GOOD",
            "avg_company_completeness": round(avg_company_score, 1),
            "avg_contact_completeness": round(avg_contact_score, 1),
            "total_critical_issues": critical_company_issues + critical_contact_issues,
            "companies_analyzed": company_analysis.get("total_companies", 0),
            "contacts_analyzed": contact_analysis.get("total_contacts", 0)
        }
    
    def _generate_recommendations(self, company_analysis, contact_analysis):
        """Generate prioritized cleanup recommendations."""
        
        recommendations = {
            "critical": [],
            "high": [],
            "medium": [],
            "process_improvements": []
        }
        
        # Critical recommendations
        if company_analysis.get("critical_gaps"):
            recommendations["critical"].append({
                "title": "Fill Critical Company Fields",
                "description": f"Fix {len(company_analysis['critical_gaps'])} companies missing essential data",
                "effort": "2-4 hours",
                "impact": "HIGH - Blocks sales and marketing activities"
            })
        
        if contact_analysis.get("critical_gaps"):
            recommendations["critical"].append({
                "title": "Complete Critical Contact Information",
                "description": f"Fix {len(contact_analysis['critical_gaps'])} contacts missing essential data",
                "effort": "1-3 hours",
                "impact": "HIGH - Affects outreach and communication"
            })
        
        # High priority recommendations
        if contact_analysis.get("email_issues"):
            recommendations["high"].append({
                "title": "Fix Invalid Email Addresses",
                "description": f"Correct {len(contact_analysis['email_issues'])} contacts with invalid emails",
                "effort": "1-2 hours",
                "impact": "MEDIUM - Improves email deliverability"
            })
        
        # Medium priority recommendations
        if company_analysis.get("format_issues") or contact_analysis.get("phone_format_issues"):
            total_format_issues = len(company_analysis.get("format_issues", [])) + len(contact_analysis.get("phone_format_issues", []))
            recommendations["medium"].append({
                "title": "Standardize Phone Number Formats",
                "description": f"Fix {total_format_issues} records with inconsistent phone formatting",
                "effort": "2-3 hours",
                "impact": "LOW - Improves data consistency"
            })
        
        # Process improvements
        recommendations["process_improvements"].extend([
            "Implement data validation rules for new record creation",
            "Set up automated data quality monitoring",
            "Create data entry guidelines for sales team",
            "Schedule monthly data quality reviews"
        ])
        
        return recommendations
    
    def _print_quality_report(self, report):
        """Print formatted data quality report."""
        
        summary = report["summary"]
        
        print(f"\n🔍 DATA QUALITY INTELLIGENCE REPORT")
        print("=" * 70)
        print(f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📊 Records Analyzed: {summary['companies_analyzed']} companies, {summary['contacts_analyzed']} contacts")
        
        print(f"\n📊 EXECUTIVE SUMMARY")
        print(f"Overall Data Health: {self._get_health_emoji(summary['overall_health'])} {summary['overall_health']}")
        print(f"Company Data Completeness: {summary['avg_company_completeness']}%")
        print(f"Contact Data Completeness: {summary['avg_contact_completeness']}%")
        print(f"Critical Issues Found: {summary['total_critical_issues']}")
        
        # Critical Issues
        recommendations = report["recommendations"]
        if recommendations["critical"]:
            print(f"\n🚨 CRITICAL ISSUES (Immediate Action Required)")
            for rec in recommendations["critical"]:
                print(f"  • {rec['title']}")
                print(f"    {rec['description']}")
                print(f"    Effort: {rec['effort']} | Impact: {rec['impact']}")
        
        # High Priority
        if recommendations["high"]:
            print(f"\n⚠️ HIGH PRIORITY GAPS")
            for rec in recommendations["high"]:
                print(f"  • {rec['title']}")
                print(f"    {rec['description']}")
                print(f"    Effort: {rec['effort']} | Impact: {rec['impact']}")
        
        # Medium Priority
        if recommendations["medium"]:
            print(f"\n📈 MEDIUM PRIORITY OPPORTUNITIES")
            for rec in recommendations["medium"]:
                print(f"  • {rec['title']}")
                print(f"    {rec['description']}")
                print(f"    Effort: {rec['effort']} | Impact: {rec['impact']}")
        
        # Top Companies Needing Attention
        company_scores = report["companies"]["completeness_scores"]
        if company_scores:
            worst_companies = sorted(company_scores, key=lambda x: x["score"])[:5]
            print(f"\n🏢 TOP COMPANIES NEEDING ATTENTION")
            for company in worst_companies:
                print(f"  • {company['name']} - {company['score']}% complete")
        
        # Top Contacts Needing Attention
        contact_scores = report["contacts"]["completeness_scores"]
        if contact_scores:
            worst_contacts = sorted(contact_scores, key=lambda x: x["score"])[:5]
            print(f"\n👥 TOP CONTACTS NEEDING ATTENTION")
            for contact in worst_contacts:
                print(f"  • {contact['name']} - {contact['score']}% complete")
        
        # Process Improvements
        print(f"\n🔧 PROCESS IMPROVEMENTS")
        for improvement in recommendations["process_improvements"]:
            print(f"  • {improvement}")
        
        print("\n" + "=" * 70)
    
    def _get_health_emoji(self, health):
        """Get emoji for health status."""
        return {"POOR": "🔴", "FAIR": "🟡", "GOOD": "🟢"}.get(health, "⚪")


def main():
    """Run data quality analysis."""
    print("🔍 Data Quality Intelligence Analyzer")
    print("Scrutinizes company and contact data to identify cleanup opportunities")
    print("=" * 70)
    
    try:
        analyzer = DataQualityAnalyzer()
        report = analyzer.generate_quality_report(company_limit=100, contact_limit=100)
        
        print(f"\n💾 Analysis complete! Report generated at {datetime.now().strftime('%H:%M:%S')}")
        print("💡 Use this report to prioritize your data cleanup efforts.")
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to MCP server")
        print("💡 Make sure the server is running: python mcp_wrapper/simple_hubspot_server.py")
    except Exception as e:
        print(f"❌ Error during analysis: {str(e)}")


if __name__ == "__main__":
    main()
