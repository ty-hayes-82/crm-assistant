#!/usr/bin/env python3
"""
Unit tests for Phase 1 provenance gate enforcement.
Tests that enrichment results require source_urls and last_verified_at.
"""

import pytest
from datetime import datetime
from crm_agent.core.state_models import CRMEnrichmentResult


class TestProvenanceGate:
    """Test Phase 1 provenance gate requirements."""
    
    def test_valid_enrichment_result_passes_provenance(self):
        """Test that enrichment result with proper provenance passes validation."""
        result = CRMEnrichmentResult(
            field_name="industry",
            current_value="Unknown",
            proposed_value="Software",
            confidence=0.9,
            source="company_website",
            source_urls=["https://example.com/about"],
            last_verified_at=datetime.now()
        )
        
        assert result.validate_provenance() == True
        assert result.get_provenance_errors() == []
    
    def test_missing_source_urls_fails_provenance(self):
        """Test that enrichment result without source_urls fails validation."""
        result = CRMEnrichmentResult(
            field_name="industry",
            current_value="Unknown",
            proposed_value="Software",
            confidence=0.9,
            source="company_website",
            source_urls=[],  # Empty source_urls
            last_verified_at=datetime.now()
        )
        
        assert result.validate_provenance() == False
        errors = result.get_provenance_errors()
        assert "Missing source_urls" in errors
    
    def test_missing_source_fails_provenance(self):
        """Test that enrichment result without source fails validation."""
        result = CRMEnrichmentResult(
            field_name="industry",
            current_value="Unknown",
            proposed_value="Software",
            confidence=0.9,
            source="",  # Empty source
            source_urls=["https://example.com/about"],
            last_verified_at=datetime.now()
        )
        
        assert result.validate_provenance() == False
        errors = result.get_provenance_errors()
        assert "Missing source" in errors
    
    def test_missing_last_verified_at_fails_provenance(self):
        """Test that enrichment result without last_verified_at fails validation."""
        result = CRMEnrichmentResult(
            field_name="industry",
            current_value="Unknown",
            proposed_value="Software",
            confidence=0.9,
            source="company_website",
            source_urls=["https://example.com/about"],
            last_verified_at=None  # Missing timestamp
        )
        
        assert result.validate_provenance() == False
        errors = result.get_provenance_errors()
        assert "Missing last_verified_at" in errors
    
    def test_multiple_missing_fields_reports_all_errors(self):
        """Test that multiple missing provenance fields are all reported."""
        result = CRMEnrichmentResult(
            field_name="industry",
            current_value="Unknown",
            proposed_value="Software",
            confidence=0.9,
            source="",  # Missing source
            source_urls=[],  # Missing source_urls
            last_verified_at=None  # Missing timestamp
        )
        
        assert result.validate_provenance() == False
        errors = result.get_provenance_errors()
        assert "Missing source_urls" in errors
        assert "Missing source" in errors
        assert "Missing last_verified_at" in errors
        assert len(errors) == 3
    
    def test_multiple_source_urls_valid(self):
        """Test that multiple source URLs are accepted."""
        result = CRMEnrichmentResult(
            field_name="industry",
            current_value="Unknown",
            proposed_value="Software",
            confidence=0.9,
            source="multiple_sources",
            source_urls=[
                "https://example.com/about",
                "https://example.com/products",
                "https://linkedin.com/company/example"
            ],
            last_verified_at=datetime.now()
        )
        
        assert result.validate_provenance() == True
        assert result.get_provenance_errors() == []
    
    def test_enrichment_result_with_default_timestamp(self):
        """Test that default timestamp generation works for provenance."""
        result = CRMEnrichmentResult(
            field_name="industry",
            current_value="Unknown",
            proposed_value="Software",
            confidence=0.9,
            source="company_website",
            source_urls=["https://example.com/about"]
            # last_verified_at will use default_factory=datetime.now
        )
        
        assert result.validate_provenance() == True
        assert result.last_verified_at is not None
        assert isinstance(result.last_verified_at, datetime)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
