#!/usr/bin/env python3
"""
Quick test script for CRM Cleanup Agent
"""

import json
from crm_cleanup_agent import CRMCleanupAgent, DuplicateContact, DuplicateCompany, DataGap

def test_duplicate_detection():
    """Test duplicate detection algorithms with sample data."""
    print("🧪 Testing Duplicate Detection Algorithms")
    print("=" * 45)
    
    agent = CRMCleanupAgent()
    
    # Sample contact data with duplicates
    sample_contacts = [
        {
            "id": "1",
            "properties": {
                "firstname": "John",
                "lastname": "Smith", 
                "email": "john.smith@example.com",
                "phone": "555-1234",
                "jobtitle": "Manager"
            }
        },
        {
            "id": "2",
            "properties": {
                "firstname": "John",
                "lastname": "Smith",
                "email": "john.smith@example.com",  # Exact email match
                "phone": "555-1234",
                "jobtitle": "Senior Manager"
            }
        },
        {
            "id": "3", 
            "properties": {
                "firstname": "Jane",
                "lastname": "Doe",
                "email": "jane.doe@company.com",
                "phone": "555-5678"
            }
        },
        {
            "id": "4",
            "properties": {
                "firstname": "Jon",  # Similar name
                "lastname": "Smith",
                "email": "jon.smith@different.com",
                "phone": "555-9999"
            }
        }
    ]
    
    # Sample company data with duplicates
    sample_companies = [
        {
            "id": "1",
            "properties": {
                "name": "Acme Corporation",
                "domain": "acme.com",
                "industry": "Technology",
                "city": "New York"
            }
        },
        {
            "id": "2",
            "properties": {
                "name": "ACME Corp",  # Similar name
                "domain": "acme.com",  # Exact domain match
                "industry": "Tech",
                "city": "NYC"
            }
        },
        {
            "id": "3",
            "properties": {
                "name": "Beta Industries",
                "domain": "beta.com",
                "industry": "Manufacturing"
            }
        }
    ]
    
    print("📊 Sample Data:")
    print(f"   Contacts: {len(sample_contacts)}")
    print(f"   Companies: {len(sample_companies)}")
    
    # Test duplicate detection
    contact_duplicates = agent.find_duplicate_contacts(sample_contacts)
    company_duplicates = agent.find_duplicate_companies(sample_companies)
    
    print(f"\n🔍 Duplicate Detection Results:")
    print(f"   Contact Duplicate Groups: {len(contact_duplicates)}")
    print(f"   Company Duplicate Groups: {len(company_duplicates)}")
    
    # Display results
    if contact_duplicates:
        print(f"\n👥 Contact Duplicates:")
        for i, dup in enumerate(contact_duplicates, 1):
            print(f"   {i}. {dup.primary_name} ({dup.primary_email})")
            print(f"      Match Type: {dup.match_type}")
            print(f"      Similarity: {dup.similarity_score:.1%}")
            print(f"      Duplicates: {len(dup.duplicate_ids)}")
    
    if company_duplicates:
        print(f"\n🏢 Company Duplicates:")
        for i, dup in enumerate(company_duplicates, 1):
            print(f"   {i}. {dup.primary_name} ({dup.primary_domain})")
            print(f"      Match Type: {dup.match_type}")
            print(f"      Similarity: {dup.similarity_score:.1%}")
            print(f"      Duplicates: {len(dup.duplicate_ids)}")
    
    return contact_duplicates, company_duplicates

def test_gap_analysis():
    """Test gap analysis with sample data."""
    print("\n🧪 Testing Gap Analysis")
    print("=" * 25)
    
    agent = CRMCleanupAgent()
    
    # Sample data with various gaps
    sample_contacts = [
        {
            "id": "1",
            "properties": {
                "firstname": "John",
                "lastname": "Smith",
                "email": "john.smith@example.com",
                "phone": "555-1234",
                "jobtitle": "Manager",
                "company": "Acme Corp"
            }
        },
        {
            "id": "2", 
            "properties": {
                "firstname": "Jane",
                "lastname": "Doe",
                # Missing email (critical)
                "phone": "555-5678"
                # Missing jobtitle, company
            }
        },
        {
            "id": "3",
            "properties": {
                "email": "unknown@example.com"
                # Missing firstname, lastname (critical)
            }
        }
    ]
    
    sample_companies = [
        {
            "id": "1",
            "properties": {
                "name": "Acme Corporation",
                "domain": "acme.com",
                "industry": "Technology",
                "city": "New York",
                "state": "NY",
                "country": "US"
            }
        },
        {
            "id": "2",
            "properties": {
                "name": "Beta Industries"
                # Missing domain, industry (critical)
                # Missing location info
            }
        }
    ]
    
    critical_gaps, moderate_gaps, minor_gaps = agent.analyze_data_gaps(sample_contacts, sample_companies)
    
    print(f"📊 Gap Analysis Results:")
    print(f"   Critical Gaps: {len(critical_gaps)}")
    print(f"   Moderate Gaps: {len(moderate_gaps)}")
    print(f"   Minor Gaps: {len(minor_gaps)}")
    
    if critical_gaps:
        print(f"\n🚨 Critical Gaps:")
        for gap in critical_gaps:
            print(f"   • {gap.object_name} ({gap.object_type})")
            print(f"     Missing: {', '.join(gap.missing_fields)}")
            print(f"     Importance: {gap.importance_score:.1%}")
            print(f"     Sources: {', '.join(gap.suggested_sources)}")
    
    return critical_gaps, moderate_gaps, minor_gaps

def test_similarity_calculation():
    """Test string similarity calculation."""
    print("\n🧪 Testing Similarity Calculation")
    print("=" * 35)
    
    agent = CRMCleanupAgent()
    
    test_pairs = [
        ("John Smith", "John Smith"),  # Exact match
        ("John Smith", "Jon Smith"),   # Minor difference
        ("ACME Corporation", "Acme Corp"),  # Case and abbreviation
        ("Microsoft Corporation", "Apple Inc."),  # Different companies
        ("", "John Smith"),  # Empty string
        ("J. Smith", "John Smith")  # Abbreviated
    ]
    
    print("String Similarity Tests:")
    for s1, s2 in test_pairs:
        similarity = agent.calculate_similarity(s1, s2)
        print(f"   '{s1}' vs '{s2}': {similarity:.1%}")

def test_full_workflow():
    """Test the complete workflow with sample data."""
    print("\n🧪 Testing Full Cleanup Workflow")
    print("=" * 35)
    
    agent = CRMCleanupAgent()
    
    # Combined sample data
    contacts = [
        {"id": "1", "properties": {"firstname": "John", "lastname": "Smith", "email": "john@acme.com", "company": "Acme Corp"}},
        {"id": "2", "properties": {"firstname": "John", "lastname": "Smith", "email": "john@acme.com", "jobtitle": "Manager"}},
        {"id": "3", "properties": {"firstname": "Jane", "email": "jane@beta.com"}},
        {"id": "4", "properties": {"email": "unknown@test.com"}}
    ]
    
    companies = [
        {"id": "1", "properties": {"name": "Acme Corporation", "domain": "acme.com", "industry": "Tech"}},
        {"id": "2", "properties": {"name": "Acme Corp", "domain": "acme.com", "city": "NYC"}},
        {"id": "3", "properties": {"name": "Beta Industries"}}
    ]
    
    # Generate full report
    report = agent.generate_cleanup_report(contacts, companies)
    
    print(f"📊 Full Workflow Results:")
    print(f"   Data Quality Score: {report.data_quality_score:.1%}")
    print(f"   Duplicate Contacts: {report.potential_duplicate_contacts}")
    print(f"   Duplicate Companies: {report.potential_duplicate_companies}")
    print(f"   Total Gaps: {report.total_data_gaps}")
    print(f"   Estimated Cleanup Time: {report.estimated_cleanup_time}")
    
    if report.priority_actions:
        print(f"\n🎯 Priority Actions:")
        for i, action in enumerate(report.priority_actions, 1):
            print(f"   {i}. {action}")
    
    return report

def main():
    """Run all tests."""
    print("🧹 CRM Cleanup Agent Test Suite")
    print("=" * 40)
    
    try:
        # Test individual components
        test_similarity_calculation()
        test_duplicate_detection()
        test_gap_analysis()
        test_full_workflow()
        
        print(f"\n✅ All tests completed successfully!")
        print(f"\n💡 To test with real HubSpot data:")
        print(f"   1. Start MCP server: python mcp_wrapper/simple_hubspot_server.py")
        print(f"   2. Run demo: python crm_cleanup_demo.py")
        print(f"   3. Or run agent: python crm_cleanup_agent.py")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
