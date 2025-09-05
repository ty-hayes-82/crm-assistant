"""
Typed state models for Jira multi-agent system.
Provides type-safe state management using Pydantic models.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime


class RiskAssessmentReport(BaseModel):
    """Risk assessment report with metrics and scores."""
    stale_issue_count: int = 0
    blocked_issue_count: int = 0
    due_soon_count: int = 0
    unassigned_count: int = 0
    overall_risk_score: float = Field(default=0.0, ge=0.0, le=10.0)
    generated_at: datetime = Field(default_factory=datetime.now)
    risk_factors: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


class DataQualityReport(BaseModel):
    """Data quality analysis report."""
    missing_fields_count: int = 0
    suggested_fixes: List[Dict[str, Any]] = Field(default_factory=list)
    quality_score: float = Field(default=1.0, ge=0.0, le=1.0)
    issues_with_missing_data: int = 0
    total_issues: int = 0
    field_completeness: Dict[str, float] = Field(default_factory=dict)


class WorkloadAnalysis(BaseModel):
    """Assignee workload analysis."""
    assignee_counts: Dict[str, int] = Field(default_factory=dict)
    unassigned_count: int = 0
    workload_by_status: Dict[str, Dict[str, int]] = Field(default_factory=dict)
    overloaded_assignees: List[str] = Field(default_factory=list)
    underutilized_assignees: List[str] = Field(default_factory=list)


class StatusBreakdown(BaseModel):
    """Status distribution analysis."""
    raw_status_counts: Dict[str, int] = Field(default_factory=dict)
    categorized_counts: Dict[str, int] = Field(default_factory=dict)
    status_percentages: Dict[str, float] = Field(default_factory=dict)
    active_issues: int = 0
    done_issues: int = 0
    pending_issues: int = 0


class JiraSessionState(BaseModel):
    """
    Central session state for Jira multi-agent system.
    Manages shared data and communication between agents.
    """
    # Data loading state
    jira_data: List[Dict[str, Any]] = Field(default_factory=list)
    data_loaded: bool = False
    data_source: Optional[str] = None
    load_timestamp: Optional[datetime] = None
    
    # Query results
    last_query_results: List[Dict[str, Any]] = Field(default_factory=list)
    query_history: List[str] = Field(default_factory=list)
    
    # Analysis results
    risk_report: Optional[RiskAssessmentReport] = None
    quality_report: Optional[DataQualityReport] = None
    workload_analysis: Optional[WorkloadAnalysis] = None
    status_breakdown: Optional[StatusBreakdown] = None
    
    # Specific issue lists (for workflows)
    stale_issues: List[Dict[str, Any]] = Field(default_factory=list)
    blocked_issues: List[Dict[str, Any]] = Field(default_factory=list)
    due_soon_issues: List[Dict[str, Any]] = Field(default_factory=list)
    unassigned_issues: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Data quality and fixes
    approved_fixes: List[Dict[str, Any]] = Field(default_factory=list)
    pending_fixes: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Agent interaction tracking
    active_agent: Optional[str] = None
    agent_history: List[str] = Field(default_factory=list)
    routing_decisions: List[Dict[str, str]] = Field(default_factory=list)
    
    # User interaction
    user_clarifications: List[Dict[str, str]] = Field(default_factory=list)
    pending_user_input: Optional[str] = None
    
    # Session metadata
    session_id: Optional[str] = None
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
    
    def add_query_to_history(self, query: str):
        """Add a query to the history."""
        self.query_history.append(query)
        self.update_timestamp()


# State key constants for type-safe access
class StateKeys:
    """Constants for session state keys to ensure consistency."""
    
    # Data
    JIRA_DATA = "jira_data"
    DATA_LOADED = "data_loaded"
    
    # Reports
    RISK_REPORT = "risk_report"
    QUALITY_REPORT = "quality_report"
    WORKLOAD_ANALYSIS = "workload_analysis"
    STATUS_BREAKDOWN = "status_breakdown"
    
    # Issue lists
    STALE_ISSUES = "stale_issues"
    BLOCKED_ISSUES = "blocked_issues"
    DUE_SOON_ISSUES = "due_soon_issues"
    UNASSIGNED_ISSUES = "unassigned_issues"
    
    # Query results
    LAST_QUERY_RESULTS = "last_query_results"
    
    # Fixes
    APPROVED_FIXES = "approved_fixes"
    PENDING_FIXES = "pending_fixes"


def create_initial_state(session_id: Optional[str] = None) -> JiraSessionState:
    """Create a new initial session state."""
    return JiraSessionState(session_id=session_id)
