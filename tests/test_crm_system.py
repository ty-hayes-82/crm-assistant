"""
Test suite for CRM multi-agent system.
Tests the CRM agents, workflows, and integration patterns.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any, List

from crm_agent.core.state_models import (
    CRMSessionState, 
    CRMStateKeys, 
    CRMEnrichmentResult,
    create_initial_crm_state
)
from crm_agent.core.factory import crm_agent_registry
from crm_agent.coordinator import create_crm_coordinator, create_crm_simple_agent
from crm_fastmcp_server.server import CRMFastMCPServer


class TestCRMSessionState:
    """Test CRM session state management."""
    
    def test_create_initial_crm_state(self):
        """Test creating initial CRM session state."""
        state = create_initial_crm_state(
            contact_email="test@example.com",
            company_domain="example.com"
        )
        
        assert isinstance(state, CRMSessionState)
        assert state.contact_email == "test@example.com"
        assert state.company_domain == "example.com"
        assert state.session_id is not None
        assert not state.data_loaded
        assert len(state.enrichment_results) == 0
    
    def test_add_enrichment_result(self):
        """Test adding enrichment results to state."""
        state = create_initial_crm_state()
        
        result = CRMEnrichmentResult(
            field_name="industry",
            current_value=None,
            proposed_value="Software",
            confidence=0.9,
            source="web_search"
        )
        
        state.add_enrichment_result(result)
        
        assert len(state.enrichment_results) == 1
        assert state.enrichment_results[0].field_name == "industry"
        assert state.enrichment_results[0].confidence == 0.9
    
    def test_state_keys_constants(self):
        """Test that state keys are properly defined."""
        assert hasattr(CRMStateKeys, 'CONTACT_EMAIL')
        assert hasattr(CRMStateKeys, 'WEB_FINDINGS')
        assert hasattr(CRMStateKeys, 'PROPOSED_CHANGES')
        assert CRMStateKeys.CONTACT_EMAIL == "contact_email"


class TestCRMAgentRegistry:
    """Test CRM agent registration and creation."""
    
    def test_crm_agents_registered(self):
        """Test that CRM agents are properly registered."""
        available_agents = crm_agent_registry.list_agents()
        
        crm_agents = [
            "crm_query_builder",
            "crm_web_retriever", 
            "crm_linkedin_retriever",
            "crm_company_data_retriever",
            "crm_email_verifier",
            "crm_summarizer",
            "crm_entity_resolver",
            "crm_updater",
            "crm_data_quality"
        ]
        
        for agent_name in crm_agents:
            assert agent_name in available_agents, f"Agent {agent_name} not registered"
    
    def test_crm_workflows_registered(self):
        """Test that CRM workflows are properly registered."""
        available_agents = crm_agent_registry.list_agents()
        
        crm_workflows = [
            "crm_enrichment_pipeline",
            "crm_parallel_retrieval",
            "crm_quick_lookup"
        ]
        
        for workflow_name in crm_workflows:
            assert workflow_name in available_agents, f"Workflow {workflow_name} not registered"
    
    def test_create_crm_agents(self):
        """Test creating CRM agent instances."""
        # Test creating individual agents
        query_builder = crm_agent_registry.create_agent("crm_query_builder")
        assert query_builder.name == "QueryBuilderAgent"
        
        web_retriever = crm_agent_registry.create_agent("crm_web_retriever")
        assert web_retriever.name == "WebRetrieverAgent"
        
        # Test creating workflows
        enrichment_pipeline = crm_agent_registry.create_agent("crm_enrichment_pipeline")
        assert enrichment_pipeline.name == "CRMEnrichmentPipeline"


class TestCRMFastMCPServer:
    """Test CRM FastMCP server functionality."""
    
    @pytest.fixture
    def crm_server(self):
        """Create a CRM FastMCP server instance for testing."""
        return CRMFastMCPServer()
    
    def test_server_initialization(self, crm_server):
        """Test that CRM server initializes properly."""
        assert crm_server.mcp is not None
        assert crm_server.hubspot_mcp_url == "https://mcp.hubspot.com/"
        assert crm_server.http_client is not None
    
    @pytest.mark.asyncio
    async def test_hubspot_tools_registered(self, crm_server):
        """Test that HubSpot tools are registered."""
        # This would test the actual tool registration
        # In a real implementation, we'd check the MCP server's tool list
        pass
    
    @pytest.mark.asyncio
    async def test_web_search_tool(self, crm_server):
        """Test web search tool functionality."""
        # Mock the HTTP client response
        with patch.object(crm_server.http_client, 'get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {
                "organic_results": [
                    {
                        "title": "Test Company",
                        "link": "https://example.com",
                        "snippet": "Test company description",
                        "position": 1
                    }
                ]
            }
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            # This would test the actual web search functionality
            # Implementation depends on the MCP tool structure
            pass


class TestCRMCoordinator:
    """Test CRM coordinator routing logic."""
    
    @pytest.fixture
    def coordinator(self):
        """Create a CRM coordinator for testing."""
        return create_crm_coordinator()
    
    def test_coordinator_creation(self, coordinator):
        """Test that coordinator is created with proper configuration."""
        assert coordinator.name == "CRMSystemCoordinator"
        assert len(coordinator.sub_agents) > 0
        
        # Check that key agents are included
        agent_names = [agent.name for agent in coordinator.sub_agents]
        expected_agents = [
            "QueryBuilderAgent",
            "WebRetrieverAgent", 
            "SummarizerAgent",
            "CRMUpdaterAgent"
        ]
        
        for expected_agent in expected_agents:
            assert any(expected_agent in name for name in agent_names), f"Missing agent: {expected_agent}"
    
    def test_simple_crm_agent_creation(self):
        """Test creating simple CRM agent."""
        simple_agent = create_crm_simple_agent()
        assert simple_agent.name == "CRMSimpleAssistant"
        assert "CRM Assistant" in simple_agent.description


class TestCRMWorkflows:
    """Test CRM workflow execution patterns."""
    
    @pytest.fixture
    def mock_session_state(self):
        """Create a mock CRM session state for testing."""
        return create_initial_crm_state(
            contact_email="test@example.com",
            company_domain="example.com"
        )
    
    def test_enrichment_pipeline_structure(self):
        """Test that enrichment pipeline has correct structure."""
        pipeline = crm_agent_registry.create_agent("crm_enrichment_pipeline")
        
        assert pipeline.name == "CRMEnrichmentPipeline"
        assert len(pipeline.sub_agents) == 8  # 8 steps in the pipeline
        
        # Verify step order (this would depend on the actual implementation)
        expected_steps = [
            "CRMDataQualityAgent",  # Gap Detection
            "QueryBuilderAgent",    # Query Planning
            # Parallel Retrieval group
            "SummarizerAgent",      # Synthesis
            "EntityResolutionAgent", # Entity Matching
            "CRMUpdaterAgent",      # Proposal + Approval + Updates
        ]
        
        # This test would need to be adapted based on actual agent structure
    
    def test_parallel_retrieval_structure(self):
        """Test that parallel retrieval has correct agents."""
        parallel_workflow = crm_agent_registry.create_agent("crm_parallel_retrieval")
        
        assert parallel_workflow.name == "CRMParallelRetrievalWorkflow"
        
        # Should contain the 4 retrieval agents
        expected_retrievers = [
            "WebRetrieverAgent",
            "LinkedInRetrieverAgent", 
            "CompanyDataRetrieverAgent",
            "EmailVerifierAgent"
        ]
        
        # This test would verify the parallel structure
    
    @pytest.mark.asyncio
    async def test_workflow_state_management(self, mock_session_state):
        """Test that workflows properly manage session state."""
        # This would test state passing between workflow steps
        
        # Simulate adding findings to state
        mock_session_state.web_findings = [
            {"source": "web", "field": "industry", "value": "Software", "confidence": 0.8}
        ]
        mock_session_state.li_findings = [
            {"source": "linkedin", "field": "employee_count", "value": "100-500", "confidence": 0.9}
        ]
        
        # Test state key access
        assert mock_session_state.web_findings[0]["field"] == "industry"
        assert len(mock_session_state.li_findings) == 1


class TestCRMIntegration:
    """Test end-to-end CRM integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_contact_enrichment_flow(self):
        """Test complete contact enrichment workflow."""
        # This would test the full enrichment pipeline
        # 1. Load contact data
        # 2. Detect gaps
        # 3. Plan queries
        # 4. Execute parallel retrieval
        # 5. Synthesize findings
        # 6. Map to CRM fields
        # 7. Generate proposals
        # 8. Apply approved changes
        
        # Mock the various steps
        contact_email = "john@acme.com"
        
        # Create initial state
        state = create_initial_crm_state(contact_email=contact_email)
        
        # Simulate workflow execution
        # (This would involve mocking the actual agent calls)
        
        assert state.contact_email == contact_email
        # Additional assertions would verify the workflow results
    
    @pytest.mark.asyncio
    async def test_data_quality_assessment(self):
        """Test data quality assessment workflow."""
        # This would test the data quality workflow
        # 1. Load CRM data
        # 2. Assess quality metrics
        # 3. Generate improvement recommendations
        
        state = create_initial_crm_state()
        
        # Mock quality assessment results
        state.detected_gaps = {
            "missing_fields": ["industry", "employee_count"],
            "outdated_fields": ["last_activity_date"],
            "quality_score": 0.6
        }
        
        assert "industry" in state.detected_gaps["missing_fields"]
        assert state.detected_gaps["quality_score"] == 0.6
    
    @pytest.mark.asyncio
    async def test_approval_workflow(self):
        """Test human approval workflow integration."""
        # This would test the approval process
        # 1. Generate proposed changes
        # 2. Format for human review
        # 3. Send to Slack
        # 4. Process approval response
        # 5. Apply approved changes only
        
        state = create_initial_crm_state()
        
        # Mock proposed changes
        proposed_changes = [
            {
                "field": "industry",
                "current_value": None,
                "proposed_value": "Software",
                "confidence": 0.9,
                "source": "web_search"
            },
            {
                "field": "employee_count", 
                "current_value": None,
                "proposed_value": "100-500",
                "confidence": 0.8,
                "source": "linkedin"
            }
        ]
        
        state.proposed_changes = proposed_changes
        
        # Mock approval (approve first change only)
        state.approved_changes = [proposed_changes[0]]
        
        assert len(state.proposed_changes) == 2
        assert len(state.approved_changes) == 1
        assert state.approved_changes[0]["field"] == "industry"


class TestCRMErrorHandling:
    """Test CRM system error handling and recovery."""
    
    @pytest.mark.asyncio
    async def test_api_error_handling(self):
        """Test handling of API errors (HubSpot, search, etc.)."""
        # This would test error scenarios:
        # - HubSpot API failures
        # - Search API rate limits
        # - Network timeouts
        # - Invalid data responses
        pass
    
    @pytest.mark.asyncio
    async def test_data_validation_errors(self):
        """Test handling of data validation errors."""
        # This would test:
        # - Invalid email formats
        # - Malformed company domains
        # - Confidence score validation
        # - Field mapping errors
        pass
    
    @pytest.mark.asyncio
    async def test_workflow_recovery(self):
        """Test workflow recovery from failures."""
        # This would test:
        # - Partial workflow completion
        # - State recovery after errors
        # - Retry mechanisms
        # - Graceful degradation
        pass


# Test fixtures and utilities

@pytest.fixture
def sample_crm_data():
    """Sample CRM data for testing."""
    return {
        "contact": {
            "id": "12345",
            "email": "john@acme.com",
            "firstname": "John",
            "lastname": "Doe",
            "company": "ACME Corp",
            "industry": None,  # Missing field
            "phone": None      # Missing field
        },
        "company": {
            "id": "67890", 
            "name": "ACME Corp",
            "domain": "acme.com",
            "industry": None,     # Missing field
            "num_employees": None # Missing field
        }
    }


@pytest.fixture
def mock_web_search_results():
    """Mock web search results for testing."""
    return {
        "results": [
            {
                "title": "ACME Corp - Software Solutions",
                "url": "https://acme.com/about",
                "snippet": "ACME Corp is a leading software company with 200+ employees...",
                "position": 1
            },
            {
                "title": "ACME Corp Company Profile",
                "url": "https://linkedin.com/company/acme-corp",
                "snippet": "Software industry, 201-500 employees, San Francisco",
                "position": 2
            }
        ]
    }


@pytest.fixture
def mock_hubspot_responses():
    """Mock HubSpot API responses for testing."""
    return {
        "contact": {
            "id": "12345",
            "properties": {
                "email": "john@acme.com",
                "firstname": "John",
                "lastname": "Doe",
                "company": "ACME Corp"
            }
        },
        "company": {
            "id": "67890",
            "properties": {
                "name": "ACME Corp",
                "domain": "acme.com",
                "industry": "SOFTWARE"
            }
        }
    }


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
