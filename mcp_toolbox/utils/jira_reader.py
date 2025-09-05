import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import re
import json

# --- Shared logging for Jira AI/MCP requests ---

LOGS_DIR = Path(__file__).resolve().parent.parent.parent / "docs"
LOG_MD = LOGS_DIR / "Jira-AI-Requests.md"
LOG_JSONL = LOGS_DIR / "jira_ai_requests.jsonl"


def _ensure_logs_dir_exists() -> None:
    try:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        # Best-effort only; do not block tool execution
        pass


def _categorize_tool(tool_name: str) -> str:
    mapping = {
        "summarize_jira_csv": "Overview",
        "get_jira_status_breakdown": "Statuses",
        "get_jira_project_breakdown": "Projects",
        "get_jira_priority_breakdown": "Priorities",
        "get_jira_assignee_workload": "Assignees & Workload",
        "filter_jira_by_assignee": "Assignees & Workload",
        "search_jira_issues": "Search",
        "list_jira_epics": "Epics",
        "get_epic_health": "Epics",
        "list_epic_children": "Epics",
        "audit_epic_gaps": "Epics",
        "get_epic_recent_progress": "Epics",
        "audit_jira_field_completeness": "Data Quality",
        "get_recent_progress": "Recent Activity",
        "jira_find_user": "Jira API Actions",
        "jira_get_issue": "Jira API Actions",
        "jira_create_issue": "Jira API Actions",
        "jira_add_comment": "Jira API Actions",
        "get_assignee_two_week_summary": "Recent Activity",
    }
    return mapping.get(tool_name, "Other")

# --- Shared normalization utilities ---

DONE_ALIASES = {"done", "closed", "resolved", "complete", "completed"}
IN_PROGRESS_ALIASES = {
    "in progress",
    "selected for development",
    "in review",
    "review",
    "in testing",
    "qa",
    "blocked",
}

PRIORITY_STARS_MAP = {
    "highest": 5,
    "critical": 5,
    "high": 4,
    "medium": 3,
    "low": 2,
    "lowest": 1,
}

def is_done_status(status_value: Any) -> bool:
    try:
        return str(status_value).strip().lower() in DONE_ALIASES
    except Exception:
        return False

def is_in_progress_status(status_value: Any) -> bool:
    try:
        return str(status_value).strip().lower() in IN_PROGRESS_ALIASES
    except Exception:
        return False

def priority_to_stars(priority_value: Any) -> str:
    try:
        stars = PRIORITY_STARS_MAP.get(str(priority_value).strip().lower(), 0)
        return "⭐" * stars if stars else ""
    except Exception:
        return ""


def _append_request_log(
    *,
    tool_name: str,
    params: Dict[str, Any],
    csv_file: Optional[str],
    response_preview: Optional[str],
) -> None:
    """Best-effort append to machine- and human-readable logs.

    - Writes JSONL with a structured record
    - Updates Markdown with a date section and a bullet entry
    """
    _ensure_logs_dir_exists()
    category = _categorize_tool(tool_name)
    timestamp_utc = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    record = {
        "timestamp": timestamp_utc,
        "category": category,
        "tool": tool_name,
        "params": params,
        "csv_file": csv_file,
        "response_preview": (response_preview or "").splitlines()[0:4],
    }

    # JSONL log
    try:
        with LOG_JSONL.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        pass

    # Markdown log
    try:
        date_heading = datetime.utcnow().strftime("%Y-%m-%d")
        entry_lines = [
            f"- {timestamp_utc} | {category} | {tool_name} | csv={csv_file or ''} | params={json.dumps(params, ensure_ascii=False)}"
        ]
        if response_preview:
            preview = "\\n  " + "\\n  ".join((response_preview or "").splitlines()[0:3])
            entry_lines.append(f"  {preview}")

        if LOG_MD.exists():
            content = LOG_MD.read_text(encoding="utf-8")
        else:
            content = "# Jira AI/MCP Requests\n\n"

        # Insert under today's section, create if missing
        section_header = f"## {date_heading}"
        if section_header in content:
            new_content = content + "\n" + "\n".join(entry_lines) + "\n"
        else:
            new_content = content + f"{section_header}\n\n" + "\n".join(entry_lines) + "\n"
        LOG_MD.write_text(new_content, encoding="utf-8")
    except Exception:
        pass

# Base directory where our data lives - updated for new structure
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "docs"

def _resolve_csv_path(filename: Optional[str]) -> Path:
    """
    Resolve the Jira CSV file path.

    If filename is provided, use it inside DATA_DIR. Otherwise, pick the most
    recently modified file matching "Jira *.csv" in the DATA_DIR.
    """
    if filename:
        return DATA_DIR / filename
    # Support a broad set of Jira CSV export filename patterns
    patterns = ["*Jira*.csv", "Jira *.csv"]
    candidates = []
    for pat in patterns:
        candidates.extend(DATA_DIR.glob(pat))
    candidates = sorted(set(candidates), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        raise FileNotFoundError("No Jira CSV files found in docs directory")
    return candidates[0]

def _load_jira_df(filename: Optional[str]) -> Tuple[pd.DataFrame, Path]:
    file_path = _resolve_csv_path(filename)
    df = pd.read_csv(file_path)
    return df, file_path

def _find_column(df: pd.DataFrame, possible_names: List[str]) -> Optional[str]:
    """Find the first matching column name (case-sensitive match against provided names)."""
    for name in possible_names:
        if name in df.columns:
            return name
    # Fallback: case-insensitive search
    lower_to_actual = {c.lower(): c for c in df.columns}
    for name in possible_names:
        if name.lower() in lower_to_actual:
            return lower_to_actual[name.lower()]
    return None

def _children_of_epic(df: pd.DataFrame, epic_key: str) -> pd.DataFrame:
    """Return subset of rows that are children of epic_key using multiple heuristics."""
    epic_link_col = _find_column(df, ["Epic Link", "Custom field (Epic Link)"])
    parent_col = _find_column(df, ["Parent", "Parent key", "Parent Key"])  # varies per export
    parent_link_col = _find_column(df, ["Parent Link"])  # sometimes a URL

    masks = []
    if epic_link_col is not None:
        masks.append(df[epic_link_col].astype(str) == str(epic_key))
    if parent_col is not None:
        series = df[parent_col].astype(str)
        masks.append(series == str(epic_key))
        masks.append(series.str.contains(re.escape(str(epic_key)), na=False))
    if parent_link_col is not None:
        pl = df[parent_link_col].astype(str)
        masks.append(pl.str.contains(re.escape(str(epic_key)), na=False))
        # Extract keys like ABC-123 from URLs/strings and compare
        pattern = re.compile(r"[A-Z][A-Z0-9]+-\d+")
        extracted = pl.apply(lambda s: (pattern.search(s) or [None])[0] if isinstance(s, str) else None)
        masks.append(extracted.astype(str) == str(epic_key))

    if not masks:
        return df.iloc[0:0]  # empty
    combined = masks[0]
    for m in masks[1:]:
        combined = combined | m
    return df[combined]

def read_jira_csv_summary(filename: Optional[str] = None) -> str:
    """
    Read the Jira CSV file and return a basic summary.
    Args:
        filename: Name of the CSV file in the /docs directory
    Returns:
        A string describing the file's basic statistics.
    """
    df, file_path = _load_jira_df(filename)
    
    total_issues = len(df)
    total_columns = len(df.columns)
    unique_projects = df['Project key'].nunique() if 'Project key' in df.columns else 0
    unique_statuses = df['Status'].nunique() if 'Status' in df.columns else 0
    
    return f"""Jira CSV Summary:
- Total Issues: {total_issues:,}
- Total Columns: {total_columns}
- Unique Projects: {unique_projects}
- Unique Statuses: {unique_statuses}
- File: {file_path.name}"""

def get_status_distribution(filename: Optional[str] = None) -> str:
    """
    Get the distribution of issue statuses.
    Args:
        filename: Name of the CSV file in the /docs directory
    Returns:
        A string showing the count of issues by status.
    """
    df, _ = _load_jira_df(filename)
    
    if 'Status' not in df.columns:
        return "Status column not found in the data"
    
    status_counts = df['Status'].value_counts()
    result = "Issue Status Distribution:\n"
    for status, count in status_counts.head(10).items():
        percentage = (count / len(df)) * 100
        result += f"- {status}: {count:,} ({percentage:.1f}%)\n"
    
    if len(status_counts) > 10:
        result += f"... and {len(status_counts) - 10} more statuses"
    
    return result

def get_project_distribution(filename: Optional[str] = None) -> str:
    """
    Get the distribution of issues by project.
    Args:
        filename: Name of the CSV file in the /docs directory
    Returns:
        A string showing the count of issues by project.
    """
    df, _ = _load_jira_df(filename)
    
    if 'Project key' not in df.columns:
        return "Project key column not found in the data"
    
    project_counts = df['Project key'].value_counts()
    result = "Issue Distribution by Project:\n"
    for project, count in project_counts.head(10).items():
        percentage = (count / len(df)) * 100
        result += f"- {project}: {count:,} ({percentage:.1f}%)\n"
    
    if len(project_counts) > 10:
        result += f"... and {len(project_counts) - 10} more projects"
    
    return result

def get_priority_distribution(filename: Optional[str] = None) -> str:
    """
    Get the distribution of issues by priority.
    Args:
        filename: Name of the CSV file in the /docs directory
    Returns:
        A string showing the count of issues by priority.
    """
    df, _ = _load_jira_df(filename)
    
    if 'Priority' not in df.columns:
        return "Priority column not found in the data"
    
    priority_counts = df['Priority'].value_counts()
    result = "Issue Distribution by Priority:\n"
    for priority, count in priority_counts.items():
        percentage = (count / len(df)) * 100
        result += f"- {priority}: {count:,} ({percentage:.1f}%)\n"
    
    return result

def get_assignee_workload(top_n: int = 10, filename: Optional[str] = None) -> str:
    """
    Get the workload distribution by assignee.
    Args:
        filename: Name of the CSV file in the /docs directory
        top_n: Number of top assignees to show
    Returns:
        A string showing the count of assigned issues by person.
    """
    df, _ = _load_jira_df(filename)
    
    if 'Assignee' not in df.columns:
        return "Assignee column not found in the data"
    
    # Filter out empty assignees
    assigned_df = df[df['Assignee'].notna() & (df['Assignee'] != '')]
    assignee_counts = assigned_df['Assignee'].value_counts()
    
    total_assigned = len(assigned_df)
    total_unassigned = len(df) - total_assigned
    
    result = f"Assignee Workload (Top {top_n}):\n"
    result += f"Total Assigned Issues: {total_assigned:,}\n"
    result += f"Total Unassigned Issues: {total_unassigned:,}\n\n"
    
    for assignee, count in assignee_counts.head(top_n).items():
        percentage = (count / total_assigned) * 100
        result += f"- {assignee}: {count:,} ({percentage:.1f}%)\n"
    
    return result

def search_issues_by_text(search_term: str, filename: Optional[str] = None, top_n: int = 10, page: int = 1) -> str:
    """
    Search for issues containing specific text in Summary or Description.
    Args:
        search_term: Text to search for
        filename: Name of the CSV file in the /docs directory
    Returns:
        A string showing matching issues.
    """
    df, _ = _load_jira_df(filename)
    
    # Search in Summary and Description columns
    search_columns = []
    if 'Summary' in df.columns:
        search_columns.append('Summary')
    if 'Description' in df.columns:
        search_columns.append('Description')
    
    if not search_columns:
        return "No searchable text columns found (Summary, Description)"
    
    # Create a mask for rows containing the search term
    mask = pd.Series([False] * len(df))
    for col in search_columns:
        mask |= df[col].astype(str).str.contains(search_term, case=False, na=False)
    
    matching_issues = df[mask]
    
    if len(matching_issues) == 0:
        return f"No issues found containing '{search_term}'"
    
    total_matches = len(matching_issues)
    result = f"Found {total_matches} issues containing '{search_term}':\n\n"

    # Pagination
    if top_n <= 0:
        top_n = 10
    if page <= 0:
        page = 1
    start = (page - 1) * top_n
    end = start + top_n
    page_df = matching_issues.iloc[start:end]

    for idx, (_, issue) in enumerate(page_df.iterrows(), start=1 + start):
        issue_key = issue.get('Issue key', 'N/A')
        summary = issue.get('Summary', 'N/A')
        status = issue.get('Status', 'N/A')
        assignee = issue.get('Assignee', 'Unassigned')
        
        result += f"{idx}. {issue_key} - {summary}\n"
        result += f"   Status: {status} | Assignee: {assignee}\n\n"

    remaining = total_matches - end
    if remaining > 0:
        result += f"... and {remaining} more matches (page {page}, page size {top_n})"
    
    return result 

def filter_issues_by_assignee(
    assignee_query: str,
    filename: Optional[str] = None,
    top_n: int = 100,
    include_unassigned: bool = False,
    case_insensitive: bool = True,
 ) -> str:
    """
    Filter issues by Assignee value using substring matching.

    Args:
        assignee_query: Text to match within the Assignee field
        filename: Optional CSV filename in the /docs directory
        top_n: Maximum number of rows to display
        include_unassigned: If True, keep rows with empty Assignee values
        case_insensitive: If True, perform case-insensitive matching

    Returns:
        A human-readable list of matching issues with key details
    """
    df, file_path = _load_jira_df(filename)

    assignee_col = _find_column(df, ["Assignee"]) or "Assignee"
    key_col = _find_column(df, ["Issue key", "Key"]) or "Issue key"
    summary_col = _find_column(df, ["Summary"]) or "Summary"
    status_col = _find_column(df, ["Status"]) or "Status"

    if assignee_col not in df.columns:
        return "Assignee column not found in the data"

    # Prepare series and optional unassigned filtering
    assignee_series = df[assignee_col].astype(str).fillna("")
    working_df = df.copy()
    if not include_unassigned:
        working_df = working_df[assignee_series.str.strip() != ""]
        assignee_series = working_df[assignee_col].astype(str).fillna("")

    # Build match mask
    if not assignee_query:
        return "Assignee query is empty"
    mask = assignee_series.str.contains(
        assignee_query,
        case=not case_insensitive,
        na=False,
    )
    matches = working_df[mask]

    if len(matches) == 0:
        return f"No issues found for assignee matching '{assignee_query}'"

    lines: List[str] = [
        f"Assignee Filter: '{assignee_query}' — {len(matches)} match(es) (file: {file_path.name})",
        "",
    ]
    for _, row in matches.head(top_n).iterrows():
        lines.append(
            f"- {row.get(key_col, 'N/A')}: {row.get(summary_col, 'N/A')} | {row.get(status_col, 'N/A')} | Assignee: {row.get(assignee_col, 'Unassigned')}"
        )
    if len(matches) > top_n:
        lines.append(f"... and {len(matches) - top_n} more issues")

    return "\n".join(lines)

# --- Epic and Field Audit Utilities ---

def list_epics(filename: Optional[str] = None, top_n: int = 20) -> str:
    """
    List epics with child counts and completion percentage.
    """
    df, file_path = _load_jira_df(filename)

    key_col = _find_column(df, ["Issue key", "Key"])
    type_col = _find_column(df, ["Issue Type", "Type"])
    status_col = _find_column(df, ["Status"]) 
    epic_link_col = _find_column(df, ["Epic Link", "Custom field (Epic Link)"])  # standard Jira CSV header name
    parent_col = _find_column(df, ["Parent", "Parent key", "Parent Key"])  # possible alternative
    parent_link_col = _find_column(df, ["Parent Link"])  # sometimes URL

    if not key_col:
        return "Issue key column not found"

    # Identify epics
    epics_df = pd.DataFrame()
    if type_col is not None:
        epics_df = df[df[type_col].astype(str).str.lower() == "epic"].copy()
    # Fallbacks: treat any keys referenced by Epic Link, Parent, or Parent Link as epics
    candidate_keys: set[str] = set()
    if epic_link_col is not None:
        candidate_keys.update(df[epic_link_col].dropna().astype(str).tolist())
    if parent_col is not None:
        candidate_keys.update(df[parent_col].dropna().astype(str).tolist())
    if parent_link_col is not None:
        pattern = re.compile(r"[A-Z][A-Z0-9]+-\d+")
        for s in df[parent_link_col].dropna().astype(str).tolist():
            m = pattern.search(s)
            if m:
                candidate_keys.add(m.group(0))
    if epics_df.empty and candidate_keys:
        epics_df = df[df[key_col].astype(str).isin(candidate_keys)].copy()

    if epics_df.empty:
        return "No epics found in CSV"

    # Compute children and completion
    lines = [f"Epics Overview (file: {file_path.name})"]
    lines.append("")

    for _, epic in epics_df.head(top_n).iterrows():
        epic_key = str(epic.get(key_col, "N/A"))
        epic_summary = str(epic.get("Summary", "N/A")) if "Summary" in df.columns else "N/A"
        children = _children_of_epic(df, epic_key)
        total_children = len(children)
        done_children = 0
        if total_children > 0 and status_col is not None:
            done_children = children[status_col].astype(str).str.lower().isin(
                ["done", "closed", "resolved", "complete", "completed"]
            ).sum()
        completion_pct = (done_children / total_children * 100) if total_children > 0 else 0.0
        lines.append(f"- {epic_key}: {epic_summary} | Items: {total_children} | Done: {done_children} ({completion_pct:.1f}%)")

    if len(epics_df) > top_n:
        lines.append(f"... and {len(epics_df) - top_n} more epics")

    return "\n".join(lines)

def epic_health_report(epic_key: str, filename: Optional[str] = None) -> str:
    """Detailed epic health with child breakdown and recent updates."""
    df, file_path = _load_jira_df(filename)

    key_col = _find_column(df, ["Issue key", "Key"]) or "Issue key"
    status_col = _find_column(df, ["Status"]) or "Status"
    summary_col = _find_column(df, ["Summary"]) or "Summary"
    epic_link_col = _find_column(df, ["Epic Link", "Custom field (Epic Link)"])  # may be None
    updated_col = _find_column(df, ["Updated"])  # may be None

    # Find epic row
    epic_row = df[df[key_col].astype(str) == str(epic_key)]
    if epic_row.empty:
        return f"Epic {epic_key} not found"
    epic_summary = str(epic_row.iloc[0].get(summary_col, "N/A"))
    epic_status = str(epic_row.iloc[0].get(status_col, "N/A"))

    # Children
    children = _children_of_epic(df, str(epic_key)).copy()
    total_children = len(children)
    done_mask = children[status_col].astype(str).str.lower().isin(["done", "closed", "resolved", "complete", "completed"]) if total_children and status_col in children.columns else pd.Series([], dtype=bool)
    done_children = int(done_mask.sum()) if total_children else 0
    completion_pct = (done_children / total_children * 100) if total_children else 0.0

    lines = [f"Epic Health Report: {epic_key}", f"Summary: {epic_summary}", f"Status: {epic_status}", f"Children: {total_children} | Done: {done_children} ({completion_pct:.1f}%)", ""]

    # Recent updates among children (last 14 days)
    if total_children and updated_col is not None:
        children["__updated_dt"] = pd.to_datetime(children[updated_col], errors="coerce")
        cutoff = datetime.utcnow() - timedelta(days=14)
        recent = children[children["__updated_dt"] >= cutoff]
        lines.append(f"Recent updates (last 14d): {len(recent)}")
        for _, row in recent.head(10).iterrows():
            lines.append(f"- {row.get(key_col, 'N/A')}: {row.get(summary_col, 'N/A')} | {row.get(status_col, 'N/A')} | Updated: {row.get(updated_col, 'N/A')}")
        if len(recent) > 10:
            lines.append(f"... and {len(recent) - 10} more recently updated items")

    return "\n".join(lines)

def audit_field_completeness(filename: Optional[str] = None) -> str:
    """Identify fields with the highest missing rates across issues."""
    df, file_path = _load_jira_df(filename)

    # Map canonical field names to possible column headers in Jira exports
    field_map: Dict[str, List[str]] = {
        "Summary": ["Summary"],
        "Description": ["Description"],
        "Assignee": ["Assignee"],
        "Priority": ["Priority"],
        "Labels": ["Labels"],
        "Fix versions": ["Fix versions", "Fix Version/s"],
        "Sprint": ["Sprint"],
        "Story Points": ["Story Points", "Story point estimate"],
        "Due date": ["Due date", "Due Date"],
        "Components": ["Components"],
    }

    results: List[Tuple[str, float, int]] = []  # (field, missing_pct, missing_count)
    total = len(df)
    for canonical, candidates in field_map.items():
        col = _find_column(df, candidates)
        if not col:
            continue
        missing_mask = df[col].isna() | (df[col] == "")
        missing_count = int(missing_mask.sum())
        missing_pct = (missing_count / total * 100) if total else 0.0
        results.append((canonical, missing_pct, missing_count))

    if not results:
        return "No recognizable fields found to audit"

    results.sort(key=lambda t: t[1], reverse=True)
    lines = [f"Field Completeness Audit (file: {file_path.name})", ""]
    for field, missing_pct, missing_count in results:
        lines.append(f"- {field}: missing {missing_count:,} of {total:,} ({missing_pct:.1f}%)")
    return "\n".join(lines)

def recent_progress(days: int = 14, filename: Optional[str] = None, top_n: int = 50) -> str:
    """Show issues updated in the last N days, grouped by epic when possible."""
    df, file_path = _load_jira_df(filename)

    key_col = _find_column(df, ["Issue key", "Key"]) or "Issue key"
    summary_col = _find_column(df, ["Summary"]) or "Summary"
    status_col = _find_column(df, ["Status"]) or "Status"
    updated_col = _find_column(df, ["Updated"])  # may be None
    epic_link_col = _find_column(df, ["Epic Link"])  # may be None

    if not updated_col:
        return "Updated column not found; cannot determine recent progress"

    df["__updated_dt"] = pd.to_datetime(df[updated_col], errors="coerce")
    cutoff = datetime.utcnow() - timedelta(days=days)
    recent = df[df["__updated_dt"] >= cutoff].copy()

    lines = [f"Recent Progress (last {days} days) - file: {file_path.name}", ""]
    if epic_link_col is not None:
        # Group by epic
        for epic_key, group in recent.groupby(recent[epic_link_col].astype(str)):
            if pd.isna(epic_key) or epic_key == "nan":
                continue
            lines.append(f"Epic {epic_key}: {len(group)} updates")
            for _, row in group.head(5).iterrows():
                lines.append(f"  - {row.get(key_col, 'N/A')}: {row.get(summary_col, 'N/A')} | {row.get(status_col, 'N/A')} | Updated: {row.get(updated_col, 'N/A')}")
            if len(group) > 5:
                lines.append(f"  ... and {len(group) - 5} more updates for this epic")
            lines.append("")
    else:
        # List top recent items
        for _, row in recent.head(top_n).iterrows():
            lines.append(f"- {row.get(key_col, 'N/A')}: {row.get(summary_col, 'N/A')} | {row.get(status_col, 'N/A')} | Updated: {row.get(updated_col, 'N/A')}")

    if len(recent) > top_n and epic_link_col is None:
        lines.append(f"... and {len(recent) - top_n} more recently updated issues")

    return "\n".join(lines)

def get_issue_details(issue_key: str, filename: Optional[str] = None) -> str:
    """Return all available fields for a single issue as key: value lines."""
    df, file_path = _load_jira_df(filename)
    key_col = _find_column(df, ["Issue key", "Key"]) or "Issue key"
    matches = df[df[key_col].astype(str) == str(issue_key)]
    if matches.empty:
        return f"Issue {issue_key} not found in {file_path.name}"
    if len(matches) > 1:
        return f"Multiple rows found for {issue_key} (expected 1)"
    row = matches.iloc[0]
    lines = [f"Issue Details: {issue_key} (file: {file_path.name})", ""]
    for col in df.columns:
        val = row.get(col)
        # Make lists/json readable
        try:
            if isinstance(val, float) and pd.isna(val):
                val_str = ""
            else:
                val_str = str(val)
        except Exception:
            val_str = str(val)
        lines.append(f"- {col}: {val_str}")
    return "\n".join(lines)

def list_epic_items(epic_key: str, top_n: int = 100, filename: Optional[str] = None) -> str:
    """List items under an epic (key, summary, status, assignee, priority, updated)."""
    df, file_path = _load_jira_df(filename)
    key_col = _find_column(df, ["Issue key", "Key"]) or "Issue key"
    # Use robust child detection
    summary_col = _find_column(df, ["Summary"]) or "Summary"
    status_col = _find_column(df, ["Status"]) or "Status"
    assignee_col = _find_column(df, ["Assignee"]) or "Assignee"
    priority_col = _find_column(df, ["Priority"]) or "Priority"
    updated_col = _find_column(df, ["Updated"]) or "Updated"

    children = _children_of_epic(df, str(epic_key)).copy()
    if children.empty:
        return f"No items found under epic {epic_key}"
    lines = [f"Epic Items for {epic_key} (showing up to {top_n})", ""]
    for _, row in children.head(top_n).iterrows():
        lines.append(
            f"- {row.get(key_col, 'N/A')}: {row.get(summary_col, 'N/A')} | {row.get(status_col, 'N/A')} | "
            f"Assignee: {row.get(assignee_col, 'Unassigned')} | Priority: {row.get(priority_col, 'N/A')} | "
            f"Updated: {row.get(updated_col, 'N/A')}"
        )
    if len(children) > top_n:
        lines.append(f"... and {len(children) - top_n} more items")
    return "\n".join(lines)

def audit_epic_field_gaps(epic_key: str, filename: Optional[str] = None) -> str:
    """Audit missing fields within a single epic's children to surface gaps."""
    df, file_path = _load_jira_df(filename)
    children = _children_of_epic(df, str(epic_key)).copy()
    if children.empty:
        return f"No items found under epic {epic_key}"

    field_map: Dict[str, List[str]] = {
        "Summary": ["Summary"],
        "Description": ["Description"],
        "Assignee": ["Assignee"],
        "Priority": ["Priority"],
        "Labels": ["Labels"],
        "Fix versions": ["Fix versions", "Fix Version/s"],
        "Sprint": ["Sprint"],
        "Story Points": ["Story Points", "Story point estimate"],
        "Due date": ["Due date", "Due Date"],
        "Components": ["Components"],
    }

    results: List[Tuple[str, float, int]] = []
    total = len(children)
    for canonical, candidates in field_map.items():
        col = _find_column(children, candidates)
        if not col:
            continue
        missing_mask = children[col].isna() | (children[col] == "")
        missing_count = int(missing_mask.sum())
        missing_pct = (missing_count / total * 100) if total else 0.0
        results.append((canonical, missing_pct, missing_count))

    if not results:
        return f"No recognizable fields found to audit for epic {epic_key}"
    results.sort(key=lambda t: t[1], reverse=True)
    lines = [f"Epic Field Gaps for {epic_key} (items: {total})", ""]
    for field, missing_pct, missing_count in results:
        lines.append(f"- {field}: missing {missing_count:,} of {total:,} ({missing_pct:.1f}%)")
    return "\n".join(lines)

def epic_recent_progress(epic_key: str, days: int = 14, filename: Optional[str] = None, top_n: int = 50) -> str:
    """Show most recently updated items within a single epic."""
    df, file_path = _load_jira_df(filename)
    epic_link_col = _find_column(df, ["Epic Link", "Custom field (Epic Link)"])
    updated_col = _find_column(df, ["Updated"])  # may be None
    key_col = _find_column(df, ["Issue key", "Key"]) or "Issue key"
    summary_col = _find_column(df, ["Summary"]) or "Summary"
    status_col = _find_column(df, ["Status"]) or "Status"
    if not updated_col:
        return "Updated column not found; cannot determine recent progress"
    children = _children_of_epic(df, str(epic_key)).copy()
    if children.empty:
        return f"No items found under epic {epic_key}"

    children["__updated_dt"] = pd.to_datetime(children[updated_col], errors="coerce")
    cutoff = datetime.utcnow() - timedelta(days=days)
    recent = children[children["__updated_dt"] >= cutoff]
    lines = [f"Epic Recent Progress for {epic_key} (last {days} days)", ""]
    for _, row in recent.head(top_n).iterrows():
        lines.append(f"- {row.get(key_col, 'N/A')}: {row.get(summary_col, 'N/A')} | {row.get(status_col, 'N/A')} | Updated: {row.get(updated_col, 'N/A')}")
    if len(recent) > top_n:
        lines.append(f"... and {len(recent) - top_n} more updates")
    return "\n".join(lines)

def get_overview_bundle(filename: Optional[str] = None, top_n_assignees: int = 5, top_n_statuses: int = 5) -> str:
    """Return a compact overview bundle: status breakdown, priority breakdown, and top assignees.

    This reduces round-trips for common overviews.
    """
    df, file_path = _load_jira_df(filename)

    lines: List[str] = [f"Overview Bundle (file: {file_path.name})", ""]

    # Status breakdown
    status_col = _find_column(df, ["Status"]) or "Status"
    if status_col in df.columns:
        status_counts = df[status_col].value_counts()
        lines.append("Statuses:")
        for status, count in status_counts.head(top_n_statuses).items():
            pct = (count / len(df) * 100) if len(df) else 0
            lines.append(f"- {status}: {count:,} ({pct:.1f}%)")
        if len(status_counts) > top_n_statuses:
            lines.append(f"... and {len(status_counts) - top_n_statuses} more statuses")
        lines.append("")

    # Priority breakdown
    priority_col = _find_column(df, ["Priority"]) or "Priority"
    if priority_col in df.columns:
        pr_counts = df[priority_col].value_counts()
        lines.append("Priorities:")
        for pr, count in pr_counts.items():
            pct = (count / len(df) * 100) if len(df) else 0
            lines.append(f"- {pr}: {count:,} ({pct:.1f}%)")
        lines.append("")

    # Top assignees
    assignee_col = _find_column(df, ["Assignee"]) or "Assignee"
    if assignee_col in df.columns:
        assigned_df = df[df[assignee_col].notna() & (df[assignee_col] != "")]
        assignee_counts = assigned_df[assignee_col].value_counts()
        total_assigned = len(assigned_df)
        total_unassigned = len(df) - total_assigned
        lines.append(f"Top Assignees (Top {top_n_assignees}):")
        lines.append(f"Total Assigned: {total_assigned:,} | Unassigned: {total_unassigned:,}")
        for name, count in assignee_counts.head(top_n_assignees).items():
            pct = (count / total_assigned * 100) if total_assigned else 0
            lines.append(f"- {name}: {count:,} ({pct:.1f}%)")

    return "\n".join(lines)

def get_assignee_two_week_summary(
    assignee_query: str,
    days: int = 14,
    filename: Optional[str] = None,
    top_n_per_section: int = 5,
) -> str:
    """Generate a 2-week activity summary for a single assignee (substring match).

    Sections:
    - Critical - Immediate Attention (stale in-progress items, last update >= 6 days)
    - Completed (done/resolved within window)
    - Active with Recent Progress (updated within window, not done)
    - Key Alerts (counts)
    """
    df, file_path = _load_jira_df(filename)

    key_col = _find_column(df, ["Issue key", "Key"]) or "Issue key"
    summary_col = _find_column(df, ["Summary"]) or "Summary"
    status_col = _find_column(df, ["Status"]) or "Status"
    assignee_col = _find_column(df, ["Assignee"]) or "Assignee"
    updated_col = _find_column(df, ["Updated"]) or None
    resolution_date_col = _find_column(df, ["Resolution date", "Resolved", "Resolution Date"]) or None
    issue_type_col = _find_column(df, ["Issue Type", "Type"]) or None

    if assignee_col not in df.columns:
        return "Assignee column not found in the data"

    if updated_col is None:
        return "Updated column not found; cannot build a two-week summary"

    # Filter by assignee substring (case-insensitive)
    assignee_series = df[assignee_col].astype(str).fillna("")
    mask = assignee_series.str.contains(assignee_query, case=False, na=False)
    assignee_df = df[mask].copy()
    if assignee_df.empty:
        return f"No issues found for assignee matching '{assignee_query}'"

    # Time window
    now_utc = datetime.utcnow()
    cutoff = now_utc - timedelta(days=days)
    assignee_df["__updated_dt"] = pd.to_datetime(assignee_df[updated_col], errors="coerce")

    # Done status set
    status_lower = assignee_df[status_col].astype(str).str.lower()

    # Completed within window: If resolution date available, use it; else done-status updated recently
    completed_mask = pd.Series([False] * len(assignee_df))
    if resolution_date_col and resolution_date_col in assignee_df.columns:
        resolved_dt = pd.to_datetime(assignee_df[resolution_date_col], errors="coerce")
        completed_mask = resolved_dt >= cutoff
    else:
        completed_mask = (status_lower.apply(is_done_status)) & (assignee_df["__updated_dt"] >= cutoff)

    completed_df = assignee_df[completed_mask].copy()

    # Active with recent progress: updated in window and not done
    active_recent_mask = (assignee_df["__updated_dt"] >= cutoff) & (~status_lower.apply(is_done_status))
    active_recent_df = assignee_df[active_recent_mask].copy()

    # Critical stale: in-progress-ish statuses and last update >= 6 days ago
    last_update_age = now_utc - assignee_df["__updated_dt"]
    stale_mask = status_lower.apply(is_in_progress_status) & (last_update_age.dt.days >= 6)
    critical_df = assignee_df[stale_mask].copy().sort_values("__updated_dt", ascending=True)

    # Active issues with recent activity count
    recent_activity_df = assignee_df[assignee_df["__updated_dt"] >= cutoff]
    active_issues_count = int(recent_activity_df[key_col].nunique())

    # Format
    period_str = f"{(now_utc - timedelta(days=days)).strftime('%b %d, %Y')} - {now_utc.strftime('%b %d, %Y')}"

    lines: List[str] = []
    # Header line with name if exact match exists
    display_name = assignee_query
    # Try to pick a canonical assignee name from data
    unique_assignees = assignee_df[assignee_col].dropna().astype(str).unique().tolist()
    if unique_assignees:
        display_name = unique_assignees[0]

    lines.append(f"# {display_name} — 2-Week Activity Summary")
    lines.append("")
    lines.append(f"**Period:** {period_str} | **Active Issues:** {active_issues_count} with recent activity")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Critical - Immediate Attention
    lines.append("## 🔥 **CRITICAL - IMMEDIATE ATTENTION**")
    if critical_df.empty:
        lines.append("- None identified")
    else:
        for _, row in critical_df.head(top_n_per_section).iterrows():
            # Impact from Priority → stars
            priority_val = str(row.get(_find_column(df, ["Priority"]) or "Priority", ""))
            stars = priority_to_stars(priority_val)
            owner_display = str(row.get(assignee_col, display_name) or display_name)
            stale_days = max((now_utc - pd.to_datetime(row.get(updated_col))).days if pd.notna(row.get(updated_col)) else 0, 0)
            lines.append(
                f"- {row.get(key_col, 'N/A')} — {row.get(summary_col, 'N/A')} | **In Progress** | **STALE {stale_days}+ days**\n"
                f"  **Owner:** {owner_display}{f' | **Impact:** {stars}' if stars else ''}"
            )
    lines.append("")
    lines.append("---")
    lines.append("")

    # Completed
    lines.append("## ✅ **COMPLETED**")
    if completed_df.empty:
        lines.append("- No completions in this period")
    else:
        show_df = completed_df.sort_values("__updated_dt", ascending=False).head(top_n_per_section)
        for _, row in show_df.iterrows():
            priority_val = str(row.get(_find_column(df, ["Priority"]) or "Priority", ""))
            stars = priority_to_stars(priority_val)
            owner_display = str(row.get(assignee_col, display_name) or display_name)
            lines.append(
                f"- {row.get(key_col, 'N/A')} — {row.get(summary_col, 'N/A')} | **Done**\n"
                f"  **Owner:** {owner_display}{f' | **Impact:** {stars}' if stars else ''}  \n"
                f"  Updated: {row.get(updated_col, 'N/A')}"
            )
    lines.append("")
    lines.append("---")
    lines.append("")

    # Active with recent progress
    lines.append("## 🔄 **ACTIVE WITH RECENT PROGRESS**")
    if active_recent_df.empty:
        lines.append("- No active updates in this period")
    else:
        show_df = active_recent_df.sort_values("__updated_dt", ascending=False).head(top_n_per_section)
        for _, row in show_df.iterrows():
            priority_val = str(row.get(_find_column(df, ["Priority"]) or "Priority", ""))
            stars = priority_to_stars(priority_val)
            owner_display = str(row.get(assignee_col, display_name) or display_name)
            lines.append(
                f"- {row.get(key_col, 'N/A')} — {row.get(summary_col, 'N/A')} | {row.get(status_col, 'N/A')}\n"
                f"  **Owner:** {owner_display}{f' | **Impact:** {stars}' if stars else ''}  \n"
                f"  Updated: {row.get(updated_col, 'N/A')}"
            )
    lines.append("")
    lines.append("---")
    lines.append("")

    # Key alerts
    total_stale = int(critical_df[key_col].nunique())
    total_completed = int(completed_df[key_col].nunique())
    total_active = int(active_recent_df[key_col].nunique())
    lines.append("## ⚠️ **KEY ALERTS**")
    lines.append(f"- Stale in-progress items: {total_stale}")
    lines.append(f"- Completed in period: {total_completed}")
    lines.append(f"- Active items with updates: {total_active}")
    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append(f"Report generated: {now_utc.strftime('%Y-%m-%d')} | Data source: {file_path.name}")

    return "\n".join(lines)