"""
Interactive Project Manager Agent Demo
Shows real-time A2A communication in chat format
"""

import sys
import os
import asyncio
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from project_manager_agent.interactive_coordinator import create_interactive_project_manager


async def main():
    """Run the interactive Project Manager Agent"""
    
    print("🚀 Starting Interactive Project Manager Agent...")
    print("This will show real-time A2A communication between agents.")
    print()
    
    # Create the interactive agent
    pm_agent = create_interactive_project_manager()
    
    # Start interactive session
    await pm_agent.start_interactive_session()


if __name__ == "__main__":
    # Run the interactive demo
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Session interrupted by user. Goodbye!")
