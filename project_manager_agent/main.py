"""
Main entry point for Project Manager Agent.
Creates the main orchestration agent that coordinates with CRM agents.
"""

from .coordinator import create_project_manager


def create_agent():
    """Create the default Project Manager agent for ADK."""
    manager = create_project_manager()
    # Ensure a friendly startup greeting for interactive sessions
    if hasattr(manager, "instruction") and "How can I help you" not in manager.instruction:
        manager.instruction = manager.instruction.strip() + "\n\nGetting started: How can I help you with your CRM project goals?"
    return manager


if __name__ == "__main__":
    # For testing purposes
    agent = create_agent()
    print(f"Created Project Manager agent: {agent.name}")
    print(f"Description: {getattr(agent, 'description', 'N/A')}")
