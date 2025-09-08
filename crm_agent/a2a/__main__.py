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
        # Minimal JSON stub for environments without A2A libs
        return {
            "name": "CRMCoordinator",
            "description": "A2A-compatible CRM Coordinator agent with expanded skills",
            "url": f"http://{host}:{port}/",
            "version": "1.0.0",
            "defaultInputModes": ["text"],
            "defaultOutputModes": ["text"],
            "capabilities": {"streaming": True},
            "skills": [
                {
                    "id": "course.profile.extract",
                    "name": "Course Profile Extraction",
                    "description": "Extract comprehensive golf course profiles including management company, amenities, and key personnel.",
                    "tags": ["crm", "hubspot", "enrichment", "golf", "course-profile"],
                    "examples": [
                        "Extract profile for The Golf Club at Mansion Ridge",
                        "Identify management company and key personnel for Pebble Beach Golf Links",
                    ],
                },
                {
                    "id": "contact.roles.infer",
                    "name": "Contact Role Inference",
                    "description": "Infer contact roles and decision-making tier from job titles and company context.",
                    "tags": ["crm", "contacts", "roles", "decision-makers"],
                    "examples": [
                        "Determine decision-making tier for John Smith, General Manager at Augusta National",
                        "Infer role taxonomy for Director of Golf Operations",
                    ],
                },
                {
                    "id": "hubspot.sync",
                    "name": "HubSpot Synchronization",
                    "description": "Synchronize enriched data to HubSpot CRM with approval workflow and idempotency.",
                    "tags": ["crm", "hubspot", "sync", "approval"],
                    "examples": [
                        "Sync enriched company data to HubSpot with human approval",
                        "Update contact properties with role and decision tier",
                    ],
                },
                {
                    "id": "lead.score.compute",
                    "name": "Lead Score Computation",
                    "description": "Compute fit and intent scores for leads based on configurable criteria.",
                    "tags": ["crm", "scoring", "leads", "qualification"],
                    "examples": [
                        "Calculate lead score for private golf club prospects",
                        "Compute fit score based on course type and management company",
                    ],
                },
                {
                    "id": "outreach.generate",
                    "name": "Personalized Outreach Generation",
                    "description": "Generate grounded, role-aware email drafts and create engagement tasks.",
                    "tags": ["crm", "outreach", "personalization", "email"],
                    "examples": [
                        "Generate personalized email for General Manager at resort golf course",
                        "Create follow-up task for Director of Golf contact",
                    ],
                }
            ],
            "supportsAuthenticatedExtendedCard": True,
            "auth": {
                "type": "bearer",
                "description": "Requires HubSpot Private App access token",
                "environment_variable": "PRIVATE_APP_ACCESS_TOKEN"
            },
            "versioning": {
                "api_version": "v1.0.0",
                "compatibility": ["adk-2.0+", "a2a-1.0+"]
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


