"""
Utility to register all Jira CSV MCP tools onto any provided MCP server instance.

Use this when you want to load these tools into an existing MCP server (e.g.,
your 'jira-tools' server) instead of running the standalone mcp_toolbox server.
"""

from typing import Optional


def register_all_tools(mcp):
    """Register all CSV analytics and Jira API tools onto the given MCP instance."""
    # Local imports to avoid side effects at module import time
    from ..utils.jira_reader import (
        read_jira_csv_summary,
        get_status_distribution,
        get_project_distribution,
        get_priority_distribution,
        get_assignee_workload,
        search_issues_by_text,
        list_epics,
        epic_health_report,
        audit_field_completeness,
        recent_progress,
        get_issue_details,
        list_epic_items,
        audit_epic_field_gaps,
        epic_recent_progress,
    )
    from ..utils.jira_api import (
        find_user,
        get_issue,
        create_issue,
        update_issue,
        add_comment,
    )
    import json

    # --- CSV tools ---
    @mcp.tool()
    def csv_summarize_jira_csv(filename: Optional[str] = None) -> str:
        return read_jira_csv_summary(filename)

    @mcp.tool()
    def csv_get_jira_status_breakdown(filename: Optional[str] = None) -> str:
        return get_status_distribution(filename)

    @mcp.tool()
    def csv_get_jira_project_breakdown(filename: Optional[str] = None) -> str:
        return get_project_distribution(filename)

    @mcp.tool()
    def csv_get_jira_priority_breakdown(filename: Optional[str] = None) -> str:
        return get_priority_distribution(filename)

    @mcp.tool()
    def csv_get_jira_assignee_workload(top_n: int = 10, filename: Optional[str] = None) -> str:
        return get_assignee_workload(top_n=top_n, filename=filename)

    @mcp.tool()
    def csv_search_jira_issues(search_term: str, filename: Optional[str] = None) -> str:
        return search_issues_by_text(search_term, filename)

    @mcp.tool()
    def csv_list_jira_epics(top_n: int = 20, filename: Optional[str] = None) -> str:
        return list_epics(filename=filename, top_n=top_n)

    @mcp.tool()
    def csv_get_epic_health(epic_key: str, filename: Optional[str] = None) -> str:
        return epic_health_report(epic_key=epic_key, filename=filename)

    @mcp.tool()
    def csv_audit_jira_field_completeness(filename: Optional[str] = None) -> str:
        return audit_field_completeness(filename=filename)

    @mcp.tool()
    def csv_get_recent_progress(days: int = 14, top_n: int = 50, filename: Optional[str] = None) -> str:
        return recent_progress(days=days, filename=filename, top_n=top_n)

    @mcp.tool()
    def csv_get_issue_full_details(issue_key: str, filename: Optional[str] = None) -> str:
        return get_issue_details(issue_key=issue_key, filename=filename)

    @mcp.tool()
    def csv_list_epic_children(epic_key: str, top_n: int = 100, filename: Optional[str] = None) -> str:
        return list_epic_items(epic_key=epic_key, top_n=top_n, filename=filename)

    @mcp.tool()
    def csv_audit_epic_gaps(epic_key: str, filename: Optional[str] = None) -> str:
        return audit_epic_field_gaps(epic_key=epic_key, filename=filename)

    @mcp.tool()
    def csv_get_epic_recent_progress(epic_key: str, days: int = 14, top_n: int = 50, filename: Optional[str] = None) -> str:
        return epic_recent_progress(epic_key=epic_key, days=days, filename=filename, top_n=top_n)

    # --- Jira API tools ---
    @mcp.tool()
    def csv_jira_find_user(query: str) -> str:
        users = find_user(query)
        return json.dumps(users, indent=2)

    @mcp.tool()
    def csv_jira_get_issue(issue_key: str) -> str:
        issue = get_issue(issue_key)
        return json.dumps(issue, indent=2)

    @mcp.tool()
    def csv_jira_create_issue(project_key: str, summary: str, description: str, issue_type: str = "Task") -> str:
        new_issue = create_issue(project_key, summary, description, issue_type)
        return json.dumps(new_issue, indent=2)

    @mcp.tool()
    def csv_jira_add_comment(issue_key: str, comment: str) -> str:
        new_comment = add_comment(issue_key, comment)
        return json.dumps(new_comment, indent=2)

    return mcp

