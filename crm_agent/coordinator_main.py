"""
Main entry point for CRM Coordinator.
Provides the full multi-agent coordinator for advanced CRM operations.
"""

from .coordinator import create_crm_coordinator


def create_crm_coordinator_agent():
    """Create and return the CRM coordinator agent."""
    return create_crm_coordinator()


# For ADK integration
def create_agent():
    """Create the CRM coordinator agent for ADK."""
    return create_crm_coordinator_agent()


if __name__ == "__main__":
    # For testing purposes
    coordinator = create_crm_coordinator_agent()
    print(f"Created CRM coordinator: {coordinator.name}")
    print(f"Description: {coordinator.description}")
    print(f"Sub-agents: {len(coordinator.sub_agents)}")
    
    # List available sub-agents
    print("\nAvailable sub-agents:")
    for agent in coordinator.sub_agents:
        print(f"  - {agent.name}: {getattr(agent, 'description', 'No description')}")
