"""
Project health workflow agents.
Implements workflows for comprehensive project health assessment and dashboards.
"""

from google.adk.agents import SequentialAgent, ParallelAgent
from ..specialized.query_agents import create_query_agent
from ..specialized.analysis_agents import create_analysis_agent, create_project_health_analyst
from ..specialized.reporting_agents import create_reporting_agent, create_executive_reporter


def create_comprehensive_info_workflow() -> SequentialAgent:
    """
    Create a comprehensive information gathering workflow using Parallel + Sequential pattern.
    Step 1: Parallel data gathering -> Step 2: Sequential synthesis and reporting
    """
    
    # Parallel data gathering agents
    status_analyzer = create_analysis_agent()
    status_analyzer.name = "StatusAnalyzer"
    status_analyzer.instruction = """Analyze project status using get_jira_status_breakdown tool.
Focus on status distribution and identify any concerning patterns.
Save results using output_key="status_analysis"."""
    
    workload_analyzer = create_analysis_agent()
    workload_analyzer.name = "WorkloadAnalyzer"
    workload_analyzer.instruction = """Analyze team workload using get_jira_assignee_workload tool.
Identify workload imbalances and capacity issues.
Save results using output_key="workload_analysis"."""
    
    issue_finder = create_query_agent()
    issue_finder.name = "IssueFinder"
    issue_finder.instruction = """Find critical issues using multiple query tools:
1. Find unassigned issues
2. Find stale issues
3. Find blocked issues
Save results using output_key="critical_issues"."""
    
    # Parallel data collection
    data_collection = ParallelAgent(
        name="DataCollectionPhase",
        description="Parallel collection of project health data",
        sub_agents=[status_analyzer, workload_analyzer, issue_finder]
    )
    
    # Sequential synthesis and reporting
    synthesizer = create_analysis_agent()
    synthesizer.name = "DataSynthesizer"
    synthesizer.instruction = """Synthesize all collected data into comprehensive insights.

You have access to:
- {status_analysis} - Status breakdown and patterns
- {workload_analysis} - Team workload distribution
- {critical_issues} - Unassigned, stale, and blocked issues

Create a comprehensive project health summary with:
1. Overall health score
2. Key insights and trends
3. Critical issues requiring attention
4. Recommendations for improvement

Save results using output_key="health_summary"."""
    
    reporter = create_reporting_agent()
    reporter.name = "ComprehensiveReporter"
    reporter.instruction = """Create a detailed project health report based on the synthesis.

Use the health summary ({health_summary}) to create a comprehensive report including:
1. Executive summary
2. Detailed findings by category
3. Visual data representations
4. Action items and recommendations
5. Risk assessment

Save the final report using output_key="comprehensive_report"."""
    
    # Complete workflow
    comprehensive_workflow = SequentialAgent(
        name="ComprehensiveInfoWorkflow",
        description="Comprehensive project information gathering and reporting workflow",
        sub_agents=[
            data_collection,
            synthesizer,
            reporter
        ]
    )
    
    return comprehensive_workflow


def create_project_health_dashboard() -> SequentialAgent:
    """
    Create a project health dashboard workflow optimized for executive reporting.
    Uses the specialized ProjectHealthAnalyst and ExecutiveReporter.
    """
    
    # Comprehensive health analysis
    health_analyst = create_project_health_analyst()
    health_analyst.instruction = """Perform comprehensive project health analysis using all available tools.

Analyze:
1. Project velocity and progress trends
2. Team workload distribution and balance
3. Issue resolution patterns and bottlenecks
4. Data quality and process efficiency
5. Risk factors and mitigation strategies

Provide a complete health assessment with scores, trends, and actionable insights.
Save results using output_key="project_health"."""
    
    # Executive reporting
    executive_reporter = create_executive_reporter()
    executive_reporter.instruction = """Create an executive dashboard based on the health analysis.

Use the project health data ({project_health}) to create:
1. Executive summary with key metrics
2. Critical issues requiring immediate attention
3. Strategic recommendations with business impact
4. Performance trends and forecasting
5. Resource allocation recommendations

Format for C-level consumption with clear action items.
Save the dashboard using output_key="executive_dashboard"."""
    
    # Dashboard workflow
    dashboard_workflow = SequentialAgent(
        name="ProjectHealthDashboard",
        description="Executive-focused project health dashboard workflow",
        sub_agents=[
            health_analyst,
            executive_reporter
        ]
    )
    
    return dashboard_workflow


__all__ = [
    'create_comprehensive_info_workflow',
    'create_project_health_dashboard'
]
