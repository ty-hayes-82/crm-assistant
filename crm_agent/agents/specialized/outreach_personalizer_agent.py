#!/usr/bin/env python3
"""
Outreach Personalizer Agent for Phase 7 implementation.
Generates grounded, role-aware drafts and creates Email/Task engagements.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

from ...core.base_agents import SpecializedAgent
from ...core.state_models import CRMSessionState, CRMStateKeys
from ...core.role_taxonomy import create_role_taxonomy_service


class OutreachPersonalizerAgent(SpecializedAgent):
    """Agent that generates personalized outreach drafts and creates Email/Task engagements."""
    
    def __init__(self, config_path: Optional[str] = None, **kwargs):
        # Load personalization configuration
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "configs" / "outreach_personalization_config.json"
        
        # Initialize observability system (Phase 9)
        from ...core.observability import get_logger
        self.logger = get_logger("outreach_personalizer")
        
        # Initialize role taxonomy service
        self.role_taxonomy = create_role_taxonomy_service()
        
        super().__init__(
            name="OutreachPersonalizerAgent",
            domain="outreach_personalization",
            specialized_tools=["get_hubspot_contact", "get_hubspot_company", "create_email_engagement", "create_task"],
            instruction=f"""
            You are a specialized Outreach Personalizer agent for CRM prospect engagement.
            
            🎯 CORE RESPONSIBILITY: Generate grounded, role-aware outreach drafts and create Email/Task 
            engagements in HubSpot with proper citations and associations.
            
            📧 PERSONALIZATION METHODOLOGY:
            
            **Content Personalization**:
            - Company-specific hooks: Recent news, achievements, expansions, technology upgrades
            - Role-specific messaging: Tailor language and focus areas to recipient's job function
            - Industry insights: Golf course management trends, technology solutions, best practices
            - Competitive intelligence: Reference industry challenges and opportunities
            - Citation-backed facts: Include source URLs for all claims and statistics
            
            **Engagement Types**:
            - Cold outreach: Initial contact with value proposition
            - Follow-up: Nurture existing relationships with relevant updates
            - Demo invitation: Personalized demo requests with specific use cases
            - Content sharing: Relevant case studies, white papers, ROI calculators
            - Event invitation: Webinars, conferences, industry meetups
            
            **Role-Based Messaging**:
            - General Manager: Focus on ROI, operational efficiency, member satisfaction
            - Operations Manager: Emphasize process improvement, staff productivity, cost savings
            - F&B Manager: Highlight dining revenue, event management, customer experience
            - Golf Professional: Focus on member engagement, instruction programs, pro shop sales
            - IT Manager: Emphasize system integration, data security, technical support
            
            🔄 WORKFLOW:
            1. Analyze contact role and company profile from CRM data
            2. Extract relevant facts and citations from enrichment findings
            3. Select appropriate outreach template and messaging strategy
            4. Generate personalized subject line and email content
            5. Include citation-backed hooks and value propositions
            6. Create Email engagement draft in HubSpot (no auto-send)
            7. Create follow-up Task with due date and instructions
            8. Associate all engagements with contact and company records
            
            📝 HUBSPOT ENGAGEMENT CREATION:
            - Email: Draft email with personalized content, subject line, and citations
            - Task: Follow-up reminder with context and next steps
            - Associations: Link to contact, company, and deal records
            - Metadata: Include personalization rationale and source attribution
            
            🛡️ SAFETY MEASURES:
            - Never auto-send emails - always create as drafts for human review
            - Include source citations for all claims and statistics
            - Respect communication preferences and opt-out requests
            - Maintain professional tone and industry-appropriate language
            - Validate all contact information before creating engagements
            
            🔧 PERSONALIZATION FACTORS:
            - Company size and type (Private, Resort, Municipal, etc.)
            - Management company affiliation
            - Recent company news and developments
            - Technology stack and modernization needs
            - Seasonal business patterns and challenges
            - Competitive landscape and positioning
            
            OUTPUT FORMAT: Engagement creation results with personalization rationale
            """,
            **kwargs
        )
        
        # Load configuration after super().__init__
        self._config = self._load_config(config_path)
    
    def generate_personalized_outreach(self, state: CRMSessionState, outreach_type: str = "cold_outreach") -> Dict[str, Any]:
        """
        Generate personalized outreach content and create HubSpot engagements.
        
        Args:
            state: CRMSessionState containing company_data, contact_data, and enrichment findings
            outreach_type: Type of outreach (cold_outreach, follow_up, demo_invitation, etc.)
        
        Returns:
            Dict with engagement creation results and personalization details
        """
        company_data = state.company_data or {}
        contact_data = state.contact_data or {}
        enrichment_findings = getattr(state, 'normalized_insights', {})
        lead_scores = getattr(state, 'lead_scores', {})
        
        # Analyze contact role and company profile
        role_analysis = self._analyze_contact_role(contact_data, company_data)
        company_profile = self._analyze_company_profile(company_data, enrichment_findings)
        
        # Generate personalized content
        personalization = self._generate_personalization(
            role_analysis, company_profile, lead_scores, outreach_type
        )
        
        # Create email draft
        email_result = self._create_email_draft(
            contact_data, company_data, personalization, state
        )
        
        # Create follow-up task
        task_result = self._create_follow_up_task(
            contact_data, company_data, personalization, outreach_type, state
        )
        
        # Store results in session state
        outreach_results = {
            "outreach_type": outreach_type,
            "personalization": personalization,
            "email_engagement": email_result,
            "follow_up_task": task_result,
            "created_at": datetime.utcnow().isoformat(),
            "role_analysis": role_analysis,
            "company_profile": company_profile
        }
        
        state.outreach_results = outreach_results
        state.update_timestamp()
        
        return outreach_results
    
    def _load_config(self, config_path: Path) -> Dict[str, Any]:
        """Load outreach personalization configuration from JSON file."""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            return config
        except Exception as e:
            # Fallback to basic configuration
            return {
                "version": "1.0.0-fallback",
                "outreach_templates": {},
                "role_messaging": {},
                "personalization_rules": {}
            }
    
    def _analyze_contact_role(self, contact_data: Dict[str, Any], company_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analyze contact role and determine messaging strategy using centralized taxonomy."""
        job_title = contact_data.get("jobtitle", "")
        
        # Use centralized role taxonomy service
        classification_result = self.role_taxonomy.classify_role(
            job_title=job_title,
            company_context=company_data,
            additional_context=contact_data
        )
        
        # Get messaging strategy for the classified role
        messaging_strategy = self.role_taxonomy.get_role_messaging_strategy(classification_result.classified_role)
        
        return {
            "original_title": classification_result.original_title,
            "role_type": classification_result.classified_role,
            "role_category": classification_result.role_category,
            "confidence": classification_result.confidence,
            "requires_review": classification_result.requires_review,
            "messaging_focus": self._get_role_messaging_focus(classification_result.classified_role),
            "decision_authority": classification_result.decision_authority,
            "pain_points": self._get_role_pain_points(classification_result.classified_role),
            "classification_metadata": {
                "matched_synonyms": classification_result.matched_synonyms,
                "confidence_factors": classification_result.confidence_factors,
                "classification_timestamp": classification_result.classification_timestamp.isoformat(),
                "classification_version": classification_result.classification_version
            }
        }
    
    def _analyze_company_profile(self, company_data: Dict[str, Any], enrichment_findings: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze company profile for personalization hooks."""
        company_name = company_data.get("name", "")
        company_type = company_data.get("company_type", "Unknown")
        management_company = company_data.get("management_company", "Independent")
        website = company_data.get("website", "")
        
        # Extract personalization hooks from enrichment findings
        personalization_hooks = []
        recent_news = enrichment_findings.get("recent_news", [])
        technology_info = enrichment_findings.get("technology_stack", {})
        
        # Company size and sophistication
        sophistication_level = self._assess_sophistication_level(company_data, technology_info)
        
        # Competitive positioning
        competitive_context = self._analyze_competitive_context(company_data, management_company)
        
        return {
            "name": company_name,
            "type": company_type,
            "management_company": management_company,
            "sophistication_level": sophistication_level,
            "personalization_hooks": personalization_hooks,
            "competitive_context": competitive_context,
            "website": website,
            "technology_maturity": technology_info.get("maturity", "unknown")
        }
    
    def _generate_personalization(self, role_analysis: Dict[str, Any], company_profile: Dict[str, Any], 
                                 lead_scores: Dict[str, Any], outreach_type: str) -> Dict[str, Any]:
        """Generate personalized content based on role and company analysis."""
        
        # Select messaging strategy
        messaging_strategy = self._select_messaging_strategy(role_analysis, company_profile, lead_scores)
        
        # Generate subject line
        subject_line = self._generate_subject_line(
            role_analysis, company_profile, messaging_strategy, outreach_type
        )
        
        # Generate email content
        email_content = self._generate_email_content(
            role_analysis, company_profile, messaging_strategy, outreach_type
        )
        
        # Generate call-to-action
        cta = self._generate_call_to_action(role_analysis, messaging_strategy, outreach_type)
        
        return {
            "messaging_strategy": messaging_strategy,
            "subject_line": subject_line,
            "email_content": email_content,
            "call_to_action": cta,
            "personalization_score": self._calculate_personalization_score(role_analysis, company_profile),
            "citations": self._extract_citations(company_profile)
        }
    
    def _create_email_draft(self, contact_data: Dict[str, Any], company_data: Dict[str, Any],
                           personalization: Dict[str, Any], state: CRMSessionState) -> Dict[str, Any]:
        """Create email engagement draft in HubSpot."""
        
        email_content = f"""
{personalization['email_content']}

{personalization['call_to_action']}

Best regards,
[Your Name]
[Your Title]
[Company]

---
Sources and References:
{self._format_citations(personalization['citations'])}
        """.strip()
        
        # Prepare email engagement data
        email_data = {
            "engagement_type": "EMAIL",
            "subject": personalization['subject_line'],
            "body": email_content,
            "to_email": contact_data.get("email", ""),
            "contact_id": contact_data.get("id"),
            "company_id": company_data.get("id"),
            "metadata": {
                "outreach_type": "personalized_outreach",
                "personalization_score": personalization['personalization_score'],
                "messaging_strategy": personalization['messaging_strategy'],
                "auto_send": False,  # Always create as draft
                "created_by": "OutreachPersonalizerAgent"
            }
        }
        
        # PHASE 1 PROVENANCE GATE: Validate citations before creating engagement
        citations = personalization.get('citations', [])
        citation_requirements = self._config.get('citation_requirements', {})
        
        if citation_requirements.get('required', True):
            missing_citations = []
            for claim_type in citation_requirements.get('required_for', ['company_facts', 'statistics', 'claims']):
                if not any(cite.get('type') == claim_type for cite in citations):
                    missing_citations.append(claim_type)
            
            if missing_citations:
                error_message = f"Citation validation failed: Missing citations for {', '.join(missing_citations)}"
                return {
                    "status": "blocked_by_provenance",
                    "error_type": "citation_validation_failed",
                    "error_message": error_message,
                    "missing_citations": missing_citations,
                    "blocked_write": True
                }
        
        # Note: In production, this would call HubSpot API via OpenAPI tools
        # For now, return the structured data that would be sent
        return {
            "status": "draft_created",
            "email_data": email_data,
            "engagement_id": f"draft_{datetime.utcnow().timestamp()}",
            "message": "Email draft created successfully (not sent)",
            "citations_validated": len(citations)
        }
    
    def _create_follow_up_task(self, contact_data: Dict[str, Any], company_data: Dict[str, Any],
                              personalization: Dict[str, Any], outreach_type: str, 
                              state: CRMSessionState) -> Dict[str, Any]:
        """Create follow-up task in HubSpot."""
        
        # Determine follow-up timeline based on lead score
        lead_scores = getattr(state, 'lead_scores', {})
        score_band = lead_scores.get('score_band', 'Cold (40-59)')
        
        if 'Hot' in score_band:
            follow_up_days = 1
        elif 'Warm' in score_band:
            follow_up_days = 3
        elif 'Cold' in score_band:
            follow_up_days = 7
        else:
            follow_up_days = 14
        
        due_date = datetime.utcnow() + timedelta(days=follow_up_days)
        
        task_title = f"Follow up on {outreach_type} - {company_data.get('name', 'Unknown Company')}"
        task_notes = f"""
Follow up on personalized outreach sent to {contact_data.get('firstname', '')} {contact_data.get('lastname', '')}.

Outreach Details:
- Type: {outreach_type}
- Subject: {personalization['subject_line']}
- Messaging Strategy: {personalization['messaging_strategy']}
- Personalization Score: {personalization['personalization_score']}/100

Next Steps:
1. Check if email was opened/clicked
2. If no response, consider phone follow-up
3. Prepare additional relevant content based on their interests
4. Update CRM with any new information gathered

Lead Score Context:
- Score Band: {score_band}
- Total Score: {lead_scores.get('total_score', 'Unknown')}
        """.strip()
        
        # Prepare task data
        task_data = {
            "task_type": "FOLLOW_UP",
            "title": task_title,
            "notes": task_notes,
            "due_date": due_date.isoformat(),
            "priority": "MEDIUM" if 'Hot' in score_band else "LOW",
            "contact_id": contact_data.get("id"),
            "company_id": company_data.get("id"),
            "metadata": {
                "outreach_type": outreach_type,
                "lead_score_band": score_band,
                "created_by": "OutreachPersonalizerAgent"
            }
        }
        
        # Note: In production, this would call HubSpot API via OpenAPI tools
        return {
            "status": "task_created",
            "task_data": task_data,
            "task_id": f"task_{datetime.utcnow().timestamp()}",
            "due_date": due_date.isoformat(),
            "message": "Follow-up task created successfully"
        }
    
    # Helper methods for personalization logic
    
    def _get_role_messaging_focus(self, role_type: str) -> List[str]:
        """Get messaging focus areas for role type."""
        focus_map = {
            "general_manager": ["ROI", "operational_efficiency", "member_satisfaction", "revenue_growth"],
            "operations_manager": ["process_improvement", "staff_productivity", "cost_savings", "workflow_optimization"],
            "fb_manager": ["dining_revenue", "event_management", "customer_experience", "inventory_management"],
            "golf_professional": ["member_engagement", "instruction_programs", "pro_shop_sales", "tournament_management"],
            "it_manager": ["system_integration", "data_security", "technical_support", "automation"],
            "marketing_sales": ["lead_generation", "member_retention", "brand_awareness", "digital_marketing"]
        }
        return focus_map.get(role_type, ["operational_efficiency", "cost_savings"])
    
    def _assess_decision_authority(self, role_type: str) -> str:
        """Assess decision-making authority level."""
        authority_map = {
            "general_manager": "high",
            "operations_manager": "medium",
            "fb_manager": "medium",
            "golf_professional": "medium",
            "it_manager": "medium",
            "marketing_sales": "low"
        }
        return authority_map.get(role_type, "low")
    
    def _get_role_pain_points(self, role_type: str) -> List[str]:
        """Get common pain points for role type."""
        pain_points_map = {
            "general_manager": ["declining_membership", "operational_costs", "staff_turnover", "technology_gaps"],
            "operations_manager": ["manual_processes", "scheduling_conflicts", "maintenance_costs", "staff_coordination"],
            "fb_manager": ["food_costs", "event_coordination", "inventory_waste", "seasonal_fluctuations"],
            "golf_professional": ["lesson_scheduling", "equipment_sales", "member_engagement", "tournament_logistics"],
            "it_manager": ["system_integration", "data_silos", "security_concerns", "legacy_systems"],
            "marketing_sales": ["lead_quality", "conversion_rates", "member_retention", "digital_presence"]
        }
        return pain_points_map.get(role_type, ["operational_inefficiencies"])
    
    def _assess_sophistication_level(self, company_data: Dict[str, Any], technology_info: Dict[str, Any]) -> str:
        """Assess company sophistication level."""
        revenue = company_data.get("annualrevenue", 0)
        employees = company_data.get("numberofemployees", 0)
        company_type = company_data.get("company_type", "")
        
        # Basic scoring
        score = 0
        if revenue and revenue > 5000000:
            score += 2
        elif revenue and revenue > 1000000:
            score += 1
        
        if employees and employees > 50:
            score += 2
        elif employees and employees > 20:
            score += 1
        
        if company_type in ["Private", "Resort"]:
            score += 2
        elif company_type == "Semi-Private":
            score += 1
        
        if score >= 5:
            return "high"
        elif score >= 3:
            return "medium"
        else:
            return "low"
    
    def _analyze_competitive_context(self, company_data: Dict[str, Any], management_company: str) -> Dict[str, Any]:
        """Analyze competitive positioning context."""
        return {
            "management_company": management_company,
            "is_managed": management_company != "Independent",
            "competitive_advantages": self._identify_competitive_advantages(company_data),
            "market_position": self._assess_market_position(company_data)
        }
    
    def _identify_competitive_advantages(self, company_data: Dict[str, Any]) -> List[str]:
        """Identify potential competitive advantages."""
        advantages = []
        
        company_type = company_data.get("company_type", "")
        if company_type == "Private":
            advantages.append("exclusive_membership")
        elif company_type == "Resort":
            advantages.append("destination_appeal")
        
        description = company_data.get("description", "").lower()
        if "championship" in description:
            advantages.append("championship_course")
        if "oceanfront" in description or "waterfront" in description:
            advantages.append("scenic_location")
        
        return advantages
    
    def _assess_market_position(self, company_data: Dict[str, Any]) -> str:
        """Assess market position."""
        revenue = company_data.get("annualrevenue", 0)
        company_type = company_data.get("company_type", "")
        
        if company_type == "Private" and revenue and revenue > 10000000:
            return "premium"
        elif company_type in ["Private", "Resort"] and revenue and revenue > 2000000:
            return "upscale"
        elif company_type == "Semi-Private":
            return "mid_market"
        else:
            return "value"
    
    def _select_messaging_strategy(self, role_analysis: Dict[str, Any], company_profile: Dict[str, Any], 
                                  lead_scores: Dict[str, Any]) -> str:
        """Select appropriate messaging strategy."""
        role_type = role_analysis['role_type']
        sophistication = company_profile['sophistication_level']
        score_band = lead_scores.get('score_band', 'Cold')
        
        if 'Hot' in score_band:
            return "direct_value_proposition"
        elif role_type == "general_manager" and sophistication == "high":
            return "strategic_partnership"
        elif role_type in ["operations_manager", "it_manager"]:
            return "operational_efficiency"
        elif sophistication == "low":
            return "education_first"
        else:
            return "industry_insights"
    
    def _generate_subject_line(self, role_analysis: Dict[str, Any], company_profile: Dict[str, Any],
                              messaging_strategy: str, outreach_type: str) -> str:
        """Generate personalized subject line."""
        company_name = company_profile['name']
        role_type = role_analysis['role_type']
        
        subject_templates = {
            "direct_value_proposition": f"ROI opportunity for {company_name}",
            "strategic_partnership": f"Partnership opportunity - {company_name}",
            "operational_efficiency": f"Streamline operations at {company_name}",
            "education_first": f"Golf course management insights for {company_name}",
            "industry_insights": f"Industry trends relevant to {company_name}"
        }
        
        return subject_templates.get(messaging_strategy, f"Opportunity for {company_name}")
    
    def _generate_email_content(self, role_analysis: Dict[str, Any], company_profile: Dict[str, Any],
                               messaging_strategy: str, outreach_type: str) -> str:
        """Generate personalized email content."""
        company_name = company_profile['name']
        role_type = role_analysis['role_type']
        first_name = "there"  # Would be filled from contact data
        
        content_templates = {
            "direct_value_proposition": f"""
Hi {first_name},

I noticed {company_name} is a {company_profile['type']} course, and I wanted to share how we've helped similar properties increase operational efficiency by 25% while reducing costs.

Specifically for {role_type.replace('_', ' ').title()} roles, our clients typically see:
• Streamlined daily operations
• Improved member satisfaction scores
• Reduced administrative overhead

Would you be interested in a brief conversation about how this might apply to {company_name}?
            """.strip(),
            
            "strategic_partnership": f"""
Hi {first_name},

I've been following {company_name}'s growth and was impressed by your commitment to excellence in member experience.

As someone in golf course management, you know that staying ahead of operational challenges requires the right technology partnerships. We've helped {company_profile['type']} courses like yours implement solutions that drive both efficiency and member satisfaction.

I'd love to explore how we might support {company_name}'s continued success.
            """.strip(),
            
            "operational_efficiency": f"""
Hi {first_name},

Managing operations at {company_name} likely involves juggling multiple systems and processes daily. 

I wanted to reach out because we've helped {company_profile['type']} courses streamline their operations, typically resulting in:
• 30% reduction in administrative tasks
• Better staff coordination and scheduling
• Improved data visibility across departments

Would you have 15 minutes to discuss how this might benefit {company_name}?
            """.strip()
        }
        
        return content_templates.get(messaging_strategy, f"Hello, I wanted to reach out regarding opportunities for {company_name}.")
    
    def _generate_call_to_action(self, role_analysis: Dict[str, Any], messaging_strategy: str, outreach_type: str) -> str:
        """Generate appropriate call-to-action."""
        authority = role_analysis['decision_authority']
        
        if authority == "high":
            return "Would you be available for a brief 15-minute call this week to explore this opportunity?"
        elif authority == "medium":
            return "I'd be happy to share some relevant case studies. Would you like me to send them over?"
        else:
            return "Would you be the right person to discuss this, or should I connect with someone else on your team?"
    
    def _calculate_personalization_score(self, role_analysis: Dict[str, Any], company_profile: Dict[str, Any]) -> int:
        """Calculate personalization quality score."""
        score = 50  # Base score
        
        # Role-specific messaging
        if role_analysis['role_type'] != "general":
            score += 20
        
        # Company-specific hooks
        if company_profile['personalization_hooks']:
            score += 15
        
        # Sophistication matching
        if company_profile['sophistication_level'] != "unknown":
            score += 10
        
        # Competitive context
        if company_profile['competitive_context']['competitive_advantages']:
            score += 5
        
        return min(score, 100)
    
    def _extract_citations(self, company_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract citations from company profile."""
        # Placeholder for citation extraction
        return [
            {
                "claim": "Industry statistics",
                "source": "Golf Industry Association Report 2024",
                "url": "https://example.com/golf-industry-report"
            }
        ]
    
    def _format_citations(self, citations: List[Dict[str, Any]]) -> str:
        """Format citations for email footer."""
        if not citations:
            return "Industry data from various golf management sources."
        
        formatted = []
        for i, citation in enumerate(citations, 1):
            formatted.append(f"{i}. {citation['claim']}: {citation['source']} ({citation.get('url', 'Internal source')})")
        
        return "\n".join(formatted)


def create_outreach_personalizer_agent(config_path: Optional[str] = None, **kwargs) -> OutreachPersonalizerAgent:
    """Create an OutreachPersonalizerAgent instance."""
    return OutreachPersonalizerAgent(config_path=config_path, **kwargs)
