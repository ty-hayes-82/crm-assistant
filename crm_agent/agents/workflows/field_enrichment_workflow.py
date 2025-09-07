"""
Field Enrichment Workflow Agents

This module implements workflow agents for systematic field enrichment using ADK's
Sequential, Parallel, and Loop agent patterns. These workflow agents orchestrate
the enrichment process with predictable, reliable execution patterns.
"""

from typing import Dict, Any, List, Optional
from google.adk.agents import SequentialAgent, ParallelAgent, LoopAgent, InvocationContext

from ...core.base_agents import SpecializedAgent
from ...core.state_models import CRMSessionState, CRMStateKeys


class FieldAnalysisAgent(SpecializedAgent):
    """Agent that analyzes field completeness and prioritizes enrichment tasks"""
    
    def __init__(self, **kwargs):
        super().__init__(
            name="FieldAnalysisAgent",
            domain="field_analysis",
            specialized_tools=["search_companies", "search_contacts"],
            instruction="""
            You are a Field Analysis Agent responsible for analyzing CRM record completeness
            and prioritizing field enrichment tasks.
            
            🎯 RESPONSIBILITIES:
            1. Analyze current field completeness for companies and contacts
            2. Identify missing critical, high-priority, and medium/low priority fields
            3. Create prioritized enrichment task lists
            4. Assess data quality and flag issues
            5. Store analysis results in session state for workflow orchestration
            
            📊 ANALYSIS FRAMEWORK:
            - **Critical Fields** (95%+ target): name, email, firstname, lastname, website
            - **High Priority** (85%+ target): domain, industry, revenue, job_title, phone
            - **Medium/Low Priority** (70%+ target): linkedin, address, description, tech_stack
            
            🔍 OUTPUT FORMAT:
            Store analysis in session state with keys:
            - FIELD_ANALYSIS_RESULTS: Detailed field-by-field analysis
            - ENRICHMENT_PRIORITIES: Prioritized list of fields to enrich
            - MISSING_CRITICAL_FIELDS: Critical fields that must be addressed
            - DATA_QUALITY_ISSUES: Identified data quality problems
            
            Always provide comprehensive analysis to guide the enrichment workflow.
            """,
            **kwargs
        )
    
    def execute_analysis(self, context: InvocationContext) -> Dict[str, Any]:
        """Execute real field analysis for workflow"""
        try:
            # Get record information from context
            record_type = context.session_state.get('record_type', 'company')
            record_id = context.session_state.get('record_id')
            
            if not record_id:
                return {
                    'agent': 'FieldAnalysisAgent',
                    'status': 'failed',
                    'error': 'No record ID provided'
                }
            
            # Use the parent agent's tools to get record data
            # This would typically be done through the agent framework
            # For now, we'll store the analysis request in context for the main agent to handle
            context.session_state['FIELD_ANALYSIS_REQUEST'] = {
                'record_type': record_type,
                'record_id': record_id,
                'requested_by': 'FieldAnalysisAgent'
            }
            
            return {
                'agent': 'FieldAnalysisAgent',
                'status': 'analysis_requested',
                'message': 'Field analysis requested from main agent'
            }
            
        except Exception as e:
            return {
                'agent': 'FieldAnalysisAgent',
                'status': 'failed',
                'error': str(e)
            }


class DataSourceAgent(SpecializedAgent):
    """Agent that enriches fields from a specific data source"""
    
    def __init__(self, source_name: str, source_tools: List[str], **kwargs):
        super().__init__(
            name=f"{source_name}DataSourceAgent",
            domain=f"{source_name.lower()}_enrichment",
            specialized_tools=source_tools,
            instruction=f"""
            You are a {source_name} Data Source Agent responsible for enriching CRM fields
            using {source_name} as the primary data source.
            
            🎯 RESPONSIBILITIES:
            1. Read enrichment priorities from session state
            2. Attempt to enrich assigned fields using {source_name}
            3. Validate and score confidence of enriched data
            4. Store enrichment results in session state
            5. Handle errors gracefully and provide fallback options
            
            📊 ENRICHMENT PROCESS:
            1. Check session state for assigned field enrichment tasks
            2. Use {source_name} tools to gather missing data
            3. Validate data quality and assign confidence scores
            4. Store results with source attribution and timestamps
            5. Update enrichment progress tracking
            
            🔍 QUALITY STANDARDS:
            - High Confidence (90+): Multiple sources confirm or authoritative source
            - Medium Confidence (70+): Single reliable source
            - Low Confidence (40+): Uncertain or outdated source
            - Failed (0): Could not retrieve or validate data
            
            Store results in session state under {source_name.upper()}_ENRICHMENT_RESULTS.
            """,
            **kwargs
        )
        
        # Store source name using object.__setattr__ to bypass Pydantic validation
        object.__setattr__(self, 'source_name', source_name)
    
    def execute_enrichment(self, context: InvocationContext) -> Dict[str, Any]:
        """Execute real data source enrichment for workflow"""
        try:
            # Get record information from context
            record_type = context.session_state.get('record_type', 'company')
            record_id = context.session_state.get('record_id')
            
            if not record_id:
                return {
                    'agent': f'{self.source_name}DataSourceAgent',
                    'status': 'failed',
                    'error': 'No record ID provided'
                }
            
            # Store enrichment request in context for main agent to handle
            context.session_state[f'{self.source_name.upper()}_ENRICHMENT_REQUEST'] = {
                'record_type': record_type,
                'record_id': record_id,
                'source': self.source_name,
                'requested_by': f'{self.source_name}DataSourceAgent'
            }
            
            return {
                'agent': f'{self.source_name}DataSourceAgent',
                'status': 'enrichment_requested',
                'message': f'{self.source_name} enrichment requested from main agent'
            }
            
        except Exception as e:
            return {
                'agent': f'{self.source_name}DataSourceAgent',
                'status': 'failed',
                'error': str(e)
            }


class EnrichmentValidatorAgent(SpecializedAgent):
    """Agent that validates and scores enriched data quality"""
    
    def __init__(self, **kwargs):
        super().__init__(
            name="EnrichmentValidatorAgent",
            domain="enrichment_validation",
            specialized_tools=["web_search"],  # For cross-validation
            instruction="""
            You are an Enrichment Validator Agent responsible for validating the quality
            and accuracy of enriched CRM data.
            
            🎯 RESPONSIBILITIES:
            1. Read enrichment results from all data sources
            2. Cross-validate data across multiple sources when possible
            3. Apply field-specific validation rules
            4. Assign final confidence scores and validation status
            5. Flag data quality issues and inconsistencies
            
            🔍 VALIDATION CRITERIA:
            
            **Format Validation**:
            - Email: RFC 5322 compliance, domain validation
            - URL: Accessibility, proper formatting, SSL status
            - Phone: Format standardization, country codes
            - Address: Completeness, geocoding validation
            
            **Content Validation**:
            - Industry: Standard classification alignment
            - Job Titles: Professional formatting, seniority consistency
            - Company Names: Legal entity handling, standardization
            - Revenue/Employee Count: Reasonableness checks
            
            **Cross-Source Validation**:
            - Compare data from multiple sources
            - Flag inconsistencies for manual review
            - Boost confidence for confirmed data
            - Lower confidence for conflicting data
            
            🎯 OUTPUT:
            Store validation results in session state under VALIDATION_RESULTS with:
            - Field-by-field validation status
            - Final confidence scores
            - Data quality flags
            - Recommendations for manual review
            """,
            **kwargs
        )
    
    def execute_validation(self, context: InvocationContext) -> Dict[str, Any]:
        """Execute real validation for workflow"""
        try:
            # Get enrichment results from context
            validation_results = {}
            overall_score = 0
            field_count = 0
            
            # Validate results from all sources
            for key, value in context.session_state.items():
                if key.endswith('_ENRICHMENT_RESULTS'):
                    source_results = value
                    for field_name, field_data in source_results.items():
                        if isinstance(field_data, dict) and 'new_value' in field_data:
                            validation_result = self._validate_field(field_name, field_data['new_value'])
                            validation_results[field_name] = validation_result
                            overall_score += validation_result.get('confidence', 0)
                            field_count += 1
            
            avg_score = overall_score / field_count if field_count > 0 else 0
            
            # Store validation results in context
            context.session_state['VALIDATION_RESULTS'] = validation_results
            
            return {
                'agent': 'EnrichmentValidatorAgent',
                'status': 'completed',
                'validation_results': validation_results,
                'overall_quality_score': avg_score
            }
            
        except Exception as e:
            return {
                'agent': 'EnrichmentValidatorAgent',
                'status': 'failed',
                'error': str(e)
            }
    
    def _validate_field(self, field_name: str, field_value: Any) -> Dict[str, Any]:
        """Validate a specific field value"""
        issues = []
        confidence = 50  # Default confidence
        
        if not field_value or str(field_value).strip() == '':
            return {'valid': False, 'confidence': 0, 'issues': ['Empty value']}
        
        # Field-specific validation
        if 'email' in field_name.lower():
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if re.match(email_pattern, str(field_value)):
                confidence = 90
            else:
                issues.append('Invalid email format')
                confidence = 20
        
        elif 'website' in field_name.lower() or 'url' in field_name.lower():
            if str(field_value).startswith(('http://', 'https://')):
                confidence = 80
            else:
                issues.append('URL should start with http:// or https://')
                confidence = 40
        
        elif 'phone' in field_name.lower():
            # Basic phone validation
            phone_str = str(field_value).replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
            if len(phone_str) >= 10 and phone_str.isdigit():
                confidence = 75
            else:
                issues.append('Invalid phone format')
                confidence = 30
        
        else:
            # General validation for other fields
            if len(str(field_value).strip()) > 2:
                confidence = 70
            else:
                issues.append('Value too short')
                confidence = 30
        
        return {
            'valid': len(issues) == 0,
            'confidence': confidence,
            'issues': issues
        }


class EnrichmentCritiqueAgent(SpecializedAgent):
    """Agent that critiques enrichment performance and suggests improvements"""
    
    def __init__(self, **kwargs):
        super().__init__(
            name="EnrichmentCritiqueAgent",
            domain="enrichment_critique",
            specialized_tools=[],  # Works with session state data
            instruction="""
            You are an Enrichment Critique Agent responsible for analyzing enrichment
            performance and identifying improvement opportunities.
            
            🎯 RESPONSIBILITIES:
            1. Analyze overall enrichment performance metrics
            2. Identify patterns in successful vs failed enrichments
            3. Critique data source reliability and effectiveness
            4. Generate actionable improvement recommendations
            5. Document insights for process optimization
            
            📊 PERFORMANCE ANALYSIS:
            
            **Success Rate Analysis**:
            - Overall success rate vs targets (Critical: 95%, High: 85%, Medium: 70%)
            - Success rates by field type and data source
            - Confidence score distribution analysis
            - Time-to-enrich performance metrics
            
            **Failure Pattern Analysis**:
            - Common failure reasons and frequency
            - Data source reliability assessment
            - Field-specific enrichment challenges
            - Error handling effectiveness
            
            **Quality Assessment**:
            - Data confidence score trends
            - Validation pass/fail rates
            - Cross-source consistency analysis
            - Manual review queue analysis
            
            🔍 IMPROVEMENT IDENTIFICATION:
            
            **Process Improvements**:
            - Enrichment workflow optimizations
            - Data source integration enhancements
            - Validation criteria refinements
            - Error handling improvements
            
            **Quality Enhancements**:
            - Confidence scoring algorithm improvements
            - Cross-validation strategy optimization
            - Data normalization enhancements
            - Source reliability weighting
            
            **Strategic Recommendations**:
            - New data source integration opportunities
            - Field priority adjustments
            - Success rate target modifications
            - Resource allocation optimization
            
            Store critique results in session state under ENRICHMENT_CRITIQUE with
            detailed analysis and improvement recommendations.
            """,
            **kwargs
        )
    
    def execute_simulation(self, context: InvocationContext) -> Dict[str, Any]:
        """Execute critique simulation for workflow"""
        # Simulate critique results
        return {
            'agent': 'EnrichmentCritiqueAgent',
            'status': 'completed',
            'critique': {
                'overall_score': 78.5,
                'success_rate': 75.0,
                'improvement_opportunities': [
                    'Improve industry classification accuracy',
                    'Add cross-validation for employee count estimates',
                    'Implement real-time website accessibility checking'
                ],
                'recommendations': [
                    'Use multiple sources for industry classification',
                    'Implement LinkedIn API for more accurate employee counts',
                    'Add automated website validation pipeline'
                ]
            }
        }


def create_field_enrichment_workflow(**kwargs) -> SequentialAgent:
    """
    Create a comprehensive field enrichment workflow that combines all patterns.
    
    This is the main workflow that orchestrates the complete enrichment process
    using sequential, parallel, and loop patterns as appropriate.
    """
    
    # Step 1: Initial field analysis
    field_analyzer = FieldAnalysisAgent(**kwargs)
    
    # Step 2: Iterative enrichment with loop workflow
    enrichment_loop = _create_field_enrichment_loop_workflow(**kwargs)
    
    # Step 3: Final validation and quality assessment
    final_validator = EnrichmentValidatorAgent(**kwargs)
    
    # Step 4: Performance critique and improvement documentation
    improvement_agent = FieldEnrichmentImprovementAgent(**kwargs)
    
    # Create comprehensive sequential workflow
    comprehensive_workflow = SequentialAgent(
        name="ComprehensiveFieldEnrichmentWorkflow",
        sub_agents=[
            field_analyzer,     # Analyze current state
            enrichment_loop,    # Iteratively improve data
            final_validator,    # Final quality check
            improvement_agent   # Document improvements
        ]
    )
    
    return comprehensive_workflow


class FieldEnrichmentImprovementAgent(SpecializedAgent):
    """Agent that documents improvement insights and optimizes the enrichment process"""
    
    def __init__(self, **kwargs):
        super().__init__(
            name="FieldEnrichmentImprovementAgent",
            domain="process_improvement",
            specialized_tools=[],
            instruction="""
            You are a Field Enrichment Improvement Agent responsible for documenting
            insights and continuously optimizing the enrichment process.
            
            🎯 RESPONSIBILITIES:
            1. Analyze enrichment performance trends over time
            2. Document improvement insights and lessons learned
            3. Optimize workflow parameters and configurations
            4. Generate comprehensive improvement reports
            5. Track process evolution and effectiveness
            
            📊 IMPROVEMENT ANALYSIS:
            
            **Performance Trends**:
            - Success rate improvements over time
            - Data source reliability trends
            - Confidence score distribution changes
            - Processing time optimizations
            
            **Process Optimizations**:
            - Workflow step effectiveness analysis
            - Resource allocation optimization
            - Parallel vs sequential performance comparison
            - Loop termination condition refinement
            
            **Quality Enhancements**:
            - Validation criteria effectiveness
            - Cross-source consistency improvements
            - Error handling enhancement opportunities
            - Data normalization optimizations
            
            📝 DOCUMENTATION FORMAT:
            Generate structured improvement reports with:
            - Executive summary of key findings
            - Detailed performance analysis
            - Specific improvement recommendations
            - Implementation priority rankings
            - Success metrics and KPIs
            
            Save reports to files with timestamps and version tracking.
            """,
            **kwargs
        )


def _create_field_enrichment_sequential_workflow(**kwargs) -> SequentialAgent:
    """
    Create a sequential workflow for systematic field enrichment.
    
    Flow: Analysis → Enrichment → Validation → Critique → Documentation
    """
    
    # Create sub-agents
    field_analyzer = FieldAnalysisAgent(**kwargs)
    
    # Data source agents for parallel enrichment
    web_source_agent = DataSourceAgent("Web", ["web_search", "fetch_url"], **kwargs)
    linkedin_source_agent = DataSourceAgent("LinkedIn", ["linkedin_company_lookup"], **kwargs)
    external_data_agent = DataSourceAgent("ExternalData", ["get_company_metadata"], **kwargs)
    
    # Import and create specialized field enrichment subagents
    from ..specialized.field_specialist_agents import create_company_competitor_agent, create_company_llm_enrichment_agent
    competitor_agent = create_company_competitor_agent(**kwargs)
    llm_enrichment_agent = create_company_llm_enrichment_agent(**kwargs)
    
    # Create parallel enrichment workflow including specialized field agents
    parallel_enrichment = ParallelAgent(
        name="ParallelEnrichmentAgent",
        sub_agents=[web_source_agent, linkedin_source_agent, external_data_agent, competitor_agent, llm_enrichment_agent]
    )
    
    validator = EnrichmentValidatorAgent(**kwargs)
    critique_agent = EnrichmentCritiqueAgent(**kwargs)
    
    # Create sequential workflow
    sequential_workflow = SequentialAgent(
        name="FieldEnrichmentSequentialWorkflow",
        sub_agents=[
            field_analyzer,        # Step 1: Analyze field completeness
            parallel_enrichment,   # Step 2: Enrich from multiple sources in parallel
            validator,            # Step 3: Validate enriched data
            critique_agent        # Step 4: Critique performance and suggest improvements
        ]
    )
    
    return sequential_workflow


class EnrichmentLoopConditionAgent(SpecializedAgent):
    """Agent that determines when to continue or stop the enrichment loop"""
    
    def __init__(self, **kwargs):
        super().__init__(
            name="EnrichmentLoopConditionAgent",
            domain="loop_control",
            specialized_tools=[],
            instruction="""
            You are an Enrichment Loop Condition Agent responsible for determining
            when to continue or terminate the enrichment loop.
            
            🎯 TERMINATION CONDITIONS:
            
            **Success Conditions** (STOP loop):
            - Target success rates achieved for all field priority levels
            - All critical fields successfully enriched
            - Maximum confidence scores reached
            - No more improvement opportunities identified
            
            **Continue Conditions** (CONTINUE loop):
            - Success rates below targets
            - Critical fields still missing
            - Improvement opportunities available
            - Additional data sources to try
            - Maximum iterations not yet reached
            
            **Failure Conditions** (STOP loop):
            - Maximum iterations reached without improvement
            - All data sources exhausted
            - Consistent failures across all sources
            - Error rates exceed acceptable thresholds
            
            📊 DECISION LOGIC:
            1. Read current enrichment results from session state
            2. Calculate success rates by field priority
            3. Assess improvement potential
            4. Check iteration count and resource limits
            5. Return boolean decision: True (continue) or False (stop)
            
            Store decision rationale in session state under LOOP_DECISION_RATIONALE.
            """,
            **kwargs
        )
    
    def should_continue_loop(self, context: InvocationContext) -> bool:
        """
        Determine if the enrichment loop should continue.
        
        Returns:
            bool: True if loop should continue, False if it should stop
        """
        # This would implement the actual loop condition logic
        # For now, return a simple condition based on iteration count
        session_state = context.session_state
        current_iteration = session_state.get('current_iteration', 0)
        max_iterations = session_state.get('max_iterations', 3)
        
        # Simple condition: continue if under max iterations
        should_continue = current_iteration < max_iterations
        
        # Update iteration count
        session_state['current_iteration'] = current_iteration + 1
        
        # Store decision rationale
        rationale = f"Iteration {current_iteration + 1}/{max_iterations}: {'Continuing' if should_continue else 'Stopping'}"
        session_state['loop_decision_rationale'] = rationale
        
        return should_continue


def _create_field_enrichment_loop_workflow(**kwargs) -> LoopAgent:
    """
    Create a loop workflow that iteratively improves field enrichment.
    
    This workflow continues enriching and refining data until target quality is achieved
    or maximum iterations are reached.
    """
    
    # Create the main enrichment workflow to loop
    enrichment_workflow = _create_field_enrichment_sequential_workflow(**kwargs)
    
    # Create loop condition agent
    loop_condition_agent = EnrichmentLoopConditionAgent(**kwargs)
    
    # Create loop workflow
    loop_workflow = LoopAgent(
        name="FieldEnrichmentLoopWorkflow",
        sub_agent=enrichment_workflow,
        condition_agent=loop_condition_agent,
        max_iterations=5  # Safety limit
    )
    
    return loop_workflow
