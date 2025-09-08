#!/usr/bin/env python3
"""
Unit tests for Outreach Personalizer Agent (Phase 7).
Tests personalized outreach generation and HubSpot engagement creation.
"""

import pytest
from datetime import datetime, timedelta
from crm_agent.agents.specialized.outreach_personalizer_agent import create_outreach_personalizer_agent
from crm_agent.core.state_models import CRMSessionState


class TestOutreachPersonalizerAgent:
    """Test suite for Outreach Personalizer Agent functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.agent = create_outreach_personalizer_agent()
        
        # Test company data - High-end private club
        self.test_company_data = {
            "name": "Prestigious Country Club",
            "company_type": "Private",
            "management_company": "Troon",
            "annualrevenue": 18000000,  # 18M
            "state": "California",
            "numberofemployees": 120,
            "website": "https://prestigiouscc.com",
            "description": "Exclusive private club with championship golf course, fine dining, and event facilities",
            "club_info": "Championship 18-hole course with clubhouse dining, event spaces, and full-service amenities"
        }
        
        # Test contact data - General Manager
        self.test_contact_data = {
            "id": "contact_12345",
            "email": "john.smith@prestigiouscc.com",
            "jobtitle": "General Manager",
            "firstname": "John",
            "lastname": "Smith"
        }
        
        # Test lead scores (from Phase 6)
        self.test_lead_scores = {
            "fit_score": 92.5,
            "intent_score": 15.0,
            "total_score": 61.5,
            "score_band": "Warm (60-79)",
            "scoring_version": "1.0.0"
        }
    
    def test_agent_initialization(self):
        """Test agent initializes correctly with config."""
        assert self.agent.name == "OutreachPersonalizerAgent"
        assert hasattr(self.agent, '_config')
        assert self.agent._config.get('version') == '1.0.0'
    
    def test_contact_role_analysis(self):
        """Test contact role analysis and classification."""
        role_analysis = self.agent._analyze_contact_role(self.test_contact_data)
        
        assert role_analysis["original_title"] == "General Manager"
        assert role_analysis["role_type"] == "general_manager"
        assert role_analysis["decision_authority"] == "high"
        assert "ROI" in role_analysis["messaging_focus"]
        assert "operational_efficiency" in role_analysis["messaging_focus"]
        assert "declining_membership" in role_analysis["pain_points"]
    
    def test_company_profile_analysis(self):
        """Test company profile analysis for personalization."""
        company_profile = self.agent._analyze_company_profile(self.test_company_data, {})
        
        assert company_profile["name"] == "Prestigious Country Club"
        assert company_profile["type"] == "Private"
        assert company_profile["management_company"] == "Troon"
        assert company_profile["sophistication_level"] == "high"
        assert company_profile["competitive_context"]["is_managed"] == True
    
    def test_role_type_classification(self):
        """Test different role type classifications."""
        # Test Operations Manager
        ops_contact = {"jobtitle": "Operations Manager"}
        role_analysis = self.agent._analyze_contact_role(ops_contact)
        assert role_analysis["role_type"] == "operations_manager"
        assert role_analysis["decision_authority"] == "medium"
        
        # Test Golf Professional
        golf_contact = {"jobtitle": "Head Golf Professional"}
        role_analysis = self.agent._analyze_contact_role(golf_contact)
        assert role_analysis["role_type"] == "golf_professional"
        assert "member_engagement" in role_analysis["messaging_focus"]
        
        # Test F&B Manager
        fb_contact = {"jobtitle": "Food & Beverage Manager"}
        role_analysis = self.agent._analyze_contact_role(fb_contact)
        assert role_analysis["role_type"] == "fb_manager"
        assert "dining_revenue" in role_analysis["messaging_focus"]
    
    def test_messaging_strategy_selection(self):
        """Test messaging strategy selection based on role and profile."""
        role_analysis = self.agent._analyze_contact_role(self.test_contact_data)
        company_profile = self.agent._analyze_company_profile(self.test_company_data, {})
        
        # Test with high-scoring lead
        hot_lead_scores = {"score_band": "Hot (80-100)"}
        strategy = self.agent._select_messaging_strategy(role_analysis, company_profile, hot_lead_scores)
        assert strategy == "direct_value_proposition"
        
        # Test with GM and high sophistication
        warm_lead_scores = {"score_band": "Warm (60-79)"}
        strategy = self.agent._select_messaging_strategy(role_analysis, company_profile, warm_lead_scores)
        assert strategy == "strategic_partnership"
    
    def test_subject_line_generation(self):
        """Test subject line generation for different strategies."""
        role_analysis = self.agent._analyze_contact_role(self.test_contact_data)
        company_profile = self.agent._analyze_company_profile(self.test_company_data, {})
        
        # Test direct value proposition
        subject = self.agent._generate_subject_line(
            role_analysis, company_profile, "direct_value_proposition", "cold_outreach"
        )
        assert "Prestigious Country Club" in subject
        assert "ROI" in subject or "opportunity" in subject
        
        # Test strategic partnership
        subject = self.agent._generate_subject_line(
            role_analysis, company_profile, "strategic_partnership", "cold_outreach"
        )
        assert "Prestigious Country Club" in subject
        assert "Partnership" in subject or "opportunity" in subject
    
    def test_email_content_generation(self):
        """Test email content generation with personalization."""
        role_analysis = self.agent._analyze_contact_role(self.test_contact_data)
        company_profile = self.agent._analyze_company_profile(self.test_company_data, {})
        
        content = self.agent._generate_email_content(
            role_analysis, company_profile, "strategic_partnership", "cold_outreach"
        )
        
        assert "Prestigious Country Club" in content
        assert len(content) > 100  # Substantial content
        assert content.strip()  # Not empty
    
    def test_call_to_action_generation(self):
        """Test call-to-action generation based on decision authority."""
        # High authority (GM)
        gm_role = {"decision_authority": "high"}
        cta = self.agent._generate_call_to_action(gm_role, "strategic_partnership", "cold_outreach")
        assert "15-minute call" in cta or "call this week" in cta
        
        # Medium authority (Operations Manager)
        ops_role = {"decision_authority": "medium"}
        cta = self.agent._generate_call_to_action(ops_role, "operational_efficiency", "cold_outreach")
        assert "case studies" in cta or "send them over" in cta
        
        # Low authority
        low_role = {"decision_authority": "low"}
        cta = self.agent._generate_call_to_action(low_role, "education_first", "cold_outreach")
        assert "right person" in cta or "someone else" in cta
    
    def test_personalization_score_calculation(self):
        """Test personalization quality score calculation."""
        # High personalization scenario
        role_analysis = {
            "role_type": "general_manager",  # Not "general"
            "decision_authority": "high"
        }
        company_profile = {
            "personalization_hooks": ["recent_expansion", "new_technology"],
            "sophistication_level": "high",
            "competitive_context": {
                "competitive_advantages": ["championship_course", "exclusive_membership"]
            }
        }
        
        score = self.agent._calculate_personalization_score(role_analysis, company_profile)
        assert score >= 90  # Should be high with all factors
        
        # Low personalization scenario
        basic_role = {"role_type": "general"}
        basic_company = {
            "personalization_hooks": [],
            "sophistication_level": "unknown",
            "competitive_context": {"competitive_advantages": []}
        }
        
        score = self.agent._calculate_personalization_score(basic_role, basic_company)
        assert score <= 60  # Should be lower with minimal factors
    
    def test_generate_personalized_outreach_integration(self):
        """Test the main generate_personalized_outreach method."""
        # Create session state with test data
        state = CRMSessionState()
        state.company_data = self.test_company_data
        state.contact_data = self.test_contact_data
        state.lead_scores = self.test_lead_scores
        
        # Execute outreach generation
        result = self.agent.generate_personalized_outreach(state, "cold_outreach")
        
        # Verify return structure
        assert "outreach_type" in result
        assert "personalization" in result
        assert "email_engagement" in result
        assert "follow_up_task" in result
        assert "role_analysis" in result
        assert "company_profile" in result
        
        # Verify personalization details
        personalization = result["personalization"]
        assert "subject_line" in personalization
        assert "email_content" in personalization
        assert "call_to_action" in personalization
        assert "personalization_score" in personalization
        assert personalization["personalization_score"] >= 50
        
        # Verify email engagement
        email_engagement = result["email_engagement"]
        assert email_engagement["status"] == "draft_created"
        assert "email_data" in email_engagement
        assert email_engagement["email_data"]["auto_send"] == False
        
        # Verify follow-up task
        follow_up_task = result["follow_up_task"]
        assert follow_up_task["status"] == "task_created"
        assert "task_data" in follow_up_task
        assert "due_date" in follow_up_task
        
        # Verify state was updated
        assert state.outreach_results == result
    
    def test_follow_up_task_timing_by_lead_score(self):
        """Test that follow-up task timing varies by lead score band."""
        state = CRMSessionState()
        state.company_data = self.test_company_data
        state.contact_data = self.test_contact_data
        
        # Test Hot lead (1 day follow-up)
        state.lead_scores = {"score_band": "Hot (80-100)"}
        result = self.agent.generate_personalized_outreach(state, "cold_outreach")
        task_data = result["follow_up_task"]["task_data"]
        due_date = datetime.fromisoformat(task_data["due_date"])
        days_diff = (due_date - datetime.utcnow()).days
        assert days_diff <= 1
        
        # Test Cold lead (7 day follow-up)
        state.lead_scores = {"score_band": "Cold (40-59)"}
        result = self.agent.generate_personalized_outreach(state, "cold_outreach")
        task_data = result["follow_up_task"]["task_data"]
        due_date = datetime.fromisoformat(task_data["due_date"])
        days_diff = (due_date - datetime.utcnow()).days
        assert days_diff >= 6
    
    def test_email_safety_measures(self):
        """Test that email safety measures are enforced."""
        state = CRMSessionState()
        state.company_data = self.test_company_data
        state.contact_data = self.test_contact_data
        state.lead_scores = self.test_lead_scores
        
        result = self.agent.generate_personalized_outreach(state, "cold_outreach")
        email_data = result["email_engagement"]["email_data"]
        
        # Verify safety measures
        assert email_data["auto_send"] == False
        assert email_data["metadata"]["auto_send"] == False
        assert "not sent" in result["email_engagement"]["message"].lower()
        
        # Verify required fields
        assert email_data["subject"]
        assert email_data["body"]
        assert email_data["to_email"]
        assert "Sources and References" in email_data["body"]
    
    def test_citation_formatting(self):
        """Test citation formatting in email content."""
        citations = [
            {
                "claim": "Golf industry growth statistics",
                "source": "Golf Industry Report 2024",
                "url": "https://example.com/report"
            },
            {
                "claim": "Member satisfaction data",
                "source": "Club Management Survey",
                "url": "https://example.com/survey"
            }
        ]
        
        formatted = self.agent._format_citations(citations)
        assert "1. Golf industry growth statistics" in formatted
        assert "2. Member satisfaction data" in formatted
        assert "https://example.com/report" in formatted
        assert "https://example.com/survey" in formatted
    
    def test_different_outreach_types(self):
        """Test different outreach types generate appropriate content."""
        state = CRMSessionState()
        state.company_data = self.test_company_data
        state.contact_data = self.test_contact_data
        state.lead_scores = self.test_lead_scores
        
        # Test cold outreach
        result_cold = self.agent.generate_personalized_outreach(state, "cold_outreach")
        assert result_cold["outreach_type"] == "cold_outreach"
        
        # Test follow-up
        result_followup = self.agent.generate_personalized_outreach(state, "follow_up")
        assert result_followup["outreach_type"] == "follow_up"
        
        # Test demo invitation
        result_demo = self.agent.generate_personalized_outreach(state, "demo_invitation")
        assert result_demo["outreach_type"] == "demo_invitation"
        
        # Verify different content for different types
        cold_content = result_cold["personalization"]["email_content"]
        demo_content = result_demo["personalization"]["email_content"]
        assert cold_content != demo_content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
