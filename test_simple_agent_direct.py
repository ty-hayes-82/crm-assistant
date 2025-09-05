#!/usr/bin/env python3
"""
Direct test script to load and run the simple agent using correct ADK imports.
"""

import os
import sys
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from google.adk.agents import LlmAgent
    from google.adk import Agent, Runner
    import yaml
    
    # Load the agent configuration manually
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
    print(f"Agent class: {config['agent_class']}")
    print(f"Model: {config['model']}")
    print(f"Number of tools: {len(config.get('tools', []))}")
    
    # Try to create the agent directly
    # Since the YAML structure defines Python tools, we need to import the bridge
    from yaml_agent.mcp_bridge import call_mcp_tool, request_human_approval
    
    # Create a simple agent instance
    agent = LlmAgent(
        name=config['name'],
        model=config['model'],
        instruction=config['instruction']
    )
    
    print(f"Agent created successfully: {type(agent)}")
    
    # Test basic functionality using Runner
    print("\n=== Testing Agent with Runner ===")
    print("Testing basic agent response...")
    
    try:
        runner = Runner()
        response = runner.run(agent, "Hello, can you tell me about your capabilities?")
        print(f"Agent response: {response}")
    except Exception as e:
        print(f"Error testing agent: {e}")
        import traceback
        traceback.print_exc()
    
    # Test MCP bridge directly
    print("\n=== Testing MCP Bridge ===")
    try:
        result = call_mcp_tool("summarize_jira_csv", {})
        print(f"MCP Bridge test successful: {result[:200]}...")
    except Exception as e:
        print(f"MCP Bridge test failed: {e}")
        import traceback
        traceback.print_exc()
        
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure google-adk is properly installed.")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
