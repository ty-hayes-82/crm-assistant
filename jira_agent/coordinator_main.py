"""
Main entry point for the Jira Coordinator agent.
This file provides the programmatic agent that can be run with `adk run jira_agent.coordinator_main`
"""

# Suppress ADK experimental warnings at startup
from .utils.warning_suppression import suppress_adk_warnings
suppress_adk_warnings()

from .coordination.coordinator import create_jira_coordinator

# Create the coordinator agent for ADK to run
coordinator_agent = create_jira_coordinator()
