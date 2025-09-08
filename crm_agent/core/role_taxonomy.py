"""
Role Taxonomy Service for Centralized Contact Role Classification

This module provides centralized role classification with confidence scoring,
policy enforcement, and provenance tracking for the CRM system.

Phase 8 Implementation:
- Centralized title→role synonyms with confidence scoring
- ADK policy callbacks for ethical data collection
- Low-confidence review task creation
- Provenance tracking for all role assignments
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import logging

from pydantic import BaseModel, Field


class RoleClassificationResult(BaseModel):
    """Result of role classification with confidence and provenance."""
    original_title: str
    classified_role: str
    role_category: str
    confidence: float = Field(ge=0.0, le=1.0)
    decision_authority: str
    typical_influence: str
    matched_synonyms: List[str] = Field(default_factory=list)
    confidence_factors: Dict[str, float] = Field(default_factory=dict)
    requires_review: bool = False
    classification_timestamp: datetime = Field(default_factory=datetime.utcnow)
    classification_version: str = "1.0.0"


class PolicyViolation(BaseModel):
    """Policy violation detected during data collection."""
    violation_type: str
    description: str
    source_url: Optional[str] = None
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    severity: str = "medium"  # low, medium, high, critical


class RoleTaxonomyService:
    """
    Centralized service for contact role classification with confidence scoring
    and policy enforcement.
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize the role taxonomy service."""
        self.logger = logging.getLogger(__name__)
        
        if config_path is None:
            config_path = Path(__file__).parent.parent / "configs" / "role_taxonomy_config.json"
        
        self.config = self._load_config(config_path)
        self.confidence_threshold = self.config.get("confidence_threshold", 0.75)
        
        # Precompile regex patterns for efficiency
        self._compile_title_patterns()
        
        self.logger.info(f"Role taxonomy service initialized with config version {self.config.get('version', 'unknown')}")
    
    def _load_config(self, config_path: Path) -> Dict[str, Any]:
        """Load role taxonomy configuration."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load role taxonomy config from {config_path}: {e}")
            return self._get_fallback_config()
    
    def _get_fallback_config(self) -> Dict[str, Any]:
        """Provide fallback configuration if main config fails to load."""
        return {
            "version": "fallback",
            "confidence_threshold": 0.75,
            "role_categories": {
                "executive": {
                    "decision_authority": "high",
                    "typical_influence": "strategic",
                    "roles": ["general_manager", "president", "ceo"]
                },
                "operations": {
                    "decision_authority": "medium", 
                    "typical_influence": "operational",
                    "roles": ["operations_manager"]
                }
            },
            "title_synonyms": {
                "general_manager": {
                    "exact_matches": ["general manager", "gm"],
                    "confidence_weights": {"exact_matches": 1.0}
                }
            }
        }
    
    def _compile_title_patterns(self):
        """Precompile regex patterns for title matching."""
        self.title_patterns = {}
        
        for role, synonyms in self.config.get("title_synonyms", {}).items():
            patterns = []
            
            # Exact matches
            for exact_match in synonyms.get("exact_matches", []):
                # Escape special regex characters and create word boundary pattern
                escaped = re.escape(exact_match.lower())
                patterns.append((f"\\b{escaped}\\b", synonyms["confidence_weights"]["exact_matches"]))
            
            # Partial matches
            for partial_match in synonyms.get("partial_matches", []):
                escaped = re.escape(partial_match.lower())
                patterns.append((escaped, synonyms["confidence_weights"]["partial_matches"]))
            
            # Compile patterns
            self.title_patterns[role] = [
                (re.compile(pattern), weight) for pattern, weight in patterns
            ]
    
    def classify_role(
        self, 
        job_title: str, 
        company_context: Optional[Dict[str, Any]] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> RoleClassificationResult:
        """
        Classify a contact's role based on job title and context.
        
        Args:
            job_title: The contact's job title
            company_context: Company information for context
            additional_context: Additional context for classification
            
        Returns:
            RoleClassificationResult with confidence scoring and metadata
        """
        if not job_title or not isinstance(job_title, str):
            return self._create_unknown_role_result(job_title or "")
        
        title_lower = job_title.lower().strip()
        
        # Find best matching role
        best_match = self._find_best_role_match(title_lower)
        
        if not best_match:
            return self._create_unknown_role_result(job_title)
        
        role, base_confidence, matched_synonyms = best_match
        
        # Calculate final confidence with context
        final_confidence, confidence_factors = self._calculate_confidence(
            role, base_confidence, title_lower, company_context, additional_context
        )
        
        # Get role category and metadata
        role_category, role_metadata = self._get_role_metadata(role)
        
        # Determine if review is required
        requires_review = self._requires_review(final_confidence, role, role_category)
        
        return RoleClassificationResult(
            original_title=job_title,
            classified_role=role,
            role_category=role_category,
            confidence=final_confidence,
            decision_authority=role_metadata.get("decision_authority", "unknown"),
            typical_influence=role_metadata.get("typical_influence", "unknown"),
            matched_synonyms=matched_synonyms,
            confidence_factors=confidence_factors,
            requires_review=requires_review,
            classification_version=self.config.get("version", "unknown")
        )
    
    def _find_best_role_match(self, title_lower: str) -> Optional[Tuple[str, float, List[str]]]:
        """Find the best matching role for a title."""
        best_role = None
        best_confidence = 0.0
        best_matches = []
        
        for role, patterns in self.title_patterns.items():
            role_confidence = 0.0
            role_matches = []
            
            for pattern, weight in patterns:
                if pattern.search(title_lower):
                    role_confidence = max(role_confidence, weight)
                    role_matches.append(pattern.pattern)
            
            if role_confidence > best_confidence:
                best_role = role
                best_confidence = role_confidence
                best_matches = role_matches
        
        return (best_role, best_confidence, best_matches) if best_role else None
    
    def _calculate_confidence(
        self, 
        role: str, 
        base_confidence: float,
        title_lower: str,
        company_context: Optional[Dict[str, Any]],
        additional_context: Optional[Dict[str, Any]]
    ) -> Tuple[float, Dict[str, float]]:
        """Calculate final confidence score with contextual factors."""
        confidence_factors = {"base_title_match": base_confidence}
        
        # Company size alignment
        if company_context:
            size_factor = self._assess_company_size_alignment(role, company_context)
            confidence_factors["company_size_alignment"] = size_factor
        
        # Industry context
        industry_factor = self._assess_industry_context(role, company_context)
        confidence_factors["industry_context"] = industry_factor
        
        # Contextual keywords
        keyword_factor = self._assess_contextual_keywords(role, title_lower)
        confidence_factors["contextual_keywords"] = keyword_factor
        
        # Calculate weighted final confidence
        scoring_config = self.config.get("confidence_scoring", {})
        factors_config = scoring_config.get("factors", {})
        
        final_confidence = base_confidence
        
        for factor_name, factor_value in confidence_factors.items():
            if factor_name != "base_title_match" and factor_name in factors_config:
                weight = factors_config[factor_name]
                final_confidence += (factor_value * weight)
        
        # Normalize to [0, 1] range
        final_confidence = min(1.0, max(0.0, final_confidence))
        
        return final_confidence, confidence_factors
    
    def _assess_company_size_alignment(self, role: str, company_context: Dict[str, Any]) -> float:
        """Assess if role aligns with company size."""
        if not company_context:
            return 0.5
        
        employee_count = company_context.get("numberofemployees", 0)
        
        # Executive roles more likely in larger companies
        if role in ["president", "ceo", "coo"]:
            if employee_count > 50:
                return 0.8
            elif employee_count > 25:
                return 0.6
            else:
                return 0.3
        
        # Specialized roles more likely in medium+ companies
        if role in ["it_manager", "marketing_sales", "controller"]:
            if employee_count > 25:
                return 0.7
            else:
                return 0.4
        
        return 0.5
    
    def _assess_industry_context(self, role: str, company_context: Optional[Dict[str, Any]]) -> float:
        """Assess role fit within golf industry context."""
        if not company_context:
            return 0.5
        
        # Golf-specific roles should have high industry context
        if role in ["golf_professional", "superintendent", "fb_manager"]:
            return 0.8
        
        # Generic business roles
        return 0.6
    
    def _assess_contextual_keywords(self, role: str, title_lower: str) -> float:
        """Assess presence of contextual keywords that support the role."""
        keyword_map = {
            "general_manager": ["club", "facility", "resort"],
            "golf_professional": ["pga", "instruction", "lessons"],
            "superintendent": ["course", "grounds", "turf"],
            "fb_manager": ["dining", "events", "catering"],
            "it_manager": ["systems", "network", "software"]
        }
        
        keywords = keyword_map.get(role, [])
        matches = sum(1 for keyword in keywords if keyword in title_lower)
        
        return min(0.8, matches * 0.3)
    
    def _get_role_metadata(self, role: str) -> Tuple[str, Dict[str, Any]]:
        """Get role category and metadata."""
        categories = self.config.get("role_categories", {})
        
        for category_name, category_data in categories.items():
            if role in category_data.get("roles", []):
                return category_name, category_data
        
        return "unknown", {"decision_authority": "unknown", "typical_influence": "unknown"}
    
    def _requires_review(self, confidence: float, role: str, role_category: str) -> bool:
        """Determine if role assignment requires human review."""
        validation_rules = self.config.get("role_validation_rules", {})
        
        # Check confidence threshold
        if confidence < self.confidence_threshold:
            return True
        
        # Executive roles always require review
        if role_category == "executive":
            return True
        
        # Check automatic assignment threshold
        auto_threshold = self.config.get("confidence_scoring", {}).get("auto_assign_threshold", 0.9)
        if confidence >= auto_threshold:
            return False
        
        return confidence < validation_rules.get("review_threshold", self.confidence_threshold)
    
    def _create_unknown_role_result(self, original_title: str) -> RoleClassificationResult:
        """Create result for unknown/unclassifiable roles."""
        return RoleClassificationResult(
            original_title=original_title,
            classified_role="unknown",
            role_category="unknown",
            confidence=0.0,
            decision_authority="unknown",
            typical_influence="unknown",
            requires_review=True,
            classification_version=self.config.get("version", "unknown")
        )
    
    def validate_data_collection_policy(self, source_url: str, request_type: str) -> List[PolicyViolation]:
        """
        Validate data collection against policy constraints.
        
        Args:
            source_url: URL being accessed
            request_type: Type of request (web_scraping, api_call, etc.)
            
        Returns:
            List of policy violations detected
        """
        violations = []
        policy_config = self.config.get("policy_enforcement", {})
        collection_limits = policy_config.get("data_collection_limits", {})
        
        # Check robots.txt compliance
        if collection_limits.get("respect_robots_txt", True):
            if self._violates_robots_txt(source_url):
                violations.append(PolicyViolation(
                    violation_type="robots_txt_violation",
                    description=f"Request to {source_url} violates robots.txt",
                    source_url=source_url,
                    severity="high"
                ))
        
        # Check paywall bypass
        if collection_limits.get("avoid_paywall_bypass", True):
            if self._is_paywall_bypass(source_url, request_type):
                violations.append(PolicyViolation(
                    violation_type="paywall_bypass",
                    description=f"Request attempts to bypass paywall at {source_url}",
                    source_url=source_url,
                    severity="critical"
                ))
        
        # Check email scraping
        if collection_limits.get("no_email_scraping", True):
            if request_type == "email_scraping":
                violations.append(PolicyViolation(
                    violation_type="email_scraping",
                    description="Email scraping is prohibited by policy",
                    source_url=source_url,
                    severity="high"
                ))
        
        return violations
    
    def _violates_robots_txt(self, url: str) -> bool:
        """Check if URL access violates robots.txt (placeholder implementation)."""
        # In a real implementation, this would fetch and parse robots.txt
        # For now, return False as placeholder
        return False
    
    def _is_paywall_bypass(self, url: str, request_type: str) -> bool:
        """Check if request attempts paywall bypass (placeholder implementation)."""
        # In a real implementation, this would check for paywall bypass indicators
        paywall_indicators = ["paywall", "subscription", "premium"]
        return any(indicator in url.lower() for indicator in paywall_indicators)
    
    def create_review_task(
        self, 
        classification_result: RoleClassificationResult,
        contact_id: Optional[str] = None,
        reason: str = "low_confidence_role_assignment"
    ) -> Dict[str, Any]:
        """
        Create a review task for low-confidence role assignments.
        
        Args:
            classification_result: The role classification that needs review
            contact_id: HubSpot contact ID if available
            reason: Reason for requiring review
            
        Returns:
            Task data for HubSpot task creation
        """
        task_data = {
            "hs_task_subject": f"Review Role Assignment: {classification_result.original_title}",
            "hs_task_body": f"""
Role Classification Review Required

Original Title: {classification_result.original_title}
Suggested Role: {classification_result.classified_role}
Confidence: {classification_result.confidence:.2%}
Reason: {reason}

Classification Details:
- Role Category: {classification_result.role_category}
- Decision Authority: {classification_result.decision_authority}
- Matched Synonyms: {', '.join(classification_result.matched_synonyms)}

Confidence Factors:
{self._format_confidence_factors(classification_result.confidence_factors)}

Please review and confirm or correct the role assignment.
            """.strip(),
            "hs_task_status": "NOT_STARTED",
            "hs_task_priority": "MEDIUM",
            "hs_task_type": "TODO",
            "hs_timestamp": int(datetime.utcnow().timestamp() * 1000),
            "hubspot_owner_id": None,  # Will be set by calling code
        }
        
        if contact_id:
            task_data["associations"] = {
                "contact": [contact_id]
            }
        
        return task_data
    
    def _format_confidence_factors(self, factors: Dict[str, float]) -> str:
        """Format confidence factors for display."""
        lines = []
        for factor, value in factors.items():
            lines.append(f"- {factor.replace('_', ' ').title()}: {value:.2f}")
        return "\n".join(lines)
    
    def get_role_messaging_strategy(self, role: str) -> Dict[str, Any]:
        """Get messaging strategy for a specific role (integration with outreach config)."""
        # This would integrate with the outreach personalization config
        # For now, return basic structure
        return {
            "focus_areas": [],
            "pain_points": [],
            "value_propositions": [],
            "messaging_tone": "professional",
            "decision_authority": self._get_role_metadata(role)[1].get("decision_authority", "unknown")
        }


def create_role_taxonomy_service(config_path: Optional[Path] = None) -> RoleTaxonomyService:
    """Factory function to create role taxonomy service."""
    return RoleTaxonomyService(config_path)
