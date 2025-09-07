"""
Project Manager Agent Package

A2A compliant project management agent that orchestrates complex CRM tasks
by coordinating with specialized agents like the CRM Agent.
"""

from .coordinator import ProjectManagerAgent, create_project_manager
from .main import create_agent

__all__ = ["ProjectManagerAgent", "create_project_manager", "create_agent"]
