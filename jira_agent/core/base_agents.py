"""
Base agent classes and utilities for Jira multi-agent system.
Provides common functionality and patterns for all Jira agents.
"""

# Suppress warnings before importing ADK components
from ..utils.warning_suppression import suppress_adk_warnings
suppress_adk_warnings()

from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools.mcp_tool import StdioConnectionParams
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from mcp import StdioServerParameters
from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod


class JiraBaseAgent(LlmAgent):
    """
    Base class for all Jira agents with common MCP toolset configuration.
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        instruction: str,
        model: str = 'gemini-2.5-flash',
        additional_tools: Optional[List] = None,
        **kwargs
    ):
        """
        Initialize a Jira agent with standard MCP toolset.
        
        Args:
            name: Agent name
            description: Agent description for routing
            instruction: System instruction for the agent
            model: LLM model to use (default: gemini-2.5-flash)
            additional_tools: Additional tools beyond MCP toolset
            **kwargs: Additional arguments passed to LlmAgent
        """
        # Standard MCP toolset for all Jira agents (with warning suppression)
        from ..utils.warning_suppression import SuppressWarnings
        with SuppressWarnings():
            mcp_toolset = MCPToolset(
                connection_params=StdioConnectionParams(
                    server_params=StdioServerParameters(
                        command='python',
                        args=['-m', 'jira_fastmcp_server'],
                    ),
                    timeout=30,
                ),
            )
        
        # Combine MCP tools with any additional tools
        tools = [mcp_toolset]
        if additional_tools:
            tools.extend(additional_tools)
        
        super().__init__(
            model=model,
            name=name,
            description=description,
            instruction=instruction,
            tools=tools,
            **kwargs
        )


class JiraSpecializedAgent(JiraBaseAgent):
    """
    Base class for specialized domain agents with focused responsibilities.
    """
    
    def __init__(
        self,
        name: str,
        domain: str,
        specialized_tools: List[str],
        instruction: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize a specialized agent for a specific domain.
        
        Args:
            name: Agent name
            domain: Domain of expertise (e.g., "query", "analysis", "reporting")
            specialized_tools: List of MCP tool names this agent specializes in
            instruction: Custom instruction (if None, will generate default)
            **kwargs: Additional arguments
        """
        description = f"Specialized agent for {domain} operations in Jira data"
        
        # Use provided instruction or build default based on domain and tools
        if instruction is None:
            tools_list = ", ".join(specialized_tools)
            instruction = f"""You are a specialized Jira {domain} agent. 
Your primary responsibility is {domain} operations on Jira data.
You have access to these specialized tools: {tools_list}

Always:
1. Load the Jira CSV data first if not already loaded
2. Use the most appropriate tool for the user's request
3. Provide clear, actionable insights
4. Format results in a user-friendly way
"""
        
        super().__init__(
            name=name,
            description=description,
            instruction=instruction,
            **kwargs
        )
        
        # Store domain and tools in the description for reference
        # (Can't add custom attributes to Pydantic models)


class JiraWorkflowAgent(ABC):
    """
    Abstract base class for workflow agents that orchestrate other agents.
    """
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    @abstractmethod
    def get_sub_agents(self) -> List[LlmAgent]:
        """Return the list of sub-agents for this workflow."""
        pass
    
    @abstractmethod
    def get_workflow_instruction(self) -> str:
        """Return the instruction for coordinating this workflow."""
        pass


# Common agent configurations
JIRA_AGENT_DEFAULTS = {
    'model': 'gemini-2.5-flash',
    'timeout': 30,
}

# Standard tool groups for different agent types
QUERY_TOOLS = [
    'load_jira_csv',
    'list_jira_issues', 
    'get_issue_details',
    'search_issues',
    'find_unassigned_issues_in_project',
    'find_stale_issues_in_project',
    'find_blocked_issues_in_project',
    'find_due_soon_issues_in_project'
]

ANALYSIS_TOOLS = [
    'summarize_jira_csv',
    'get_jira_status_breakdown',
    'get_jira_assignee_workload',
    'find_issues_with_missing_fields',
    'suggest_data_fixes'
]

REPORTING_TOOLS = [
    'get_status_summary',
    'get_assignee_summary',
    'summarize_jira_csv',
    'get_jira_status_breakdown',
    'get_jira_assignee_workload'
]

DATA_QUALITY_TOOLS = [
    'find_issues_with_missing_fields',
    'suggest_data_fixes',
    'apply_bulk_jira_updates'
]
