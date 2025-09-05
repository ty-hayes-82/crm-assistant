#!/usr/bin/env python3
"""
Test script to load and run the YAML agent directly.
"""

import os
import sys
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from google.adk.agents.config_loader import load_agent_config
    from google.adk.agents.agent_factory import create_agent
    
    # Load the agent configuration
    config_path = "yaml_agent/agent.yaml"
    
    print(f"Loading agent config from: {config_path}")
    
    # Check if file exists
    if not os.path.exists(config_path):
        print(f"Error: Config file {config_path} not found")
        sys.exit(1)
    
    # Load and create the agent
    config = load_agent_config(config_path)
    print(f"Config loaded successfully: {config.name}")
    
    agent = create_agent(config)
    print(f"Agent created successfully: {type(agent)}")
    
    # Try to run a simple interaction
    print("\n=== Agent Ready ===")
    print("You can now interact with the agent.")
    print("Type 'quit' or 'exit' to stop.")
    
    while True:
        user_input = input("\nUser: ").strip()
        if user_input.lower() in ['quit', 'exit']:
            break
        
        if user_input:
            try:
                response = agent.run(user_input)
                print(f"Agent: {response}")
            except Exception as e:
                print(f"Error: {e}")
                
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure google-adk is properly installed.")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
