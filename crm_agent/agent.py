"""
ADK agent entry point for CRM Assistant.
This file exposes the root_agent for ADK to discover and run.
"""

from .main import create_agent

# ADK looks for root_agent in this module
root_agent = create_agent()
