"""
Warning suppression utilities for ADK experimental features.
Suppresses the repetitive warnings about experimental features.
"""

import warnings
import logging


def suppress_adk_warnings():
    """
    Suppress ADK experimental warnings and other verbose warnings.
    Call this at the start of agent initialization to clean up output.
    """
    
    # Suppress specific UserWarnings from ADK experimental features
    warnings.filterwarnings(
        "ignore", 
        message=".*EXPERIMENTAL.*InMemoryCredentialService.*",
        category=UserWarning
    )
    
    warnings.filterwarnings(
        "ignore", 
        message=".*EXPERIMENTAL.*BaseCredentialService.*",
        category=UserWarning
    )
    
    warnings.filterwarnings(
        "ignore", 
        message=".*EXPERIMENTAL.*BaseAuthenticatedTool.*",
        category=UserWarning
    )
    
    # Suppress all ADK experimental warnings more broadly
    warnings.filterwarnings(
        "ignore",
        message=".*EXPERIMENTAL.*",
        category=UserWarning,
        module="google.adk.*"
    )
    
    # Also suppress at the logging level for ADK modules
    logging.getLogger("google.adk").setLevel(logging.ERROR)
    
    # Suppress MCP-related warnings
    warnings.filterwarnings(
        "ignore",
        category=UserWarning,
        module=".*mcp.*"
    )


def suppress_all_experimental_warnings():
    """
    More aggressive warning suppression for all experimental features.
    Use this if you want to suppress all experimental warnings system-wide.
    """
    warnings.filterwarnings(
        "ignore",
        message=".*experimental.*",
        category=UserWarning
    )
    
    warnings.filterwarnings(
        "ignore", 
        message=".*EXPERIMENTAL.*",
        category=UserWarning
    )


# Context manager for temporary warning suppression
class SuppressWarnings:
    """Context manager to temporarily suppress warnings."""
    
    def __init__(self, suppress_experimental=True, suppress_all=False):
        self.suppress_experimental = suppress_experimental
        self.suppress_all = suppress_all
        self.original_filters = None
        
    def __enter__(self):
        # Save original warning filters
        self.original_filters = warnings.filters.copy()
        
        if self.suppress_all:
            warnings.simplefilter("ignore")
        elif self.suppress_experimental:
            suppress_adk_warnings()
            
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore original warning filters
        warnings.filters[:] = self.original_filters

