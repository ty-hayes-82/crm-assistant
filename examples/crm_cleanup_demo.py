#!/usr/bin/env python3
"""
Demo script for CRM Cleanup Agent

This script demonstrates the CRM cleanup agent's capabilities for
identifying duplicates and data gaps in your HubSpot CRM.
"""

import sys
import os
from crm_cleanup_agent import CRMCleanupAgent, CleanupReport

def demo_interactive_cleanup():
    """Interactive demo of CRM cleanup capabilities."""
    print("🧹 CRM Cleanup Agent Demo")
    print("=" * 50)
    
    print("\nThis demo will analyze your HubSpot CRM data to:")
    print("• Identify potential duplicate contacts and companies")
    print("• Find critical data gaps that need attention")
    print("• Provide actionable cleanup recommendations")
    
    # Check if MCP server is running
    agent = CRMCleanupAgent()
    
    # Test connection
    print("\n🔗 Testing connection to MCP server...")
    test_result = agent.make_mcp_request("get_account_info", {})
    
    if "error" in test_result:
        print("❌ Cannot connect to MCP server")
        print("💡 Make sure the server is running: python mcp_wrapper/simple_hubspot_server.py")
        return
    
    print("✅ Connected to HubSpot successfully!")
    
    # Get user preferences
    print("\n⚙️  Configuration Options:")
    
    try:
        max_contacts = int(input("Maximum contacts to analyze (default 200): ") or "200")
        max_companies = int(input("Maximum companies to analyze (default 200): ") or "200")
    except ValueError:
        max_contacts = 200
        max_companies = 200
    
    similarity_threshold = input("Similarity threshold for duplicates (0.8): ") or "0.8"
    try:
        agent.similarity_threshold = float(similarity_threshold)
    except ValueError:
        agent.similarity_threshold = 0.8
    
    print(f"\n📊 Analysis Configuration:")
    print(f"   Max Contacts: {max_contacts}")
    print(f"   Max Companies: {max_companies}")
    print(f"   Similarity Threshold: {agent.similarity_threshold}")
    
    # Perform analysis
    print("\n🔍 Starting comprehensive analysis...")
    
    print("📥 Fetching contact data...")
    contacts = agent.get_all_contacts(limit=max_contacts)
    
    print("📥 Fetching company data...")
    companies = agent.get_all_companies(limit=max_companies)
    
    if not contacts and not companies:
        print("❌ No data found. Check your HubSpot configuration.")
        return
    
    print(f"✅ Retrieved {len(contacts)} contacts and {len(companies)} companies")
    
    # Generate comprehensive report
    print("\n🧮 Generating cleanup report...")
    report = agent.generate_cleanup_report(contacts, companies)
    
    # Display results
    agent.print_cleanup_report(report)
    
    # Interactive options
    print("\n🔧 What would you like to do next?")
    print("1. View detailed duplicate analysis")
    print("2. View detailed gap analysis") 
    print("3. Export recommendations to file")
    print("4. Generate action plan")
    print("5. Exit")
    
    choice = input("\nEnter your choice (1-5): ").strip()
    
    if choice == "1":
        show_detailed_duplicates(report)
    elif choice == "2":
        show_detailed_gaps(report)
    elif choice == "3":
        export_recommendations(report)
    elif choice == "4":
        generate_action_plan(report)
    else:
        print("👋 Thanks for using CRM Cleanup Agent!")

def show_detailed_duplicates(report: CleanupReport):
    """Show detailed duplicate analysis."""
    print("\n" + "=" * 80)
    print("🔍 DETAILED DUPLICATE ANALYSIS")
    print("=" * 80)
    
    if report.duplicate_contacts:
        print(f"\n👥 ALL DUPLICATE CONTACTS ({len(report.duplicate_contacts)})")
        for i, dup in enumerate(report.duplicate_contacts, 1):
            print(f"\n{i}. PRIMARY: {dup.primary_name}")
            print(f"   Email: {dup.primary_email}")
            print(f"   ID: {dup.primary_id}")
            print(f"   DUPLICATES ({len(dup.duplicate_ids)}):")
            
            for j, (dup_id, dup_name, dup_email) in enumerate(zip(dup.duplicate_ids, dup.duplicate_names, dup.duplicate_emails), 1):
                print(f"     {j}. {dup_name} - {dup_email} (ID: {dup_id})")
            
            print(f"   Match Type: {dup.match_type}")
            print(f"   Similarity: {dup.similarity_score:.1%}")
            print(f"   Recommended Action: {dup.recommended_action}")
    
    if report.duplicate_companies:
        print(f"\n🏢 ALL DUPLICATE COMPANIES ({len(report.duplicate_companies)})")
        for i, dup in enumerate(report.duplicate_companies, 1):
            print(f"\n{i}. PRIMARY: {dup.primary_name}")
            print(f"   Domain: {dup.primary_domain}")
            print(f"   ID: {dup.primary_id}")
            print(f"   DUPLICATES ({len(dup.duplicate_ids)}):")
            
            for j, (dup_id, dup_name, dup_domain) in enumerate(zip(dup.duplicate_ids, dup.duplicate_names, dup.duplicate_domains), 1):
                print(f"     {j}. {dup_name} - {dup_domain} (ID: {dup_id})")
            
            print(f"   Match Type: {dup.match_type}")
            print(f"   Similarity: {dup.similarity_score:.1%}")
            print(f"   Recommended Action: {dup.recommended_action}")

def show_detailed_gaps(report: CleanupReport):
    """Show detailed gap analysis."""
    print("\n" + "=" * 80)
    print("📋 DETAILED GAP ANALYSIS")
    print("=" * 80)
    
    all_gaps = [
        ("🚨 CRITICAL", report.critical_gaps),
        ("⚠️  MODERATE", report.moderate_gaps),
        ("ℹ️  MINOR", report.minor_gaps)
    ]
    
    for category, gaps in all_gaps:
        if gaps:
            print(f"\n{category} GAPS ({len(gaps)})")
            for i, gap in enumerate(gaps, 1):
                print(f"\n{i}. {gap.object_name} ({gap.object_type.upper()})")
                print(f"   ID: {gap.object_id}")
                print(f"   Missing Fields: {', '.join(gap.missing_fields)}")
                print(f"   Importance Score: {gap.importance_score:.1%}")
                print(f"   Suggested Sources: {', '.join(gap.suggested_sources)}")

def export_recommendations(report: CleanupReport):
    """Export recommendations to a file."""
    filename = f"crm_cleanup_recommendations_{report.analysis_timestamp.strftime('%Y%m%d_%H%M%S')}.txt"
    
    try:
        with open(filename, 'w') as f:
            f.write("CRM CLEANUP RECOMMENDATIONS\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Analysis Date: {report.analysis_timestamp}\n")
            f.write(f"Data Quality Score: {report.data_quality_score:.1%}\n\n")
            
            f.write("PRIORITY ACTIONS:\n")
            for i, action in enumerate(report.priority_actions, 1):
                f.write(f"{i}. {action}\n")
            f.write(f"\nEstimated Time: {report.estimated_cleanup_time}\n\n")
            
            f.write("DUPLICATE CONTACTS:\n")
            for dup in report.duplicate_contacts:
                f.write(f"- {dup.primary_name} ({dup.primary_email}): {len(dup.duplicate_ids)} duplicates\n")
                f.write(f"  Action: {dup.recommended_action}\n")
            
            f.write(f"\nDUPLICATE COMPANIES:\n")
            for dup in report.duplicate_companies:
                f.write(f"- {dup.primary_name} ({dup.primary_domain}): {len(dup.duplicate_ids)} duplicates\n")
                f.write(f"  Action: {dup.recommended_action}\n")
            
            f.write(f"\nCRITICAL DATA GAPS:\n")
            for gap in report.critical_gaps:
                f.write(f"- {gap.object_name} ({gap.object_type}): Missing {', '.join(gap.missing_fields)}\n")
                f.write(f"  Sources: {', '.join(gap.suggested_sources)}\n")
        
        print(f"✅ Recommendations exported to: {filename}")
        
    except Exception as e:
        print(f"❌ Error exporting recommendations: {str(e)}")

def generate_action_plan(report: CleanupReport):
    """Generate a prioritized action plan."""
    print("\n" + "=" * 80)
    print("📋 CRM CLEANUP ACTION PLAN")
    print("=" * 80)
    
    print(f"\n🎯 OBJECTIVES:")
    print(f"   Current Data Quality Score: {report.data_quality_score:.1%}")
    print(f"   Target: 90%+ data quality")
    print(f"   Estimated Time Investment: {report.estimated_cleanup_time}")
    
    print(f"\n📈 PHASE 1: QUICK WINS (Week 1)")
    
    # High-confidence duplicates
    high_confidence_contacts = [d for d in report.duplicate_contacts if d.similarity_score >= 0.95]
    high_confidence_companies = [d for d in report.duplicate_companies if d.similarity_score >= 0.95]
    
    if high_confidence_contacts:
        print(f"   1. Merge {len(high_confidence_contacts)} high-confidence duplicate contacts")
        print(f"      Time: {len(high_confidence_contacts) * 3} minutes")
    
    if high_confidence_companies:
        print(f"   2. Merge {len(high_confidence_companies)} high-confidence duplicate companies")
        print(f"      Time: {len(high_confidence_companies) * 3} minutes")
    
    # Critical gaps with easy sources
    easy_critical_gaps = [g for g in report.critical_gaps if 'LinkedIn' in g.suggested_sources or 'Company website' in g.suggested_sources]
    if easy_critical_gaps:
        print(f"   3. Fill {len(easy_critical_gaps)} critical gaps from LinkedIn/websites")
        print(f"      Time: {len(easy_critical_gaps) * 2} minutes")
    
    print(f"\n📊 PHASE 2: SYSTEMATIC CLEANUP (Week 2-3)")
    
    if len(report.duplicate_contacts) > len(high_confidence_contacts):
        remaining_contact_dups = len(report.duplicate_contacts) - len(high_confidence_contacts)
        print(f"   1. Review and merge {remaining_contact_dups} moderate-confidence contact duplicates")
        print(f"      Time: {remaining_contact_dups * 5} minutes")
    
    if len(report.duplicate_companies) > len(high_confidence_companies):
        remaining_company_dups = len(report.duplicate_companies) - len(high_confidence_companies)
        print(f"   2. Review and merge {remaining_company_dups} moderate-confidence company duplicates")
        print(f"      Time: {remaining_company_dups * 5} minutes")
    
    if len(report.critical_gaps) > len(easy_critical_gaps):
        remaining_critical_gaps = len(report.critical_gaps) - len(easy_critical_gaps)
        print(f"   3. Research and fill {remaining_critical_gaps} remaining critical gaps")
        print(f"      Time: {remaining_critical_gaps * 5} minutes")
    
    print(f"\n🔧 PHASE 3: OPTIMIZATION (Week 4)")
    
    if report.moderate_gaps:
        print(f"   1. Address {min(len(report.moderate_gaps), 50)} moderate data gaps")
        print(f"      Time: {min(len(report.moderate_gaps), 50) * 2} minutes")
    
    print(f"   2. Implement data quality processes to prevent future issues")
    print(f"   3. Set up regular cleanup reviews (monthly)")
    
    print(f"\n📈 EXPECTED OUTCOMES:")
    estimated_improvement = min(0.3, (len(report.duplicate_contacts) + len(report.duplicate_companies)) * 0.02 + len(report.critical_gaps) * 0.01)
    target_score = min(0.95, report.data_quality_score + estimated_improvement)
    print(f"   Data Quality Score: {report.data_quality_score:.1%} → {target_score:.1%}")
    print(f"   Duplicate Records: -{len(report.duplicate_contacts) + len(report.duplicate_companies)}")
    print(f"   Critical Gaps: -{len(report.critical_gaps)}")

def quick_analysis():
    """Quick analysis mode for fast insights."""
    print("⚡ Quick CRM Analysis Mode")
    print("=" * 30)
    
    agent = CRMCleanupAgent()
    
    # Smaller sample for quick analysis
    print("📥 Fetching sample data...")
    contacts = agent.get_all_contacts(limit=100)
    companies = agent.get_all_companies(limit=100)
    
    if not contacts and not companies:
        print("❌ No data retrieved. Check MCP server connection.")
        return
    
    report = agent.generate_cleanup_report(contacts, companies)
    
    print(f"\n⚡ QUICK INSIGHTS:")
    print(f"   Data Quality Score: {report.data_quality_score:.1%}")
    print(f"   Potential Duplicates: {report.potential_duplicate_contacts + report.potential_duplicate_companies}")
    print(f"   Critical Gaps: {len(report.critical_gaps)}")
    print(f"   Estimated Cleanup Time: {report.estimated_cleanup_time}")
    
    if report.priority_actions:
        print(f"\n🎯 TOP PRIORITY:")
        print(f"   {report.priority_actions[0]}")

def main():
    """Main function with mode selection."""
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        quick_analysis()
    else:
        demo_interactive_cleanup()

if __name__ == "__main__":
    main()
