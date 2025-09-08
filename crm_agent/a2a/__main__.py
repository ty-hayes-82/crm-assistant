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
            "description": "A2A-compatible CRM Coordinator agent (stub)",
            "url": f"http://{host}:{port}/",
            "version": "1.0.0",
            "defaultInputModes": ["text"],
            "defaultOutputModes": ["text"],
            "capabilities": {"streaming": True},
            "skills": [
                {
                    "id": "CRMCoordinator",
                    "name": "CRM_Coordinator_Agent",
                    "description": "Agent to analyze and enrich HubSpot company/contact records.",
                    "tags": ["crm", "hubspot", "enrichment", "management_company"],
                    "examples": [
                        "Analyze The Golf Club at Mansion Ridge and provide company intelligence",
                        "Identify the management company for The Golf Club at Mansion Ridge",
                    ],
                }
            ],
            "supportsAuthenticatedExtendedCard": True,
        }

    skill = AgentSkill(
        id="CRMCoordinator",
        name="CRM_Coordinator_Agent",
        description="Agent to analyze and enrich HubSpot company/contact records.",
        tags=["crm", "hubspot", "enrichment", "management_company"],
        examples=[
            "Analyze The Golf Club at Mansion Ridge and provide company intelligence",
            "Identify the management company for The Golf Club at Mansion Ridge",
        ],
    )

    card = AgentCard(
        name="CRMCoordinator",
        description="A2A-compatible CRM Coordinator agent.",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[skill],
        supportsAuthenticatedExtendedCard=True,
    )
    return card


if __name__ == "__main__":
    card = build_agent_card()
    print("CRM A2A AgentCard:")
    print(card)


