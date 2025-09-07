"""
Test for the Field Mapping Agent
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from crm_agent.agents.specialized.field_mapping_agent import FieldMappingAgent


def test_field_mapping_agent():
    """Test the Field Mapping Agent with various field names."""
    
    print("🧪 Testing Field Mapping Agent")
    print("=" * 60)
    
    # Create the agent
    agent = FieldMappingAgent()
    
    # Test cases for field mapping
    test_cases = [
        {
            "field_name": "state_region_code", 
            "object_type": "company",
            "expected": "State/Region Code",
            "description": "State region code mapping"
        },
        {
            "field_name": "management_company",
            "object_type": "company", 
            "expected": "Management Company",
            "description": "Management company field"
        },
        {
            "field_name": "company_type",
            "object_type": "company",
            "expected": "Company Type",
            "description": "Company type field"
        },
        {
            "field_name": "ngf_category",
            "object_type": "company",
            "expected": "NGF Category", 
            "description": "NGF category field"
        },
        {
            "field_name": "email_pattern",
            "object_type": "company",
            "expected": "email_pattern",
            "description": "Email pattern field"
        },
        {
            "field_name": "has_pool",
            "object_type": "company",
            "expected": "Has Pool",
            "description": "Pool amenity field"
        },
        {
            "field_name": "has_tennis_courts",
            "object_type": "company",
            "expected": "Has Tennis Courts",
            "description": "Tennis courts amenity field"
        }
    ]
    
    print(f"🔍 Testing {len(test_cases)} field mappings...")
    print()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['description']}")
        print(f"Input: '{test_case['field_name']}'")
        
        result = agent.map_field_name(test_case['field_name'], test_case['object_type'])
        
        if result['status'] in ['exact_match', 'fuzzy_match']:
            hubspot_name = result['hubspot_name']
            confidence = result['confidence']
            print(f"✅ Found: '{hubspot_name}' (confidence: {confidence}%)")
            
            # Check field info
            if 'field_info' in result and result['field_info']:
                field_info = result['field_info']
                null_pct = field_info.get('null_percentage', 0)
                print(f"   📊 Field Stats: {null_pct}% null rate")
                
        elif result['status'] == 'no_match':
            print(f"❌ No match found")
            if 'suggestions' in result:
                print(f"   💡 Suggestions:")
                for suggestion in result['suggestions'][:3]:
                    print(f"      • {suggestion['field_name']} ({suggestion['confidence']}%)")
        
        print("-" * 50)
    
    # Test multiple field mapping
    print(f"\n🔄 Testing Multiple Field Mapping")
    print("=" * 60)
    
    test_fields = {
        "management_company": "Troon",
        "company_type": "Golf Club", 
        "ngf_category": "Daily Fee",
        "state_region_code": "NY-SE",
        "has_pool": "No",
        "has_tennis_courts": "No"
    }
    
    bulk_result = agent.map_multiple_fields(test_fields, "company")
    
    print(f"📊 Bulk Mapping Results:")
    print(f"   Total Fields: {bulk_result['total_fields']}")
    print(f"   Valid Mappings: {bulk_result['valid_fields']}")
    print(f"   Invalid Fields: {bulk_result['invalid_count']}")
    
    print(f"\n✅ Valid HubSpot Mappings:")
    for hubspot_field, value in bulk_result['valid_mappings'].items():
        print(f"   • {hubspot_field}: {value}")
    
    if bulk_result['invalid_fields']:
        print(f"\n❌ Invalid Fields:")
        for field in bulk_result['invalid_fields']:
            print(f"   • {field}")
    
    return bulk_result


def test_enrichment_suggestions():
    """Test the enrichment field suggestions."""
    
    print(f"\n💡 Testing Enrichment Suggestions")
    print("=" * 60)
    
    agent = FieldMappingAgent()
    
    # Get enrichment suggestions for companies
    suggestions = agent.suggest_enrichment_fields("company")
    
    print(f"🎯 Top Enrichment Opportunities for Companies:")
    print(f"Found {len(suggestions)} fields with high null rates\n")
    
    for i, suggestion in enumerate(suggestions[:10], 1):  # Show top 10
        field_name = suggestion['field_name']
        null_pct = suggestion['null_percentage']
        priority = suggestion['priority']
        
        priority_labels = {1: "🔥 HIGH", 2: "🟡 MEDIUM", 3: "🔵 LOW", 4: "⚪ VERY LOW", 5: "⚫ MINIMAL"}
        priority_label = priority_labels.get(priority, "❓ UNKNOWN")
        
        print(f"{i:2d}. {field_name}")
        print(f"    Null Rate: {null_pct}% | Priority: {priority_label}")
        print()


if __name__ == "__main__":
    test_field_mapping_agent()
    test_enrichment_suggestions()
