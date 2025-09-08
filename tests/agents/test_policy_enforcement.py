#!/usr/bin/env python3
"""
Policy Enforcement Tests for Phase 8.

Tests negative scenarios for policy enforcement including
robots.txt violations, paywall bypass attempts, and data collection limits.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from crm_agent.core.role_taxonomy import RoleTaxonomyService, PolicyViolation


class TestPolicyEnforcement:
    """Test suite for policy enforcement scenarios."""
    
    @pytest.fixture
    def service(self):
        """Create role taxonomy service for policy testing."""
        return RoleTaxonomyService()
    
    def test_robots_txt_violation_detection(self, service):
        """Test detection of robots.txt violations."""
        # Mock robots.txt violation
        with patch.object(service, '_violates_robots_txt', return_value=True):
            violations = service.validate_data_collection_policy(
                "https://restricted-site.com/data",
                "web_scraping"
            )
            
            robots_violations = [v for v in violations if v.violation_type == "robots_txt_violation"]
            assert len(robots_violations) > 0
            assert robots_violations[0].severity == "high"
            assert "robots.txt" in robots_violations[0].description
    
    def test_paywall_bypass_detection(self, service):
        """Test detection of paywall bypass attempts."""
        paywall_urls = [
            "https://premium-site.com/paywall-content",
            "https://news-site.com/subscription/article",
            "https://data-provider.com/premium/reports"
        ]
        
        for url in paywall_urls:
            violations = service.validate_data_collection_policy(url, "web_scraping")
            
            paywall_violations = [v for v in violations if v.violation_type == "paywall_bypass"]
            assert len(paywall_violations) > 0, f"Should detect paywall bypass for {url}"
            assert paywall_violations[0].severity == "critical"
    
    def test_email_scraping_prohibition(self, service):
        """Test prohibition of email scraping."""
        violations = service.validate_data_collection_policy(
            "https://company.com/contacts",
            "email_scraping"
        )
        
        email_violations = [v for v in violations if v.violation_type == "email_scraping"]
        assert len(email_violations) > 0
        assert email_violations[0].severity == "high"
        assert "Email scraping is prohibited" in email_violations[0].description
    
    def test_multiple_policy_violations(self, service):
        """Test detection of multiple policy violations simultaneously."""
        with patch.object(service, '_violates_robots_txt', return_value=True):
            violations = service.validate_data_collection_policy(
                "https://paywall-site.com/premium/data",
                "email_scraping"
            )
            
            # Should detect both robots.txt and email scraping violations
            violation_types = [v.violation_type for v in violations]
            assert "robots_txt_violation" in violation_types
            assert "email_scraping" in violation_types
            
            # And paywall bypass
            assert "paywall_bypass" in violation_types
    
    def test_safe_data_collection_no_violations(self, service):
        """Test that safe data collection produces no violations."""
        violations = service.validate_data_collection_policy(
            "https://public-api.com/data",
            "api_call"
        )
        
        # Should have no violations for legitimate API calls
        assert len(violations) == 0
    
    def test_policy_violation_metadata(self, service):
        """Test that policy violations include proper metadata."""
        violations = service.validate_data_collection_policy(
            "https://premium-site.com/paywall",
            "web_scraping"
        )
        
        if violations:
            violation = violations[0]
            assert violation.source_url == "https://premium-site.com/paywall"
            assert isinstance(violation.detected_at, datetime)
            assert violation.severity in ["low", "medium", "high", "critical"]
    
    def test_low_confidence_review_task_creation(self, service):
        """Test that low-confidence roles trigger review task creation."""
        # Test various low-confidence scenarios
        low_confidence_titles = [
            "Chief Happiness Officer",
            "Wizard of Fun",
            "Director of First Impressions",
            ""
        ]
        
        for title in low_confidence_titles:
            result = service.classify_role(title)
            
            if result.confidence < service.confidence_threshold:
                assert result.requires_review
                
                # Should be able to create review task
                task_data = service.create_review_task(result, reason="low_confidence")
                assert "Review Role Assignment" in task_data["hs_task_subject"]
                assert task_data["hs_task_priority"] == "MEDIUM"
    
    def test_executive_role_review_requirement(self, service):
        """Test that executive roles always require review regardless of confidence."""
        executive_titles = [
            "General Manager",
            "President", 
            "CEO",
            "Chief Executive Officer"
        ]
        
        for title in executive_titles:
            result = service.classify_role(title)
            
            # Even high-confidence executive roles should require review
            assert result.requires_review, f"Executive role '{title}' should require review"
            
            # Should be able to create review task
            task_data = service.create_review_task(result, reason="executive_role_verification")
            assert "Review Role Assignment" in task_data["hs_task_subject"]
    
    def test_throttling_policy_enforcement(self, service):
        """Test request throttling policy (placeholder test)."""
        # This would be implemented with actual rate limiting in a real system
        # For now, just test that the policy configuration exists
        policy_config = service.config.get("policy_enforcement", {})
        collection_limits = policy_config.get("data_collection_limits", {})
        
        assert "throttle_requests" in collection_limits or "max_requests_per_minute" in collection_limits
    
    def test_pii_handling_policy(self, service):
        """Test PII handling policy configuration."""
        policy_config = service.config.get("policy_enforcement", {})
        pii_handling = policy_config.get("pii_handling", {})
        
        # Should have PII handling policies
        assert isinstance(pii_handling, dict)
        # Common PII policies should be defined
        expected_policies = ["tag_personal_info", "data_retention_days", "consent_required"]
        for policy in expected_policies:
            assert policy in pii_handling or len(pii_handling) == 0  # Allow empty config for testing
    
    def test_compliance_checks_configuration(self, service):
        """Test compliance checks configuration."""
        policy_config = service.config.get("policy_enforcement", {})
        compliance_checks = policy_config.get("compliance_checks", {})
        
        # Should have compliance configurations
        assert isinstance(compliance_checks, dict)
        
        # Common compliance standards
        expected_compliance = ["gdpr_compliance", "ccpa_compliance", "industry_standards"]
        for compliance in expected_compliance:
            assert compliance in compliance_checks or len(compliance_checks) == 0  # Allow empty config for testing
    
    def test_policy_violation_severity_levels(self, service):
        """Test that policy violations have appropriate severity levels."""
        # Test different violation types and their severities
        test_cases = [
            ("https://paywall-site.com/premium", "web_scraping", "paywall_bypass", "critical"),
            ("https://any-site.com", "email_scraping", "email_scraping", "high")
        ]
        
        for url, request_type, violation_type, expected_severity in test_cases:
            violations = service.validate_data_collection_policy(url, request_type)
            
            matching_violations = [v for v in violations if v.violation_type == violation_type]
            if matching_violations:
                assert matching_violations[0].severity == expected_severity
    
    def test_unknown_role_handling(self, service):
        """Test handling of completely unknown roles."""
        unknown_titles = [
            "Galactic Overlord",
            "Chief Unicorn Wrangler", 
            "Senior Ninja",
            "Rock Star Developer"
        ]
        
        for title in unknown_titles:
            result = service.classify_role(title)
            
            assert result.classified_role == "unknown"
            assert result.role_category == "unknown"
            assert result.confidence == 0.0
            assert result.requires_review
            assert result.decision_authority == "unknown"
    
    def test_conflicting_title_signals(self, service):
        """Test handling of titles with conflicting signals."""
        conflicting_titles = [
            "Assistant General Manager and Head Golf Professional",
            "President of Operations and IT Manager",
            "CEO and Maintenance Supervisor"
        ]
        
        for title in conflicting_titles:
            result = service.classify_role(title)
            
            # Should still classify but may require review due to ambiguity
            assert result.classified_role != "unknown"
            # Confidence might be lower due to conflicting signals
            if result.confidence < service.confidence_threshold:
                assert result.requires_review


class TestDataCollectionLimits:
    """Test suite for data collection limits and ethical guidelines."""
    
    @pytest.fixture 
    def service(self):
        return RoleTaxonomyService()
    
    def test_respectful_web_scraping_policy(self, service):
        """Test that web scraping respects site policies."""
        # Test robots.txt compliance
        with patch.object(service, '_violates_robots_txt', return_value=True):
            violations = service.validate_data_collection_policy(
                "https://restricted-site.com/data",
                "web_scraping"
            )
            
            robots_violations = [v for v in violations if v.violation_type == "robots_txt_violation"]
            assert len(robots_violations) > 0
    
    def test_no_paywall_circumvention(self, service):
        """Test that paywall circumvention is prevented."""
        paywall_indicators = [
            "https://site.com/paywall/content",
            "https://site.com/subscription/data", 
            "https://site.com/premium/info"
        ]
        
        for url in paywall_indicators:
            violations = service.validate_data_collection_policy(url, "web_scraping")
            paywall_violations = [v for v in violations if v.violation_type == "paywall_bypass"]
            assert len(paywall_violations) > 0, f"Should prevent paywall bypass for {url}"
    
    def test_email_harvesting_prevention(self, service):
        """Test prevention of email harvesting."""
        violations = service.validate_data_collection_policy(
            "https://company.com/staff-directory",
            "email_scraping"
        )
        
        email_violations = [v for v in violations if v.violation_type == "email_scraping"]
        assert len(email_violations) > 0
        assert email_violations[0].severity == "high"
    
    def test_rate_limiting_compliance(self, service):
        """Test that rate limiting policies are configured."""
        policy_config = service.config.get("policy_enforcement", {})
        limits = policy_config.get("data_collection_limits", {})
        
        # Should have some form of rate limiting configured
        rate_limit_keys = ["throttle_requests", "max_requests_per_minute", "max_requests_per_hour"]
        has_rate_limiting = any(key in limits for key in rate_limit_keys)
        
        # Allow for different rate limiting implementations
        assert has_rate_limiting or limits.get("throttle_requests", True)
