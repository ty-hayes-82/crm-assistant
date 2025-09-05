"""
Data quality focused specialized agents.
Handles data quality assessment, validation, and improvement suggestions.
"""

from ...core.base_agents import JiraBaseAgent, JiraSpecializedAgent, DATA_QUALITY_TOOLS, QUERY_TOOLS


def create_data_quality_agent(**kwargs):
    """Create a specialized data quality agent for Jira data operations."""
    instruction = """You are a specialized Jira data quality agent. 
Your primary responsibility is data quality operations on Jira data.
You have access to these specialized tools: find_issues_with_missing_fields, suggest_data_fixes, apply_bulk_jira_updates

Always:
1. Load the Jira CSV data first if not already loaded using: load_jira_csv('Jira 2025-09-04T10_24_25-0700.csv')
2. Use the most appropriate tool for the user's request
3. Identify data quality issues and provide specific recommendations
4. Focus on actionable improvements that enhance data integrity
5. Save quality assessment results to session state using appropriate output keys

When performing data quality operations, use the output_key parameter to save results:
- For missing fields analysis: output_key="missing_fields_report"
- For data quality assessment: output_key="quality_assessment"
- For recommended fixes: output_key="recommended_fixes"
- For bulk update results: output_key="update_results"
"""
    
    return JiraSpecializedAgent(
        name="DataQualityAgent",
        domain="data_quality",
        specialized_tools=DATA_QUALITY_TOOLS,
        instruction=instruction,
        **kwargs
    )


def create_stale_issue_finder(**kwargs):
    """Create a specialized agent for finding and analyzing stale issues."""
    instruction = """You are the StaleIssueFinder, a specialized expert in identifying and analyzing stale issues.

Your expertise includes:
1. Finding issues that haven't been updated recently (default: 30 days)
2. Categorizing staleness by severity (30-60 days = yellow, 60+ days = red)
3. Identifying patterns in stale issues (by assignee, component, status)
4. Providing actionable recommendations for addressing staleness

Always:
1. Load the Jira CSV data first if not already loaded
2. Use find_stale_issues_in_project tool with appropriate thresholds
3. Analyze patterns and provide insights beyond just listing issues
4. Suggest specific actions for different categories of stale issues
5. Save results using output_key="stale_issues" when working in workflows

Provide detailed analysis including:
- Stale issue count and distribution
- Top assignees with stale issues
- Common characteristics of stale issues
- Prioritized recommendations for cleanup
"""
    
    return JiraSpecializedAgent(
        name="StaleIssueFinder",
        domain="stale_issue_analysis",
        specialized_tools=QUERY_TOOLS,  # Uses query tools to find stale issues
        instruction=instruction,
        **kwargs
    )


__all__ = [
    'create_data_quality_agent',
    'create_stale_issue_finder'
]
