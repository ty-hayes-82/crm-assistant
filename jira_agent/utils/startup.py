"""
Startup utilities for Jira agents.
Handles automatic data loading and initialization.
"""

import asyncio
from typing import Optional
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import StdioConnectionParams, MCPToolset
from mcp import StdioServerParameters


async def auto_load_jira_data(agent: Optional[LlmAgent] = None) -> str:
    """
    Automatically load the most recent Jira CSV data using MCP tools.
    
    Args:
        agent: Optional agent to use for loading. If None, creates a temporary MCP connection.
        
    Returns:
        Result message from loading operation
    """
    try:
        # Create a temporary MCP connection if no agent provided
        if agent is None:
            mcp_toolset = MCPToolset(
                connection_params=StdioConnectionParams(
                    server_params=StdioServerParameters(
                        command='python',
                        args=['-m', 'jira_fastmcp_server'],
                    ),
                    timeout=30,
                ),
            )
            
            # Get the load_jira_csv tool
            tools = await mcp_toolset.list_tools()
            load_tool = None
            for tool in tools:
                if tool.name == 'load_jira_csv':
                    load_tool = tool
                    break
            
            if load_tool is None:
                return "Error: load_jira_csv tool not found"
            
            # Call the tool without parameters to auto-load latest CSV
            result = await mcp_toolset.call_tool(load_tool.name, {})
            return result.content[0].text if result.content else "No result from loading"
        
        else:
            # Use the provided agent to load data
            # This would require the agent to have MCP tools available
            # For now, we'll use the direct approach above
            return await auto_load_jira_data(None)
            
    except Exception as e:
        return f"Error during auto-load: {str(e)}"


def create_agent_with_auto_load(agent_factory, **kwargs) -> LlmAgent:
    """
    Create an agent and configure it with auto-loading capability.
    
    Args:
        agent_factory: Function that creates the agent
        **kwargs: Arguments to pass to the agent factory
        
    Returns:
        Configured agent with auto-loading
    """
    # Create the base agent
    agent = agent_factory(**kwargs)
    
    # Modify the agent's instruction to include auto-loading behavior
    original_instruction = agent.instruction
    
    enhanced_instruction = f"""SYSTEM INITIALIZATION: You will automatically load the most recent Jira CSV data at startup.

{original_instruction}

IMPORTANT: The Jira data is automatically loaded when you start. You don't need to ask the user to load it manually. 
If for any reason the data isn't loaded, you can call load_jira_csv() without parameters to auto-load the latest file.
"""
    
    # Update the agent's instruction
    agent.instruction = enhanced_instruction
    
    return agent


async def initialize_jira_agent(agent: LlmAgent) -> tuple[LlmAgent, str]:
    """
    Initialize a Jira agent with automatic data loading.
    
    Args:
        agent: The agent to initialize
        
    Returns:
        Tuple of (initialized_agent, load_result_message)
    """
    try:
        # Attempt to auto-load data
        load_result = await auto_load_jira_data()
        
        # Add a startup message to the agent's context if successful
        if "Successfully loaded" in load_result:
            startup_message = f"✅ STARTUP COMPLETE: {load_result}\n\nI'm ready to help you analyze your Jira data! You can ask me to:\n- List issues\n- Search for specific tickets\n- Generate reports and summaries\n- Analyze project health and risks\n- Find data quality issues\n\nWhat would you like to explore?"
        else:
            startup_message = f"⚠️ STARTUP WARNING: {load_result}\n\nI'll try to load data when you make your first request. What would you like to do?"
        
        # Store the startup message in the agent's context
        # Note: This is a conceptual approach - actual implementation may vary based on ADK capabilities
        if hasattr(agent, 'system_message'):
            agent.system_message = startup_message
        
        return agent, startup_message
        
    except Exception as e:
        error_msg = f"❌ STARTUP ERROR: {str(e)}\n\nI'll try to load data when you make your first request."
        return agent, error_msg
