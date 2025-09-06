#!/usr/bin/env python3
"""
Usage Examples for CRM Cleanup Agent

This file demonstrates various ways to use the CRM cleanup agent
for different scenarios and use cases.
"""

from crm_cleanup_agent import CRMCleanupAgent
from crm_agent_integration import CRMCleanupIntegration
import json

def example_basic_usage():
    """Basic usage example - analyze all data and get report."""
    print("📋 Example 1: Basic CRM Cleanup Analysis")
    print("=" * 45)
    
    # Initialize the agent
    agent = CRMCleanupAgent()
    
    # Fetch data (adjust limits based on your CRM size)
    print("📥 Fetching CRM data...")
    contacts = agent.get_all_contacts(limit=200)
    companies = agent.get_all_companies(limit=100)
    
    if not contacts and not companies:
        print("❌ No data found. Make sure MCP server is running.")
        return
    
    # Generate comprehensive report
    print("🧮 Analyzing data quality...")
    report = agent.generate_cleanup_report(contacts, companies)
    
    # Display results
    agent.print_cleanup_report(report)

def example_targeted_duplicate_search():
    """Example focusing specifically on duplicate detection."""
    print("\n📋 Example 2: Targeted Duplicate Detection")
    print("=" * 45)
    
    agent = CRMCleanupAgent()
    
    # Adjust similarity threshold for more/fewer matches
    agent.similarity_threshold = 0.7  # Lower = more matches (less strict)
    
    print(f"🔍 Using similarity threshold: {agent.similarity_threshold}")
    
    contacts = agent.get_all_contacts(limit=300)
    companies = agent.get_all_companies(limit=150)
    
    if contacts:
        print(f"👥 Analyzing {len(contacts)} contacts for duplicates...")
        contact_duplicates = agent.find_duplicate_contacts(contacts)
        
        print(f"Found {len(contact_duplicates)} potential duplicate groups:")
        for i, dup in enumerate(contact_duplicates[:5], 1):  # Show first 5
            print(f"  {i}. {dup.primary_name} - {dup.match_type} match ({dup.similarity_score:.1%})")
            print(f"     Action: {dup.recommended_action}")
    
    if companies:
        print(f"\n🏢 Analyzing {len(companies)} companies for duplicates...")
        company_duplicates = agent.find_duplicate_companies(companies)
        
        print(f"Found {len(company_duplicates)} potential duplicate groups:")
        for i, dup in enumerate(company_duplicates[:5], 1):  # Show first 5
            print(f"  {i}. {dup.primary_name} - {dup.match_type} match ({dup.similarity_score:.1%})")
            print(f"     Action: {dup.recommended_action}")

def example_gap_analysis_focus():
    """Example focusing on data gap analysis."""
    print("\n📋 Example 3: Data Gap Analysis Focus")
    print("=" * 40)
    
    agent = CRMCleanupAgent()
    
    # Customize critical fields based on your business needs
    agent.critical_fields = {
        'contact': ['firstname', 'lastname', 'email', 'jobtitle', 'company', 'phone'],
        'company': ['name', 'domain', 'industry', 'website', 'city', 'country']
    }
    
    contacts = agent.get_all_contacts(limit=200)
    companies = agent.get_all_companies(limit=100)
    
    if contacts or companies:
        critical_gaps, moderate_gaps, minor_gaps = agent.analyze_data_gaps(contacts, companies)
        
        print(f"📊 Gap Analysis Results:")
        print(f"   Critical: {len(critical_gaps)} gaps")
        print(f"   Moderate: {len(moderate_gaps)} gaps") 
        print(f"   Minor: {len(minor_gaps)} gaps")
        
        # Show top critical gaps
        if critical_gaps:
            print(f"\n🚨 Top Critical Gaps:")
            for gap in critical_gaps[:10]:
                print(f"   • {gap.object_name} ({gap.object_type})")
                print(f"     Missing: {', '.join(gap.missing_fields)}")
                print(f"     Sources: {', '.join(gap.suggested_sources[:2])}")  # Show first 2 sources

def example_integration_usage():
    """Example using the integration layer for structured results."""
    print("\n📋 Example 4: Integration Layer Usage")
    print("=" * 40)
    
    integration = CRMCleanupIntegration()
    
    # Get structured analysis results
    print("🔍 Running structured analysis...")
    results = integration.analyze_crm_quality(
        contact_limit=150,
        company_limit=75,
        similarity_threshold=0.8
    )
    
    if "error" in results:
        print(f"❌ Analysis failed: {results['error']}")
        return
    
    # Display structured results
    summary = results["summary"]
    print(f"\n📊 Analysis Summary:")
    print(f"   Quality Score: {summary['data_quality_score']:.1%}")
    print(f"   Contacts: {summary['total_contacts_analyzed']}")
    print(f"   Companies: {summary['total_companies_analyzed']}")
    print(f"   Duplicates: {summary['potential_duplicate_contacts']} + {summary['potential_duplicate_companies']}")
    print(f"   Gaps: {summary['total_data_gaps']}")
    
    # Show quick wins
    quick_wins = results["recommendations"]["quick_wins"]
    if quick_wins:
        print(f"\n⚡ Quick Wins Available:")
        for win in quick_wins:
            print(f"   • {win['description']} ({win['estimated_time_minutes']} min)")

def example_custom_workflow():
    """Example of a custom workflow for specific business needs."""
    print("\n📋 Example 5: Custom Business Workflow")
    print("=" * 40)
    
    agent = CRMCleanupAgent()
    
    # Step 1: Quick health check
    print("🏥 Step 1: CRM Health Check...")
    contacts = agent.get_all_contacts(limit=50)  # Small sample
    companies = agent.get_all_companies(limit=25)
    
    if not contacts and not companies:
        print("❌ Cannot perform health check - no data available")
        return
    
    report = agent.generate_cleanup_report(contacts, companies)
    health_score = report.data_quality_score
    
    print(f"   Health Score: {health_score:.1%}")
    
    # Step 2: Decide on action based on health score
    if health_score < 0.6:
        print("🚨 Step 2: Critical Issues Detected - Full Analysis Required")
        
        # Full analysis for critical issues
        contacts = agent.get_all_contacts(limit=500)
        companies = agent.get_all_companies(limit=250)
        full_report = agent.generate_cleanup_report(contacts, companies)
        
        print(f"   Full Analysis Complete:")
        print(f"   - Duplicates: {full_report.potential_duplicate_contacts + full_report.potential_duplicate_companies}")
        print(f"   - Critical Gaps: {len(full_report.critical_gaps)}")
        print(f"   - Estimated Fix Time: {full_report.estimated_cleanup_time}")
        
    elif health_score < 0.8:
        print("⚠️  Step 2: Moderate Issues - Targeted Cleanup")
        
        # Focus on duplicates only
        contact_duplicates = agent.find_duplicate_contacts(contacts)
        company_duplicates = agent.find_duplicate_companies(companies)
        
        print(f"   Duplicate Analysis:")
        print(f"   - Contact groups: {len(contact_duplicates)}")
        print(f"   - Company groups: {len(company_duplicates)}")
        
    else:
        print("✅ Step 2: Good Health - Maintenance Mode")
        print("   - Regular monitoring recommended")
        print("   - Focus on minor gap filling")

def example_export_and_action_plan():
    """Example showing how to export results and create action plans."""
    print("\n📋 Example 6: Export and Action Planning")
    print("=" * 45)
    
    agent = CRMCleanupAgent()
    
    # Generate report
    contacts = agent.get_all_contacts(limit=100)
    companies = agent.get_all_companies(limit=50)
    
    if not contacts and not companies:
        print("❌ No data for export example")
        return
    
    report = agent.generate_cleanup_report(contacts, companies)
    
    # Create custom export
    export_data = {
        "analysis_date": report.analysis_timestamp.isoformat(),
        "summary": {
            "quality_score": report.data_quality_score,
            "total_issues": len(report.duplicate_contacts) + len(report.duplicate_companies) + report.total_data_gaps,
            "estimated_time": report.estimated_cleanup_time
        },
        "high_priority_duplicates": [
            {
                "type": "contact",
                "primary_name": dup.primary_name,
                "primary_email": dup.primary_email,
                "duplicate_count": len(dup.duplicate_ids),
                "confidence": dup.similarity_score
            }
            for dup in report.duplicate_contacts if dup.similarity_score >= 0.9
        ],
        "critical_gaps_by_type": {}
    }
    
    # Group critical gaps by object type
    for gap in report.critical_gaps:
        obj_type = gap.object_type
        if obj_type not in export_data["critical_gaps_by_type"]:
            export_data["critical_gaps_by_type"][obj_type] = []
        
        export_data["critical_gaps_by_type"][obj_type].append({
            "name": gap.object_name,
            "missing_fields": gap.missing_fields,
            "importance": gap.importance_score
        })
    
    # Save to file
    filename = f"crm_analysis_{report.analysis_timestamp.strftime('%Y%m%d_%H%M%S')}.json"
    try:
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        print(f"✅ Analysis exported to: {filename}")
    except Exception as e:
        print(f"❌ Export failed: {str(e)}")
    
    # Create action plan
    print(f"\n📋 3-Phase Action Plan:")
    
    # Phase 1: High-confidence duplicates (immediate)
    high_conf_dups = [d for d in report.duplicate_contacts + report.duplicate_companies if d.similarity_score >= 0.95]
    if high_conf_dups:
        print(f"   Phase 1 (This Week): Merge {len(high_conf_dups)} high-confidence duplicates")
    
    # Phase 2: Critical gaps (next 2 weeks)
    if report.critical_gaps:
        print(f"   Phase 2 (Next 2 Weeks): Fill {len(report.critical_gaps)} critical data gaps")
    
    # Phase 3: Remaining issues (ongoing)
    remaining_issues = len(report.duplicate_contacts) + len(report.duplicate_companies) - len(high_conf_dups)
    if remaining_issues > 0:
        print(f"   Phase 3 (Ongoing): Review {remaining_issues} moderate-confidence duplicates")

def main():
    """Run all usage examples."""
    print("🧹 CRM Cleanup Agent - Usage Examples")
    print("=" * 50)
    
    print("\n💡 These examples demonstrate different ways to use the CRM cleanup agent.")
    print("Make sure the MCP server is running before running these examples.\n")
    
    try:
        # Run examples (comment out ones you don't want to run)
        example_basic_usage()
        example_targeted_duplicate_search()
        example_gap_analysis_focus()
        example_integration_usage()
        example_custom_workflow()
        example_export_and_action_plan()
        
        print(f"\n✅ All examples completed!")
        
    except KeyboardInterrupt:
        print(f"\n⏹️  Examples interrupted by user")
    except Exception as e:
        print(f"\n❌ Example failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
