#!/usr/bin/env python3
"""
Field Enrichment Manager Agent Demo

This script demonstrates how to use the Field Enrichment Manager Agent to:
1. Analyze field completeness for companies and contacts
2. Enrich missing fields systematically
3. Critique enrichment results and identify improvements
4. Document insights for process optimization

Usage:
    python field_enrichment_demo.py --company-id 12345
    python field_enrichment_demo.py --contact-email john@company.com
    python field_enrichment_demo.py --demo-mode
"""

import os
import sys
import argparse
import logging
from datetime import datetime

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crm_agent.core.factory import create_field_enrichment_manager_agent
from crm_agent.agents.specialized.field_enrichment_manager_agent import (
    EnrichmentStatus, ConfidenceLevel
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def demo_company_enrichment(agent, company_id: str):
    """Demonstrate company field enrichment"""
    
    print(f"\n🏢 Company Field Enrichment Demo")
    print(f"{'='*50}")
    print(f"Target Company ID: {company_id}")
    print()
    
    # Step 1: Enrich company fields using workflow orchestration
    print("📊 Step 1: Enriching Company Fields with Workflow Orchestration...")
    enrichment_results = agent.enrich_record_fields('company', company_id, dry_run=True, use_workflow=True)
    
    if not enrichment_results:
        print("❌ No enrichment results available")
        return
    
    # Step 2: Display enrichment results
    print(f"\n📋 Step 2: Enrichment Results ({len(enrichment_results)} fields processed)")
    print("-" * 60)
    
    for result in enrichment_results:
        status_emoji = "✅" if result.status == EnrichmentStatus.COMPLETE else "❌" if result.status == EnrichmentStatus.FAILED else "⏭️"
        confidence_emoji = "🔥" if result.confidence.value >= 80 else "👍" if result.confidence.value >= 60 else "⚠️"
        
        print(f"{status_emoji} {result.field_name}")
        print(f"   Status: {result.status.value}")
        print(f"   Confidence: {result.confidence.name} {confidence_emoji} ({result.confidence.value})")
        print(f"   Source: {result.source}")
        
        if result.new_value != result.old_value and result.new_value:
            print(f"   Old: {result.old_value or 'Empty'}")
            print(f"   New: {result.new_value}")
        
        if result.critique_notes:
            print(f"   Notes: {result.critique_notes}")
        
        print()
    
    # Step 3: Generate critique
    print("🔍 Step 3: Generating Enrichment Critique...")
    critique = agent.critique_enrichment_results(enrichment_results)
    
    print(f"\n📈 Enrichment Performance Analysis")
    print("-" * 40)
    print(f"Overall Score: {critique.overall_score:.1f}/100")
    print(f"Success Rate: {critique.success_rate:.1f}%")
    print(f"Total Fields: {len(enrichment_results)}")
    
    if critique.confidence_distribution:
        print(f"\nConfidence Distribution:")
        for conf_level, count in critique.confidence_distribution.items():
            percentage = (count / len(enrichment_results)) * 100
            print(f"  {conf_level}: {count} fields ({percentage:.1f}%)")
    
    if critique.common_failures:
        print(f"\nCommon Issues:")
        for i, failure in enumerate(critique.common_failures[:3], 1):
            print(f"  {i}. {failure}")
    
    if critique.recommendations:
        print(f"\nRecommendations:")
        for i, rec in enumerate(critique.recommendations[:3], 1):
            print(f"  {i}. {rec}")
    
    # Step 4: Document improvements
    print(f"\n💡 Step 4: Documenting Improvement Insights...")
    improvement_file = agent.document_improvement_insights(critique, 'company', company_id)
    
    if improvement_file:
        print(f"✅ Improvement insights documented in: {improvement_file}")
    else:
        print("⚠️ Could not save improvement documentation")
    
    # Step 5: Generate summary report
    print(f"\n📄 Step 5: Generating Summary Report...")
    summary_report = agent.generate_enrichment_summary_report(enrichment_results, critique)
    
    # Save summary report
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f"company_enrichment_report_{company_id}_{timestamp}.md"
    
    try:
        with open(report_file, 'w') as f:
            f.write(summary_report)
        print(f"✅ Summary report saved to: {report_file}")
    except Exception as e:
        print(f"⚠️ Could not save summary report: {e}")
    
    return enrichment_results, critique


def demo_contact_enrichment(agent, contact_email: str):
    """Demonstrate contact field enrichment"""
    
    print(f"\n👥 Contact Field Enrichment Demo")
    print(f"{'='*50}")
    print(f"Target Contact Email: {contact_email}")
    print()
    
    # For demo purposes, we'll simulate with a contact ID
    # In real usage, you'd search for the contact first
    print("📊 Step 1: Enriching Contact Fields...")
    enrichment_results = agent.enrich_record_fields('contact', 'demo_contact_id', dry_run=True)
    
    if not enrichment_results:
        print("❌ No enrichment results available")
        return
    
    # Display results (similar to company demo)
    print(f"\n📋 Step 2: Enrichment Results ({len(enrichment_results)} fields processed)")
    print("-" * 60)
    
    for result in enrichment_results:
        status_emoji = "✅" if result.status == EnrichmentStatus.COMPLETE else "❌" if result.status == EnrichmentStatus.FAILED else "⏭️"
        print(f"{status_emoji} {result.field_name}: {result.status.value}")
        
        if result.improvement_suggestions:
            print(f"   Suggestions: {', '.join(result.improvement_suggestions[:2])}")
        print()
    
    # Generate critique
    critique = agent.critique_enrichment_results(enrichment_results)
    print(f"\n📈 Contact Enrichment Performance: {critique.overall_score:.1f}/100 ({critique.success_rate:.1f}% success)")
    
    return enrichment_results, critique


def demo_company_enrichment_by_domain(agent, domain: str, company_id: str):
    """Demonstrate company field enrichment by finding company via domain first"""
    
    print(f"\n🏢 Company Field Enrichment Demo (Domain Search)")
    print(f"{'='*50}")
    print(f"Target Domain: {domain}")
    print(f"Expected Company ID: {company_id}")
    print()
    
    # First, find the company by domain
    print("🔍 Step 1: Finding company by domain...")
    
    try:
        # Create a modified agent method to search by domain
        search_result = agent.call_mcp_tool("search_companies", {
            "query": domain,
            "limit": 10
        })
        
        if search_result and "results" in search_result:
            for company in search_result["results"]:
                company_domain = company.get('properties', {}).get('domain', '')
                if domain in company_domain:
                    found_company_id = company.get('id')
                    company_name = company.get('properties', {}).get('name', 'Unknown')
                    print(f"✅ Found company: {company_name} (ID: {found_company_id})")
                    
                    # Now run enrichment on this company data directly
                    print(f"\n📊 Step 2: Enriching Fields for {company_name}...")
                    
                    # Manually call the enrichment with the found company data
                    enrichment_results = agent._enrich_with_company_data(company, dry_run=True)
                    
                    if enrichment_results:
                        # Display results (similar to original demo)
                        print(f"\n📋 Step 3: Enrichment Results ({len(enrichment_results)} fields processed)")
                        print("-" * 60)
                        
                        for result in enrichment_results:
                            status_emoji = "✅" if result.status.value == "✅ Complete" else "❌" if result.status.value == "❌ Failed" else "⏭️"
                            confidence_emoji = "🔥" if result.confidence.value >= 80 else "👍" if result.confidence.value >= 60 else "⚠️"
                            
                            print(f"{status_emoji} {result.field_name}")
                            print(f"   Status: {result.status.value}")
                            print(f"   Confidence: {result.confidence.name} {confidence_emoji} ({result.confidence.value})")
                            print(f"   Source: {result.source}")
                            
                            if result.new_value != result.old_value and result.new_value:
                                print(f"   Old: {result.old_value or 'Empty'}")
                                print(f"   New: {result.new_value}")
                            
                            if result.critique_notes:
                                print(f"   Notes: {result.critique_notes}")
                            
                            print()
                        
                        # Generate critique
                        critique = agent.critique_enrichment_results(enrichment_results)
                        print(f"\n📈 Enrichment Performance Analysis")
                        print("-" * 40)
                        print(f"Overall Score: {critique.overall_score:.1f}/100")
                        print(f"Success Rate: {critique.success_rate:.1f}%")
                        
                        # Document improvements
                        improvement_file = agent.document_improvement_insights(critique, 'company', found_company_id)
                        if improvement_file:
                            print(f"\n✅ Improvement insights documented")
                        
                        return enrichment_results, critique
                    
                    break
        
        print("❌ Could not find company with that domain")
        return None, None
        
    except Exception as e:
        print(f"❌ Error during domain search: {e}")
        return None, None


def demo_workflow_comparison(agent, company_id: str):
    """Demonstrate workflow performance comparison"""
    
    print(f"\n⚖️ Workflow Performance Comparison Demo")
    print(f"{'='*50}")
    print(f"Comparing different workflow types on company {company_id}")
    print()
    
    try:
        print("🔄 Running workflow performance comparison...")
        comparison = agent.compare_workflow_performance('company', company_id)
        
        print(f"\n📊 Comparison Results:")
        print(f"Best Workflow: {comparison['best_workflow']}")
        print(f"Best Score: {comparison['best_score']:.1f}")
        print()
        
        print("Workflow Performance Details:")
        for workflow_type, metrics in comparison['workflow_results'].items():
            if 'error' not in metrics:
                print(f"  {workflow_type}:")
                print(f"    Success Rate: {metrics['success_rate']:.1f}%")
                print(f"    Execution Time: {metrics['execution_time_seconds']:.2f}s")
                print(f"    Avg Confidence: {metrics['average_confidence']:.1f}")
            else:
                print(f"  {workflow_type}: FAILED - {metrics['error']}")
        
        return comparison
    
    except Exception as e:
        print(f"❌ Workflow comparison failed: {e}")
        return None


def demo_specific_workflow(agent, workflow_type: str, company_id: str):
    """Demonstrate a specific workflow type"""
    
    print(f"\n🔧 {workflow_type.title()} Workflow Demo")
    print(f"{'='*50}")
    
    try:
        print(f"🚀 Running {workflow_type} workflow...")
        results = agent.run_workflow_type(workflow_type, 'company', company_id, dry_run=True)
        
        print(f"\n📋 {workflow_type.title()} Results ({len(results)} fields):")
        
        success_count = len([r for r in results if r.status.value == "✅ Complete"])
        print(f"  Success Rate: {success_count}/{len(results)} ({success_count/len(results)*100:.1f}%)")
        
        for result in results[:5]:  # Show top 5 results
            status_emoji = "✅" if "Complete" in result.status.value else "❌" if "Failed" in result.status.value else "⏭️"
            print(f"  {status_emoji} {result.field_name}: {result.status.value}")
        
        if len(results) > 5:
            print(f"  ... and {len(results) - 5} more fields")
        
        return results
    
    except Exception as e:
        print(f"❌ {workflow_type} workflow failed: {e}")
        return []


def demo_field_analysis(agent):
    """Demonstrate field completeness analysis"""
    
    print(f"\n🔍 Field Completeness Analysis Demo")
    print(f"{'='*50}")
    
    # Simulate company data for analysis
    sample_company_data = {
        'properties': {
            'name': 'ACME Corporation',
            'website': 'https://acme.com',
            'industry': '',  # Missing
            'domain': '',    # Missing
            'description': '',  # Missing
            'annualrevenue': '5000000',
            'numberofemployees': '50'
        }
    }
    
    print("📊 Analyzing Company Field Completeness...")
    analysis = agent.analyze_field_completeness('company', sample_company_data)
    
    print(f"\nCompany Analysis Results:")
    print(f"  Total Fields: {analysis['total_fields']}")
    print(f"  Populated Fields: {analysis['populated_fields']}")
    print(f"  Completion Score: {analysis['completion_score']:.1f}%")
    
    if analysis['missing_critical']:
        print(f"  Missing Critical Fields: {', '.join(analysis['missing_critical'])}")
    if analysis['missing_high_priority']:
        print(f"  Missing High Priority Fields: {', '.join(analysis['missing_high_priority'])}")
    if analysis['missing_medium_low']:
        print(f"  Missing Medium/Low Priority Fields: {', '.join(analysis['missing_medium_low'])}")
    
    # Show field details
    print(f"\nField Details:")
    for field_name, details in analysis['field_details'].items():
        status = "✅" if details['populated'] else "❌"
        priority = details['priority']
        print(f"  {status} {details['name']} ({priority}): {details['current_value'] or 'Empty'}")


def main():
    """Main demo function"""
    
    parser = argparse.ArgumentParser(description='Field Enrichment Manager Agent Demo')
    parser.add_argument('--company-id', help='HubSpot company ID to enrich')
    parser.add_argument('--contact-email', help='Contact email to enrich')
    parser.add_argument('--demo-mode', action='store_true', help='Run comprehensive demo with simulated data')
    
    args = parser.parse_args()
    
    if not any([args.company_id, args.contact_email, args.demo_mode]):
        parser.print_help()
        sys.exit(1)
    
    print("🤖 Field Enrichment Manager Agent Demo")
    print("=" * 60)
    print("This demo showcases systematic field enrichment and quality improvement")
    print("for the top 10 most valuable CRM fields in the Swoop sales process.")
    print()
    
    # Create the agent
    try:
        agent = create_field_enrichment_manager_agent()
        print("✅ Field Enrichment Manager Agent initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        sys.exit(1)
    
    try:
        if args.demo_mode:
            print("\n🎯 Running Comprehensive Demo Mode...")
            
            # Demo 1: Field Analysis
            demo_field_analysis(agent)
            
            # Demo 2: Company Enrichment (simulated)
            print(f"\n" + "="*60)
            demo_company_enrichment(agent, "demo_company_123")
            
            # Demo 3: Workflow Comparison
            print(f"\n" + "="*60)
            demo_workflow_comparison(agent, "demo_company_123")
            
            # Demo 4: Specific Workflow Types
            print(f"\n" + "="*60)
            demo_specific_workflow(agent, "sequential", "demo_company_123")
            
            print(f"\n" + "="*60)
            demo_specific_workflow(agent, "parallel", "demo_company_123")
            
            # Demo 5: Contact Enrichment (simulated)
            print(f"\n" + "="*60)
            demo_contact_enrichment(agent, "demo@example.com")
            
        elif args.company_id:
            # Special handling for Louisville Country Club ID
            if args.company_id == "15537372824":
                print("\n🏌️ Special handling for Louisville Country Club")
                print("Searching by domain since direct ID search has pagination issues...")
                demo_company_enrichment_by_domain(agent, "loucc.net", args.company_id)
            else:
                demo_company_enrichment(agent, args.company_id)
            
        elif args.contact_email:
            demo_contact_enrichment(agent, args.contact_email)
        
        print(f"\n🎉 Demo completed successfully!")
        print(f"Review the generated reports and improvement documentation for insights.")
        
    except KeyboardInterrupt:
        print(f"\n⚠️ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        logger.error(f"Demo error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
