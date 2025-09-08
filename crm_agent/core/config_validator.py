"""
Configuration Validation System for Phase 9.

This module provides JSON Schema validation for all agent configurations
to prevent runtime errors due to misconfiguration.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass

try:
    import jsonschema
    from jsonschema import validate, ValidationError, Draft7Validator
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    jsonschema = None
    validate = None
    ValidationError = None
    Draft7Validator = None
    JSONSCHEMA_AVAILABLE = False


@dataclass
class ValidationResult:
    """Result of configuration validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    config_path: Optional[str] = None
    schema_path: Optional[str] = None


class ConfigValidator:
    """Configuration validator using JSON Schema."""
    
    def __init__(self):
        if not JSONSCHEMA_AVAILABLE:
            raise ImportError("jsonschema not available. Install with: pip install jsonschema")
        
        self.logger = logging.getLogger(__name__)
        self.schema_cache: Dict[str, Dict[str, Any]] = {}
        
        # Define schema paths
        self.schema_dir = Path(__file__).parent.parent / "configs" / "schemas"
        self.config_dir = Path(__file__).parent.parent / "configs"
        
        # Register known schema mappings
        self.schema_mappings = {
            "lead_scoring_config.json": "lead_scoring_config_schema.json",
            "outreach_personalization_config.json": "outreach_personalization_config_schema.json",
            "hubspot_field_mapping.json": "hubspot_field_mapping_schema.json",
            "role_taxonomy_config.json": "role_taxonomy_config_schema.json",
            "field_enrichment_rules.json": "field_enrichment_rules_schema.json"
        }
    
    def load_schema(self, schema_name: str) -> Dict[str, Any]:
        """Load and cache a JSON schema."""
        if schema_name in self.schema_cache:
            return self.schema_cache[schema_name]
        
        schema_path = self.schema_dir / schema_name
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema not found: {schema_path}")
        
        try:
            with open(schema_path, 'r') as f:
                schema = json.load(f)
            
            # Validate the schema itself
            Draft7Validator.check_schema(schema)
            
            self.schema_cache[schema_name] = schema
            return schema
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in schema {schema_name}: {e}")
        except jsonschema.SchemaError as e:
            raise ValueError(f"Invalid schema {schema_name}: {e}")
    
    def validate_config_file(self, config_path: Union[str, Path]) -> ValidationResult:
        """Validate a configuration file against its schema."""
        config_path = Path(config_path)
        
        if not config_path.exists():
            return ValidationResult(
                is_valid=False,
                errors=[f"Configuration file not found: {config_path}"],
                warnings=[],
                config_path=str(config_path)
            )
        
        # Determine schema file
        config_name = config_path.name
        if config_name not in self.schema_mappings:
            return ValidationResult(
                is_valid=False,
                errors=[f"No schema mapping found for config: {config_name}"],
                warnings=[],
                config_path=str(config_path)
            )
        
        schema_name = self.schema_mappings[config_name]
        
        try:
            # Load configuration
            with open(config_path, 'r') as f:
                config_data = json.load(f)
            
            # Load schema
            schema = self.load_schema(schema_name)
            
            # Validate
            return self.validate_config_data(config_data, schema, str(config_path), schema_name)
            
        except json.JSONDecodeError as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"Invalid JSON in config file: {e}"],
                warnings=[],
                config_path=str(config_path)
            )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"Error validating config: {e}"],
                warnings=[],
                config_path=str(config_path)
            )
    
    def validate_config_data(self, config_data: Dict[str, Any], schema: Dict[str, Any], 
                           config_path: str = None, schema_name: str = None) -> ValidationResult:
        """Validate configuration data against a schema."""
        errors = []
        warnings = []
        
        try:
            # Perform validation
            validate(instance=config_data, schema=schema)
            
            # Additional custom validations
            custom_errors, custom_warnings = self._perform_custom_validations(
                config_data, schema_name or "unknown"
            )
            errors.extend(custom_errors)
            warnings.extend(custom_warnings)
            
            return ValidationResult(
                is_valid=len(errors) == 0,
                errors=errors,
                warnings=warnings,
                config_path=config_path,
                schema_path=schema_name
            )
            
        except ValidationError as e:
            errors.append(f"Schema validation error: {e.message}")
            if e.absolute_path:
                errors.append(f"  Path: {' -> '.join(str(p) for p in e.absolute_path)}")
            
            return ValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                config_path=config_path,
                schema_path=schema_name
            )
    
    def _perform_custom_validations(self, config_data: Dict[str, Any], 
                                  schema_name: str) -> tuple[List[str], List[str]]:
        """Perform custom validation logic beyond JSON Schema."""
        errors = []
        warnings = []
        
        if schema_name == "lead_scoring_config_schema.json":
            errors_custom, warnings_custom = self._validate_lead_scoring_config(config_data)
            errors.extend(errors_custom)
            warnings.extend(warnings_custom)
        
        elif schema_name == "outreach_personalization_config_schema.json":
            errors_custom, warnings_custom = self._validate_outreach_config(config_data)
            errors.extend(errors_custom)
            warnings.extend(warnings_custom)
        
        return errors, warnings
    
    def _validate_lead_scoring_config(self, config: Dict[str, Any]) -> tuple[List[str], List[str]]:
        """Custom validation for lead scoring configuration."""
        errors = []
        warnings = []
        
        # Validate that fit_weight + intent_weight = 1.0
        total_calc = config.get("total_score_calculation", {})
        fit_weight = total_calc.get("fit_weight", 0)
        intent_weight = total_calc.get("intent_weight", 0)
        
        if abs(fit_weight + intent_weight - 1.0) > 0.001:
            errors.append(f"fit_weight ({fit_weight}) + intent_weight ({intent_weight}) must equal 1.0")
        
        # Validate score bands don't overlap
        score_bands = config.get("score_bands", {})
        if score_bands:
            bands = ["hot", "warm", "cold", "unqualified"]
            for i, band in enumerate(bands[:-1]):
                current_max = score_bands.get(band, {}).get("max_score", 0)
                next_min = score_bands.get(bands[i + 1], {}).get("min_score", 0)
                if current_max <= next_min:
                    warnings.append(f"Score band gap between {band} and {bands[i + 1]}: {band} max ({current_max}) should be > {bands[i + 1]} min ({next_min})")
        
        # Validate weights sum to reasonable values
        fit_weights = config.get("fit_scoring", {}).get("weights", {})
        if fit_weights:
            weight_sum = sum(fit_weights.values())
            if weight_sum == 0:
                errors.append("Fit scoring weights sum to 0 - no scoring will occur")
            elif weight_sum > 2.0:
                warnings.append(f"Fit scoring weights sum to {weight_sum:.2f} - consider normalizing")
        
        return errors, warnings
    
    def _validate_outreach_config(self, config: Dict[str, Any]) -> tuple[List[str], List[str]]:
        """Custom validation for outreach personalization configuration."""
        errors = []
        warnings = []
        
        # Validate personalization scoring weights sum to 1.0
        scoring = config.get("personalization_scoring", {})
        if scoring:
            weights = scoring.get("weights", {})
            if weights:
                weight_sum = sum(weights.values())
                if abs(weight_sum - 1.0) > 0.001:
                    errors.append(f"Personalization scoring weights sum to {weight_sum:.3f}, must equal 1.0")
        
        # Validate that all role messaging strategies have required fields
        role_strategies = config.get("role_messaging_strategies", {})
        required_roles = ["general_manager", "operations_manager", "fb_manager", "golf_professional", "it_manager"]
        
        for role in required_roles:
            if role not in role_strategies:
                warnings.append(f"Missing messaging strategy for role: {role}")
            else:
                strategy = role_strategies[role]
                if not strategy.get("focus_areas"):
                    warnings.append(f"No focus areas defined for role: {role}")
                if not strategy.get("key_metrics"):
                    warnings.append(f"No key metrics defined for role: {role}")
        
        # Validate template completeness
        templates = config.get("personalization_templates", {})
        template_types = ["cold_outreach", "follow_up", "demo_invitation"]
        template_components = ["subject_templates", "intro_templates", "value_prop_templates", "cta_templates"]
        
        for template_type in template_types:
            if template_type in templates:
                for component in template_components:
                    component_templates = templates[template_type].get(component, [])
                    if len(component_templates) < 2:
                        warnings.append(f"Only {len(component_templates)} {component} for {template_type} - consider adding variety")
        
        return errors, warnings
    
    def validate_all_configs(self) -> Dict[str, ValidationResult]:
        """Validate all known configuration files."""
        results = {}
        
        for config_name in self.schema_mappings.keys():
            config_path = self.config_dir / config_name
            if config_path.exists():
                results[config_name] = self.validate_config_file(config_path)
            else:
                results[config_name] = ValidationResult(
                    is_valid=False,
                    errors=[f"Configuration file not found: {config_path}"],
                    warnings=[],
                    config_path=str(config_path)
                )
        
        return results
    
    def print_validation_report(self, results: Dict[str, ValidationResult]) -> None:
        """Print a formatted validation report."""
        print("Configuration Validation Report")
        print("=" * 50)
        
        total_configs = len(results)
        valid_configs = sum(1 for r in results.values() if r.is_valid)
        
        print(f"Total configurations: {total_configs}")
        print(f"Valid configurations: {valid_configs}")
        print(f"Invalid configurations: {total_configs - valid_configs}")
        print()
        
        for config_name, result in results.items():
            status = "✅ VALID" if result.is_valid else "❌ INVALID"
            print(f"{config_name}: {status}")
            
            if result.errors:
                for error in result.errors:
                    print(f"  ERROR: {error}")
            
            if result.warnings:
                for warning in result.warnings:
                    print(f"  WARNING: {warning}")
            
            print()


def validate_config_on_startup(config_path: Union[str, Path]) -> None:
    """Validate a configuration file on agent startup and raise if invalid."""
    validator = ConfigValidator()
    result = validator.validate_config_file(config_path)
    
    if not result.is_valid:
        error_msg = f"Configuration validation failed for {config_path}:\n"
        for error in result.errors:
            error_msg += f"  - {error}\n"
        raise ValueError(error_msg)
    
    # Log warnings
    if result.warnings:
        logger = logging.getLogger(__name__)
        for warning in result.warnings:
            logger.warning(f"Config validation warning for {config_path}: {warning}")


# Convenience function for CLI usage
def main():
    """CLI entry point for configuration validation."""
    import sys
    
    validator = ConfigValidator()
    
    if len(sys.argv) > 1:
        # Validate specific config file
        config_path = sys.argv[1]
        result = validator.validate_config_file(config_path)
        
        if result.is_valid:
            print(f"✅ {config_path} is valid")
            if result.warnings:
                for warning in result.warnings:
                    print(f"  WARNING: {warning}")
            sys.exit(0)
        else:
            print(f"❌ {config_path} is invalid")
            for error in result.errors:
                print(f"  ERROR: {error}")
            sys.exit(1)
    else:
        # Validate all configs
        results = validator.validate_all_configs()
        validator.print_validation_report(results)
        
        # Exit with error code if any configs are invalid
        if any(not r.is_valid for r in results.values()):
            sys.exit(1)


if __name__ == "__main__":
    main()

