"""
Typed state models for CRM multi-agent system.
Provides type-safe state management using Pydantic models.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
import uuid
import hashlib


class CRMEnrichmentResult(BaseModel):
    """Result from CRM data enrichment process."""
    field_name: str
    current_value: Optional[Any] = None
    proposed_value: Optional[Any] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    source: str = ""
    source_urls: List[str] = Field(default_factory=list)  # Phase 1: Required for provenance
    last_verified_at: Optional[datetime] = Field(default_factory=datetime.now)  # Phase 1: Required for provenance
    
    def validate_provenance(self) -> bool:
        """
        Phase 1: Validate that enrichment result has required provenance.
        
        Returns:
            True if result has source_urls and last_verified_at
        """
        return (
            len(self.source_urls) > 0 and 
            self.last_verified_at is not None and
            self.source != ""
        )
    
    def get_provenance_errors(self) -> List[str]:
        """Get list of provenance validation errors."""
        errors = []
        if not self.source_urls:
            errors.append("Missing source_urls")
        if not self.source:
            errors.append("Missing source")
        if self.last_verified_at is None:
            errors.append("Missing last_verified_at")
        return errors


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
    # Lead scoring results (Phase 6)
    lead_scores: Dict[str, Any] = Field(default_factory=dict)
    
    # Outreach personalization results (Phase 7)
    outreach_results: Dict[str, Any] = Field(default_factory=dict)
    
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
    
    # Idempotency tracking for Phase 3
    idempotency_keys: Dict[str, str] = Field(default_factory=dict)
    
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
    
    def generate_idempotency_key(self, object_type: str, object_id: str, field_set: List[str]) -> str:
        """
        Generate an idempotency key for HubSpot operations.
        
        Args:
            object_type: 'company' or 'contact'
            object_id: HubSpot object ID
            field_set: List of fields being updated
            
        Returns:
            Unique idempotency key
        """
        # Create deterministic key based on operation parameters
        key_components = [
            object_type,
            object_id,
            "|".join(sorted(field_set)),
            self.session_id
        ]
        key_string = ":".join(key_components)
        
        # Generate SHA-256 hash for consistent, unique key
        key_hash = hashlib.sha256(key_string.encode()).hexdigest()[:16]
        idempotency_key = f"{object_type}_{object_id}_{key_hash}"
        
        # Store in session state for tracking
        operation_key = f"{object_type}:{object_id}"
        self.idempotency_keys[operation_key] = idempotency_key
        self.update_timestamp()
        
        return idempotency_key
    
    def get_idempotency_key(self, object_type: str, object_id: str) -> Optional[str]:
        """Get existing idempotency key for an operation."""
        operation_key = f"{object_type}:{object_id}"
        return self.idempotency_keys.get(operation_key)


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
    LEAD_SCORES = "lead_scores"
    
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

