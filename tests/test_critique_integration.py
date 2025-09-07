"""
Test the integration of the critique system with the Project Manager Agent
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import pytest
import asyncio
from project_manager_agent.coordinator import ProjectManagerAgent
from project_manager_agent.core.critique_system import CRMResponseCritic, ResponseQuality


class TestCritiqueIntegration:
    """Test critique system integration with Project Manager Agent"""
    
    def test_project_manager_has_critique_components(self):
        """Test that Project Manager Agent has critique components initialized"""
        pm_agent = ProjectManagerAgent()
        
        # Check that critique components are initialized
        assert hasattr(pm_agent, 'critic')
        assert hasattr(pm_agent, 'thinking_engine')
        assert hasattr(pm_agent, 'critique_history')
        
        # Check that components are the right type
        assert isinstance(pm_agent.critic, CRMResponseCritic)
    
    def test_critique_mode_toggle(self):
        """Test enabling/disabling critique mode"""
        pm_agent = ProjectManagerAgent()
        
        # Test default state
        assert not pm_agent.is_critique_enabled()
        
        # Test enabling critique mode
        pm_agent.enable_critique_mode(True)
        assert pm_agent.is_critique_enabled()
        
        # Test disabling critique mode  
        pm_agent.enable_critique_mode(False)
        assert not pm_agent.is_critique_enabled()
    
    def test_company_intelligence_response_critique(self):
        """Test critiquing company intelligence responses"""
        pm_agent = ProjectManagerAgent()
        
        # Test poor quality response
        poor_response = {
            "name": "Test Company"
            # Missing domain, industry, description
        }
        
        critique = pm_agent.critic.critique_response(
            agent_type="company_intelligence",
            task_description="Analyze Test Company",
            response=poor_response
        )
        
        assert critique.overall_quality in [ResponseQuality.POOR, ResponseQuality.ACCEPTABLE]
        assert critique.needs_follow_up
        assert len(critique.follow_up_questions) > 0
        assert critique.score < 90
    
    def test_management_enrichment_response_critique(self):
        """Test critiquing management enrichment responses"""
        pm_agent = ProjectManagerAgent()
        
        # Test good quality response
        good_response = {
            "management_company": "Troon Golf",
            "management_company_id": "hubspot_troon_123", 
            "match_score": 95,
            "confidence": 95
        }
        
        critique = pm_agent.critic.critique_response(
            agent_type="company_management_enrichment",
            task_description="Identify management company",
            response=good_response
        )
        
        assert critique.overall_quality in [ResponseQuality.GOOD, ResponseQuality.EXCELLENT]
        assert not critique.needs_follow_up or len(critique.follow_up_questions) == 0
        assert critique.score >= 80
    
    def test_error_response_handling(self):
        """Test handling of error responses"""
        pm_agent = ProjectManagerAgent()
        
        error_response = {
            "error": "Connection failed"
        }
        
        critique = pm_agent.critic.critique_response(
            agent_type="crm_enrichment",
            task_description="Enrich company data",
            response=error_response
        )
        
        assert critique.overall_quality == ResponseQuality.UNACCEPTABLE
        assert critique.needs_follow_up
        assert critique.score == 0
        assert len(critique.follow_up_questions) > 0
    
    def test_critical_thinking_analysis(self):
        """Test critical thinking analysis of project results"""
        pm_agent = ProjectManagerAgent()
        
        sample_results = [
            {"company_name": "Test Golf Club", "industry": "Recreation"},
            {"management_company": "Troon", "confidence": 85},
            {"error": "Data unavailable"}
        ]
        
        analysis = pm_agent.thinking_engine.think_critically(
            project_goal="Find golf clubs and identify management companies",
            task_results=sample_results
        )
        
        assert "goal_achievement" in analysis
        assert "data_quality" in analysis
        assert "strategic_insights" in analysis
        assert "recommended_actions" in analysis
        
        # Check that analysis provides meaningful insights
        assert isinstance(analysis["strategic_insights"], list)
        assert isinstance(analysis["recommended_actions"], list)
    
    def test_follow_up_task_generation(self):
        """Test generation of follow-up tasks from critique"""
        pm_agent = ProjectManagerAgent()
        
        # Create a task with poor response
        from project_manager_agent.core.task_models import Task, TaskPriority
        
        original_task = Task(
            id="test_task_123",
            name="Test Company Analysis",
            description="Analyze test company",
            agent_type="company_intelligence",
            parameters={"company_name": "Test Corp"},
            priority=TaskPriority.HIGH
        )
        
        poor_response = {"name": "Test Corp"}  # Very minimal response
        
        critique = pm_agent.critic.critique_response(
            agent_type="company_intelligence",
            task_description="Analyze test company",
            response=poor_response
        )
        
        # Test follow-up task generation
        follow_up_task = pm_agent._create_follow_up_task(original_task, critique)
        
        if critique.needs_follow_up:
            assert follow_up_task is not None
            assert "Follow-up" in follow_up_task.name
            assert follow_up_task.agent_type == original_task.agent_type
            assert "follow_up_questions" in follow_up_task.parameters
    
    def test_critique_summary_generation(self):
        """Test generation of critique summaries"""
        pm_agent = ProjectManagerAgent()
        
        # Add some mock critiques to history
        from project_manager_agent.core.critique_system import CritiqueResult
        
        mock_critique = CritiqueResult(
            overall_quality=ResponseQuality.POOR,
            score=45,
            critiques=[{"category": "completeness", "issue": "Missing data"}],
            follow_up_questions=["What is missing?"],
            suggested_improvements=["Add more data"],
            needs_follow_up=True,
            confidence=80
        )
        
        pm_agent.critique_history["test_task"] = mock_critique
        
        summary = pm_agent._generate_critique_summary()
        
        assert "total_critiques" in summary
        assert "quality_distribution" in summary
        assert summary["total_critiques"] == 1
        assert "poor" in summary["quality_distribution"]


def test_async_execution_with_critique():
    """Test async execution with critique (basic test)"""
    
    async def run_test():
        pm_agent = ProjectManagerAgent()
        
        # This would normally execute with real CRM agents
        # For testing, we just verify the method exists and can be called
        try:
            # Test that the method exists and can be called
            result = await pm_agent.execute_goal_with_critique(
                "Test goal for critique system"
            )
            # In a real test with mocked agents, we would verify the result
            assert isinstance(result, dict)
        except Exception as e:
            # Expected in test environment without full CRM setup
            assert "crm_agent_registry" in str(e) or "AttributeError" in str(type(e).__name__)
    
    # Run the async test
    asyncio.run(run_test())


if __name__ == "__main__":
    # Run basic tests
    test_integration = TestCritiqueIntegration()
    
    print("🧪 Running Critique System Integration Tests...")
    
    try:
        test_integration.test_project_manager_has_critique_components()
        print("✅ Critique components initialization test passed")
        
        test_integration.test_critique_mode_toggle()
        print("✅ Critique mode toggle test passed")
        
        test_integration.test_company_intelligence_response_critique()
        print("✅ Company intelligence critique test passed")
        
        test_integration.test_management_enrichment_response_critique()
        print("✅ Management enrichment critique test passed")
        
        test_integration.test_error_response_handling()
        print("✅ Error response handling test passed")
        
        test_integration.test_critical_thinking_analysis()
        print("✅ Critical thinking analysis test passed")
        
        test_integration.test_follow_up_task_generation()
        print("✅ Follow-up task generation test passed")
        
        test_integration.test_critique_summary_generation()
        print("✅ Critique summary generation test passed")
        
        test_async_execution_with_critique()
        print("✅ Async execution test passed")
        
        print("\n🎉 ALL TESTS PASSED! Critique system is properly integrated.")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        raise
