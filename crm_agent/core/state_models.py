"""
Typed state models for CRM multi-agent system.
Provides type-safe state management using Pydantic models.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
import uuid


class CRMEnrichmentResult(BaseModel):
    """Result from CRM data enrichment process with required provenance."""
    field_name: str
    current_value: Optional[Any] = None
    proposed_value: Optional[Any] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    source: str = ""
    source_urls: List[str] = Field(default_factory=list, description="Required: URLs where data was found")
    last_verified_at: Optional[datetime] = Field(default_factory=datetime.now, description="Required: When data was last verified")
    extracted_at: datetime = Field(default_factory=datetime.now)


class CRMDataQualityReport(BaseModel):
    """CRM data quality analysis report."""
    missing_required_fields: List[str] = Field(default_factory=list)
    outdated_fields: List[str] = Field(default_factory=list)
    inconsistent_fields: List[str] = Field(default_factory=list)
    quality_score: float = Field(default=1.0, ge=0.0, le=1.0)
    total_contacts_analyzed: int = 0
    total_companies_analyzed: int = 0
    field_completeness: Dict[str, float] = Field(default_factory=dict)
    suggested_enrichments: List[CRMEnrichmentResult] = Field(default_factory=list)


class CRMSessionState(BaseModel):
    """
    Central session state for CRM multi-agent system.
    Manages shared data and communication between agents for CRM enrichment.
    """
    # Identifiers
    contact_id: Optional[str] = None
    company_id: Optional[str] = None
    contact_email: Optional[str] = None
    company_domain: Optional[str] = None
    
    # Data health
    data_loaded: bool = False
    load_timestamp: Optional[datetime] = None
    
    # Current CRM data
    contact_data: Dict[str, Any] = Field(default_factory=dict)
    company_data: Dict[str, Any] = Field(default_factory=dict)
    
    # Enrichment findings from different sources
    web_findings: List[Dict[str, Any]] = Field(default_factory=list)
    li_findings: List[Dict[str, Any]] = Field(default_factory=list)
    company_findings: List[Dict[str, Any]] = Field(default_factory=list)
    email_validation: Dict[str, Any] = Field(default_factory=dict)
    
    # Processed insights
    normalized_insights: Dict[str, Any] = Field(default_factory=dict)
    enrichment_results: List[CRMEnrichmentResult] = Field(default_factory=list)
    
    # Quality analysis
    detected_gaps: Dict[str, Any] = Field(default_factory=dict)
    quality_report: Optional[CRMDataQualityReport] = None
    
    # Workflow state
    search_plan: Dict[str, Any] = Field(default_factory=dict)
    proposed_field_map: Dict[str, Any] = Field(default_factory=dict)
    proposed_changes: List[Dict[str, Any]] = Field(default_factory=list)
    approved_changes: List[Dict[str, Any]] = Field(default_factory=list)
    update_results: Dict[str, Any] = Field(default_factory=dict)
    
    # Agent interaction tracking
    active_agent: Optional[str] = None
    agent_history: List[str] = Field(default_factory=list)
    routing_decisions: List[Dict[str, str]] = Field(default_factory=list)
    
    # User interaction
    pending_approvals: List[Dict[str, Any]] = Field(default_factory=list)
    user_preferences: Dict[str, Any] = Field(default_factory=dict)
    user_clarifications: List[Dict[str, str]] = Field(default_factory=list)
    
    # Session metadata
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)
    
    def update_timestamp(self):
        """Update the last_updated timestamp."""
        self.last_updated = datetime.now()
    
    def add_routing_decision(self, from_agent: str, to_agent: str, reason: str):
        """Track agent routing decisions."""
        self.routing_decisions.append({
            "from": from_agent,
            "to": to_agent,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        })
        self.update_timestamp()
    
    def add_agent_to_history(self, agent_name: str):
        """Add an agent to the interaction history."""
        self.agent_history.append(agent_name)
        self.active_agent = agent_name
        self.update_timestamp()
    
    def get_analysis_result(self, key: str, default=None):
        """Get a result from normalized insights."""
        return self.normalized_insights.get(key, default)
    
    def set_analysis_result(self, key: str, value: Any):
        """Set a result in normalized insights."""
        self.normalized_insights[key] = value
        self.update_timestamp()
    
    def add_enrichment_result(self, result: CRMEnrichmentResult):
        """Add an enrichment result."""
        self.enrichment_results.append(result)
        self.update_timestamp()


class CRMStateKeys:
    """Constants for CRM session state keys to ensure consistency."""
    
    # Identifiers
    CONTACT_ID = "contact_id"
    COMPANY_ID = "company_id"
    CONTACT_EMAIL = "contact_email"
    COMPANY_DOMAIN = "company_domain"
    
    # Data
    CONTACT_DATA = "contact_data"
    COMPANY_DATA = "company_data"
    DATA_LOADED = "data_loaded"
    
    # Findings
    WEB_FINDINGS = "web_findings"
    LI_FINDINGS = "li_findings"
    COMPANY_FINDINGS = "company_findings"
    EMAIL_VALIDATION = "email_validation"
    
    # Processing
    NORMALIZED_INSIGHTS = "normalized_insights"
    ENRICHMENT_RESULTS = "enrichment_results"
    
    # Quality
    DETECTED_GAPS = "detected_gaps"
    QUALITY_REPORT = "quality_report"
    
    # Workflow
    SEARCH_PLAN = "search_plan"
    PROPOSED_FIELD_MAP = "proposed_field_map"
    PROPOSED_CHANGES = "proposed_changes"
    APPROVED_CHANGES = "approved_changes"
    UPDATE_RESULTS = "update_results"


def create_initial_crm_state(
    contact_email: Optional[str] = None,
    company_domain: Optional[str] = None,
    session_id: Optional[str] = None
) -> CRMSessionState:
    """Create a new initial CRM session state."""
    return CRMSessionState(
        contact_email=contact_email,
        company_domain=company_domain,
        session_id=session_id or str(uuid.uuid4())
    )


def validate_enrichment_result_provenance(result: CRMEnrichmentResult) -> bool:
    """
    Validate that an enrichment result has required provenance fields.
    
    Args:
        result: CRMEnrichmentResult to validate
        
    Returns:
        True if provenance is valid, False otherwise
        
    Raises:
        ValueError: If provenance requirements are not met
    """
    errors = []
    
    if not result.source_urls:
        errors.append(f"Field '{result.field_name}' missing required source_urls")
    
    if not result.last_verified_at:
        errors.append(f"Field '{result.field_name}' missing required last_verified_at")
        
    # Validate source URLs are properly formatted
    for url in result.source_urls:
        if not url.startswith(('http://', 'https://')):
            errors.append(f"Field '{result.field_name}' has invalid source URL: {url}")
    
    if errors:
        raise ValueError("Provenance validation failed: " + "; ".join(errors))
    
    return True


def create_enrichment_result_with_provenance(
    field_name: str,
    proposed_value: Any,
    source_urls: List[str],
    confidence: float = 1.0,
    source: str = "",
    current_value: Optional[Any] = None
) -> CRMEnrichmentResult:
    """
    Create a CRMEnrichmentResult with proper provenance validation.
    
    Args:
        field_name: Name of the field being enriched
        proposed_value: New value for the field
        source_urls: List of URLs where data was found (required)
        confidence: Confidence score (0.0-1.0)
        source: Description of the data source
        current_value: Current value in CRM (if any)
        
    Returns:
        Validated CRMEnrichmentResult
        
    Raises:
        ValueError: If provenance requirements are not met
    """
    result = CRMEnrichmentResult(
        field_name=field_name,
        current_value=current_value,
        proposed_value=proposed_value,
        confidence=confidence,
        source=source,
        source_urls=source_urls,
        last_verified_at=datetime.now()
    )
    
    # Validate provenance before returning
    validate_enrichment_result_provenance(result)
    
    return result

