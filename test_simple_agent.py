#!/usr/bin/env python3
"""
Non-interactive smoke test for the simple YAML agent.
"""

import os
import sys
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_simple_agent():
    """Test the simple agent with basic queries."""
    try:
        # Test MCP bridge first
        print("🔧 Testing MCP bridge...")
        try:
            from yaml_agent.mcp_bridge import call_mcp_tool
            result = call_mcp_tool("summarize_jira_csv", {})
            print(f"✅ MCP bridge working: {result[:100]}...")
        except Exception as e:
            print(f"❌ MCP bridge error: {e}")
            return False
        
        # Test search tool
        print("🔧 Testing search tool...")
        try:
            search_result = call_mcp_tool("search_jira_issues", {"search_term": "authentication"})
            print(f"✅ Search tool working: {search_result[:100]}...")
        except Exception as e:
            print(f"❌ Search tool error: {e}")
            return False
        
        # Test status breakdown tool
        print("🔧 Testing status breakdown tool...")
        try:
            status_result = call_mcp_tool("get_jira_status_breakdown", {})
            print(f"✅ Status breakdown working: {status_result[:100]}...")
        except Exception as e:
            print(f"❌ Status breakdown error: {e}")
            return False
        
        # Test assignee workload tool
        print("🔧 Testing assignee workload tool...")
        try:
            workload_result = call_mcp_tool("get_jira_assignee_workload", {})
            print(f"✅ Assignee workload working: {workload_result[:100]}...")
        except Exception as e:
            print(f"❌ Assignee workload error: {e}")
            return False
        
        print(f"\n🎉 All MCP tools are working correctly!")
        print("✅ The simple_agent.yaml configuration should work with the ADK CLI.")
        print("\nTo test the full agent interactively, run:")
        print("  python -m google.adk.cli run yaml_agent")
        print("  (Note: This expects yaml_agent to be a directory with __init__.py)")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure google-adk is properly installed.")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_simple_agent()
    sys.exit(0 if success else 1)
