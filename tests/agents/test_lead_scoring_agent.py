#!/usr/bin/env python3
"""
Unit tests for Lead Scoring Agent (Phase 6).
Tests deterministic inputs and expected score calculations.
"""

import pytest
import json
from datetime import datetime
from crm_agent.agents.specialized.lead_scoring_agent import create_lead_scoring_agent
from crm_agent.core.state_models import CRMSessionState


class TestLeadScoringAgent:
    """Test suite for Lead Scoring Agent functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.agent = create_lead_scoring_agent()
        
        # Test company data - Private golf course with strong profile
        self.test_company_data_high_fit = {
            "name": "Exclusive Country Club",
            "company_type": "Private",
            "management_company": "Troon",
            "annualrevenue": 15000000,  # 15M
            "state": "California",
            "numberofemployees": 150,
            "website": "https://exclusivecc.com/teesheet-booking",
            "description": "Full service private club with dining, events, and pro shop",
            "club_info": "Championship golf course with dining facilities, event spaces, and full pro shop"
        }
        
        # Test company data - Municipal course with lower fit
        self.test_company_data_low_fit = {
            "name": "City Municipal Golf Course",
            "company_type": "Municipal", 
            "management_company": "Independent",
            "annualrevenue": 300000,  # 300K
            "state": "Other",
            "numberofemployees": 8,
            "website": "https://citygolf.gov",
            "description": "Basic municipal golf course",
            "club_info": "18-hole municipal course"
        }
        
        # Test contact data
        self.test_contact_data = {
            "email": "gm@exclusivecc.com",
            "jobtitle": "General Manager"
        }
    
    def test_agent_initialization(self):
        """Test agent initializes correctly with config."""
        assert self.agent.name == "LeadScoringAgent"
        assert hasattr(self.agent, '_config')
        assert self.agent._config.get('version') == '1.0.0'
    
    def test_fit_score_calculation_high_fit(self):
        """Test fit score calculation for high-fit prospect."""
        fit_score, rationale = self.agent.calculate_fit_score(
            self.test_company_data_high_fit, 
            self.test_contact_data
        )
        
        # Should score highly due to Private + Troon + High Revenue + California + Large staff
        assert fit_score >= 85, f"Expected high fit score >= 85, got {fit_score}"
        
        # Check rationale contains all scoring factors
        assert "course_type" in rationale
        assert "management_company" in rationale
        assert "revenue_range" in rationale
        assert "location" in rationale
        assert "employee_count" in rationale
        
        # Verify specific high-scoring factors
        assert rationale["course_type"]["value"] == "Private"
        assert rationale["course_type"]["score"] == 100
        assert rationale["management_company"]["value"] == "Troon"
        assert rationale["management_company"]["score"] == 100
    
    def test_fit_score_calculation_low_fit(self):
        """Test fit score calculation for low-fit prospect."""
        fit_score, rationale = self.agent.calculate_fit_score(
            self.test_company_data_low_fit,
            self.test_contact_data
        )
        
        # Should score lower due to Municipal + Independent + Low Revenue + Other state + Small staff
        assert fit_score <= 50, f"Expected low fit score <= 50, got {fit_score}"
        
        # Verify specific low-scoring factors
        assert rationale["course_type"]["value"] == "Municipal"
        assert rationale["course_type"]["score"] == 30
        assert rationale["management_company"]["value"] == "Independent"
        assert rationale["management_company"]["score"] == 60
    
    def test_intent_score_calculation(self):
        """Test intent score calculation (currently returns low scores due to no engagement data)."""
        intent_score, rationale = self.agent.calculate_intent_score(
            self.test_company_data_high_fit,
            self.test_contact_data
        )
        
        # Should be low since we have no engagement signals
        assert intent_score <= 20, f"Expected low intent score <= 20, got {intent_score}"
        
        # Check rationale contains all intent factors
        assert "website_activity" in rationale
        assert "email_engagement" in rationale
        assert "content_downloads" in rationale
        assert "meeting_requests" in rationale
    
    def test_total_score_calculation(self):
        """Test total score calculation with weighted average."""
        fit_score = 90.0
        intent_score = 20.0
        
        total_score, score_band, details = self.agent.calculate_total_score(fit_score, intent_score)
        
        # Should be weighted average: 90*0.6 + 20*0.4 = 54 + 8 = 62
        expected_total = 62.0
        assert abs(total_score - expected_total) < 0.1, f"Expected {expected_total}, got {total_score}"
        assert score_band == "Warm (60-79)"
        
        # Check calculation details
        assert details["fit_score"] == fit_score
        assert details["intent_score"] == intent_score
        assert details["fit_weight"] == 0.6
        assert details["intent_weight"] == 0.4
    
    def test_score_bands(self):
        """Test score band classification."""
        # Hot
        total_score, score_band, details = self.agent.calculate_total_score(95.0, 90.0)
        assert score_band == "Hot (80-100)"
        
        # Warm  
        total_score, score_band, details = self.agent.calculate_total_score(80.0, 50.0)
        assert score_band == "Warm (60-79)"
        
        # Cold
        total_score, score_band, details = self.agent.calculate_total_score(60.0, 30.0)
        assert score_band == "Cold (40-59)"
        
        # Unqualified
        total_score, score_band, details = self.agent.calculate_total_score(40.0, 20.0)
        assert score_band == "Unqualified (0-39)"
    
    def test_revenue_categorization(self):
        """Test revenue range categorization."""
        assert self.agent._categorize_revenue(15000000) == "10M+"
        assert self.agent._categorize_revenue(7000000) == "5M-10M"
        assert self.agent._categorize_revenue(3000000) == "2M-5M"
        assert self.agent._categorize_revenue(1500000) == "1M-2M"
        assert self.agent._categorize_revenue(750000) == "500K-1M"
        assert self.agent._categorize_revenue(300000) == "Under 500K"
        assert self.agent._categorize_revenue(None) == "Unknown"
        assert self.agent._categorize_revenue("invalid") == "Unknown"
    
    def test_employee_categorization(self):
        """Test employee count categorization."""
        assert self.agent._categorize_employees(150) == "100+"
        assert self.agent._categorize_employees(75) == "50-100"
        assert self.agent._categorize_employees(35) == "25-50"
        assert self.agent._categorize_employees(15) == "10-25"
        assert self.agent._categorize_employees(8) == "5-10"
        assert self.agent._categorize_employees(3) == "Under 5"
        assert self.agent._categorize_employees(None) == "Unknown"
        assert self.agent._categorize_employees("invalid") == "Unknown"
    
    def test_score_and_store_integration(self):
        """Test the main score_and_store method integration."""
        # Create session state with test data
        state = CRMSessionState()
        state.company_data = self.test_company_data_high_fit
        state.contact_data = self.test_contact_data
        
        # Execute scoring
        result = self.agent.score_and_store(state)
        
        # Verify return structure
        assert "scores" in result
        assert "hubspot_updates" in result
        
        scores = result["scores"]
        hubspot_updates = result["hubspot_updates"]
        
        # Verify scores were computed
        assert "fit_score" in scores
        assert "intent_score" in scores
        assert "total_score" in scores
        assert "score_band" in scores
        assert "scoring_version" in scores
        assert "score_updated_at" in scores
        
        # Verify HubSpot field mapping
        assert "swoop_fit_score" in hubspot_updates
        assert "swoop_intent_score" in hubspot_updates
        assert "swoop_total_lead_score" in hubspot_updates
        assert "swoop_score_band" in hubspot_updates
        assert "swoop_score_updated_at" in hubspot_updates
        assert "swoop_scoring_version" in hubspot_updates
        
        # Verify scores were saved to state
        assert state.lead_scores == scores
        assert state.lead_scores["fit_score"] == hubspot_updates["swoop_fit_score"]
        assert state.lead_scores["total_score"] == hubspot_updates["swoop_total_lead_score"]
    
    def test_deterministic_scoring(self):
        """Test that scoring is deterministic for same inputs."""
        state = CRMSessionState()
        state.company_data = self.test_company_data_high_fit
        state.contact_data = self.test_contact_data
        
        # Run scoring twice
        result1 = self.agent.score_and_store(state)
        result2 = self.agent.score_and_store(state)
        
        # Scores should be identical (excluding timestamps)
        assert result1["scores"]["fit_score"] == result2["scores"]["fit_score"]
        assert result1["scores"]["intent_score"] == result2["scores"]["intent_score"]
        assert result1["scores"]["total_score"] == result2["scores"]["total_score"]
        assert result1["scores"]["score_band"] == result2["scores"]["score_band"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
