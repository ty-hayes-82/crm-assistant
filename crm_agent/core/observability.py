"""
Observability and Structured Logging System for Phase 9.

This module provides structured logging with trace_id, session/job IDs,
audit trail capabilities, and observability features for the CRM system.
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from contextlib import contextmanager
from contextvars import ContextVar
import threading
from dataclasses import dataclass, asdict
from enum import Enum

from pydantic import BaseModel, Field


class LogLevel(str, Enum):
    """Log levels for structured logging."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class EventType(str, Enum):
    """Event types for audit trail."""
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    AGENT_INVOCATION = "agent_invocation"
    TOOL_CALL = "tool_call"
    HUBSPOT_READ = "hubspot_read"
    HUBSPOT_WRITE = "hubspot_write"
    DATA_ENRICHMENT = "data_enrichment"
    ROLE_CLASSIFICATION = "role_classification"
    LEAD_SCORING = "lead_scoring"
    OUTREACH_GENERATION = "outreach_generation"
    APPROVAL_REQUEST = "approval_request"
    APPROVAL_RESPONSE = "approval_response"
    ERROR_OCCURRED = "error_occurred"
    RETRY_ATTEMPT = "retry_attempt"
    IDEMPOTENCY_CHECK = "idempotency_check"


@dataclass
class TraceContext:
    """Trace context for distributed tracing."""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    session_id: Optional[str] = None
    job_id: Optional[str] = None
    user_id: Optional[str] = None
    
    @classmethod
    def new_trace(cls, session_id: Optional[str] = None, job_id: Optional[str] = None) -> 'TraceContext':
        """Create a new trace context."""
        return cls(
            trace_id=str(uuid.uuid4()),
            span_id=str(uuid.uuid4()),
            session_id=session_id,
            job_id=job_id
        )
    
    def new_span(self, parent_span_id: Optional[str] = None) -> 'TraceContext':
        """Create a new span within the same trace."""
        return TraceContext(
            trace_id=self.trace_id,
            span_id=str(uuid.uuid4()),
            parent_span_id=parent_span_id or self.span_id,
            session_id=self.session_id,
            job_id=self.job_id,
            user_id=self.user_id
        )


class AuditLogEntry(BaseModel):
    """Audit log entry for tracking all system changes."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    trace_id: str
    span_id: str
    session_id: Optional[str] = None
    job_id: Optional[str] = None
    event_type: EventType
    agent_name: Optional[str] = None
    operation: str
    resource_type: Optional[str] = None  # contact, company, email, task
    resource_id: Optional[str] = None
    before_state: Optional[Dict[str, Any]] = None
    after_state: Optional[Dict[str, Any]] = None
    evidence_urls: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    success: bool = True
    error_message: Optional[str] = None
    duration_ms: Optional[int] = None
    idempotency_key: Optional[str] = None


class StructuredLogEntry(BaseModel):
    """Structured log entry with trace context."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    level: LogLevel
    message: str
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    session_id: Optional[str] = None
    job_id: Optional[str] = None
    agent_name: Optional[str] = None
    operation: Optional[str] = None
    component: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[Dict[str, Any]] = None
    duration_ms: Optional[int] = None


# Context variable for trace context
_trace_context: ContextVar[Optional[TraceContext]] = ContextVar('trace_context', default=None)


class StructuredLogger:
    """
    Structured logger with trace context and audit capabilities.
    """
    
    def __init__(
        self, 
        name: str, 
        log_file: Optional[Path] = None,
        audit_file: Optional[Path] = None,
        console_output: bool = True,
        json_format: bool = True
    ):
        self.name = name
        self.log_file = log_file
        self.audit_file = audit_file
        self.console_output = console_output
        self.json_format = json_format
        
        # Set up Python logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers to avoid duplicates
        self.logger.handlers.clear()
        
        # Set up handlers
        self._setup_handlers()
        
        # Audit log storage
        self.audit_entries: List[AuditLogEntry] = []
        self._audit_lock = threading.Lock()
    
    def _setup_handlers(self):
        """Set up logging handlers."""
        formatter = self._get_formatter()
        
        # Console handler
        if self.console_output:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # File handler
        if self.log_file:
            file_handler = logging.FileHandler(self.log_file)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def _get_formatter(self) -> logging.Formatter:
        """Get appropriate formatter based on configuration."""
        if self.json_format:
            return logging.Formatter('%(message)s')
        else:
            return logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - [%(trace_id)s] %(message)s'
            )
    
    def _get_current_context(self) -> Optional[TraceContext]:
        """Get current trace context."""
        return _trace_context.get()
    
    def _log_structured(
        self, 
        level: LogLevel, 
        message: str,
        operation: Optional[str] = None,
        component: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        error: Optional[Exception] = None,
        duration_ms: Optional[int] = None
    ):
        """Log a structured entry."""
        context = self._get_current_context()
        
        entry = StructuredLogEntry(
            level=level,
            message=message,
            trace_id=context.trace_id if context else None,
            span_id=context.span_id if context else None,
            session_id=context.session_id if context else None,
            job_id=context.job_id if context else None,
            agent_name=self.name,
            operation=operation,
            component=component,
            metadata=metadata or {},
            duration_ms=duration_ms
        )
        
        if error:
            entry.error = {
                "type": type(error).__name__,
                "message": str(error),
                "traceback": None  # Could add traceback if needed
            }
        
        # Log to Python logger
        log_message = entry.model_dump_json() if self.json_format else message
        getattr(self.logger, level.lower())(log_message)
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self._log_structured(LogLevel.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self._log_structured(LogLevel.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self._log_structured(LogLevel.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message."""
        self._log_structured(LogLevel.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self._log_structured(LogLevel.CRITICAL, message, **kwargs)
    
    def audit_log(
        self,
        event_type: EventType,
        operation: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        before_state: Optional[Dict[str, Any]] = None,
        after_state: Optional[Dict[str, Any]] = None,
        evidence_urls: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        duration_ms: Optional[int] = None,
        idempotency_key: Optional[str] = None
    ) -> AuditLogEntry:
        """Create an audit log entry."""
        context = self._get_current_context()
        
        entry = AuditLogEntry(
            trace_id=context.trace_id if context else str(uuid.uuid4()),
            span_id=context.span_id if context else str(uuid.uuid4()),
            session_id=context.session_id if context else None,
            job_id=context.job_id if context else None,
            event_type=event_type,
            agent_name=self.name,
            operation=operation,
            resource_type=resource_type,
            resource_id=resource_id,
            before_state=before_state,
            after_state=after_state,
            evidence_urls=evidence_urls or [],
            metadata=metadata or {},
            success=success,
            error_message=error_message,
            duration_ms=duration_ms,
            idempotency_key=idempotency_key
        )
        
        # Store audit entry
        with self._audit_lock:
            self.audit_entries.append(entry)
        
        # Write to audit file if configured
        if self.audit_file:
            self._write_audit_entry(entry)
        
        # Also log as structured log
        self.info(
            f"Audit: {operation}",
            operation=operation,
            component="audit",
            metadata={
                "event_type": event_type,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "success": success,
                "idempotency_key": idempotency_key
            }
        )
        
        return entry
    
    def _write_audit_entry(self, entry: AuditLogEntry):
        """Write audit entry to file."""
        try:
            with open(self.audit_file, 'a', encoding='utf-8') as f:
                f.write(entry.model_dump_json() + '\n')
        except Exception as e:
            self.error(f"Failed to write audit entry: {e}", error=e)
    
    def get_audit_trail(
        self, 
        session_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        event_type: Optional[EventType] = None,
        limit: Optional[int] = None
    ) -> List[AuditLogEntry]:
        """Get audit trail with optional filtering."""
        with self._audit_lock:
            entries = self.audit_entries.copy()
        
        # Apply filters
        if session_id:
            entries = [e for e in entries if e.session_id == session_id]
        if resource_id:
            entries = [e for e in entries if e.resource_id == resource_id]
        if event_type:
            entries = [e for e in entries if e.event_type == event_type]
        
        # Sort by timestamp (newest first)
        entries.sort(key=lambda x: x.timestamp, reverse=True)
        
        # Apply limit
        if limit:
            entries = entries[:limit]
        
        return entries


class ObservabilityManager:
    """
    Central manager for observability features including tracing,
    logging, and audit trail management.
    """
    
    def __init__(self, base_log_dir: Optional[Path] = None):
        self.base_log_dir = base_log_dir or Path("logs")
        self.base_log_dir.mkdir(exist_ok=True)
        
        # Create loggers for different components
        self.loggers: Dict[str, StructuredLogger] = {}
        self._setup_default_loggers()
    
    def _setup_default_loggers(self):
        """Set up default loggers for system components."""
        components = [
            "crm_coordinator",
            "crm_updater", 
            "lead_scoring",
            "outreach_personalizer",
            "role_taxonomy",
            "a2a_server",
            "hubspot_api"
        ]
        
        for component in components:
            self.get_logger(component)
    
    def get_logger(self, name: str) -> StructuredLogger:
        """Get or create a structured logger for a component."""
        if name not in self.loggers:
            log_file = self.base_log_dir / f"{name}.log"
            audit_file = self.base_log_dir / f"{name}_audit.log"
            
            self.loggers[name] = StructuredLogger(
                name=name,
                log_file=log_file,
                audit_file=audit_file,
                console_output=True,
                json_format=True
            )
        
        return self.loggers[name]
    
    @contextmanager
    def trace_context(
        self, 
        session_id: Optional[str] = None,
        job_id: Optional[str] = None,
        trace_id: Optional[str] = None
    ):
        """Context manager for trace context."""
        if trace_id:
            # Use existing trace
            context = TraceContext(
                trace_id=trace_id,
                span_id=str(uuid.uuid4()),
                session_id=session_id,
                job_id=job_id
            )
        else:
            # Create new trace
            context = TraceContext.new_trace(session_id=session_id, job_id=job_id)
        
        token = _trace_context.set(context)
        try:
            yield context
        finally:
            _trace_context.reset(token)
    
    @contextmanager
    def span_context(self, operation: str, component: Optional[str] = None):
        """Context manager for span tracking with timing."""
        current_context = _trace_context.get()
        if not current_context:
            # Create a new trace if none exists
            with self.trace_context() as new_context:
                span_context = new_context.new_span()
                token = _trace_context.set(span_context)
                try:
                    start_time = datetime.utcnow()
                    yield span_context
                    duration = (datetime.utcnow() - start_time).total_seconds() * 1000
                    
                    # Log span completion
                    logger = self.get_logger(component or "system")
                    logger.info(
                        f"Completed span: {operation}",
                        operation=operation,
                        component=component,
                        duration_ms=int(duration)
                    )
                finally:
                    _trace_context.reset(token)
        else:
            # Create child span
            span_context = current_context.new_span()
            token = _trace_context.set(span_context)
            try:
                start_time = datetime.utcnow()
                yield span_context
                duration = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                # Log span completion
                logger = self.get_logger(component or "system")
                logger.info(
                    f"Completed span: {operation}",
                    operation=operation,
                    component=component,
                    duration_ms=int(duration)
                )
            finally:
                _trace_context.reset(token)
    
    def get_current_trace_id(self) -> Optional[str]:
        """Get current trace ID."""
        context = _trace_context.get()
        return context.trace_id if context else None
    
    def get_current_session_id(self) -> Optional[str]:
        """Get current session ID."""
        context = _trace_context.get()
        return context.session_id if context else None
    
    def create_correlation_metadata(self) -> Dict[str, Any]:
        """Create correlation metadata for external API calls."""
        context = _trace_context.get()
        if not context:
            return {}
        
        return {
            "trace_id": context.trace_id,
            "span_id": context.span_id,
            "session_id": context.session_id,
            "job_id": context.job_id
        }


# Global observability manager instance
_observability_manager: Optional[ObservabilityManager] = None


def get_observability_manager() -> ObservabilityManager:
    """Get the global observability manager."""
    global _observability_manager
    if _observability_manager is None:
        _observability_manager = ObservabilityManager()
    return _observability_manager


def get_logger(name: str) -> StructuredLogger:
    """Get a structured logger for a component."""
    return get_observability_manager().get_logger(name)


# Convenience functions
def trace_context(*args, **kwargs):
    """Create trace context."""
    return get_observability_manager().trace_context(*args, **kwargs)


def span_context(*args, **kwargs):
    """Create span context."""
    return get_observability_manager().span_context(*args, **kwargs)


def current_trace_id() -> Optional[str]:
    """Get current trace ID."""
    return get_observability_manager().get_current_trace_id()


def current_session_id() -> Optional[str]:
    """Get current session ID."""
    return get_observability_manager().get_current_session_id()


def correlation_metadata() -> Dict[str, Any]:
    """Get correlation metadata for external calls."""
    return get_observability_manager().create_correlation_metadata()
