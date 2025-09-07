"""
Test Field Mapping Agent with Business Rules and Context
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from crm_agent.agents.specialized.field_mapping_agent import FieldMappingAgent


def test_business_context():
    """Test business context retrieval for fields."""
    
    print("🧪 Testing Field Business Context & Rules")
    print("=" * 70)
    
    agent = FieldMappingAgent()
    
    # Test key business fields
    test_fields = [
        "competitor", "email_pattern", "management_company", 
        "company_type", "ngf_category", "description"
    ]
    
    for field in test_fields:
        print(f"\n📋 Field: {field}")
        print("-" * 40)
        
        context = agent.get_field_business_context(field)
        if context:
            print(f"🎯 Purpose: {context.get('purpose', 'N/A')}")
            print(f"💼 Business Value: {context.get('business_value', 'N/A')}")
            
            if 'swoop_competitors' in context:
                competitors = context['swoop_competitors'][:5]  # Show first 5
                print(f"🏆 Key Competitors: {', '.join(competitors)}")
                
            if 'valid_options' in context:
                options = context['valid_options']
                print(f"✅ Valid Options: {', '.join(options)}")
                
        else:
            print("❌ No business context found")


def test_field_validation():
    """Test field value validation against business rules."""
    
    print(f"\n🔍 Testing Field Value Validation")
    print("=" * 70)
    
    agent = FieldMappingAgent()
    
    # Test competitor field validation
    competitor_tests = [
        ("competitor", "Club Essentials", "Should flag as Swoop competitor"),
        ("competitor", "Unknown", "Should flag as high-priority prospect"),
        ("competitor", "In-House App", "Should flag as medium priority"),
        ("competitor", "Some Random System", "Should be neutral")
    ]
    
    for field, value, expected in competitor_tests:
        print(f"\n🧪 Testing: {field} = '{value}'")
        print(f"Expected: {expected}")
        
        result = agent.validate_field_value(field, value)
        
        print(f"Status: {result['status']}")
        print(f"Purpose: {result.get('business_purpose', 'N/A')}")
        
        if result.get('warnings'):
            print(f"⚠️ Warnings: {'; '.join(result['warnings'])}")
            
        if result.get('suggestions'):
            print(f"💡 Suggestions: {'; '.join(result['suggestions'])}")
            
        if result.get('sales_priority'):
            print(f"🎯 Sales Priority: {result['sales_priority']}")
        
        print("-" * 50)
    
    # Test email pattern validation
    email_tests = [
        ("email_pattern", "@clubname.com", "Should be valid"),
        ("email_pattern", "clubname.com", "Should suggest adding @"),
        ("email_pattern", "@mansionridgegc.com", "Should be valid")
    ]
    
    print(f"\n📧 Email Pattern Validation:")
    for field, value, expected in email_tests:
        print(f"\n🧪 Testing: {field} = '{value}'")
        result = agent.validate_field_value(field, value)
        
        if result.get('warnings'):
            print(f"⚠️ Warnings: {'; '.join(result['warnings'])}")
        if result.get('suggestions'):
            print(f"💡 Suggestions: {'; '.join(result['suggestions'])}")


def test_enrichment_strategy():
    """Test enrichment strategy generation."""
    
    print(f"\n📊 Testing Enrichment Strategy Generation")
    print("=" * 70)
    
    agent = FieldMappingAgent()
    
    # Simulate company data with missing fields
    test_companies = [
        {
            "name": "Test Golf Club 1",
            "competitor": "Unknown",  # Missing critical field
            "management_company": "",  # Missing critical field
            "description": "Some description"  # Has this field
        },
        {
            "name": "Test Golf Club 2", 
            "competitor": "Club Essentials",  # Has competitor (Swoop competitor)
            "management_company": "Troon",  # Has management company
            "company_type": "Golf Club",  # Has company type
            "email_pattern": "@testclub.com"  # Has email pattern
        }
    ]
    
    for i, company_data in enumerate(test_companies, 1):
        print(f"\n🏌️ Company {i}: {company_data['name']}")
        print("-" * 50)
        
        strategy = agent.get_enrichment_strategy(company_data)
        
        if strategy.get("critical_missing"):
            print(f"🔥 CRITICAL Missing Fields:")
            for field_info in strategy["critical_missing"]:
                print(f"   • {field_info['field']}: {field_info['business_impact']}")
        
        if strategy.get("high_value_missing"):
            print(f"⚡ HIGH VALUE Missing Fields:")
            for field_info in strategy["high_value_missing"]:
                print(f"   • {field_info['field']}: {field_info['business_impact']}")
        
        if strategy.get("supplementary_missing"):
            print(f"📋 SUPPLEMENTARY Missing Fields:")
            for field_info in strategy["supplementary_missing"]:
                print(f"   • {field_info['field']}: {field_info['business_impact']}")
        
        if strategy.get("recommendations"):
            print(f"\n💡 RECOMMENDATIONS:")
            for rec in strategy["recommendations"]:
                print(f"   • {rec}")


def test_swoop_competitor_analysis():
    """Test specific Swoop Golf competitor analysis."""
    
    print(f"\n🏆 Testing Swoop Golf Competitor Analysis")
    print("=" * 70)
    
    agent = FieldMappingAgent()
    
    # Get competitor context
    context = agent.get_field_business_context("competitor")
    if context and 'swoop_competitors' in context:
        competitors = context['swoop_competitors']
        
        print(f"📋 Swoop Golf Competitors ({len(competitors)} total):")
        for i, competitor in enumerate(competitors, 1):
            print(f"   {i:2d}. {competitor}")
        
        print(f"\n🎯 Sales Priority Analysis:")
        
        # Test each competitor type
        test_scenarios = [
            ("Unknown", "🟢 HIGH PRIORITY - No existing solution"),
            ("Club Essentials", "🟡 LOW-MEDIUM - Major competitor, needs competitive approach"),
            ("Jonas", "🟡 LOW-MEDIUM - Established competitor"),
            ("In-House App", "🟠 MEDIUM - Custom solution, may be open to upgrade"),
            ("ForeTees", "🟡 LOW-MEDIUM - Direct competitor")
        ]
        
        for competitor, expected_priority in test_scenarios:
            validation = agent.validate_field_value("competitor", competitor)
            priority = validation.get("sales_priority", "Not specified")
            print(f"   • {competitor:15} → Priority: {priority}")


if __name__ == "__main__":
    test_business_context()
    test_field_validation() 
    test_enrichment_strategy()
    test_swoop_competitor_analysis()
