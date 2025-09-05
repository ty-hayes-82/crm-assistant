## Jira Assistant Architecture (ADK + FastMCP)

This document recommends a practical, self-sufficient multi-agent architecture (using ADK primitives) that integrates with your existing FastMCP Jira toolbox. It is optimized to: 1) keep you on top of team tasks, 2) highlight risks and gaps, 3) clean missing data, and 4) scale and delegate effectively.

### TL;DR Recommendation

- **Primary pattern**: Hierarchical Coordinator/Dispatcher with specialist sub‑agents
- **Workflow patterns**: Parallel Fan‑Out/Gather for health checks; Sequential Pipeline for data hygiene; optional Human‑in‑the‑Loop steps; Iterative loops for periodic monitoring
- **Integration**: Reuse your `mcp_toolbox` FastMCP server; call via MCP from the agent system (Approach A) or a small Python bridge (Approach B)
- **Why this works**: Clear delegation, modularity, and easy scaling—add new specialists without changing the core. Suits Jira monitoring, reporting, and cleanup.

---

## 1) Goals and constraints

- **Stay on top of tasks**: periodic health status, per‑assignee workload, sprint view
- **Highlight areas to address**: blocked, stale, due‑soon, unassigned, scope changes
- **Clean missing data**: missing story points, assignee, labels, epic links
- **Self‑sufficient**: scheduled/looped checks with minimal human intervention
- **Scalable and delegative**: add specialists; coordinator routes requests
- **Windows‑friendly**: short, single-purpose commands; non-interactive scripts

---

## 2) Proposed agent tree (high-level)

```mermaid
graph TD
  A[JiraCoordinator (LLM)] --> B[RiskMonitor (Workflow)]
  A --> C[DataCleaner (Workflow)]
  A --> D[Reporter (LLM)]
  A --> E[AdHocQuery (LLM)]

  subgraph B1[RiskMonitor internals]
    B --> Bp[[ParallelAgent: checks]]
    Bp --> B1a[Find stale]
    Bp --> B1b[Find blocked]
    Bp --> B1c[Find due soon]
    Bp --> B1d[Find unassigned]
    Bp --> B2[RiskSynthesizer (LLM)]
  end

  subgraph C1[DataCleaner internals]
    C --> Cs[[SequentialAgent]]
    Cs --> C1a[Find missing fields]
    Cs --> C1b[Suggest fixes (LLM)]
    Cs --> C1c[Human approval (optional)]
    Cs --> C1d[Apply updates]
  end

  subgraph MCP[FastMCP server]
    M1[mcp_toolbox Jira tools]
  end

  B1a --> M1
  B1b --> M1
  B1c --> M1
  B1d --> M1
  C1a --> M1
  C1d --> M1
  D --> M1
  E --> M1
```

---

## 3) How ADK primitives map to the Jira use cases

- **Coordinator/Dispatcher (LLM‑Driven Delegation)**
  - **Agent**: `JiraCoordinator`
  - **Role**: Interpret the user’s intent and delegate to specialists (`RiskMonitor`, `DataCleaner`, `Reporter`, `AdHocQuery`) via transfer or AgentTool calls.

- **Parallel Fan‑Out/Gather**
  - **Agent**: `RiskMonitor`
  - **Role**: Run independent health checks concurrently (stale/blocked/due‑soon/unassigned) via a `ParallelAgent`, save outputs to distinct `session.state` keys, then trigger a separate `LlmAgent` step to synthesize a concise summary.

- **Sequential Pipeline**
  - **Agent**: `DataCleaner`
  - **Role**: Deterministic steps orchestrated by `SequentialAgent`: find → suggest (via an `LlmAgent`) → approve (optional) → apply updates. Ideal for consistent cleanup with safe control points.

- **Human‑in‑the‑Loop (optional)**
  - **Agent**: approval step inside `DataCleaner`
  - **Role**: When needed, pause to confirm bulk edits (e.g., setting story points) via a custom tool; otherwise run headless on pre‑approved rules.

- **Iterative/Loop**
  - **Agent**: Scheduled or `LoopAgent` wrapper
  - **Role**: Periodic morning checks, sprint hygiene audits, weekly reports; loop ends on condition (e.g., all checks done) or after N iterations.

---

## 4) Specialist agent responsibilities

- **JiraCoordinator (LLM)**
  - Natural‑language entry point; routes to specialists using transfer or AgentTool
  - Maintains light state (e.g., current sprint, team selection) and aggregates responses

- **RiskMonitor (Workflow)**
  - Orchestrates parallel checks (via `ParallelAgent`) using MCP Jira tools; writes findings to `state`
  - Triggers `RiskSynthesizer` (`LlmAgent`) to produce a short, actionable “attention list” (top risks, owners, due dates)
  - **State I/O**: Each check agent (`FindStale`, `FindBlocked`, etc.) writes a structured list of issues to a dedicated `session.state` key (e.g., `stale_issues`, `blocked_issues`). The synthesizer reads from these keys.

- **DataCleaner (Workflow)**
  - Orchestrates steps: detection → `FixSuggester` (`LlmAgent`) → optional approval → apply updates
  - Applies updates through MCP Jira tools (idempotent, logged)
  - **State I/O**: `FindMissingFields` writes its findings to `session.state.missing_fields`; subsequent steps read from and act on this data.

- **Reporter (LLM)**
  - Produces concise summaries: sprint status, per‑assignee workload, burndown‑style narratives
  - Can emit artifacts (CSV/markdown) for dashboards or emails

- **AdHocQuery (LLM)**
  - Flexible question answering over Jira data; leverages search/CSV summarization tools

---

## 5) FastMCP integration (fits your existing setup)

You already have a FastMCP server and Jira tools:

- `mcp_toolbox/server.py` exposes a shared `mcp` instance
- `mcp_toolbox/tools/jira_tools.py` registers tools via `@mcp.tool()`
- Entry point: `python -m mcp_toolbox.main` (no stdout noise)
- Local smoke test: `python mcp_toolbox\local_client.py`

Two integration options from the agent system:

- **A) Direct MCP launch (if supported)**
  - Configure the agent runtime to spawn `python -m mcp_toolbox.main` as an MCP tool server

- **B) Python bridge wrapper (universal, recommended to start)**
  - Small bridge (e.g., `yaml_agent/mcp_bridge.py`) that spawns the MCP server and calls tools programmatically
  - Register this bridge as a Python tool in the agent config with fixed `tool_name` per Jira capability

### 5.1) MCP Server Lifecycle and Health

- **Process Management**: The ADK runtime or Python bridge is responsible for starting and stopping the `python -m mcp_toolbox.main` process. Ensure the subprocess is terminated gracefully on agent shutdown.
- **Health/Handshake**: Before the first tool call, the bridge should perform a health check (e.g., a simple `ping` or `get_version` tool call) to ensure the MCP server is responsive.
- **Startup/Retry**: Implement a timeout and retry mechanism for the initial health check to handle slow server startup.
- **Error Handling**: The MCP server must only emit JSON-RPC on stdout. All logging and errors should be structured and sent to stderr or a log file to avoid corrupting the communication channel.

Windows‑friendly setup reminder (short, single‑purpose commands):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install mcp pydantic pandas

# Run server
python -m mcp_toolbox.main

# Smoke test client
python mcp_toolbox\local_client.py
```

---

## 6) Example ADK wiring (conceptual)

```python
# Coordinator with workflow composition and LLM leaves
from google.adk.agents import LlmAgent
from google.adk.agents.workflow import ParallelAgent, SequentialAgent, LoopAgent

# Leaf LLM agents (they may call MCP tools via a bridge)
find_stale = LlmAgent(name="FindStale", description="Finds stale Jira issues and writes to state key 'stale_issues'.")
find_blocked = LlmAgent(name="FindBlocked", description="Finds blocked Jira issues and writes to state key 'blocked_issues'.")
find_due_soon = LlmAgent(name="FindDueSoon", description="Finds issues due soon and writes to state key 'due_soon_issues'.")
find_unassigned = LlmAgent(name="FindUnassigned", description="Finds unassigned issues and writes to state key 'unassigned_issues'.")
risk_synthesizer = LlmAgent(name="RiskSynthesizer", description="Synthesizes checks into an attention list using values from session.state.")

# RiskMonitor as a SequentialAgent: Parallel checks, then LLM synthesis
risk_checks = ParallelAgent(name="RiskChecks", agents=[find_stale, find_blocked, find_due_soon, find_unassigned])
risk_monitor = SequentialAgent(name="RiskMonitor", agents=[risk_checks, risk_synthesizer])

# DataCleaner steps
find_missing = LlmAgent(name="FindMissingFields", description="Detects issues with missing fields and writes to state key 'missing_fields'.")
fix_suggester = LlmAgent(name="FixSuggester", description="Proposes fixes for missing fields based on heuristics and context.")
apply_updates = LlmAgent(name="ApplyUpdates", description="Applies approved updates via MCP Jira tools; idempotent.")
data_cleaner = SequentialAgent(name="DataCleaner", agents=[find_missing, fix_suggester, apply_updates])

# Reporter and Ad-hoc remain LLM-driven
reporter = LlmAgent(name="Reporter", description="Summarizes status and workload.")
ad_hoc = LlmAgent(name="AdHocQuery", description="Answers flexible queries over Jira data.")

# Coordinator delegates to specialists
jira_coordinator = LlmAgent(
    name="JiraCoordinator",
    model="gemini-2.0-flash",
    instruction=(
        "You are a Jira project assistant. Delegate to RiskMonitor, DataCleaner, "
        "Reporter, or AdHocQuery based on the user's request."
    ),
    sub_agents=[risk_monitor, data_cleaner, reporter, ad_hoc],
)
```

```yaml
# Conceptual agent config snippet (tool registration via bridge)
# yaml_agent/root_agent.yaml
name: JiraCoordinator
description: A Jira project assistant that delegates to specialist agents.
model: gemini-2.5-flash
instruction: >
  You are a Jira project assistant. Delegate to RiskMonitor, DataCleaner,
  Reporter, or AdHocQuery based on the user's request.

sub_agents:
  - name: RiskMonitor
    type: sequential
    agents:
      - name: RiskChecks
        type: parallel
        agents:
          - name: FindStale
            model: gemini-2.5-flash
            instruction: Find stale Jira issues.
            tools: [find_stale_issues]
          - name: FindBlocked
            model: gemini-2.5-flash
            instruction: Find blocked Jira issues.
            tools: [find_blocked_issues]
          - name: FindDueSoon
            model: gemini-2.5-flash
            instruction: Find issues due soon.
            tools: [find_due_soon_issues]
          - name: FindUnassigned
            model: gemini-2.5-flash
            instruction: Find unassigned issues.
            tools: [find_unassigned_issues]
      - name: RiskSynthesizer
        model: gemini-2.5-flash
        instruction: >
          Review the lists of issues in session.state (stale_issues, blocked_issues, etc.)
          and create a short, actionable summary for the project manager.

  - name: DataCleaner
    type: sequential
    agents:
      - name: FindMissingFields
        model: gemini-2.5-flash
        instruction: Detects issues with missing fields and writes to state key 'missing_fields'.
        tools: [find_missing_fields]
      - name: FixSuggester
        model: gemini-2.5-flash
        instruction: Proposes fixes for missing fields based on heuristics and context.
        tools: [fix_suggester_suggestions]
      - name: HumanApproval
        model: gemini-2.5-flash
        instruction: Pause to confirm bulk edits (e.g., setting story points).
        tools: [approve_updates]
      - name: ApplyUpdates
        model: gemini-2.5-flash
        instruction: Applies approved updates via MCP Jira tools; idempotent.
        tools: [apply_updates]

  - name: Reporter
    model: gemini-2.5-flash
    instruction: Create reports and summaries from Jira data.
    tools: [get_jira_status_breakdown, get_jira_assignee_workload]

  - name: AdHocQuery
    model: gemini-2.5-flash
    instruction: Answer ad-hoc questions about Jira.
    tools: [search_jira_issues]

# Tool definitions using the Python bridge
tools:
  - name: find_stale_issues
    type: python
    module: yaml_agent.mcp_bridge
    function: call_mcp_tool
    fixedArgs: { tool_name: "find_stale_issues_in_project" }
    # Schemas for inputs (args) and outputs should be defined here
    # to guide the LLM in using the tool correctly.

  - name: find_blocked_issues
    type: python
    module: yaml_agent.mcp_bridge
    function: call_mcp_tool
    fixedArgs: { tool_name: "find_blocked_issues_in_project" }

  - name: find_due_soon_issues
    type: python
    module: yaml_agent.mcp_bridge
    function: call_mcp_tool
    fixedArgs: { tool_name: "find_due_soon_issues_in_project" }

  - name: find_unassigned_issues
    type: python
    module: yaml_agent.mcp_bridge
    function: call_mcp_tool
    fixedArgs: { tool_name: "find_unassigned_issues_in_project" }

  - name: fix_suggester_suggestions
    type: python
    module: yaml_agent.mcp_bridge
    function: call_mcp_tool
    fixedArgs: { tool_name: "fix_suggester_suggestions" }

  - name: approve_updates
    type: python
    module: yaml_agent.mcp_bridge
    function: call_mcp_tool
    fixedArgs: { tool_name: "approve_updates" }

  - name: apply_updates
    type: python
    module: yaml_agent.mcp_bridge
    function: call_mcp_tool
    fixedArgs: { tool_name: "apply_updates" }

  - name: get_jira_status_breakdown
    type: python
    module: yaml_agent.mcp_bridge
    function: call_mcp_tool
    fixedArgs: { tool_name: "get_jira_status_breakdown" }

  - name: get_jira_assignee_workload
    type: python
    module: yaml_agent.mcp_bridge
    function: call_mcp_tool
    fixedArgs: { tool_name: "get_jira_assignee_workload" }

  - name: search_jira_issues
    type: python
    module: yaml_agent.mcp_bridge
    function: call_mcp_tool
    fixedArgs: { tool_name: "search_jira_issues" }
```

Notes:
- Use `output_key` (or equivalent) on leaf agents to write results into `session.state` (e.g., `stale_issues`, `blocked_issues`, `workload`) for easy synthesis. Define clear schemas for these state objects.
- Prefer AgentTool wrappers or transfer for tool calls; keep workflow agents free of LLM reasoning, using them solely for deterministic orchestration.
- Each tool definition in the agent config should include input/output schemas to ensure the LLM calls them correctly and predictably.

---

## 7) Example user flows

- **Morning health check (autonomous)**
  - Scheduler or `LoopAgent` triggers `RiskMonitor` → parallel checks → synthesized “Top 10 risks” summary → optional email/dashboard artifact

- **Sprint hygiene**
  - `DataCleaner` runs: find missing fields → propose fixes (e.g., pointing) → optional approval → apply updates via MCP

- **Weekly status report**
  - `Reporter` composes a narrative and tables using `workload` and `status_breakdown`; publishes markdown/CSV artifacts

- **Ad hoc queries**
  - Ask “What’s blocking the release?” → Coordinator delegates to `RiskMonitor` then `Reporter` for a crisp management summary

---

## 8) Observability, safety, and ops

- **Logging**: Keep MCP server stdout clean (JSON‑RPC). Use file logging or external logs for execution traces.
- **Idempotency**: `DataCleaner` should re‑read Jira state before applying updates; log change sets.
- **Rate limits**: Batch or throttle Jira calls inside tools.
- **Validation**: Add a Reviewer step (Generator‑Critic) for sensitive reports before sending to stakeholders.
- **Artifacts**: Emit CSV/markdown for dashboards; persist to repo or storage.
- **Tool Allowlist**: Use agent configuration to explicitly grant tool access only to the leaf agents that need them (as shown in the YAML example). This prevents agents from calling unintended tools.
- **Secrets Management**: Jira credentials (API tokens, passwords) should be managed via a secure secrets store and passed to the MCP server or bridge through environment variables, not hardcoded in agent configs.
- **ADK Callbacks**: Implement `on_tool_start` and `on_tool_end` callbacks to trace tool inputs and outputs, providing a clear audit trail of MCP interactions.

---

## 9) Why this architecture

- **Self‑sufficient**: Coordinator + scheduled/looped workflows run without constant human prompts.
- **Scalable**: Add a new specialist (e.g., `BugTrends`, `ScopeChangeWatch`) without altering existing agents.
- **Delegative**: The LLM‑driven Coordinator routes to the right expert; tools provide precise execution.
- **Maintainable**: Specialists are small, testable, and map to concrete Jira operations via MCP.

---

## 10) Next steps

- Wire the Coordinator with four specialists as above
- Register MCP tools via bridge (Approach B) for immediate compatibility
- Start with two safe actions: `summarize_jira_csv`, `get_jira_status_breakdown`
- Add `get_jira_assignee_workload`, `search_jira_issues` next; then enable `DataCleaner` updates
- Introduce optional approval for bulk edits; later, automate with rules


