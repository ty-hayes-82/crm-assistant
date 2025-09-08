"""
MCP Prompts implementation for pre-written templates.
Provides standardized prompt templates following MCP protocol.
"""

from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
import json

try:
    from mcp import Prompt
    MCP_AVAILABLE = True
except ImportError:
    # Fallback if MCP not available
    class Prompt:
        def __init__(self, name: str, description: str, template: str):
            self.name = name
            self.description = description
            self.template = template
    MCP_AVAILABLE = False


class BaseMCPPrompt(Prompt, ABC):
    """Base class for MCP prompts with common functionality."""
    
    def __init__(self, name: str, description: str, template: str, 
                 variables: Optional[List[str]] = None, 
                 examples: Optional[List[Dict[str, Any]]] = None):
        super().__init__(name=name, description=description, template=template)
        self.variables = variables or []
        self.examples = examples or []
    
    def render(self, **kwargs) -> str:
        """Render the prompt template with provided variables."""
        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            missing_var = str(e).strip("'")
            raise ValueError(f"Missing required variable: {missing_var}")
    
    def validate_variables(self, variables: Dict[str, Any]) -> List[str]:
        """Validate that all required variables are provided."""
        missing = []
        for var in self.variables:
            if var not in variables:
                missing.append(var)
        return missing
    
    def get_example_usage(self) -> Optional[str]:
        """Get an example of how to use this prompt."""
        if self.examples:
            example = self.examples[0]
            return self.render(**example)
        return None


class CompanyEnrichmentPrompt(BaseMCPPrompt):
    """Template for company data enrichment."""
    
    def __init__(self):
        template = """
Enrich the following company record with accurate, verifiable information:

Company: {company_name}
Domain: {domain}
Current Data: {current_data}

Focus on: {focus_areas}

Requirements:
- Include source URLs for all claims
- Verify information recency
- Follow data quality standards
- Provide confidence scores for each field
- Use structured JSON output format

Output Format:
{{
    "enriched_data": {{
        "field_name": {{
            "value": "enriched_value",
            "confidence": 0.95,
            "source_url": "https://...",
            "last_verified": "2025-01-XX"
        }}
    }},
    "summary": "Brief summary of changes made",
    "quality_score": 0.85
}}

Focus Areas: {focus_areas}
"""
        
        super().__init__(
            name="enrich_company",
            description="Template for company data enrichment with quality standards",
            template=template.strip(),
            variables=["company_name", "domain", "current_data", "focus_areas"],
            examples=[
                {
                    "company_name": "Pebble Beach Golf Links",
                    "domain": "pebblebeach.com",
                    "current_data": '{"industry": "Golf", "location": "California"}',
                    "focus_areas": "management company, amenities, course details"
                }
            ]
        )


class ContactRoleInferencePrompt(BaseMCPPrompt):
    """Template for inferring contact roles and decision-making tiers."""
    
    def __init__(self):
        template = """
Analyze the following contact information to infer their role and decision-making tier:

Contact Information:
- Name: {contact_name}
- Job Title: {job_title}
- Company: {company_name}
- Company Type: {company_type}
- Additional Context: {additional_context}

Role Taxonomy Options:
- General Manager (GM)
- Director of Golf
- Head Professional
- Golf Superintendent  
- Membership Director
- Food & Beverage Manager
- Owner/Board Member
- IT Manager
- Operations Manager

Decision Tiers:
- D1: Primary Decision Maker (final approval authority)
- D2: Influencer (significant input on decisions)
- D3: Champion (advocates for solutions internally)

Analysis Requirements:
- Consider industry context (golf/hospitality)
- Evaluate authority level based on title and company size
- Assess budget influence and procurement involvement
- Provide confidence score for role classification

Output Format:
{{
    "inferred_role": "role_name",
    "decision_tier": "D1|D2|D3",
    "confidence_score": 0.85,
    "reasoning": "Explanation of role inference",
    "authority_areas": ["budget", "operations", "technology"],
    "personalization_hooks": ["specific interests or responsibilities"]
}}
"""
        
        super().__init__(
            name="infer_contact_role",
            description="Template for contact role inference and decision tier classification",
            template=template.strip(),
            variables=["contact_name", "job_title", "company_name", "company_type", "additional_context"],
            examples=[
                {
                    "contact_name": "John Smith",
                    "job_title": "General Manager",
                    "company_name": "Augusta National Golf Club",
                    "company_type": "Private Golf Club",
                    "additional_context": "Oversees daily operations and member services"
                }
            ]
        )


class LeadScoringPrompt(BaseMCPPrompt):
    """Template for lead scoring analysis."""
    
    def __init__(self):
        template = """
Calculate lead scores for the following prospect based on fit and intent criteria:

Company Information:
{company_data}

Contact Information:
{contact_data}

Scoring Criteria:
Fit Score (0-100):
- Company size and type alignment
- Technology stack compatibility  
- Geographic location
- Industry vertical match
- Budget indicators

Intent Score (0-100):
- Recent website activity
- Content engagement
- Email interactions
- Sales touchpoints
- Competitive research

Current Engagement Data:
{engagement_data}

Scoring Rules:
{scoring_rules}

Analysis Requirements:
- Calculate separate fit and intent scores
- Provide detailed rationale for each score component
- Suggest next best actions based on score band
- Include confidence level for scoring accuracy

Output Format:
{{
    "fit_score": 75,
    "intent_score": 45,
    "total_score": 60,
    "score_band": "Warm Lead",
    "fit_breakdown": {{
        "company_size": {{score: 20, max: 25, reason: "..."}},
        "industry_match": {{score: 15, max: 20, reason: "..."}}
    }},
    "intent_breakdown": {{
        "website_activity": {{score: 10, max: 25, reason: "..."}},
        "email_engagement": {{score: 5, max: 15, reason: "..."}}
    }},
    "recommended_actions": ["action1", "action2"],
    "confidence": 0.88
}}
"""
        
        super().__init__(
            name="score_lead",
            description="Template for comprehensive lead scoring analysis",
            template=template.strip(),
            variables=["company_data", "contact_data", "engagement_data", "scoring_rules"],
            examples=[
                {
                    "company_data": '{"name": "Pine Valley Golf Club", "type": "Private", "size": "Premium"}',
                    "contact_data": '{"name": "Mike Johnson", "title": "General Manager"}',
                    "engagement_data": '{"website_visits": 3, "email_opens": 2}',
                    "scoring_rules": '{"fit_weights": {"size": 0.3, "type": 0.4}, "intent_weights": {"activity": 0.6}}'
                }
            ]
        )


class OutreachPersonalizationPrompt(BaseMCPPrompt):
    """Template for personalized outreach generation."""
    
    def __init__(self):
        template = """
Generate a personalized outreach message for the following prospect:

Recipient Information:
- Name: {contact_name}
- Title: {job_title}
- Company: {company_name}
- Role: {inferred_role}
- Decision Tier: {decision_tier}

Company Context:
{company_context}

Personalization Data:
{personalization_data}

Outreach Strategy:
- Message Type: {message_type}
- Tone: {tone}
- Primary Goal: {primary_goal}
- Call-to-Action: {call_to_action}

Requirements:
- Reference specific company details or challenges
- Align with recipient's role and responsibilities
- Include relevant industry insights
- Provide clear value proposition
- Professional but approachable tone
- Include credible social proof when relevant

Output Format:
{{
    "subject_line": "Compelling subject that mentions company or role",
    "email_body": "Full email content with personalization",
    "personalization_score": 85,
    "key_hooks": ["specific personalization elements used"],
    "follow_up_strategy": "Recommended next steps",
    "compliance_check": {{
        "spam_risk": "Low",
        "professional_tone": true,
        "clear_opt_out": true
    }}
}}

Company Context: {company_context}
Personalization Data: {personalization_data}
"""
        
        super().__init__(
            name="generate_outreach",
            description="Template for personalized outreach message generation",
            template=template.strip(),
            variables=[
                "contact_name", "job_title", "company_name", "inferred_role", 
                "decision_tier", "company_context", "personalization_data",
                "message_type", "tone", "primary_goal", "call_to_action"
            ],
            examples=[
                {
                    "contact_name": "Sarah Williams",
                    "job_title": "Director of Golf",
                    "company_name": "Oakmont Country Club",
                    "inferred_role": "Director of Golf",
                    "decision_tier": "D1",
                    "company_context": "Historic private club known for championship tournaments",
                    "personalization_data": "Recently hosted major tournament, focus on member experience",
                    "message_type": "Introduction",
                    "tone": "Professional",
                    "primary_goal": "Schedule discovery call",
                    "call_to_action": "15-minute conversation about golf operations"
                }
            ]
        )


class DataQualityAnalysisPrompt(BaseMCPPrompt):
    """Template for data quality analysis and recommendations."""
    
    def __init__(self):
        template = """
Analyze the data quality for the following CRM record and provide improvement recommendations:

Record Type: {record_type}
Record Data: {record_data}

Quality Criteria:
- Completeness: All required fields populated
- Accuracy: Data appears correct and current
- Consistency: Format and values align with standards
- Timeliness: Information is recent and relevant
- Uniqueness: No duplicate or conflicting data

Field Requirements:
{field_requirements}

Analysis Focus:
- Identify missing critical fields
- Flag potentially outdated information
- Detect format inconsistencies
- Suggest data enrichment opportunities
- Prioritize fixes by business impact

Output Format:
{{
    "overall_quality_score": 75,
    "completeness_score": 80,
    "accuracy_score": 70,
    "field_analysis": {{
        "field_name": {{
            "status": "missing|incomplete|outdated|good",
            "current_value": "...",
            "confidence": 0.85,
            "recommendation": "specific action to take"
        }}
    }},
    "priority_fixes": [
        {{
            "field": "field_name",
            "priority": "high|medium|low",
            "impact": "business impact description",
            "suggested_source": "where to find correct data"
        }}
    ],
    "enrichment_opportunities": ["list of potential enhancements"]
}}

Field Requirements: {field_requirements}
"""
        
        super().__init__(
            name="analyze_data_quality",
            description="Template for comprehensive data quality analysis",
            template=template.strip(),
            variables=["record_type", "record_data", "field_requirements"],
            examples=[
                {
                    "record_type": "Company",
                    "record_data": '{"name": "Golf Club", "domain": "example.com", "phone": null}',
                    "field_requirements": '{"required": ["name", "domain", "phone"], "optional": ["address", "description"]}'
                }
            ]
        )


class MCPPromptRegistry:
    """Registry for managing MCP prompts."""
    
    def __init__(self):
        self.prompts: Dict[str, BaseMCPPrompt] = {}
        self._register_default_prompts()
    
    def _register_default_prompts(self):
        """Register default system prompts."""
        self.register_prompt(CompanyEnrichmentPrompt())
        self.register_prompt(ContactRoleInferencePrompt())
        self.register_prompt(LeadScoringPrompt())
        self.register_prompt(OutreachPersonalizationPrompt())
        self.register_prompt(DataQualityAnalysisPrompt())
    
    def register_prompt(self, prompt: BaseMCPPrompt):
        """Register a prompt in the registry."""
        self.prompts[prompt.name] = prompt
    
    def get_prompt(self, name: str) -> Optional[BaseMCPPrompt]:
        """Get a prompt by name."""
        return self.prompts.get(name)
    
    def list_prompts(self) -> List[Dict[str, Any]]:
        """List all available prompts."""
        return [
            {
                "name": prompt.name,
                "description": prompt.description,
                "variables": prompt.variables,
                "example_count": len(prompt.examples)
            }
            for prompt in self.prompts.values()
        ]
    
    def render_prompt(self, name: str, **kwargs) -> str:
        """Render a prompt with provided variables."""
        prompt = self.get_prompt(name)
        if not prompt:
            raise ValueError(f"Prompt not found: {name}")
        
        # Validate variables
        missing = prompt.validate_variables(kwargs)
        if missing:
            raise ValueError(f"Missing required variables: {', '.join(missing)}")
        
        return prompt.render(**kwargs)


# Global prompt registry
_prompt_registry = None


def get_mcp_prompt_registry() -> MCPPromptRegistry:
    """Get the global MCP prompt registry."""
    global _prompt_registry
    if _prompt_registry is None:
        _prompt_registry = MCPPromptRegistry()
    return _prompt_registry


# Convenience functions
def render_company_enrichment_prompt(company_name: str, domain: str, 
                                   current_data: str, focus_areas: str) -> str:
    """Render company enrichment prompt with provided data."""
    registry = get_mcp_prompt_registry()
    return registry.render_prompt(
        "enrich_company",
        company_name=company_name,
        domain=domain,
        current_data=current_data,
        focus_areas=focus_areas
    )


def render_contact_role_prompt(contact_name: str, job_title: str, 
                             company_name: str, company_type: str, 
                             additional_context: str = "") -> str:
    """Render contact role inference prompt."""
    registry = get_mcp_prompt_registry()
    return registry.render_prompt(
        "infer_contact_role",
        contact_name=contact_name,
        job_title=job_title,
        company_name=company_name,
        company_type=company_type,
        additional_context=additional_context
    )


def render_lead_scoring_prompt(company_data: str, contact_data: str,
                             engagement_data: str, scoring_rules: str) -> str:
    """Render lead scoring prompt."""
    registry = get_mcp_prompt_registry()
    return registry.render_prompt(
        "score_lead",
        company_data=company_data,
        contact_data=contact_data,
        engagement_data=engagement_data,
        scoring_rules=scoring_rules
    )


def render_outreach_prompt(contact_name: str, job_title: str, company_name: str,
                         inferred_role: str, decision_tier: str, company_context: str,
                         personalization_data: str, message_type: str = "Introduction",
                         tone: str = "Professional", primary_goal: str = "Schedule call",
                         call_to_action: str = "Brief conversation") -> str:
    """Render personalized outreach prompt."""
    registry = get_mcp_prompt_registry()
    return registry.render_prompt(
        "generate_outreach",
        contact_name=contact_name,
        job_title=job_title,
        company_name=company_name,
        inferred_role=inferred_role,
        decision_tier=decision_tier,
        company_context=company_context,
        personalization_data=personalization_data,
        message_type=message_type,
        tone=tone,
        primary_goal=primary_goal,
        call_to_action=call_to_action
    )


def render_data_quality_prompt(record_type: str, record_data: str, 
                             field_requirements: str) -> str:
    """Render data quality analysis prompt."""
    registry = get_mcp_prompt_registry()
    return registry.render_prompt(
        "analyze_data_quality",
        record_type=record_type,
        record_data=record_data,
        field_requirements=field_requirements
    )
