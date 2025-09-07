"""
Main entry point for CRM Assistant.
Provides simple CRM agent for basic enrichment operations.
"""

from .coordinator import create_crm_simple_agent, create_crm_coordinator


def create_simple_crm_agent():
    """Create and return the simple CRM agent."""
    return create_crm_simple_agent()


# For ADK integration
def create_agent():
    """Create the default CRM agent for ADK (orchestration coordinator)."""
    coordinator = create_crm_coordinator()
    # Ensure a friendly startup greeting for interactive sessions
    if hasattr(coordinator, "instruction") and "How can I help you" not in coordinator.instruction:
        coordinator.instruction = coordinator.instruction.strip() + "\n\nGetting started: How can I help you?"
    return coordinator


if __name__ == "__main__":
    # For testing purposes
    agent = create_agent()
    print(f"Created CRM agent: {agent.name}")
    print(f"Description: {agent.description}")
