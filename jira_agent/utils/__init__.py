"""
Utility functions for Jira agent system.
"""

from .warning_suppression import suppress_adk_warnings

# Automatically suppress warnings when this module is imported
suppress_adk_warnings()

__all__ = ['suppress_adk_warnings']