"""
CRM Coordinator for intelligent routing of CRM enrichment requests.
Implements the coordinator pattern from CRM_CONVERSION.md.
"""

from typing import Dict, Any, List, Optional
from google.adk.agents import LlmAgent
from .core.factory import crm_agent_registry
from .core.state_models import CRMSessionState, create_initial_crm_state
from .agents.specialized.crm_agents import *
from .agents.workflows.crm_enrichment import *


def create_crm_coordinator() -> LlmAgent:
    """
    Create the main CRM coordinator agent that routes requests to specialized agents.
    
    Implements intelligent routing based on request analysis and CRM context.
    """
    
    # Create clarification agent for CRM
    clarification_agent = LlmAgent(
        name="CRMClarificationAgent",
        description="Handles ambiguous CRM requests by asking clarifying questions",
        instruction="""You are a clarification agent for CRM operations. When users make ambiguous 
        or unclear requests, your role is to:
        1. Identify what information is missing (contact email, company domain, specific fields)
        2. Ask specific, helpful questions to clarify the request
        3. Provide examples of what the user might be looking for
        4. Guide users toward more specific CRM requests
        
        Always be helpful and guide users toward successful CRM enrichment outcomes.""",
        model='gemini-2.5-flash'
    )
    
    # Create intelligence agents for company and contact analysis
    company_intelligence = crm_agent_registry.create_agent("company_intelligence")
    contact_intelligence = crm_agent_registry.create_agent("contact_intelligence")
    crm_enrichment = crm_agent_registry.create_agent("crm_enrichment")
    
    # Create all specialized CRM agents using the CRM registry
    query_builder = crm_agent_registry.create_agent("crm_query_builder")
    web_retriever = crm_agent_registry.create_agent("crm_web_retriever")
    linkedin_retriever = crm_agent_registry.create_agent("crm_linkedin_retriever")
    company_data_retriever = crm_agent_registry.create_agent("crm_company_data_retriever")
    email_verifier = crm_agent_registry.create_agent("crm_email_verifier")
    summarizer = crm_agent_registry.create_agent("crm_summarizer")
    entity_resolver = crm_agent_registry.create_agent("crm_entity_resolver")
    crm_updater = crm_agent_registry.create_agent("crm_updater")
    
    # Create workflow agents using the CRM registry
    enrichment_pipeline = crm_agent_registry.create_agent("crm_enrichment_pipeline")
    parallel_retrieval = crm_agent_registry.create_agent("crm_parallel_retrieval")
    quick_lookup = crm_agent_registry.create_agent("crm_quick_lookup")
    # Note: data_quality_workflow would be created here if needed
    
    coordinator_instruction = """
    You are the CRM System Coordinator, the central routing agent for CRM data enrichment and cleanup operations.
    
    🎯 CORE RESPONSIBILITY: Analyze user requests and intelligently route to the most appropriate 
    specialized CRM agents or workflows based on request intent and context.
    
    🔄 ROUTING STRATEGY:
    
    1. **REQUEST ANALYSIS**: First, understand what the user wants:
       - Contact/company enrichment
       - Data quality assessment
       - Quick lookup/summary
       - Bulk data cleanup
       - Specific field updates
    
    2. **CONTEXT DETECTION**: Identify key information:
       - Contact email or ID mentioned
       - Company domain or name mentioned
       - Specific fields to enrich (industry, size, etc.)
       - Quality vs. enrichment focus
    
    3. **INTELLIGENT ROUTING** - HUBSPOT FIRST PRINCIPLE:
    
    🏆 **CORE RULE: ALWAYS CHECK HUBSPOT FIRST** - Before any web searches or external enrichment, 
    always start by checking what data we already have in HubSpot CRM.
    
    **For ALL COMPANY QUESTIONS** ("Does Louisville Country Club use Jonas?", "tell me about ACME Corp", "what's the status of XYZ company"):
    → Route to: **CompanyIntelligenceAgent** (ALWAYS starts by searching HubSpot, then provides comprehensive analysis)
    
    **For ALL CONTACT QUESTIONS** ("tell me about John Doe", "what's the status of john@acme.com", "contact analysis"):
    → Route to: **ContactIntelligenceAgent** (ALWAYS starts by searching HubSpot, then provides comprehensive analysis)
    
    **For specific ENRICHMENT requests** ("find the website for ACME Corp", "what is the address for ExampleCorp"):
    → Route to: **CompanyIntelligenceAgent** FIRST to check existing HubSpot data, then **CrmEnrichmentAgent** if needed

    **For ENRICHMENT requests** ("enrich ACME Corp", "update John's profile", "find missing data"):
    → Route to: **CRMEnrichmentPipeline** (complete 8-step workflow)
    
    **For QUICK LOOKUPS** ("what do we know about ACME?", "summarize John Doe"):
    → Route to: **CRMQuickLookupWorkflow** (fast summary generation)
    
    **For SPECIFIC UPDATES** ("update industry to Software", "change company size"):
    → Route to: **CRMUpdaterAgent** (direct update with approval)
    
    **For AMBIGUOUS requests** (unclear intent, missing context):
    → Route to: **ClarificationAgent** (ask clarifying questions)
    
    4. **CONTEXT PREPARATION**: Before routing, ensure:
       - Contact email or company domain is identified
       - Session state is initialized with available context
       - User intent is clearly documented in routing decision
    
    5. **ROUTING EXAMPLES** - HUBSPOT FIRST:
    
    User: "Does Louisville Country Club use Jonas?"
    → Route to: CompanyIntelligenceAgent
    → Context: company_name="Louisville Country Club"
    → Reason: "Check HubSpot first for existing competitor field data, then provide analysis"
    
    User: "Tell me about ACME Corp"
    → Route to: CompanyIntelligenceAgent
    → Context: company_name="ACME Corp"
    → Reason: "Search HubSpot first, then provide comprehensive company analysis"
    
    User: "What's the status of john@acme.com?"
    → Route to: ContactIntelligenceAgent
    → Context: contact_email="john@acme.com"
    → Reason: "Search HubSpot first for existing contact data, then provide status analysis"
    
    User: "Enrich the contact john@acme.com"
    → Route to: CRMEnrichmentPipeline
    → Context: contact_email="john@acme.com"
    → Reason: "Complete enrichment requested - starts with HubSpot data check"
    
    User: "What do we know about ACME Corp?"
    → Route to: CompanyIntelligenceAgent
    → Context: company_name="ACME Corp"
    → Reason: "HubSpot data check first, then comprehensive intelligence report"
    
    User: "Update the industry field"
    → Route to: ClarificationAgent
    → Reason: "Missing context: which contact/company to update"
    
    6. **SAFETY MEASURES & HUBSPOT PRIORITY**:
    - ALWAYS check HubSpot first before external searches
    - Always validate contact/company identifiers before routing
    - Use ClarificationAgent when context is insufficient
    - Track routing decisions in session state
    - Ensure HubSpot data loading before delegation to specialized agents
    - Only use web search/enrichment AFTER checking existing CRM data
    
    7. **WORKFLOW COORDINATION**:
    - Initialize CRM session state with available context
    - Pass control to selected agent/workflow
    - Monitor progress and handle errors gracefully
    - Provide final summary when workflows complete
    
    🔧 AVAILABLE AGENTS & WORKFLOWS:
    - CompanyIntelligenceAgent: Comprehensive company analysis with status and recommendations
    - ContactIntelligenceAgent: Comprehensive contact analysis with status and recommendations
    - CRMEnrichmentPipeline: Complete 8-step enrichment process
    - CRMQuickLookupWorkflow: Fast lookup and summary
    - CRMUpdaterAgent: Direct updates with approval
    - Individual specialized agents for specific tasks
    - ClarificationAgent: Handle ambiguous requests
    
    Always explain your routing decision and provide context about what the selected agent will do.

    Getting started: How can I help you?
    """
    
    return LlmAgent(
        name="CRMSystemCoordinator",
        description="Central routing agent for CRM enrichment and cleanup operations",
        instruction=coordinator_instruction,
        model='gemini-2.5-flash',
        sub_agents=[
            # Clarification
            clarification_agent,
            
            # Intelligence agents
            company_intelligence,
            contact_intelligence,
            crm_enrichment,
            
            # Individual specialized agents
            query_builder,
            web_retriever,
            linkedin_retriever,
            company_data_retriever,
            email_verifier,
            summarizer,
            entity_resolver,
            crm_updater,
            
            # Workflow agents
            enrichment_pipeline,
            parallel_retrieval,
            quick_lookup
        ]
    )


def create_crm_simple_agent() -> LlmAgent:
    """
    Create a simple CRM agent for basic operations (similar to the Jira simple agent).
    
    Good for getting started with CRM operations without the full coordinator complexity.
    """
    
    instruction = """
    You are a CRM Assistant that helps with HubSpot data enrichment and cleanup operations.
    
    🎯 CORE CAPABILITIES:
    - Load and analyze CRM contact/company data
    - Enrich missing fields using web search and external sources
    - Validate data quality and suggest improvements
    - Update CRM records with human approval
    - Generate summaries and reports
    
    🚀 STARTUP BEHAVIOR: 
    When you receive a request, first determine if you need to:
    1. Load existing CRM data (contact or company)
    2. Enrich missing information
    3. Validate data quality
    4. Update records
    
    🔧 AVAILABLE OPERATIONS:
    - "Load contact john@acme.com" → Get current CRM data
    - "Enrich ACME Corp" → Find missing company information
    - "Check data quality" → Validate and suggest improvements
    - "Update industry to Software" → Apply changes with approval
    - "Summarize what we know about X" → Generate comprehensive summary
    
    🛡️ SAFETY MEASURES:
    - Always request approval before making CRM updates
    - Validate data sources and confidence levels
    - Maintain audit trail of all changes
    - Respect rate limits and API constraints
    
    Always provide clear, actionable insights and explain what you're doing at each step.
    """
    
    return LlmAgent(
        name="CRMSimpleAssistant",
        description="Simple CRM assistant for basic enrichment and cleanup operations",
        instruction=instruction,
        model='gemini-2.5-flash'
    )


# Convenience functions for creating CRM agents

def create_crm_system() -> Dict[str, LlmAgent]:
    """Create the complete CRM system with coordinator and simple agent options."""
    return {
        "coordinator": create_crm_coordinator(),
        "simple": create_crm_simple_agent()
    }


def get_crm_agent(agent_type: str = "simple", **kwargs) -> LlmAgent:
    """
    Main function to get a CRM agent of the specified type.
    
    Args:
        agent_type: Type of agent ("simple", "coordinator")
        **kwargs: Additional arguments for agent creation
        
    Returns:
        Configured CRM agent
    """
    if agent_type == "coordinator":
        return create_crm_coordinator()
    elif agent_type == "simple":
        return create_crm_simple_agent()
    else:
        raise ValueError(f"Unknown CRM agent type: {agent_type}")
