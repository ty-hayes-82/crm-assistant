"""
CRM Agent Factory with Registry Pattern.
Implements the registry pattern for CRM-specific agent management.
"""

from typing import Dict, Type, Callable, List, Any, Optional
from google.adk.agents import BaseAgent, LlmAgent
import os

try:
    from google.adk.tools import OpenApiTool
    OPENAPI_AVAILABLE = True
except ImportError:
    OpenApiTool = None
    OPENAPI_AVAILABLE = False


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
        )
        from ..agents.specialized.company_intelligence_agent import create_company_intelligence_agent
        from ..agents.specialized.outreach_personalizer_agent import create_outreach_personalizer_agent
        from ..agents.specialized.contact_intelligence_agent import create_contact_intelligence_agent
        from ..agents.specialized.crm_enrichment_agent import create_agent as create_crm_enrichment_agent
        from ..agents.specialized.field_enrichment_manager_agent import FieldEnrichmentManagerAgent
        from ..agents.specialized.company_llm_enrichment_agent import create_company_llm_enrichment_agent
        from ..agents.specialized.company_competitor_agent import create_company_competitor_agent
        from ..agents.specialized.company_management_agent import create_company_management_agent
        from ..agents.specialized.field_mapping_agent import create_field_mapping_agent
        from ..agents.specialized.lead_scoring_agent import create_lead_scoring_agent
        # Note: CRM data quality workflow is created in the CRM workflows module
        
        # Crm Enrichment Agent
        self.register("crm_enrichment", create_crm_enrichment_agent, {
            "description": "Enriches CRM data by filling in gaps using grounded web searches.",
            "domain": "crm_data_enrichment",
            "tools": ["web_search", "fetch_url"]
        })

        # Company Intelligence Agent
        self.register("company_intelligence", create_company_intelligence_agent, {
            "description": "Provides comprehensive company analysis and intelligence.",
            "domain": "company_intelligence",
            "tools": ["search_companies", "get_company_details", "generate_company_report", "web_search", "get_company_metadata"]
        })

        # Contact Intelligence Agent
        self.register("contact_intelligence", create_contact_intelligence_agent, {
            "description": "Provides comprehensive analysis of contacts",
            "capabilities": ["Contact analysis", "Relationship mapping", "Data enrichment"]
        })

        # Field Enrichment Manager Agent
        self.register("field_enrichment_manager", lambda **kwargs: FieldEnrichmentManagerAgent(**kwargs), {
            "description": "Manages systematic field enrichment, validation, and quality improvement for top 10 Swoop sales fields",
            "domain": "field_enrichment_management",
            "tools": ["search_companies", "search_contacts", "generate_company_report", "generate_contact_report", "web_search", "get_company_metadata"]
        })

        # Company LLM Enrichment Agent
        self.register("company_llm_enrichment", create_company_llm_enrichment_agent, {
            "description": "Provides LLM-powered data enrichment for companies",
            "capabilities": ["Company data enrichment", "LLM-based analysis", "Web scraping"]
        })

        # Company Competitor Agent
        self.register("company_competitor", create_company_competitor_agent, {
            "description": "Identifies competitors for a given company.",
            "capabilities": ["Competitor analysis", "Company data enrichment"]
        })

        # Company Management Agent
        self.register("company_management_enrichment", create_company_management_agent, {
            "description": "Identifies and sets the management company for golf courses.",
            "capabilities": ["Company data enrichment", "Fuzzy matching"]
        })

        # Field Mapping Agent
        self.register("field_mapping", create_field_mapping_agent, {
            "description": "Maps field names to correct HubSpot internal names using field profiles.",
            "capabilities": ["Field name mapping", "HubSpot property identification", "Fuzzy matching"]
        })

        # Lead Scoring Agent (Phase 6)
        self.register("lead_scoring", create_lead_scoring_agent, {
            "description": "Computes Fit and Intent scores for leads and writes swoop_fit_score, swoop_intent_score, swoop_total_lead_score.",
            "domain": "lead_scoring",
            "tools": ["get_hubspot_contact", "get_hubspot_company", "update_company", "update_contact"]
        })

        # Outreach Personalizer Agent (Phase 7)
        self.register("outreach_personalizer", create_outreach_personalizer_agent, {
            "description": "Generates grounded, role-aware outreach drafts and creates Email/Task engagements in HubSpot.",
            "domain": "outreach_personalization",
            "tools": ["get_hubspot_contact", "get_hubspot_company", "create_email_engagement", "create_task"]
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
        
        # CRM Workflows - Import workflow creation functions
        from ..agents.workflows.crm_enrichment import (
            create_crm_enrichment_pipeline,
            create_crm_parallel_retrieval_workflow,
            create_crm_quick_lookup_workflow,
        )
        
        # CRM Enrichment Pipeline
        self.register("crm_enrichment_pipeline", create_crm_enrichment_pipeline, {
            "description": "Complete CRM enrichment pipeline with gap detection, retrieval, synthesis, and updates",
            "domain": "crm_workflows",
            "tools": ["hubspot_tools"]
        })
        
        # CRM Parallel Retrieval
        self.register("crm_parallel_retrieval", create_crm_parallel_retrieval_workflow, {
            "description": "Parallel execution of web, LinkedIn, company data, and email verification",
            "domain": "crm_workflows",
            "tools": ["retrieval_tools"]
        })
        
        # CRM Quick Lookup
        self.register("crm_quick_lookup", create_crm_quick_lookup_workflow, {
            "description": "Quick CRM record lookup and summary generation",
            "domain": "crm_workflows",
            "tools": ["hubspot_tools"]
        })
        
        # Field Enrichment Workflows
        from ..agents.workflows.field_enrichment_workflow import (
            create_field_enrichment_workflow,
        )
        
        # Comprehensive Field Enrichment Workflow
        self.register("field_enrichment_workflow", create_field_enrichment_workflow, {
            "description": "Complete field enrichment workflow combining sequential, parallel, and loop patterns",
            "domain": "field_enrichment_workflows",
            "tools": ["all_enrichment_tools"]
        })
        


# Global CRM registry instance
crm_agent_registry = CRMAgentRegistry()


def create_hubspot_openapi_tool():
    """
    Create HubSpot OpenAPI tool for Phase 3 implementation.
    Uses environment variables for authentication.
    """
    if not OPENAPI_AVAILABLE or OpenApiTool is None:
        raise ImportError("OpenApiTool not available in this environment")
    
    hubspot_token = os.getenv('PRIVATE_APP_ACCESS_TOKEN')
    if not hubspot_token:
        # Try alternative env var names
        hubspot_token = os.getenv('HUBSPOT_TOKEN') or os.getenv('HUBSPOT_ACCESS_TOKEN')
    
    if not hubspot_token:
        raise ValueError("HubSpot access token not found. Set PRIVATE_APP_ACCESS_TOKEN environment variable.")
    
    # Create OpenAPI tool for HubSpot CRM v3 API
    # Note: In production, you'd use the full HubSpot OpenAPI spec URL
    # For now, we'll create a minimal tool configuration
    hubspot_tool = OpenApiTool(
        name="hubspot_crm_api",
        description="HubSpot CRM API tool for Companies, Contacts, Associations, Emails, and Tasks",
        # In a full implementation, this would be the HubSpot OpenAPI spec URL
        # spec_url="https://api.hubspot.com/api-catalog-public/v1/apis/crm/v3/openapi.json",
        base_url="https://api.hubapi.com",
        auth={
            "type": "bearer",
            "token": hubspot_token
        },
        # Define key endpoints manually for Phase 3
        endpoints=[
            {
                "path": "/crm/v3/objects/companies/{companyId}",
                "method": "PATCH",
                "operation_id": "update_company",
                "description": "Update a company record",
                "parameters": [
                    {"name": "companyId", "in": "path", "required": True, "type": "string"}
                ],
                "request_body": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "properties": {
                                        "type": "object",
                                        "description": "Company properties to update"
                                    }
                                }
                            }
                        }
                    }
                }
            },
            {
                "path": "/crm/v3/objects/contacts/{contactId}",
                "method": "PATCH", 
                "operation_id": "update_contact",
                "description": "Update a contact record",
                "parameters": [
                    {"name": "contactId", "in": "path", "required": True, "type": "string"}
                ],
                "request_body": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "properties": {
                                        "type": "object",
                                        "description": "Contact properties to update"
                                    }
                                }
                            }
                        }
                    }
                }
            },
            {
                "path": "/crm/v3/objects/companies/{companyId}",
                "method": "GET",
                "operation_id": "get_company",
                "description": "Get a company record",
                "parameters": [
                    {"name": "companyId", "in": "path", "required": True, "type": "string"},
                    {"name": "properties", "in": "query", "required": False, "type": "string"}
                ]
            },
            {
                "path": "/crm/v3/objects/contacts/{contactId}",
                "method": "GET",
                "operation_id": "get_contact", 
                "description": "Get a contact record",
                "parameters": [
                    {"name": "contactId", "in": "path", "required": True, "type": "string"},
                    {"name": "properties", "in": "query", "required": False, "type": "string"}
                ]
            }
        ]
    )
    
    return hubspot_tool


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


def create_crm_enrichment_agent(**kwargs) -> BaseAgent:
    """Create a CRM Enrichment agent."""
    return crm_agent_registry.create_agent("crm_enrichment", **kwargs)


def create_field_enrichment_manager_agent(**kwargs) -> BaseAgent:
    """Create a Field Enrichment Manager agent."""
    return crm_agent_registry.create_agent("field_enrichment_manager", **kwargs)


def create_company_competitor_agent(**kwargs) -> BaseAgent:
    """Create a Company Competitor agent."""
    return crm_agent_registry.create_agent("company_competitor", **kwargs)


def create_company_llm_enrichment_agent(**kwargs) -> BaseAgent:
    """Create a Company LLM Enrichment agent."""
    return crm_agent_registry.create_agent("company_llm_enrichment", **kwargs)


def create_company_management_agent(**kwargs) -> BaseAgent:
    """Create a Company Management agent."""
    return crm_agent_registry.create_agent("company_management_enrichment", **kwargs)


def create_lead_scoring_agent(**kwargs) -> BaseAgent:
    """Create a Lead Scoring agent."""
    return crm_agent_registry.create_agent("lead_scoring", **kwargs)


def create_outreach_personalizer_agent(**kwargs) -> BaseAgent:
    """Create an Outreach Personalizer agent."""
    return crm_agent_registry.create_agent("outreach_personalizer", **kwargs)


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
