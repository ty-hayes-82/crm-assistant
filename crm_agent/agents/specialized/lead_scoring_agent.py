#!/usr/bin/env python3
"""
Lead Scoring Agent for Phase 6 implementation.
Computes Fit and Intent scores and writes swoop_fit_score, swoop_intent_score, swoop_total_lead_score.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

from ...core.base_agents import SpecializedAgent
from ...core.state_models import CRMSessionState, CRMStateKeys


class LeadScoringAgent(SpecializedAgent):
    """Agent that computes fit and intent scores for leads based on configurable criteria."""
    
    def __init__(self, config_path: Optional[str] = None, **kwargs):
        # Load scoring configuration
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "configs" / "lead_scoring_config.json"
        
        # Initialize observability system (Phase 9)
        from ...core.observability import get_logger
        self.logger = get_logger("lead_scoring")
        
        super().__init__(
            name="LeadScoringAgent",
            domain="lead_scoring",
            specialized_tools=["get_hubspot_contact", "get_hubspot_company", "update_company", "update_contact"],
            instruction=f"""
            You are a specialized Lead Scoring agent for CRM prospect qualification.
            
            🎯 CORE RESPONSIBILITY: Compute Fit and Intent scores for leads and write 
            swoop_fit_score, swoop_intent_score, and swoop_total_lead_score to HubSpot.
            
            📊 SCORING METHODOLOGY:
            
            **Fit Score (0-100)**: Measures how well prospect aligns with Ideal Customer Profile
            - Course Type: Private (100), Resort (90), Semi-Private (70), Daily Fee (50), Municipal (30)
            - Management Company: Troon (100), ClubCorp (95), Invited (90), etc.
            - Revenue Range: 10M+ (100) down to Under 500K (25)
            - Location: California (95), Florida (90), Texas (85), etc.
            - Employee Count: 100+ (100) down to Under 5 (25)
            - Technology Stack: Modern systems (100) down to Legacy/Manual (20)
            - Amenities: Full Service (100) down to Basic (30)
            
            **Intent Score (0-100)**: Measures buying signals and engagement level
            - Website Activity: Demo requests (95), pricing pages (90), multiple visits (100)
            - Email Engagement: Multiple clicks (100), opens (80), single interactions (50-70)
            - Content Downloads: ROI Calculator (100), Case Studies (90), White Papers (80)
            - Meeting Requests: Demo scheduled (100), discovery calls (95)
            - Technology Research: Active RFP (100), comparing solutions (90)
            - Competitive Mentions: Evaluating competitors (90)
            - Recent Changes: Technology upgrades (85), new management (80)
            
            **Total Score**: Weighted average of Fit (60%) and Intent (40%)
            - Hot (80-100): Immediate outreach, 4h SLA
            - Warm (60-79): Personalized follow-up, 24h SLA  
            - Cold (40-59): Nurture campaign, 72h SLA
            - Unqualified (0-39): Long-term nurture, 168h SLA
            
            🔄 WORKFLOW:
            1. Load current contact/company data from HubSpot
            2. Extract relevant data points for scoring
            3. Calculate Fit score using ICP alignment rules
            4. Calculate Intent score using engagement signals
            5. Compute weighted total score
            6. Determine score band and recommended actions
            7. Write scores to HubSpot fields with timestamps
            8. Log scoring rationale and version
            
            📝 HUBSPOT FIELD MAPPING:
            - swoop_fit_score: Fit score (0-100)
            - swoop_intent_score: Intent score (0-100)
            - swoop_total_lead_score: Total weighted score (0-100)
            - swoop_score_band: Hot/Warm/Cold/Unqualified
            - swoop_score_updated_at: Timestamp of last scoring
            - swoop_scoring_version: Configuration version used
            
            🛡️ SAFETY MEASURES:
            - Always validate data before scoring
            - Handle missing data gracefully with default scores
            - Log all scoring decisions with rationale
            - Version scoring configuration for reproducibility
            - Allow manual score overrides with audit trail
            
            🔧 CONFIGURATION:
            Using scoring configuration version: {self._load_config(config_path).get('version', 'unknown')}
            Updated: {self._load_config(config_path).get('updated_at', 'unknown')}
            
            OUTPUT FORMAT: Scoring results with rationale and HubSpot field updates
            """,
            **kwargs
        )
        
        # Load configuration after super().__init__
        self._config = self._load_config(config_path)
    
    def score_and_store(self, state: CRMSessionState) -> Dict[str, Any]:
        """
        Compute lead scores from session state, store results, and return HubSpot field updates.
        
        Args:
            state: CRMSessionState containing company_data and contact_data
        
        Returns:
            Dict with two keys:
              - "scores": computed score bundle saved to state.lead_scores
              - "hubspot_updates": mapping of HubSpot property names to values
        """
        company_data = state.company_data or {}
        contact_data = state.contact_data or {}
        
        fit_score, fit_rationale = self.calculate_fit_score(company_data, contact_data)
        intent_score, intent_rationale = self.calculate_intent_score(company_data, contact_data)
        total_score, score_band, details = self.calculate_total_score(fit_score, intent_score)
        
        score_updated_at = datetime.utcnow().isoformat()
        scores = {
            "fit_score": round(fit_score, 2),
            "intent_score": round(intent_score, 2),
            "total_score": round(total_score, 2),
            "score_band": score_band,
            "fit_rationale": fit_rationale,
            "intent_rationale": intent_rationale,
            "details": details,
            "scoring_version": self._config.get("version", "unknown"),
            "score_updated_at": score_updated_at,
        }
        
        # Persist to session state
        state.lead_scores = scores
        state.update_timestamp()
        
        # Build HubSpot property updates based on config mapping
        mapping = self._config.get("hubspot_field_mapping", {})
        hubspot_updates = {
            mapping.get("swoop_fit_score", "swoop_fit_score"): scores["fit_score"],
            mapping.get("swoop_intent_score", "swoop_intent_score"): scores["intent_score"],
            mapping.get("swoop_total_lead_score", "swoop_total_lead_score"): scores["total_score"],
            mapping.get("score_band", "swoop_score_band"): scores["score_band"],
            mapping.get("score_updated_at", "swoop_score_updated_at"): score_updated_at,
            mapping.get("scoring_version", "swoop_scoring_version"): scores["scoring_version"],
        }
        
        # Native HubSpot scoring toggle (no-op placeholder; surfaced for later wiring)
        native_cfg = self._config.get("native_hubspot_integration", {})
        if native_cfg.get("enabled", False):
            scores["native_scoring_hint"] = {
                "enabled": True,
                "sync_direction": native_cfg.get("sync_direction", "one_way_to_hubspot"),
                "override_native": native_cfg.get("override_native", False),
            }
        
        return {"scores": scores, "hubspot_updates": hubspot_updates}
    
    def _load_config(self, config_path: Path) -> Dict[str, Any]:
        """Load lead scoring configuration from JSON file."""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            return config
        except Exception as e:
            # Fallback to basic configuration
            return {
                "version": "1.0.0-fallback",
                "fit_scoring": {"max_score": 100, "weights": {}, "rules": {}},
                "intent_scoring": {"max_score": 100, "weights": {}, "signals": {}},
                "total_score_calculation": {"fit_weight": 0.6, "intent_weight": 0.4}
            }
    
    def calculate_fit_score(self, company_data: Dict[str, Any], contact_data: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate fit score based on ICP alignment.
        
        Returns:
            Tuple of (score, rationale_dict)
        """
        fit_config = self._config.get("fit_scoring", {})
        weights = fit_config.get("weights", {})
        rules = fit_config.get("rules", {})
        
        total_score = 0.0
        rationale = {}
        
        # Course Type scoring
        course_type = company_data.get("company_type", "Unknown")
        course_type_score = rules.get("course_type", {}).get(course_type, 40)
        course_type_weight = weights.get("course_type", 0.25)
        total_score += course_type_score * course_type_weight
        rationale["course_type"] = {
            "value": course_type,
            "score": course_type_score,
            "weight": course_type_weight,
            "contribution": course_type_score * course_type_weight
        }
        
        # Management Company scoring
        mgmt_company = company_data.get("management_company", "Unknown")
        mgmt_score = rules.get("management_company", {}).get(mgmt_company, 40)
        mgmt_weight = weights.get("management_company", 0.20)
        total_score += mgmt_score * mgmt_weight
        rationale["management_company"] = {
            "value": mgmt_company,
            "score": mgmt_score,
            "weight": mgmt_weight,
            "contribution": mgmt_score * mgmt_weight
        }
        
        # Revenue Range scoring
        revenue = company_data.get("annualrevenue", "Unknown")
        revenue_range = self._categorize_revenue(revenue)
        revenue_score = rules.get("revenue_range", {}).get(revenue_range, 30)
        revenue_weight = weights.get("revenue_range", 0.15)
        total_score += revenue_score * revenue_weight
        rationale["revenue_range"] = {
            "value": revenue_range,
            "score": revenue_score,
            "weight": revenue_weight,
            "contribution": revenue_score * revenue_weight
        }
        
        # Location scoring
        location = company_data.get("state", "Unknown")
        location_score = rules.get("location", {}).get(location, 50)
        location_weight = weights.get("location", 0.10)
        total_score += location_score * location_weight
        rationale["location"] = {
            "value": location,
            "score": location_score,
            "weight": location_weight,
            "contribution": location_score * location_weight
        }
        
        # Employee Count scoring
        employees = company_data.get("numberofemployees", "Unknown")
        employee_range = self._categorize_employees(employees)
        employee_score = rules.get("employee_count", {}).get(employee_range, 35)
        employee_weight = weights.get("employee_count", 0.10)
        total_score += employee_score * employee_weight
        rationale["employee_count"] = {
            "value": employee_range,
            "score": employee_score,
            "weight": employee_weight,
            "contribution": employee_score * employee_weight
        }
        
        # Technology Stack scoring (simplified)
        tech_stack = self._assess_technology_stack(company_data)
        tech_score = rules.get("technology_stack", {}).get(tech_stack, 30)
        tech_weight = weights.get("technology_stack", 0.10)
        total_score += tech_score * tech_weight
        rationale["technology_stack"] = {
            "value": tech_stack,
            "score": tech_score,
            "weight": tech_weight,
            "contribution": tech_score * tech_weight
        }
        
        # Amenities scoring
        amenities = self._assess_amenities(company_data)
        amenities_score = rules.get("amenities", {}).get(amenities, 25)
        amenities_weight = weights.get("amenities", 0.10)
        total_score += amenities_score * amenities_weight
        rationale["amenities"] = {
            "value": amenities,
            "score": amenities_score,
            "weight": amenities_weight,
            "contribution": amenities_score * amenities_weight
        }
        
        return min(total_score, 100.0), rationale
    
    def calculate_intent_score(self, company_data: Dict[str, Any], contact_data: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate intent score based on engagement signals.
        
        Returns:
            Tuple of (score, rationale_dict)
        """
        intent_config = self._config.get("intent_scoring", {})
        weights = intent_config.get("weights", {})
        signals = intent_config.get("signals", {})
        
        total_score = 0.0
        rationale = {}
        
        # Website Activity (placeholder - would integrate with web analytics)
        website_activity = self._assess_website_activity(company_data, contact_data)
        website_score = signals.get("website_activity", {}).get(website_activity, 0)
        website_weight = weights.get("website_activity", 0.25)
        total_score += website_score * website_weight
        rationale["website_activity"] = {
            "value": website_activity,
            "score": website_score,
            "weight": website_weight,
            "contribution": website_score * website_weight
        }
        
        # Email Engagement (placeholder - would integrate with email platform)
        email_engagement = self._assess_email_engagement(contact_data)
        email_score = signals.get("email_engagement", {}).get(email_engagement, 0)
        email_weight = weights.get("email_engagement", 0.20)
        total_score += email_score * email_weight
        rationale["email_engagement"] = {
            "value": email_engagement,
            "score": email_score,
            "weight": email_weight,
            "contribution": email_score * email_weight
        }
        
        # Content Downloads (placeholder)
        content_downloads = self._assess_content_downloads(contact_data)
        content_score = signals.get("content_downloads", {}).get(content_downloads, 0)
        content_weight = weights.get("content_downloads", 0.15)
        total_score += content_score * content_weight
        rationale["content_downloads"] = {
            "value": content_downloads,
            "score": content_score,
            "weight": content_weight,
            "contribution": content_score * content_weight
        }
        
        # Meeting Requests (placeholder)
        meeting_requests = self._assess_meeting_requests(contact_data)
        meeting_score = signals.get("meeting_requests", {}).get(meeting_requests, 0)
        meeting_weight = weights.get("meeting_requests", 0.15)
        total_score += meeting_score * meeting_weight
        rationale["meeting_requests"] = {
            "value": meeting_requests,
            "score": meeting_score,
            "weight": meeting_weight,
            "contribution": meeting_score * meeting_weight
        }
        
        # For now, set remaining signals to default values
        # In production, these would integrate with actual data sources
        default_signals = ["technology_research", "competitive_mentions", "recent_changes"]
        for signal in default_signals:
            signal_weight = weights.get(signal, 0.05)
            rationale[signal] = {
                "value": "No data",
                "score": 0,
                "weight": signal_weight,
                "contribution": 0
            }
        
        return min(total_score, 100.0), rationale
    
    def calculate_total_score(self, fit_score: float, intent_score: float) -> Tuple[float, str, Dict[str, Any]]:
        """
        Calculate total weighted score and determine score band.
        
        Returns:
            Tuple of (total_score, score_band, calculation_details)
        """
        total_config = self._config.get("total_score_calculation", {})
        fit_weight = total_config.get("fit_weight", 0.6)
        intent_weight = total_config.get("intent_weight", 0.4)
        
        total_score = (fit_score * fit_weight) + (intent_score * intent_weight)
        
        # Determine score band
        score_bands = total_config.get("score_bands", {})
        if total_score >= 80:
            score_band = "Hot (80-100)"
        elif total_score >= 60:
            score_band = "Warm (60-79)"
        elif total_score >= 40:
            score_band = "Cold (40-59)"
        else:
            score_band = "Unqualified (0-39)"
        
        calculation_details = {
            "fit_score": fit_score,
            "intent_score": intent_score,
            "fit_weight": fit_weight,
            "intent_weight": intent_weight,
            "total_score": total_score,
            "score_band": score_band,
            "recommended_action": score_bands.get(score_band, {}).get("action", "Review"),
            "sla_hours": score_bands.get(score_band, {}).get("sla_hours", 72)
        }
        
        return total_score, score_band, calculation_details
    
    def _categorize_revenue(self, revenue: Any) -> str:
        """Categorize revenue into ranges."""
        if not revenue or revenue == "Unknown":
            return "Unknown"
        
        try:
            rev_val = float(revenue)
            if rev_val >= 10000000:
                return "10M+"
            elif rev_val >= 5000000:
                return "5M-10M"
            elif rev_val >= 2000000:
                return "2M-5M"
            elif rev_val >= 1000000:
                return "1M-2M"
            elif rev_val >= 500000:
                return "500K-1M"
            else:
                return "Under 500K"
        except (ValueError, TypeError):
            return "Unknown"
    
    def _categorize_employees(self, employees: Any) -> str:
        """Categorize employee count into ranges."""
        if not employees or employees == "Unknown":
            return "Unknown"
        
        try:
            emp_val = int(employees)
            if emp_val >= 100:
                return "100+"
            elif emp_val >= 50:
                return "50-100"
            elif emp_val >= 25:
                return "25-50"
            elif emp_val >= 10:
                return "10-25"
            elif emp_val >= 5:
                return "5-10"
            else:
                return "Under 5"
        except (ValueError, TypeError):
            return "Unknown"
    
    def _assess_technology_stack(self, company_data: Dict[str, Any]) -> str:
        """Assess technology stack sophistication."""
        # Simplified assessment based on available data
        # In production, would integrate with technology detection services
        website = company_data.get("website", "")
        if "teesheet" in website.lower() or "booking" in website.lower():
            return "Tee Sheet Software"
        elif website and len(website) > 10:
            return "Basic Systems"
        else:
            return "Unknown"
    
    def _assess_amenities(self, company_data: Dict[str, Any]) -> str:
        """Assess amenities and facilities."""
        club_info = company_data.get("club_info", "").lower()
        description = company_data.get("description", "").lower()
        combined_text = f"{club_info} {description}"
        
        if any(word in combined_text for word in ["dining", "restaurant", "events", "pro shop"]):
            if "dining" in combined_text and "events" in combined_text and "pro shop" in combined_text:
                return "Full Service (Dining, Events, Pro Shop)"
            elif "dining" in combined_text and "pro shop" in combined_text:
                return "Dining + Pro Shop"
            elif "pro shop" in combined_text:
                return "Pro Shop + Range"
            else:
                return "Pro Shop Only"
        elif combined_text:
            return "Basic Facilities"
        else:
            return "Unknown"
    
    def _assess_website_activity(self, company_data: Dict[str, Any], contact_data: Dict[str, Any]) -> str:
        """Assess website activity (placeholder for web analytics integration)."""
        # In production, would integrate with Google Analytics, Mixpanel, etc.
        return "No activity"
    
    def _assess_email_engagement(self, contact_data: Dict[str, Any]) -> str:
        """Assess email engagement (placeholder for email platform integration)."""
        # In production, would integrate with HubSpot email data, Mailchimp, etc.
        return "No engagement"
    
    def _assess_content_downloads(self, contact_data: Dict[str, Any]) -> str:
        """Assess content downloads (placeholder for marketing automation integration)."""
        # In production, would integrate with HubSpot forms, Marketo, etc.
        return "No downloads"
    
    def _assess_meeting_requests(self, contact_data: Dict[str, Any]) -> str:
        """Assess meeting requests (placeholder for CRM activity integration)."""
        # In production, would check HubSpot meetings, Calendly, etc.
        return "No meetings"


def create_lead_scoring_agent(config_path: Optional[str] = None, **kwargs) -> LeadScoringAgent:
    """Create a LeadScoringAgent instance."""
    return LeadScoringAgent(config_path=config_path, **kwargs)
