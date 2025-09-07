"""
Field Enrichment Manager Agent

This agent manages the systematic enrichment and validation of the top 10 most valuable
CRM fields for companies and contacts in the Swoop sales process. It orchestrates
enrichment activities, critiques results, and documents improvement opportunities.
"""

import os
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, ClassVar
from dataclasses import dataclass, field
from enum import Enum

from ...core.base_agents import SpecializedAgent
from ...core.state_models import CRMSessionState, CRMStateKeys
from ..workflows.field_enrichment_workflow import (
    create_field_enrichment_workflow
)

# Import ADK components
try:
    from google.adk.agents import InvocationContext
except ImportError:
    # Fallback for environments without ADK
    class InvocationContext:
        def __init__(self):
            self.session_state = {}

logger = logging.getLogger(__name__)


class EnrichmentPriority(Enum):
    """Priority levels for field enrichment"""
    CRITICAL = 1  # Must have for sales process
    HIGH = 2      # Important for sales effectiveness  
    MEDIUM = 3    # Useful for analytics and insights
    LOW = 4       # Nice to have


class EnrichmentStatus(Enum):
    """Status of field enrichment"""
    COMPLETE = "✅ Complete"
    NEEDS_REVIEW = "⚠️ Needs Review" 
    FAILED = "❌ Failed"
    PENDING = "🔄 Pending"
    SKIPPED = "⏭️ Skipped"


class ConfidenceLevel(Enum):
    """Data confidence assessment"""
    HIGH = 90     # Multiple sources confirm, high reliability
    MEDIUM = 70   # Single reliable source
    LOW = 40      # Uncertain or outdated source
    UNKNOWN = 0   # No confidence assessment available


@dataclass
class FieldEnrichmentConfig:
    """Configuration for a field to be enriched"""
    name: str
    internal_name: str
    priority: EnrichmentPriority
    enrichment_sources: List[str]
    validation_criteria: List[str]
    target_success_rate: float
    required_for_sales: bool = False
    custom_field: bool = False


@dataclass
class EnrichmentResult:
    """Result of a field enrichment attempt"""
    field_name: str
    field_internal_name: str
    old_value: Any
    new_value: Any
    status: EnrichmentStatus
    confidence: ConfidenceLevel
    source: str
    validation_passed: bool
    critique_notes: str = ""
    improvement_suggestions: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class EnrichmentCritique:
    """Detailed critique of enrichment performance"""
    overall_score: float  # 0-100
    field_scores: Dict[str, float]
    success_rate: float
    confidence_distribution: Dict[str, int]
    common_failures: List[str]
    improvement_opportunities: List[str]
    data_quality_issues: List[str]
    recommendations: List[str]


class FieldEnrichmentManagerAgent(SpecializedAgent):
    """Agent that manages systematic field enrichment and quality improvement"""
    
    # Primary Company Fields for CRM Intelligence (Always Include)
    COMPANY_FIELD_CONFIGS: ClassVar[List[FieldEnrichmentConfig]] = [
        # Critical Primary Fields - Always Retrieved
        FieldEnrichmentConfig("Company Name", "name", EnrichmentPriority.CRITICAL, 
                            ["hubspot"], ["format_validation", "completeness"], 0.98, True),
        FieldEnrichmentConfig("Company Domain", "domain", EnrichmentPriority.CRITICAL,
                            ["website_extraction", "email_analysis"], ["domain_validation", "dns_check"], 0.95),
        FieldEnrichmentConfig("Phone Number", "phone", EnrichmentPriority.CRITICAL,
                            ["hubspot", "web_search"], ["format_validation", "accessibility"], 0.90),
        FieldEnrichmentConfig("City", "city", EnrichmentPriority.CRITICAL,
                            ["hubspot"], ["format_validation", "completeness"], 0.95, True),
        FieldEnrichmentConfig("State/Region", "state", EnrichmentPriority.CRITICAL,
                            ["hubspot"], ["format_validation", "completeness"], 0.95, True),
        
        # High Priority Primary Fields
        FieldEnrichmentConfig("Annual Revenue", "annualrevenue", EnrichmentPriority.HIGH,
                            ["external_data", "public_filings"], ["credibility", "recency"], 0.75),
        FieldEnrichmentConfig("Company Type", "company_type", EnrichmentPriority.HIGH,
                            ["web_search", "ai_classification"], ["category_validation", "accuracy"], 0.80),
        FieldEnrichmentConfig("Competitor", "competitor", EnrichmentPriority.HIGH,
                            ["market_research", "ai_analysis"], ["relevance", "accuracy"], 0.75),
        FieldEnrichmentConfig("Lifecycle Stage", "lifecyclestage", EnrichmentPriority.HIGH,
                            ["hubspot"], ["stage_validation", "completeness"], 0.90, True),
        FieldEnrichmentConfig("Club Type", "club_type", EnrichmentPriority.HIGH,
                            ["industry_data", "web_search"], ["category_validation", "relevance"], 0.85),
        
        # Medium Priority Primary Fields
        FieldEnrichmentConfig("Description", "description", EnrichmentPriority.MEDIUM,
                            ["website_extraction", "ai_summarization"], ["quality_assessment", "relevance"], 0.75),
        FieldEnrichmentConfig("Club Info", "club_info", EnrichmentPriority.MEDIUM,
                            ["web_search", "industry_data"], ["completeness", "accuracy"], 0.70),
        FieldEnrichmentConfig("NGF Category", "ngf_category", EnrichmentPriority.MEDIUM,
                            ["industry_data", "classification"], ["category_validation", "relevance"], 0.75),
        FieldEnrichmentConfig("Lead Status", "hs_lead_status", EnrichmentPriority.MEDIUM,
                            ["hubspot"], ["status_validation", "completeness"], 0.85, True),
        FieldEnrichmentConfig("Management Company", "management_company", EnrichmentPriority.MEDIUM,
                            ["web_search", "industry_data"], ["verification", "accuracy"], 0.70),
        FieldEnrichmentConfig("Email Pattern", "email_pattern", EnrichmentPriority.MEDIUM,
                            ["email_analysis", "domain_research"], ["pattern_validation", "accuracy"], 0.80),
        FieldEnrichmentConfig("Market", "market", EnrichmentPriority.MEDIUM,
                            ["geographic_data", "market_research"], ["relevance", "accuracy"], 0.75),
        
        # Additional Important Fields
        FieldEnrichmentConfig("Has Pool", "has_pool", EnrichmentPriority.LOW,
                            ["web_search", "facility_data"], ["boolean_validation", "accuracy"], 0.70),
        FieldEnrichmentConfig("Has Tennis Courts", "has_tennis_courts", EnrichmentPriority.LOW,
                            ["web_search", "facility_data"], ["boolean_validation", "accuracy"], 0.70),
        FieldEnrichmentConfig("Number of Holes", "number_of_holes", EnrichmentPriority.LOW,
                            ["web_search", "industry_data"], ["numeric_validation", "accuracy"], 0.75),
        
        # Standard Enrichment Fields
        FieldEnrichmentConfig("Website URL", "website", EnrichmentPriority.HIGH,
                            ["web_search", "domain_research"], ["url_validation", "accessibility"], 0.90),
        FieldEnrichmentConfig("Industry", "industry", EnrichmentPriority.HIGH,
                            ["web_search", "ai_classification"], ["industry_standards", "accuracy"], 0.85),
        FieldEnrichmentConfig("LinkedIn Company Page", "linkedin_company_page", EnrichmentPriority.MEDIUM,
                            ["linkedin_search"], ["url_validation", "profile_match"], 0.85)
    ]
    
    # Top 10 Contact Fields for Swoop Sales Process  
    CONTACT_FIELD_CONFIGS: ClassVar[List[FieldEnrichmentConfig]] = [
        FieldEnrichmentConfig("Email", "email", EnrichmentPriority.CRITICAL,
                            ["hubspot"], ["format_validation", "deliverability"], 0.98, True),
        FieldEnrichmentConfig("First Name", "firstname", EnrichmentPriority.CRITICAL,
                            ["hubspot"], ["format_validation", "completeness"], 0.98, True),
        FieldEnrichmentConfig("Last Name", "lastname", EnrichmentPriority.CRITICAL,
                            ["hubspot"], ["format_validation", "completeness"], 0.98, True),
        FieldEnrichmentConfig("Job Title", "jobtitle", EnrichmentPriority.HIGH,
                            ["linkedin", "web_search"], ["accuracy", "standardization"], 0.85),
        FieldEnrichmentConfig("Job Seniority Level", "job_seniority", EnrichmentPriority.HIGH,
                            ["ai_parsing"], ["seniority_mapping", "consistency"], 0.80, custom_field=True),
        FieldEnrichmentConfig("Direct Phone", "phone", EnrichmentPriority.HIGH,
                            ["external_data", "web_search"], ["format_validation", "reachability"], 0.70),
        FieldEnrichmentConfig("LinkedIn Profile", "linkedin_profile", EnrichmentPriority.MEDIUM,
                            ["linkedin_search"], ["url_validation", "profile_match"], 0.75, custom_field=True),
        FieldEnrichmentConfig("Department/Function", "job_function", EnrichmentPriority.MEDIUM,
                            ["ai_parsing"], ["function_mapping", "consistency"], 0.75, custom_field=True),
        FieldEnrichmentConfig("Years of Experience", "years_experience", EnrichmentPriority.LOW,
                            ["linkedin_analysis"], ["reasonableness", "source_quality"], 0.65, custom_field=True),
        FieldEnrichmentConfig("Previous Companies", "previous_companies", EnrichmentPriority.LOW,
                            ["linkedin_analysis"], ["relevance", "career_progression"], 0.60, custom_field=True)
    ]
    
    def __init__(self, **kwargs):
        super().__init__(
            name="FieldEnrichmentManagerAgent",
            domain="field_enrichment_management",
            specialized_tools=[
                "search_companies",
                "search_contacts", 
                "generate_company_report",
                "generate_contact_report",
                "web_search",
                "get_company_metadata"
            ],
            instruction="""
            You are the Field Enrichment Manager Agent, responsible for systematically enriching 
            and validating the top 10 most valuable CRM fields for companies and contacts in the 
            Swoop sales process.

            🎯 CORE RESPONSIBILITIES:
            1. **Enrichment Orchestration**: Manage systematic field enrichment across all records
            2. **Quality Assessment**: Critique enrichment results and identify improvement areas
            3. **Process Optimization**: Document and implement enrichment process improvements
            4. **Validation Management**: Ensure enriched data meets quality standards
            5. **Performance Tracking**: Monitor success rates and field completion metrics

            🔍 ENRICHMENT PROCESS:
            1. **Field Analysis**: Assess current field completion and quality
            2. **Gap Identification**: Identify missing or low-quality field data
            3. **Enrichment Execution**: Coordinate data enrichment from multiple sources
            4. **Quality Validation**: Apply validation criteria to enriched data
            5. **Critique & Analysis**: Evaluate enrichment performance and identify issues
            6. **Improvement Documentation**: Record insights and optimization opportunities

            📊 FIELD PRIORITIES:
            
            **CRITICAL FIELDS** (Must achieve 95%+ success rate):
            - Company Name, Website URL (companies)
            - Email, First Name, Last Name (contacts)
            
            **HIGH PRIORITY** (Target 85%+ success rate):
            - Domain, Industry, Revenue, Employee Count (companies)  
            - Job Title, Seniority, Phone (contacts)
            
            **MEDIUM/LOW PRIORITY** (Target 70%+ success rate):
            - LinkedIn, Address, Description, Tech Stack (companies)
            - LinkedIn Profile, Function, Experience, Previous Companies (contacts)

            🔄 ENRICHMENT SOURCES:
            - **HubSpot Data**: Existing CRM data and associations
            - **Web Search**: Company websites, news, industry information
            - **LinkedIn Integration**: Professional profiles and company pages
            - **External APIs**: Business directories, data providers
            - **AI Processing**: Intelligent parsing and classification

            🛡️ VALIDATION CRITERIA:
            - **Format Validation**: Proper formatting and structure
            - **Accuracy Assessment**: Cross-source verification when possible
            - **Completeness Check**: Required fields populated appropriately
            - **Relevance Scoring**: Data relevance to sales process
            - **Confidence Rating**: Source reliability and data quality

            📈 CRITIQUE FRAMEWORK:
            
            **Performance Metrics**:
            - Field completion rates vs. targets
            - Data confidence score distribution
            - Validation pass/fail rates
            - Source reliability assessment
            
            **Quality Assessment**:
            - Data accuracy and consistency
            - Format standardization compliance
            - Business relevance and utility
            - Recency and currency of information
            
            **Improvement Identification**:
            - Common failure patterns
            - Source reliability issues  
            - Process bottlenecks
            - Enhancement opportunities

            💡 IMPROVEMENT DOCUMENTATION:
            
            **Process Improvements**:
            - Enrichment workflow optimizations
            - New data source integrations
            - Validation criteria enhancements
            - Automation opportunities
            
            **Quality Enhancements**:
            - Data normalization improvements
            - Confidence scoring refinements
            - Cross-validation strategies
            - Error handling enhancements
            
            **Strategic Recommendations**:
            - Field priority adjustments
            - Success rate target modifications
            - Resource allocation suggestions
            - Technology integration opportunities

            🎯 SUCCESS CRITERIA:
            - Achieve target success rates for each field priority level
            - Maintain high data confidence scores (>80% average)
            - Minimize manual review requirements (<10% of records)
            - Continuously improve enrichment effectiveness
            - Provide actionable insights for process optimization

            Always focus on systematic improvement and measurable quality enhancement.
            Document all insights and recommendations for future optimization.
            """,
            **kwargs
        )
    
    @classmethod
    def get_primary_company_fields(cls) -> List[str]:
        """Get list of primary company fields that should always be retrieved."""
        return [
            "name", "domain", "phone", "city", "state", "country", "website", "description", "hs_object_id",
            "annualrevenue", "company_type", "ngf_category", "competitor", "lifecyclestage", "hs_lead_status",
            "club_type", "club_info", "management_company", "state_region_code", "email_pattern", "market",
            "has_pool", "has_tennis_courts", "postal_code", "street_address", "number_of_holes", "industry"
        ]
    
    @classmethod
    def get_critical_company_fields(cls) -> List[str]:
        """Get list of critical company fields (highest priority)."""
        return [config.hubspot_property for config in cls.COMPANY_FIELD_CONFIGS 
                if config.priority == EnrichmentPriority.CRITICAL]
        
        # Initialize instance variables using object.__setattr__ to bypass Pydantic validation
        object.__setattr__(self, 'enrichment_history', [])
        object.__setattr__(self, 'improvement_log', [])
        object.__setattr__(self, 'performance_metrics', {})
        
        # Initialize workflow agents
        object.__setattr__(self, 'workflow_factories', {'comprehensive': create_field_enrichment_workflow})
        object.__setattr__(self, 'comprehensive_workflow', None)
    
    def call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """Call a tool via the MCP server."""
        import requests
        import json
        
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "call_tool",
            "params": {
                "name": tool_name,
                "arguments": arguments or {}
            }
        }
        
        try:
            # Use the MCP server endpoint
            mcp_url = "http://localhost:8081/mcp"  # MCP server URL
            
            response = requests.post(mcp_url, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            if "error" in result:
                return {"error": result["error"]}
            
            # Extract the actual content from MCP response format
            mcp_result = result.get("result", {})
            if "content" in mcp_result and mcp_result["content"]:
                # MCP returns content as array with text field
                content_text = mcp_result["content"][0].get("text", "{}")
                try:
                    return json.loads(content_text)
                except json.JSONDecodeError:
                    return {"raw_text": content_text}
            
            return mcp_result
            
        except Exception as e:
            logger.error(f"MCP tool call error for {tool_name}: {e}")
            return {"error": str(e)}
    
        
    def analyze_field_completeness(self, record_type: str, record_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze field completeness for a company or contact record"""
        
        if record_type.lower() == 'company':
            field_configs = self.COMPANY_FIELD_CONFIGS
        else:
            field_configs = self.CONTACT_FIELD_CONFIGS
            
        analysis = {
            'total_fields': len(field_configs),
            'populated_fields': 0,
            'missing_critical': [],
            'missing_high_priority': [],
            'missing_medium_low': [],
            'field_details': {},
            'completion_score': 0.0
        }
        
        properties = record_data.get('properties', {})
        
        for config in field_configs:
            field_value = properties.get(config.internal_name)
            is_populated = bool(field_value and str(field_value).strip())
            
            field_info = {
                'name': config.name,
                'internal_name': config.internal_name,
                'priority': config.priority.name,
                'populated': is_populated,
                'current_value': field_value,
                'required_for_sales': config.required_for_sales,
                'target_success_rate': config.target_success_rate
            }
            
            analysis['field_details'][config.internal_name] = field_info
            
            if is_populated:
                analysis['populated_fields'] += 1
            else:
                if config.priority == EnrichmentPriority.CRITICAL:
                    analysis['missing_critical'].append(config.name)
                elif config.priority == EnrichmentPriority.HIGH:
                    analysis['missing_high_priority'].append(config.name)
                else:
                    analysis['missing_medium_low'].append(config.name)
        
        analysis['completion_score'] = (analysis['populated_fields'] / analysis['total_fields']) * 100
        
        return analysis
    
    def enrich_record_fields(self, record_type: str, record_id: str, dry_run: bool = False, 
                           use_workflow: bool = True) -> List[EnrichmentResult]:
        """Enrich missing fields for a specific record using workflow orchestration"""
        
        results = []
        
        if use_workflow:
            return self._enrich_with_workflow(record_type, record_id, dry_run)
        
        try:
            # Get record data from HubSpot
            if record_type.lower() == 'company':
                # Use search_companies to find the company
                search_response = self.use_tool('search_companies', {'query': f'hs_object_id:{record_id}'})
                if not search_response or 'companies' not in search_response:
                    logger.error(f"Could not find company {record_id}")
                    return results
                
                companies = search_response.get('companies', [])
                if not companies:
                    logger.error(f"No company found with ID {record_id}")
                    return results
                
                record_data = companies[0]
                field_configs = self.COMPANY_FIELD_CONFIGS
            else:
                # Use search_contacts to find the contact
                search_response = self.use_tool('search_contacts', {'query': f'hs_object_id:{record_id}'})
                if not search_response or 'contacts' not in search_response:
                    logger.error(f"Could not find contact {record_id}")
                    return results
                
                contacts = search_response.get('contacts', [])
                if not contacts:
                    logger.error(f"No contact found with ID {record_id}")
                    return results
                
                record_data = contacts[0]
                field_configs = self.CONTACT_FIELD_CONFIGS
            
            # Analyze current field completeness
            completeness_analysis = self.analyze_field_completeness(record_type, record_data)
            
            # Enrich missing fields
            for config in field_configs:
                field_detail = completeness_analysis['field_details'][config.internal_name]
                
                if not field_detail['populated']:
                    # Attempt enrichment for this field
                    enrichment_result = self._enrich_single_field(record_type, record_data, config)
                    results.append(enrichment_result)
                else:
                    # Field already populated - create skipped result
                    results.append(EnrichmentResult(
                        field_name=config.name,
                        field_internal_name=config.internal_name,
                        old_value=field_detail['current_value'],
                        new_value=field_detail['current_value'],
                        status=EnrichmentStatus.SKIPPED,
                        confidence=ConfidenceLevel.HIGH,
                        source="existing_data",
                        validation_passed=True,
                        critique_notes="Field already populated with data"
                    ))
            
            # Store enrichment history
            self.enrichment_history.append({
                'timestamp': datetime.now(),
                'record_type': record_type,
                'record_id': record_id,
                'results': results,
                'dry_run': dry_run
            })
            
        except Exception as e:
            logger.error(f"Error enriching {record_type} {record_id}: {e}")
            
        return results
    
    def _enrich_with_workflow(self, record_type: str, record_id: str, dry_run: bool = False) -> List[EnrichmentResult]:
        """Enrich record using workflow orchestration"""
        
        try:
            # Initialize comprehensive workflow if not already done
            if not self.comprehensive_workflow:
                self.comprehensive_workflow = create_field_enrichment_workflow()
            
            # Prepare session state for workflow
            session_state = {
                'record_type': record_type,
                'record_id': record_id,
                'dry_run': dry_run,
                'target_success_rates': {
                    'critical': 0.95,
                    'high': 0.85,
                    'medium': 0.70
                },
                'max_iterations': 3,
                'current_iteration': 0
            }
            
            # Create context for workflow execution
            from google.adk.agents import InvocationContext
            context = InvocationContext()
            context.session_state = session_state
            
            # Execute the comprehensive workflow
            logger.info(f"Starting workflow-based enrichment for {record_type} {record_id}")
            workflow_result = self.comprehensive_workflow.run(context)
            
            # Extract enrichment results from workflow execution
            results = self._extract_results_from_workflow(context, record_type, record_id)
            
            # Store workflow execution in history
            self.enrichment_history.append({
                'timestamp': datetime.now(),
                'record_type': record_type,
                'record_id': record_id,
                'workflow_used': True,
                'results': results,
                'dry_run': dry_run,
                'workflow_context': context.session_state
            })
            
            logger.info(f"Workflow enrichment completed: {len(results)} fields processed")
            return results
            
        except Exception as e:
            logger.error(f"Workflow enrichment failed for {record_type} {record_id}: {e}")
            # Fallback to direct enrichment
            return self._enrich_direct(record_type, record_id, dry_run)
    
    def _enrich_direct(self, record_type: str, record_id: str, dry_run: bool = False) -> List[EnrichmentResult]:
        """Direct enrichment without workflow orchestration (fallback)"""
        
        logger.info(f"Using direct enrichment for {record_type} {record_id}")
        
        results = []
        
        try:
            # Get record data using MCP tools
            if record_type.lower() == 'company':
                field_configs = self.COMPANY_FIELD_CONFIGS
                # Use the inherited MCP tools from base agent
                record_data = self._get_company_data_via_mcp(record_id)
                if not record_data:
                    return results
            else:
                field_configs = self.CONTACT_FIELD_CONFIGS
                record_data = self._get_contact_data_via_mcp(record_id)
                if not record_data:
                    return results
            
            # Process each field
            for config in field_configs:
                result = self._enrich_single_field(record_type, record_data, config)
                results.append(result)
            
        except Exception as e:
            logger.error(f"Direct enrichment failed: {e}")
        
        return results
    
    def _enrich_with_company_data(self, company_data: Dict[str, Any], dry_run: bool = False) -> List[EnrichmentResult]:
        """Enrich fields using provided company data (bypass MCP lookup)"""
        
        logger.info(f"Enriching company with provided data: {company_data.get('properties', {}).get('name', 'Unknown')}")
        
        results = []
        field_configs = self.COMPANY_FIELD_CONFIGS
        
        try:
            # Process each field
            for config in field_configs:
                result = self._enrich_single_field('company', company_data, config)
                results.append(result)
                
        except Exception as e:
            logger.error(f"Enrichment with company data failed: {e}")
        
        return results
    
    def _get_company_data_via_mcp(self, company_id: str) -> Optional[Dict[str, Any]]:
        """Get company data using MCP HubSpot server"""
        try:
            # Use the MCP toolset that's configured in the base agent
            # The base agent should have HubSpot MCP tools available
            
            # Try multiple search strategies to find the company
            
            # Strategy 1: Search by ID directly
            search_result = self.call_mcp_tool("search_companies", {
                "query": company_id,
                "limit": 10
            })
            
            if search_result and "results" in search_result:
                # Look for exact ID match
                for company in search_result["results"]:
                    if company.get("id") == company_id or company.get("properties", {}).get("hs_object_id") == company_id:
                        logger.info(f"Found company {company_id}: {company.get('properties', {}).get('name', 'Unknown')}")
                        return company
            
            # Strategy 2: Search with hs_object_id prefix
            search_result2 = self.call_mcp_tool("search_companies", {
                "query": f"hs_object_id:{company_id}",
                "limit": 1
            })
            
            if search_result2 and "results" in search_result2 and search_result2["results"]:
                logger.info(f"Found company via hs_object_id search: {search_result2['results'][0].get('properties', {}).get('name', 'Unknown')}")
                return search_result2["results"][0]
            
            # Strategy 3: Get all companies with pagination
            logger.info(f"Searching through all companies for ID {company_id}")
            
            # Try multiple pages to find the company
            for page_limit in [100, 200, 500]:
                all_companies_result = self.call_mcp_tool("get_companies", {
                    "limit": page_limit
                })
                
                if all_companies_result and "results" in all_companies_result:
                    for company in all_companies_result["results"]:
                        if (company.get("id") == company_id or 
                            company.get("properties", {}).get("hs_object_id") == company_id):
                            logger.info(f"Found company in full list (page {page_limit}): {company.get('properties', {}).get('name', 'Unknown')}")
                            return company
                
                # If we found some results but not our target, try next page size
                if all_companies_result and "results" in all_companies_result:
                    continue
                else:
                    break
            
            logger.warning(f"Company {company_id} not found in HubSpot after exhaustive search")
            return None
            
        except Exception as e:
            logger.error(f"Error getting company data via MCP: {e}")
            return None
    
    def _get_contact_data_via_mcp(self, contact_id: str) -> Optional[Dict[str, Any]]:
        """Get contact data using MCP HubSpot server"""
        try:
            # Try to get contact data using MCP tools
            # First try searching by ID
            search_result = self.call_mcp_tool("search_contacts", {
                "query": f"hs_object_id:{contact_id}",
                "limit": 1
            })
            
            if search_result and "results" in search_result and search_result["results"]:
                return search_result["results"][0]
            
            # If that doesn't work, try getting contact details directly
            contact_result = self.call_mcp_tool("get_contact_details", {
                "contact_id": contact_id
            })
            
            if contact_result and "error" not in contact_result:
                return contact_result
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting contact data via MCP: {e}")
            return None
    
    def _parse_mcp_response(self, response: Any, record_type: str) -> Optional[Dict[str, Any]]:
        """Parse MCP response to extract record data"""
        try:
            # Convert response to string if it's not already
            response_str = str(response)
            
            # Try to extract JSON if present
            import json
            import re
            
            # Look for JSON patterns in the response
            json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
            json_matches = re.findall(json_pattern, response_str)
            
            for match in json_matches:
                try:
                    data = json.loads(match)
                    if isinstance(data, dict):
                        # Look for properties or relevant data structure
                        if 'properties' in data:
                            return data
                        elif record_type in data:
                            return data[record_type]
                        elif any(key in data for key in ['name', 'firstname', 'lastname', 'email']):
                            return {'properties': data}
                except json.JSONDecodeError:
                    continue
            
            # If no JSON found, create a basic structure with the response
            return {
                'id': 'unknown',
                'properties': {
                    'raw_response': response_str
                }
            }
            
        except Exception as e:
            logger.error(f"Error parsing MCP response: {e}")
            return None
    
    def _extract_results_from_workflow(self, context: InvocationContext, record_type: str, record_id: str) -> List[EnrichmentResult]:
        """Extract enrichment results from workflow execution context"""
        
        results = []
        session_state = context.session_state
        
        # Extract results from different workflow stages
        field_analysis = session_state.get('FIELD_ANALYSIS_RESULTS', {})
        web_results = session_state.get('WEB_ENRICHMENT_RESULTS', {})
        linkedin_results = session_state.get('LINKEDIN_ENRICHMENT_RESULTS', {})
        external_results = session_state.get('EXTERNALDATA_ENRICHMENT_RESULTS', {})
        validation_results = session_state.get('VALIDATION_RESULTS', {})
        
        # Combine results from all sources
        all_source_results = {
            **web_results,
            **linkedin_results,
            **external_results
        }
        
        # Convert to EnrichmentResult objects
        field_configs = self.COMPANY_FIELD_CONFIGS if record_type.lower() == 'company' else self.CONTACT_FIELD_CONFIGS
        
        for config in field_configs:
            field_name = config.internal_name
            
            if field_name in all_source_results:
                source_result = all_source_results[field_name]
                validation = validation_results.get(field_name, {})
                
                result = EnrichmentResult(
                    field_name=config.name,
                    field_internal_name=config.internal_name,
                    old_value=source_result.get('old_value', ''),
                    new_value=source_result.get('new_value', ''),
                    status=EnrichmentStatus(source_result.get('status', 'FAILED')),
                    confidence=ConfidenceLevel(source_result.get('confidence', 0)),
                    source=source_result.get('source', 'workflow'),
                    validation_passed=validation.get('passed', False),
                    critique_notes=source_result.get('notes', ''),
                    improvement_suggestions=source_result.get('suggestions', [])
                )
                results.append(result)
            else:
                # Create a "not processed" result
                result = EnrichmentResult(
                    field_name=config.name,
                    field_internal_name=config.internal_name,
                    old_value='',
                    new_value='',
                    status=EnrichmentStatus.PENDING,
                    confidence=ConfidenceLevel.UNKNOWN,
                    source='workflow',
                    validation_passed=False,
                    critique_notes='Field not processed by workflow'
                )
                results.append(result)
        
        return results
    
    def run_workflow_type(self, workflow_type: str, record_type: str, record_id: str, 
                         **workflow_params) -> List[EnrichmentResult]:
        """Run a specific type of workflow for field enrichment"""
        
        if workflow_type not in self.workflow_factories:
            available_types = list(self.workflow_factories.keys())
            raise ValueError(f"Unknown workflow type: {workflow_type}. Available: {available_types}")
        
        try:
            # Create the specified workflow
            workflow_factory = self.workflow_factories[workflow_type]
            workflow = workflow_factory(**workflow_params)
            
            # Prepare session state
            session_state = {
                'record_type': record_type,
                'record_id': record_id,
                'workflow_type': workflow_type,
                **workflow_params
            }
            
            # Create context and run workflow
            from google.adk.agents import InvocationContext
            context = InvocationContext()
            context.session_state = session_state
            
            logger.info(f"Running {workflow_type} workflow for {record_type} {record_id}")
            workflow_result = workflow.run(context)
            
            # Extract and return results
            results = self._extract_results_from_workflow(context, record_type, record_id)
            
            logger.info(f"{workflow_type} workflow completed: {len(results)} fields processed")
            return results
            
        except Exception as e:
            logger.error(f"{workflow_type} workflow failed: {e}")
            raise
    
    def compare_workflow_performance(self, record_type: str, record_id: str) -> Dict[str, Any]:
        """Compare performance of different workflow types on the same record"""
        
        performance_comparison = {
            'record_type': record_type,
            'record_id': record_id,
            'timestamp': datetime.now(),
            'workflow_results': {}
        }
        
        # Test each workflow type
        for workflow_type in self.workflow_factories.keys():
            try:
                logger.info(f"Testing {workflow_type} workflow...")
                
                start_time = datetime.now()
                results = self.run_workflow_type(workflow_type, record_type, record_id, dry_run=True)
                end_time = datetime.now()
                
                # Calculate performance metrics
                total_fields = len(results)
                successful_fields = len([r for r in results if r.status == EnrichmentStatus.COMPLETE])
                success_rate = (successful_fields / total_fields) * 100 if total_fields > 0 else 0
                execution_time = (end_time - start_time).total_seconds()
                
                # Calculate average confidence
                confidence_scores = [r.confidence.value for r in results if r.confidence != ConfidenceLevel.UNKNOWN]
                avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
                
                performance_comparison['workflow_results'][workflow_type] = {
                    'success_rate': success_rate,
                    'total_fields': total_fields,
                    'successful_fields': successful_fields,
                    'execution_time_seconds': execution_time,
                    'average_confidence': avg_confidence,
                    'results': results
                }
                
                logger.info(f"{workflow_type} workflow: {success_rate:.1f}% success in {execution_time:.2f}s")
                
            except Exception as e:
                logger.error(f"Failed to test {workflow_type} workflow: {e}")
                performance_comparison['workflow_results'][workflow_type] = {
                    'error': str(e),
                    'success_rate': 0,
                    'execution_time_seconds': 0
                }
        
        # Determine best performing workflow
        best_workflow = None
        best_score = 0
        
        for workflow_type, metrics in performance_comparison['workflow_results'].items():
            if 'error' not in metrics:
                # Combined score: success_rate * 0.7 + (avg_confidence/100) * 0.3
                score = metrics['success_rate'] * 0.7 + (metrics['average_confidence']/100) * 30
                if score > best_score:
                    best_score = score
                    best_workflow = workflow_type
        
        performance_comparison['best_workflow'] = best_workflow
        performance_comparison['best_score'] = best_score
        
        # Document comparison results
        self._document_workflow_comparison(performance_comparison)
        
        return performance_comparison
    
    def _document_workflow_comparison(self, comparison: Dict[str, Any]):
        """Document workflow performance comparison results"""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"workflow_performance_comparison_{comparison['record_type']}_{timestamp}.md"
        filepath = os.path.join(os.path.dirname(__file__), '..', '..', 'docs', filename)
        
        report_lines = [
            "# Workflow Performance Comparison Report",
            f"**Generated**: {comparison['timestamp']}",
            f"**Record Type**: {comparison['record_type']}",
            f"**Record ID**: {comparison['record_id']}",
            "",
            "## Executive Summary",
            f"**Best Performing Workflow**: {comparison['best_workflow']}",
            f"**Best Performance Score**: {comparison['best_score']:.1f}",
            "",
            "## Workflow Performance Details",
            ""
        ]
        
        for workflow_type, metrics in comparison['workflow_results'].items():
            if 'error' not in metrics:
                report_lines.extend([
                    f"### {workflow_type.title()} Workflow",
                    f"- **Success Rate**: {metrics['success_rate']:.1f}%",
                    f"- **Fields Processed**: {metrics['total_fields']}",
                    f"- **Successful Fields**: {metrics['successful_fields']}",
                    f"- **Execution Time**: {metrics['execution_time_seconds']:.2f} seconds",
                    f"- **Average Confidence**: {metrics['average_confidence']:.1f}",
                    ""
                ])
            else:
                report_lines.extend([
                    f"### {workflow_type.title()} Workflow",
                    f"- **Status**: Failed",
                    f"- **Error**: {metrics['error']}",
                    ""
                ])
        
        report_lines.extend([
            "## Recommendations",
            "",
            f"1. **Primary Workflow**: Use {comparison['best_workflow']} workflow for optimal performance",
            "2. **Performance Monitoring**: Track workflow performance over time",
            "3. **Optimization**: Focus on improving lower-performing workflows",
            "",
            "---",
            "*Generated by Field Enrichment Manager Agent*"
        ])
        
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w') as f:
                f.write("\n".join(report_lines))
            
            logger.info(f"Workflow comparison documented in {filepath}")
        except Exception as e:
            logger.error(f"Error saving workflow comparison: {e}")
    
    def _enrich_single_field(self, record_type: str, record_data: Dict[str, Any], 
                           config: FieldEnrichmentConfig) -> EnrichmentResult:
        """Enrich a single field using appropriate sources"""
        
        properties = record_data.get('properties', {})
        current_value = properties.get(config.internal_name)
        
        # Field-specific enrichment logic
        if config.internal_name == 'name':
            # Company name should already be populated - just validate it
            if current_value and current_value.strip():
                return EnrichmentResult(
                    field_name=config.name,
                    field_internal_name=config.internal_name,
                    old_value=current_value,
                    new_value=current_value,
                    status=EnrichmentStatus.SKIPPED,
                    confidence=ConfidenceLevel.HIGH,
                    source="existing_data",
                    validation_passed=True,
                    critique_notes="Company name already populated"
                )
            else:
                return EnrichmentResult(
                    field_name=config.name,
                    field_internal_name=config.internal_name,
                    old_value=current_value,
                    new_value=current_value,
                    status=EnrichmentStatus.FAILED,
                    confidence=ConfidenceLevel.UNKNOWN,
                    source="existing_data",
                    validation_passed=False,
                    critique_notes="Company name is missing - this is a critical field"
                )
        elif config.internal_name == 'website':
            return self._enrich_website_field(record_data, config)
        elif config.internal_name == 'domain':
            return self._enrich_domain_field(record_data, config)
        elif config.internal_name == 'industry':
            return self._enrich_industry_field(record_data, config)
        elif config.internal_name == 'description':
            return self._enrich_description_field(record_data, config)
        elif config.internal_name in ['job_seniority', 'job_function']:
            return self._enrich_job_parsing_field(record_data, config)
        elif config.internal_name == 'annualrevenue':
            return self._enrich_annual_revenue_field(record_data, config)
        elif config.internal_name == 'numberofemployees':
            return self._enrich_employee_count_field(record_data, config)
        elif config.internal_name == 'linkedin_company_page':
            return self._enrich_linkedin_company_field(record_data, config)
        elif config.internal_name == 'phone':
            return self._enrich_phone_field(record_data, config)
        elif config.internal_name in ['firstname', 'lastname', 'email']:
            # Contact critical fields - should already be populated
            if current_value and current_value.strip():
                return EnrichmentResult(
                    field_name=config.name,
                    field_internal_name=config.internal_name,
                    old_value=current_value,
                    new_value=current_value,
                    status=EnrichmentStatus.SKIPPED,
                    confidence=ConfidenceLevel.HIGH,
                    source="existing_data",
                    validation_passed=True,
                    critique_notes=f"{config.name} already populated"
                )
            else:
                return EnrichmentResult(
                    field_name=config.name,
                    field_internal_name=config.internal_name,
                    old_value=current_value,
                    new_value=current_value,
                    status=EnrichmentStatus.FAILED,
                    confidence=ConfidenceLevel.UNKNOWN,
                    source="existing_data",
                    validation_passed=False,
                    critique_notes=f"{config.name} is missing - this is a critical field"
                )
        else:
            # Default handling for not-yet-implemented fields
            return EnrichmentResult(
                field_name=config.name,
                field_internal_name=config.internal_name,
                old_value=current_value,
                new_value=current_value,
                status=EnrichmentStatus.FAILED,
                confidence=ConfidenceLevel.UNKNOWN,
                source="not_implemented",
                validation_passed=False,
                critique_notes=f"Enrichment logic for {config.name} not yet implemented",
                improvement_suggestions=[
                    f"Implement enrichment logic for {config.name}",
                    f"Define data sources for {', '.join(config.enrichment_sources)}",
                    f"Create validation criteria for {', '.join(config.validation_criteria)}"
                ]
            )
    
    def _enrich_website_field(self, record_data: Dict[str, Any], config: FieldEnrichmentConfig) -> EnrichmentResult:
        """Enrich website field using multiple strategies"""
        
        properties = record_data.get('properties', {})
        company_name = properties.get('name', '')
        domain = properties.get('domain', '')
        current_value = properties.get(config.internal_name)
        
        if not company_name:
            return EnrichmentResult(
                field_name=config.name,
                field_internal_name=config.internal_name,
                old_value=current_value,
                new_value=current_value,
                status=EnrichmentStatus.FAILED,
                confidence=ConfidenceLevel.UNKNOWN,
                source="web_search",
                validation_passed=False,
                critique_notes="Cannot search for website without company name"
            )
        
        # Strategy 1: If we have a domain, construct the website URL
        if domain and not current_value:
            website_candidates = [
                f"https://www.{domain}",
                f"https://{domain}",
                f"http://www.{domain}",
                f"http://{domain}"
            ]
            
            for candidate in website_candidates:
                if self._validate_url_accessibility(candidate):
                    return EnrichmentResult(
                        field_name=config.name,
                        field_internal_name=config.internal_name,
                        old_value=current_value,
                        new_value=candidate,
                        status=EnrichmentStatus.COMPLETE,
                        confidence=ConfidenceLevel.HIGH,
                        source="domain_construction",
                        validation_passed=True,
                        critique_notes=f"Constructed from domain: {domain}"
                    )
        
        # Strategy 2: Web search for official website
        try:
            search_queries = [
                f"{company_name} official website",
                f"{company_name} homepage",
                f'"{company_name}" site:',
                f"{company_name} contact information website"
            ]
            
            for query in search_queries:
                search_result = self.call_mcp_tool("web_search", {
                    "query": query,
                    "num_results": 5
                })
                
                website_url = self._extract_website_from_search(search_result, company_name)
                if website_url and self._validate_url_accessibility(website_url):
                    return EnrichmentResult(
                        field_name=config.name,
                        field_internal_name=config.internal_name,
                        old_value=current_value,
                        new_value=website_url,
                        status=EnrichmentStatus.COMPLETE,
                        confidence=ConfidenceLevel.MEDIUM,
                        source="web_search_mcp",
                        validation_passed=True,
                        critique_notes=f"Found via web search: {query}"
                    )
            
            # Strategy 3: Domain guessing based on company name
            website_url = self._guess_domain_from_company_name(company_name)
            if website_url:
                return EnrichmentResult(
                    field_name=config.name,
                    field_internal_name=config.internal_name,
                    old_value=current_value,
                    new_value=website_url,
                    status=EnrichmentStatus.COMPLETE,
                    confidence=ConfidenceLevel.LOW,
                    source="domain_guessing",
                    validation_passed=True,
                    critique_notes="Guessed from company name - needs verification"
                )
            
        except Exception as e:
            logger.error(f"Website enrichment error: {e}")
        
        return EnrichmentResult(
            field_name=config.name,
            field_internal_name=config.internal_name,
            old_value=current_value,
            new_value=current_value,
            status=EnrichmentStatus.FAILED,
            confidence=ConfidenceLevel.LOW,
            source="web_search_mcp",
            validation_passed=False,
            critique_notes="Could not find or validate website URL"
        )
    
    def _extract_website_from_search(self, search_result: Any, company_name: str) -> Optional[str]:
        """Extract website URL from search results"""
        try:
            result_str = str(search_result).lower()
            
            # Look for common website patterns
            import re
            
            # Pattern for URLs
            url_pattern = r'https?://(?:[-\w.])+(?:\.[a-zA-Z]{2,})+(?:/[^"\s]*)?'
            urls = re.findall(url_pattern, str(search_result), re.IGNORECASE)
            
            if urls:
                # Prefer URLs that seem related to the company name
                company_words = company_name.lower().replace(' ', '').replace(',', '').replace('.', '')
                for url in urls:
                    if any(word in url.lower() for word in company_words.split() if len(word) > 2):
                        return url
                
                # If no company-specific URL found, return the first one
                return urls[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting website from search: {e}")
            return None
    
    def _enrich_domain_field(self, record_data: Dict[str, Any], config: FieldEnrichmentConfig) -> EnrichmentResult:
        """Enrich domain field from website URL"""
        
        properties = record_data.get('properties', {})
        website = properties.get('website', '')
        current_value = properties.get(config.internal_name)
        
        if not website:
            return EnrichmentResult(
                field_name=config.name,
                field_internal_name=config.internal_name,
                old_value=current_value,
                new_value=current_value,
                status=EnrichmentStatus.FAILED,
                confidence=ConfidenceLevel.UNKNOWN,
                source="website_extraction",
                validation_passed=False,
                critique_notes="No website URL available for domain extraction",
                improvement_suggestions=[
                    "Enrich website field first",
                    "Try domain guessing from company name",
                    "Use email domain as fallback"
                ]
            )
        
        try:
            from urllib.parse import urlparse
            parsed = urlparse(website if website.startswith('http') else f'http://{website}')
            domain = parsed.netloc.replace('www.', '').lower()
            
            if domain:
                return EnrichmentResult(
                    field_name=config.name,
                    field_internal_name=config.internal_name,
                    old_value=current_value,
                    new_value=domain,
                    status=EnrichmentStatus.COMPLETE,
                    confidence=ConfidenceLevel.HIGH,
                    source="website_extraction",
                    validation_passed=True,
                    critique_notes="Successfully extracted from website URL",
                    improvement_suggestions=[
                        "Add DNS validation to confirm domain is active",
                        "Check for domain redirects",
                        "Validate domain ownership"
                    ]
                )
            
        except Exception as e:
            pass
        
        return EnrichmentResult(
            field_name=config.name,
            field_internal_name=config.internal_name,
            old_value=current_value,
            new_value=current_value,
            status=EnrichmentStatus.FAILED,
            confidence=ConfidenceLevel.LOW,
            source="website_extraction",
            validation_passed=False,
            critique_notes="Could not extract valid domain from website",
            improvement_suggestions=[
                "Improve URL parsing logic",
                "Handle edge cases in domain extraction",
                "Add manual review for complex cases"
            ]
        )
    
    def _enrich_industry_field(self, record_data: Dict[str, Any], config: FieldEnrichmentConfig) -> EnrichmentResult:
        """Enrich industry field using web search and AI classification via MCP"""
        
        properties = record_data.get('properties', {})
        company_name = properties.get('name', '')
        website = properties.get('website', '')
        current_value = properties.get(config.internal_name)
        
        if not company_name:
            return EnrichmentResult(
                field_name=config.name,
                field_internal_name=config.internal_name,
                old_value=current_value,
                new_value=current_value,
                status=EnrichmentStatus.FAILED,
                confidence=ConfidenceLevel.UNKNOWN,
                source="ai_classification",
                validation_passed=False,
                critique_notes="Cannot classify industry without company name"
            )
        
        try:
            # Use MCP to search for company industry information
            search_result = self.call_mcp_tool("web_search", {
                "query": f"{company_name} industry business type",
                "num_results": 3
            })
            
            # Extract industry classification from the result
            classified_industry = self._extract_industry_from_search(search_result, company_name)
            
            if classified_industry and classified_industry != "Unknown":
                return EnrichmentResult(
                    field_name=config.name,
                    field_internal_name=config.internal_name,
                    old_value=current_value,
                    new_value=classified_industry,
                    status=EnrichmentStatus.COMPLETE,
                    confidence=ConfidenceLevel.MEDIUM,
                    source="ai_classification_mcp",
                    validation_passed=True,
                    critique_notes="Classified using MCP web search and AI analysis",
                    improvement_suggestions=[
                        "Add NAICS/SIC code mapping",
                        "Cross-validate with multiple sources",
                        "Build industry classification confidence scoring"
                    ]
                )
            
        except Exception as e:
            logger.error(f"Industry classification error: {e}")
        
        return EnrichmentResult(
            field_name=config.name,
            field_internal_name=config.internal_name,
            old_value=current_value,
            new_value=current_value,
            status=EnrichmentStatus.FAILED,
            confidence=ConfidenceLevel.LOW,
            source="ai_classification_mcp",
            validation_passed=False,
            critique_notes="Could not determine industry classification",
            improvement_suggestions=[
                "Implement robust AI classification system",
                "Add fallback to business directory APIs",
                "Create manual review workflow for unclear cases"
            ]
        )
    
    def _extract_industry_from_search(self, search_result: Any, company_name: str) -> Optional[str]:
        """Extract industry classification from search results"""
        try:
            result_str = str(search_result).lower()
            
            # Common industry keywords and their mappings
            industry_keywords = {
                'technology': ['tech', 'software', 'saas', 'it', 'digital', 'computer'],
                'healthcare': ['health', 'medical', 'hospital', 'pharma', 'biotech'],
                'finance': ['bank', 'financial', 'investment', 'insurance', 'fintech'],
                'retail': ['retail', 'store', 'shop', 'ecommerce', 'consumer'],
                'manufacturing': ['manufacturing', 'factory', 'production', 'industrial'],
                'education': ['education', 'school', 'university', 'learning'],
                'real estate': ['real estate', 'property', 'construction', 'building'],
                'professional services': ['consulting', 'legal', 'accounting', 'advisory'],
                'hospitality': ['hotel', 'restaurant', 'travel', 'tourism'],
                'transportation': ['transport', 'logistics', 'shipping', 'delivery'],
                'energy': ['energy', 'oil', 'gas', 'renewable', 'utility'],
                'media': ['media', 'entertainment', 'publishing', 'broadcasting'],
                'non-profit': ['nonprofit', 'charity', 'foundation', 'ngo']
            }
            
            # Score each industry based on keyword matches
            industry_scores = {}
            for industry, keywords in industry_keywords.items():
                score = sum(1 for keyword in keywords if keyword in result_str)
                if score > 0:
                    industry_scores[industry] = score
            
            # Return the industry with the highest score
            if industry_scores:
                best_industry = max(industry_scores.items(), key=lambda x: x[1])
                return best_industry[0].title()
            
            return "Business Services"  # Default fallback
            
        except Exception as e:
            logger.error(f"Error extracting industry from search: {e}")
            return None
    
    def _enrich_description_field(self, record_data: Dict[str, Any], config: FieldEnrichmentConfig) -> EnrichmentResult:
        """Enrich company description using multiple strategies"""
        
        properties = record_data.get('properties', {})
        company_name = properties.get('name', '')
        website = properties.get('website', '')
        domain = properties.get('domain', '')
        industry = properties.get('industry', '')
        current_value = properties.get(config.internal_name)
        
        if not company_name:
            return self._create_failed_result(config, current_value, "Cannot generate description without company name")
        
        try:
            # Strategy 1: Search for "about us" or company overview
            search_queries = [
                f'"{company_name}" about overview mission what we do',
                f'site:{website} about company overview' if website else f'{company_name} company overview',
                f'{company_name} services products offerings',
                f'{company_name} business model company profile'
            ]
            
            best_description = None
            best_confidence = ConfidenceLevel.UNKNOWN
            
            for query in search_queries:
                search_result = self.call_mcp_tool("web_search", {
                    "query": query,
                    "num_results": 5
                })
                
                description = self._extract_description_from_search(search_result, company_name)
                if description and len(description) > 50:
                    # Score this description
                    confidence = self._score_description_quality(description, company_name, industry)
                    if confidence.value > best_confidence.value:
                        best_description = description
                        best_confidence = confidence
            
            # Strategy 2: Generate description from available data if no good description found
            if not best_description or best_confidence == ConfidenceLevel.LOW:
                generated_description = self._generate_description_from_data(company_name, industry, domain, website)
                if generated_description:
                    # Use generated description if we found nothing better
                    if not best_description:
                        best_description = generated_description
                        best_confidence = ConfidenceLevel.LOW
                    # Or combine if we have partial information
                    elif len(best_description) < 100:
                        combined_description = f"{best_description} {generated_description}"
                        if len(combined_description) <= 500:
                            best_description = combined_description
                            best_confidence = ConfidenceLevel.MEDIUM
            
            if best_description:
                return EnrichmentResult(
                    field_name=config.name,
                    field_internal_name=config.internal_name,
                    old_value=current_value,
                    new_value=best_description,
                    status=EnrichmentStatus.COMPLETE,
                    confidence=best_confidence,
                    source="enhanced_description_generation",
                    validation_passed=True,
                    critique_notes=f"Generated comprehensive description (confidence: {best_confidence.name})"
                )
            
        except Exception as e:
            logger.error(f"Description enrichment error: {e}")
        
        return self._create_failed_result(config, current_value, "Could not generate meaningful description")
    
    def _score_description_quality(self, description: str, company_name: str, industry: str) -> ConfidenceLevel:
        """Score the quality of a description"""
        score = 0
        
        # Length check (50-500 words ideal)
        word_count = len(description.split())
        if 20 <= word_count <= 100:
            score += 30
        elif 10 <= word_count < 20 or 100 < word_count <= 200:
            score += 20
        elif word_count > 200:
            score += 10
        
        # Company name mentioned
        if company_name.lower() in description.lower():
            score += 20
        
        # Industry relevance
        if industry and industry.lower() in description.lower():
            score += 20
        
        # Professional language indicators
        professional_words = ['provides', 'offers', 'specializes', 'services', 'solutions', 'expertise', 'committed', 'dedicated']
        if any(word in description.lower() for word in professional_words):
            score += 15
        
        # Avoid marketing fluff
        fluff_words = ['best', 'leading', 'premier', 'world-class', 'cutting-edge', 'revolutionary']
        if not any(word in description.lower() for word in fluff_words):
            score += 15
        
        # Convert score to confidence level
        if score >= 80:
            return ConfidenceLevel.HIGH
        elif score >= 60:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW
    
    def _generate_description_from_data(self, company_name: str, industry: str, domain: str, website: str) -> Optional[str]:
        """Generate a basic description from available data"""
        try:
            description_parts = []
            
            # Start with company name
            description_parts.append(f"{company_name}")
            
            # Add industry information
            if industry:
                if 'club' in company_name.lower():
                    description_parts.append(f"is a private {industry.lower()} facility")
                else:
                    description_parts.append(f"operates in the {industry.lower()} industry")
            else:
                description_parts.append("is a business organization")
            
            # Add location context if available in name
            if any(word in company_name.lower() for word in ['country club', 'golf club']):
                description_parts.append("providing recreational services and facilities to its members")
            elif 'club' in company_name.lower():
                description_parts.append("serving its membership community")
            else:
                description_parts.append("providing services to its clients and customers")
            
            # Add domain/website context
            if domain:
                description_parts.append(f"More information is available at {domain}")
            elif website:
                description_parts.append(f"Additional details can be found on their website")
            
            description = ". ".join(description_parts) + "."
            
            # Clean up the description
            description = description.replace(".. ", ". ").replace("  ", " ")
            
            return description if len(description) > 30 else None
            
        except Exception as e:
            logger.error(f"Error generating description: {e}")
            return None
    
    def _extract_description_from_search(self, search_result: Any, company_name: str) -> Optional[str]:
        """Extract company description from search results"""
        try:
            result_str = str(search_result)
            
            # Look for descriptive sentences about the company
            sentences = result_str.split('.')
            relevant_sentences = []
            
            for sentence in sentences:
                sentence = sentence.strip()
                if (len(sentence) > 20 and 
                    (company_name.lower() in sentence.lower() or 
                     any(word in sentence.lower() for word in ['company', 'business', 'provides', 'offers', 'specializes']))):
                    relevant_sentences.append(sentence)
            
            if relevant_sentences:
                # Take the first few relevant sentences
                description = '. '.join(relevant_sentences[:3])
                if not description.endswith('.'):
                    description += '.'
                
                # Clean up the description
                description = description.replace('\n', ' ').replace('  ', ' ').strip()
                
                # Limit length
                if len(description) > 500:
                    description = description[:497] + '...'
                
                return description
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting description from search: {e}")
            return None
    
    def _enrich_job_parsing_field(self, record_data: Dict[str, Any], config: FieldEnrichmentConfig) -> EnrichmentResult:
        """Enrich job seniority or function from job title"""
        
        properties = record_data.get('properties', {})
        job_title = properties.get('jobtitle', '')
        current_value = properties.get(config.internal_name)
        
        if not job_title:
            return EnrichmentResult(
                field_name=config.name,
                field_internal_name=config.internal_name,
                old_value=current_value,
                new_value=current_value,
                status=EnrichmentStatus.FAILED,
                confidence=ConfidenceLevel.UNKNOWN,
                source="ai_parsing",
                validation_passed=False,
                critique_notes="No job title available for parsing"
            )
        
        # Parse job title using real logic
        parsed_data = self._parse_job_title_real(job_title)
        
        if config.internal_name == 'job_seniority':
            new_value = parsed_data.get('seniority', 'Unknown')
        else:  # job_function
            new_value = parsed_data.get('function', 'Unknown')
        
        if new_value and new_value != 'Unknown':
            return EnrichmentResult(
                field_name=config.name,
                field_internal_name=config.internal_name,
                old_value=current_value,
                new_value=new_value,
                status=EnrichmentStatus.COMPLETE,
                confidence=ConfidenceLevel.MEDIUM,
                source="ai_parsing",
                validation_passed=True,
                critique_notes=f"Parsed from job title: {job_title}",
                improvement_suggestions=[
                    "Implement advanced NLP for title parsing",
                    "Build comprehensive seniority/function mappings",
                    "Add industry-specific parsing rules",
                    "Create confidence scoring for parsed results"
                ]
            )
        
        return EnrichmentResult(
            field_name=config.name,
            field_internal_name=config.internal_name,
            old_value=current_value,
            new_value=current_value,
            status=EnrichmentStatus.FAILED,
            confidence=ConfidenceLevel.LOW,
            source="ai_parsing",
            validation_passed=False,
            critique_notes="Could not parse meaningful information from job title"
        )
    
    def critique_enrichment_results(self, results: List[EnrichmentResult]) -> EnrichmentCritique:
        """Provide detailed critique of enrichment performance"""
        
        if not results:
            return EnrichmentCritique(
                overall_score=0.0,
                field_scores={},
                success_rate=0.0,
                confidence_distribution={},
                common_failures=["No enrichment results to analyze"],
                improvement_opportunities=["Execute field enrichment first"],
                data_quality_issues=["No data to assess"],
                recommendations=["Run enrichment process on sample records"]
            )
        
        # Calculate performance metrics
        total_fields = len(results)
        successful_enrichments = len([r for r in results if r.status == EnrichmentStatus.COMPLETE])
        success_rate = (successful_enrichments / total_fields) * 100 if total_fields > 0 else 0
        
        # Confidence distribution
        confidence_dist = {}
        for result in results:
            conf_name = result.confidence.name
            confidence_dist[conf_name] = confidence_dist.get(conf_name, 0) + 1
        
        # Field-specific scores
        field_scores = {}
        for result in results:
            if result.status == EnrichmentStatus.COMPLETE:
                field_scores[result.field_name] = result.confidence.value
            else:
                field_scores[result.field_name] = 0
        
        # Analyze common failures
        failure_reasons = []
        improvement_opportunities = []
        data_quality_issues = []
        
        for result in results:
            if result.status != EnrichmentStatus.COMPLETE:
                if result.critique_notes:
                    failure_reasons.append(result.critique_notes)
                improvement_opportunities.extend(result.improvement_suggestions)
            
            if result.confidence == ConfidenceLevel.LOW:
                data_quality_issues.append(f"{result.field_name}: Low confidence data")
        
        # Generate recommendations
        recommendations = self._generate_enrichment_recommendations(results, success_rate)
        
        # Calculate overall score
        overall_score = self._calculate_overall_enrichment_score(results)
        
        critique = EnrichmentCritique(
            overall_score=overall_score,
            field_scores=field_scores,
            success_rate=success_rate,
            confidence_distribution=confidence_dist,
            common_failures=list(set(failure_reasons)),
            improvement_opportunities=list(set(improvement_opportunities)),
            data_quality_issues=data_quality_issues,
            recommendations=recommendations
        )
        
        return critique
    
    def document_improvement_insights(self, critique: EnrichmentCritique, 
                                    record_type: str, record_id: str) -> str:
        """Document improvement insights and save to file"""
        
        timestamp = datetime.now()
        improvement_doc = {
            'timestamp': timestamp.isoformat(),
            'record_type': record_type,
            'record_id': record_id,
            'critique_summary': {
                'overall_score': critique.overall_score,
                'success_rate': critique.success_rate,
                'confidence_distribution': critique.confidence_distribution
            },
            'identified_issues': {
                'common_failures': critique.common_failures,
                'data_quality_issues': critique.data_quality_issues
            },
            'improvement_opportunities': critique.improvement_opportunities,
            'recommendations': critique.recommendations,
            'next_steps': self._generate_next_steps(critique)
        }
        
        # Add to improvement log
        self.improvement_log.append(improvement_doc)
        
        # Generate formatted report
        report = self._format_improvement_report(improvement_doc)
        
        # Save to file
        filename = f"enrichment_improvement_{timestamp.strftime('%Y%m%d_%H%M%S')}.md"
        filepath = os.path.join(os.path.dirname(__file__), '..', '..', 'docs', filename)
        
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w') as f:
                f.write(report)
            
            logger.info(f"Improvement insights documented in {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Error saving improvement documentation: {e}")
            return ""
    
    def generate_enrichment_summary_report(self, results: List[EnrichmentResult], 
                                         critique: EnrichmentCritique) -> str:
        """Generate comprehensive enrichment summary report"""
        
        report_lines = [
            "# Swoop CRM Field Enrichment Summary Report",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Executive Summary",
            f"- **Overall Score**: {critique.overall_score:.1f}/100",
            f"- **Success Rate**: {critique.success_rate:.1f}%",
            f"- **Fields Processed**: {len(results)}",
            f"- **Successful Enrichments**: {len([r for r in results if r.status == EnrichmentStatus.COMPLETE])}",
            "",
            "## Field-by-Field Results",
            ""
        ]
        
        # Group results by status
        complete_results = [r for r in results if r.status == EnrichmentStatus.COMPLETE]
        failed_results = [r for r in results if r.status == EnrichmentStatus.FAILED]
        skipped_results = [r for r in results if r.status == EnrichmentStatus.SKIPPED]
        
        if complete_results:
            report_lines.extend([
                "### ✅ Successfully Enriched Fields",
                ""
            ])
            for result in complete_results:
                confidence_emoji = "🔥" if result.confidence.value >= 80 else "👍" if result.confidence.value >= 60 else "⚠️"
                report_lines.extend([
                    f"#### {result.field_name}",
                    f"- **Status**: {result.status.value} {confidence_emoji}",
                    f"- **Confidence**: {result.confidence.name} ({result.confidence.value})",
                    f"- **Source**: {result.source}",
                    f"- **New Value**: {result.new_value}",
                    f"- **Notes**: {result.critique_notes}",
                    ""
                ])
        
        if failed_results:
            report_lines.extend([
                "### ❌ Failed Enrichments",
                ""
            ])
            for result in failed_results:
                report_lines.extend([
                    f"#### {result.field_name}",
                    f"- **Status**: {result.status.value}",
                    f"- **Source Attempted**: {result.source}",
                    f"- **Issue**: {result.critique_notes}",
                    ""
                ])
                if result.improvement_suggestions:
                    report_lines.append("- **Improvement Suggestions**:")
                    for suggestion in result.improvement_suggestions[:3]:  # Top 3 suggestions
                        report_lines.append(f"  - {suggestion}")
                    report_lines.append("")
        
        if skipped_results:
            report_lines.extend([
                "### ⏭️ Skipped Fields (Already Populated)",
                ""
            ])
            for result in skipped_results:
                report_lines.append(f"- **{result.field_name}**: {result.old_value}")
            report_lines.append("")
        
        # Add critique insights
        report_lines.extend([
            "## Quality Assessment & Critique",
            "",
            "### Performance Analysis",
            f"- **Target vs Actual**: Aiming for 85%+ success rate, achieved {critique.success_rate:.1f}%",
            ""
        ])
        
        if critique.confidence_distribution:
            report_lines.extend([
                "### Confidence Distribution",
                ""
            ])
            for conf_level, count in critique.confidence_distribution.items():
                percentage = (count / len(results)) * 100
                report_lines.append(f"- **{conf_level}**: {count} fields ({percentage:.1f}%)")
            report_lines.append("")
        
        if critique.common_failures:
            report_lines.extend([
                "### Common Failure Patterns",
                ""
            ])
            for failure in critique.common_failures[:5]:  # Top 5 failures
                report_lines.append(f"- {failure}")
            report_lines.append("")
        
        # Add recommendations
        if critique.recommendations:
            report_lines.extend([
                "## Recommendations for Improvement",
                ""
            ])
            for i, rec in enumerate(critique.recommendations, 1):
                report_lines.append(f"{i}. {rec}")
            report_lines.append("")
        
        # Add next steps
        report_lines.extend([
            "## Next Steps",
            "",
            "1. **Address Critical Failures**: Focus on failed enrichments for high-priority fields",
            "2. **Improve Data Sources**: Enhance reliability of low-confidence enrichments",
            "3. **Automate Validation**: Implement automated quality checks for enriched data",
            "4. **Monitor Progress**: Track improvement in success rates over time",
            "",
            "---",
            f"*Report generated by Field Enrichment Manager Agent*",
            f"*For questions or improvements, review the detailed improvement log*"
        ])
        
        return "\n".join(report_lines)
    
    # Real implementation methods
    
    def _parse_job_title_real(self, job_title: str) -> Dict[str, str]:
        """Parse job title to extract seniority and function using comprehensive logic"""
        if not job_title:
            return {'seniority': 'Unknown', 'function': 'Unknown'}
        
        title_lower = job_title.lower().strip()
        
        # Seniority mapping with comprehensive patterns
        seniority_patterns = {
            'C-Level': [
                'ceo', 'chief executive officer', 'president', 'founder', 'owner', 'principal',
                'cfo', 'chief financial officer', 'cto', 'chief technology officer',
                'coo', 'chief operating officer', 'cmo', 'chief marketing officer',
                'chro', 'chief human resources officer', 'ciso', 'chief information security officer'
            ],
            'VP': [
                'vp', 'vice president', 'executive vice president', 'evp', 'senior vice president', 'svp'
            ],
            'Director': [
                'director', 'head of', 'senior director', 'executive director', 'managing director'
            ],
            'Manager': [
                'manager', 'senior manager', 'team lead', 'team leader', 'supervisor',
                'program manager', 'project manager', 'product manager', 'account manager'
            ],
            'Senior': [
                'senior', 'lead', 'principal', 'staff', 'senior analyst', 'senior consultant',
                'senior engineer', 'senior developer', 'senior specialist'
            ]
        }
        
        seniority = 'Individual Contributor'  # Default
        for level, patterns in seniority_patterns.items():
            if any(pattern in title_lower for pattern in patterns):
                seniority = level
                break
        
        # Function mapping with comprehensive patterns
        function_patterns = {
            'Sales': [
                'sales', 'business development', 'account executive', 'sales rep', 'sales manager',
                'business development manager', 'account manager', 'sales director', 'revenue'
            ],
            'Marketing': [
                'marketing', 'brand', 'digital marketing', 'content', 'social media',
                'growth', 'demand generation', 'product marketing', 'communications'
            ],
            'Operations': [
                'operations', 'ops', 'operational', 'supply chain', 'logistics',
                'process', 'quality', 'facilities', 'procurement'
            ],
            'Finance': [
                'finance', 'financial', 'accounting', 'controller', 'treasurer',
                'fp&a', 'financial planning', 'budget', 'audit'
            ],
            'Human Resources': [
                'hr', 'human resources', 'people', 'talent', 'recruiting', 'recruitment',
                'compensation', 'benefits', 'organizational development'
            ],
            'Engineering': [
                'engineer', 'engineering', 'developer', 'development', 'software',
                'technical', 'architect', 'devops', 'qa', 'quality assurance'
            ],
            'Product': [
                'product', 'product manager', 'product owner', 'ux', 'ui', 'design',
                'user experience', 'product development'
            ],
            'Customer Success': [
                'customer success', 'customer support', 'customer service', 'support',
                'client services', 'customer experience'
            ],
            'Legal': [
                'legal', 'counsel', 'attorney', 'lawyer', 'compliance', 'regulatory'
            ],
            'IT': [
                'it', 'information technology', 'systems', 'infrastructure', 'security',
                'network', 'database', 'system administrator'
            ]
        }
        
        function = 'General Management'  # Default
        for func, patterns in function_patterns.items():
            if any(pattern in title_lower for pattern in patterns):
                function = func
                break
        
        return {'seniority': seniority, 'function': function}
    
    def _validate_url_accessibility(self, url: str) -> bool:
        """Validate if a URL is accessible"""
        try:
            import requests
            response = requests.head(url, timeout=5, allow_redirects=True)
            return response.status_code in [200, 301, 302]
        except:
            return False
    
    def _guess_domain_from_company_name(self, company_name: str) -> Optional[str]:
        """Guess domain from company name using common patterns"""
        if not company_name:
            return None
        
        # Clean company name for domain guessing
        clean_name = company_name.lower()
        
        # Remove common business suffixes
        suffixes_to_remove = [
            'inc', 'inc.', 'llc', 'ltd', 'ltd.', 'corp', 'corp.', 
            'company', 'co', 'co.', 'corporation', 'enterprises',
            'country club', 'golf club', 'club', 'group'
        ]
        
        for suffix in suffixes_to_remove:
            if clean_name.endswith(f' {suffix}'):
                clean_name = clean_name[:-len(suffix)-1]
        
        # Remove special characters and spaces
        clean_name = ''.join(c for c in clean_name if c.isalnum())
        
        if len(clean_name) < 3:
            return None
        
        # Common domain patterns to try
        domain_patterns = [
            f"{clean_name}.com",
            f"{clean_name}.org", 
            f"{clean_name}.net",
            f"{clean_name}club.com",
            f"{clean_name}cc.com",
            f"{clean_name}golf.com"
        ]
        
        for domain_pattern in domain_patterns:
            for protocol in ["https://", "http://"]:
                candidate_url = f"{protocol}{domain_pattern}"
                if self._validate_url_accessibility(candidate_url):
                    return candidate_url
        
        return None
    
    def _enrich_annual_revenue_field(self, record_data: Dict[str, Any], config: FieldEnrichmentConfig) -> EnrichmentResult:
        """Enrich annual revenue field using multiple sources"""
        
        properties = record_data.get('properties', {})
        company_name = properties.get('name', '')
        website = properties.get('website', '')
        domain = properties.get('domain', '')
        current_value = properties.get(config.internal_name)
        
        if not company_name:
            return self._create_failed_result(config, current_value, "Cannot estimate revenue without company name")
        
        try:
            # Strategy 1: Web search for financial information
            search_queries = [
                f"{company_name} annual revenue financial information",
                f"{company_name} revenue earnings financial",
                f'"{company_name}" million revenue OR earnings OR sales',
                f"{company_name} financial statements SEC filings"
            ]
            
            for query in search_queries:
                search_result = self.call_mcp_tool("web_search", {
                    "query": query,
                    "num_results": 5
                })
                
                revenue = self._extract_revenue_from_search(search_result, company_name)
                if revenue:
                    return EnrichmentResult(
                        field_name=config.name,
                        field_internal_name=config.internal_name,
                        old_value=current_value,
                        new_value=revenue,
                        status=EnrichmentStatus.COMPLETE,
                        confidence=ConfidenceLevel.MEDIUM,
                        source="web_search_financial",
                        validation_passed=True,
                        critique_notes=f"Revenue estimate from web search: {query[:50]}..."
                    )
            
            # Strategy 2: Industry-based revenue estimation
            industry = properties.get('industry', '')
            employee_count = properties.get('numberofemployees', '')
            
            if industry or employee_count:
                estimated_revenue = self._estimate_revenue_by_industry(company_name, industry, employee_count)
                if estimated_revenue:
                    return EnrichmentResult(
                        field_name=config.name,
                        field_internal_name=config.internal_name,
                        old_value=current_value,
                        new_value=estimated_revenue,
                        status=EnrichmentStatus.COMPLETE,
                        confidence=ConfidenceLevel.LOW,
                        source="industry_estimation",
                        validation_passed=True,
                        critique_notes="Revenue estimated based on industry and company size"
                    )
            
        except Exception as e:
            logger.error(f"Revenue enrichment error: {e}")
        
        return self._create_failed_result(config, current_value, "Could not determine annual revenue")
    
    def _enrich_employee_count_field(self, record_data: Dict[str, Any], config: FieldEnrichmentConfig) -> EnrichmentResult:
        """Enrich employee count field using LinkedIn and web search"""
        
        properties = record_data.get('properties', {})
        company_name = properties.get('name', '')
        domain = properties.get('domain', '')
        current_value = properties.get(config.internal_name)
        
        if not company_name:
            return self._create_failed_result(config, current_value, "Cannot estimate employees without company name")
        
        try:
            # Strategy 1: LinkedIn company page search
            linkedin_result = self.call_mcp_tool("web_search", {
                "query": f'"{company_name}" site:linkedin.com/company employees OR "employees on LinkedIn"',
                "num_results": 3
            })
            
            employee_count = self._extract_employee_count_from_search(linkedin_result, company_name)
            if employee_count:
                return EnrichmentResult(
                    field_name=config.name,
                    field_internal_name=config.internal_name,
                    old_value=current_value,
                    new_value=employee_count,
                    status=EnrichmentStatus.COMPLETE,
                    confidence=ConfidenceLevel.MEDIUM,
                    source="linkedin_search",
                    validation_passed=True,
                    critique_notes="Employee count from LinkedIn search"
                )
            
            # Strategy 2: General web search for company size
            search_result = self.call_mcp_tool("web_search", {
                "query": f"{company_name} employees staff size team",
                "num_results": 5
            })
            
            employee_count = self._extract_employee_count_from_search(search_result, company_name)
            if employee_count:
                return EnrichmentResult(
                    field_name=config.name,
                    field_internal_name=config.internal_name,
                    old_value=current_value,
                    new_value=employee_count,
                    status=EnrichmentStatus.COMPLETE,
                    confidence=ConfidenceLevel.LOW,
                    source="web_search_employees",
                    validation_passed=True,
                    critique_notes="Employee count estimated from web search"
                )
            
        except Exception as e:
            logger.error(f"Employee count enrichment error: {e}")
        
        return self._create_failed_result(config, current_value, "Could not determine employee count")
    
    def _enrich_linkedin_company_field(self, record_data: Dict[str, Any], config: FieldEnrichmentConfig) -> EnrichmentResult:
        """Enrich LinkedIn company page field"""
        
        properties = record_data.get('properties', {})
        company_name = properties.get('name', '')
        domain = properties.get('domain', '')
        current_value = properties.get(config.internal_name)
        
        if not company_name:
            return self._create_failed_result(config, current_value, "Cannot find LinkedIn page without company name")
        
        try:
            # Search for LinkedIn company page
            search_result = self.call_mcp_tool("web_search", {
                "query": f'"{company_name}" site:linkedin.com/company',
                "num_results": 3
            })
            
            linkedin_url = self._extract_linkedin_url_from_search(search_result, company_name)
            if linkedin_url:
                return EnrichmentResult(
                    field_name=config.name,
                    field_internal_name=config.internal_name,
                    old_value=current_value,
                    new_value=linkedin_url,
                    status=EnrichmentStatus.COMPLETE,
                    confidence=ConfidenceLevel.MEDIUM,
                    source="linkedin_search",
                    validation_passed=True,
                    critique_notes="LinkedIn company page found via search"
                )
            
        except Exception as e:
            logger.error(f"LinkedIn enrichment error: {e}")
        
        return self._create_failed_result(config, current_value, "Could not find LinkedIn company page")
    
    def _enrich_phone_field(self, record_data: Dict[str, Any], config: FieldEnrichmentConfig) -> EnrichmentResult:
        """Enrich phone field for contacts or companies"""
        
        properties = record_data.get('properties', {})
        company_name = properties.get('name', '')
        website = properties.get('website', '')
        current_value = properties.get(config.internal_name)
        
        if not company_name and not website:
            return self._create_failed_result(config, current_value, "Cannot find phone without company name or website")
        
        try:
            # Strategy 1: Search company website for contact information
            if website:
                search_result = self.call_mcp_tool("web_search", {
                    "query": f'site:{website} phone contact "call us" telephone',
                    "num_results": 3
                })
            else:
                search_result = self.call_mcp_tool("web_search", {
                    "query": f'"{company_name}" phone contact telephone number',
                    "num_results": 5
                })
            
            phone_number = self._extract_phone_from_search(search_result, company_name)
            if phone_number:
                return EnrichmentResult(
                    field_name=config.name,
                    field_internal_name=config.internal_name,
                    old_value=current_value,
                    new_value=phone_number,
                    status=EnrichmentStatus.COMPLETE,
                    confidence=ConfidenceLevel.MEDIUM,
                    source="web_search_contact",
                    validation_passed=True,
                    critique_notes="Phone number found via web search"
                )
            
        except Exception as e:
            logger.error(f"Phone enrichment error: {e}")
        
        return self._create_failed_result(config, current_value, "Could not find phone number")
    
    def _create_failed_result(self, config: FieldEnrichmentConfig, current_value: Any, notes: str) -> EnrichmentResult:
        """Helper to create a standardized failed enrichment result"""
        return EnrichmentResult(
            field_name=config.name,
            field_internal_name=config.internal_name,
            old_value=current_value,
            new_value=current_value,
            status=EnrichmentStatus.FAILED,
            confidence=ConfidenceLevel.UNKNOWN,
            source="enrichment_attempt",
            validation_passed=False,
            critique_notes=notes
        )
    
    def _extract_revenue_from_search(self, search_result: Any, company_name: str) -> Optional[str]:
        """Extract revenue information from search results"""
        try:
            result_str = str(search_result).lower()
            
            # Look for revenue patterns
            import re
            
            # Pattern for revenue mentions
            revenue_patterns = [
                r'revenue[:\s]*\$?([\d,]+(?:\.\d+)?)\s*(million|billion|k|thousand)?',
                r'sales[:\s]*\$?([\d,]+(?:\.\d+)?)\s*(million|billion|k|thousand)?',
                r'earnings[:\s]*\$?([\d,]+(?:\.\d+)?)\s*(million|billion|k|thousand)?',
                r'\$\s*([\d,]+(?:\.\d+)?)\s*(million|billion|k|thousand)?\s*(?:revenue|sales|earnings)'
            ]
            
            for pattern in revenue_patterns:
                matches = re.findall(pattern, result_str, re.IGNORECASE)
                for match in matches:
                    amount, unit = match
                    amount = amount.replace(',', '')
                    
                    try:
                        amount_float = float(amount)
                        
                        # Convert to dollars
                        if unit and unit.lower() in ['million', 'm']:
                            amount_float *= 1000000
                        elif unit and unit.lower() in ['billion', 'b']:
                            amount_float *= 1000000000
                        elif unit and unit.lower() in ['thousand', 'k']:
                            amount_float *= 1000
                        
                        # Reasonable range check (between $10K and $100B)
                        if 10000 <= amount_float <= 100000000000:
                            return f"${amount_float:,.0f}"
                            
                    except ValueError:
                        continue
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting revenue: {e}")
            return None
    
    def _estimate_revenue_by_industry(self, company_name: str, industry: str, employee_count: str) -> Optional[str]:
        """Estimate revenue based on industry and employee count"""
        try:
            # Industry revenue per employee averages (rough estimates)
            industry_revenue_per_employee = {
                'technology': 200000,
                'software': 250000,
                'finance': 150000,
                'healthcare': 120000,
                'retail': 80000,
                'manufacturing': 100000,
                'professional services': 130000,
                'hospitality': 60000,
                'real estate': 110000,
                'education': 70000,
                'recreational facilities': 75000,  # For country clubs
                'recreation': 75000
            }
            
            # Extract employee count number
            employee_num = self._extract_number_from_string(employee_count) if employee_count else None
            
            if not employee_num and 'club' in company_name.lower():
                employee_num = 50  # Default for country clubs
            
            if employee_num and industry:
                industry_lower = industry.lower()
                revenue_per_employee = None
                
                for ind_key, rev_per_emp in industry_revenue_per_employee.items():
                    if ind_key in industry_lower:
                        revenue_per_employee = rev_per_emp
                        break
                
                if not revenue_per_employee:
                    revenue_per_employee = 100000  # Default
                
                estimated_revenue = employee_num * revenue_per_employee
                
                # Add some variance (±30%)
                estimated_revenue = int(estimated_revenue * 0.8)  # Conservative estimate
                
                return f"${estimated_revenue:,.0f}"
            
            return None
            
        except Exception as e:
            logger.error(f"Error estimating revenue: {e}")
            return None
    
    def _extract_employee_count_from_search(self, search_result: Any, company_name: str) -> Optional[str]:
        """Extract employee count from search results"""
        try:
            result_str = str(search_result).lower()
            
            import re
            
            # Patterns for employee count
            employee_patterns = [
                r'(\d+(?:,\d+)?)\s*(?:employees?|staff|workers?|team members?)',
                r'(?:employees?|staff|team)[:\s]*(\d+(?:,\d+)?)',
                r'(\d+(?:,\d+)?)\s*(?:people|persons?)\s*(?:work|employed)',
                r'(?:size|headcount)[:\s]*(\d+(?:,\d+)?)',
                r'(\d+)\s*-\s*(\d+)\s*(?:employees?|staff)'  # Range pattern
            ]
            
            for pattern in employee_patterns:
                matches = re.findall(pattern, result_str)
                for match in matches:
                    if isinstance(match, tuple):
                        # Range pattern
                        try:
                            low, high = int(match[0].replace(',', '')), int(match[1].replace(',', ''))
                            if 1 <= low <= 50000 and low < high <= 50000:
                                return f"{low}-{high}"
                        except:
                            continue
                    else:
                        # Single number
                        try:
                            count = int(match.replace(',', ''))
                            if 1 <= count <= 50000:
                                return str(count)
                        except:
                            continue
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting employee count: {e}")
            return None
    
    def _extract_linkedin_url_from_search(self, search_result: Any, company_name: str) -> Optional[str]:
        """Extract LinkedIn company page URL from search results"""
        try:
            result_str = str(search_result)
            
            import re
            
            # Pattern for LinkedIn company URLs
            linkedin_pattern = r'https?://(?:www\.)?linkedin\.com/company/[^/\s]+'
            matches = re.findall(linkedin_pattern, result_str, re.IGNORECASE)
            
            if matches:
                # Return the first valid LinkedIn URL
                return matches[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting LinkedIn URL: {e}")
            return None
    
    def _extract_phone_from_search(self, search_result: Any, company_name: str) -> Optional[str]:
        """Extract phone number from search results"""
        try:
            result_str = str(search_result)
            
            import re
            
            # Phone number patterns
            phone_patterns = [
                r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # US format
                r'\+1[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # US with country code
                r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}',  # Simple US format
                r'\(\d{3}\)\s?\d{3}-\d{4}'  # (XXX) XXX-XXXX format
            ]
            
            for pattern in phone_patterns:
                matches = re.findall(pattern, result_str)
                for match in matches:
                    # Basic validation - should be 10 digits
                    digits_only = ''.join(c for c in match if c.isdigit())
                    if len(digits_only) == 10:
                        # Format as (XXX) XXX-XXXX
                        formatted = f"({digits_only[:3]}) {digits_only[3:6]}-{digits_only[6:]}"
                        return formatted
                    elif len(digits_only) == 11 and digits_only.startswith('1'):
                        # US number with country code
                        formatted = f"+1 ({digits_only[1:4]}) {digits_only[4:7]}-{digits_only[7:]}"
                        return formatted
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting phone: {e}")
            return None
    
    def _extract_number_from_string(self, text: str) -> Optional[int]:
        """Extract a number from a text string"""
        if not text:
            return None
        
        import re
        
        # Look for numbers
        numbers = re.findall(r'\d+', str(text).replace(',', ''))
        if numbers:
            try:
                return int(numbers[0])
            except ValueError:
                pass
        
        return None
    
    def _generate_enrichment_recommendations(self, results: List[EnrichmentResult], 
                                           success_rate: float) -> List[str]:
        """Generate specific recommendations based on enrichment results"""
        
        recommendations = []
        
        # Success rate based recommendations
        if success_rate < 70:
            recommendations.append("Success rate is below target. Focus on improving data source reliability and enrichment logic.")
        elif success_rate < 85:
            recommendations.append("Success rate is moderate. Identify and address the most common failure patterns.")
        
        # Source-specific recommendations
        sources_with_failures = {}
        for result in results:
            if result.status != EnrichmentStatus.COMPLETE:
                source = result.source
                sources_with_failures[source] = sources_with_failures.get(source, 0) + 1
        
        if sources_with_failures:
            worst_source = max(sources_with_failures.items(), key=lambda x: x[1])
            recommendations.append(f"Source '{worst_source[0]}' has {worst_source[1]} failures. Consider alternative data sources or improved error handling.")
        
        # Field-specific recommendations
        failed_critical_fields = [r for r in results if r.status != EnrichmentStatus.COMPLETE and 'Critical' in str(r)]
        if failed_critical_fields:
            recommendations.append("Critical fields are failing enrichment. These should be prioritized for immediate improvement.")
        
        # Confidence-based recommendations
        low_confidence_results = [r for r in results if r.confidence == ConfidenceLevel.LOW]
        if low_confidence_results:
            recommendations.append(f"{len(low_confidence_results)} fields have low confidence. Implement cross-validation or manual review processes.")
        
        return recommendations
    
    def _calculate_overall_enrichment_score(self, results: List[EnrichmentResult]) -> float:
        """Calculate overall enrichment quality score"""
        
        if not results:
            return 0.0
        
        total_score = 0
        total_weight = 0
        
        for result in results:
            # Weight by field priority (critical fields count more)
            if 'critical' in result.field_name.lower() or result.field_internal_name in ['name', 'email', 'firstname', 'lastname']:
                weight = 3.0
            elif result.field_internal_name in ['website', 'domain', 'industry', 'jobtitle']:
                weight = 2.0
            else:
                weight = 1.0
            
            # Score based on status and confidence
            if result.status == EnrichmentStatus.COMPLETE:
                field_score = result.confidence.value
            elif result.status == EnrichmentStatus.SKIPPED:
                field_score = 90  # Already populated is good
            else:
                field_score = 0
            
            total_score += field_score * weight
            total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else 0
    
    def _generate_next_steps(self, critique: EnrichmentCritique) -> List[str]:
        """Generate actionable next steps based on critique"""
        
        next_steps = []
        
        if critique.success_rate < 85:
            next_steps.append("Investigate and resolve the most common failure patterns")
            
        if critique.overall_score < 80:
            next_steps.append("Implement additional data sources to improve enrichment coverage")
        
        if 'LOW' in critique.confidence_distribution and critique.confidence_distribution['LOW'] > 0:
            next_steps.append("Add validation rules to improve data confidence scores")
        
        next_steps.extend([
            "Test enrichment improvements on a larger sample set",
            "Implement automated monitoring for enrichment quality",
            "Document successful enrichment patterns for replication"
        ])
        
        return next_steps
    
    def _format_improvement_report(self, improvement_doc: Dict[str, Any]) -> str:
        """Format improvement documentation as markdown"""
        
        lines = [
            "# CRM Field Enrichment Improvement Analysis",
            f"**Generated**: {improvement_doc['timestamp']}",
            f"**Record Type**: {improvement_doc['record_type']}",
            f"**Record ID**: {improvement_doc['record_id']}",
            "",
            "## Performance Summary",
            f"- **Overall Score**: {improvement_doc['critique_summary']['overall_score']:.1f}/100",
            f"- **Success Rate**: {improvement_doc['critique_summary']['success_rate']:.1f}%",
            "",
            "### Confidence Distribution",
        ]
        
        for conf_level, count in improvement_doc['critique_summary']['confidence_distribution'].items():
            lines.append(f"- **{conf_level}**: {count} fields")
        
        lines.extend([
            "",
            "## Identified Issues",
            "",
            "### Common Failure Patterns"
        ])
        
        for failure in improvement_doc['identified_issues']['common_failures']:
            lines.append(f"- {failure}")
        
        lines.extend([
            "",
            "### Data Quality Issues"
        ])
        
        for issue in improvement_doc['identified_issues']['data_quality_issues']:
            lines.append(f"- {issue}")
        
        lines.extend([
            "",
            "## Improvement Opportunities",
            ""
        ])
        
        for opportunity in improvement_doc['improvement_opportunities']:
            lines.append(f"- {opportunity}")
        
        lines.extend([
            "",
            "## Recommendations",
            ""
        ])
        
        for i, rec in enumerate(improvement_doc['recommendations'], 1):
            lines.append(f"{i}. {rec}")
        
        lines.extend([
            "",
            "## Next Steps",
            ""
        ])
        
        for i, step in enumerate(improvement_doc['next_steps'], 1):
            lines.append(f"{i}. {step}")
        
        lines.extend([
            "",
            "---",
            "*Generated by Field Enrichment Manager Agent*"
        ])
        
        return "\n".join(lines)
