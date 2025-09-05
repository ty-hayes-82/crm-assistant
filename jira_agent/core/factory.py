"""
Agent Factory with Registry Pattern for dynamic agent creation.
Implements the registry pattern for flexible, testable agent management.
"""

from typing import Dict, Type, Callable, List, Any, Optional
from google.adk.agents import BaseAgent, LlmAgent
from .base_agents import (
    JiraBaseAgent, 
    JiraSpecializedAgent,
    QUERY_TOOLS,
    ANALYSIS_TOOLS,
    REPORTING_TOOLS,
    DATA_QUALITY_TOOLS
)


class AgentRegistry:
    """
    Registry for dynamic agent creation and management.
    Enables flexible agent composition and easy testing.
    """
    
    def __init__(self):
        self._agent_factories: Dict[str, Callable[..., BaseAgent]] = {}
        self._agent_metadata: Dict[str, Dict[str, Any]] = {}
        self._register_default_agents()
    
    def register(self, name: str, factory: Callable[..., BaseAgent], metadata: Optional[Dict] = None):
        """
        Register an agent factory function.
        
        Args:
            name: Agent type name
            factory: Factory function that creates the agent
            metadata: Optional metadata about the agent
        """
        self._agent_factories[name] = factory
        self._agent_metadata[name] = metadata or {}
    
    def create_agent(self, name: str, **kwargs) -> BaseAgent:
        """
        Create an agent instance by name.
        
        Args:
            name: Agent type name
            **kwargs: Arguments passed to the agent factory
            
        Returns:
            Configured agent instance
            
        Raises:
            ValueError: If agent type is not registered
        """
        if name not in self._agent_factories:
            available = ", ".join(self.list_agents())
            raise ValueError(f"Unknown agent type: {name}. Available: {available}")
        
        return self._agent_factories[name](**kwargs)
    
    def list_agents(self) -> List[str]:
        """List all registered agent types."""
        return list(self._agent_factories.keys())
    
    def get_agent_metadata(self, name: str) -> Dict[str, Any]:
        """Get metadata for a specific agent type."""
        return self._agent_metadata.get(name, {})
    
    def _register_default_agents(self):
        """Register the default set of Jira agents."""
        
        # Query Agent - Handles data queries and searches
        def create_query_agent(**kwargs):
            # Enhanced instruction with automatic data loading
            instruction = """You are a specialized Jira query agent with automatic data loading.

🚀 STARTUP BEHAVIOR: Immediately when you start or receive your first user message, automatically load the Jira CSV data by calling load_jira_csv() without any parameters. This will find and load the most recent Jira export file. Do this before responding to the user's question.

Your primary responsibility is query operations on Jira data.
You have access to these specialized tools: load_jira_csv, list_jira_issues, get_issue_details, search_issues, find_unassigned_issues_in_project, find_stale_issues_in_project, find_blocked_issues_in_project, find_due_soon_issues_in_project

Always:
1. 🔄 AUTO-LOAD: On your first interaction, immediately call load_jira_csv() to load the most recent CSV file
2. Use the most appropriate tool for the user's request
3. Provide clear, actionable insights
4. Format results in a user-friendly way
5. Save important results to session state using appropriate output keys

When finding specific types of issues, use the output_key parameter to save results:
- For unassigned issues: output_key="unassigned_issues"
- For stale issues: output_key="stale_issues" 
- For blocked issues: output_key="blocked_issues"
- For due soon issues: output_key="due_soon_issues"
- For general query results: output_key="last_query_results"
"""
            
            return JiraSpecializedAgent(
                name="QueryAgent",
                domain="query",
                specialized_tools=QUERY_TOOLS,
                instruction=instruction,
                **kwargs
            )
        
        self.register("query", create_query_agent, {
            "description": "Handles data queries, searches, and issue lookups",
            "domain": "query",
            "tools": QUERY_TOOLS
        })
        
        # Analysis Agent - Performs data analysis and metrics
        def create_analysis_agent(**kwargs):
            # Enhanced instruction with automatic data loading
            instruction = """You are a specialized Jira analysis agent with automatic data loading.

🚀 STARTUP BEHAVIOR: Immediately when you start or receive your first user message, automatically load the Jira CSV data by calling load_jira_csv() without any parameters. This will find and load the most recent Jira export file. Do this before responding to the user's question.

Your primary responsibility is analysis operations on Jira data.
You have access to these specialized tools: summarize_jira_csv, get_jira_status_breakdown, get_jira_assignee_workload, find_issues_with_missing_fields, suggest_data_fixes

Always:
1. 🔄 AUTO-LOAD: On your first interaction, immediately call load_jira_csv() to load the most recent CSV file
2. Use the most appropriate tool for the user's request
3. Provide clear, actionable insights with metrics and analysis
4. Format results in a user-friendly way with charts and breakdowns when possible
5. Save analysis results to session state using appropriate output keys

When performing analysis, use the output_key parameter to save results:
- For status breakdown: output_key="status_breakdown"
- For workload analysis: output_key="workload_analysis"  
- For data quality reports: output_key="quality_report"
- For risk assessments: output_key="risk_report"
"""
            
            return JiraSpecializedAgent(
                name="AnalysisAgent", 
                domain="analysis",
                specialized_tools=ANALYSIS_TOOLS,
                instruction=instruction,
                **kwargs
            )
        
        self.register("analysis", create_analysis_agent, {
            "description": "Performs data analysis, metrics calculation, and insights",
            "domain": "analysis", 
            "tools": ANALYSIS_TOOLS
        })
        
        # Reporting Agent - Generates reports and summaries
        def create_reporting_agent(**kwargs):
            # Enhanced instruction with automatic data loading
            instruction = """You are a specialized Jira reporting agent with automatic data loading.

🚀 STARTUP BEHAVIOR: Immediately when you start or receive your first user message, automatically load the Jira CSV data by calling load_jira_csv() without any parameters. This will find and load the most recent Jira export file. Do this before responding to the user's question.

Your primary responsibility is reporting operations on Jira data.
You have access to these specialized tools: get_status_summary, get_assignee_summary, summarize_jira_csv, get_jira_status_breakdown, get_jira_assignee_workload

Always:
1. 🔄 AUTO-LOAD: On your first interaction, immediately call load_jira_csv() to load the most recent CSV file
2. Use the most appropriate tools for comprehensive reporting
3. Create well-formatted, professional reports with clear sections
4. Include executive summaries and key takeaways
5. Use data from session state when available to create comprehensive reports

When generating reports, you can read from session state:
- Use {status_breakdown} for status analysis data
- Use {workload_analysis} for assignee workload data
- Use {risk_report} for risk assessment data
- Use {quality_report} for data quality information

Focus on creating actionable, executive-ready reports with clear insights and recommendations.
"""
            
            return JiraSpecializedAgent(
                name="ReportingAgent",
                domain="reporting", 
                specialized_tools=REPORTING_TOOLS,
                instruction=instruction,
                **kwargs
            )
        
        self.register("reporting", create_reporting_agent, {
            "description": "Generates reports, summaries, and formatted outputs",
            "domain": "reporting",
            "tools": REPORTING_TOOLS
        })
        
        # Data Quality Agent - Handles data quality and cleanup
        def create_data_quality_agent(**kwargs):
            return JiraSpecializedAgent(
                name="DataQualityAgent",
                domain="data quality",
                specialized_tools=DATA_QUALITY_TOOLS,
                **kwargs
            )
        
        self.register("data_quality", create_data_quality_agent, {
            "description": "Handles data quality analysis and cleanup operations", 
            "domain": "data_quality",
            "tools": DATA_QUALITY_TOOLS
        })
        
        # Clarification Agent - Handles ambiguous requests
        def create_clarification_agent(**kwargs):
            instruction = """You are a clarification agent. When the coordinator transfers 
ambiguous requests to you, ask specific clarifying questions to determine the user's intent.
Present clear options and help the user specify exactly what they want.

For example:
- If they say "show me updates", ask if they want recent ticket updates or a status report
- If they say "find issues", ask what type of issues or criteria they're looking for
- Always provide 2-3 specific options for the user to choose from

Once you have clarification, summarize their intent clearly."""
            
            return JiraBaseAgent(
                name="ClarificationAgent",
                description="Asks clarifying questions when user requests are ambiguous",
                instruction=instruction,
                **kwargs
            )
        
        self.register("clarification", create_clarification_agent, {
            "description": "Handles ambiguous requests by asking clarifying questions",
            "domain": "clarification",
            "tools": []
        })
        
        # Simple Jira Agent - The current basic agent
        def create_simple_agent(**kwargs):
            instruction = """You are a Jira assistant that automatically loads and analyzes Jira tickets from CSV files.

🚀 STARTUP BEHAVIOR: Immediately when you start or receive your first user message, automatically load the Jira CSV data by calling load_jira_csv() without any parameters. This will find and load the most recent Jira export file from the docs/jira_exports/ folder. Do this before responding to the user's question.

After loading the data, provide a brief welcome message showing:
- How many issues were loaded
- The data source file name
- A few example things the user can ask for

Available capabilities:
- List and search tickets
- Get details for specific issues
- Generate status and assignee summaries
- Analyze project health and risks
- Find data quality issues
- Create comprehensive reports

Always:
1. 🔄 AUTO-LOAD: On your first interaction, immediately call load_jira_csv() to load the most recent CSV file
2. Provide helpful, actionable insights
3. Format results clearly and professionally
4. Suggest follow-up questions when appropriate
"""
            return JiraBaseAgent(
                name="jira_csv_assistant",
                description="Basic Jira CSV assistant for simple operations",
                instruction=instruction,
                **kwargs
            )
        
        self.register("simple", create_simple_agent, {
            "description": "Basic Jira CSV assistant (current implementation)",
            "domain": "simple",
            "tools": ["all"]
        })
        
        # Specialized Phase 4 Agents
        def create_stale_finder_agent(**kwargs):
            from .specialized_agents import create_stale_issue_finder
            return create_stale_issue_finder()
        
        def create_blocked_analyzer_agent(**kwargs):
            from .specialized_agents import create_blocked_issue_analyzer
            return create_blocked_issue_analyzer()
        
        def create_due_monitor_agent(**kwargs):
            from .specialized_agents import create_due_date_monitor
            return create_due_date_monitor()
        
        def create_quality_auditor_agent(**kwargs):
            from .specialized_agents import create_data_quality_auditor
            return create_data_quality_auditor()
        
        def create_executive_reporter_agent(**kwargs):
            from .specialized_agents import create_executive_reporter
            return create_executive_reporter()
        
        def create_health_analyst_agent(**kwargs):
            from .specialized_agents import create_project_health_analyst
            return create_project_health_analyst()
        
        # Register specialized agents
        self.register("stale_finder", create_stale_finder_agent, {
            "description": "Specialized expert in stale issue detection and analysis",
            "domain": "risk_monitoring",
            "tools": ["find_stale_issues_in_project"]
        })
        
        self.register("blocked_analyzer", create_blocked_analyzer_agent, {
            "description": "Specialized expert in blocked issue analysis and resolution",
            "domain": "risk_monitoring", 
            "tools": ["find_blocked_issues_in_project"]
        })
        
        self.register("due_monitor", create_due_monitor_agent, {
            "description": "Specialized expert in deadline management and schedule risk",
            "domain": "risk_monitoring",
            "tools": ["find_due_soon_issues_in_project"]
        })
        
        self.register("quality_auditor", create_quality_auditor_agent, {
            "description": "Specialized expert in data quality auditing and governance",
            "domain": "data_quality",
            "tools": ["find_issues_with_missing_fields", "suggest_data_fixes"]
        })
        
        self.register("executive_reporter", create_executive_reporter_agent, {
            "description": "Specialized expert in executive-level reporting with AgentTool access",
            "domain": "reporting",
            "tools": ["agent_tools"]
        })
        
        self.register("health_analyst", create_health_analyst_agent, {
            "description": "Comprehensive project health expert with multi-agent orchestration",
            "domain": "analysis",
            "tools": ["agent_tools"]
        })


# Global registry instance
agent_registry = AgentRegistry()


# Convenience functions for creating common agents
def create_query_agent(**kwargs) -> BaseAgent:
    """Create a QueryAgent instance."""
    return agent_registry.create_agent("query", **kwargs)


def create_analysis_agent(**kwargs) -> BaseAgent:
    """Create an AnalysisAgent instance.""" 
    return agent_registry.create_agent("analysis", **kwargs)


def create_reporting_agent(**kwargs) -> BaseAgent:
    """Create a ReportingAgent instance."""
    return agent_registry.create_agent("reporting", **kwargs)


def create_data_quality_agent(**kwargs) -> BaseAgent:
    """Create a DataQualityAgent instance."""
    return agent_registry.create_agent("data_quality", **kwargs)


def create_clarification_agent(**kwargs) -> BaseAgent:
    """Create a ClarificationAgent instance."""
    return agent_registry.create_agent("clarification", **kwargs)


def create_simple_agent(**kwargs) -> BaseAgent:
    """Create the simple Jira agent (current implementation)."""
    return agent_registry.create_agent("simple", **kwargs)


# Export the main agent creation function
def get_jira_agent(agent_type: str = "simple", **kwargs) -> BaseAgent:
    """
    Main function to get a Jira agent of the specified type.
    
    Args:
        agent_type: Type of agent ("simple", "query", "analysis", "reporting", "data_quality", "clarification")
        **kwargs: Additional arguments for agent creation
        
    Returns:
        Configured Jira agent
    """
    return agent_registry.create_agent(agent_type, **kwargs)


def create_agent_registry() -> AgentRegistry:
    """Create a new agent registry with default agents."""
    return AgentRegistry()