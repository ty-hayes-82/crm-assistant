#!/usr/bin/env python3
"""
Python-based Jira Assistant Agent.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from yaml_agent.mcp_bridge import call_mcp_tool, request_human_approval

def create_jira_tools():
    """Create all the Jira-related tools."""
    
    def summarize_jira_csv():
        """Get a high-level summary of the Jira CSV including total issues, projects, and statuses."""
        return call_mcp_tool("summarize_jira_csv", {})
    
    def search_jira_issues(query: str):
        """Search for issues containing specific text in summaries or descriptions."""
        return call_mcp_tool("search_jira_issues", {"query": query})
    
    def get_jira_status_breakdown():
        """Get the distribution of issues by status (Done, In Progress, Backlog, etc.)."""
        return call_mcp_tool("get_jira_status_breakdown", {})
    
    def get_jira_assignee_workload():
        """Get workload distribution showing how many issues are assigned to each person."""
        return call_mcp_tool("get_jira_assignee_workload", {})
    
    def find_stale_issues():
        """Find issues that have not been updated recently."""
        return call_mcp_tool("find_stale_issues_in_project", {})
    
    def find_blocked_issues():
        """Find issues that are marked as blocked."""
        return call_mcp_tool("find_blocked_issues_in_project", {})
    
    def find_due_soon_issues():
        """Find issues that are due in the near future."""
        return call_mcp_tool("find_due_soon_issues_in_project", {})
    
    def find_unassigned_issues():
        """Find issues that have no assignee."""
        return call_mcp_tool("find_unassigned_issues_in_project", {})
    
    # Create FunctionTool instances
    return [
        FunctionTool(summarize_jira_csv),
        FunctionTool(search_jira_issues),
        FunctionTool(get_jira_status_breakdown),
        FunctionTool(get_jira_assignee_workload),
        FunctionTool(find_stale_issues),
        FunctionTool(find_blocked_issues),
        FunctionTool(find_due_soon_issues),
        FunctionTool(find_unassigned_issues),
        FunctionTool(request_human_approval)
    ]

# Create the root agent
root_agent = LlmAgent(
    name="JiraCoordinator",
    model="gemini-2.5-flash",
    instruction="""You are a Jira project assistant. You can help users analyze Jira data,
create reports, find issues, and provide insights about project status.

Available capabilities:
- Summarize Jira CSV data
- Get status breakdowns
- Find stale, blocked, or unassigned issues
- Generate workload reports
- Search for specific issues
- Request human approval for changes

When users ask questions about Jira data, use the appropriate tools to gather the information
and provide helpful, actionable insights. Always be specific and include relevant details
from the data in your responses.""",
    tools=create_jira_tools()
)

# This is what the CLI looks for
agent = type('Agent', (), {'root_agent': root_agent})()
