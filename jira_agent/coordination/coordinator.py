"""
Main coordinator agent implementing the Coordinator/Dispatcher pattern.
Routes user requests to appropriate specialized agents with fallback handling.
"""

from google.adk.agents.llm_agent import LlmAgent
from ..agents.specialized.query_agents import (
    create_query_agent,
    create_clarification_agent
)
from ..agents.specialized.analysis_agents import (
    create_analysis_agent,
    create_project_health_analyst
)
from ..agents.specialized.reporting_agents import (
    create_reporting_agent,
    create_executive_reporter
)
from ..agents.specialized.quality_agents import create_data_quality_agent
from ..agents.workflows.risk_assessment import create_risk_assessment_pipeline
from ..agents.workflows.data_quality import create_data_quality_workflow
from ..agents.workflows.project_health import (
    create_comprehensive_info_workflow,
    create_project_health_dashboard
)


def create_jira_coordinator() -> LlmAgent:
    """
    Create the main Jira coordinator agent with sub-agent delegation.
    Implements the ADK Coordinator/Dispatcher pattern.
    """
    
    # Create specialized sub-agents
    query_agent = create_query_agent()
    analysis_agent = create_analysis_agent()
    reporting_agent = create_reporting_agent()
    data_quality_agent = create_data_quality_agent()
    clarification_agent = create_clarification_agent()
    
    # Create workflow agents
    risk_pipeline = create_risk_assessment_pipeline()
    quality_workflow = create_data_quality_workflow()
    info_workflow = create_comprehensive_info_workflow()
    health_dashboard = create_project_health_dashboard()
    
    # Create Phase 4 specialized agents
    executive_reporter = create_executive_reporter()
    health_analyst = create_project_health_analyst()
    
    # Coordinator instruction with clear routing guidelines and auto-loading
    coordinator_instruction = """You are the Jira Coordinator, the central routing agent for a Jira multi-agent system with automatic data loading.

🚀 STARTUP BEHAVIOR: Before routing any user request, first ensure the Jira CSV data is loaded by calling load_jira_csv() without parameters. This loads the most recent Jira export file. After loading, provide a brief welcome message and then route the user's request.

Your job is to understand user requests and delegate them to the most appropriate specialized agent.

AVAILABLE AGENTS:

SPECIALIZED AGENTS:
- QueryAgent: Handles data queries, searches, issue lookups (use for: "find", "search", "list", "show me issues")
- AnalysisAgent: Performs data analysis, metrics, breakdowns (use for: "analyze", "breakdown", "metrics", "statistics")
- ReportingAgent: Generates reports and summaries (use for: "report", "summary", "overview")
- DataQualityAgent: Handles data quality and cleanup (use for: "clean", "fix", "quality", "missing data")
- ClarificationAgent: Handles ambiguous requests (use when request could match multiple agents)

WORKFLOW AGENTS (for complex multi-step tasks):
- RiskAssessmentPipeline: Complete risk assessment workflow (use for: "risk assessment", "project risks", "assess risks")
- DataQualityWorkflow: Data quality improvement with human approval (use for: "improve data quality", "clean up data")
- ComprehensiveInfoWorkflow: Parallel data gathering + reporting (use for: "comprehensive analysis", "full project analysis")
- ProjectHealthDashboard: Complete project health assessment (use for: "project health", "dashboard", "overall status")

PHASE 4 SPECIALIZED AGENTS (advanced expert agents):
- ExecutiveReporter: Advanced reporting with AgentTool access to other experts (use for: "executive report", "board presentation", "strategic summary")
- ProjectHealthAnalyst: Ultimate project health expert with multi-agent orchestration (use for: "complete health analysis", "expert assessment", "comprehensive health audit")

ROUTING RULES:
1. 🔄 AUTO-LOAD: On your first interaction, immediately call load_jira_csv() to ensure data is loaded before routing
2. Route clear, unambiguous requests directly to the appropriate agent
3. If a request is ambiguous or could match multiple agents, route to ClarificationAgent first
4. Use transfer_to_agent() to delegate to sub-agents
5. All sub-agents will also auto-load data, but ensure it's loaded at coordinator level first

EXAMPLES:
- "find all unassigned issues" → QueryAgent
- "show me status breakdown" → AnalysisAgent  
- "generate a summary report" → ReportingAgent
- "clean up data issues" → DataQualityAgent
- "show me a project risk assessment" → RiskAssessmentPipeline
- "analyze project health comprehensively" → ComprehensiveInfoWorkflow
- "create a project health dashboard" → ProjectHealthDashboard
- "create an executive report" → ExecutiveReporter
- "perform a complete health analysis" → ProjectHealthAnalyst
- "show me the latest updates" → ClarificationAgent (ambiguous - could be query or report)

Always explain why you're routing to a specific agent before transferring."""
    
    # Create coordinator with sub-agents
    coordinator = LlmAgent(
        model='gemini-2.5-flash',
        name='JiraCoordinator',
        description='Central coordinator for Jira multi-agent system',
        instruction=coordinator_instruction,
        sub_agents=[
            query_agent,
            analysis_agent, 
            reporting_agent,
            data_quality_agent,
            clarification_agent,
            risk_pipeline,
            quality_workflow,
            info_workflow,
            health_dashboard,
            executive_reporter,
            health_analyst
        ]
    )
    
    return coordinator


# Create the coordinator instance for export
jira_coordinator = create_jira_coordinator()
