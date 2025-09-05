import pandas as pd
from mcp.server.fastmcp import FastMCP
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json

mcp = FastMCP("Jira CSV Reader")

# In-memory storage for the DataFrame
jira_df = None

def _find_latest_jira_csv() -> str:
    """Find the most recent Jira CSV file in the jira_exports folder."""
    jira_exports_dir = os.path.join("docs", "jira_exports")
    
    if not os.path.exists(jira_exports_dir):
        raise FileNotFoundError(f"Jira exports directory not found: {jira_exports_dir}")
    
    # Find all CSV files in the directory
    csv_files = []
    for filename in os.listdir(jira_exports_dir):
        if filename.endswith('.csv') and filename.startswith('Jira'):
            filepath = os.path.join(jira_exports_dir, filename)
            # Get file modification time
            mtime = os.path.getmtime(filepath)
            csv_files.append((filepath, mtime, filename))
    
    if not csv_files:
        raise FileNotFoundError(f"No Jira CSV files found in {jira_exports_dir}")
    
    # Sort by modification time (newest first) and return the most recent
    csv_files.sort(key=lambda x: x[1], reverse=True)
    latest_file = csv_files[0][0]
    latest_filename = csv_files[0][2]
    
    return latest_file, latest_filename

@mcp.tool()
def list_available_jira_csvs() -> str:
    """List all available Jira CSV files in the exports directory with their details."""
    jira_exports_dir = os.path.join("docs", "jira_exports")
    
    if not os.path.exists(jira_exports_dir):
        return f"Jira exports directory not found: {jira_exports_dir}"
    
    # Find all CSV files in the directory
    csv_files = []
    for filename in os.listdir(jira_exports_dir):
        if filename.endswith('.csv') and filename.startswith('Jira'):
            filepath = os.path.join(jira_exports_dir, filename)
            # Get file info
            mtime = os.path.getmtime(filepath)
            size = os.path.getsize(filepath)
            mod_date = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
            csv_files.append((filename, mod_date, size))
    
    if not csv_files:
        return f"No Jira CSV files found in {jira_exports_dir}"
    
    # Sort by modification time (newest first)
    csv_files.sort(key=lambda x: x[1], reverse=True)
    
    result = "AVAILABLE JIRA CSV FILES\n========================\n\n"
    for i, (filename, mod_date, size) in enumerate(csv_files):
        size_mb = size / (1024 * 1024)
        status = " (LATEST)" if i == 0 else ""
        result += f"{filename}{status}\n"
        result += f"  Modified: {mod_date}\n"
        result += f"  Size: {size_mb:.1f} MB\n\n"
    
    result += f"Note: load_jira_csv() without parameters will automatically load the latest file."
    return result

@mcp.tool()
def load_jira_csv(filepath: str = None) -> str:
    """Loads a Jira CSV file into memory, using a Parquet cache for speed.
    
    Args:
        filepath: Optional path to specific CSV file. If not provided, will automatically
                 find and load the most recent Jira CSV file from docs/jira_exports/
    """
    global jira_df
    
    try:
        # If no filepath provided, find the latest CSV file automatically
        if filepath is None:
            filepath, filename = _find_latest_jira_csv()
            auto_selected_msg = f"Auto-selected most recent file: {filename}"
        else:
            # Handle relative paths - check if file exists, if not try in jira_exports
            if not os.path.exists(filepath):
                # Try in jira_exports directory
                jira_exports_path = os.path.join("docs", "jira_exports", filepath)
                if os.path.exists(jira_exports_path):
                    filepath = jira_exports_path
                else:
                    return f"File not found: {filepath}. Checked current directory and docs/jira_exports/"
            auto_selected_msg = f"Using specified file: {os.path.basename(filepath)}"
        
        parquet_path = filepath.replace('.csv', '.parquet')
        
        # Check if a valid Parquet cache exists
        if os.path.exists(parquet_path) and os.path.getmtime(parquet_path) > os.path.getmtime(filepath):
            jira_df = pd.read_parquet(parquet_path)
            message = f"{auto_selected_msg}\nSuccessfully loaded {len(jira_df)} issues from cached file {os.path.basename(parquet_path)}"
        else:
            # Load from CSV and create/update the cache
            jira_df = pd.read_csv(filepath)
            jira_df.dropna(how='all', inplace=True)
            #Intelligently fill NaN values based on column type
            for col in jira_df.columns:
                if jira_df[col].dtype == 'object':
                    jira_df[col].fillna('[NOT_AVAILABLE]', inplace=True)
                else:
                    jira_df[col].fillna(0, inplace=True)
            jira_df.to_parquet(parquet_path)
            message = f"{auto_selected_msg}\nSuccessfully loaded {len(jira_df)} issues from {os.path.basename(filepath)} and created cache."
            
        return message
    except Exception as e:
        return f"Error loading data: {e}"

@mcp.tool()
def list_jira_issues(count: int = 10) -> str:
    """Lists the first N Jira issues from the loaded CSV."""
    if jira_df is None:
        return "Jira CSV not loaded. Please load a file first using load_jira_csv."
    if count > len(jira_df):
        count = len(jira_df)
    
    # Selecting key columns for a concise summary
    summary_df = jira_df[['Issue key', 'Summary', 'Status', 'Assignee']].head(count)
    return summary_df.to_string()

@mcp.tool()
def get_issue_details(issue_key: str) -> str:
    """Gets all details for a specific Jira issue by its key."""
    if jira_df is None:
        return "Jira CSV not loaded. Please load a file first using load_jira_csv."
    
    issue = jira_df[jira_df['Issue key'] == issue_key]
    
    if issue.empty:
        return f"Issue with key '{issue_key}' not found."
    
    # Return all details for the found issue
    return issue.to_string()

@mcp.tool()
def search_issues(query: str, search_in_column: str = 'Summary') -> str:
    """Searches for issues containing a query string in a specified column."""
    if jira_df is None:
        return "Jira CSV not loaded. Please load a file first using load_jira_csv."
    
    if search_in_column not in jira_df.columns:
        return f"Column '{search_in_column}' not found. Available columns are: {list(jira_df.columns)}"

    # Case-insensitive search
    results = jira_df[jira_df[search_in_column].str.contains(query, case=False, na=False)]
    
    if results.empty:
        return f"No issues found with query '{query}' in column '{search_in_column}'."
    
    summary_df = results[['Issue key', 'Summary', 'Status', 'Assignee']]
    return summary_df.to_string()

@mcp.tool()
def get_status_summary() -> str:
    """Gets a summary of issue counts by status."""
    if jira_df is None:
        return "Jira CSV not loaded. Please load a file first using load_jira_csv."
    
    if 'Status' not in jira_df.columns:
        return "Column 'Status' not found in the CSV."

    status_counts = jira_df['Status'].value_counts()
    return status_counts.to_string()

@mcp.tool()
def get_assignee_summary() -> str:
    """Gets a summary of issue counts by assignee."""
    if jira_df is None:
        return "Jira CSV not loaded. Please load a file first using load_jira_csv."
    
    if 'Assignee' not in jira_df.columns:
        return "Column 'Assignee' not found in the CSV."

    assignee_counts = jira_df['Assignee'].value_counts()
    return assignee_counts.to_string()

# Helper functions for enhanced analysis
def _parse_date(date_str: str) -> datetime:
    """Parse various date formats commonly found in Jira exports."""
    if pd.isna(date_str) or date_str == '[NOT_AVAILABLE]':
        return None
    
    # Common Jira date formats
    formats = [
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d',
        '%d/%m/%Y %H:%M:%S',
        '%d/%m/%Y',
        '%m/%d/%Y %H:%M:%S',
        '%m/%d/%Y'
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except (ValueError, TypeError):
            continue
    return None

def _categorize_status(status: str) -> str:
    """Categorize status into active vs done states."""
    if pd.isna(status) or status == '[NOT_AVAILABLE]':
        return 'Unknown'
    
    done_statuses = ['done', 'closed', 'resolved', 'completed', 'finished']
    active_statuses = ['in progress', 'in development', 'in review', 'testing']
    
    status_lower = status.lower()
    if any(done in status_lower for done in done_statuses):
        return 'Done'
    elif any(active in status_lower for active in active_statuses):
        return 'Active'
    else:
        return 'Pending'

def _calculate_days_since_update(updated_date: str) -> int:
    """Calculate days since last update."""
    parsed_date = _parse_date(updated_date)
    if parsed_date is None:
        return -1
    return (datetime.now() - parsed_date).days

# Enhanced MCP Tools (Phase 1.1)

@mcp.tool()
def summarize_jira_csv() -> str:
    """High-level project summary with key metrics."""
    if jira_df is None:
        return "Jira CSV not loaded. Please load a file first using load_jira_csv."
    
    total_issues = len(jira_df)
    
    # Status breakdown
    status_counts = jira_df['Status'].value_counts() if 'Status' in jira_df.columns else {}
    
    # Assignee breakdown
    assignee_counts = jira_df['Assignee'].value_counts() if 'Assignee' in jira_df.columns else {}
    unassigned_count = len(jira_df[jira_df['Assignee'] == '[NOT_AVAILABLE]']) if 'Assignee' in jira_df.columns else 0
    
    # Priority breakdown if available
    priority_counts = jira_df['Priority'].value_counts() if 'Priority' in jira_df.columns else {}
    
    summary = f"""
PROJECT SUMMARY
===============
Total Issues: {total_issues}
Unassigned Issues: {unassigned_count}

TOP STATUSES:
{status_counts.head().to_string() if not status_counts.empty else 'No status data'}

TOP ASSIGNEES:
{assignee_counts.head().to_string() if not assignee_counts.empty else 'No assignee data'}

PRIORITY BREAKDOWN:
{priority_counts.to_string() if not priority_counts.empty else 'No priority data'}
"""
    return summary.strip()

@mcp.tool()
def get_jira_status_breakdown() -> str:
    """Status distribution analysis with categorization."""
    if jira_df is None:
        return "Jira CSV not loaded. Please load a file first using load_jira_csv."
    
    if 'Status' not in jira_df.columns:
        return "Column 'Status' not found in the CSV."
    
    # Raw status counts
    status_counts = jira_df['Status'].value_counts()
    
    # Categorized status analysis
    jira_df['Status_Category'] = jira_df['Status'].apply(_categorize_status)
    category_counts = jira_df['Status_Category'].value_counts()
    
    breakdown = f"""
STATUS BREAKDOWN
================
Raw Status Counts:
{status_counts.to_string()}

Categorized Status:
{category_counts.to_string()}

Status Category Percentages:
{(category_counts / len(jira_df) * 100).round(1).to_string()}%
"""
    return breakdown.strip()

@mcp.tool()
def get_jira_assignee_workload() -> str:
    """Workload distribution per assignee with detailed analysis."""
    if jira_df is None:
        return "Jira CSV not loaded. Please load a file first using load_jira_csv."
    
    if 'Assignee' not in jira_df.columns:
        return "Column 'Assignee' not found in the CSV."
    
    # Basic assignee counts
    assignee_counts = jira_df['Assignee'].value_counts()
    
    # Workload analysis by status if available
    if 'Status' in jira_df.columns:
        workload_by_status = jira_df.groupby(['Assignee', 'Status']).size().unstack(fill_value=0)
        
        workload = f"""
ASSIGNEE WORKLOAD ANALYSIS
==========================
Total Issues per Assignee:
{assignee_counts.to_string()}

Issues by Assignee and Status:
{workload_by_status.to_string()}
"""
    else:
        workload = f"""
ASSIGNEE WORKLOAD ANALYSIS
==========================
Total Issues per Assignee:
{assignee_counts.to_string()}
"""
    
    return workload.strip()

@mcp.tool()
def find_stale_issues_in_project(days_threshold: int = 30) -> str:
    """Find issues not updated recently."""
    if jira_df is None:
        return "Jira CSV not loaded. Please load a file first using load_jira_csv."
    
    # Look for common update date columns
    update_columns = ['Updated', 'Last Updated', 'Modified', 'updated']
    update_col = None
    
    for col in update_columns:
        if col in jira_df.columns:
            update_col = col
            break
    
    if update_col is None:
        return f"No update date column found. Available columns: {list(jira_df.columns)}"
    
    # Calculate days since update
    jira_df['Days_Since_Update'] = jira_df[update_col].apply(_calculate_days_since_update)
    
    # Find stale issues
    stale_issues = jira_df[jira_df['Days_Since_Update'] > days_threshold]
    stale_count = len(stale_issues)
    
    if stale_count == 0:
        return f"No stale issues found (older than {days_threshold} days)."
    
    # Get key details for stale issues
    if stale_count > 20:
        display_issues = stale_issues.nlargest(20, 'Days_Since_Update')
        result = f"Found {stale_count} stale issues (showing top 20 by staleness):\n\n"
    else:
        display_issues = stale_issues
        result = f"Found {stale_count} stale issues:\n\n"
    
    columns_to_show = ['Issue key', 'Summary', 'Status', 'Assignee', 'Days_Since_Update']
    available_columns = [col for col in columns_to_show if col in display_issues.columns]
    
    result += display_issues[available_columns].to_string()
    return result

@mcp.tool()
def find_blocked_issues_in_project() -> str:
    """Find blocked issues that need attention."""
    if jira_df is None:
        return "Jira CSV not loaded. Please load a file first using load_jira_csv."
    
    # Look for blocked indicators in status or other fields
    blocked_patterns = ['blocked', 'waiting', 'on hold', 'impediment']
    blocked_issues = pd.DataFrame()
    
    # Check Status column
    if 'Status' in jira_df.columns:
        status_blocked = jira_df[jira_df['Status'].str.contains('|'.join(blocked_patterns), case=False, na=False)]
        blocked_issues = pd.concat([blocked_issues, status_blocked])
    
    # Check Summary for blocked indicators
    if 'Summary' in jira_df.columns:
        summary_blocked = jira_df[jira_df['Summary'].str.contains('|'.join(blocked_patterns), case=False, na=False)]
        blocked_issues = pd.concat([blocked_issues, summary_blocked])
    
    # Remove duplicates
    blocked_issues = blocked_issues.drop_duplicates()
    blocked_count = len(blocked_issues)
    
    if blocked_count == 0:
        return "No blocked issues found."
    
    columns_to_show = ['Issue key', 'Summary', 'Status', 'Assignee']
    available_columns = [col for col in columns_to_show if col in blocked_issues.columns]
    
    result = f"Found {blocked_count} potentially blocked issues:\n\n"
    result += blocked_issues[available_columns].to_string()
    return result

@mcp.tool()
def find_due_soon_issues_in_project(days_ahead: int = 7) -> str:
    """Find issues due soon based on due date analysis."""
    if jira_df is None:
        return "Jira CSV not loaded. Please load a file first using load_jira_csv."
    
    # Look for due date columns
    due_columns = ['Due Date', 'Due date', 'due_date', 'DueDate']
    due_col = None
    
    for col in due_columns:
        if col in jira_df.columns:
            due_col = col
            break
    
    if due_col is None:
        return f"No due date column found. Available columns: {list(jira_df.columns)}"
    
    # Parse due dates and find upcoming ones
    current_date = datetime.now()
    future_date = current_date + timedelta(days=days_ahead)
    
    def is_due_soon(due_date_str):
        parsed_date = _parse_date(due_date_str)
        if parsed_date is None:
            return False
        return current_date <= parsed_date <= future_date
    
    due_soon_mask = jira_df[due_col].apply(is_due_soon)
    due_soon_issues = jira_df[due_soon_mask]
    due_count = len(due_soon_issues)
    
    if due_count == 0:
        return f"No issues due within the next {days_ahead} days."
    
    columns_to_show = ['Issue key', 'Summary', 'Status', 'Assignee', due_col]
    available_columns = [col for col in columns_to_show if col in due_soon_issues.columns]
    
    result = f"Found {due_count} issues due within {days_ahead} days:\n\n"
    result += due_soon_issues[available_columns].to_string()
    return result

@mcp.tool()
def find_unassigned_issues_in_project() -> str:
    """Find all unassigned issues."""
    if jira_df is None:
        return "Jira CSV not loaded. Please load a file first using load_jira_csv."
    
    if 'Assignee' not in jira_df.columns:
        return "Column 'Assignee' not found in the CSV."
    
    # Find unassigned issues (empty, NaN, or [NOT_AVAILABLE])
    unassigned_mask = (
        (jira_df['Assignee'] == '[NOT_AVAILABLE]') |
        (jira_df['Assignee'].isna()) |
        (jira_df['Assignee'] == '') |
        (jira_df['Assignee'].str.strip() == '')
    )
    
    unassigned_issues = jira_df[unassigned_mask]
    unassigned_count = len(unassigned_issues)
    
    if unassigned_count == 0:
        return "No unassigned issues found."
    
    columns_to_show = ['Issue key', 'Summary', 'Status', 'Priority']
    available_columns = [col for col in columns_to_show if col in unassigned_issues.columns]
    
    result = f"Found {unassigned_count} unassigned issues:\n\n"
    result += unassigned_issues[available_columns].to_string()
    return result

@mcp.tool()
def find_issues_with_missing_fields() -> str:
    """Data quality analysis - find issues with missing critical fields."""
    if jira_df is None:
        return "Jira CSV not loaded. Please load a file first using load_jira_csv."
    
    # Critical fields to check
    critical_fields = ['Summary', 'Status', 'Assignee', 'Priority']
    available_critical_fields = [field for field in critical_fields if field in jira_df.columns]
    
    if not available_critical_fields:
        return f"None of the critical fields found. Available columns: {list(jira_df.columns)}"
    
    missing_data_summary = {}
    issues_with_missing = pd.DataFrame()
    
    for field in available_critical_fields:
        missing_mask = (
            (jira_df[field] == '[NOT_AVAILABLE]') |
            (jira_df[field].isna()) |
            (jira_df[field] == '') |
            (jira_df[field].str.strip() == '')
        )
        missing_count = missing_mask.sum()
        missing_data_summary[field] = missing_count
        
        if missing_count > 0:
            field_missing_issues = jira_df[missing_mask].copy()
            field_missing_issues['Missing_Field'] = field
            issues_with_missing = pd.concat([issues_with_missing, field_missing_issues])
    
    # Remove duplicates but keep track of which fields are missing
    issues_with_missing = issues_with_missing.drop_duplicates(subset=['Issue key'])
    
    total_issues = len(jira_df)
    quality_score = 1.0 - (len(issues_with_missing) / total_issues) if total_issues > 0 else 0.0
    
    result = f"""
DATA QUALITY ANALYSIS
=====================
Total Issues: {total_issues}
Issues with Missing Critical Fields: {len(issues_with_missing)}
Data Quality Score: {quality_score:.2%}

Missing Field Counts:
"""
    for field, count in missing_data_summary.items():
        percentage = (count / total_issues * 100) if total_issues > 0 else 0
        result += f"{field}: {count} ({percentage:.1f}%)\n"
    
    if len(issues_with_missing) > 0:
        result += f"\nIssues with Missing Data (showing first 20):\n"
        display_columns = ['Issue key', 'Summary', 'Status', 'Assignee', 'Priority']
        available_display_columns = [col for col in display_columns if col in issues_with_missing.columns]
        result += issues_with_missing[available_display_columns].head(20).to_string()
    
    return result.strip()

@mcp.tool()
def suggest_data_fixes() -> str:
    """Generate automated fix suggestions for data quality issues."""
    if jira_df is None:
        return "Jira CSV not loaded. Please load a file first using load_jira_csv."
    
    suggestions = []
    
    # Check for unassigned issues
    if 'Assignee' in jira_df.columns:
        unassigned_count = len(jira_df[jira_df['Assignee'] == '[NOT_AVAILABLE]'])
        if unassigned_count > 0:
            suggestions.append({
                "issue": "Unassigned Issues",
                "count": unassigned_count,
                "suggestion": "Consider assigning issues based on component, priority, or workload distribution",
                "action": "bulk_assign_by_component"
            })
    
    # Check for missing priorities
    if 'Priority' in jira_df.columns:
        missing_priority_count = len(jira_df[jira_df['Priority'] == '[NOT_AVAILABLE]'])
        if missing_priority_count > 0:
            suggestions.append({
                "issue": "Missing Priorities",
                "count": missing_priority_count,
                "suggestion": "Set default priority based on issue type or component",
                "action": "set_default_priority"
            })
    
    # Check for stale issues
    if 'Updated' in jira_df.columns or 'updated' in jira_df.columns:
        update_col = 'Updated' if 'Updated' in jira_df.columns else 'updated'
        stale_count = len(jira_df[jira_df[update_col].apply(_calculate_days_since_update) > 60])
        if stale_count > 0:
            suggestions.append({
                "issue": "Stale Issues (>60 days)",
                "count": stale_count,
                "suggestion": "Review and close completed issues or update status",
                "action": "review_stale_issues"
            })
    
    if not suggestions:
        return "No significant data quality issues found. Your data looks good!"
    
    result = "DATA FIX SUGGESTIONS\n====================\n\n"
    for i, suggestion in enumerate(suggestions, 1):
        result += f"{i}. {suggestion['issue']} ({suggestion['count']} issues)\n"
        result += f"   Suggestion: {suggestion['suggestion']}\n"
        result += f"   Recommended Action: {suggestion['action']}\n\n"
    
    return result.strip()

@mcp.tool()
def apply_bulk_jira_updates(updates_json: str) -> str:
    """Apply bulk updates with idempotency checks (simulation for CSV data)."""
    if jira_df is None:
        return "Jira CSV not loaded. Please load a file first using load_jira_csv."
    
    try:
        updates = json.loads(updates_json)
    except json.JSONDecodeError:
        return "Invalid JSON format for updates."
    
    if not isinstance(updates, list):
        return "Updates must be a list of update objects."
    
    results = {"applied": [], "skipped": [], "errors": []}
    
    for update in updates:
        if not isinstance(update, dict) or 'issue_id' not in update or 'changes' not in update:
            results["errors"].append({
                "error": "Invalid update format. Must have 'issue_id' and 'changes' fields."
            })
            continue
        
        issue_id = update["issue_id"]
        proposed_changes = update["changes"]
        
        # Find the issue
        issue_mask = jira_df['Issue key'] == issue_id
        if not issue_mask.any():
            results["errors"].append({
                "issue_id": issue_id,
                "error": f"Issue {issue_id} not found"
            })
            continue
        
        # Check if changes would actually change anything (idempotency)
        issue_row = jira_df[issue_mask].iloc[0]
        changes_needed = False
        
        for field, new_value in proposed_changes.items():
            if field not in jira_df.columns:
                results["errors"].append({
                    "issue_id": issue_id,
                    "error": f"Field '{field}' not found in data"
                })
                continue
            
            current_value = issue_row[field]
            if current_value != new_value:
                changes_needed = True
                break
        
        if not changes_needed:
            results["skipped"].append({
                "issue_id": issue_id,
                "reason": "No changes needed (values already match)"
            })
            continue
        
        # Apply changes (simulation - in real implementation this would update the actual system)
        try:
            # For CSV simulation, we just track what would be changed
            results["applied"].append({
                "issue_id": issue_id,
                "changes": proposed_changes,
                "note": "Simulated update - would apply in real system"
            })
        except Exception as e:
            results["errors"].append({
                "issue_id": issue_id,
                "error": str(e)
            })
    
    # Summary
    summary = f"""
BULK UPDATE RESULTS
===================
Applied: {len(results['applied'])} updates
Skipped: {len(results['skipped'])} (no changes needed)
Errors: {len(results['errors'])}

Details: {json.dumps(results, indent=2)}
"""
    
    return summary.strip()