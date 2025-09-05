import os
import requests
from requests.auth import HTTPBasicAuth
import json

# --- Jira API Configuration ---
# It's recommended to set these as environment variables
JIRA_URL = os.environ.get("JIRA_URL")
JIRA_USERNAME = os.environ.get("JIRA_USERNAME")
JIRA_API_TOKEN = os.environ.get("JIRA_API_TOKEN")

def get_auth():
    """Returns the authentication object for Jira API requests."""
    if not all([JIRA_URL, JIRA_USERNAME, JIRA_API_TOKEN]):
        raise ValueError(
            "Jira credentials not set. Please set JIRA_URL, JIRA_USERNAME, and JIRA_API_TOKEN environment variables."
        )
    return HTTPBasicAuth(JIRA_USERNAME, JIRA_API_TOKEN)

def make_request(method, endpoint, payload=None):
    """Generic function to make requests to the Jira API."""
    url = f"{JIRA_URL}/rest/api/3/{endpoint}"
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    auth = get_auth()
    
    try:
        if payload:
            response = requests.request(method, url, headers=headers, data=json.dumps(payload), auth=auth)
        else:
            response = requests.request(method, url, headers=headers, auth=auth)
        
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # Handle responses that might not have content
        if response.status_code == 204:  # No Content
            return None
        return response.json()
    except requests.exceptions.HTTPError as err:
        return {"error": f"HTTP Error: {err.response.status_code}", "message": err.response.text}
    except requests.exceptions.RequestException as e:
        return {"error": "Request failed", "message": str(e)}

# --- API Utility Functions ---

def find_user(query: str):
    """Find a Jira user by their name or email."""
    return make_request("GET", f"user/search?query={query}")

def get_issue(issue_key: str):
    """Get the details of a specific Jira issue."""
    return make_request("GET", f"issue/{issue_key}")

def create_issue(project_key: str, summary: str, description: str, issue_type: str = "Task"):
    """Create a new issue in a Jira project."""
    payload = {
        "fields": {
            "project": {"key": project_key},
            "summary": summary,
            "description": {
                "type": "doc",
                "version": 1,
                "content": [{"type": "paragraph", "content": [{"type": "text", "text": description}]}]
            },
            "issuetype": {"name": issue_type}
        }
    }
    return make_request("POST", "issue", payload)

def update_issue(issue_key: str, fields: dict):
    """Update an existing Jira issue."""
    payload = {"fields": fields}
    return make_request("PUT", f"issue/{issue_key}", payload)

def add_comment(issue_key: str, comment: str):
    """Add a comment to a Jira issue."""
    payload = {
        "body": {
            "type": "doc",
            "version": 1,
            "content": [{"type": "paragraph", "content": [{"type": "text", "text": comment}]}]
        }
    }
    return make_request("POST", f"issue/{issue_key}/comment", payload) 