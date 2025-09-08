#!/usr/bin/env python3
"""
Unit tests for Role Taxonomy Service (Phase 8).

Tests role classification, confidence scoring, policy enforcement,
and review task creation functionality.
"""

import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

from crm_agent.core.role_taxonomy import (
    RoleTaxonomyService, 
    RoleClassificationResult, 
    PolicyViolation,
    create_role_taxonomy_service
)


class TestRoleTaxonomyService:
    """Test suite for role taxonomy service."""
    
    @pytest.fixture
    def service(self):
        """Create role taxonomy service for testing."""
        return create_role_taxonomy_service()
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        return {
            "version": "1.0.0-test",
            "confidence_threshold": 0.75,
            "role_categories": {
                "executive": {
                    "decision_authority": "high",
                    "typical_influence": "strategic",
                    "roles": ["general_manager", "president", "ceo"]
                },
                "operations": {
                    "decision_authority": "medium",
                    "typical_influence": "operational", 
                    "roles": ["operations_manager"]
                }
            },
            "title_synonyms": {
                "general_manager": {
                    "exact_matches": ["general manager", "gm", "club manager"],
                    "partial_matches": ["general mgr", "gen manager"],
                    "confidence_weights": {
                        "exact_matches": 1.0,
                        "partial_matches": 0.9
                    }
                },
                "president": {
                    "exact_matches": ["president", "club president"],
                    "partial_matches": ["pres"],
                    "confidence_weights": {
                        "exact_matches": 1.0,
                        "partial_matches": 0.8
                    }
                }
            },
            "confidence_scoring": {
                "factors": {
                    "company_size_alignment": 0.4,
                    "industry_context": 0.3,
                    "contextual_keywords": 0.6
                },
                "auto_assign_threshold": 0.9
            },
            "policy_enforcement": {
                "data_collection_limits": {
                    "respect_robots_txt": True,
                    "avoid_paywall_bypass": True,
                    "no_email_scraping": True
                }
            }
        }
    
    def test_exact_title_match_high_confidence(self, service):
        """Test exact title match produces high confidence."""
        result = service.classify_role("General Manager")
        
        assert result.classified_role == "general_manager"
        assert result.confidence >= 0.9
        assert result.role_category == "executive"
        assert result.decision_authority == "high"
        assert not result.requires_review  # High confidence, auto-assign
    
    def test_partial_title_match_medium_confidence(self, service):
        """Test partial title match produces medium confidence."""
        result = service.classify_role("Gen Manager")
        
        assert result.classified_role == "general_manager"
        assert 0.7 <= result.confidence < 0.9
        assert result.role_category == "executive"
        assert result.requires_review  # Executive always requires review
    
    def test_case_insensitive_matching(self, service):
        """Test that title matching is case-insensitive."""
        results = [
            service.classify_role("GENERAL MANAGER"),
            service.classify_role("general manager"),
            service.classify_role("General Manager"),
            service.classify_role("GeNeRaL mAnAgEr")
        ]
        
        for result in results:
            assert result.classified_role == "general_manager"
            assert result.confidence >= 0.9
    
    def test_unknown_title_classification(self, service):
        """Test classification of unknown titles."""
        result = service.classify_role("Chief Happiness Officer")
        
        assert result.classified_role == "unknown"
        assert result.confidence == 0.0
        assert result.role_category == "unknown"
        assert result.requires_review
    
    def test_empty_title_handling(self, service):
        """Test handling of empty or None titles."""
        results = [
            service.classify_role(""),
            service.classify_role(None),
            service.classify_role("   ")
        ]
        
        for result in results:
            assert result.classified_role == "unknown"
            assert result.confidence == 0.0
            assert result.requires_review
    
    def test_company_context_confidence_boost(self, service):
        """Test that company context improves confidence."""
        company_context = {
            "name": "Augusta National Golf Club",
            "numberofemployees": 150,
            "industry": "Golf Course"
        }
        
        result_with_context = service.classify_role(
            "General Manager", 
            company_context=company_context
        )
        result_without_context = service.classify_role("General Manager")
        
        # Context should boost confidence
        assert result_with_context.confidence >= result_without_context.confidence
        assert "company_size_alignment" in result_with_context.confidence_factors
    
    def test_confidence_factors_tracking(self, service):
        """Test that confidence factors are properly tracked."""
        result = service.classify_role("GM", company_context={"numberofemployees": 50})
        
        assert "base_title_match" in result.confidence_factors
        assert "company_size_alignment" in result.confidence_factors
        assert "industry_context" in result.confidence_factors
        assert "contextual_keywords" in result.confidence_factors
    
    def test_executive_roles_require_review(self, service):
        """Test that executive roles always require review."""
        executive_titles = ["General Manager", "President", "CEO", "Owner"]
        
        for title in executive_titles:
            result = service.classify_role(title)
            assert result.requires_review, f"Executive role {title} should require review"
    
    def test_high_confidence_auto_assignment(self, service):
        """Test that very high confidence bypasses review for non-executives."""
        # Mock a non-executive role with very high confidence
        with patch.object(service, '_get_role_metadata') as mock_metadata:
            mock_metadata.return_value = ("operations", {"decision_authority": "medium"})
            
            result = service.classify_role("Operations Manager")
            
            # If confidence is very high, should not require review
            if result.confidence >= 0.9:
                assert not result.requires_review
    
    def test_policy_violation_detection(self, service):
        """Test policy violation detection."""
        violations = service.validate_data_collection_policy(
            "https://example.com/paywall-content", 
            "web_scraping"
        )
        
        # Should detect paywall bypass attempt
        paywall_violations = [v for v in violations if v.violation_type == "paywall_bypass"]
        assert len(paywall_violations) > 0
        assert paywall_violations[0].severity == "critical"
    
    def test_email_scraping_policy_violation(self, service):
        """Test email scraping policy violation."""
        violations = service.validate_data_collection_policy(
            "https://example.com/contacts",
            "email_scraping"
        )
        
        email_violations = [v for v in violations if v.violation_type == "email_scraping"]
        assert len(email_violations) > 0
        assert email_violations[0].severity == "high"
    
    def test_review_task_creation(self, service):
        """Test creation of review tasks for low-confidence assignments."""
        # Create a low-confidence result
        classification_result = RoleClassificationResult(
            original_title="Mysterious Title",
            classified_role="unknown",
            role_category="unknown",
            confidence=0.3,
            decision_authority="unknown",
            typical_influence="unknown",
            requires_review=True
        )
        
        task_data = service.create_review_task(
            classification_result,
            contact_id="12345",
            reason="low_confidence_role_assignment"
        )
        
        assert "hs_task_subject" in task_data
        assert "Mysterious Title" in task_data["hs_task_subject"]
        assert task_data["hs_task_status"] == "NOT_STARTED"
        assert task_data["hs_task_priority"] == "MEDIUM"
        assert "associations" in task_data
        assert "12345" in task_data["associations"]["contact"]
    
    def test_role_metadata_retrieval(self, service):
        """Test retrieval of role metadata."""
        category, metadata = service._get_role_metadata("general_manager")
        
        assert category == "executive"
        assert metadata["decision_authority"] == "high"
        assert metadata["typical_influence"] == "strategic"
    
    def test_title_pattern_compilation(self, service):
        """Test that title patterns are properly compiled."""
        assert hasattr(service, 'title_patterns')
        assert "general_manager" in service.title_patterns
        
        patterns = service.title_patterns["general_manager"]
        assert len(patterns) > 0
        
        # Each pattern should be a tuple of (compiled_regex, weight)
        for pattern, weight in patterns:
            assert hasattr(pattern, 'search')  # Compiled regex has search method
            assert isinstance(weight, (int, float))
    
    def test_confidence_normalization(self, service):
        """Test that confidence scores are properly normalized to [0, 1]."""
        # Test with various titles that might produce different confidence scores
        test_titles = [
            "General Manager",
            "GM", 
            "Assistant Manager",
            "Unknown Title",
            ""
        ]
        
        for title in test_titles:
            result = service.classify_role(title)
            assert 0.0 <= result.confidence <= 1.0, f"Confidence for '{title}' not in [0,1]: {result.confidence}"
    
    def test_messaging_strategy_integration(self, service):
        """Test integration with messaging strategy."""
        strategy = service.get_role_messaging_strategy("general_manager")
        
        assert isinstance(strategy, dict)
        assert "focus_areas" in strategy
        assert "decision_authority" in strategy
    
    def test_fallback_config_handling(self):
        """Test handling of fallback configuration when main config fails."""
        # Test with invalid config path
        service = RoleTaxonomyService(config_path=Path("/nonexistent/path/config.json"))
        
        assert service.config["version"] == "fallback"
        
        # Should still be able to classify basic roles
        result = service.classify_role("General Manager")
        assert result.classified_role == "general_manager"
    
    def test_multiple_pattern_matching(self, service):
        """Test that multiple patterns can match the same title."""
        # A title that might match multiple patterns
        result = service.classify_role("General Manager and President")
        
        # Should pick the best match
        assert result.classified_role in ["general_manager", "president"]
        assert result.confidence > 0.5
        assert len(result.matched_synonyms) > 0


class TestRoleClassificationResult:
    """Test suite for RoleClassificationResult model."""
    
    def test_result_model_validation(self):
        """Test that result model validates properly."""
        result = RoleClassificationResult(
            original_title="Test Title",
            classified_role="test_role",
            role_category="test_category",
            confidence=0.85,
            decision_authority="medium",
            typical_influence="departmental"
        )
        
        assert result.original_title == "Test Title"
        assert result.confidence == 0.85
        assert isinstance(result.classification_timestamp, datetime)
    
    def test_confidence_validation(self):
        """Test confidence score validation."""
        # Valid confidence
        result = RoleClassificationResult(
            original_title="Test",
            classified_role="test",
            role_category="test",
            confidence=0.75,
            decision_authority="medium",
            typical_influence="departmental"
        )
        assert result.confidence == 0.75
        
        # Invalid confidence should raise validation error
        with pytest.raises(ValueError):
            RoleClassificationResult(
                original_title="Test",
                classified_role="test", 
                role_category="test",
                confidence=1.5,  # Invalid: > 1.0
                decision_authority="medium",
                typical_influence="departmental"
            )


class TestPolicyViolation:
    """Test suite for PolicyViolation model."""
    
    def test_policy_violation_creation(self):
        """Test policy violation model creation."""
        violation = PolicyViolation(
            violation_type="robots_txt_violation",
            description="Test violation",
            source_url="https://example.com",
            severity="high"
        )
        
        assert violation.violation_type == "robots_txt_violation"
        assert violation.severity == "high"
        assert isinstance(violation.detected_at, datetime)


def test_factory_function():
    """Test the factory function creates service properly."""
    service = create_role_taxonomy_service()
    assert isinstance(service, RoleTaxonomyService)
    assert hasattr(service, 'classify_role')
    assert hasattr(service, 'validate_data_collection_policy')
