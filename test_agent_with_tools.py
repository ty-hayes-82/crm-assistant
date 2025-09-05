#!/usr/bin/env python3
"""
Test script to create and run the simple agent with properly configured tools.
"""

import os
import sys
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from google.adk.agents import LlmAgent
    from google.adk.tools import FunctionTool
    from google.adk import Runner
    import yaml
    
    # Import our MCP bridge functions
    from yaml_agent.mcp_bridge import call_mcp_tool, request_human_approval
    
    # Load the agent configuration
    config_path = "yaml_agent/agent.yaml"
    
    print(f"Loading agent config from: {config_path}")
    
    # Check if file exists
    if not os.path.exists(config_path):
        print(f"Error: Config file {config_path} not found")
        sys.exit(1)
    
    # Load YAML configuration
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    print(f"Config loaded successfully: {config['name']}")
    
    # Create function tools for each MCP tool
    tools = []
    
    def summarize_jira_csv():
        """Get a high-level summary of the Jira CSV including total issues, projects, and statuses."""
        return call_mcp_tool("summarize_jira_csv", {})
    
    def search_jira_issues(query: str):
        """Search for issues containing specific text in summaries or descriptions."""
        return call_mcp_tool("search_jira_issues", {"query": query})
    
    def get_jira_status_breakdown():
        """Get the distribution of issues by status (Done, In Progress, Backlog, etc.)."""
        return call_mcp_tool("get_jira_status_breakdown", {})
    
    def get_jira_assignee_workload():
        """Get workload distribution showing how many issues are assigned to each person."""
        return call_mcp_tool("get_jira_assignee_workload", {})
    
    # Create FunctionTool instances
    tools.append(FunctionTool(summarize_jira_csv))
    tools.append(FunctionTool(search_jira_issues))
    tools.append(FunctionTool(get_jira_status_breakdown))
    tools.append(FunctionTool(get_jira_assignee_workload))
    
    print(f"Created {len(tools)} tools")
    
    # Create the agent with tools
    agent = LlmAgent(
        name=config['name'],
        model=config['model'],
        instruction=config['instruction'],
        tools=tools
    )
    
    print(f"Agent created successfully with tools: {type(agent)}")
    
    # Test the agent by calling one of the tools
    print("\n=== Testing Agent Tools Directly ===")
    try:
        print("Testing summarize_jira_csv...")
        result = summarize_jira_csv()
        print(f"Direct tool call successful: {result[:200]}...")
    except Exception as e:
        print(f"Direct tool call failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n=== Agent and Tools Created Successfully ===")
    print(f"Agent: {agent.name}")
    print(f"Model: {agent.model}")
    print(f"Number of tools: {len(agent.tools)}")
    print("\nThe agent is ready to use. You can now integrate it with a proper Runner or CLI interface.")
        
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure google-adk is properly installed.")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
