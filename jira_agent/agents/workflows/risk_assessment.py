"""
Risk assessment workflow agents.
Implements sequential workflows for comprehensive project risk analysis.
"""

from google.adk.agents import SequentialAgent
from ..specialized.query_agents import create_query_agent
from ..specialized.analysis_agents import create_analysis_agent


def create_risk_assessment_pipeline() -> SequentialAgent:
    """
    Create a risk assessment workflow using Sequential pattern.
    Steps: Find stale issues -> Find blocked issues -> Find due soon issues -> Synthesize risk report
    """
    
    # Create specialized agents for each risk detection step
    stale_finder = create_query_agent()
    stale_finder.name = "StaleIssueFinder"
    stale_finder.instruction = """Find stale issues in the project using find_stale_issues_in_project tool.
Focus on issues that haven't been updated in the last 30 days.
Save results using output_key="stale_issues" for the next agent to use."""
    
    blocked_finder = create_query_agent()
    blocked_finder.name = "BlockedIssueFinder"
    blocked_finder.instruction = """Find blocked issues in the project using find_blocked_issues_in_project tool.
Look for issues that are waiting, blocked, or have impediments.
Save results using output_key="blocked_issues" for the next agent to use."""
    
    due_soon_finder = create_query_agent()
    due_soon_finder.name = "DueSoonFinder"
    due_soon_finder.instruction = """Find issues due soon using find_due_soon_issues_in_project tool.
Look for issues due within the next 7 days.
Save results using output_key="due_soon_issues" for the next agent to use."""
    
    # Risk synthesizer that combines all the findings
    risk_synthesizer = create_analysis_agent()
    risk_synthesizer.name = "RiskSynthesizer"
    risk_synthesizer.instruction = """You are the risk synthesizer. Analyze the risk data collected by previous agents.

You have access to:
- {stale_issues} - Issues that haven't been updated recently
- {blocked_issues} - Issues that are blocked or waiting
- {due_soon_issues} - Issues due soon

Create a comprehensive risk assessment report that includes:
1. Overall risk score (0-10 scale)
2. Risk breakdown by category
3. Priority recommendations
4. Action items for risk mitigation

Save the final report using output_key="risk_report"."""
    
    # Create the sequential pipeline
    risk_pipeline = SequentialAgent(
        name="RiskAssessmentPipeline",
        description="Sequential workflow for comprehensive project risk assessment",
        sub_agents=[
            stale_finder,
            blocked_finder, 
            due_soon_finder,
            risk_synthesizer
        ]
    )
    
    return risk_pipeline


__all__ = [
    'create_risk_assessment_pipeline'
]
