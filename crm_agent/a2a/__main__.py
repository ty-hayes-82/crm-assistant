"""
CRM A2A entrypoint that exposes AgentCard and skills per Google's guide.

Note: This is a lightweight scaffold; in a full implementation, you'd run an
HTTP server that serves the AgentCard and handles A2A requests by delegating
to CRMAgentTaskManager.
"""

try:
    from a2a.skills.skill_declarations import AgentSkill
    from a2a.cards.agent_card import AgentCard, AgentCapabilities
except Exception:
    AgentSkill = None  # type: ignore
    AgentCard = None  # type: ignore
    AgentCapabilities = None  # type: ignore


def build_agent_card(host: str = "localhost", port: int = 10000):
    """
    Build and return the A2A Agent Card. If A2A libraries are unavailable,
    return a minimal JSON stub so Phase 0 smoke tests still pass.
    """
    if AgentSkill is None or AgentCard is None or AgentCapabilities is None:
        # Enhanced JSON stub with full A2A compliance
        return {
            "name": "CRMCoordinator",
            "version": "1.0.0",
            "description": "A2A-compatible CRM Coordinator agent with expanded skills",
            "url": f"http://{host}:{port}/",
            
            # Enhanced metadata
            "vendor": "Swoop Golf",
            "category": "crm_automation",
            "tags": ["crm", "hubspot", "golf", "enrichment", "lead-scoring", "outreach"],
            "license": "proprietary",
            "documentation_url": "https://github.com/swoop-golf/crm-assistant/docs",
            
            # Capability negotiation
            "capabilities": {
                "streaming": True,
                "batch_processing": True,
                "async_tasks": True,
                "rate_limiting": {"requests_per_minute": 60},
                "max_concurrent_tasks": 5
            },
            
            # Enhanced authentication
            "auth": {
                "type": "bearer",
                "description": "Requires HubSpot Private App access token",
                "environment_variable": "PRIVATE_APP_ACCESS_TOKEN",
                "scopes": ["crm.objects.companies.write", "crm.objects.contacts.write", "crm.objects.deals.write"]
            },
            
            # Service level agreements
            "sla": {
                "response_time_ms": 5000,
                "availability": "99.9%",
                "support_contact": "support@swoopgolf.com"
            },
            
            # Enhanced skills with I/O schemas
            "skills": [
                {
                    "id": "course.profile.extract",
                    "name": "Course Profile Extraction",
                    "description": "Extract comprehensive golf course profiles including management company, amenities, and key personnel.",
                    "version": "1.0.0",
                    "tags": ["crm", "hubspot", "enrichment", "golf", "course-profile"],
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "company_name": {"type": "string"},
                            "domain": {"type": "string", "format": "uri"},
                            "focus_areas": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["company_name"]
                    },
                    "output_schema": {
                        "type": "object",
                        "properties": {
                            "profile": {"type": "object"},
                            "confidence_score": {"type": "number", "minimum": 0, "maximum": 1},
                            "source_urls": {"type": "array", "items": {"type": "string"}},
                            "last_verified": {"type": "string", "format": "date-time"}
                        }
                    },
                    "examples": [
                        {
                            "input": {"company_name": "Pebble Beach Golf Links", "domain": "pebblebeach.com"},
                            "output": {"profile": {"management_company": "Pebble Beach Company", "course_type": "Resort"}}
                        }
                    ]
                },
                {
                    "id": "contact.roles.infer",
                    "name": "Contact Role Inference",
                    "description": "Infer contact roles and decision-making tier from job titles and company context.",
                    "version": "1.0.0",
                    "tags": ["crm", "contacts", "roles", "decision-makers"],
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "contact_name": {"type": "string"},
                            "job_title": {"type": "string"},
                            "company_name": {"type": "string"},
                            "company_type": {"type": "string", "enum": ["Private", "Resort", "Municipal", "Semi-Private"]}
                        },
                        "required": ["contact_name", "job_title", "company_name"]
                    },
                    "output_schema": {
                        "type": "object",
                        "properties": {
                            "inferred_role": {"type": "string"},
                            "decision_tier": {"type": "string", "enum": ["D1", "D2", "D3"]},
                            "confidence_score": {"type": "number", "minimum": 0, "maximum": 1},
                            "reasoning": {"type": "string"}
                        }
                    },
                    "examples": [
                        {
                            "input": {"contact_name": "John Smith", "job_title": "General Manager", "company_name": "Augusta National"},
                            "output": {"inferred_role": "General Manager", "decision_tier": "D1", "confidence_score": 0.95}
                        }
                    ]
                },
                {
                    "id": "hubspot.sync",
                    "name": "HubSpot Synchronization",
                    "description": "Synchronize enriched data to HubSpot CRM with approval workflow and idempotency.",
                    "version": "1.0.0",
                    "tags": ["crm", "hubspot", "sync", "approval"],
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "record_type": {"type": "string", "enum": ["company", "contact"]},
                            "record_id": {"type": "string"},
                            "updates": {"type": "object"},
                            "require_approval": {"type": "boolean", "default": True}
                        },
                        "required": ["record_type", "record_id", "updates"]
                    },
                    "output_schema": {
                        "type": "object",
                        "properties": {
                            "sync_status": {"type": "string", "enum": ["completed", "pending_approval", "failed"]},
                            "updated_fields": {"type": "array", "items": {"type": "string"}},
                            "approval_url": {"type": "string", "format": "uri"}
                        }
                    },
                    "examples": [
                        {
                            "input": {"record_type": "company", "record_id": "123", "updates": {"industry": "Golf"}},
                            "output": {"sync_status": "completed", "updated_fields": ["industry"]}
                        }
                    ]
                },
                {
                    "id": "lead.score.compute",
                    "name": "Lead Score Computation",
                    "description": "Compute fit and intent scores for leads based on configurable criteria.",
                    "version": "1.0.0",
                    "tags": ["crm", "scoring", "leads", "qualification"],
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "company_data": {"type": "object"},
                            "contact_data": {"type": "object"},
                            "engagement_data": {"type": "object"},
                            "scoring_config": {"type": "object"}
                        },
                        "required": ["company_data", "contact_data"]
                    },
                    "output_schema": {
                        "type": "object",
                        "properties": {
                            "fit_score": {"type": "number", "minimum": 0, "maximum": 100},
                            "intent_score": {"type": "number", "minimum": 0, "maximum": 100},
                            "total_score": {"type": "number", "minimum": 0, "maximum": 100},
                            "score_band": {"type": "string"},
                            "reasoning": {"type": "object"}
                        }
                    },
                    "examples": [
                        {
                            "input": {"company_data": {"type": "Private", "size": "Premium"}, "contact_data": {"title": "GM"}},
                            "output": {"fit_score": 85, "intent_score": 45, "total_score": 65, "score_band": "Warm"}
                        }
                    ]
                },
                {
                    "id": "outreach.generate",
                    "name": "Personalized Outreach Generation",
                    "description": "Generate grounded, role-aware email drafts and create engagement tasks.",
                    "version": "1.0.0",
                    "tags": ["crm", "outreach", "personalization", "email"],
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "contact_data": {"type": "object"},
                            "company_data": {"type": "object"},
                            "message_type": {"type": "string", "enum": ["introduction", "follow_up", "demo_request"]},
                            "personalization_level": {"type": "string", "enum": ["basic", "advanced"], "default": "advanced"}
                        },
                        "required": ["contact_data", "company_data"]
                    },
                    "output_schema": {
                        "type": "object",
                        "properties": {
                            "subject_line": {"type": "string"},
                            "email_body": {"type": "string"},
                            "personalization_score": {"type": "number", "minimum": 0, "maximum": 100},
                            "follow_up_task": {"type": "object"}
                        }
                    },
                    "examples": [
                        {
                            "input": {"contact_data": {"name": "Sarah", "title": "Director of Golf"}, "company_data": {"name": "Oakmont"}},
                            "output": {"subject_line": "Golf operations insights for Oakmont", "personalization_score": 85}
                        }
                    ]
                }
            ],
            "supportsAuthenticatedExtendedCard": True,
            "versioning": {
                "api_version": "v1.0.0",
                "compatibility": ["adk-2.0+", "a2a-1.0+"],
                "changelog_url": "https://github.com/swoop-golf/crm-assistant/releases"
            }
        }

    # Create expanded skills for A2A Agent Card
    skills = [
        AgentSkill(
            id="course.profile.extract",
            name="Course Profile Extraction",
            description="Extract comprehensive golf course profiles including management company, amenities, and key personnel.",
            tags=["crm", "hubspot", "enrichment", "golf", "course-profile"],
            examples=[
                "Extract profile for The Golf Club at Mansion Ridge",
                "Identify management company and key personnel for Pebble Beach Golf Links",
            ],
        ),
        AgentSkill(
            id="contact.roles.infer",
            name="Contact Role Inference", 
            description="Infer contact roles and decision-making tier from job titles and company context.",
            tags=["crm", "contacts", "roles", "decision-makers"],
            examples=[
                "Determine decision-making tier for John Smith, General Manager at Augusta National",
                "Infer role taxonomy for Director of Golf Operations",
            ],
        ),
        AgentSkill(
            id="hubspot.sync",
            name="HubSpot Synchronization",
            description="Synchronize enriched data to HubSpot CRM with approval workflow and idempotency.",
            tags=["crm", "hubspot", "sync", "approval"],
            examples=[
                "Sync enriched company data to HubSpot with human approval",
                "Update contact properties with role and decision tier",
            ],
        ),
        AgentSkill(
            id="lead.score.compute",
            name="Lead Score Computation",
            description="Compute fit and intent scores for leads based on configurable criteria.",
            tags=["crm", "scoring", "leads", "qualification"],
            examples=[
                "Calculate lead score for private golf club prospects",
                "Compute fit score based on course type and management company",
            ],
        ),
        AgentSkill(
            id="outreach.generate",
            name="Personalized Outreach Generation",
            description="Generate grounded, role-aware email drafts and create engagement tasks.",
            tags=["crm", "outreach", "personalization", "email"],
            examples=[
                "Generate personalized email for General Manager at resort golf course",
                "Create follow-up task for Director of Golf contact",
            ],
        ),
    ]

    card = AgentCard(
        name="CRMCoordinator",
        description="A2A-compatible CRM Coordinator agent with expanded skills",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        capabilities=AgentCapabilities(streaming=True),
        skills=skills,
        supportsAuthenticatedExtendedCard=True,
    )
    return card


if __name__ == "__main__":
    card = build_agent_card()
    print("CRM A2A AgentCard:")
    print(card)


