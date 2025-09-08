"""
End-to-end integration test for provenance gate enforcement.
Tests that no HubSpot write operations are attempted when provenance validation fails.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from crm_agent.core.state_models import CRMEnrichmentResult, CRMSessionState
from crm_agent.agents.specialized.crm_agents import CRMUpdaterAgent
from crm_agent.agents.specialized.outreach_personalizer_agent import OutreachPersonalizerAgent


class TestProvenanceGateIntegration:
    """Test end-to-end provenance validation enforcement."""
    
    def test_crm_updater_blocks_write_with_missing_provenance(self):
        """Test that CRM updater blocks writes when enrichment results lack provenance."""
        # Create enrichment results with missing provenance
        bad_result = CRMEnrichmentResult(
            field_name="company_industry",
            current_value="Unknown",
            proposed_value="Golf Course Management",
            confidence=0.95,
            source="",  # Missing source
            source_urls=[],  # Missing source URLs
            last_verified_at=None  # Missing verification timestamp
        )
        
        # Create CRM updater agent
        with patch('crm_agent.agents.specialized.crm_agents.create_hubspot_openapi_tool'):
            with patch('crm_agent.agents.specialized.crm_agents.get_logger') as mock_logger:
                with patch('crm_agent.agents.specialized.crm_agents.get_idempotency_manager'):
                    updater = CRMUpdaterAgent()
                    
                    # Attempt to update with bad provenance
                    result = updater.apply_hubspot_update_with_idempotency(
                        object_type="company",
                        object_id="12345",
                        properties={"industry": "Golf Course Management"},
                        enrichment_results=[bad_result]
                    )
                    
                    # Verify write was blocked
                    assert result["success"] is False
                    assert result["error_type"] == "provenance_validation_failed"
                    assert result["blocked_write"] is True
                    assert "Missing source_urls" in result["error_message"]
                    assert "Missing source" in result["error_message"]
                    assert "Missing last_verified_at" in result["error_message"]
                    
                    # Verify error was logged
                    mock_logger.return_value.error.assert_called()
                    error_call = mock_logger.return_value.error.call_args
                    assert "HubSpot write blocked due to provenance validation failure" in error_call[0][0]
    
    def test_crm_updater_allows_write_with_valid_provenance(self):
        """Test that CRM updater allows writes when enrichment results have valid provenance."""
        # Create enrichment results with valid provenance
        good_result = CRMEnrichmentResult(
            field_name="company_industry",
            current_value="Unknown",
            proposed_value="Golf Course Management",
            confidence=0.95,
            source="Company website analysis",
            source_urls=["https://example-golf-course.com/about"],
            last_verified_at=datetime.now()
        )
        
        # Create CRM updater agent
        with patch('crm_agent.agents.specialized.crm_agents.create_hubspot_openapi_tool'):
            with patch('crm_agent.agents.specialized.crm_agents.get_logger'):
                with patch('crm_agent.agents.specialized.crm_agents.get_idempotency_manager') as mock_idempotency:
                    # Mock idempotency manager responses
                    mock_key = Mock()
                    mock_key.key = "test_key_123"
                    mock_idempotency.return_value.create_hubspot_update_key.return_value = mock_key
                    mock_idempotency.return_value.check_duplicate.return_value = None
                    mock_idempotency.return_value.record_operation.return_value = {
                        "success": True,
                        "resource_id": "12345"
                    }
                    
                    updater = CRMUpdaterAgent()
                    
                    # Mock the actual HubSpot update method
                    with patch.object(updater, '_execute_hubspot_update') as mock_execute:
                        with patch.object(updater, '_get_current_object_state'):
                            mock_execute.return_value = {"status": "updated", "object_id": "12345"}
                            
                            # Attempt to update with good provenance
                            result = updater.apply_hubspot_update_with_idempotency(
                                object_type="company",
                                object_id="12345",
                                properties={"industry": "Golf Course Management"},
                                enrichment_results=[good_result]
                            )
                            
                            # Verify write was allowed
                            assert result["success"] is True
                            assert "error_type" not in result
                            assert "blocked_write" not in result
                            
                            # Verify HubSpot update was actually called
                            mock_execute.assert_called_once_with(
                                "company", "12345", {"industry": "Golf Course Management"}
                            )
    
    def test_outreach_agent_blocks_engagement_with_missing_citations(self):
        """Test that outreach agent blocks engagement creation when citations are missing."""
        # Create outreach agent with citation requirements
        config_data = {
            "citation_requirements": {
                "required": True,
                "required_for": ["company_facts", "statistics", "claims"]
            }
        }
        
        with patch('crm_agent.agents.specialized.outreach_personalizer_agent.create_role_taxonomy_service'):
            with patch.object(OutreachPersonalizerAgent, '_load_config', return_value=config_data):
                agent = OutreachPersonalizerAgent()
                agent._config = config_data
                
                # Create personalization data without proper citations
                personalization = {
                    "subject_line": "Test Subject",
                    "email_content": "Test content with claims",
                    "call_to_action": "Let's connect",
                    "personalization_score": 85,
                    "messaging_strategy": "value_proposition",
                    "citations": []  # Missing required citations
                }
                
                contact_data = {"id": "contact_123", "email": "test@example.com"}
                company_data = {"id": "company_456", "name": "Test Company"}
                state = CRMSessionState()
                
                # Attempt to create email draft
                result = agent._create_email_draft(contact_data, company_data, personalization, state)
                
                # Verify engagement creation was blocked
                assert result["status"] == "blocked_by_provenance"
                assert result["error_type"] == "citation_validation_failed"
                assert result["blocked_write"] is True
                assert "company_facts" in result["missing_citations"]
                assert "statistics" in result["missing_citations"]
                assert "claims" in result["missing_citations"]
    
    def test_outreach_agent_allows_engagement_with_valid_citations(self):
        """Test that outreach agent allows engagement creation when citations are provided."""
        # Create outreach agent with citation requirements
        config_data = {
            "citation_requirements": {
                "required": True,
                "required_for": ["company_facts", "statistics", "claims"]
            }
        }
        
        with patch('crm_agent.agents.specialized.outreach_personalizer_agent.create_role_taxonomy_service'):
            with patch.object(OutreachPersonalizerAgent, '_load_config', return_value=config_data):
                agent = OutreachPersonalizerAgent()
                agent._config = config_data
                
                # Create personalization data with proper citations
                personalization = {
                    "subject_line": "Test Subject",
                    "email_content": "Test content with claims",
                    "call_to_action": "Let's connect",
                    "personalization_score": 85,
                    "messaging_strategy": "value_proposition",
                    "citations": [
                        {"type": "company_facts", "url": "https://company.com/about", "title": "About Us"},
                        {"type": "statistics", "url": "https://industry-report.com", "title": "Industry Stats"},
                        {"type": "claims", "url": "https://news.com/article", "title": "Recent News"}
                    ]
                }
                
                contact_data = {"id": "contact_123", "email": "test@example.com"}
                company_data = {"id": "company_456", "name": "Test Company"}
                state = CRMSessionState()
                
                # Attempt to create email draft
                result = agent._create_email_draft(contact_data, company_data, personalization, state)
                
                # Verify engagement creation was allowed
                assert result["status"] == "draft_created"
                assert "error_type" not in result
                assert "blocked_write" not in result
                assert result["citations_validated"] == 3
    
    def test_mixed_provenance_results_blocks_entire_operation(self):
        """Test that if any enrichment result lacks provenance, the entire operation is blocked."""
        # Create mix of good and bad enrichment results
        good_result = CRMEnrichmentResult(
            field_name="company_industry",
            current_value="Unknown",
            proposed_value="Golf Course Management",
            confidence=0.95,
            source="Company website analysis",
            source_urls=["https://example-golf-course.com/about"],
            last_verified_at=datetime.now()
        )
        
        bad_result = CRMEnrichmentResult(
            field_name="employee_count",
            current_value=None,
            proposed_value="50-100",
            confidence=0.80,
            source="",  # Missing source
            source_urls=[],  # Missing source URLs
            last_verified_at=None  # Missing verification timestamp
        )
        
        # Create CRM updater agent
        with patch('crm_agent.agents.specialized.crm_agents.create_hubspot_openapi_tool'):
            with patch('crm_agent.agents.specialized.crm_agents.get_logger'):
                with patch('crm_agent.agents.specialized.crm_agents.get_idempotency_manager'):
                    updater = CRMUpdaterAgent()
                    
                    # Attempt to update with mixed provenance
                    result = updater.apply_hubspot_update_with_idempotency(
                        object_type="company",
                        object_id="12345",
                        properties={
                            "industry": "Golf Course Management",
                            "employee_count": "50-100"
                        },
                        enrichment_results=[good_result, bad_result]
                    )
                    
                    # Verify entire operation was blocked due to one bad result
                    assert result["success"] is False
                    assert result["error_type"] == "provenance_validation_failed"
                    assert result["blocked_write"] is True
                    assert "employee_count" in result["error_message"]
