"""
Data Quality Workflow for comprehensive CRM data analysis and cleanup recommendations.
Integrates with the CRM agent framework to provide systematic data quality assessment.
"""

from typing import Dict, Any, List
from google.adk.agents import SequentialAgent, ParallelAgent
from ..specialized.data_quality_intelligence_agent import create_data_quality_intelligence_agent
from ..specialized.crm_agents import (
    create_crm_data_quality_agent,
    create_crm_summarizer,
    create_crm_entity_resolver
)


def create_data_quality_assessment_workflow() -> SequentialAgent:
    """
    Create comprehensive data quality assessment workflow.
    
    Implements systematic data quality analysis:
    1. Data Collection & Sampling
    2. Quality Assessment & Gap Analysis  
    3. Issue Prioritization & Impact Analysis
    4. Cleanup Recommendations & Action Plan
    """
    
    # Step 1: Data Collection
    data_collector = create_crm_data_quality_agent()
    data_collector.instruction += """
    
    📋 WORKFLOW STEP 1: DATA COLLECTION & SAMPLING
    - Load representative samples of companies and contacts
    - Gather field completeness statistics across all records
    - Identify data format patterns and inconsistencies
    - Collect relationship mapping between companies and contacts
    - Save collected data using CRMStateKeys.RAW_DATA_SAMPLE
    - Proceed to next step: Quality Assessment
    """
    
    # Step 2: Quality Assessment
    quality_assessor = create_data_quality_intelligence_agent()
    quality_assessor.instruction += """
    
    📋 WORKFLOW STEP 2: QUALITY ASSESSMENT & GAP ANALYSIS
    - Read raw data sample from previous step: {raw_data_sample}
    - Analyze field completeness across companies and contacts
    - Validate data formats (emails, phones, domains, addresses)
    - Identify duplicate candidates and data conflicts
    - Score data quality by record type and business impact
    - Save assessment results using CRMStateKeys.QUALITY_ASSESSMENT
    - Proceed to next step: Issue Prioritization
    """
    
    # Step 3: Issue Prioritization
    issue_prioritizer = create_crm_entity_resolver()
    issue_prioritizer.instruction = """
    You are handling Issue Prioritization in the data quality workflow.
    
    📋 WORKFLOW STEP 3: ISSUE PRIORITIZATION & IMPACT ANALYSIS
    - Read quality assessment from previous step: {quality_assessment}
    - Rank data quality issues by business impact and effort required
    - Identify critical issues blocking sales/marketing activities
    - Group related cleanup opportunities for batch processing
    - Estimate time and resources needed for each fix category
    - Save prioritized issues using CRMStateKeys.PRIORITIZED_ISSUES
    - Proceed to next step: Recommendations Generation
    
    PRIORITIZATION CRITERIA:
    - CRITICAL: Issues blocking business operations (missing emails, invalid contacts)
    - HIGH: Data affecting reporting accuracy and efficiency
    - MEDIUM: Standardization opportunities for consistency
    - LOW: Nice-to-have improvements for completeness
    
    BUSINESS IMPACT FACTORS:
    - Active deals with incomplete contact information
    - High-value companies with poor data quality
    - Marketing lists with bad email addresses
    - Sales territories with inconsistent data
    """
    
    # Step 4: Recommendations Generation
    recommendations_generator = create_crm_summarizer()
    recommendations_generator.instruction = """
    You are generating Data Quality Cleanup Recommendations.
    
    📋 WORKFLOW STEP 4: CLEANUP RECOMMENDATIONS & ACTION PLAN
    - Read prioritized issues from previous step: {prioritized_issues}
    - Generate specific, actionable cleanup recommendations
    - Create step-by-step remediation plans with effort estimates
    - Identify automation opportunities for ongoing maintenance
    - Suggest process improvements to prevent future data quality issues
    - Save final recommendations using CRMStateKeys.CLEANUP_RECOMMENDATIONS
    - Workflow complete: Provide comprehensive data quality report
    
    RECOMMENDATION FORMAT:
    - Immediate action items for critical issues
    - Batch cleanup opportunities for efficiency
    - Process improvements and preventive measures
    - Success metrics and monitoring strategies
    - Resource requirements and timeline estimates
    
    AUTOMATION OPPORTUNITIES:
    - Data validation rules for new record creation
    - Automated data quality monitoring and alerts
    - Bulk update scripts for format standardization
    - Integration with external data enrichment services
    """
    
    return SequentialAgent(
        name="DataQualityAssessmentWorkflow",
        description="Comprehensive data quality assessment and cleanup planning workflow",
        sub_agents=[
            data_collector,        # Step 1: Data Collection
            quality_assessor,      # Step 2: Quality Assessment
            issue_prioritizer,     # Step 3: Issue Prioritization
            recommendations_generator  # Step 4: Recommendations
        ]
    )


def create_data_quality_monitoring_workflow() -> SequentialAgent:
    """
    Create ongoing data quality monitoring workflow.
    
    For continuous data quality maintenance and monitoring.
    """
    
    # Step 1: Quality Metrics Collection
    metrics_collector = create_data_quality_intelligence_agent()
    metrics_collector.instruction = """
    You are collecting ongoing data quality metrics.
    
    📋 MONITORING STEP 1: QUALITY METRICS COLLECTION
    - Calculate current data completeness scores
    - Track data quality trends over time
    - Identify new data quality issues since last assessment
    - Monitor compliance with data entry standards
    - Generate quality scorecards by team/region
    
    METRICS TO TRACK:
    - Overall data completeness percentage
    - Critical field completion rates
    - Data format compliance scores
    - New record quality trends
    - Issue resolution progress
    """
    
    # Step 2: Alert Generation
    alert_generator = create_crm_summarizer()
    alert_generator.instruction = """
    You are generating data quality alerts and notifications.
    
    📋 MONITORING STEP 2: ALERT GENERATION
    - Identify data quality degradation trends
    - Generate alerts for critical data quality thresholds
    - Create notifications for teams with poor data entry practices
    - Suggest proactive cleanup actions
    - Schedule regular data quality review meetings
    
    ALERT TRIGGERS:
    - Data completeness drops below 80%
    - Critical field completion below 90%
    - Increase in format validation errors
    - Large number of duplicate records detected
    """
    
    return SequentialAgent(
        name="DataQualityMonitoringWorkflow",
        description="Ongoing data quality monitoring and alerting workflow",
        sub_agents=[
            metrics_collector,
            alert_generator
        ]
    )


def create_data_quality_workflows() -> Dict[str, Any]:
    """Create all data quality workflows and return as a dictionary."""
    return {
        "assessment": create_data_quality_assessment_workflow(),
        "monitoring": create_data_quality_monitoring_workflow()
    }
