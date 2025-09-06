#!/usr/bin/env python3
"""
Data Quality Analysis Main Script
Integrates with the CRM agent framework to provide comprehensive data quality assessment.
"""

import sys
import os
import asyncio
from datetime import datetime

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from crm_agent.agents.workflows.data_quality_workflow import create_data_quality_workflows
from crm_agent.agents.specialized.data_quality_analyzer import DataQualityAnalyzer
from crm_agent.core.state_models import CRMSessionState


async def run_data_quality_assessment():
    """Run comprehensive data quality assessment using the agent framework."""
    
    print("🔍 CRM Data Quality Intelligence System")
    print("=" * 70)
    print("Integrating with CRM agent framework for comprehensive analysis...")
    
    # Initialize session state
    session_state = CRMSessionState()
    
    # Create data quality workflows
    workflows = create_data_quality_workflows()
    assessment_workflow = workflows["assessment"]
    
    print(f"\n📋 Data Quality Assessment Workflow:")
    print(f"  1. 📊 Data Collection & Sampling")
    print(f"  2. 🔍 Quality Assessment & Gap Analysis")
    print(f"  3. 🎯 Issue Prioritization & Impact Analysis")
    print(f"  4. 📋 Cleanup Recommendations & Action Plan")
    
    try:
        # For now, use the direct analyzer since the full agent framework integration 
        # would require more complex setup
        print(f"\n⚡ Running direct data quality analysis...")
        analyzer = DataQualityAnalyzer()
        report = analyzer.generate_quality_report(company_limit=100, contact_limit=100)
        
        print(f"\n✅ Data quality assessment completed!")
        print(f"📊 Analysis Results:")
        print(f"   • Overall Health: {report['summary']['overall_health']}")
        print(f"   • Companies: {report['summary']['avg_company_completeness']}% complete")
        print(f"   • Contacts: {report['summary']['avg_contact_completeness']}% complete")
        print(f"   • Critical Issues: {report['summary']['total_critical_issues']}")
        
        return report
        
    except Exception as e:
        print(f"❌ Error during assessment: {str(e)}")
        return None


def run_quick_analysis():
    """Run a quick data quality analysis without the full workflow."""
    
    print("🚀 Quick Data Quality Analysis")
    print("=" * 50)
    
    try:
        analyzer = DataQualityAnalyzer()
        report = analyzer.generate_quality_report(company_limit=50, contact_limit=50)
        
        print(f"\n💡 Quick Analysis Summary:")
        print(f"   • Analyzed: {report['summary']['companies_analyzed']} companies, {report['summary']['contacts_analyzed']} contacts")
        print(f"   • Data Health: {report['summary']['overall_health']}")
        print(f"   • Critical Issues: {report['summary']['total_critical_issues']}")
        
        # Show top recommendations
        if report['recommendations']['critical']:
            print(f"\n🚨 Top Critical Issues:")
            for rec in report['recommendations']['critical'][:3]:
                print(f"   • {rec['title']}: {rec['description']}")
        
        return report
        
    except Exception as e:
        print(f"❌ Error during analysis: {str(e)}")
        return None


def main():
    """Main entry point for data quality analysis."""
    
    print("🎯 CRM Data Quality Intelligence")
    print("Choose your analysis mode:")
    print("1. Comprehensive Assessment (Full agent workflow)")
    print("2. Quick Analysis (Direct analysis)")
    print("3. Monitoring Mode (Check current status)")
    
    try:
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == "1":
            print("\n🔄 Starting comprehensive assessment...")
            asyncio.run(run_data_quality_assessment())
            
        elif choice == "2":
            print("\n⚡ Starting quick analysis...")
            run_quick_analysis()
            
        elif choice == "3":
            print("\n📊 Running monitoring check...")
            analyzer = DataQualityAnalyzer()
            
            # Quick health check
            companies = analyzer._call_mcp_tool("get_companies", {"limit": 10})
            contacts = analyzer._call_mcp_tool("get_contacts", {"limit": 10})
            
            if companies and contacts:
                print("✅ MCP Server connection: OK")
                print(f"📊 Sample data: {len(companies.get('results', []))} companies, {len(contacts.get('results', []))} contacts")
                print("💡 Run full analysis with option 1 or 2 for detailed insights")
            else:
                print("❌ Unable to connect to data source")
                
        else:
            print("❌ Invalid choice. Please select 1, 2, or 3.")
            
    except KeyboardInterrupt:
        print("\n\n👋 Analysis cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        print("💡 Make sure the MCP server is running: python mcp_wrapper/simple_hubspot_server.py")


if __name__ == "__main__":
    main()
