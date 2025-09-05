# Agent Configuration Files

This directory contains ADK agent configuration files for top-level entry point agents.

## Available Configurations

### `coordinator.yaml`
- **Purpose**: Main coordinator agent with intelligent routing
- **Usage**: `adk run jira_agent/configs/coordinator.yaml`
- **Description**: Routes user requests to specialized agents based on intent

### `simple_agent.yaml` 
- **Purpose**: Simple general-purpose Jira agent
- **Usage**: `adk run jira_agent/configs/simple_agent.yaml`
- **Description**: Direct access to all Jira tools without routing

## Why These Agents Have YAML Files

These are **top-level entry point agents** that can be run independently via the ADK runtime. Most other agents in the system are **sub-agents** that are created programmatically and don't need individual YAML configurations.

## Usage Examples

```bash
# Run the coordinator (recommended for most use cases)
adk run jira_agent/configs/coordinator.yaml

# Run the simple agent (for direct tool access)
adk run jira_agent/configs/simple_agent.yaml
```

## Adding New Top-Level Agents

If you create new top-level agents that should be runnable via ADK, add their YAML configurations here following the same pattern.
