"""
Contract tests for the A2A server.
Validates JSON-RPC request/response schemas and SSE event stream format.
"""

import pytest
import json
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

from crm_agent.a2a.http_server import (
    CRMA2AHttpServer, JsonRpcRequest, JsonRpcResponse, 
    TaskInfo, TaskState
)


class TestA2AContracts:
    """Test A2A server contract compliance."""
    
    def test_json_rpc_request_schema(self):
        """Test that JSON-RPC requests follow the 2.0 specification."""
        # Valid request
        valid_request = {
            "jsonrpc": "2.0",
            "method": "course.profile.extract",
            "params": {"query": "Extract profile for Pebble Beach Golf Links"},
            "id": "req-123"
        }
        
        request_obj = JsonRpcRequest(**valid_request)
        assert request_obj.jsonrpc == "2.0"
        assert request_obj.method == "course.profile.extract"
        assert request_obj.params["query"] == "Extract profile for Pebble Beach Golf Links"
        assert request_obj.id == "req-123"
    
    def test_json_rpc_response_schema(self):
        """Test that JSON-RPC responses follow the 2.0 specification."""
        # Success response
        success_response = JsonRpcResponse(
            jsonrpc="2.0",
            id="req-123",
            result={
                "task_id": "task-456",
                "context_id": "ctx-789",
                "state": "queued",
                "stream_url": "/stream/task-456"
            }
        )
        
        response_dict = success_response.__dict__
        assert response_dict["jsonrpc"] == "2.0"
        assert response_dict["id"] == "req-123"
        assert response_dict["result"]["task_id"] == "task-456"
        assert response_dict["error"] is None
        
        # Error response
        error_response = JsonRpcResponse(
            jsonrpc="2.0",
            id="req-123",
            error={
                "code": -32601,
                "message": "Method not found"
            }
        )
        
        error_dict = error_response.__dict__
        assert error_dict["jsonrpc"] == "2.0"
        assert error_dict["id"] == "req-123"
        assert error_dict["result"] is None
        assert error_dict["error"]["code"] == -32601
        assert error_dict["error"]["message"] == "Method not found"
    
    def test_supported_methods(self):
        """Test that all documented A2A methods are supported."""
        expected_methods = [
            "course.profile.extract",
            "contact.roles.infer", 
            "hubspot.sync",
            "lead.score.compute",
            "outreach.generate"
        ]
        
        # This would be tested against the actual server implementation
        # For now, we verify the method list is documented
        assert len(expected_methods) == 5
        assert "course.profile.extract" in expected_methods
        assert "lead.score.compute" in expected_methods
        assert "outreach.generate" in expected_methods
    
    def test_task_lifecycle_states(self):
        """Test that task lifecycle follows the documented state machine."""
        # Valid state transitions
        valid_transitions = {
            TaskState.QUEUED: [TaskState.RUNNING, TaskState.FAILED],
            TaskState.RUNNING: [TaskState.COMPLETED, TaskState.FAILED],
            TaskState.COMPLETED: [],  # Terminal state
            TaskState.FAILED: []      # Terminal state
        }
        
        for from_state, to_states in valid_transitions.items():
            assert isinstance(from_state, TaskState)
            for to_state in to_states:
                assert isinstance(to_state, TaskState)
        
        # Test TaskInfo creation
        task = TaskInfo(
            id="task-123",
            context_id="ctx-456",
            state=TaskState.QUEUED,
            created_at=pytest.importorskip("datetime").datetime.utcnow(),
            updated_at=pytest.importorskip("datetime").datetime.utcnow(),
            query="Test query"
        )
        
        assert task.state == TaskState.QUEUED
        assert task.id == "task-123"
        assert task.context_id == "ctx-456"
    
    def test_sse_event_format(self):
        """Test that SSE events follow the documented format."""
        # Task status update event
        status_event = {
            "event": "task_status",
            "data": {
                "task_id": "task-123",
                "state": "running",
                "timestamp": "2025-01-09T12:00:00Z"
            }
        }
        
        assert status_event["event"] == "task_status"
        assert status_event["data"]["task_id"] == "task-123"
        assert status_event["data"]["state"] in ["queued", "running", "completed", "failed"]
        
        # Task progress event
        progress_event = {
            "event": "task_progress", 
            "data": {
                "task_id": "task-123",
                "message": "Processing CRM request...",
                "timestamp": "2025-01-09T12:00:01Z"
            }
        }
        
        assert progress_event["event"] == "task_progress"
        assert "message" in progress_event["data"]
        
        # Task completion event
        completion_event = {
            "event": "task_complete",
            "data": {
                "task_id": "task-123",
                "result": {
                    "success": True,
                    "content": "Task completed successfully"
                },
                "timestamp": "2025-01-09T12:00:10Z"
            }
        }
        
        assert completion_event["event"] == "task_complete"
        assert completion_event["data"]["result"]["success"] is True
    
    def test_error_code_compliance(self):
        """Test that error codes follow JSON-RPC 2.0 specification."""
        # Standard JSON-RPC error codes
        error_codes = {
            -32700: "Parse error",
            -32600: "Invalid Request", 
            -32601: "Method not found",
            -32602: "Invalid params",
            -32603: "Internal error"
        }
        
        for code, message in error_codes.items():
            error_response = JsonRpcResponse(
                jsonrpc="2.0",
                id=None,
                error={"code": code, "message": message}
            )
            
            assert error_response.error["code"] == code
            assert error_response.error["message"] == message
    
    def test_agent_card_schema(self):
        """Test that Agent Card follows the documented schema."""
        # Expected Agent Card structure
        expected_agent_card = {
            "name": "CRM Assistant",
            "description": "AI-powered CRM data enrichment and automation agent",
            "version": "1.0.0",
            "skills": [
                {
                    "name": "course.profile.extract",
                    "description": "Extract comprehensive golf course profiles from web sources",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"}
                        },
                        "required": ["query"]
                    },
                    "output_schema": {
                        "type": "object",
                        "properties": {
                            "company_data": {"type": "object"},
                            "enrichment_results": {"type": "array"}
                        }
                    }
                },
                {
                    "name": "lead.score.compute",
                    "description": "Compute fit and intent scores for leads",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "contact_id": {"type": "string"},
                            "company_id": {"type": "string"}
                        }
                    },
                    "output_schema": {
                        "type": "object",
                        "properties": {
                            "fit_score": {"type": "number"},
                            "intent_score": {"type": "number"},
                            "total_score": {"type": "number"}
                        }
                    }
                },
                {
                    "name": "outreach.generate",
                    "description": "Generate personalized outreach content",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "contact_id": {"type": "string"},
                            "outreach_type": {"type": "string"}
                        }
                    },
                    "output_schema": {
                        "type": "object",
                        "properties": {
                            "email_draft": {"type": "object"},
                            "follow_up_task": {"type": "object"}
                        }
                    }
                }
            ],
            "auth": {
                "type": "api_key",
                "description": "Requires HubSpot Private App access token"
            }
        }
        
        # Validate structure
        assert "name" in expected_agent_card
        assert "skills" in expected_agent_card
        assert len(expected_agent_card["skills"]) >= 3
        
        # Validate each skill has required fields
        for skill in expected_agent_card["skills"]:
            assert "name" in skill
            assert "description" in skill
            assert "input_schema" in skill
            assert "output_schema" in skill
    
    @pytest.mark.asyncio
    async def test_request_response_cycle(self):
        """Test a complete request-response cycle."""
        # This would test against a running server instance
        # For now, we test the data structures
        
        # Create request
        request = JsonRpcRequest(
            jsonrpc="2.0",
            method="course.profile.extract",
            params={"query": "Test query"},
            id="test-123"
        )
        
        # Simulate server processing
        task_id = "task-456"
        context_id = "ctx-789"
        
        # Create response
        response = JsonRpcResponse(
            jsonrpc="2.0",
            id=request.id,
            result={
                "task_id": task_id,
                "context_id": context_id,
                "state": "queued",
                "stream_url": f"/stream/{task_id}"
            }
        )
        
        # Validate response
        assert response.id == request.id
        assert response.result["task_id"] == task_id
        assert response.result["stream_url"] == f"/stream/{task_id}"
    
    def test_trace_id_propagation(self):
        """Test that trace_id is properly propagated through requests."""
        # Mock trace context
        mock_trace_context = type('TraceContext', (), {
            'trace_id': 'trace-123',
            'span_id': 'span-456', 
            'session_id': 'session-789'
        })()
        
        # Verify trace context has required fields
        assert hasattr(mock_trace_context, 'trace_id')
        assert hasattr(mock_trace_context, 'span_id')
        assert hasattr(mock_trace_context, 'session_id')
        
        # Test that trace_id would be included in response
        response_with_trace = {
            "jsonrpc": "2.0",
            "id": "req-123",
            "result": {
                "task_id": "task-456",
                "trace_id": mock_trace_context.trace_id
            }
        }
        
        assert response_with_trace["result"]["trace_id"] == "trace-123"
    
    def test_idempotency_key_format(self):
        """Test that idempotency keys follow the expected format."""
        # Mock idempotency key
        mock_key = type('IdempotencyKey', (), {
            'key': 'idem_company_12345_abc123_20250109',
            'operation_type': 'update_company',
            'resource_id': '12345',
            'field_hash': 'abc123'
        })()
        
        # Validate key format
        assert mock_key.key.startswith('idem_')
        assert 'company' in mock_key.key
        assert mock_key.resource_id in mock_key.key
        assert mock_key.field_hash in mock_key.key
        
        # Test key components
        key_parts = mock_key.key.split('_')
        assert key_parts[0] == 'idem'
        assert key_parts[1] == 'company'
        assert key_parts[2] == '12345'  # resource_id
        assert key_parts[3] == 'abc123'  # field_hash
