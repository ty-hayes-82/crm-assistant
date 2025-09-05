#!/usr/bin/env python3
"""
Simple script to run the YAML agent.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from google.adk.cli import main

if __name__ == "__main__":
    # Set up arguments for the CLI
    sys.argv = ["run_agent.py", "run", "yaml_agent"]
    main()
