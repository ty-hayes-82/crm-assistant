#!/usr/bin/env python3
"""
Integration layer between CRM Cleanup Agent and existing CRM agent system.

This module provides integration hooks to use the cleanup agent within
the existing multi-agent CRM framework.
"""

from typing import Dict, List, Any, Optional
from crm_cleanup_agent import CRMCleanupAgent, CleanupReport
import json
import logging

logger = logging.getLogger(__name__)

class CRMCleanupIntegration:
    """
    Integration wrapper for CRM Cleanup Agent that works with the existing
    CRM agent system and state management.
    """
    
    def __init__(self, mcp_url: str = "http://localhost:8081/mcp"):
        self.cleanup_agent = CRMCleanupAgent(mcp_url)
        
    def analyze_crm_quality(self, 
                           contact_limit: int = 1000,
                           company_limit: int = 500,
                           similarity_threshold: float = 0.8) -> Dict[str, Any]:
        """
        Analyze CRM data quality and return structured results.
        
        Returns results in a format compatible with existing CRM agent state.
        """
        try:
            # Configure agent
            self.cleanup_agent.similarity_threshold = similarity_threshold
            
            # Fetch data
            logger.info(f"Fetching up to {contact_limit} contacts and {company_limit} companies")
            contacts = self.cleanup_agent.get_all_contacts(limit=contact_limit)
            companies = self.cleanup_agent.get_all_companies(limit=company_limit)
            
            if not contacts and not companies:
                return {
                    "error": "No data retrieved from HubSpot",
                    "suggestion": "Check MCP server connection and HubSpot access token"
                }
            
            # Generate report
            report = self.cleanup_agent.generate_cleanup_report(contacts, companies)
            
            # Convert to structured format
            return self._convert_report_to_dict(report)
            
        except Exception as e:
            logger.error(f"CRM quality analysis failed: {str(e)}")
            return {
                "error": f"Analysis failed: {str(e)}",
                "suggestion": "Check logs for detailed error information"
            }
    
    def _convert_report_to_dict(self, report: CleanupReport) -> Dict[str, Any]:
        """Convert CleanupReport to dictionary format."""
        return {
            "analysis_timestamp": report.analysis_timestamp.isoformat(),
            "summary": {
                "total_contacts_analyzed": report.total_contacts_analyzed,
                "total_companies_analyzed": report.total_companies_analyzed,
                "data_quality_score": report.data_quality_score,
                "potential_duplicate_contacts": report.potential_duplicate_contacts,
                "potential_duplicate_companies": report.potential_duplicate_companies,
                "total_data_gaps": report.total_data_gaps,
                "estimated_cleanup_time": report.estimated_cleanup_time
            },
            "duplicates": {
                "contacts": [
                    {
                        "primary_id": dup.primary_id,
                        "primary_name": dup.primary_name,
                        "primary_email": dup.primary_email,
                        "duplicate_count": len(dup.duplicate_ids),
                        "duplicate_ids": dup.duplicate_ids,
                        "similarity_score": dup.similarity_score,
                        "match_type": dup.match_type,
                        "recommended_action": dup.recommended_action
                    }
                    for dup in report.duplicate_contacts
                ],
                "companies": [
                    {
                        "primary_id": dup.primary_id,
                        "primary_name": dup.primary_name,
                        "primary_domain": dup.primary_domain,
                        "duplicate_count": len(dup.duplicate_ids),
                        "duplicate_ids": dup.duplicate_ids,
                        "similarity_score": dup.similarity_score,
                        "match_type": dup.match_type,
                        "recommended_action": dup.recommended_action
                    }
                    for dup in report.duplicate_companies
                ]
            },
            "gaps": {
                "critical": [
                    {
                        "object_type": gap.object_type,
                        "object_id": gap.object_id,
                        "object_name": gap.object_name,
                        "missing_fields": gap.missing_fields,
                        "importance_score": gap.importance_score,
                        "suggested_sources": gap.suggested_sources
                    }
                    for gap in report.critical_gaps
                ],
                "moderate": [
                    {
                        "object_type": gap.object_type,
                        "object_id": gap.object_id,
                        "object_name": gap.object_name,
                        "missing_fields": gap.missing_fields,
                        "importance_score": gap.importance_score,
                        "suggested_sources": gap.suggested_sources
                    }
                    for gap in report.moderate_gaps
                ],
                "minor": [
                    {
                        "object_type": gap.object_type,
                        "object_id": gap.object_id,
                        "object_name": gap.object_name,
                        "missing_fields": gap.missing_fields,
                        "importance_score": gap.importance_score,
                        "suggested_sources": gap.suggested_sources
                    }
                    for gap in report.minor_gaps
                ]
            },
            "recommendations": {
                "priority_actions": report.priority_actions,
                "quick_wins": self._identify_quick_wins(report),
                "long_term_improvements": self._identify_long_term_improvements(report)
            }
        }
    
    def _identify_quick_wins(self, report: CleanupReport) -> List[Dict[str, Any]]:
        """Identify quick win opportunities."""
        quick_wins = []
        
        # High-confidence duplicates
        high_conf_contacts = [d for d in report.duplicate_contacts if d.similarity_score >= 0.95]
        high_conf_companies = [d for d in report.duplicate_companies if d.similarity_score >= 0.95]
        
        if high_conf_contacts:
            quick_wins.append({
                "type": "merge_high_confidence_contacts",
                "count": len(high_conf_contacts),
                "estimated_time_minutes": len(high_conf_contacts) * 3,
                "description": f"Merge {len(high_conf_contacts)} high-confidence duplicate contacts"
            })
        
        if high_conf_companies:
            quick_wins.append({
                "type": "merge_high_confidence_companies",
                "count": len(high_conf_companies),
                "estimated_time_minutes": len(high_conf_companies) * 3,
                "description": f"Merge {len(high_conf_companies)} high-confidence duplicate companies"
            })
        
        # Easy critical gaps
        easy_gaps = [g for g in report.critical_gaps if 'LinkedIn' in g.suggested_sources]
        if easy_gaps:
            quick_wins.append({
                "type": "fill_linkedin_gaps",
                "count": len(easy_gaps),
                "estimated_time_minutes": len(easy_gaps) * 2,
                "description": f"Fill {len(easy_gaps)} critical gaps using LinkedIn"
            })
        
        return quick_wins
    
    def _identify_long_term_improvements(self, report: CleanupReport) -> List[Dict[str, Any]]:
        """Identify long-term improvement opportunities."""
        improvements = []
        
        if report.data_quality_score < 0.8:
            improvements.append({
                "type": "implement_data_quality_processes",
                "priority": "high",
                "description": "Implement automated data quality checks and validation rules"
            })
        
        if report.potential_duplicate_contacts + report.potential_duplicate_companies > 10:
            improvements.append({
                "type": "duplicate_prevention",
                "priority": "medium", 
                "description": "Set up duplicate prevention workflows in HubSpot"
            })
        
        if len(report.critical_gaps) > 20:
            improvements.append({
                "type": "data_enrichment_automation",
                "priority": "medium",
                "description": "Implement automated data enrichment using external APIs"
            })
        
        return improvements
    
    def get_cleanup_summary_for_agent(self, contact_limit: int = 100) -> str:
        """
        Get a concise cleanup summary suitable for agent-to-agent communication.
        
        Returns a formatted string that can be used in agent instructions or responses.
        """
        try:
            analysis = self.analyze_crm_quality(contact_limit=contact_limit, company_limit=50)
            
            if "error" in analysis:
                return f"❌ CRM Analysis Error: {analysis['error']}"
            
            summary = analysis["summary"]
            duplicates = analysis["duplicates"]
            gaps = analysis["gaps"]
            
            return f"""
🧹 CRM CLEANUP ANALYSIS SUMMARY:
• Data Quality Score: {summary['data_quality_score']:.1%}
• Records Analyzed: {summary['total_contacts_analyzed']} contacts, {summary['total_companies_analyzed']} companies
• Duplicates Found: {summary['potential_duplicate_contacts']} contact groups, {summary['potential_duplicate_companies']} company groups
• Data Gaps: {len(gaps['critical'])} critical, {len(gaps['moderate'])} moderate, {len(gaps['minor'])} minor
• Estimated Cleanup Time: {summary['estimated_cleanup_time']}

🎯 TOP RECOMMENDATIONS:
{chr(10).join(f"• {action}" for action in analysis['recommendations']['priority_actions'][:3])}
            """.strip()
            
        except Exception as e:
            return f"❌ Failed to generate cleanup summary: {str(e)}"

# Utility functions for integration with existing agent system

def create_cleanup_agent_tool():
    """
    Create a tool definition that can be used by other agents.
    
    Returns a tool definition compatible with the existing agent framework.
    """
    return {
        "name": "analyze_crm_data_quality",
        "description": "Analyze CRM data quality, identify duplicates, and find data gaps",
        "parameters": {
            "type": "object",
            "properties": {
                "contact_limit": {
                    "type": "integer",
                    "description": "Maximum number of contacts to analyze (default: 500)",
                    "default": 500
                },
                "company_limit": {
                    "type": "integer", 
                    "description": "Maximum number of companies to analyze (default: 200)",
                    "default": 200
                },
                "similarity_threshold": {
                    "type": "number",
                    "description": "Similarity threshold for duplicate detection (0.0-1.0, default: 0.8)",
                    "default": 0.8,
                    "minimum": 0.0,
                    "maximum": 1.0
                }
            }
        }
    }

def handle_cleanup_tool_call(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle a tool call to the cleanup agent.
    
    This function can be integrated into existing tool handling systems.
    """
    integration = CRMCleanupIntegration()
    
    contact_limit = arguments.get("contact_limit", 500)
    company_limit = arguments.get("company_limit", 200)
    similarity_threshold = arguments.get("similarity_threshold", 0.8)
    
    return integration.analyze_crm_quality(
        contact_limit=contact_limit,
        company_limit=company_limit,
        similarity_threshold=similarity_threshold
    )

# Example usage for existing agent system
def demo_agent_integration():
    """Demonstrate how to integrate with existing agent system."""
    print("🔗 CRM Cleanup Agent Integration Demo")
    print("=" * 40)
    
    integration = CRMCleanupIntegration()
    
    # Quick summary for agent communication
    print("📊 Getting cleanup summary for agent...")
    summary = integration.get_cleanup_summary_for_agent(contact_limit=50)
    print(summary)
    
    # Full analysis
    print(f"\n🔍 Running full analysis...")
    analysis = integration.analyze_crm_quality(contact_limit=100, company_limit=50)
    
    if "error" not in analysis:
        print(f"✅ Analysis completed successfully!")
        print(f"   Data Quality Score: {analysis['summary']['data_quality_score']:.1%}")
        print(f"   Quick Wins Available: {len(analysis['recommendations']['quick_wins'])}")
        print(f"   Long-term Improvements: {len(analysis['recommendations']['long_term_improvements'])}")
    else:
        print(f"❌ Analysis failed: {analysis['error']}")

if __name__ == "__main__":
    demo_agent_integration()
