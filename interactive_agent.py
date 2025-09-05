#!/usr/bin/env python3
"""
Interactive interface for the Jira assistant agent.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from google.adk.agents import LlmAgent
    from google.adk.tools import FunctionTool
    import yaml
    
    # Import our MCP bridge functions
    from yaml_agent.mcp_bridge import call_mcp_tool, request_human_approval
    
    def create_agent():
        """Create and configure the Jira assistant agent."""
        # Load the agent configuration
        config_path = "yaml_agent/agent.yaml"
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Create function tools for each MCP tool
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
        tools = [
            FunctionTool(summarize_jira_csv),
            FunctionTool(search_jira_issues),
            FunctionTool(get_jira_status_breakdown),
            FunctionTool(get_jira_assignee_workload)
        ]
        
        # Create the agent with tools
        agent = LlmAgent(
            name=config['name'],
            model=config['model'],
            instruction=config['instruction'],
            tools=tools
        )
        
        return agent
    
    async def run_agent_async(agent, user_input):
        """Run the agent asynchronously with user input."""
        try:
            response_parts = []
            async for chunk in agent.run_async(user_input):
                if hasattr(chunk, 'text'):
                    response_parts.append(chunk.text)
                elif hasattr(chunk, 'content'):
                    response_parts.append(str(chunk.content))
                else:
                    response_parts.append(str(chunk))
            return ''.join(response_parts)
        except Exception as e:
            return f"Error: {str(e)}"
    
    def main():
        """Main interactive loop."""
        print("🤖 Jira Assistant Agent")
        print("=" * 50)
        
        # Create the agent
        print("Initializing agent...")
        try:
            agent = create_agent()
            print(f"✅ Agent '{agent.name}' loaded successfully with {len(agent.tools)} tools")
        except Exception as e:
            print(f"❌ Failed to create agent: {e}")
            return
        
        print("\n📋 Available capabilities:")
        print("• Summarize Jira CSV data")
        print("• Get status breakdowns") 
        print("• Search for specific issues")
        print("• Generate workload reports")
        print("\n💡 Try asking: 'Can you summarize the Jira data?' or 'What is the status breakdown?'")
        print("\nType 'quit' or 'exit' to stop.\n")
        
        # Interactive loop
        while True:
            try:
                user_input = input("👤 You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                if not user_input:
                    continue
                
                print("🤖 Agent: Thinking...")
                
                # Run the agent
                response = asyncio.run(run_agent_async(agent, user_input))
                print(f"🤖 Agent: {response}\n")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}\n")
    
    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure google-adk is properly installed.")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
