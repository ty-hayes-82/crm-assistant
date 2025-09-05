"""
Jira Agent System - Multi-agent system for Jira data analysis and management.

This package provides a comprehensive multi-agent system for analyzing Jira data,
generating reports, and managing data quality. The system follows Google ADK
best practices and implements various agent patterns including coordination,
specialization, and workflow orchestration.

Main Components:
- Core: Base classes, factories, and data models
- Agents: Specialized domain agents and workflow orchestrators  
- Coordination: Main coordinator and entry points
- Utils: Error handling and monitoring utilities
"""

# Suppress ADK experimental warnings at package level
from .utils.warning_suppression import suppress_adk_warnings
suppress_adk_warnings()

# Core exports
from .core import (
    JiraBaseAgent,
    JiraSpecializedAgent,
    JiraWorkflowAgent,
    JIRA_AGENT_DEFAULTS,
    AgentRegistry,
    create_agent_registry
)

# Main coordination exports
from .coordination import (
    create_jira_coordinator,
    root_agent
)

# Specialized agents (most commonly used)
from .agents.specialized import (
    create_query_agent,
    create_analysis_agent,
    create_reporting_agent,
    create_data_quality_agent,
    create_simple_agent
)

# Workflow agents
from .agents.workflows import (
    create_risk_assessment_pipeline,
    create_data_quality_workflow,
    create_comprehensive_info_workflow,
    create_project_health_dashboard
)

__version__ = "1.0.0"

__all__ = [
    # Core components
    'JiraBaseAgent',
    'JiraSpecializedAgent',
    'JiraWorkflowAgent', 
    'JIRA_AGENT_DEFAULTS',
    'AgentRegistry',
    'create_agent_registry',
    
    # Main entry points
    'create_jira_coordinator',
    'root_agent',
    
    # Specialized agents
    'create_query_agent',
    'create_analysis_agent', 
    'create_reporting_agent',
    'create_data_quality_agent',
    'create_simple_agent',
    
    # Workflow agents
    'create_risk_assessment_pipeline',
    'create_data_quality_workflow',
    'create_comprehensive_info_workflow',
    'create_project_health_dashboard'
]
