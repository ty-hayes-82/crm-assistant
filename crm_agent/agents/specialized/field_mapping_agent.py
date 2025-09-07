"""
Field Mapping Agent
Identifies correct HubSpot field names by analyzing field profiles data
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from thefuzz import process
from ...core.base_agents import SpecializedAgent


class FieldMappingAgent(SpecializedAgent):
    """Agent that maps field names to correct HubSpot internal names using field profiles."""

    def __init__(self, **kwargs):
        super().__init__(
            name="FieldMappingAgent",
            domain="field_mapping",
            specialized_tools=["search_companies", "get_company"],
            instruction="""
            You are a specialized agent responsible for mapping field names to correct HubSpot internal names.
            Your task is to:
            1. Load field profiles data for companies and contacts
            2. Use fuzzy matching to find the correct HubSpot field names
            3. Provide mapping suggestions with confidence scores
            4. Handle variations in field naming conventions
            5. Apply business rules and context for field enrichment
            
            This agent helps ensure data enrichment uses the correct HubSpot property names
            and follows Swoop Golf's business rules for field purposes and data quality.
            """,
            **kwargs
        )
        self._company_fields = self._load_field_profiles("companies_field_profiles.json")
        self._contact_fields = self._load_field_profiles("contacts_field_profiles.json")
        self._enrichment_rules = self._load_enrichment_rules()

    def _load_field_profiles(self, filename: str) -> List[Dict[str, Any]]:
        """Load field profiles from JSON file."""
        file_path = Path(__file__).parent.parent.parent.parent / "docs" / filename
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading {filename}: {e}")
            return []

    def _load_enrichment_rules(self) -> Dict[str, Any]:
        """Load field enrichment rules and business context."""
        file_path = Path(__file__).parent.parent.parent / "configs" / "field_enrichment_rules.json"
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading enrichment rules: {e}")
            return {}

    def get_all_company_field_names(self) -> List[str]:
        """Get all available company field names."""
        return [field["field_name"] for field in self._company_fields]

    def get_all_contact_field_names(self) -> List[str]:
        """Get all available contact field names."""
        return [field["field_name"] for field in self._contact_fields]

    def map_field_name(self, field_name: str, object_type: str = "company") -> Dict[str, Any]:
        """
        Map a field name to the correct HubSpot internal name.

        Args:
            field_name: The field name to map (e.g., "state_region_code", "management_company")
            object_type: Either "company" or "contact"

        Returns:
            Dictionary with mapping results
        """
        if object_type.lower() == "company":
            available_fields = self.get_all_company_field_names()
            field_profiles = self._company_fields
        else:
            available_fields = self.get_all_contact_field_names()
            field_profiles = self._contact_fields

        if not available_fields:
            return {
                "status": "error",
                "message": f"No {object_type} field profiles loaded"
            }

        # Try exact match first
        for field in available_fields:
            if field.lower() == field_name.lower():
                field_info = next((f for f in field_profiles if f["field_name"] == field), None)
                return {
                    "status": "exact_match",
                    "original_name": field_name,
                    "hubspot_name": field,
                    "confidence": 100,
                    "field_info": field_info
                }

        # Use fuzzy matching for close matches
        best_match, score = process.extractOne(field_name, available_fields)

        if score > 70:  # Good confidence threshold
            field_info = next((f for f in field_profiles if f["field_name"] == best_match), None)
            
            # Special handling for common field variations
            suggestions = self._get_field_suggestions(field_name, available_fields)
            
            return {
                "status": "fuzzy_match",
                "original_name": field_name,
                "hubspot_name": best_match,
                "confidence": score,
                "field_info": field_info,
                "suggestions": suggestions
            }

        # No good match found
        suggestions = self._get_field_suggestions(field_name, available_fields)
        
        return {
            "status": "no_match",
            "original_name": field_name,
            "message": f"No good match found for '{field_name}'",
            "suggestions": suggestions
        }

    def _get_field_suggestions(self, field_name: str, available_fields: List[str]) -> List[Dict[str, Any]]:
        """Get multiple field suggestions for a given field name."""
        # Get top 5 matches
        top_matches = process.extract(field_name, available_fields, limit=5)
        
        suggestions = []
        for match_name, score in top_matches:
            if score > 50:  # Only include reasonable matches
                suggestions.append({
                    "field_name": match_name,
                    "confidence": score
                })
        
        return suggestions

    def map_multiple_fields(self, field_mapping: Dict[str, str], object_type: str = "company") -> Dict[str, Any]:
        """
        Map multiple fields at once.

        Args:
            field_mapping: Dictionary of {desired_name: value} pairs
            object_type: Either "company" or "contact"

        Returns:
            Dictionary with mapping results for all fields
        """
        results = {}
        valid_mappings = {}
        invalid_fields = []

        for field_name, value in field_mapping.items():
            mapping_result = self.map_field_name(field_name, object_type)
            results[field_name] = mapping_result

            if mapping_result["status"] in ["exact_match", "fuzzy_match"]:
                # Use the correct HubSpot field name
                hubspot_name = mapping_result["hubspot_name"]
                valid_mappings[hubspot_name] = value
                print(f"✅ Mapped '{field_name}' → '{hubspot_name}' (confidence: {mapping_result['confidence']}%)")
            else:
                invalid_fields.append(field_name)
                print(f"❌ Could not map '{field_name}'")

        return {
            "status": "completed",
            "valid_mappings": valid_mappings,
            "invalid_fields": invalid_fields,
            "mapping_results": results,
            "total_fields": len(field_mapping),
            "valid_fields": len(valid_mappings),
            "invalid_count": len(invalid_fields)
        }

    def get_field_info(self, field_name: str, object_type: str = "company") -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific field."""
        if object_type.lower() == "company":
            field_profiles = self._company_fields
        else:
            field_profiles = self._contact_fields

        for field in field_profiles:
            if field["field_name"].lower() == field_name.lower():
                return field

        return None

    def suggest_enrichment_fields(self, object_type: str = "company") -> List[Dict[str, Any]]:
        """
        Suggest fields that have high null rates and could benefit from enrichment.
        
        Args:
            object_type: Either "company" or "contact"
            
        Returns:
            List of fields with high null rates
        """
        if object_type.lower() == "company":
            field_profiles = self._company_fields
        else:
            field_profiles = self._contact_fields

        enrichment_candidates = []

        for field in field_profiles:
            null_percentage = field.get("null_percentage", 0)
            field_name = field.get("field_name", "")
            
            # Look for fields with high null rates that are business-relevant
            if null_percentage > 50 and self._is_business_relevant_field(field_name):
                enrichment_candidates.append({
                    "field_name": field_name,
                    "null_percentage": null_percentage,
                    "total_records": field.get("total_records", 0),
                    "data_type": field.get("data_type", "unknown"),
                    "priority": self._calculate_enrichment_priority(field)
                })

        # Sort by priority (lower number = higher priority)
        enrichment_candidates.sort(key=lambda x: x["priority"])
        
        return enrichment_candidates[:20]  # Return top 20 candidates

    def get_field_business_context(self, field_name: str) -> Optional[Dict[str, Any]]:
        """
        Get business context and rules for a specific field.
        
        Args:
            field_name: The field name to get context for
            
        Returns:
            Dictionary with business context, purpose, and rules
        """
        if not self._enrichment_rules:
            return None
            
        company_fields = self._enrichment_rules.get("field_enrichment_rules", {}).get("company_fields", {})
        
        # Try direct match first
        if field_name in company_fields:
            return company_fields[field_name]
            
        # Try lowercase match
        field_lower = field_name.lower()
        for rule_field, context in company_fields.items():
            if rule_field.lower() == field_lower:
                return context
                
        # Try fuzzy match for field names
        field_names = list(company_fields.keys())
        best_match, score = process.extractOne(field_name, field_names)
        
        if score > 80:  # High confidence match
            return company_fields[best_match]
            
        return None

    def validate_field_value(self, field_name: str, value: str) -> Dict[str, Any]:
        """
        Validate a field value against business rules.
        
        Args:
            field_name: The field name
            value: The value to validate
            
        Returns:
            Dictionary with validation results
        """
        context = self.get_field_business_context(field_name)
        
        if not context:
            return {
                "status": "no_rules",
                "message": f"No validation rules found for field '{field_name}'"
            }
        
        validation_results = {
            "status": "valid",
            "field_name": field_name,
            "value": value,
            "business_purpose": context.get("purpose", ""),
            "warnings": [],
            "suggestions": []
        }
        
        # Validate competitor field
        if field_name.lower() in ["competitor", "competitors"]:
            swoop_competitors = context.get("swoop_competitors", [])
            data_interpretation = context.get("data_interpretation", {})
            
            if value in swoop_competitors:
                validation_results["warnings"].append(f"'{value}' is a Swoop Golf competitor - requires competitive sales approach")
                validation_results["sales_priority"] = "Low-Medium"
            elif value == "Unknown":
                validation_results["suggestions"].append("High priority prospect - no existing solution to replace")
                validation_results["sales_priority"] = "High"
            elif value == "In-House App":
                validation_results["suggestions"].append("Medium priority - may be dissatisfied with custom solution")
                validation_results["sales_priority"] = "Medium"
        
        # Validate email pattern
        elif field_name.lower() in ["email_pattern", "emailpattern"]:
            if not value.startswith("@"):
                validation_results["warnings"].append("Email pattern should start with '@'")
                validation_results["suggestions"].append(f"Consider: '@{value}' instead of '{value}'")
        
        # Validate company type
        elif field_name.lower() in ["company_type", "companytype"]:
            valid_options = context.get("valid_options", [])
            if valid_options and value not in valid_options:
                validation_results["warnings"].append(f"'{value}' may not be a valid company type")
                validation_results["suggestions"].append(f"Valid options: {', '.join(valid_options)}")
        
        return validation_results

    def get_enrichment_strategy(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate an enrichment strategy based on current company data and business rules.
        
        Args:
            company_data: Current company data from HubSpot
            
        Returns:
            Dictionary with enrichment recommendations
        """
        if not self._enrichment_rules:
            return {"status": "no_rules", "message": "No enrichment rules loaded"}
        
        rules = self._enrichment_rules.get("field_enrichment_rules", {})
        priorities = rules.get("enrichment_priorities", {})
        
        strategy = {
            "critical_missing": [],
            "high_value_missing": [],
            "supplementary_missing": [],
            "recommendations": []
        }
        
        # Check critical fields
        for field in priorities.get("critical_fields", []):
            if not company_data.get(field):
                strategy["critical_missing"].append({
                    "field": field,
                    "priority": "CRITICAL",
                    "business_impact": self._get_field_impact(field)
                })
        
        # Check high value fields
        for field in priorities.get("high_value_fields", []):
            if not company_data.get(field):
                strategy["high_value_missing"].append({
                    "field": field,
                    "priority": "HIGH",
                    "business_impact": self._get_field_impact(field)
                })
        
        # Check supplementary fields
        for field in priorities.get("supplementary_fields", []):
            if not company_data.get(field):
                strategy["supplementary_missing"].append({
                    "field": field,
                    "priority": "SUPPLEMENTARY",
                    "business_impact": self._get_field_impact(field)
                })
        
        # Generate recommendations
        if strategy["critical_missing"]:
            strategy["recommendations"].append("🔥 URGENT: Critical fields missing - these are essential for sales qualification")
        
        if strategy["high_value_missing"]:
            strategy["recommendations"].append("⚡ HIGH PRIORITY: Missing high-value fields that significantly impact sales effectiveness")
        
        # Special competitor analysis
        competitor_value = company_data.get("competitor", "Unknown")
        if competitor_value == "Unknown":
            strategy["recommendations"].append("🎯 OPPORTUNITY: No competitor identified - this is a high-priority greenfield prospect")
        
        return strategy

    def _get_field_impact(self, field_name: str) -> str:
        """Get the business impact description for a field."""
        context = self.get_field_business_context(field_name)
        if context:
            return context.get("business_value", "Improves data completeness")
        return "Improves data completeness"

    def _is_business_relevant_field(self, field_name: str) -> bool:
        """Check if a field is business-relevant for enrichment."""
        business_keywords = [
            "description", "industry", "revenue", "employee", "company_type", 
            "management", "competitor", "ngf", "club", "golf", "address",
            "website", "phone", "founded", "year"
        ]
        
        field_lower = field_name.lower()
        return any(keyword in field_lower for keyword in business_keywords)

    def _calculate_enrichment_priority(self, field: Dict[str, Any]) -> int:
        """Calculate enrichment priority (lower = higher priority)."""
        field_name = field.get("field_name", "").lower()
        null_percentage = field.get("null_percentage", 0)
        
        # High priority fields
        if any(keyword in field_name for keyword in ["description", "management_company", "competitor"]):
            return 1
        
        # Medium priority fields  
        elif any(keyword in field_name for keyword in ["company_type", "industry", "ngf"]):
            return 2
            
        # Lower priority based on null percentage
        elif null_percentage > 90:
            return 3
        elif null_percentage > 70:
            return 4
        else:
            return 5


def create_field_mapping_agent(**kwargs) -> FieldMappingAgent:
    """Create a FieldMappingAgent instance."""
    return FieldMappingAgent(**kwargs)
