from ..server import mcp
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
    filter_issues_by_assignee,
    get_assignee_two_week_summary,
    get_overview_bundle,
)
from ..utils.jira_reader import _append_request_log, _resolve_csv_path
from ..utils.jira_api import (
    find_user,
    get_issue,
    create_issue,
    update_issue,
    add_comment
)
import json

# --- CSV-based Tools (Read-Only) ---

@mcp.tool()
def summarize_jira_csv(filename: str | None = None) -> str:
    """
    Get a high-level summary of the Jira CSV file including total issues, columns, projects, and statuses.
    
    Args:
        filename: Optional CSV filename in the /docs directory. If omitted, uses the newest Jira*.csv.
    
    Returns:
        A string with basic statistics about the Jira data
    """
    result = read_jira_csv_summary(filename)
    csv_file = None
    try:
        csv_file = _resolve_csv_path(filename).name if filename or True else None
    except Exception:
        pass
    _append_request_log(tool_name="summarize_jira_csv", params={"filename": filename}, csv_file=csv_file, response_preview=result)
    return result

@mcp.tool()
def get_jira_status_breakdown(filename: str | None = None) -> str:
    """
    Get the distribution of Jira issues by status (e.g., Done, In Progress, Backlog, etc.).
    
    Returns:
        A string showing the count and percentage of issues in each status
    """
    result = get_status_distribution(filename)
    csv_file = None
    try:
        csv_file = _resolve_csv_path(filename).name
    except Exception:
        pass
    _append_request_log(tool_name="get_jira_status_breakdown", params={"filename": filename}, csv_file=csv_file, response_preview=result)
    return result

@mcp.tool()
def get_jira_project_breakdown(filename: str | None = None) -> str:
    """
    Get the distribution of Jira issues by project key.
    
    Returns:
        A string showing the count and percentage of issues in each project
    """
    result = get_project_distribution(filename)
    csv_file = None
    try:
        csv_file = _resolve_csv_path(filename).name
    except Exception:
        pass
    _append_request_log(tool_name="get_jira_project_breakdown", params={"filename": filename}, csv_file=csv_file, response_preview=result)
    return result

@mcp.tool()
def get_jira_priority_breakdown(filename: str | None = None) -> str:
    """
    Get the distribution of Jira issues by priority level.
    
    Returns:
        A string showing the count and percentage of issues by priority
    """
    result = get_priority_distribution(filename)
    csv_file = None
    try:
        csv_file = _resolve_csv_path(filename).name
    except Exception:
        pass
    _append_request_log(tool_name="get_jira_priority_breakdown", params={"filename": filename}, csv_file=csv_file, response_preview=result)
    return result

@mcp.tool()
def get_jira_assignee_workload(top_n: int = 10, filename: str | None = None) -> str:
    """
    Get the workload distribution showing how many issues are assigned to each person.
    
    Args:
        top_n: Number of top assignees to show (default: 10)
    
    Returns:
        A string showing the assigned and unassigned issues breakdown
    """
    result = get_assignee_workload(top_n=top_n, filename=filename)
    csv_file = None
    try:
        csv_file = _resolve_csv_path(filename).name
    except Exception:
        pass
    _append_request_log(tool_name="get_jira_assignee_workload", params={"top_n": top_n, "filename": filename}, csv_file=csv_file, response_preview=result)
    return result

@mcp.tool()
def search_jira_issues(search_term: str, filename: str | None = None, top_n: int = 10, page: int = 1) -> str:
    """
    Search for Jira issues containing specific text in the Summary or Description fields.
    
    Args:
        search_term: Text to search for in issue summaries and descriptions
    
    Returns:
        A string showing matching issues with their key, summary, status, and assignee
    """
    result = search_issues_by_text(search_term, filename, top_n=top_n, page=page)
    csv_file = None
    try:
        csv_file = _resolve_csv_path(filename).name
    except Exception:
        pass
    _append_request_log(tool_name="search_jira_issues", params={"search_term": search_term, "filename": filename, "top_n": top_n, "page": page}, csv_file=csv_file, response_preview=result)
    return result

# --- New: Epics, Field Gaps, Recent Progress ---

@mcp.tool()
def list_jira_epics(top_n: int = 20, filename: str | None = None) -> str:
    """List epics with child counts and completion percentage."""
    result = list_epics(filename=filename, top_n=top_n)
    csv_file = None
    try:
        csv_file = _resolve_csv_path(filename).name
    except Exception:
        pass
    _append_request_log(tool_name="list_jira_epics", params={"top_n": top_n, "filename": filename}, csv_file=csv_file, response_preview=result)
    return result

@mcp.tool()
def get_epic_health(epic_key: str, filename: str | None = None) -> str:
    """Detailed epic health with child breakdown and recent updates."""
    result = epic_health_report(epic_key=epic_key, filename=filename)
    csv_file = None
    try:
        csv_file = _resolve_csv_path(filename).name
    except Exception:
        pass
    _append_request_log(tool_name="get_epic_health", params={"epic_key": epic_key, "filename": filename}, csv_file=csv_file, response_preview=result)
    return result

@mcp.tool()
def audit_jira_field_completeness(filename: str | None = None) -> str:
    """Identify fields with the highest missing rates across issues."""
    result = audit_field_completeness(filename=filename)
    csv_file = None
    try:
        csv_file = _resolve_csv_path(filename).name
    except Exception:
        pass
    _append_request_log(tool_name="audit_jira_field_completeness", params={"filename": filename}, csv_file=csv_file, response_preview=result)
    return result

@mcp.tool()
def get_recent_progress(days: int = 14, top_n: int = 50, filename: str | None = None) -> str:
    """Show issues updated in the last N days, grouped by epic when possible."""
    result = recent_progress(days=days, filename=filename, top_n=top_n)
    csv_file = None
    try:
        csv_file = _resolve_csv_path(filename).name
    except Exception:
        pass
    _append_request_log(tool_name="get_recent_progress", params={"days": days, "top_n": top_n, "filename": filename}, csv_file=csv_file, response_preview=result)
    return result

@mcp.tool()
def get_issue_full_details(issue_key: str, filename: str | None = None) -> str:
    """Return all fields for a single issue as key: value lines."""
    result = get_issue_details(issue_key=issue_key, filename=filename)
    csv_file = None
    try:
        csv_file = _resolve_csv_path(filename).name
    except Exception:
        pass
    _append_request_log(tool_name="get_issue_full_details", params={"issue_key": issue_key, "filename": filename}, csv_file=csv_file, response_preview=result)
    return result

@mcp.tool()
def filter_jira_by_assignee(
    assignee_query: str,
    filename: str | None = None,
    top_n: int = 100,
    include_unassigned: bool = False,
    case_insensitive: bool = True,
) -> str:
    """
    Filter issues by assignee using substring matching on the CSV export.

    Args:
        assignee_query: Substring to match within the Assignee field (e.g., 'ashley', 'Ashley_cleavenger')
        filename: Optional CSV filename in /docs (defaults to newest Jira*.csv)
        top_n: Max number of results to show
        include_unassigned: Include rows with empty assignee if True
        case_insensitive: Case-insensitive matching when True

    Returns:
        Human-readable lines of matching issues.
    """
    result = filter_issues_by_assignee(
        assignee_query=assignee_query,
        filename=filename,
        top_n=top_n,
        include_unassigned=include_unassigned,
        case_insensitive=case_insensitive,
    )
    csv_file = None
    try:
        csv_file = _resolve_csv_path(filename).name
    except Exception:
        pass
    _append_request_log(
        tool_name="filter_jira_by_assignee",
        params={
            "assignee_query": assignee_query,
            "top_n": top_n,
            "include_unassigned": include_unassigned,
            "case_insensitive": case_insensitive,
            "filename": filename,
        },
        csv_file=csv_file,
        response_preview=result,
    )
    return result

@mcp.tool()
def list_epic_children(epic_key: str, top_n: int = 100, filename: str | None = None) -> str:
    """List items under an epic with key details."""
    result = list_epic_items(epic_key=epic_key, top_n=top_n, filename=filename)
    csv_file = None
    try:
        csv_file = _resolve_csv_path(filename).name
    except Exception:
        pass
    _append_request_log(tool_name="list_epic_children", params={"epic_key": epic_key, "top_n": top_n, "filename": filename}, csv_file=csv_file, response_preview=result)
    return result

@mcp.tool()
def audit_epic_gaps(epic_key: str, filename: str | None = None) -> str:
    """Audit missing fields within an epic's items to surface gaps."""
    result = audit_epic_field_gaps(epic_key=epic_key, filename=filename)
    csv_file = None
    try:
        csv_file = _resolve_csv_path(filename).name
    except Exception:
        pass
    _append_request_log(tool_name="audit_epic_gaps", params={"epic_key": epic_key, "filename": filename}, csv_file=csv_file, response_preview=result)
    return result

@mcp.tool()
def get_epic_recent_progress(epic_key: str, days: int = 14, top_n: int = 50, filename: str | None = None) -> str:
    """Show most recently updated items within a single epic."""
    result = epic_recent_progress(epic_key=epic_key, days=days, filename=filename, top_n=top_n)
    csv_file = None
    try:
        csv_file = _resolve_csv_path(filename).name
    except Exception:
        pass
    _append_request_log(tool_name="get_epic_recent_progress", params={"epic_key": epic_key, "days": days, "top_n": top_n, "filename": filename}, csv_file=csv_file, response_preview=result)
    return result

@mcp.tool()
def get_assignee_two_week_summary_tool(assignee_query: str, days: int = 14, top_n_per_section: int = 5, filename: str | None = None) -> str:
    """Generate a 2-week activity summary for a single assignee (substring match)."""
    result = get_assignee_two_week_summary(
        assignee_query=assignee_query,
        days=days,
        filename=filename,
        top_n_per_section=top_n_per_section,
    )
    csv_file = None
    try:
        csv_file = _resolve_csv_path(filename).name
    except Exception:
        pass
    _append_request_log(
        tool_name="get_assignee_two_week_summary",
        params={"assignee_query": assignee_query, "days": days, "top_n_per_section": top_n_per_section, "filename": filename},
        csv_file=csv_file,
        response_preview=result,
    )
    return result

@mcp.tool()
def get_overview_bundle_tool(filename: str | None = None, top_n_assignees: int = 5, top_n_statuses: int = 5) -> str:
    """Return a compact overview bundle: statuses, priorities, and top assignees."""
    result = get_overview_bundle(filename=filename, top_n_assignees=top_n_assignees, top_n_statuses=top_n_statuses)
    csv_file = None
    try:
        csv_file = _resolve_csv_path(filename).name
    except Exception:
        pass
    _append_request_log(
        tool_name="get_overview_bundle",
        params={"filename": filename, "top_n_assignees": top_n_assignees, "top_n_statuses": top_n_statuses},
        csv_file=csv_file,
        response_preview=result,
    )
    return result

# --- Jira API Tools (Read-Write) ---

@mcp.tool()
def jira_find_user(query: str) -> str:
    """
    Find a Jira user by their name or email address. Requires JIRA_URL, JIRA_USERNAME, and JIRA_API_TOKEN environment variables.
    
    Args:
        query: The name or email to search for.
    
    Returns:
        A JSON string of matching users.
    """
    users = find_user(query)
    result = json.dumps(users, indent=2)
    _append_request_log(tool_name="jira_find_user", params={"query": query}, csv_file=None, response_preview=result)
    return result

@mcp.tool()
def jira_get_issue(issue_key: str) -> str:
    """
    Get the full details of a specific Jira issue. Requires JIRA_URL, JIRA_USERNAME, and JIRA_API_TOKEN environment variables.
    
    Args:
        issue_key: The key of the issue (e.g., 'PROJ-123').
    
    Returns:
        A JSON string of the issue details.
    """
    issue = get_issue(issue_key)
    result = json.dumps(issue, indent=2)
    _append_request_log(tool_name="jira_get_issue", params={"issue_key": issue_key}, csv_file=None, response_preview=result)
    return result

@mcp.tool()
def jira_create_issue(project_key: str, summary: str, description: str, issue_type: str = "Task") -> str:
    """
    Create a new issue in a Jira project. Requires JIRA_URL, JIRA_USERNAME, and JIRA_API_TOKEN environment variables.
    
    Args:
        project_key: The key of the project (e.g., 'PROJ').
        summary: The title of the issue.
        description: The full description of the issue.
        issue_type: The type of issue (e.g., 'Task', 'Story', 'Bug'). Defaults to 'Task'.
        
    Returns:
        A JSON string of the newly created issue.
    """
    new_issue = create_issue(project_key, summary, description, issue_type)
    result = json.dumps(new_issue, indent=2)
    _append_request_log(tool_name="jira_create_issue", params={"project_key": project_key, "summary": summary, "issue_type": issue_type}, csv_file=None, response_preview=result)
    return result

@mcp.tool()
def jira_add_comment(issue_key: str, comment: str) -> str:
    """
    Add a comment to an existing Jira issue. Requires JIRA_URL, JIRA_USERNAME, and JIRA_API_TOKEN environment variables.
    
    Args:
        issue_key: The key of the issue to comment on (e.g., 'PROJ-123').
        comment: The text of the comment to add.
        
    Returns:
        A JSON string of the newly added comment.
    """
    new_comment = add_comment(issue_key, comment)
    result = json.dumps(new_comment, indent=2)
    _append_request_log(tool_name="jira_add_comment", params={"issue_key": issue_key}, csv_file=None, response_preview=result)
    return result