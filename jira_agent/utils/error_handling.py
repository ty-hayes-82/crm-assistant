"""
Error handling and recovery mechanisms for the Jira multi-agent system.
Provides graceful degradation and user-friendly error messages.
"""

import logging
import traceback
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for better handling."""
    DATA_LOADING = "data_loading"
    AGENT_ROUTING = "agent_routing"
    TOOL_EXECUTION = "tool_execution"
    STATE_MANAGEMENT = "state_management"
    WORKFLOW_EXECUTION = "workflow_execution"
    CONFIGURATION = "configuration"
    NETWORK = "network"
    UNKNOWN = "unknown"


class JiraAgentError(Exception):
    """Base exception for Jira agent system errors."""
    
    def __init__(
        self, 
        message: str, 
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        recovery_suggestions: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.category = category
        self.severity = severity
        self.recovery_suggestions = recovery_suggestions or []
        self.context = context or {}
        self.timestamp = datetime.now()


class DataLoadingError(JiraAgentError):
    """Error during data loading operations."""
    
    def __init__(self, message: str, filepath: Optional[str] = None, **kwargs):
        super().__init__(
            message, 
            category=ErrorCategory.DATA_LOADING,
            severity=ErrorSeverity.HIGH,
            **kwargs
        )
        if filepath:
            self.context["filepath"] = filepath


class AgentRoutingError(JiraAgentError):
    """Error during agent routing and delegation."""
    
    def __init__(self, message: str, agent_name: Optional[str] = None, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.AGENT_ROUTING,
            severity=ErrorSeverity.MEDIUM,
            **kwargs
        )
        if agent_name:
            self.context["agent_name"] = agent_name


class ToolExecutionError(JiraAgentError):
    """Error during tool execution."""
    
    def __init__(self, message: str, tool_name: Optional[str] = None, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.TOOL_EXECUTION,
            severity=ErrorSeverity.MEDIUM,
            **kwargs
        )
        if tool_name:
            self.context["tool_name"] = tool_name


class WorkflowExecutionError(JiraAgentError):
    """Error during workflow execution."""
    
    def __init__(self, message: str, workflow_name: Optional[str] = None, step: Optional[str] = None, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.WORKFLOW_EXECUTION,
            severity=ErrorSeverity.HIGH,
            **kwargs
        )
        if workflow_name:
            self.context["workflow_name"] = workflow_name
        if step:
            self.context["step"] = step


class ErrorHandler:
    """Central error handling and recovery system."""
    
    def __init__(self):
        self.logger = logging.getLogger("jira_agent_system")
        self.error_history: List[JiraAgentError] = []
        self.recovery_strategies = self._initialize_recovery_strategies()
    
    def _initialize_recovery_strategies(self) -> Dict[ErrorCategory, List[str]]:
        """Initialize recovery strategies for different error categories."""
        return {
            ErrorCategory.DATA_LOADING: [
                "Check if the CSV file exists and is readable",
                "Verify the file path is correct",
                "Ensure the file is not corrupted or locked",
                "Try loading a different CSV file",
                "Check file permissions"
            ],
            ErrorCategory.AGENT_ROUTING: [
                "Verify the agent name is correct",
                "Check if the agent is properly registered",
                "Try using the ClarificationAgent for ambiguous requests",
                "Restart the coordinator agent",
                "Use a simpler, more direct request"
            ],
            ErrorCategory.TOOL_EXECUTION: [
                "Check if the MCP server is running",
                "Verify tool parameters are correct",
                "Ensure data is loaded before using analysis tools",
                "Try a simpler version of the operation",
                "Check network connectivity"
            ],
            ErrorCategory.WORKFLOW_EXECUTION: [
                "Check if all required data is available",
                "Verify workflow step dependencies",
                "Try running individual steps separately",
                "Check session state for missing data",
                "Restart the workflow from the beginning"
            ],
            ErrorCategory.STATE_MANAGEMENT: [
                "Clear the session state and restart",
                "Check for state corruption",
                "Verify state model validation",
                "Try creating a new session",
                "Check memory usage"
            ],
            ErrorCategory.CONFIGURATION: [
                "Verify agent configuration is valid",
                "Check environment variables",
                "Validate YAML configuration files",
                "Ensure all dependencies are installed",
                "Check ADK version compatibility"
            ],
            ErrorCategory.NETWORK: [
                "Check internet connectivity",
                "Verify MCP server is accessible",
                "Check firewall settings",
                "Try again after a short delay",
                "Verify API endpoints are available"
            ]
        }
    
    def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Handle an error with appropriate logging and recovery suggestions.
        
        Args:
            error: The exception that occurred
            context: Additional context about the error
            
        Returns:
            User-friendly error message with recovery suggestions
        """
        # Convert to JiraAgentError if needed
        if not isinstance(error, JiraAgentError):
            jira_error = self._convert_to_jira_error(error, context)
        else:
            jira_error = error
        
        # Log the error
        self._log_error(jira_error)
        
        # Add to error history
        self.error_history.append(jira_error)
        
        # Generate user-friendly response
        return self._generate_user_response(jira_error)
    
    def _convert_to_jira_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> JiraAgentError:
        """Convert a generic exception to a JiraAgentError."""
        error_message = str(error)
        category = self._categorize_error(error, error_message)
        severity = self._assess_severity(error, category)
        
        return JiraAgentError(
            message=error_message,
            category=category,
            severity=severity,
            context=context or {}
        )
    
    def _categorize_error(self, error: Exception, message: str) -> ErrorCategory:
        """Categorize an error based on its type and message."""
        error_type = type(error).__name__.lower()
        message_lower = message.lower()
        
        # Data loading errors
        if "file" in message_lower or "csv" in message_lower or "parquet" in message_lower:
            return ErrorCategory.DATA_LOADING
        
        # Network/connection errors
        if "connection" in message_lower or "network" in message_lower or "timeout" in message_lower:
            return ErrorCategory.NETWORK
        
        # Agent/routing errors
        if "agent" in message_lower or "routing" in message_lower or "transfer" in message_lower:
            return ErrorCategory.AGENT_ROUTING
        
        # Tool execution errors
        if "tool" in message_lower or "mcp" in message_lower:
            return ErrorCategory.TOOL_EXECUTION
        
        # Workflow errors
        if "workflow" in message_lower or "pipeline" in message_lower or "sequential" in message_lower:
            return ErrorCategory.WORKFLOW_EXECUTION
        
        # Configuration errors
        if "config" in message_lower or "yaml" in message_lower or "validation" in message_lower:
            return ErrorCategory.CONFIGURATION
        
        # State management errors
        if "state" in message_lower or "session" in message_lower:
            return ErrorCategory.STATE_MANAGEMENT
        
        return ErrorCategory.UNKNOWN
    
    def _assess_severity(self, error: Exception, category: ErrorCategory) -> ErrorSeverity:
        """Assess the severity of an error."""
        # Critical errors that break the system
        if isinstance(error, (SystemError, MemoryError)):
            return ErrorSeverity.CRITICAL
        
        # High severity for data and workflow issues
        if category in [ErrorCategory.DATA_LOADING, ErrorCategory.WORKFLOW_EXECUTION]:
            return ErrorSeverity.HIGH
        
        # Medium severity for most operational issues
        if category in [ErrorCategory.AGENT_ROUTING, ErrorCategory.TOOL_EXECUTION]:
            return ErrorSeverity.MEDIUM
        
        # Low severity for minor issues
        return ErrorSeverity.LOW
    
    def _log_error(self, error: JiraAgentError):
        """Log an error with appropriate level."""
        log_message = f"[{error.category.value.upper()}] {error.message}"
        
        if error.context:
            log_message += f" | Context: {error.context}"
        
        if error.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message)
        elif error.severity == ErrorSeverity.HIGH:
            self.logger.error(log_message)
        elif error.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
    
    def _generate_user_response(self, error: JiraAgentError) -> str:
        """Generate a user-friendly error response."""
        # Base response
        response = f"❌ **Error:** {error.message}\n\n"
        
        # Add severity indicator
        severity_icons = {
            ErrorSeverity.CRITICAL: "🚨",
            ErrorSeverity.HIGH: "⚠️",
            ErrorSeverity.MEDIUM: "⚡",
            ErrorSeverity.LOW: "ℹ️"
        }
        response += f"{severity_icons[error.severity]} **Severity:** {error.severity.value.title()}\n\n"
        
        # Add recovery suggestions
        suggestions = error.recovery_suggestions or self.recovery_strategies.get(error.category, [])
        if suggestions:
            response += "🔧 **Try these solutions:**\n"
            for i, suggestion in enumerate(suggestions[:3], 1):  # Limit to top 3
                response += f"{i}. {suggestion}\n"
            response += "\n"
        
        # Add context if available
        if error.context:
            response += "📋 **Additional Details:**\n"
            for key, value in error.context.items():
                response += f"- {key}: {value}\n"
            response += "\n"
        
        # Add general help
        response += "💡 **Need more help?** Try using simpler commands or ask for clarification."
        
        return response
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics for monitoring."""
        if not self.error_history:
            return {"total_errors": 0}
        
        stats = {
            "total_errors": len(self.error_history),
            "by_category": {},
            "by_severity": {},
            "recent_errors": len([e for e in self.error_history if (datetime.now() - e.timestamp).seconds < 3600])
        }
        
        # Count by category
        for error in self.error_history:
            category = error.category.value
            stats["by_category"][category] = stats["by_category"].get(category, 0) + 1
        
        # Count by severity
        for error in self.error_history:
            severity = error.severity.value
            stats["by_severity"][severity] = stats["by_severity"].get(severity, 0) + 1
        
        return stats
    
    def clear_error_history(self):
        """Clear the error history."""
        self.error_history.clear()


# Global error handler instance
error_handler = ErrorHandler()


def handle_agent_error(func):
    """Decorator for handling agent errors gracefully."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_message = error_handler.handle_error(e, {"function": func.__name__})
            return f"Error in {func.__name__}: {error_message}"
    return wrapper


def safe_agent_call(agent_func, *args, **kwargs):
    """Safely call an agent function with error handling."""
    try:
        return agent_func(*args, **kwargs)
    except Exception as e:
        return error_handler.handle_error(e, {"agent_function": agent_func.__name__})


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('jira_agent_system.log'),
        logging.StreamHandler()
    ]
)
