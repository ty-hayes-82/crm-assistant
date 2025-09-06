"""
CRM Agent Factory with Registry Pattern.
Implements the registry pattern for CRM-specific agent management.
"""

from typing import Dict, Type, Callable, List, Any, Optional
from google.adk.agents import BaseAgent, LlmAgent


class AgentRegistry:
    """
    Registry for dynamic agent creation and management.
    Enables flexible agent composition and easy testing.
    """
    
    def __init__(self):
        self._agent_factories: Dict[str, Callable[..., BaseAgent]] = {}
        self._agent_metadata: Dict[str, Dict[str, Any]] = {}
    
    def register(self, name: str, factory: Callable[..., BaseAgent], metadata: Optional[Dict] = None):
        """
        Register an agent factory function.
        
        Args:
            name: Agent type name
            factory: Factory function that creates the agent
            metadata: Optional metadata about the agent
        """
        self._agent_factories[name] = factory
        self._agent_metadata[name] = metadata or {}
    
    def create_agent(self, name: str, **kwargs) -> BaseAgent:
        """
        Create an agent instance by name.
        
        Args:
            name: Agent type name
            **kwargs: Arguments passed to the agent factory
            
        Returns:
            Configured agent instance
            
        Raises:
            ValueError: If agent type is not registered
        """
        if name not in self._agent_factories:
            available = ", ".join(self.list_agents())
            raise ValueError(f"Unknown agent type: {name}. Available: {available}")
        
        return self._agent_factories[name](**kwargs)
    
    def list_agents(self) -> List[str]:
        """List all registered agent types."""
        return list(self._agent_factories.keys())
    
    def get_agent_metadata(self, name: str) -> Dict[str, Any]:
        """Get metadata for a specific agent type."""
        return self._agent_metadata.get(name, {})


class CRMAgentRegistry(AgentRegistry):
    """
    Registry for CRM-specific agent creation and management.
    Extends the base AgentRegistry with CRM-focused agents.
    """
    
    def __init__(self):
        super().__init__()
        self._register_crm_agents()
    
    def _register_crm_agents(self):
        """Register CRM-specific agents for data enrichment and cleanup."""
        
        # Import CRM agents
        from ..agents.specialized.crm_agents import (
            create_crm_query_builder,
            create_crm_web_retriever,
            create_crm_linkedin_retriever,
            create_crm_company_data_retriever,
            create_crm_email_verifier,
            create_crm_summarizer,
            create_crm_entity_resolver,
            create_crm_updater,
            create_crm_data_quality_agent
        )
        from ..agents.specialized.company_intelligence_agent import create_company_intelligence_agent
        from ..agents.specialized.contact_intelligence_agent import create_contact_intelligence_agent
        from ..agents.workflows.crm_enrichment import create_crm_workflows
        # Note: CRM data quality workflow is created in the CRM workflows module
        
        # Company Intelligence Agent
        self.register("company_intelligence", create_company_intelligence_agent, {
            "description": "Provides comprehensive company analysis and intelligence.",
            "domain": "company_intelligence",
            "tools": ["search_companies", "get_company_details", "generate_company_report", "web_search", "get_company_metadata"]
        })

        # Contact Intelligence Agent
        self.register("contact_intelligence", create_contact_intelligence_agent, {
            "description": "Provides comprehensive contact analysis and intelligence.",
            "domain": "contact_intelligence",
            "tools": ["search_contacts", "get_contact_details", "generate_contact_report", "web_search"]
        })

        # CRM Query Builder Agent
        self.register("crm_query_builder", create_crm_query_builder, {
            "description": "Crafts precise queries for web/LinkedIn/company sources from CRM gaps",
            "domain": "crm_query_planning",
            "tools": ["web_search", "fetch_url"]
        })
        
        # CRM Web Retriever Agent
        self.register("crm_web_retriever", create_crm_web_retriever, {
            "description": "Executes web searches and extracts candidate facts",
            "domain": "web_retrieval", 
            "tools": ["web_search", "fetch_url"]
        })
        
        # CRM LinkedIn Retriever Agent
        self.register("crm_linkedin_retriever", create_crm_linkedin_retriever, {
            "description": "Retrieves LinkedIn company/contact profile metadata",
            "domain": "linkedin_retrieval",
            "tools": ["linkedin_company_lookup", "web_search"]
        })
        
        # CRM Company Data Retriever Agent
        self.register("crm_company_data_retriever", create_crm_company_data_retriever, {
            "description": "Retrieves structured company data from external sources",
            "domain": "company_data_retrieval",
            "tools": ["get_company_metadata", "web_search"]
        })
        
        # CRM Email Verifier Agent
        self.register("crm_email_verifier", create_crm_email_verifier, {
            "description": "Validates email deliverability and assesses risk",
            "domain": "email_verification",
            "tools": ["verify_email"]
        })
        
        # CRM Summarizer Agent
        self.register("crm_summarizer", create_crm_summarizer, {
            "description": "Normalizes and deduplicates findings into concise summaries",
            "domain": "data_synthesis",
            "tools": []  # Uses session state data
        })
        
        # CRM Entity Resolution Agent
        self.register("crm_entity_resolver", create_crm_entity_resolver, {
            "description": "Maps findings to CRM objects and handles deduplication",
            "domain": "entity_resolution",
            "tools": []  # Uses session state data
        })
        
        # CRM Updater Agent
        self.register("crm_updater", create_crm_updater, {
            "description": "Prepares and applies updates to HubSpot CRM",
            "domain": "crm_updates",
            "tools": ["query_hubspot_crm", "get_hubspot_contact", "get_hubspot_company", "await_human_approval", "notify_slack"]
        })
        
        # CRM Data Quality Agent
        self.register("crm_data_quality", create_crm_data_quality_agent, {
            "description": "Validates CRM data quality and proposes improvements",
            "domain": "crm_data_quality",
            "tools": ["get_hubspot_contact", "get_hubspot_company"]
        })
        
        # CRM Workflows
        workflows = create_crm_workflows()
        
        # CRM Enrichment Pipeline
        def create_crm_enrichment_pipeline(**kwargs):
            return workflows["enrichment_pipeline"]
        
        self.register("crm_enrichment_pipeline", create_crm_enrichment_pipeline, {
            "description": "Complete CRM enrichment pipeline with gap detection, retrieval, synthesis, and updates",
            "domain": "crm_workflows",
            "tools": ["all_crm_tools"]
        })
        
        # CRM Parallel Retrieval
        def create_crm_parallel_retrieval(**kwargs):
            return workflows["parallel_retrieval"]
        
        self.register("crm_parallel_retrieval", create_crm_parallel_retrieval, {
            "description": "Parallel execution of web, LinkedIn, company data, and email verification",
            "domain": "crm_workflows",
            "tools": ["retrieval_tools"]
        })
        
        # CRM Quick Lookup
        def create_crm_quick_lookup(**kwargs):
            return workflows["quick_lookup"]
        
        self.register("crm_quick_lookup", create_crm_quick_lookup, {
            "description": "Quick CRM record lookup and summary generation",
            "domain": "crm_workflows",
            "tools": ["hubspot_tools"]
        })
        
        # Note: CRM Data Quality Workflow would be added here if needed


# Global CRM registry instance
crm_agent_registry = CRMAgentRegistry()


# Convenience functions for creating CRM agents
def create_crm_query_builder(**kwargs) -> BaseAgent:
    """Create a CRM QueryBuilder agent."""
    return crm_agent_registry.create_agent("crm_query_builder", **kwargs)


def create_crm_web_retriever(**kwargs) -> BaseAgent:
    """Create a CRM WebRetriever agent."""
    return crm_agent_registry.create_agent("crm_web_retriever", **kwargs)


def create_crm_enrichment_pipeline(**kwargs) -> BaseAgent:
    """Create a CRM Enrichment Pipeline workflow."""
    return crm_agent_registry.create_agent("crm_enrichment_pipeline", **kwargs)


def create_company_intelligence_agent(**kwargs) -> BaseAgent:
    """Create a Company Intelligence agent."""
    return crm_agent_registry.create_agent("company_intelligence", **kwargs)


def create_contact_intelligence_agent(**kwargs) -> BaseAgent:
    """Create a Contact Intelligence agent."""
    return crm_agent_registry.create_agent("contact_intelligence", **kwargs)


# Export the main CRM agent creation function
def get_crm_agent(agent_type: str, **kwargs) -> BaseAgent:
    """
    Main function to get a CRM agent of the specified type.
    
    Args:
        agent_type: Type of CRM agent (see crm_agent_registry.list_agents())
        **kwargs: Additional arguments for agent creation
        
    Returns:
        Configured CRM agent
    """
    return crm_agent_registry.create_agent(agent_type, **kwargs)
