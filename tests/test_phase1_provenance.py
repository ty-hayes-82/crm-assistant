#!/usr/bin/env python3
"""
Unit tests for Phase 1 provenance requirements.

Tests that data quality agent fails when any field lacks source_urls or last_verified_at.
This is a specific requirement from Phase 1 acceptance criteria.
"""

import pytest
from datetime import datetime
from crm_agent.core.state_models import (
    CRMEnrichmentResult,
    validate_enrichment_result_provenance,
    create_enrichment_result_with_provenance
)


class TestProvenanceValidation:
    """Test provenance validation requirements for Phase 1."""
    
    def test_valid_enrichment_result_passes(self):
        """Test that valid enrichment results with proper provenance pass validation."""
        result = create_enrichment_result_with_provenance(
            field_name="swoop_course_type",
            proposed_value="resort",
            source_urls=["https://pebblebeach.com/about"],
            confidence=0.9,
            source="Company website"
        )
        
        # Should not raise an exception
        assert validate_enrichment_result_provenance(result) is True
        assert result.source_urls == ["https://pebblebeach.com/about"]
        assert result.last_verified_at is not None
        assert result.field_name == "swoop_course_type"
        assert result.proposed_value == "resort"
    
    def test_missing_source_urls_fails(self):
        """Test that enrichment results without source_urls fail validation."""
        result = CRMEnrichmentResult(
            field_name="industry",
            proposed_value="Golf Course Management",
            confidence=0.9,
            source="Unknown source",
            source_urls=[],  # Empty - should fail
            last_verified_at=datetime.now()
        )
        
        with pytest.raises(ValueError) as exc_info:
            validate_enrichment_result_provenance(result)
        
        assert "missing required source_urls" in str(exc_info.value)
        assert "industry" in str(exc_info.value)
    
    def test_missing_last_verified_at_fails(self):
        """Test that enrichment results without last_verified_at fail validation."""
        result = CRMEnrichmentResult(
            field_name="swoop_holes",
            proposed_value="18",
            confidence=0.85,
            source="Course website",
            source_urls=["https://example.com/course-info"],
            last_verified_at=None  # Missing - should fail
        )
        
        with pytest.raises((ValueError, TypeError)):
            validate_enrichment_result_provenance(result)
    
    def test_invalid_url_format_fails(self):
        """Test that enrichment results with invalid URL formats fail validation."""
        result = CRMEnrichmentResult(
            field_name="swoop_management_company",
            proposed_value="Test Management Co",
            confidence=0.8,
            source="Invalid source",
            source_urls=["not-a-valid-url", "also-invalid"],  # Invalid URL formats
            last_verified_at=datetime.now()
        )
        
        with pytest.raises(ValueError) as exc_info:
            validate_enrichment_result_provenance(result)
        
        assert "invalid source URL" in str(exc_info.value)
        assert "not-a-valid-url" in str(exc_info.value)
    
    def test_multiple_valid_source_urls_passes(self):
        """Test that multiple valid source URLs pass validation."""
        result = create_enrichment_result_with_provenance(
            field_name="swoop_amenities",
            proposed_value="range, lessons, dining, events",
            source_urls=[
                "https://pebblebeach.com/amenities",
                "https://pebblebeach.com/facilities",
                "https://pebblebeach.com/dining"
            ],
            confidence=0.95,
            source="Multiple website pages"
        )
        
        assert validate_enrichment_result_provenance(result) is True
        assert len(result.source_urls) == 3
        assert all(url.startswith('https://') for url in result.source_urls)
    
    def test_create_with_provenance_factory_enforces_validation(self):
        """Test that the factory function enforces validation."""
        # Valid creation should work
        result = create_enrichment_result_with_provenance(
            field_name="swoop_par",
            proposed_value="72",
            source_urls=["https://example-golf.com/scorecard"],
            confidence=0.9
        )
        assert result.field_name == "swoop_par"
        assert result.proposed_value == "72"
        
        # Invalid creation should fail
        with pytest.raises(ValueError):
            create_enrichment_result_with_provenance(
                field_name="swoop_par",
                proposed_value="72",
                source_urls=[],  # Empty - should fail
                confidence=0.9
            )
    
    def test_golf_course_specific_fields_validation(self):
        """Test validation for golf course specific fields from the strategy doc."""
        golf_fields = [
            ("swoop_course_type", "resort"),
            ("swoop_holes", "18"),
            ("swoop_par", "72"),
            ("swoop_course_rating", "74.2"),
            ("swoop_slope", "142"),
            ("swoop_booking_engine", "https://teesheet.example.com"),
            ("swoop_management_company", "Pebble Beach Company"),
            ("swoop_amenities", "range, lessons, dining, events"),
            ("swoop_unique_hook", "Iconic oceanside course with stunning views"),
        ]
        
        for field_name, value in golf_fields:
            result = create_enrichment_result_with_provenance(
                field_name=field_name,
                proposed_value=value,
                source_urls=[f"https://example-golf.com/{field_name.replace('swoop_', '')}"],
                confidence=0.8,
                source="Golf course website"
            )
            
            # Should pass validation
            assert validate_enrichment_result_provenance(result) is True
            assert result.field_name == field_name
            assert result.proposed_value == value
            assert len(result.source_urls) == 1
            assert result.last_verified_at is not None


class TestDataQualityGate:
    """Test that the data quality gate enforces provenance requirements."""
    
    def test_data_quality_gate_rejects_missing_provenance(self):
        """Test that any enrichment result without proper provenance is rejected."""
        # This is the core Phase 1 requirement: 
        # "Add a unit test to fail when any field lacks source_urls or last_verified_at"
        
        invalid_results = [
            # Missing source_urls
            CRMEnrichmentResult(
                field_name="industry",
                proposed_value="Golf Course",
                confidence=0.9,
                source="Web search",
                source_urls=[],  # Missing
                last_verified_at=datetime.now()
            ),
            # Missing last_verified_at
            CRMEnrichmentResult(
                field_name="company_size",
                proposed_value="50-100 employees",
                confidence=0.8,
                source="LinkedIn",
                source_urls=["https://linkedin.com/company/example"],
                last_verified_at=None  # Missing
            ),
            # Invalid URL format
            CRMEnrichmentResult(
                field_name="location",
                proposed_value="Pebble Beach, CA",
                confidence=0.95,
                source="Company website",
                source_urls=["invalid-url"],  # Invalid format
                last_verified_at=datetime.now()
            )
        ]
        
        for result in invalid_results:
            with pytest.raises((ValueError, TypeError)):
                validate_enrichment_result_provenance(result)
    
    def test_data_quality_gate_accepts_valid_provenance(self):
        """Test that enrichment results with proper provenance are accepted."""
        valid_results = [
            create_enrichment_result_with_provenance(
                field_name="swoop_course_type",
                proposed_value="resort",
                source_urls=["https://pebblebeach.com/about"],
                confidence=0.9
            ),
            create_enrichment_result_with_provenance(
                field_name="swoop_holes",
                proposed_value="18",
                source_urls=["https://augustanational.com/course"],
                confidence=0.95
            ),
            create_enrichment_result_with_provenance(
                field_name="swoop_management_company",
                proposed_value="Pinehurst Resort",
                source_urls=[
                    "https://pinehurst.com/about",
                    "https://pinehurst.com/management"
                ],
                confidence=0.85
            )
        ]
        
        for result in valid_results:
            # Should not raise any exceptions
            assert validate_enrichment_result_provenance(result) is True


if __name__ == "__main__":
    # Run the tests directly if called as a script
    pytest.main([__file__, "-v"])
