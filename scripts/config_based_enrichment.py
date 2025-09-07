#!/usr/bin/env python3
"""
Configuration-Based HubSpot Enrichment

Uses the hubspot_field_mapping.json configuration to automatically
validate and correct field mappings before HubSpot updates.
"""

import os
import sys
import json
import requests
from pathlib import Path
from typing import Dict, Any

# Add the project root to the path
sys.path.append(str(Path(__file__).parent.parent))

from scripts.field_mapping_validator import HubSpotFieldValidator


class ConfigBasedEnrichment:
    """Enrichment system that uses field mapping configuration."""
    
    def __init__(self):
        self.validator = HubSpotFieldValidator()
        self.token = self._get_hubspot_token()
    
    def _get_hubspot_token(self) -> str:
        """Get HubSpot token from environment or .env file."""
        token = os.getenv("PRIVATE_APP_ACCESS_TOKEN")
        if token:
            return token
        
        env_path = Path(".env")
        if env_path.exists():
            with open(env_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        k, v = line.split("=", 1)
                        if k == "PRIVATE_APP_ACCESS_TOKEN" and v:
                            return v
        
        raise ValueError("HubSpot token not found in environment or .env file")
    
    def enrich_company(self, company_id: str, raw_properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich a company using configuration-based field mapping.
        
        Args:
            company_id: HubSpot company ID
            raw_properties: Raw properties to update (may have incorrect field names)
            
        Returns:
            Dictionary with enrichment results
        """
        print(f"🔧 Configuration-Based Enrichment for Company {company_id}")
        print("=" * 60)
        
        # Step 1: Validate and correct field mappings
        print("\n📋 Step 1: Field Mapping Validation")
        validation_results = self.validator.validate_properties(raw_properties)
        mapping_results = self.validator.get_correct_field_mappings(raw_properties)
        
        corrected_properties = mapping_results["corrected_properties"]
        mapping_log = mapping_results["mapping_log"]
        
        print(f"✅ Valid properties: {len(validation_results['valid_properties'])}")
        print(f"❌ Invalid properties: {len(validation_results['invalid_properties'])}")
        print(f"🔄 Field mappings applied: {len(mapping_log)}")
        
        # Show mapping log
        if mapping_log:
            print("\n🗺️  Field Mapping Log:")
            for log_entry in mapping_log:
                print(f"   • {log_entry}")
        
        # Step 2: Apply enrichment rules
        print(f"\n⚡ Step 2: Applying Enrichment Rules")
        enriched_properties = self._apply_enrichment_rules(corrected_properties)
        
        # Step 3: Update HubSpot
        print(f"\n🚀 Step 3: HubSpot Update")
        update_result = self._update_hubspot_company(company_id, enriched_properties)
        
        return {
            "company_id": company_id,
            "original_properties": raw_properties,
            "corrected_properties": corrected_properties,
            "enriched_properties": enriched_properties,
            "mapping_log": mapping_log,
            "validation_results": validation_results,
            "update_result": update_result
        }
    
    def _apply_enrichment_rules(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Apply enrichment rules based on configuration."""
        enriched = properties.copy()
        
        # Get enrichment rules from configuration
        enrichment_rules = self.validator.field_mapping.get("hubspot_field_mapping", {}).get("enrichment_rules", {})
        
        # Auto-populate derived fields
        auto_sources = self.validator.field_mapping.get("hubspot_field_mapping", {}).get("auto_population_sources", {})
        
        # Example: If we have a domain, try to construct website
        if "domain" in enriched and "website" not in enriched:
            domain = enriched["domain"]
            if domain and not domain.startswith("http"):
                enriched["website"] = f"https://{domain}"
                print(f"   🔗 Auto-populated website from domain: {enriched['website']}")
        
        # Example: Derive market from city/state
        if "city" in enriched and "state" in enriched and "market" not in enriched:
            city = enriched.get("city", "")
            state = enriched.get("state", "")
            if city and state:
                # Simple market derivation - in practice this could be more sophisticated
                enriched["market"] = f"{city} Metro" if city else state
                print(f"   🗺️  Auto-populated market: {enriched['market']}")
        
        return enriched
    
    def _update_hubspot_company(self, company_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Update HubSpot company with validated properties."""
        url = f"https://api.hubapi.com/crm/v3/objects/companies/{company_id}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        body = {"properties": properties}
        
        print(f"   📤 Updating {len(properties)} properties...")
        for key, value in properties.items():
            display_value = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
            print(f"      • {key}: {display_value}")
        
        try:
            response = requests.patch(url, headers=headers, json=body, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            print("   ✅ HubSpot update successful!")
            return {"status": "success", "result": result}
            
        except requests.exceptions.RequestException as e:
            error_msg = f"HubSpot update failed: {e}"
            if hasattr(e, 'response') and e.response:
                error_msg += f"\n   Response: {e.response.text}"
            print(f"   ❌ {error_msg}")
            return {"status": "error", "error": error_msg}


def enrich_mansion_ridge():
    """Enrich The Golf Club at Mansion Ridge using configuration-based approach."""
    enrichment = ConfigBasedEnrichment()
    
    # Raw properties (may have incorrect field names)
    raw_properties = {
        "management_company": "Troon",
        "company_type": "Golf Club",
        "ngf_category": "Daily Fee", 
        "description": (
            "The Golf Club at Mansion Ridge is an 18-hole championship golf course located in Monroe, "
            "New York. Designed by Jack Nicklaus, this scenic course features rolling hills, strategic "
            "water hazards, and well-maintained greens. Known for its challenging layout and beautiful "
            "Hudson Valley setting, the course offers a premium golf experience for players of all skill levels."
        ),
        "club_info": (
            "18-hole Jack Nicklaus designed championship course featuring rolling terrain, strategic water features, "
            "and panoramic Hudson Valley views. Full-service clubhouse with dining facilities, pro shop, and event spaces. "
            "Practice facilities include driving range and putting green."
        ),
        "email_pattern": "first.last",
        "competitor": "ClubCorp",
        "has_pool": "No",
        "has_tennis_courts": "No",
        "state": "New York",
        "club_type": "Daily Fee",
        "market": "Hudson Valley",
        "hs_lead_status": "New",
        # Test problematic fields that should be auto-corrected
        "state_region": "New York",    # Should map to "state"
        "state_region_code": "NY",     # Should be skipped (deprecated)
    }
    
    company_id = "15537401601"  # Mansion Ridge company ID
    
    result = enrichment.enrich_company(company_id, raw_properties)
    
    print(f"\n🎉 Configuration-Based Enrichment Complete!")
    print(f"   📊 Original properties: {len(result['original_properties'])}")
    print(f"   🔧 Corrected properties: {len(result['corrected_properties'])}")
    print(f"   ⚡ Enriched properties: {len(result['enriched_properties'])}")
    print(f"   📝 Mapping changes: {len(result['mapping_log'])}")
    
    return result


def main():
    """Main function."""
    if len(sys.argv) > 1 and sys.argv[1] == "mansion-ridge":
        enrich_mansion_ridge()
    else:
        print("Usage: python config_based_enrichment.py mansion-ridge")
        print("       Enriches Mansion Ridge using configuration-based field mapping")


if __name__ == "__main__":
    main()
