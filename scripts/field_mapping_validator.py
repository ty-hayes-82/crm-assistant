#!/usr/bin/env python3
"""
Field Mapping Validator for HubSpot CRM Enrichment

This utility validates HubSpot property names against actual field profiles
and provides intelligent mapping suggestions to prevent enrichment failures.
"""

import json
import sys
import os
from typing import Dict, List, Any, Optional
from pathlib import Path


class HubSpotFieldValidator:
    """Validates and maps field names using HubSpot field mapping configuration."""
    
    def __init__(self, 
                 field_mapping_path: str = "crm_agent/configs/hubspot_field_mapping.json",
                 field_profiles_path: str = "docs/companies_field_profiles.json"):
        """Initialize with field mapping configuration and profiles data."""
        self.mapping_path = Path(field_mapping_path)
        self.profiles_path = Path(field_profiles_path)
        self.field_mapping = self._load_field_mapping()
        self.field_profiles = self._load_field_profiles()
        self.field_map = self._build_field_map()
    
    def _load_field_mapping(self) -> Dict[str, Any]:
        """Load field mapping configuration from JSON file."""
        try:
            with open(self.mapping_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading field mapping: {e}")
            return {}
    
    def _load_field_profiles(self) -> List[Dict[str, Any]]:
        """Load field profiles from JSON file."""
        try:
            with open(self.profiles_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading field profiles: {e}")
            return []
    
    def _build_field_map(self) -> Dict[str, Dict[str, Any]]:
        """Build mapping of field names using configuration and profile data."""
        field_map = {}
        
        # Use field mapping configuration as primary source
        company_fields = self.field_mapping.get("hubspot_field_mapping", {}).get("company_fields", {})
        
        for internal_name, config in company_fields.items():
            # Create multiple mapping keys for flexibility
            display_name = config.get("display_name", "")
            keys = [
                internal_name,  # hubspot_internal_name
                display_name,   # display_name
                internal_name.lower(),
                display_name.lower() if display_name else "",
                display_name.replace(" ", "_").lower() if display_name else "",
                display_name.replace("/", "_").lower() if display_name else "",
                display_name.replace(" ", "").lower() if display_name else ""
            ]
            
            # Combine config with profile data if available
            profile_data = self._find_profile_by_display_name(display_name)
            combined_data = {**config}
            if profile_data:
                combined_data.update({
                    "actual_null_percentage": profile_data.get("null_percentage", 0),
                    "actual_data_type": profile_data.get("data_type", "unknown"),
                    "quality_issues": profile_data.get("quality_issues", []),
                    "sample_values": profile_data.get("sample_values", [])
                })
            
            for key in keys:
                if key:  # Skip empty keys
                    field_map[key] = combined_data
        
        return field_map
    
    def _find_profile_by_display_name(self, display_name: str) -> Optional[Dict[str, Any]]:
        """Find profile data by display name."""
        for profile in self.field_profiles:
            if profile.get("field_name", "").lower() == display_name.lower():
                return profile
        return None
    
    def validate_properties(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a dictionary of properties against HubSpot field profiles.
        
        Returns:
            Dictionary with validation results
        """
        results = {
            "valid_properties": {},
            "invalid_properties": {},
            "suggestions": {},
            "warnings": [],
            "field_insights": {}
        }
        
        for prop_name, prop_value in properties.items():
            validation = self._validate_single_property(prop_name, prop_value)
            
            if validation["is_valid"]:
                results["valid_properties"][prop_name] = prop_value
                if validation["profile"]:
                    results["field_insights"][prop_name] = {
                        "null_percentage": validation["profile"].get("null_percentage", 0),
                        "data_type": validation["profile"].get("data_type", "unknown"),
                        "quality_issues": validation["profile"].get("quality_issues", [])
                    }
            else:
                results["invalid_properties"][prop_name] = prop_value
                if validation["suggestions"]:
                    results["suggestions"][prop_name] = validation["suggestions"]
                if validation["warning"]:
                    results["warnings"].append(validation["warning"])
        
        return results
    
    def _validate_single_property(self, prop_name: str, prop_value: Any) -> Dict[str, Any]:
        """Validate a single property."""
        # Try exact match first
        profile = self.field_map.get(prop_name)
        if profile:
            return {
                "is_valid": True,
                "profile": profile,
                "suggestions": [],
                "warning": None
            }
        
        # Try fuzzy matching
        suggestions = self._find_similar_fields(prop_name)
        
        # Check if field might be completely empty (unused)
        warning = None
        if suggestions:
            top_suggestion = suggestions[0]
            if top_suggestion.get("null_percentage", 0) == 100.0:
                warning = f"Field '{prop_name}' maps to '{top_suggestion['field_name']}' which is completely empty (unused field)"
        
        return {
            "is_valid": False,
            "profile": None,
            "suggestions": suggestions[:3],  # Top 3 suggestions
            "warning": warning
        }
    
    def _find_similar_fields(self, prop_name: str) -> List[Dict[str, Any]]:
        """Find similar field names using fuzzy matching."""
        try:
            from thefuzz import process
        except ImportError:
            print("Warning: thefuzz not available for fuzzy matching")
            return []
        
        field_names = [profile["field_name"] for profile in self.field_profiles]
        matches = process.extract(prop_name, field_names, limit=5)
        
        suggestions = []
        for match_name, score in matches:
            if score > 60:  # Reasonable similarity threshold
                profile = next(p for p in self.field_profiles if p["field_name"] == match_name)
                suggestions.append({
                    "field_name": match_name,
                    "similarity_score": score,
                    "null_percentage": profile.get("null_percentage", 0),
                    "data_type": profile.get("data_type", "unknown"),
                    "quality_issues": profile.get("quality_issues", [])
                })
        
        return suggestions
    
    def get_correct_field_mappings(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get the correct HubSpot field mappings for a set of properties.
        
        Returns:
            Dictionary with corrected property mappings
        """
        corrected_properties = {}
        mapping_log = []
        
        for prop_name, prop_value in properties.items():
            # Check if this is a deprecated field
            deprecated_fields = self.field_mapping.get("hubspot_field_mapping", {}).get("deprecated_fields", {})
            if prop_name in deprecated_fields:
                deprecated_info = deprecated_fields[prop_name]
                replacement = deprecated_info.get("replacement")
                if replacement:
                    corrected_properties[replacement] = prop_value
                    mapping_log.append(f"Mapped deprecated '{prop_name}' → '{replacement}': {deprecated_info['reason']}")
                else:
                    mapping_log.append(f"Skipped deprecated '{prop_name}': {deprecated_info['reason']}")
                continue
            
            # Check if field exists in our mapping
            field_config = self.field_map.get(prop_name)
            if field_config:
                hubspot_name = field_config.get("hubspot_internal_name", prop_name)
                corrected_properties[hubspot_name] = prop_value
                if hubspot_name != prop_name:
                    mapping_log.append(f"Mapped '{prop_name}' → '{hubspot_name}'")
            else:
                # Try to find a suggestion
                suggestions = self._find_similar_fields(prop_name)
                if suggestions and suggestions[0]["similarity_score"] > 80:
                    suggested_field = suggestions[0]["field_name"]
                    # Find the internal name for this suggestion
                    suggested_config = self._find_profile_by_display_name(suggested_field)
                    if suggested_config:
                        corrected_properties[prop_name] = prop_value  # Keep original for now
                        mapping_log.append(f"Warning: '{prop_name}' might map to '{suggested_field}' (similarity: {suggestions[0]['similarity_score']}%)")
                    else:
                        corrected_properties[prop_name] = prop_value
                        mapping_log.append(f"Warning: Unknown field '{prop_name}' - keeping as-is")
                else:
                    corrected_properties[prop_name] = prop_value
                    mapping_log.append(f"Warning: No mapping found for '{prop_name}' - keeping as-is")
        
        return {
            "corrected_properties": corrected_properties,
            "mapping_log": mapping_log
        }
    
    def get_field_analysis(self, field_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed analysis for a specific field."""
        profile = self.field_map.get(field_name) or self.field_map.get(field_name.lower())
        if not profile:
            return None
        
        return {
            "field_name": profile.get("field_name"),
            "null_percentage": profile.get("null_percentage", 0),
            "data_type": profile.get("data_type", "unknown"),
            "unique_values": profile.get("unique_values", 0),
            "quality_issues": profile.get("quality_issues", []),
            "sample_values": profile.get("sample_values", []),
            "analysis": profile.get("analysis", ""),
            "enrichment_priority": self._calculate_enrichment_priority(profile)
        }
    
    def _calculate_enrichment_priority(self, profile: Dict[str, Any]) -> str:
        """Calculate enrichment priority based on field characteristics."""
        null_pct = profile.get("null_percentage", 0)
        quality_issues = profile.get("quality_issues", [])
        
        if null_pct == 100.0:
            return "SKIP - Completely empty field"
        elif null_pct > 95.0:
            return "LOW - Nearly empty field"
        elif "HIGH_NULL_RATE" in quality_issues:
            return "MEDIUM - High null rate"
        elif null_pct < 20.0:
            return "LOW - Already well populated"
        else:
            return "HIGH - Good enrichment candidate"


def validate_mansion_ridge_properties():
    """Validate the properties used in the Mansion Ridge update."""
    validator = HubSpotFieldValidator()
    
    # Properties from the update script
    test_properties = {
        "management_company": "Troon",
        "company_type": "Golf Club", 
        "ngf_category": "Daily Fee",
        "description": "Sample description",
        "club_info": "Sample club info",
        "email_pattern": "first.last",
        "competitor": "ClubCorp",
        "has_pool": "No",
        "has_tennis_courts": "No",
        "state": "New York",
        "club_type": "Daily Fee",
        "market": "Hudson Valley",
        "hs_lead_status": "New",
        # Test problematic fields
        "state_region": "New York",  # Should be "state"
        "state_region_code": "NY",   # May not exist
    }
    
    print("🔍 HubSpot Field Validation Results")
    print("=" * 60)
    
    results = validator.validate_properties(test_properties)
    
    print(f"✅ Valid Properties ({len(results['valid_properties'])}):")
    for prop, value in results['valid_properties'].items():
        insight = results['field_insights'].get(prop, {})
        null_pct = insight.get('null_percentage', 0)
        quality_issues = insight.get('quality_issues', [])
        
        status = "🟢" if null_pct < 50 else "🟡" if null_pct < 90 else "🔴"
        issues_str = f" ({', '.join(quality_issues)})" if quality_issues else ""
        
        print(f"  {status} {prop}: {null_pct:.1f}% null{issues_str}")
    
    if results['invalid_properties']:
        print(f"\n❌ Invalid Properties ({len(results['invalid_properties'])}):")
        for prop, value in results['invalid_properties'].items():
            suggestions = results['suggestions'].get(prop, [])
            print(f"  • {prop}")
            if suggestions:
                print("    Suggestions:")
                for sug in suggestions:
                    print(f"      - {sug['field_name']} (similarity: {sug['similarity_score']}%, null: {sug['null_percentage']:.1f}%)")
    
    if results['warnings']:
        print(f"\n⚠️  Warnings:")
        for warning in results['warnings']:
            print(f"  • {warning}")
    
    return results


def main():
    """Main function for command line usage."""
    if len(sys.argv) > 1 and sys.argv[1] == "validate":
        validate_mansion_ridge_properties()
    else:
        print("Usage: python field_mapping_validator.py validate")
        print("       Validates the Mansion Ridge properties against HubSpot field profiles")


if __name__ == "__main__":
    main()
