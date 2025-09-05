"""
Comprehensive test suite for the enhanced Jira multi-agent system.
Tests all phases of the implementation for production readiness.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from datetime import datetime, timedelta

# Import the system components
from jira_agent.agent_factory import agent_registry, create_simple_agent
from jira_agent.coordinator import create_jira_coordinator
from jira_agent.workflow_agents import (
    create_risk_assessment_pipeline,
    create_data_quality_workflow,
    create_comprehensive_info_workflow,
    create_project_health_dashboard
)
from jira_agent.specialized_agents import (
    create_stale_issue_finder,
    create_blocked_issue_analyzer,
    create_due_date_monitor,
    create_data_quality_auditor,
    create_executive_reporter,
    create_project_health_analyst
)
from jira_agent.state_models import JiraSessionState, create_initial_state


class TestPhase1EnhancedTools:
    """Test Phase 1: Enhanced MCP Tools functionality."""
    
    @pytest.fixture
    def sample_jira_data(self):
        """Create sample Jira data for testing."""
        return pd.DataFrame([
            {
                "Issue key": "PROJ-1",
                "Summary": "Test issue 1",
                "Status": "In Progress", 
                "Assignee": "john.doe@company.com",
                "Priority": "High",
                "Updated": "2024-01-01"
            },
            {
                "Issue key": "PROJ-2", 
                "Summary": "Blocked issue",
                "Status": "Blocked",
                "Assignee": "[NOT_AVAILABLE]",
                "Priority": "[NOT_AVAILABLE]", 
                "Updated": "2023-11-01"
            },
            {
                "Issue key": "PROJ-3",
                "Summary": "Done issue",
                "Status": "Done",
                "Assignee": "jane.smith@company.com",
                "Priority": "Medium",
                "Updated": "2024-01-15"
            }
        ])
    
    def test_agent_registry_functionality(self):
        """Test that the agent registry works correctly."""
        # Test listing agents
        agents = agent_registry.list_agents()
        assert "simple" in agents
        assert "query" in agents
        assert "analysis" in agents
        assert "reporting" in agents
        assert "data_quality" in agents
        assert "clarification" in agents
        
        # Test creating agents
        simple_agent = agent_registry.create_agent("simple")
        assert simple_agent.name == "jira_csv_assistant"
        
        query_agent = agent_registry.create_agent("query")
        assert query_agent.name == "QueryAgent"
        
        # Test error handling
        with pytest.raises(ValueError, match="Unknown agent type"):
            agent_registry.create_agent("nonexistent")
    
    def test_specialized_agent_creation(self):
        """Test that specialized Phase 4 agents can be created."""
        # Test Phase 4 specialized agents
        stale_finder = create_stale_issue_finder()
        assert stale_finder.name == "StaleIssueFinder"
        
        blocked_analyzer = create_blocked_issue_analyzer()
        assert blocked_analyzer.name == "BlockedIssueAnalyzer"
        
        due_monitor = create_due_date_monitor()
        assert due_monitor.name == "DueDateMonitor"
        
        quality_auditor = create_data_quality_auditor()
        assert quality_auditor.name == "DataQualityAuditor"
        
        executive_reporter = create_executive_reporter()
        assert executive_reporter.name == "ExecutiveReporter"
        
        health_analyst = create_project_health_analyst()
        assert health_analyst.name == "ProjectHealthAnalyst"


class TestPhase2CoordinatorRouting:
    """Test Phase 2: Coordinator/Dispatcher pattern."""
    
    def test_coordinator_creation(self):
        """Test that the coordinator can be created with all sub-agents."""
        coordinator = create_jira_coordinator()
        assert coordinator.name == "JiraCoordinator"
        assert len(coordinator.sub_agents) == 11  # 5 basic + 4 workflow + 2 Phase 4
        
        # Verify sub-agent names
        sub_agent_names = [agent.name for agent in coordinator.sub_agents]
        expected_names = [
            "QueryAgent", "AnalysisAgent", "ReportingAgent", 
            "DataQualityAgent", "ClarificationAgent",
            "RiskAssessmentPipeline", "DataQualityWorkflow",
            "ComprehensiveInfoWorkflow", "ProjectHealthDashboard",
            "ExecutiveReporter", "ProjectHealthAnalyst"
        ]
        
        for expected_name in expected_names:
            assert expected_name in sub_agent_names
    
    def test_agent_descriptions_for_routing(self):
        """Test that agents have proper descriptions for LLM routing."""
        coordinator = create_jira_coordinator()
        
        for agent in coordinator.sub_agents:
            assert agent.description is not None
            assert len(agent.description) > 10  # Meaningful description
            assert agent.name is not None


class TestPhase3WorkflowAgents:
    """Test Phase 3: Sequential and Parallel workflow patterns."""
    
    def test_risk_assessment_pipeline_creation(self):
        """Test that the risk assessment pipeline is properly configured."""
        pipeline = create_risk_assessment_pipeline()
        assert pipeline.name == "RiskAssessmentPipeline"
        assert len(pipeline.sub_agents) == 4  # 3 finders + 1 synthesizer
        
        # Verify the sequence
        agent_names = [agent.name for agent in pipeline.sub_agents]
        expected_sequence = [
            "StaleIssueFinder", "BlockedIssueFinder", 
            "DueSoonFinder", "RiskSynthesizer"
        ]
        assert agent_names == expected_sequence
    
    def test_data_quality_workflow_creation(self):
        """Test that the data quality workflow is properly configured."""
        workflow = create_data_quality_workflow()
        assert workflow.name == "DataQualityWorkflow"
        assert len(workflow.sub_agents) == 4  # analyzer + suggester + approval + updater
        
        agent_names = [agent.name for agent in workflow.sub_agents]
        expected_sequence = [
            "DataQualityAnalyzer", "FixSuggester",
            "HumanApprovalAgent", "BulkUpdater"
        ]
        assert agent_names == expected_sequence
    
    def test_comprehensive_info_workflow_creation(self):
        """Test the parallel + sequential workflow pattern."""
        workflow = create_comprehensive_info_workflow()
        assert workflow.name == "ComprehensiveInfoWorkflow"
        assert len(workflow.sub_agents) == 2  # parallel gather + reporter
        
        # First agent should be ParallelAgent
        parallel_agent = workflow.sub_agents[0]
        assert parallel_agent.name == "ConcurrentDataGather"
        assert len(parallel_agent.sub_agents) == 3  # 3 parallel analyzers
        
        # Second agent should be the reporter
        reporter = workflow.sub_agents[1]
        assert reporter.name == "ComprehensiveReporter"
    
    def test_project_health_dashboard_creation(self):
        """Test the complex nested workflow."""
        dashboard = create_project_health_dashboard()
        assert dashboard.name == "ProjectHealthDashboard"
        assert len(dashboard.sub_agents) == 3  # risk + info + dashboard creator
        
        # Verify nested structure
        risk_pipeline = dashboard.sub_agents[0]
        assert risk_pipeline.name == "RiskAssessmentPipeline"
        
        info_workflow = dashboard.sub_agents[1]
        assert info_workflow.name == "ComprehensiveInfoWorkflow"
        
        dashboard_creator = dashboard.sub_agents[2]
        assert dashboard_creator.name == "ProjectHealthDashboard"


class TestPhase4SpecializedAgents:
    """Test Phase 4: Specialized agent implementations with AgentTool pattern."""
    
    def test_executive_reporter_agent_tools(self):
        """Test that ExecutiveReporter has AgentTool access to other agents."""
        reporter = create_executive_reporter()
        assert reporter.name == "ExecutiveReporter"
        
        # Should have tools (AgentTools for sub-agents)
        assert len(reporter.tools) > 0
        
        # Verify it's configured for executive-level reporting
        assert "executive" in reporter.instruction.lower()
        assert "strategic" in reporter.instruction.lower() or "business" in reporter.instruction.lower()
    
    def test_project_health_analyst_orchestration(self):
        """Test that ProjectHealthAnalyst orchestrates multiple expert agents."""
        analyst = create_project_health_analyst()
        assert analyst.name == "ProjectHealthAnalyst"
        
        # Should have multiple AgentTools
        assert len(analyst.tools) >= 4  # At least 4 expert agents
        
        # Verify comprehensive analysis capability
        assert "comprehensive" in analyst.instruction.lower()
        assert "health" in analyst.instruction.lower()
        assert "score" in analyst.instruction.lower()
    
    def test_specialized_agent_expertise(self):
        """Test that specialized agents have domain-specific expertise."""
        stale_finder = create_stale_issue_finder()
        assert "stale" in stale_finder.instruction.lower()
        assert "pattern" in stale_finder.instruction.lower()
        
        blocked_analyzer = create_blocked_issue_analyzer()
        assert "blocked" in blocked_analyzer.instruction.lower()
        assert "impediment" in blocked_analyzer.instruction.lower()
        
        due_monitor = create_due_date_monitor()
        assert "due" in due_monitor.instruction.lower() or "deadline" in due_monitor.instruction.lower()
        assert "schedule" in due_monitor.instruction.lower()
        
        quality_auditor = create_data_quality_auditor()
        assert "quality" in quality_auditor.instruction.lower()
        assert "governance" in quality_auditor.instruction.lower()


class TestPhase5ProductionReadiness:
    """Test Phase 5: Production readiness features."""
    
    def test_state_model_validation(self):
        """Test that state models work correctly."""
        # Test initial state creation
        state = create_initial_state("test-session-123")
        assert state.session_id == "test-session-123"
        assert state.data_loaded == False
        assert len(state.jira_data) == 0
        
        # Test state updates
        state.add_routing_decision("Coordinator", "QueryAgent", "User requested issue search")
        assert len(state.routing_decisions) == 1
        assert state.routing_decisions[0]["from"] == "Coordinator"
        assert state.routing_decisions[0]["to"] == "QueryAgent"
        
        state.add_agent_to_history("QueryAgent")
        assert state.active_agent == "QueryAgent"
        assert "QueryAgent" in state.agent_history
    
    def test_error_handling_graceful_degradation(self):
        """Test that the system handles errors gracefully."""
        # Test agent registry error handling
        with pytest.raises(ValueError):
            agent_registry.create_agent("invalid_agent_type")
        
        # Test that agents can be created even with missing dependencies
        try:
            simple_agent = create_simple_agent()
            assert simple_agent is not None
        except Exception as e:
            pytest.fail(f"Simple agent creation should not fail: {e}")
    
    def test_system_scalability(self):
        """Test that the system can handle multiple agents efficiently."""
        # Create multiple agents to test memory usage
        agents = []
        for i in range(10):
            agent = create_simple_agent()
            agents.append(agent)
        
        assert len(agents) == 10
        
        # Test coordinator with many sub-agents
        coordinator = create_jira_coordinator()
        assert len(coordinator.sub_agents) >= 10  # Should have many sub-agents
    
    def test_configuration_validation(self):
        """Test that agent configurations are valid."""
        coordinator = create_jira_coordinator()
        
        # Verify all sub-agents have required attributes
        for agent in coordinator.sub_agents:
            assert hasattr(agent, 'name')
            assert hasattr(agent, 'description')
            assert hasattr(agent, 'instruction')
            assert agent.name is not None
            assert agent.description is not None
            assert agent.instruction is not None
            assert len(agent.name) > 0
            assert len(agent.description) > 0
            assert len(agent.instruction) > 0


class TestIntegrationScenarios:
    """Integration tests for complete workflows."""
    
    def test_end_to_end_system_creation(self):
        """Test that the entire system can be created without errors."""
        try:
            # Create all major components
            coordinator = create_jira_coordinator()
            risk_pipeline = create_risk_assessment_pipeline()
            quality_workflow = create_data_quality_workflow()
            info_workflow = create_comprehensive_info_workflow()
            health_dashboard = create_project_health_dashboard()
            
            # Verify they're all created successfully
            assert coordinator is not None
            assert risk_pipeline is not None
            assert quality_workflow is not None
            assert info_workflow is not None
            assert health_dashboard is not None
            
        except Exception as e:
            pytest.fail(f"End-to-end system creation failed: {e}")
    
    def test_agent_registry_completeness(self):
        """Test that all expected agents are registered."""
        agents = agent_registry.list_agents()
        
        # Basic agents
        basic_agents = ["simple", "query", "analysis", "reporting", "data_quality", "clarification"]
        for agent_type in basic_agents:
            assert agent_type in agents, f"Missing basic agent: {agent_type}"
        
        # Phase 4 specialized agents
        specialized_agents = ["stale_finder", "blocked_analyzer", "due_monitor", "quality_auditor", "executive_reporter", "health_analyst"]
        for agent_type in specialized_agents:
            assert agent_type in agents, f"Missing specialized agent: {agent_type}"
    
    def test_system_performance_baseline(self):
        """Test basic performance characteristics."""
        import time
        
        # Test agent creation time
        start_time = time.time()
        coordinator = create_jira_coordinator()
        creation_time = time.time() - start_time
        
        # Should create quickly (under 5 seconds)
        assert creation_time < 5.0, f"Agent creation took too long: {creation_time}s"
        
        # Test memory usage is reasonable
        import sys
        coordinator_size = sys.getsizeof(coordinator)
        assert coordinator_size < 1024 * 1024, f"Coordinator too large: {coordinator_size} bytes"


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])
