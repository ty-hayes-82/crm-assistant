"""
Main entry point for CRM Assistant.
Provides simple CRM agent for basic enrichment operations.
"""

from .coordinator import create_crm_simple_agent


def create_simple_crm_agent():
    """Create and return the simple CRM agent."""
    return create_crm_simple_agent()


# For ADK integration
def create_agent():
    """Create the default CRM agent for ADK."""
    return create_simple_crm_agent()


if __name__ == "__main__":
    # For testing purposes
    agent = create_simple_crm_agent()
    print(f"Created CRM agent: {agent.name}")
    print(f"Description: {agent.description}")
