"""
Data quality workflow agents.
Implements workflows for data quality assessment and improvement.
"""

from google.adk.agents import SequentialAgent
from ..specialized.quality_agents import create_data_quality_agent


def create_data_quality_workflow() -> SequentialAgent:
    """
    Create a data quality workflow with human approval step.
    Steps: Analyze data quality -> Suggest fixes -> Get human approval -> Apply fixes
    """
    
    # Data quality analyzer
    quality_analyzer = create_data_quality_agent()
    quality_analyzer.name = "DataQualityAnalyzer"
    quality_analyzer.instruction = """Analyze data quality using find_issues_with_missing_fields tool.
Identify all data quality issues and calculate quality scores.
Save results using output_key="quality_report" for the next agent."""
    
    # Fix suggestion generator
    fix_suggester = create_data_quality_agent()
    fix_suggester.name = "FixSuggester"
    fix_suggester.instruction = """Based on the quality report from the previous agent ({quality_report}), 
use suggest_data_fixes tool to generate specific recommendations.

Provide detailed fix suggestions including:
1. Priority level for each fix
2. Specific actions to take
3. Potential impact of implementing fixes
4. Risk assessment for each change

Save suggestions using output_key="suggested_fixes" for human review."""
    
    # Human approval agent (simulated for demo)
    approval_agent = create_data_quality_agent()
    approval_agent.name = "HumanApprovalSimulator"
    approval_agent.instruction = """You are simulating human approval for data quality fixes.

Review the suggested fixes ({suggested_fixes}) and make approval decisions based on:
1. Risk level (approve low-risk fixes automatically)
2. Business impact (prioritize high-impact fixes)
3. Resource requirements (consider implementation effort)

For this demo, approve fixes that are:
- Low risk (missing fields, standardization)
- High business value (critical fields, data consistency)

Save approved fixes using output_key="approved_fixes"."""
    
    # Fix applicator
    fix_applicator = create_data_quality_agent()
    fix_applicator.name = "FixApplicator"
    fix_applicator.instruction = """Apply the approved fixes ({approved_fixes}) using apply_bulk_jira_updates tool.

Carefully implement each approved fix and track:
1. Successfully applied fixes
2. Any errors or issues encountered
3. Final data quality improvement metrics

Save the application results using output_key="fix_results"."""
    
    # Create the sequential workflow
    data_quality_workflow = SequentialAgent(
        name="DataQualityWorkflow",
        description="Sequential workflow for data quality assessment and improvement with approval",
        sub_agents=[
            quality_analyzer,
            fix_suggester,
            approval_agent,
            fix_applicator
        ]
    )
    
    return data_quality_workflow


__all__ = [
    'create_data_quality_workflow'
]
