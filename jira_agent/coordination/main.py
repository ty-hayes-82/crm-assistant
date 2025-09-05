"""
Simple Jira agent using the new ADK foundation.
This maintains backward compatibility while leveraging the new agent factory.
"""

# Suppress ADK experimental warnings at startup
from ..utils.warning_suppression import suppress_adk_warnings
suppress_adk_warnings()

from ..core.factory import create_simple_agent

# Create the root agent using the factory
root_agent = create_simple_agent()
