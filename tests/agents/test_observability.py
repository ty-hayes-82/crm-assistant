#!/usr/bin/env python3
"""
Tests for Observability System (Phase 9).

Tests structured logging, trace context, audit trails,
and observability features.
"""

import pytest
import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch
import threading
import time

from crm_agent.core.observability import (
    StructuredLogger,
    ObservabilityManager,
    TraceContext,
    AuditLogEntry,
    StructuredLogEntry,
    LogLevel,
    EventType,
    get_observability_manager,
    get_logger,
    trace_context,
    span_context,
    current_trace_id,
    correlation_metadata
)


class TestTraceContext:
    """Test suite for trace context management."""
    
    def test_new_trace_creation(self):
        """Test creation of new trace context."""
        context = TraceContext.new_trace(session_id="test_session", job_id="test_job")
        
        assert context.trace_id is not None
        assert context.span_id is not None
        assert context.session_id == "test_session"
        assert context.job_id == "test_job"
        assert context.parent_span_id is None
    
    def test_new_span_creation(self):
        """Test creation of child spans."""
        parent_context = TraceContext.new_trace()
        child_context = parent_context.new_span()
        
        assert child_context.trace_id == parent_context.trace_id
        assert child_context.span_id != parent_context.span_id
        assert child_context.parent_span_id == parent_context.span_id
        assert child_context.session_id == parent_context.session_id


class TestStructuredLogger:
    """Test suite for structured logger."""
    
    @pytest.fixture
    def temp_log_file(self):
        """Create temporary log file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            yield Path(f.name)
        Path(f.name).unlink(missing_ok=True)
    
    @pytest.fixture
    def temp_audit_file(self):
        """Create temporary audit file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.audit') as f:
            yield Path(f.name)
        Path(f.name).unlink(missing_ok=True)
    
    def test_logger_creation(self, temp_log_file, temp_audit_file):
        """Test structured logger creation."""
        logger = StructuredLogger(
            name="test_logger",
            log_file=temp_log_file,
            audit_file=temp_audit_file,
            console_output=False,
            json_format=True
        )
        
        assert logger.name == "test_logger"
        assert logger.log_file == temp_log_file
        assert logger.audit_file == temp_audit_file
    
    def test_structured_logging_levels(self):
        """Test different log levels."""
        logger = StructuredLogger(name="test", console_output=False)
        
        # Test all log levels
        logger.debug("Debug message", operation="test_op")
        logger.info("Info message", component="test_component")
        logger.warning("Warning message", metadata={"key": "value"})
        logger.error("Error message", error=Exception("Test error"))
        logger.critical("Critical message", duration_ms=100)
        
        # Should not raise any exceptions
        assert True
    
    def test_audit_logging(self, temp_audit_file):
        """Test audit log functionality."""
        logger = StructuredLogger(
            name="test_audit",
            audit_file=temp_audit_file,
            console_output=False
        )
        
        # Create audit log entry
        entry = logger.audit_log(
            event_type=EventType.HUBSPOT_WRITE,
            operation="update_contact",
            resource_type="contact",
            resource_id="12345",
            before_state={"name": "John Doe"},
            after_state={"name": "John Smith"},
            evidence_urls=["https://example.com/source"],
            success=True
        )
        
        assert entry.event_type == EventType.HUBSPOT_WRITE
        assert entry.operation == "update_contact"
        assert entry.resource_id == "12345"
        assert entry.success is True
        assert len(entry.evidence_urls) == 1
        
        # Check that audit entry was written to file
        if temp_audit_file.exists():
            content = temp_audit_file.read_text()
            assert "update_contact" in content
    
    def test_audit_trail_retrieval(self):
        """Test audit trail retrieval with filtering."""
        logger = StructuredLogger(name="test_audit", console_output=False)
        
        # Create multiple audit entries
        logger.audit_log(
            event_type=EventType.HUBSPOT_WRITE,
            operation="update_contact",
            resource_id="contact_1",
            success=True
        )
        
        logger.audit_log(
            event_type=EventType.HUBSPOT_READ,
            operation="get_contact",
            resource_id="contact_2",
            success=True
        )
        
        logger.audit_log(
            event_type=EventType.HUBSPOT_WRITE,
            operation="update_company",
            resource_id="company_1",
            success=False,
            error_message="API error"
        )
        
        # Test filtering by event type
        write_entries = logger.get_audit_trail(event_type=EventType.HUBSPOT_WRITE)
        assert len(write_entries) == 2
        
        # Test filtering by resource ID
        contact_entries = logger.get_audit_trail(resource_id="contact_1")
        assert len(contact_entries) == 1
        assert contact_entries[0].resource_id == "contact_1"
        
        # Test limit
        limited_entries = logger.get_audit_trail(limit=2)
        assert len(limited_entries) <= 2


class TestObservabilityManager:
    """Test suite for observability manager."""
    
    @pytest.fixture
    def temp_log_dir(self):
        """Create temporary log directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    def test_manager_creation(self, temp_log_dir):
        """Test observability manager creation."""
        manager = ObservabilityManager(base_log_dir=temp_log_dir)
        
        assert manager.base_log_dir == temp_log_dir
        assert len(manager.loggers) > 0  # Default loggers created
    
    def test_logger_retrieval(self, temp_log_dir):
        """Test logger retrieval and creation."""
        manager = ObservabilityManager(base_log_dir=temp_log_dir)
        
        # Get existing logger
        logger1 = manager.get_logger("test_component")
        logger2 = manager.get_logger("test_component")
        
        # Should return same instance
        assert logger1 is logger2
        
        # Should create log files
        expected_log_file = temp_log_dir / "test_component.log"
        expected_audit_file = temp_log_dir / "test_component_audit.log"
        
        assert logger1.log_file == expected_log_file
        assert logger1.audit_file == expected_audit_file
    
    def test_trace_context_manager(self):
        """Test trace context manager."""
        manager = ObservabilityManager()
        
        with manager.trace_context(session_id="test_session") as context:
            assert context.session_id == "test_session"
            assert context.trace_id is not None
            
            # Should be able to get current trace ID
            assert current_trace_id() == context.trace_id
        
        # Context should be cleared after exiting
        assert current_trace_id() is None
    
    def test_span_context_manager(self):
        """Test span context manager with timing."""
        manager = ObservabilityManager()
        
        with manager.trace_context():
            with manager.span_context("test_operation", "test_component") as span:
                assert span.span_id is not None
                time.sleep(0.01)  # Small delay to test timing
        
        # Should complete without errors
        assert True
    
    def test_nested_spans(self):
        """Test nested span creation."""
        manager = ObservabilityManager()
        
        with manager.trace_context() as root_context:
            with manager.span_context("parent_op") as parent_span:
                parent_trace_id = parent_span.trace_id
                parent_span_id = parent_span.span_id
                
                with manager.span_context("child_op") as child_span:
                    # Child should have same trace ID but different span ID
                    assert child_span.trace_id == parent_trace_id
                    assert child_span.span_id != parent_span_id
                    assert child_span.parent_span_id == parent_span_id
    
    def test_correlation_metadata(self):
        """Test correlation metadata generation."""
        manager = ObservabilityManager()
        
        with manager.trace_context(session_id="test_session", job_id="test_job"):
            metadata = correlation_metadata()
            
            assert "trace_id" in metadata
            assert "session_id" in metadata
            assert "job_id" in metadata
            assert metadata["session_id"] == "test_session"
            assert metadata["job_id"] == "test_job"
    
    def test_concurrent_trace_contexts(self):
        """Test that trace contexts are properly isolated across threads."""
        manager = ObservabilityManager()
        results = []
        
        def worker(session_id: str):
            with manager.trace_context(session_id=session_id):
                time.sleep(0.01)  # Simulate work
                trace_id = current_trace_id()
                results.append((session_id, trace_id))
        
        # Start multiple threads with different contexts
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=[f"session_{i}"])
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Each thread should have had a different trace ID
        trace_ids = [result[1] for result in results]
        assert len(set(trace_ids)) == 5  # All unique
        assert all(trace_id is not None for trace_id in trace_ids)


class TestAuditLogEntry:
    """Test suite for audit log entry model."""
    
    def test_audit_entry_creation(self):
        """Test audit log entry creation."""
        entry = AuditLogEntry(
            trace_id="test_trace",
            span_id="test_span",
            event_type=EventType.HUBSPOT_WRITE,
            operation="update_contact",
            resource_type="contact",
            resource_id="12345",
            before_state={"name": "John"},
            after_state={"name": "Jane"},
            success=True
        )
        
        assert entry.trace_id == "test_trace"
        assert entry.event_type == EventType.HUBSPOT_WRITE
        assert entry.operation == "update_contact"
        assert entry.success is True
        assert isinstance(entry.timestamp, datetime)
    
    def test_audit_entry_serialization(self):
        """Test audit log entry JSON serialization."""
        entry = AuditLogEntry(
            trace_id="test_trace",
            span_id="test_span",
            event_type=EventType.AGENT_INVOCATION,
            operation="classify_role",
            metadata={"confidence": 0.85}
        )
        
        # Should serialize to JSON without errors
        json_data = entry.model_dump_json()
        assert isinstance(json_data, str)
        
        # Should be able to parse back
        parsed_data = json.loads(json_data)
        assert parsed_data["trace_id"] == "test_trace"
        assert parsed_data["event_type"] == "agent_invocation"


class TestStructuredLogEntry:
    """Test suite for structured log entry model."""
    
    def test_log_entry_creation(self):
        """Test structured log entry creation."""
        entry = StructuredLogEntry(
            level=LogLevel.INFO,
            message="Test message",
            trace_id="test_trace",
            operation="test_operation",
            metadata={"key": "value"}
        )
        
        assert entry.level == LogLevel.INFO
        assert entry.message == "Test message"
        assert entry.trace_id == "test_trace"
        assert entry.metadata["key"] == "value"
    
    def test_log_entry_with_error(self):
        """Test log entry with error information."""
        entry = StructuredLogEntry(
            level=LogLevel.ERROR,
            message="Error occurred",
            error={
                "type": "ValueError",
                "message": "Invalid input",
                "traceback": None
            }
        )
        
        assert entry.level == LogLevel.ERROR
        assert entry.error["type"] == "ValueError"


class TestGlobalFunctions:
    """Test suite for global convenience functions."""
    
    def test_get_logger_function(self):
        """Test global get_logger function."""
        logger = get_logger("test_global")
        
        assert isinstance(logger, StructuredLogger)
        assert logger.name == "test_global"
    
    def test_trace_context_function(self):
        """Test global trace_context function."""
        with trace_context(session_id="global_test") as context:
            assert context.session_id == "global_test"
            assert current_trace_id() == context.trace_id
    
    def test_span_context_function(self):
        """Test global span_context function."""
        with trace_context():
            with span_context("global_span", "global_component") as span:
                assert span.span_id is not None
    
    def test_correlation_metadata_function(self):
        """Test global correlation_metadata function."""
        with trace_context(session_id="meta_test"):
            metadata = correlation_metadata()
            assert "trace_id" in metadata
            assert metadata["session_id"] == "meta_test"


class TestIntegration:
    """Integration tests for observability system."""
    
    def test_end_to_end_logging_flow(self, temp_log_dir=None):
        """Test complete logging flow with trace context."""
        if temp_log_dir is None:
            temp_log_dir = Path(tempfile.mkdtemp())
        
        manager = ObservabilityManager(base_log_dir=temp_log_dir)
        logger = manager.get_logger("integration_test")
        
        # Start trace context
        with manager.trace_context(session_id="integration_session") as context:
            # Log structured message
            logger.info(
                "Starting integration test",
                operation="integration_test",
                component="test_suite"
            )
            
            # Create span for operation
            with manager.span_context("test_operation", "test_component"):
                # Log within span
                logger.debug("Processing within span")
                
                # Create audit log
                audit_entry = logger.audit_log(
                    event_type=EventType.AGENT_INVOCATION,
                    operation="test_agent_call",
                    success=True,
                    metadata={"test": True}
                )
                
                assert audit_entry.trace_id == context.trace_id
                assert audit_entry.session_id == context.session_id
        
        # Check that logs were created
        log_file = temp_log_dir / "integration_test.log"
        if log_file.exists():
            content = log_file.read_text()
            assert "integration_test" in content
    
    def test_error_handling_and_recovery(self):
        """Test error handling in observability system."""
        logger = StructuredLogger(name="error_test", console_output=False)
        
        # Test logging with invalid data
        try:
            logger.error(
                "Test error with complex data",
                metadata={"circular_ref": None},  # This should be handled gracefully
                error=ValueError("Test exception")
            )
            
            # Should not raise exception
            assert True
        except Exception as e:
            pytest.fail(f"Logging should handle errors gracefully: {e}")
    
    def test_performance_with_high_volume(self):
        """Test performance with high volume logging."""
        logger = StructuredLogger(name="perf_test", console_output=False)
        
        start_time = datetime.utcnow()
        
        # Log many entries quickly
        for i in range(100):
            logger.info(f"High volume test message {i}", metadata={"index": i})
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        # Should complete in reasonable time (less than 1 second)
        assert duration < 1.0
