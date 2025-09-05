#!/usr/bin/env python3
"""
Local client to interact with the Jira CSV MCP server directly.
This allows you to test the server without Claude for Desktop.
"""

import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_mcp_tools():
    """Test the MCP tools directly."""
    
    # Create a client session using stdio to communicate with the server
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "mcp_toolbox.main"],
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the session
            await session.initialize()
            
            print("🚀 Connected to MCP Server!")
            print("=" * 50)
            
            # List available tools
            tools_result = await session.list_tools()
            print(f"📋 Available Tools ({len(tools_result.tools)}):")
            for tool in tools_result.tools:
                print(f"  • {tool.name}: {tool.description}")
            print()
            
            # Test each tool
            test_cases = [
                {
                    "name": "summarize_jira_csv",
                    "args": {},
                    "description": "Getting Jira CSV summary"
                },
                {
                    "name": "get_jira_status_breakdown", 
                    "args": {},
                    "description": "Getting status breakdown"
                },
                {
                    "name": "get_jira_assignee_workload",
                    "args": {"top_n": 5},
                    "description": "Getting top 5 assignees"
                },
                {
                    "name": "search_jira_issues",
                    "args": {"search_term": "data"},
                    "description": "Searching for 'data' issues"
                },
                {
                    "name": "list_jira_epics",
                    "args": {"top_n": 5},
                    "description": "Listing epics"
                },
                {
                    "name": "audit_jira_field_completeness",
                    "args": {},
                    "description": "Auditing global field completeness"
                },
                {
                    "name": "get_recent_progress",
                    "args": {"days": 14, "top_n": 10},
                    "description": "Getting recent progress (14 days)"
                },
                # Epic deep-dive smoke tests (using a sample epic key expected in the CSV)
                {
                    "name": "get_epic_health",
                    "args": {"epic_key": "BI-607"},
                    "description": "Epic health for BI-607"
                },
                {
                    "name": "list_epic_children",
                    "args": {"epic_key": "BI-607", "top_n": 10},
                    "description": "List children for BI-607"
                },
                {
                    "name": "audit_epic_gaps",
                    "args": {"epic_key": "BI-607"},
                    "description": "Audit field gaps for BI-607"
                },
                {
                    "name": "get_epic_recent_progress",
                    "args": {"epic_key": "BI-607", "days": 30, "top_n": 10},
                    "description": "Recent progress for BI-607"
                },
                {
                    "name": "get_issue_full_details",
                    "args": {"issue_key": "BI-726"},
                    "description": "Issue full details for BI-726"
                },
            ]
            
            for test_case in test_cases:
                print(f"🔧 {test_case['description']}...")
                print("-" * 30)
                
                try:
                    result = await session.call_tool(
                        test_case["name"],
                        test_case["args"]
                    )
                    
                    # Print result content (truncate if too long)
                    content = result.content[0].text if result.content else "No content"
                    if len(content) > 500:
                        content = content[:500] + "..."
                    
                    print(content)
                    print("✅ Success!")
                    
                except Exception as e:
                    print(f"❌ Error: {e}")
                
                print()

def run_interactive_mode():
    """Run an interactive mode where user can call tools manually."""
    print("🎯 Interactive MCP Client")
    print("=" * 50)
    print("Available commands:")
    print("  1. summary     - Get CSV summary")
    print("  2. status      - Get status breakdown") 
    print("  3. projects    - Get project breakdown")
    print("  4. priorities  - Get priority breakdown")
    print("  5. workload    - Get assignee workload")
    print("  6. search      - Search issues")
    print("  7. test        - Run all tests")
    print("  8. quit        - Exit")
    print()
    
    async def interactive_session():
        server_params = StdioServerParameters(
            command="python",
            args=["-m", "mcp_toolbox.main"],
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                print("🚀 Connected to MCP Server!")
                
                while True:
                    try:
                        choice = input("\nEnter command (1-8): ").strip()
                        
                        if choice == "8" or choice.lower() == "quit":
                            print("👋 Goodbye!")
                            break
                        elif choice == "7" or choice.lower() == "test":
                            print("🧪 Running all tests...")
                            await test_mcp_tools()
                            continue
                        
                        tool_map = {
                            "1": ("summarize_jira_csv", {}),
                            "2": ("get_jira_status_breakdown", {}),
                            "3": ("get_jira_project_breakdown", {}),
                            "4": ("get_jira_priority_breakdown", {}),
                            "5": ("get_jira_assignee_workload", {"top_n": 10}),
                            "6": ("search_jira_issues", {"search_term": input("Enter search term: ").strip()}),
                        }
                        
                        if choice in tool_map:
                            tool_name, args = tool_map[choice]
                            
                            if choice == "5":  # workload
                                try:
                                    top_n = int(input("How many top assignees? (default 10): ").strip() or "10")
                                    args["top_n"] = top_n
                                except ValueError:
                                    args["top_n"] = 10
                            
                            print(f"\n🔧 Calling {tool_name}...")
                            result = await session.call_tool(tool_name, args)
                            content = result.content[0].text if result.content else "No content"
                            print("\n" + "="*50)
                            print(content)
                            print("="*50)
                        else:
                            print("❌ Invalid choice. Please enter 1-8.")
                    
                    except KeyboardInterrupt:
                        print("\n👋 Goodbye!")
                        break
                    except Exception as e:
                        print(f"❌ Error: {e}")
    
    return asyncio.run(interactive_session())

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        # Interactive mode
        run_interactive_mode()
    else:
        # Test mode
        print("🧪 Testing MCP Tools (use --interactive for interactive mode)")
        asyncio.run(test_mcp_tools()) 