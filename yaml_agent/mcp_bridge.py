"""
MCP Bridge for yaml_agent integration.

This module provides a bridge to call MCP tools from the yaml_agent system.
It connects to the FastMCP server running the Jira CSV toolbox.
"""

import asyncio
import os
import sys
from typing import Dict, Any, Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Add project root to sys.path to allow imports from mcp_toolbox
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def _call_mcp_tool(tool_name: str, args: Dict[str, Any]) -> str:
    """
    Call an MCP tool asynchronously.
    
    Args:
        tool_name: Name of the MCP tool to call
        args: Arguments to pass to the tool
        
    Returns:
        String result from the tool
    """
    logging.info(f"Attempting to call MCP tool: {tool_name} with args: {args}")
    # Get the project root directory (assuming we're in yaml_agent/)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "mcp_toolbox.main"],
        cwd=project_root
    )
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                logging.info("MCP client session started.")
                await session.initialize()
                logging.info("MCP session initialized.")
                result = await session.call_tool(tool_name, args or {})
                logging.info(f"MCP tool {tool_name} call successful.")
                return result.content[0].text if result.content else ""
    except Exception as e:
        import traceback
        tb_str = traceback.format_exc()
        error_message = f"Error calling MCP tool '{tool_name}': {str(e)}\nTraceback:\n{tb_str}"
        logging.error(error_message)
        print(error_message, file=sys.stderr)  # Print to stderr to avoid polluting stdout
        return error_message


def call_mcp_tool(tool_name: str, args: Optional[Dict[str, Any]] = None) -> str:
    """
    Synchronous wrapper to call MCP tools.
    
    Args:
        tool_name: Name of the MCP tool to call
        args: Optional arguments to pass to the tool
        
    Returns:
        String result from the tool
    """
    logging.info(f"Synchronous call to MCP tool: {tool_name}")
    result = asyncio.run(_call_mcp_tool(tool_name, args or {}))
    logging.info(f"Synchronous call to MCP tool: {tool_name} completed.")
    return result


def request_human_approval(suggested_fixes: str) -> str:
    """
    Presents a set of suggested fixes to the user and asks for approval.

    This is a blocking tool that requires interactive user input from the console
    where the agent is running.

    Args:
        suggested_fixes: A string describing the proposed changes.

    Returns:
        The original `suggested_fixes` string if approved, or a rejection
        message if denied or in a non-interactive environment.
    """
    logging.info(f"Requesting human approval for: {suggested_fixes[:100]}...")
    if not suggested_fixes or not suggested_fixes.strip():
        logging.warning("No fixes were suggested, nothing to approve.")
        return "No fixes were suggested, nothing to approve."

    print("\n" + "=" * 60)
    print("🤖 The DataCleaner agent proposes the following changes:")
    print("-" * 60)
    print(suggested_fixes)
    print("-" * 60)

    try:
        # In a non-interactive environment (like a CI/CD pipeline), input() will raise EOFError.
        if not sys.stdout.isatty():
            logging.warning("Non-interactive environment detected. Assuming rejection.")
            print(" unattended environment. Assuming rejection.")
            return "REJECTED: Non-interactive environment"

        while True:
            response = input("Do you want to apply these changes? (yes/no): ").lower().strip()
            if response in ["yes", "y"]:
                print("✅ Changes approved by user.")
                logging.info("Changes approved by user.")
                return suggested_fixes
            elif response in ["no", "n"]:
                print("❌ Changes rejected by user.")
                logging.info("Changes rejected by user.")
                return "REJECTED: User denied request"
            else:
                print("Invalid input. Please enter 'yes' or 'no'.")
    except (EOFError, KeyboardInterrupt):
        logging.warning("User interruption detected. Assuming rejection.")
        print("\n user interruption. Assuming rejection.")
        return "REJECTED: User interruption"


def test_bridge():
    """Test the MCP bridge functionality."""
    print("🧪 Testing MCP Bridge...")
    print("=" * 50)

    # Test generic tool caller
    print("🔧 Testing generic call_mcp_tool...")
    try:
        result = call_mcp_tool("summarize_jira_csv", {})
        # Truncate for display
        if len(result) > 200:
            result = result[:200] + "..."
        print(f"✅ summarize_jira_csv: {result}")
    except Exception as e:
        print(f"❌ summarize_jira_csv: Error - {e}")
    print()

    # Test human approval tool
    print("🔧 Testing request_human_approval...")
    try:
        approval_test_string = "1. Set story points for PROJ-123 to 8.\n2. Assign PROJ-456 to 'Test User'."
        result = request_human_approval(approval_test_string)
        print(f"✅ request_human_approval: Returned '{result}'")
    except Exception as e:
        print(f"❌ request_human_approval: Error - {e}")
    print()


if __name__ == "__main__":
    test_bridge()
