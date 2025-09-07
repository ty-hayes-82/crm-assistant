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

    print("\nEnter your questions for the CRM Coordinator below (type 'exit' to quit).")
    while True:
        try:
            question = input("> ")
            if question.lower() == 'exit':
                break
            if question:
                response = coordinator.run(question)
                print("\nAssistant:")
                print(response)
                print("-" * 20)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"An error occurred: {e}")
            break
    print("\nExiting CRM Coordinator.")