"""
Query-focused specialized agents.
Handles data queries, searches, and issue lookups.
"""

from ...core.base_agents import JiraBaseAgent, JiraSpecializedAgent, QUERY_TOOLS


def create_query_agent(**kwargs):
    """Create a specialized query agent for Jira data operations."""
    instruction = """You are a specialized Jira query agent. 
Your primary responsibility is query operations on Jira data.
You have access to these specialized tools: load_jira_csv, list_jira_issues, get_issue_details, search_issues, find_unassigned_issues_in_project, find_stale_issues_in_project, find_blocked_issues_in_project, find_due_soon_issues_in_project

Always:
1. Load the Jira CSV data first if not already loaded using: load_jira_csv('Jira 2025-09-04T10_24_25-0700.csv')
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


def create_simple_agent(**kwargs):
    """Create a simple general-purpose Jira agent."""
    instruction = """You are a general-purpose Jira agent with access to comprehensive Jira tools.

Your capabilities include:
1. Loading and analyzing Jira CSV data
2. Querying issues by various criteria
3. Generating reports and summaries
4. Analyzing data quality and suggesting improvements

Always start by loading the Jira CSV data using: load_jira_csv('Jira 2025-09-04T10_24_25-0700.csv')

Be helpful, thorough, and provide actionable insights based on the Jira data."""
    
    return JiraBaseAgent(
        name="SimpleJiraAgent",
        description="General-purpose Jira agent with comprehensive toolset",
        instruction=instruction,
        **kwargs
    )


def create_clarification_agent(**kwargs):
    """Create an agent specialized in clarifying ambiguous requests."""
    instruction = """You are a clarification specialist for Jira operations.

When users make ambiguous or unclear requests, your role is to:
1. Identify what information is missing or unclear
2. Ask specific, helpful questions to clarify the request
3. Provide examples of what the user might be looking for
4. Guide users toward more specific requests

You have access to basic query tools to understand the available data structure.
Use these tools to provide context-aware clarification questions.

Always be helpful and guide users toward successful outcomes."""
    
    return JiraSpecializedAgent(
        name="ClarificationAgent",
        domain="clarification",
        specialized_tools=QUERY_TOOLS[:4],  # Basic tools for understanding data structure
        instruction=instruction,
        **kwargs
    )


__all__ = [
    'create_query_agent',
    'create_simple_agent', 
    'create_clarification_agent'
]
