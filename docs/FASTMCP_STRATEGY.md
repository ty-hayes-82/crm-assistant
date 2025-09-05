## Goal

Create a simple FastMCP server for `@mcp_toolbox/` and make it callable from `@yaml_agent/`.

## Current state (what you already have)

- `mcp_toolbox/server.py` uses `FastMCP` and exposes a shared instance `mcp`.
- `mcp_toolbox/tools/jira_tools.py` registers tools via `@mcp.tool()` at import time.
- Entry point: `python -m mcp_toolbox.main` runs `mcp.run()` with no stdout noise.
- `mcp_toolbox/local_client.py` can list/call tools for local smoke testing.

This already is a FastMCP server; we only need a minimal surface and an integration path from `yaml_agent`.

## Strategy overview

1) Provide a minimal tool surface (optional but recommended) to keep the interface simple.
2) Ensure Windows-friendly run/test commands and dependency setup.
3) Integrate from `yaml_agent` using either:
   - A) Direct MCP invocation if your agent runtime supports MCP client connectors.
   - B) A small Python bridge that calls the MCP server and is registered as a tool in the YAML agent.
4) Add quick tests and guardrails.

### 1) Minimal tool surface (optional)

Keep the original toolbox intact, but expose a small curated set for the first integration:

- `summarize_jira_csv`
- `get_jira_status_breakdown`
- `get_jira_assignee_workload`
- `search_jira_issues`

Implementation options:

- Easiest: Keep using `mcp_toolbox/__main__.py` as-is (loads all tools). The agent can still choose to call only the four above.
- Stricter: Create `mcp_toolbox/tools/minimal_tools.py` that selectively imports and re-exports only those functions, then modify `mcp_toolbox/__main__.py` to import that module instead of `tools/jira_tools.py`.

Start with the easiest; tighten later if needed.

### 2) Windows-friendly setup and run

Dependencies (example):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install mcp pydantic pandas
```

Run the server locally for testing:

```powershell
python -m mcp_toolbox.main
```

List/call tools via the provided client:

```powershell
python mcp_toolbox\local_client.py
```

### 3) Integrate from `yaml_agent`

Pick one of these approaches.

#### A) Direct MCP integration (if supported by your agent runtime)

Some agents support MCP servers as tools via a command-based launcher. Configure your agent to launch:

```yaml
# yaml_agent/root_agent.yaml (conceptual example)
name: root_agent
description: A helpful assistant for user questions.
instruction: Answer user questions to the best of your knowledge
model: gemini-2.5-flash
# tools:
#   - name: jira_csv
#     type: mcp
#     server:
#       command: python
#       args:
#         - -m
#         - mcp_toolbox.main
#       cwd: C:\\GIT\\test-adk
```

Notes:

- The exact YAML schema for registering tools depends on the agent runtime. Use the above as a template and adapt field names to your runtime’s schema.
- Ensure the working directory points at the repo root or wherever the module resolves.

#### B) Python bridge wrapper (works universally)

Add a tiny bridge in `yaml_agent` that calls the MCP server programmatically. Then register that Python function as a tool in your agent config.

Proposed file: `yaml_agent/mcp_bridge.py`

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def _call(tool_name: str, args: dict) -> str:
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "mcp_toolbox.main"],
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, args or {})
            return result.content[0].text if result.content else ""

def call_mcp_tool(tool_name: str, args: dict | None = None) -> str:
    return asyncio.run(_call(tool_name, args or {}))
```

Register this function as a Python tool in your agent system. Example (conceptual):

```yaml
# yaml_agent/root_agent.yaml (conceptual example)
name: root_agent
description: A helpful assistant for user questions.
instruction: Answer user questions to the best of your knowledge
model: gemini-2.5-flash
# tools:
#   - name: jira_csv_summarize
#     type: python
#     module: yaml_agent.mcp_bridge
#     function: call_mcp_tool
#     fixedArgs: { tool_name: "summarize_jira_csv" }
#   - name: jira_csv_status
#     type: python
#     module: yaml_agent.mcp_bridge
#     function: call_mcp_tool
#     fixedArgs: { tool_name: "get_jira_status_breakdown" }
#   - name: jira_csv_workload
#     type: python
#     module: yaml_agent.mcp_bridge
#     function: call_mcp_tool
#     fixedArgs: { tool_name: "get_jira_assignee_workload" }
#   - name: jira_csv_search
#     type: python
#     module: yaml_agent.mcp_bridge
#     function: call_mcp_tool
#     fixedArgs: { tool_name: "search_jira_issues" }
```

Notes:

- Adjust to your agent framework’s schema. The pattern is to wrap `call_mcp_tool` with fixed `tool_name` and pass user arguments as needed.
- Keep each command short and non-interactive to comply with your Windows PowerShell rules.

### 4) Quick tests and guardrails

- Local smoke test: `python mcp_toolbox/local_client.py` to list and run tools.
- Basic CSV availability: place a Jira CSV under `docs/` (or override `filename` args). Many tools resolve the newest `Jira *.csv` by default.
- Logging: If you add entrypoint scripts, avoid stdout prints (MCP uses stdio for JSON-RPC). Keep logging outside the MCP stdio process or use file logging.

## Rollout plan

1) Verify environment and run server locally.
2) Choose approach A or B and wire the agent.
3) Start with two tools (`summarize_jira_csv`, `get_jira_status_breakdown`).
4) Add `get_jira_assignee_workload` and `search_jira_issues` after basic success.
5) Optionally tighten surface with a `minimal_tools.py` import path.

## Troubleshooting

- If tools don’t appear, ensure the server process starts (no stdout prints) and the working directory is correct.
- On Windows, activate the venv in the same session before running Python commands:

```powershell
.venv\Scripts\Activate.ps1
```

- If the agent cannot find modules, confirm `C:\GIT\test-adk` is the working directory and `python -m mcp_toolbox.main` works directly in PowerShell.


