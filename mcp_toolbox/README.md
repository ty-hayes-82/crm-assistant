# Jira CSV MCP Toolbox

This MCP toolbox provides Claude for Desktop with tools to analyze Jira CSV export data. It's organized following the same pattern as the official MCP toolbox but uses a custom Python implementation for Jira-specific analytics.

## Features

The toolbox provides the following tools for Jira CSV analysis. When these tools are registered into an external/combined MCP server, they are prefixed with `csv_` to avoid name collisions.

- summarize and breakdowns: `csv_summarize_jira_csv`, `csv_get_jira_status_breakdown`, `csv_get_jira_project_breakdown`, `csv_get_jira_priority_breakdown`, `csv_get_jira_assignee_workload`
- search: `csv_search_jira_issues`
- epics: `csv_list_jira_epics`, `csv_get_epic_health`, `csv_list_epic_children`, `csv_audit_epic_gaps`, `csv_get_epic_recent_progress`
- details & recent progress: `csv_get_issue_full_details`, `csv_get_recent_progress`
- Jira API passthrough (optional env vars required): `csv_jira_find_user`, `csv_jira_get_issue`, `csv_jira_create_issue`, `csv_jira_add_comment`

## Prerequisites

- Python 3.11+
- Poetry for dependency management
- Claude for Desktop (for MCP integration)
- Docker (optional, for containerized deployment)

## Project Structure

```
mcp_toolbox/
├── utils/
│   ├── __init__.py
│   └── jira_reader.py          # CSV analysis utilities
├── tools/
│   ├── __init__.py
│   └── jira_tools.py           # MCP tool definitions
├── server.py                   # MCP server instance
├── main.py                     # Entry point
├── docker-compose.yaml         # Docker deployment
├── Dockerfile                  # Container definition
└── README.md                   # This file
```

## Local Development

### 1. Install Dependencies

```bash
cd mcp_toolbox
poetry install
```

### 2. Run the MCP Server

```bash
poetry run python -m mcp_toolbox.main
```

### 3. Configure MCP client (Claude/Cursor)

Create or update your Claude configuration file:

**macOS/Linux:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```
{
  "mcpServers": {
    "jira_toolbox": {
      "type": "command",
      "command": "python",
      "args": ["-u", "-m", "mcp_toolbox"],
      "cwd": "C:\\path\\to\\jira-assistant"
    }
  }
}
```

## Docker Deployment

### 1. Build and Run with Docker Compose

```bash
cd mcp_toolbox
docker-compose up --build
```

### 2. Or Build Docker Image Manually

```bash
docker build -t jira-csv-toolbox .
docker run -p 5000:5000 -v $(pwd)/../docs:/app/docs jira-csv-toolbox
```

## Usage Examples

Once connected to Claude for Desktop, you can ask:

- "Give me a summary of the Jira CSV data"
- "What's the status breakdown of our issues?"
- "Show me the top 5 assignees by workload"
- "Search for issues containing 'authentication'"
- "What's the priority distribution?"

## Data Requirements

The toolbox expects a Jira CSV export file located at `../docs/Jira 2025-07-24T08_20_44-0700.csv` with standard Jira columns:

- `Issue key`
- `Summary`
- `Status`
- `Project key`
- `Priority`
- `Assignee`
- `Description`

## Configuration

The toolbox is configured through:

- **CSV file location**: Tools auto-detect the newest `Jira *.csv` in `docs`. You can pass `filename` to most tools to override.
- **Server name**: Set in `server.py` (`FastMCP` instance name)
- **Tool definitions**: Defined in `tools/jira_tools.py`

### Load tools into an existing MCP server

If you already have a server (e.g., `jira-tools`) and want to load these tools into it, add this to your server script before `mcp.run()`:

```python
import sys
sys.path.append(r"C:\\path\\to\\jira-assistant")
from mcp_toolbox.tools.registry import register_all_tools

# mcp is your FastMCP instance
register_all_tools(mcp)  # Registers CSV tools with csv_ prefix names
```

## Extending the Toolbox

To add new CSV tools in the future:

1) Add a utility function in `utils/jira_reader.py` that takes optional `filename` and returns a string. Follow patterns like `_resolve_csv_path`, `_load_jira_df`, `_find_column`, and prefer robust column detection.

2) Expose it to MCP:
   - For the standalone toolbox server: add a new `@mcp.tool()` in `tools/jira_tools.py` that calls your utility.
   - For external servers (like `jira-tools`): also add a prefixed registration in `tools/registry.py` (e.g., `csv_my_new_tool`) so names don’t collide.

3) Keep stdout clean: don’t print in MCP entrypoints. The server speaks JSON-RPC over stdio.

4) CSV handling best practices learned:
   - Auto-pick newest `Jira *.csv` in `docs` by default; allow overriding via `filename`.
   - Use `_find_column` with multiple possible headers (e.g., `Epic Link`, `Parent`, `Parent Link`), including case-insensitive matching.
   - Be resilient to missing columns and return helpful messages.

5) Testing:
   - `python mcp_toolbox/local_client.py` to verify tools register and run.
   - For integration with Cursor/Claude, ensure config uses `-u -m mcp_toolbox` and correct `cwd`.

## Troubleshooting

### Server won't start
- Ensure dependencies are installed: `poetry install`
- Check Python version: `python --version` (should be 3.11+)
- Verify CSV file exists at expected location

### Claude can't connect
- Ensure server is running before trying to use tools
- Check configuration file path is absolute and correct
- Restart Claude for Desktop after configuration changes

### Tools not appearing
- Look for tool/hammer icon in Claude interface
- Check server logs for registration errors
- Verify JSON configuration syntax

## License

This toolbox is part of the jira-assistant project and follows the same Apache License 2.0. 