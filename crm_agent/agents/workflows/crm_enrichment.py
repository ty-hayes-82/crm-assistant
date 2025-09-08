"""
CRM enrichment workflows implementing sequential and parallel patterns.
Based on the workflow designs in CRM_CONVERSION.md.
"""

from typing import Dict, Any, List
from google.adk.agents import SequentialAgent, ParallelAgent
from ..specialized.crm_agents import (
    create_crm_query_builder,
    create_crm_web_retriever, 
    create_crm_linkedin_retriever,
    create_crm_company_data_retriever,
    create_crm_email_verifier,
    create_crm_summarizer,
    create_crm_entity_resolver,
    create_crm_updater,
    create_crm_data_quality_agent
)
from ..specialized.lead_scoring_agent import create_lead_scoring_agent


def create_crm_parallel_retrieval_workflow() -> ParallelAgent:
    """
    Create parallel retrieval workflow for concurrent data gathering.
    
    Executes web, LinkedIn, company data, and email verification in parallel
    to maximize efficiency and reduce total processing time.
    """
    
    # Create retrieval agents
    web_retriever = create_crm_web_retriever()
    linkedin_retriever = create_crm_linkedin_retriever()
    company_data_retriever = create_crm_company_data_retriever()
    email_verifier = create_crm_email_verifier()
    
    # Configure agents for parallel execution
    web_retriever.instruction += """
    
    🔄 PARALLEL EXECUTION MODE:
    - Read search plan from session state
    - Execute web searches independently
    - Save results to CRMStateKeys.WEB_FINDINGS
    - Work concurrently with other retrieval agents
    """
    
    linkedin_retriever.instruction += """
    
    🔄 PARALLEL EXECUTION MODE:
    - Read search plan from session state
    - Execute LinkedIn lookups independently
    - Save results to CRMStateKeys.LI_FINDINGS
    - Work concurrently with other retrieval agents
    """
    
    company_data_retriever.instruction += """
    
    🔄 PARALLEL EXECUTION MODE:
    - Read search plan from session state
    - Execute company data lookups independently
    - Save results to CRMStateKeys.COMPANY_FINDINGS
    - Work concurrently with other retrieval agents
    """
    
    email_verifier.instruction += """
    
    🔄 PARALLEL EXECUTION MODE:
    - Read contact email from session state
    - Execute email verification independently
    - Save results to CRMStateKeys.EMAIL_VALIDATION
    - Work concurrently with other retrieval agents
    """
    
    return ParallelAgent(
        name="CRMParallelRetrievalWorkflow",
        description="Parallel execution of web, LinkedIn, company data, and email verification",
        sub_agents=[
            web_retriever,
            linkedin_retriever, 
            company_data_retriever,
            email_verifier
        ]
    )


def create_crm_enrichment_pipeline() -> SequentialAgent:
    """
    Create the main CRM enrichment pipeline with sequential steps.
    
    Implements the 9-step enrichment process:
    1. Gap Detection
    2. Query Planning  
    3. Parallel Retrieval
    4. Synthesis
    5. Entity Matching
    6. Lead Scoring
    7. Proposal Generation
    8. Human Approval
    9. Update Application
    """
    
    # Step 1: Gap Detection
    gap_detector = create_crm_data_quality_agent()
    gap_detector.instruction += """
    
    📋 PIPELINE STEP 1: GAP DETECTION
    - Load current CRM contact/company data
    - Identify missing, outdated, or inconsistent fields
    - Generate quality assessment and gap analysis
    - Save detected gaps using CRMStateKeys.DETECTED_GAPS
    - Proceed to next step: Query Planning
    """
    
    # Step 2: Query Planning
    query_planner = create_crm_query_builder()
    query_planner.instruction += """
    
    📋 PIPELINE STEP 2: QUERY PLANNING
    - Read detected gaps from previous step using CRMStateKeys.DETECTED_GAPS
    - Craft targeted search queries for each identified gap
    - Create prioritized search plan with confidence estimates
    - Save search plan using CRMStateKeys.SEARCH_PLAN
    - Proceed to next step: Parallel Retrieval
    """
    
    # Step 3: Parallel Retrieval (created above)
    parallel_retrieval = create_crm_parallel_retrieval_workflow()
    
    # Step 4: Synthesis
    synthesizer = create_crm_summarizer()
    synthesizer.instruction += """
    
    📋 PIPELINE STEP 4: SYNTHESIS
    - Read findings from parallel retrieval using session state keys:
      * Web findings: CRMStateKeys.WEB_FINDINGS
      * LinkedIn findings: CRMStateKeys.LI_FINDINGS
      * Company findings: CRMStateKeys.COMPANY_FINDINGS
      * Email validation: CRMStateKeys.EMAIL_VALIDATION
    - Normalize and deduplicate all findings
    - Resolve conflicts using source reliability
    - Generate confidence scores for each insight
    - Save normalized insights using CRMStateKeys.NORMALIZED_INSIGHTS
    - Proceed to next step: Entity Matching
    """
    
    # Step 5: Entity Matching
    entity_matcher = create_crm_entity_resolver()
    entity_matcher.instruction += """
    
    📋 PIPELINE STEP 5: ENTITY MATCHING
    - Read normalized insights from previous step using CRMStateKeys.NORMALIZED_INSIGHTS
    - Map insights to specific HubSpot CRM fields
    - Apply field precedence and update policies
    - Generate proposed field mappings with justifications
    - Save mappings using CRMStateKeys.PROPOSED_FIELD_MAP
    - Proceed to next step: Lead Scoring
    """
    
    # Step 6: Lead Scoring (Phase 6)
    lead_scorer = create_lead_scoring_agent()
    lead_scorer.instruction += """
    
    📋 PIPELINE STEP 6: LEAD SCORING
    - Read current contact/company data from HubSpot
    - Read enriched data from previous steps for enhanced scoring
    - Calculate Fit score based on ICP alignment (course type, management company, revenue, etc.)
    - Calculate Intent score based on engagement signals (website activity, email engagement, etc.)
    - Compute weighted total score (Fit 60% + Intent 40%)
    - Determine score band: Hot (80-100), Warm (60-79), Cold (40-59), Unqualified (0-39)
    - Prepare score updates for HubSpot fields: swoop_fit_score, swoop_intent_score, swoop_total_lead_score
    - Save scoring results using CRMStateKeys.LEAD_SCORES
    - Proceed to next step: Proposal Generation
    """
    
    # Step 7: Proposal Generation
    proposal_generator = create_crm_updater()
    proposal_generator.instruction += """
    
    📋 PIPELINE STEP 7: PROPOSAL GENERATION
    - Read proposed field mappings using CRMStateKeys.PROPOSED_FIELD_MAP
    - Read lead scores using CRMStateKeys.LEAD_SCORES
    - Generate detailed change proposals with before/after values
    - Include confidence scores and source attribution
    - Format proposals for human review
    - Save proposals using CRMStateKeys.PROPOSED_CHANGES
    - Proceed to next step: Human Approval
    """
    
    # Step 8: Human Approval (handled by CRMUpdaterAgent)
    approval_handler = create_crm_updater()
    approval_handler.instruction = """
    You are handling the Human Approval step in the CRM enrichment pipeline.
    
    📋 PIPELINE STEP 8: HUMAN APPROVAL
    - Read proposed changes from previous step using CRMStateKeys.PROPOSED_CHANGES
    - Format changes for human review in Slack
    - Send approval request with clear options
    - Process user response (approve all, selected, or none)
    - Save approved changes using CRMStateKeys.APPROVED_CHANGES
    - Proceed to next step: Update Application
    
    APPROVAL FORMAT:
    - Present each proposed change clearly
    - Include current value, proposed value, confidence, and source
    - Provide options: ✅ approve all, ❌ reject all, or specify numbers
    - Wait for user response before proceeding
    """
    
    # Step 9: Update Application
    update_applier = create_crm_updater()
    update_applier.instruction = """
    You are handling the Update Application step in the CRM enrichment pipeline.
    
    📋 PIPELINE STEP 9: UPDATE APPLICATION
    - Read approved changes from previous step using CRMStateKeys.APPROVED_CHANGES
    - Apply only approved changes to HubSpot via MCP server
    - Handle API errors gracefully with retries
    - Track success/failure for each update
    - Generate comprehensive update report
    - Save results using CRMStateKeys.UPDATE_RESULTS
    - Pipeline complete: Provide final summary
    
    SAFETY MEASURES:
    - Validate all data before API calls
    - Never apply unapproved changes
    - Maintain detailed audit trail
    - Provide rollback information if needed
    """
    
    return SequentialAgent(
        name="CRMEnrichmentPipeline",
        description="Complete CRM enrichment pipeline with gap detection, retrieval, synthesis, and updates",
        sub_agents=[
            gap_detector,           # Step 1: Gap Detection
            query_planner,          # Step 2: Query Planning
            parallel_retrieval,     # Step 3: Parallel Retrieval
            synthesizer,            # Step 4: Synthesis
            entity_matcher,         # Step 5: Entity Matching
            lead_scorer,            # Step 6: Lead Scoring
            proposal_generator,     # Step 7: Proposal Generation
            approval_handler,       # Step 8: Human Approval
            update_applier          # Step 9: Update Application
        ]
    )


def create_crm_quick_lookup_workflow() -> SequentialAgent:
    """
    Create a simplified workflow for quick CRM record lookups and summaries.
    
    For requests like "What do we know about ACME Corp?" or "Summarize John Doe's profile"
    """
    
    # Step 1: Data Loading
    data_loader = create_crm_data_quality_agent()
    data_loader.instruction = """
    You are handling CRM data loading for quick lookup.
    
    📋 QUICK LOOKUP STEP 1: DATA LOADING
    - Load current CRM contact/company data from HubSpot
    - Validate data completeness and quality
    - Identify any obvious gaps or issues
    - Save loaded data to session state
    - Proceed to summary generation
    """
    
    # Step 2: Summary Generation
    summarizer = create_crm_summarizer()
    summarizer.instruction = """
    You are generating a quick summary of CRM data.
    
    📋 QUICK LOOKUP STEP 2: SUMMARY GENERATION
    - Read loaded CRM data from session state
    - Generate comprehensive summary of available information
    - Highlight any missing or outdated fields
    - Suggest enrichment opportunities if gaps exist
    - Provide actionable insights and next steps
    
    SUMMARY FORMAT:
    - Contact/Company overview
    - Key data points and metrics
    - Data quality assessment
    - Suggested improvements
    - Recent activity (if available)
    """
    
    return SequentialAgent(
        name="CRMQuickLookupWorkflow",
        description="Quick CRM record lookup and summary generation",
        sub_agents=[
            data_loader,
            summarizer
        ]
    )


def create_crm_data_quality_workflow() -> SequentialAgent:
    """
    Create a workflow focused on CRM data quality assessment and cleanup.
    
    For requests focused on data quality improvement and validation.
    """
    
    # Step 1: Quality Assessment
    quality_assessor = create_crm_data_quality_agent()
    quality_assessor.instruction += """
    
    📋 QUALITY WORKFLOW STEP 1: COMPREHENSIVE ASSESSMENT
    - Analyze all CRM contact and company records
    - Generate detailed quality metrics and scores
    - Identify systematic data issues
    - Prioritize improvement opportunities
    - Save quality report using CRMStateKeys.QUALITY_REPORT
    """
    
    # Step 2: Improvement Planning
    improvement_planner = create_crm_query_builder()
    improvement_planner.instruction = """
    You are planning CRM data quality improvements.
    
    📋 QUALITY WORKFLOW STEP 2: IMPROVEMENT PLANNING
    - Read quality report from previous step using CRMStateKeys.QUALITY_REPORT
    - Identify high-impact, low-effort improvements
    - Create action plan for data quality enhancement
    - Prioritize fixes by business impact
    - Generate improvement recommendations
    
    PLANNING FOCUS:
    - Required field completion
    - Data standardization opportunities
    - Duplicate detection and resolution
    - Format compliance improvements
    """
    
    # Step 3: Selective Enrichment (if needed)
    selective_enrichment = create_crm_parallel_retrieval_workflow()
    selective_enrichment.name = "CRMSelectiveEnrichment"
    selective_enrichment.description = "Targeted enrichment for quality improvement"
    
    return SequentialAgent(
        name="CRMDataQualityWorkflow", 
        description="Comprehensive CRM data quality assessment and improvement",
        sub_agents=[
            quality_assessor,
            improvement_planner,
            selective_enrichment
        ]
    )


# Workflow creation helper functions

def create_crm_workflows() -> Dict[str, Any]:
    """Create all CRM workflows and return as a dictionary."""
    return {
        "enrichment_pipeline": create_crm_enrichment_pipeline(),
        "parallel_retrieval": create_crm_parallel_retrieval_workflow(),
        "quick_lookup": create_crm_quick_lookup_workflow(),
        "data_quality": create_crm_data_quality_workflow()
    }
