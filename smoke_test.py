import sys
import os

# Ensure yaml_agent is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'yaml_agent'))
from yaml_agent import mcp_bridge as b


def main() -> None:
    """Updated smoke tests to use the MCP bridge correctly."""
    print("Running smoke tests for Jira MCP wrappers...\n")

    print("SUMMARY:")
    print(b.call_mcp_tool("summarize_jira_csv", {})[:400], "\n")

    print("PROJECTS:")
    print(b.call_mcp_tool("get_jira_project_breakdown", {})[:400], "\n")

    print("PRIORITIES:")
    print(b.call_mcp_tool("get_jira_priority_breakdown", {})[:400], "\n")

    print("OVERVIEW (3 assignees, 3 statuses):")
    print(b.call_mcp_tool(
        "get_overview_bundle_tool",
        {"top_n_assignees": 3, "top_n_statuses": 3}
    )[:600], "\n")

    print("ASSIGNEE FILTER (ashley, top 3):")
    print(b.call_mcp_tool(
        "filter_jira_by_assignee",
        {"assignee_query": 'ashley', "top_n": 3}
    )[:600], "\n")

    print("EPIC CHILDREN (BI-607, top 3):")
    print(b.call_mcp_tool(
        "list_epic_children",
        {"epic_key": 'BI-607', "top_n": 3}
    )[:600], "\n")

    print("EPIC RECENT PROGRESS (BI-607, 7 days, top 5):")
    print(b.call_mcp_tool(
        "get_epic_recent_progress",
        {"epic_key": 'BI-607', "days": 7, "top_n": 5}
    )[:600], "\n")

    print("FIELD COMPLETENESS:")
    print(b.call_mcp_tool("audit_jira_field_completeness", {})[:400], "\n")

    # Skip Jira API tests unless env vars are set
    required_env = ['JIRA_URL', 'JIRA_USERNAME', 'JIRA_API_TOKEN']
    if all(os.getenv(v) for v in required_env):
        print("JIRA API - FIND USER (example: 'john'):")
        print(b.call_mcp_tool("jira_find_user", {"query": 'john'})[:400], "\n")
    else:
        print("JIRA API tests skipped (missing env vars).\n")


if __name__ == '__main__':
    main()
