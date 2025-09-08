#!/usr/bin/env python3
"""
E2E integration tests for Lead Scoring Agent (Phase 6).
Tests pipeline integration and HubSpot field updates.
"""

import pytest
from unittest.mock import Mock, patch
from crm_agent.agents.specialized.lead_scoring_agent import create_lead_scoring_agent
from crm_agent.agents.workflows.crm_enrichment import create_crm_enrichment_pipeline
from crm_agent.core.state_models import CRMSessionState


class TestLeadScoringPipelineIntegration:
    """Test suite for Lead Scoring Agent pipeline integration."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.agent = create_lead_scoring_agent()
        
        # Test data representing a high-value prospect
        self.test_company_data = {
            "name": "Pebble Beach Golf Links",
            "company_type": "Resort",
            "management_company": "Troon",
            "annualrevenue": 25000000,  # 25M
            "state": "California",
            "numberofemployees": 200,
            "website": "https://pebblebeach.com/teesheet-booking",
            "description": "World-class resort golf course with full dining, events, and pro shop",
            "club_info": "Championship 18-hole course with oceanfront dining, event facilities, and full-service pro shop"
        }
        
        self.test_contact_data = {
            "email": "gm@pebblebeach.com",
            "jobtitle": "General Manager",
            "firstname": "John",
            "lastname": "Smith"
        }
    
    def test_lead_scoring_in_enrichment_pipeline(self):
        """Test that lead scoring agent integrates properly with enrichment pipeline."""
        # Create session state with test data
        state = CRMSessionState()
        state.company_data = self.test_company_data
        state.contact_data = self.test_contact_data
        
        # Execute lead scoring
        result = self.agent.score_and_store(state)
        
        # Verify scoring results
        assert "scores" in result
        assert "hubspot_updates" in result
        
        scores = result["scores"]
        hubspot_updates = result["hubspot_updates"]
        
        # This should be a high-scoring prospect (fit score high, intent score low due to no engagement)
        assert scores["fit_score"] >= 80, f"Expected high fit score >= 80, got {scores['fit_score']}"
        # Total score will be lower due to low intent score (fit_score * 0.6 + intent_score * 0.4)
        # With fit ~95 and intent ~0: 95*0.6 + 0*0.4 = 57
        assert scores["total_score"] >= 50, f"Expected total score >= 50, got {scores['total_score']}"
        
        # Verify HubSpot field mappings are correct
        expected_fields = [
            "swoop_fit_score",
            "swoop_intent_score", 
            "swoop_total_lead_score",
            "swoop_score_band",
            "swoop_score_updated_at",
            "swoop_scoring_version"
        ]
        
        for field in expected_fields:
            assert field in hubspot_updates, f"Missing HubSpot field: {field}"
        
        # Verify field values match scores
        assert hubspot_updates["swoop_fit_score"] == scores["fit_score"]
        assert hubspot_updates["swoop_intent_score"] == scores["intent_score"]
        assert hubspot_updates["swoop_total_lead_score"] == scores["total_score"]
        assert hubspot_updates["swoop_score_band"] == scores["score_band"]
        assert hubspot_updates["swoop_scoring_version"] == scores["scoring_version"]
        
        # Verify state was updated
        assert state.lead_scores == scores
    
    def test_hubspot_field_mapping_configuration(self):
        """Test that HubSpot field mapping respects configuration."""
        # Test with default configuration
        state = CRMSessionState()
        state.company_data = self.test_company_data
        state.contact_data = self.test_contact_data
        
        result = self.agent.score_and_store(state)
        hubspot_updates = result["hubspot_updates"]
        
        # Verify all expected Swoop fields are present
        assert "swoop_fit_score" in hubspot_updates
        assert "swoop_intent_score" in hubspot_updates
        assert "swoop_total_lead_score" in hubspot_updates
        assert "swoop_score_band" in hubspot_updates
        assert "swoop_score_updated_at" in hubspot_updates
        assert "swoop_scoring_version" in hubspot_updates
    
    def test_score_band_classification_integration(self):
        """Test score band classification with different prospect profiles."""
        # Test Hot prospect (high fit + some intent)
        hot_prospect_data = {
            **self.test_company_data,
            "company_type": "Private",  # Higher fit score
            "management_company": "Troon",
            "annualrevenue": 50000000,  # Very high revenue
        }
        
        state = CRMSessionState()
        state.company_data = hot_prospect_data
        state.contact_data = self.test_contact_data
        
        result = self.agent.score_and_store(state)
        scores = result["scores"]
        
        # Should be high fit score
        assert scores["fit_score"] >= 85
        
        # Test Cold prospect (lower fit)
        cold_prospect_data = {
            "name": "Municipal Golf Course",
            "company_type": "Municipal",
            "management_company": "Independent", 
            "annualrevenue": 400000,
            "state": "Other",
            "numberofemployees": 12,
            "website": "https://citygolf.gov",
            "description": "Basic municipal course",
            "club_info": "18-hole municipal course"
        }
        
        state.company_data = cold_prospect_data
        result = self.agent.score_and_store(state)
        scores = result["scores"]
        
        # Should be lower fit score
        assert scores["fit_score"] <= 55
        assert scores["score_band"] in ["Cold (40-59)", "Unqualified (0-39)"]
    
    def test_scoring_version_tracking(self):
        """Test that scoring version is properly tracked."""
        state = CRMSessionState()
        state.company_data = self.test_company_data
        state.contact_data = self.test_contact_data
        
        result = self.agent.score_and_store(state)
        scores = result["scores"]
        
        # Verify version is tracked
        assert "scoring_version" in scores
        assert scores["scoring_version"] == "1.0.0"
        
        # Verify timestamp is recorded
        assert "score_updated_at" in scores
        assert scores["score_updated_at"] is not None
    
    def test_missing_data_handling(self):
        """Test that agent handles missing data gracefully."""
        # Test with minimal data
        minimal_company_data = {
            "name": "Unknown Golf Course"
        }
        
        minimal_contact_data = {
            "email": "contact@unknown.com"
        }
        
        state = CRMSessionState()
        state.company_data = minimal_company_data
        state.contact_data = minimal_contact_data
        
        # Should not raise exceptions
        result = self.agent.score_and_store(state)
        
        assert "scores" in result
        assert "hubspot_updates" in result
        
        # Should still produce valid scores (likely low)
        scores = result["scores"]
        assert 0 <= scores["fit_score"] <= 100
        assert 0 <= scores["intent_score"] <= 100
        assert 0 <= scores["total_score"] <= 100
        assert scores["score_band"] in ["Hot (80-100)", "Warm (60-79)", "Cold (40-59)", "Unqualified (0-39)"]
    
    def test_score_rationale_completeness(self):
        """Test that scoring rationale includes all expected factors."""
        state = CRMSessionState()
        state.company_data = self.test_company_data
        state.contact_data = self.test_contact_data
        
        result = self.agent.score_and_store(state)
        scores = result["scores"]
        
        # Verify fit rationale includes all factors
        fit_rationale = scores["fit_rationale"]
        expected_fit_factors = [
            "course_type", "management_company", "revenue_range", 
            "location", "employee_count", "technology_stack", "amenities"
        ]
        
        for factor in expected_fit_factors:
            assert factor in fit_rationale, f"Missing fit factor: {factor}"
            assert "value" in fit_rationale[factor]
            assert "score" in fit_rationale[factor]
            assert "weight" in fit_rationale[factor]
            assert "contribution" in fit_rationale[factor]
        
        # Verify intent rationale includes expected factors
        intent_rationale = scores["intent_rationale"]
        expected_intent_factors = [
            "website_activity", "email_engagement", "content_downloads", "meeting_requests"
        ]
        
        for factor in expected_intent_factors:
            assert factor in intent_rationale, f"Missing intent factor: {factor}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])