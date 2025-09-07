"""
Business Rules Enrichment Demo
Demonstrates how the Field Mapping Agent applies Swoop Golf business rules
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from crm_agent.agents.specialized.field_mapping_agent import FieldMappingAgent


def demo_competitor_analysis():
    """Demonstrate competitor analysis with business context."""
    
    print("🏆 SWOOP GOLF COMPETITOR ANALYSIS DEMO")
    print("=" * 70)
    print("Understanding the competitive landscape for sales strategy")
    print()
    
    agent = FieldMappingAgent()
    
    # Simulate different golf clubs with various competitor scenarios
    test_clubs = [
        {
            "name": "Greenfield Golf Club",
            "competitor": "Unknown",
            "description": "No current technology solution identified"
        },
        {
            "name": "Tech-Savvy Country Club", 
            "competitor": "Club Essentials",
            "description": "Using major Swoop competitor"
        },
        {
            "name": "Custom Solution Club",
            "competitor": "In-House App", 
            "description": "Built their own system"
        },
        {
            "name": "Legacy System Club",
            "competitor": "Jonas",
            "description": "Using established competitor"
        }
    ]
    
    print("📊 SALES PRIORITY ANALYSIS:")
    print()
    
    for club in test_clubs:
        print(f"🏌️ {club['name']}")
        print(f"   Current Solution: {club['competitor']}")
        
        # Validate competitor value with business rules
        validation = agent.validate_field_value("competitor", club['competitor'])
        
        priority = validation.get("sales_priority", "Standard")
        purpose = validation.get("business_purpose", "")
        
        print(f"   🎯 Sales Priority: {priority}")
        
        if validation.get("warnings"):
            for warning in validation["warnings"]:
                print(f"   ⚠️  {warning}")
                
        if validation.get("suggestions"):
            for suggestion in validation["suggestions"]:
                print(f"   💡 {suggestion}")
        
        print()


def demo_email_pattern_validation():
    """Demonstrate email pattern validation."""
    
    print("📧 EMAIL PATTERN VALIDATION DEMO")
    print("=" * 70)
    print("Ensuring accurate email prospecting patterns")
    print()
    
    agent = FieldMappingAgent()
    
    email_examples = [
        ("@pinehurstresort.com", "Resort with proper format"),
        ("clubname.com", "Missing @ symbol - needs correction"),
        ("@troonprivate.com", "Troon-managed facility"),
        ("@mansionridgegc.com", "Golf club domain")
    ]
    
    for pattern, description in email_examples:
        print(f"🧪 Testing: {pattern}")
        print(f"   Context: {description}")
        
        validation = agent.validate_field_value("email_pattern", pattern)
        
        if validation.get("warnings"):
            for warning in validation["warnings"]:
                print(f"   ⚠️  {warning}")
                
        if validation.get("suggestions"):
            for suggestion in validation["suggestions"]:
                print(f"   💡 {suggestion}")
        else:
            print(f"   ✅ Valid email pattern")
        
        print()


def demo_enrichment_strategy():
    """Demonstrate enrichment strategy based on business rules."""
    
    print("📈 ENRICHMENT STRATEGY DEMO")
    print("=" * 70)
    print("Prioritizing field enrichment based on business impact")
    print()
    
    agent = FieldMappingAgent()
    
    # Simulate a golf club with missing critical data
    sample_club = {
        "name": "Sample Golf Club",
        "city": "Phoenix", 
        "state": "AZ",
        # Missing critical fields:
        # - competitor (CRITICAL for sales strategy)
        # - management_company (CRITICAL for decision-making)
        # - company_type (CRITICAL for targeting)
        # - email_pattern (CRITICAL for prospecting)
        # Missing high-value fields:
        # - ngf_category (HIGH for market analysis)
        # - description (HIGH for context)
        # - club_info (HIGH for understanding scope)
    }
    
    print(f"🏌️ Analyzing: {sample_club['name']}")
    print(f"   Current Data: {len(sample_club)} fields populated")
    print()
    
    strategy = agent.get_enrichment_strategy(sample_club)
    
    if strategy.get("critical_missing"):
        print("🔥 CRITICAL MISSING FIELDS (Immediate Action Required):")
        for field_info in strategy["critical_missing"]:
            field_name = field_info['field']
            impact = field_info['business_impact']
            
            # Get business context for this field
            context = agent.get_field_business_context(field_name)
            purpose = context.get('purpose', 'No purpose defined') if context else 'No context available'
            
            print(f"   • {field_name}")
            print(f"     Purpose: {purpose}")
            print(f"     Impact: {impact}")
            print()
    
    if strategy.get("high_value_missing"):
        print("⚡ HIGH VALUE MISSING FIELDS (High Priority):")
        for field_info in strategy["high_value_missing"]:
            field_name = field_info['field']
            impact = field_info['business_impact']
            print(f"   • {field_name}: {impact}")
        print()
    
    if strategy.get("recommendations"):
        print("💡 STRATEGIC RECOMMENDATIONS:")
        for rec in strategy["recommendations"]:
            print(f"   • {rec}")
        print()


def demo_business_context():
    """Demonstrate business context for key fields."""
    
    print("📋 BUSINESS CONTEXT DEMO")
    print("=" * 70)
    print("Understanding the business purpose behind each field")
    print()
    
    agent = FieldMappingAgent()
    
    key_fields = [
        ("competitor", "🏆"),
        ("management_company", "🏢"), 
        ("email_pattern", "📧"),
        ("company_type", "🏷️"),
        ("ngf_category", "📊")
    ]
    
    for field_name, emoji in key_fields:
        print(f"{emoji} {field_name.upper().replace('_', ' ')}")
        
        context = agent.get_field_business_context(field_name)
        if context:
            print(f"   🎯 Purpose: {context.get('purpose', 'N/A')}")
            print(f"   💼 Business Value: {context.get('business_value', 'N/A')}")
            
            # Show specific business insights
            if field_name == "competitor":
                print(f"   🔍 Sales Insights:")
                data_interp = context.get('data_interpretation', {})
                for value, meaning in data_interp.items():
                    print(f"      • '{value}': {meaning}")
            
            elif field_name == "company_type":
                print(f"   🔍 Sales Implications:")
                sales_impl = context.get('sales_implications', {})
                for club_type, implication in sales_impl.items():
                    print(f"      • {club_type}: {implication}")
        
        print()


def main():
    """Run all demos."""
    
    print("🚀 SWOOP GOLF CRM ENRICHMENT WITH BUSINESS RULES")
    print("=" * 70)
    print("Demonstrating intelligent field enrichment based on business context")
    print()
    
    demo_business_context()
    demo_competitor_analysis()
    demo_email_pattern_validation()
    demo_enrichment_strategy()
    
    print("✅ DEMO COMPLETE!")
    print()
    print("🎯 KEY TAKEAWAYS:")
    print("   • Competitor field drives sales priority and strategy")
    print("   • Email patterns enable accurate prospecting")
    print("   • Management companies reveal decision-making hierarchy")
    print("   • Company types determine sales approach and expectations")
    print("   • Business rules ensure data quality and sales effectiveness")


if __name__ == "__main__":
    main()
