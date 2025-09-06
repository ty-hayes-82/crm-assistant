"""CRM Assistant - Multi-agent system for CRM data enrichment and cleanup."""

from .coordinator import (
    create_crm_coordinator,
    create_crm_simple_agent,
    get_crm_agent
)

__version__ = "1.0.0"
__all__ = [
    "create_crm_coordinator",
    "create_crm_simple_agent", 
    "get_crm_agent"
]
