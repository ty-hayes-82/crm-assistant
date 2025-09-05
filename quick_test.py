#!/usr/bin/env python3
"""
Quick test of the agent functionality.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
import yaml
from yaml_agent.mcp_bridge import call_mcp_tool

async def quick_test():
    # Load config
    with open("yaml_agent/agent.yaml", 'r') as f:
        config = yaml.safe_load(f)
    
    # Create tools
    def summarize_jira_csv():
        return call_mcp_tool("summarize_jira_csv", {})
    
    def get_jira_status_breakdown():
        return call_mcp_tool("get_jira_status_breakdown", {})
    
    tools = [
        FunctionTool(summarize_jira_csv),
        FunctionTool(get_jira_status_breakdown)
    ]
    
    # Create agent
    agent = LlmAgent(
        name=config['name'],
        model=config['model'],
        instruction=config['instruction'],
        tools=tools
    )
    
    print("🧪 Testing agent with a simple question...")
    
    # Test the agent
    response_parts = []
    async for chunk in agent.run_async("Can you summarize the Jira data for me?"):
        if hasattr(chunk, 'text'):
            response_parts.append(chunk.text)
        elif hasattr(chunk, 'content'):
            response_parts.append(str(chunk.content))
        else:
            response_parts.append(str(chunk))
    
    response = ''.join(response_parts)
    print(f"✅ Agent Response: {response}")

if __name__ == "__main__":
    asyncio.run(quick_test())
