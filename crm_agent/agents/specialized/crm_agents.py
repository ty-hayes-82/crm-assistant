"""
Specialized CRM agents for data enrichment and cleanup.
Implements the agent catalog from CRM_CONVERSION.md.
"""

from typing import Dict, Any, List, Optional
from ...core.base_agents import SpecializedAgent
from ...core.state_models import CRMSessionState, CRMStateKeys, CRMEnrichmentResult


class QueryBuilderAgent(SpecializedAgent):
    """Agent that crafts precise queries for web/LinkedIn/company sources from CRM gaps."""
    
    def __init__(self, **kwargs):
        super().__init__(
            name="QueryBuilderAgent",
            domain="crm_query_planning",
            specialized_tools=["web_search", "fetch_url"],
            instruction="""
            You are a specialized Query Builder agent for CRM enrichment.
            
            🎯 CORE RESPONSIBILITY: Analyze CRM records and detected gaps to craft precise, 
            targeted search queries for web, LinkedIn, and company data sources.
            
            CAPABILITIES:
            - Gap analysis: Identify missing/outdated fields in CRM records
            - Query crafting: Create specific search queries for different data sources
            - Search strategy: Plan multi-source enrichment approaches
            - Priority ranking: Determine which gaps to address first
            
            WORKFLOW:
            1. Analyze current CRM contact/company data from session state
            2. Review detected gaps from DataQualityAgent
            3. Craft targeted search queries for each gap
            4. Create search plan with priorities and confidence estimates
            5. Save search plan to session state for retrieval agents
            
            SEARCH QUERY TYPES:
            - Web searches: "ACME Corp industry" OR "ACME Corp employees count"
            - LinkedIn searches: "ACME Corp company page" OR "John Doe ACME Corp"
            - Company data: Domain-based lookups for structured data
            - Competitor analysis: "ACME Corp competitors" OR "ACME Corp vs [competitor]"
            
            OUTPUT FORMAT: Save detailed search plan using CRMStateKeys.SEARCH_PLAN
            """,
            **kwargs
        )


class WebRetrieverAgent(SpecializedAgent):
    """Agent that executes web searches and extracts candidate facts."""
    
    def __init__(self, **kwargs):
        super().__init__(
            name="WebRetrieverAgent", 
            domain="web_retrieval",
            specialized_tools=["web_search", "fetch_url"],
            instruction="""
            You are a specialized Web Retrieval agent for CRM enrichment.
            
            🎯 CORE RESPONSIBILITY: Execute web searches and extract candidate facts 
            like industry, HQ location, staff size, tech stack, competitor usage.
            
            CAPABILITIES:
            - Web search execution using SERP APIs
            - Content extraction from company websites
            - Fact extraction: industry, size, location, technology, competitors
            - Source attribution and confidence scoring
            
            WORKFLOW:
            1. Read search plan from session state (CRMStateKeys.SEARCH_PLAN)
            2. Execute web searches for each planned query
            3. Fetch and analyze relevant URLs from search results
            4. Extract structured facts with confidence scores
            5. Save findings to session state using CRMStateKeys.WEB_FINDINGS
            
            EXTRACTION TARGETS:
            - Company industry/sector
            - Headquarters location
            - Employee count/company size
            - Technology stack mentions
            - Competitor references
            - Recent news/updates
            - Contact information
            
            OUTPUT FORMAT: List of structured findings with source URLs and confidence
            """,
            **kwargs
        )


class LinkedInRetrieverAgent(SpecializedAgent):
    """Agent that retrieves LinkedIn company/contact profile metadata."""
    
    def __init__(self, **kwargs):
        super().__init__(
            name="LinkedInRetrieverAgent",
            domain="linkedin_retrieval", 
            specialized_tools=["linkedin_company_lookup", "web_search"],
            instruction="""
            You are a specialized LinkedIn Retrieval agent for CRM enrichment.
            
            🎯 CORE RESPONSIBILITY: Retrieve company and contact profile metadata 
            from LinkedIn while respecting platform terms and rate limits.
            
            CAPABILITIES:
            - LinkedIn company page lookup
            - Professional profile information
            - Company size and specialties extraction
            - Industry classification
            - Employee insights (when available)
            
            WORKFLOW:
            1. Read search plan from session state
            2. Execute LinkedIn-specific lookups using available tools
            3. Extract professional metadata with confidence scoring
            4. Respect rate limits and ToS requirements
            5. Save findings to session state using CRMStateKeys.LI_FINDINGS
            
            EXTRACTION TARGETS:
            - Company size (employee ranges)
            - Industry specialties
            - Company description
            - Location information
            - Recent company updates
            - Key personnel (when appropriate)
            
            COMPLIANCE NOTES:
            - Respect LinkedIn's Terms of Service
            - Use only publicly available information
            - Implement appropriate rate limiting
            - Attribute sources properly
            
            OUTPUT FORMAT: Structured LinkedIn data with source attribution
            """,
            **kwargs
        )


class CompanyDataRetrieverAgent(SpecializedAgent):
    """Agent that retrieves structured company data from external sources."""
    
    def __init__(self, **kwargs):
        super().__init__(
            name="CompanyDataRetrieverAgent",
            domain="company_data_retrieval",
            specialized_tools=["get_company_metadata", "web_search"],
            instruction="""
            You are a specialized Company Data Retrieval agent for CRM enrichment.
            
            🎯 CORE RESPONSIBILITY: Retrieve structured company data from external 
            sources like Clearbit, Crunchbase, or other business data providers.
            
            CAPABILITIES:
            - Structured data source integration
            - Domain-based company lookups
            - Financial and business metrics
            - Technology stack identification
            - Funding and growth information
            
            WORKFLOW:
            1. Read search plan from session state
            2. Execute lookups using structured data sources
            3. Aggregate data from multiple providers when available
            4. Normalize and validate data quality
            5. Save findings to session state using CRMStateKeys.COMPANY_FINDINGS
            
            DATA SOURCES (when available):
            - Business directories
            - Technology databases
            - Financial data providers
            - Industry classification systems
            - Government business registries
            
            EXTRACTION TARGETS:
            - Official company name and legal structure
            - Industry codes (NAICS, SIC)
            - Revenue ranges
            - Technology stack
            - Funding information
            - Geographic presence
            
            OUTPUT FORMAT: Structured company data with provider attribution
            """,
            **kwargs
        )


class EmailVerifierAgent(SpecializedAgent):
    """Agent that validates email deliverability and assesses risk."""
    
    def __init__(self, **kwargs):
        super().__init__(
            name="EmailVerifierAgent",
            domain="email_verification",
            specialized_tools=["verify_email"],
            instruction="""
            You are a specialized Email Verification agent for CRM data quality.
            
            🎯 CORE RESPONSIBILITY: Validate email deliverability and assess 
            risk factors for email addresses in CRM records.
            
            CAPABILITIES:
            - Email syntax validation
            - Domain deliverability checks
            - Catch-all domain detection
            - Risk assessment scoring
            - Provider identification
            
            WORKFLOW:
            1. Read contact email from session state
            2. Execute email verification using available APIs
            3. Assess deliverability and risk factors
            4. Provide recommendations for email quality
            5. Save results to session state using CRMStateKeys.EMAIL_VALIDATION
            
            VALIDATION CHECKS:
            - Syntax validation (RFC compliance)
            - Domain MX record verification
            - Catch-all domain detection
            - Disposable email detection
            - Role-based email identification
            - Deliverability scoring
            
            RISK FACTORS:
            - Bounce probability
            - Spam trap likelihood
            - Domain reputation
            - Email age and activity
            
            OUTPUT FORMAT: Validation results with risk scores and recommendations
            """,
            **kwargs
        )


class SummarizerAgent(SpecializedAgent):
    """Agent that normalizes and deduplicates findings into concise summaries."""
    
    def __init__(self, **kwargs):
        super().__init__(
            name="SummarizerAgent",
            domain="data_synthesis",
            specialized_tools=[],  # Uses data from session state
            instruction="""
            You are a specialized Summarizer agent for CRM data synthesis.
            
            🎯 CORE RESPONSIBILITY: Normalize and deduplicate findings from multiple 
            sources, producing concise, source-attributed summaries.
            
            CAPABILITIES:
            - Multi-source data aggregation
            - Conflict resolution and deduplication
            - Confidence scoring and source weighting
            - Structured insight generation
            - Quality assessment
            
            WORKFLOW:
            1. Read findings from all retrieval agents (web, LinkedIn, company data)
            2. Normalize data formats and field mappings
            3. Resolve conflicts using source reliability and recency
            4. Generate confidence scores for each insight
            5. Save normalized insights using CRMStateKeys.NORMALIZED_INSIGHTS
            
            NORMALIZATION RULES:
            - Prefer structured sources over unstructured
            - Weight recent data higher than old data
            - Use multiple source confirmation for high confidence
            - Flag conflicting information for human review
            - Maintain source attribution for all insights
            
            CONFLICT RESOLUTION:
            - LinkedIn > Official website > News articles > General web
            - Recent data > Historical data
            - Multiple sources > Single source
            - Structured APIs > Scraped content
            
            OUTPUT FORMAT: Normalized insights with confidence scores and sources
            """,
            **kwargs
        )


class EntityResolutionAgent(SpecializedAgent):
    """Agent that maps findings to CRM objects and handles deduplication."""
    
    def __init__(self, **kwargs):
        super().__init__(
            name="EntityResolutionAgent",
            domain="entity_resolution",
            specialized_tools=[],  # Uses session state data
            instruction="""
            You are a specialized Entity Resolution agent for CRM field mapping.
            
            🎯 CORE RESPONSIBILITY: Map normalized findings to specific CRM 
            object fields and handle deduplication with field precedence policies.
            
            CAPABILITIES:
            - CRM field mapping and transformation
            - Data type conversion and validation
            - Deduplication logic
            - Field precedence policy enforcement
            - Change impact assessment
            
            WORKFLOW:
            1. Read normalized insights from SummarizerAgent
            2. Map insights to specific HubSpot contact/company fields
            3. Apply field precedence and update policies
            4. Generate proposed field mappings with justifications
            5. Save mappings using CRMStateKeys.PROPOSED_FIELD_MAP
            
            FIELD MAPPING EXAMPLES:
            - "Software Company" → industry: "Software"
            - "100-500 employees" → num_employees: 300 (midpoint)
            - "San Francisco, CA" → city: "San Francisco", state: "California"
            - "Series B funded" → lifecycle_stage: "Customer"
            
            PRECEDENCE RULES:
            - Don't overwrite recent manual updates
            - Prefer high-confidence automated data
            - Flag conflicts for human review
            - Maintain audit trail of changes
            
            OUTPUT FORMAT: Proposed field mappings with confidence and justification
            """,
            **kwargs
        )


class CRMUpdaterAgent(SpecializedAgent):
    """Agent that prepares and applies updates to HubSpot CRM."""
    
    def __init__(self, **kwargs):
        # Import OpenAPI tool for Phase 3
        try:
            from ...core.factory import create_hubspot_openapi_tool
            hubspot_openapi_tool = create_hubspot_openapi_tool()
            additional_tools = [hubspot_openapi_tool]
        except Exception:
            # Fallback to MCP tools if OpenAPI tool creation fails
            additional_tools = []
        
        super().__init__(
            name="CRMUpdaterAgent",
            domain="crm_updates",
            specialized_tools=["query_hubspot_crm", "get_hubspot_contact", "get_hubspot_company", "await_human_approval", "notify_slack"],
            additional_tools=additional_tools,
            instruction="""
            You are a specialized CRM Updater agent for HubSpot integration.
            
            🎯 CORE RESPONSIBILITY: Prepare proposed CRM updates, request human 
            approval, and apply approved changes to HubSpot.
            
            CAPABILITIES:
            - Change proposal generation
            - Human approval workflow integration
            - HubSpot API updates (via OpenAPI tools and MCP server)
            - Update result tracking and reporting
            - Rollback and error handling
            - Idempotency key generation for safe retries
            
            WORKFLOW:
            1. Read proposed field mappings from EntityResolutionAgent
            2. Generate detailed change proposals with before/after values
            3. Request human approval via Slack integration
            4. Apply only approved changes to HubSpot
            5. Track and report update results
            
            APPROVAL WORKFLOW:
            - Format changes for human review
            - Send approval request via Slack
            - Process approval responses (all, selected, or none)
            - Apply only approved changes
            - Report success/failure status
            
            SAFETY MEASURES:
            - Never apply changes without approval (unless explicitly configured)
            - Validate data before updates
            - Maintain audit trail
            - Handle API errors gracefully
            - Provide rollback information
            - Use idempotency keys for all HubSpot writes to prevent duplicates
            
            IDEMPOTENCY STRATEGY:
            - Generate unique keys based on object ID + field set + timestamp
            - Store keys in session state to prevent duplicate operations
            - Include keys in API requests where supported
            
            TOOL USAGE:
            - Prefer OpenAPI tools (update_company, update_contact, get_company, get_contact) when available
            - Fallback to MCP tools if OpenAPI tools fail
            - Use appropriate tool based on object type and operation
            
            OUTPUT FORMAT: Update results with success/failure details and idempotency tracking
            """,
            **kwargs
        )
    
    def _get_logger(self):
        """Get logger instance for this agent."""
        from ...core.observability import get_logger
        return get_logger("crm_updater")
    
    def _get_idempotency_manager(self):
        """Get idempotency manager instance."""
        from ...core.idempotency import get_idempotency_manager
        return get_idempotency_manager()
    
    def apply_hubspot_update_with_idempotency(
        self,
        object_type: str,
        object_id: str,
        properties: dict,
        enrichment_results: List = None,
        session_id: str = None,
        trace_id: str = None
    ) -> dict:
        """
        Apply HubSpot update with idempotency and full observability.
        
        Phase 9 implementation with structured logging, audit trail,
        and safe retry capabilities.
        
        PHASE 1 PROVENANCE GATE: Validates that all enrichment results have
        source_urls and last_verified_at before allowing HubSpot writes.
        """
        from ...core.observability import span_context, EventType
        from ...core.idempotency import OperationType
        
        # PHASE 1 PROVENANCE GATE: Validate all enrichment results before write
        if enrichment_results:
            provenance_errors = []
            for result in enrichment_results:
                if hasattr(result, 'validate_provenance') and not result.validate_provenance():
                    errors = result.get_provenance_errors() if hasattr(result, 'get_provenance_errors') else ["Missing provenance data"]
                    provenance_errors.append(f"Field '{result.field_name}': {', '.join(errors)}")
            
            if provenance_errors:
                error_message = f"Provenance validation failed: {'; '.join(provenance_errors)}"
                self._get_logger().error(
                    f"HubSpot write blocked due to provenance validation failure",
                    operation=f"update_{object_type}",
                    metadata={
                        "object_id": object_id,
                        "provenance_errors": provenance_errors,
                        "fields_attempted": list(properties.keys())
                    }
                )
                return {
                    "success": False,
                    "error_type": "provenance_validation_failed",
                    "error_message": error_message,
                    "provenance_errors": provenance_errors,
                    "blocked_write": True
                }
        
        with span_context(f"hubspot_update_{object_type}", "crm_updater") as span:
            # Generate idempotency key
            idempotency_key = self._get_idempotency_manager().create_hubspot_update_key(
                object_type=object_type,
                object_id=object_id,
                properties=properties,
                session_id=session_id,
                trace_id=trace_id or span.trace_id
            )
            
            # Log operation start
            self._get_logger().info(
                f"Starting HubSpot {object_type} update",
                operation=f"update_{object_type}",
                metadata={
                    "object_id": object_id,
                    "property_count": len(properties),
                    "idempotency_key": idempotency_key.key
                }
            )
            
            # Check for duplicate operation
            duplicate_result = self._get_idempotency_manager().check_duplicate(idempotency_key)
            if duplicate_result:
                self._get_logger().info(
                    f"Duplicate {object_type} update detected",
                    operation=f"update_{object_type}",
                    metadata={
                        "object_id": object_id,
                        "idempotency_key": idempotency_key.key,
                        "original_success": duplicate_result.success
                    }
                )
                
                # Return previous result
                return {
                    "success": duplicate_result.success,
                    "resource_id": duplicate_result.resource_id,
                    "was_duplicate": True,
                    "idempotency_key": idempotency_key.key,
                    "response_data": duplicate_result.response_data,
                    "error_message": duplicate_result.error_message
                }
            
            # Get current state for audit trail
            try:
                current_state = self._get_current_object_state(object_type, object_id)
            except Exception as e:
                self._get_logger().warning(
                    f"Could not retrieve current state for audit trail",
                    operation=f"update_{object_type}",
                    error=e,
                    metadata={"object_id": object_id}
                )
                current_state = None
            
            # Perform the update
            try:
                # Apply update through appropriate tool
                response_data = self._execute_hubspot_update(object_type, object_id, properties)
                
                # Get updated state for audit trail
                try:
                    updated_state = self._get_current_object_state(object_type, object_id)
                except Exception:
                    updated_state = None
                
                # Record successful operation
                operation_result = self._get_idempotency_manager().record_operation(
                    key=idempotency_key,
                    success=True,
                    resource_id=object_id,
                    response_data=response_data
                )
                
                # Create audit log entry
                self._get_logger().audit_log(
                    event_type=EventType.HUBSPOT_WRITE,
                    operation=f"update_{object_type}",
                    resource_type=object_type,
                    resource_id=object_id,
                    before_state=current_state,
                    after_state=updated_state,
                    evidence_urls=[],  # Could add HubSpot record URL
                    success=True,
                    idempotency_key=idempotency_key.key,
                    metadata={
                        "properties_updated": list(properties.keys()),
                        "property_count": len(properties)
                    }
                )
                
                self._get_logger().info(
                    f"Successfully updated {object_type}",
                    operation=f"update_{object_type}",
                    metadata={
                        "object_id": object_id,
                        "idempotency_key": idempotency_key.key
                    }
                )
                
                return {
                    "success": True,
                    "resource_id": object_id,
                    "was_duplicate": False,
                    "idempotency_key": idempotency_key.key,
                    "response_data": response_data
                }
                
            except Exception as e:
                error_message = str(e)
                
                # Record failed operation
                operation_result = self._get_idempotency_manager().record_operation(
                    key=idempotency_key,
                    success=False,
                    resource_id=object_id,
                    error_message=error_message
                )
                
                # Create audit log entry for failure
                self._get_logger().audit_log(
                    event_type=EventType.ERROR_OCCURRED,
                    operation=f"update_{object_type}",
                    resource_type=object_type,
                    resource_id=object_id,
                    before_state=current_state,
                    success=False,
                    error_message=error_message,
                    idempotency_key=idempotency_key.key
                )
                
                self._get_logger().error(
                    f"Failed to update {object_type}",
                    operation=f"update_{object_type}",
                    error=e,
                    metadata={
                        "object_id": object_id,
                        "idempotency_key": idempotency_key.key
                    }
                )
                
                return {
                    "success": False,
                    "resource_id": object_id,
                    "was_duplicate": False,
                    "idempotency_key": idempotency_key.key,
                    "error_message": error_message
                }
    
    def _get_current_object_state(self, object_type: str, object_id: str) -> dict:
        """Get current state of HubSpot object for audit trail."""
        # This would use the appropriate tool to get current object state
        # Implementation depends on available tools
        return {"object_type": object_type, "object_id": object_id}
    
    def _execute_hubspot_update(self, object_type: str, object_id: str, properties: dict) -> dict:
        """Execute the actual HubSpot update operation."""
        # This would use the appropriate tool (OpenAPI or MCP) to perform the update
        # Implementation depends on available tools
        return {"status": "updated", "object_id": object_id}


class CRMDataQualityAgent(SpecializedAgent):
    """Agent that validates CRM data quality and proposes improvements."""
    
    def __init__(self, **kwargs):
        super().__init__(
            name="CRMDataQualityAgent",
            domain="crm_data_quality",
            specialized_tools=["get_hubspot_contact", "get_hubspot_company", "normalize_company_data", "determine_company_type_with_gemini", "detect_competitors_from_website", "generate_club_info_with_gemini", "update_crm_state"],
            instruction="""
            You are a specialized CRM Data Quality agent for validation and cleanup.
            
            🎯 CORE RESPONSIBILITY: Validate required fields, normalize taxonomy 
            (industry, lifecycle stage), and propose data quality improvements.
            
            🔒 PHASE 1 PROVENANCE GATE: Enforce that all enrichment results must have
            source_urls and last_verified_at before allowing HubSpot writes.
            
            CAPABILITIES:
            - Required field validation
            - Data consistency checking
            - Taxonomy normalization
            - Duplicate detection
            - Quality scoring and reporting
            
            WORKFLOW:
            1. Load current CRM contact/company data
            2. Validate against required field policies
            3. Check data consistency and format compliance
            4. PHASE 1: Validate provenance on all enrichment results
            5. Identify normalization opportunities
            6. Generate quality report and improvement suggestions
            
            VALIDATION RULES:
            - Required fields: email, company, industry (configurable)
            - Format validation: email syntax, phone numbers, URLs
            - Taxonomy compliance: standardized industry values
            - Consistency checks: contact-company relationships
            - PHASE 1 PROVENANCE: All enrichment results must have source_urls and last_verified_at
            
            QUALITY METRICS:
            - Field completeness percentage
            - Data freshness (last updated)
            - Format compliance score
            - Taxonomy standardization
            - Duplicate risk assessment
            
            OUTPUT FORMAT: Quality report with specific improvement recommendations
            
            PROVENANCE ENFORCEMENT:
            - Block any enrichment result that lacks source_urls or last_verified_at
            - Generate detailed provenance validation errors
            - Require manual review for results without proper citations
            """,
            **kwargs
        )


# Agent creation helper functions

def create_crm_query_builder(**kwargs) -> QueryBuilderAgent:
    """Create a QueryBuilderAgent instance."""
    return QueryBuilderAgent(**kwargs)


def create_crm_web_retriever(**kwargs) -> WebRetrieverAgent:
    """Create a WebRetrieverAgent instance."""
    return WebRetrieverAgent(**kwargs)


def create_crm_linkedin_retriever(**kwargs) -> LinkedInRetrieverAgent:
    """Create a LinkedInRetrieverAgent instance."""
    return LinkedInRetrieverAgent(**kwargs)


def create_crm_company_data_retriever(**kwargs) -> CompanyDataRetrieverAgent:
    """Create a CompanyDataRetrieverAgent instance."""
    return CompanyDataRetrieverAgent(**kwargs)


def create_crm_email_verifier(**kwargs) -> EmailVerifierAgent:
    """Create an EmailVerifierAgent instance."""
    return EmailVerifierAgent(**kwargs)


def create_crm_summarizer(**kwargs) -> SummarizerAgent:
    """Create a SummarizerAgent instance."""
    return SummarizerAgent(**kwargs)


def create_crm_entity_resolver(**kwargs) -> EntityResolutionAgent:
    """Create an EntityResolutionAgent instance."""
    return EntityResolutionAgent(**kwargs)


def create_crm_updater(**kwargs) -> CRMUpdaterAgent:
    """Create a CRMUpdaterAgent instance."""
    return CRMUpdaterAgent(**kwargs)


def create_crm_data_quality_agent(**kwargs) -> CRMDataQualityAgent:
    """Create a CRMDataQualityAgent instance."""
    return CRMDataQualityAgent(**kwargs)
