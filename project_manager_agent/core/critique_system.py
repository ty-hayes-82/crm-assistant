"""
Critical Thinking and Critique System for Project Manager Agent

This module provides intelligent critique and validation of CRM agent responses,
enabling the Project Manager to think critically and follow up when needed.
"""

from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
import json
import re


class ResponseQuality(Enum):
    """Quality assessment levels for CRM agent responses"""
    EXCELLENT = "excellent"
    GOOD = "good" 
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    UNACCEPTABLE = "unacceptable"


class CritiqueCategory(Enum):
    """Categories of critique for different aspects"""
    COMPLETENESS = "completeness"
    ACCURACY = "accuracy"
    RELEVANCE = "relevance"
    ACTIONABILITY = "actionability"
    DATA_QUALITY = "data_quality"


@dataclass
class CritiqueResult:
    """Result of critiquing a CRM agent response"""
    overall_quality: ResponseQuality
    score: float  # 0-100
    critiques: List[Dict[str, Any]]
    follow_up_questions: List[str]
    suggested_improvements: List[str]
    needs_follow_up: bool
    confidence: float  # 0-100


class CRMResponseCritic:
    """
    Intelligent critic that evaluates CRM agent responses and generates follow-up actions.
    
    This critic applies domain knowledge about CRM operations to assess whether
    responses meet the project manager's expectations and requirements.
    """
    
    def __init__(self):
        self.response_validators = {
            "company_intelligence": self._validate_company_intelligence_response,
            "contact_intelligence": self._validate_contact_intelligence_response,
            "crm_enrichment": self._validate_enrichment_response,
            "company_management_enrichment": self._validate_management_response,
            "field_enrichment_manager": self._validate_field_enrichment_response
        }
        
        # Expected fields for different agent types
        self.expected_fields = {
            "company_intelligence": [
                "company_name", "domain", "industry", "description", "status"
            ],
            "contact_intelligence": [
                "contact_name", "email", "title", "company", "status"  
            ],
            "crm_enrichment": [
                "enriched_fields", "success_rate", "data_sources"
            ],
            "company_management_enrichment": [
                "management_company", "match_score", "confidence"
            ]
        }
    
    def critique_response(self, agent_type: str, task_description: str, 
                         response: Dict[str, Any], context: Dict[str, Any] = None) -> CritiqueResult:
        """
        Perform comprehensive critique of a CRM agent response.
        
        Args:
            agent_type: Type of CRM agent that provided the response
            task_description: What the agent was asked to do
            response: The agent's response
            context: Additional context about the task
            
        Returns:
            Detailed critique result with quality assessment and follow-up actions
        """
        
        if not response:
            return CritiqueResult(
                overall_quality=ResponseQuality.UNACCEPTABLE,
                score=0,
                critiques=[{"category": "completeness", "issue": "Empty response received"}],
                follow_up_questions=["Why did the agent return an empty response?"],
                suggested_improvements=["Request agent to retry the task"],
                needs_follow_up=True,
                confidence=100
            )
        
        # Check for errors first
        if "error" in response:
            return self._handle_error_response(response, task_description)
        
        # Use specific validator for agent type
        if agent_type in self.response_validators:
            return self.response_validators[agent_type](task_description, response, context)
        else:
            return self._validate_generic_response(task_description, response, context)
    
    def _validate_company_intelligence_response(self, task_description: str, 
                                               response: Dict[str, Any], context: Dict[str, Any]) -> CritiqueResult:
        """Validate company intelligence agent responses"""
        critiques = []
        follow_up_questions = []
        improvements = []
        score = 100
        
        # Check for essential company information - More lenient scoring
        company_name = response.get("company_name") or response.get("name")
        if not company_name:
            critiques.append({
                "category": CritiqueCategory.COMPLETENESS.value,
                "severity": "medium",  # Reduced severity
                "issue": "Missing company name in response"
            })
            follow_up_questions.append("What is the exact company name you analyzed?")
            score -= 15  # Reduced penalty
        
        # Check for domain/website information
        domain = response.get("domain") or response.get("website")
        if not domain and "website" in task_description.lower():
            critiques.append({
                "category": CritiqueCategory.COMPLETENESS.value,
                "severity": "medium", 
                "issue": "Missing domain/website information when requested"
            })
            follow_up_questions.append("What is the company's website or domain?")
            score -= 20
        
        # Check for industry classification - More lenient
        industry = response.get("industry") or response.get("industry_classification")
        if not industry:
            critiques.append({
                "category": CritiqueCategory.COMPLETENESS.value,
                "severity": "low",  # Reduced severity
                "issue": "Missing industry classification"
            })
            follow_up_questions.append("What industry does this company operate in?")
            score -= 8  # Reduced penalty
        
        # Check for company description - More lenient
        description = response.get("description") or response.get("company_description")
        if not description or len(str(description).strip()) < 10:  # More lenient length requirement
            critiques.append({
                "category": CritiqueCategory.COMPLETENESS.value,
                "severity": "low",  # Reduced severity
                "issue": "Missing or insufficient company description"
            })
            follow_up_questions.append("Can you provide a detailed description of what this company does?")
            score -= 8  # Reduced penalty
        
        # Check for data sources and confidence
        if "data_sources" not in response and "source" not in response:
            critiques.append({
                "category": CritiqueCategory.ACCURACY.value,
                "severity": "low",
                "issue": "No data sources mentioned for verification"
            })
            improvements.append("Include data sources used for company analysis")
            score -= 10
        
        # Assess overall quality
        quality = self._score_to_quality(score)
        
        # CRITICAL: Prevent infinite loops - Only follow up if quality is truly unacceptable
        # and we haven't already done multiple follow-ups
        is_follow_up_task = "follow_up" in task_description.lower() or (context and context.get("is_follow_up"))
        follow_up_count = task_description.lower().count("follow-up")
        
        needs_follow_up = (
            quality == ResponseQuality.UNACCEPTABLE and  # Only for truly unacceptable responses
            not is_follow_up_task and  # Don't follow up on follow-ups
            follow_up_count < 2  # Maximum 2 follow-ups
        )
        
        return CritiqueResult(
            overall_quality=quality,
            score=max(0, score),
            critiques=critiques,
            follow_up_questions=follow_up_questions,
            suggested_improvements=improvements,
            needs_follow_up=needs_follow_up,
            confidence=85
        )
    
    def _validate_contact_intelligence_response(self, task_description: str,
                                              response: Dict[str, Any], context: Dict[str, Any]) -> CritiqueResult:
        """Validate contact intelligence agent responses"""
        critiques = []
        follow_up_questions = []
        improvements = []
        score = 100
        
        # Check for essential contact information
        contact_name = response.get("contact_name") or response.get("name")
        if not contact_name:
            critiques.append({
                "category": CritiqueCategory.COMPLETENESS.value,
                "severity": "high",
                "issue": "Missing contact name in response"
            })
            follow_up_questions.append("What is the contact's full name?")
            score -= 25
        
        # Check for email address
        email = response.get("email") or response.get("contact_email")
        if not email and "email" in task_description.lower():
            critiques.append({
                "category": CritiqueCategory.COMPLETENESS.value,
                "severity": "high",
                "issue": "Missing email address when requested"
            })
            follow_up_questions.append("What is the contact's email address?")
            score -= 25
        
        # Validate email format if provided
        if email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            critiques.append({
                "category": CritiqueCategory.ACCURACY.value,
                "severity": "medium",
                "issue": "Invalid email format provided"
            })
            follow_up_questions.append("Can you verify the correct email address format?")
            score -= 20
        
        # Check for job title
        title = response.get("title") or response.get("job_title")
        if not title:
            critiques.append({
                "category": CritiqueCategory.COMPLETENESS.value,
                "severity": "medium",
                "issue": "Missing job title information"
            })
            follow_up_questions.append("What is the contact's job title or role?")
            score -= 15
        
        # Check for company association
        company = response.get("company") or response.get("company_name")
        if not company:
            critiques.append({
                "category": CritiqueCategory.COMPLETENESS.value,
                "severity": "medium",
                "issue": "Missing company association"
            })
            follow_up_questions.append("Which company is this contact associated with?")
            score -= 15
        
        quality = self._score_to_quality(score)
        needs_follow_up = len(follow_up_questions) > 0 or quality in [ResponseQuality.POOR, ResponseQuality.UNACCEPTABLE]
        
        return CritiqueResult(
            overall_quality=quality,
            score=max(0, score),
            critiques=critiques,
            follow_up_questions=follow_up_questions,
            suggested_improvements=improvements,
            needs_follow_up=needs_follow_up,
            confidence=80
        )
    
    def _validate_enrichment_response(self, task_description: str,
                                    response: Dict[str, Any], context: Dict[str, Any]) -> CritiqueResult:
        """Validate CRM enrichment agent responses"""
        critiques = []
        follow_up_questions = []
        improvements = []
        score = 100
        
        # Check for enrichment results
        enriched_fields = response.get("enriched_fields") or response.get("updated_fields")
        if not enriched_fields:
            critiques.append({
                "category": CritiqueCategory.COMPLETENESS.value,
                "severity": "high",
                "issue": "No enriched fields reported"
            })
            follow_up_questions.append("Which specific fields were enriched with new data?")
            score -= 40
        
        # Check success rate or status
        success_rate = response.get("success_rate")
        status = response.get("status")
        if not success_rate and status != "success":
            critiques.append({
                "category": CritiqueCategory.ACTIONABILITY.value,
                "severity": "medium",
                "issue": "No success rate or clear status provided"
            })
            follow_up_questions.append("What was the success rate of the enrichment process?")
            score -= 20
        
        # Check for data sources
        data_sources = response.get("data_sources") or response.get("sources")
        if not data_sources:
            critiques.append({
                "category": CritiqueCategory.ACCURACY.value,
                "severity": "medium",
                "issue": "No data sources specified for enrichment"
            })
            improvements.append("Include sources used for data enrichment")
            score -= 15
        
        # Check for specific field updates
        if isinstance(enriched_fields, list) and len(enriched_fields) == 0:
            critiques.append({
                "category": CritiqueCategory.COMPLETENESS.value,
                "severity": "high",
                "issue": "Empty list of enriched fields"
            })
            follow_up_questions.append("Were any fields actually updated during enrichment?")
            score -= 30
        
        quality = self._score_to_quality(score)
        needs_follow_up = len(follow_up_questions) > 0 or quality in [ResponseQuality.POOR, ResponseQuality.UNACCEPTABLE]
        
        return CritiqueResult(
            overall_quality=quality,
            score=max(0, score),
            critiques=critiques,
            follow_up_questions=follow_up_questions,
            suggested_improvements=improvements,
            needs_follow_up=needs_follow_up,
            confidence=75
        )
    
    def _validate_management_response(self, task_description: str,
                                    response: Dict[str, Any], context: Dict[str, Any]) -> CritiqueResult:
        """Validate company management enrichment agent responses"""
        critiques = []
        follow_up_questions = []
        improvements = []
        score = 100
        
        # Check for management company identification
        management_company = response.get("management_company") or response.get("parent_company")
        if not management_company:
            critiques.append({
                "category": CritiqueCategory.COMPLETENESS.value,
                "severity": "high",
                "issue": "No management company identified"
            })
            follow_up_questions.append("What management company was identified for this golf course?")
            score -= 40
        
        # Check for confidence/match score
        match_score = response.get("match_score") or response.get("confidence")
        if match_score is None:
            critiques.append({
                "category": CritiqueCategory.ACCURACY.value,
                "severity": "medium",
                "issue": "No confidence score provided for management company match"
            })
            follow_up_questions.append("How confident are you in this management company identification?")
            score -= 20
        elif isinstance(match_score, (int, float)) and match_score < 70:
            critiques.append({
                "category": CritiqueCategory.ACCURACY.value,
                "severity": "medium",
                "issue": f"Low confidence score ({match_score}%) for management company match"
            })
            follow_up_questions.append("Can you provide additional evidence for this management company match?")
            score -= 15
        
        # Check for HubSpot ID or update status
        hubspot_id = response.get("management_company_id") or response.get("hubspot_id")
        if not hubspot_id and "update" in task_description.lower():
            critiques.append({
                "category": CritiqueCategory.ACTIONABILITY.value,
                "severity": "medium",
                "issue": "No HubSpot ID provided for management company update"
            })
            improvements.append("Include HubSpot ID for management company record")
            score -= 15
        
        quality = self._score_to_quality(score)
        needs_follow_up = len(follow_up_questions) > 0 or quality in [ResponseQuality.POOR, ResponseQuality.UNACCEPTABLE]
        
        return CritiqueResult(
            overall_quality=quality,
            score=max(0, score),
            critiques=critiques,
            follow_up_questions=follow_up_questions,
            suggested_improvements=improvements,
            needs_follow_up=needs_follow_up,
            confidence=85
        )
    
    def _validate_field_enrichment_response(self, task_description: str,
                                          response: Dict[str, Any], context: Dict[str, Any]) -> CritiqueResult:
        """Validate field enrichment manager agent responses"""
        critiques = []
        follow_up_questions = []
        improvements = []
        score = 100
        
        # Check for field mapping results
        field_mappings = response.get("field_mappings") or response.get("mappings")
        if not field_mappings:
            critiques.append({
                "category": CritiqueCategory.COMPLETENESS.value,
                "severity": "high",
                "issue": "No field mappings provided"
            })
            follow_up_questions.append("Which fields were mapped and enriched?")
            score -= 35
        
        # Check for validation results
        validation_results = response.get("validation_results") or response.get("validation")
        if not validation_results:
            critiques.append({
                "category": CritiqueCategory.DATA_QUALITY.value,
                "severity": "medium",
                "issue": "No validation results provided"
            })
            follow_up_questions.append("What were the validation results for the enriched fields?")
            score -= 20
        
        # Check for enrichment statistics
        stats = response.get("enrichment_stats") or response.get("statistics")
        if not stats:
            critiques.append({
                "category": CritiqueCategory.ACTIONABILITY.value,
                "severity": "low",
                "issue": "No enrichment statistics provided"
            })
            improvements.append("Include statistics about enrichment success rates")
            score -= 10
        
        quality = self._score_to_quality(score)
        needs_follow_up = len(follow_up_questions) > 0 or quality in [ResponseQuality.POOR, ResponseQuality.UNACCEPTABLE]
        
        return CritiqueResult(
            overall_quality=quality,
            score=max(0, score),
            critiques=critiques,
            follow_up_questions=follow_up_questions,
            suggested_improvements=improvements,
            needs_follow_up=needs_follow_up,
            confidence=70
        )
    
    def _validate_generic_response(self, task_description: str,
                                 response: Dict[str, Any], context: Dict[str, Any]) -> CritiqueResult:
        """Validate generic agent responses"""
        critiques = []
        follow_up_questions = []
        improvements = []
        score = 80  # Start with lower baseline for generic responses
        
        # Check if response has meaningful content
        if len(response) < 2:
            critiques.append({
                "category": CritiqueCategory.COMPLETENESS.value,
                "severity": "medium",
                "issue": "Very minimal response content"
            })
            follow_up_questions.append("Can you provide more detailed information about the task results?")
            score -= 30
        
        # Check for status or result indicator
        if "status" not in response and "result" not in response and "success" not in response:
            critiques.append({
                "category": CritiqueCategory.ACTIONABILITY.value,
                "severity": "low",
                "issue": "No clear status or result indicator"
            })
            improvements.append("Include clear status or result information")
            score -= 15
        
        quality = self._score_to_quality(score)
        needs_follow_up = len(follow_up_questions) > 0 or quality in [ResponseQuality.POOR, ResponseQuality.UNACCEPTABLE]
        
        return CritiqueResult(
            overall_quality=quality,
            score=max(0, score),
            critiques=critiques,
            follow_up_questions=follow_up_questions,
            suggested_improvements=improvements,
            needs_follow_up=needs_follow_up,
            confidence=60
        )
    
    def _handle_error_response(self, response: Dict[str, Any], task_description: str) -> CritiqueResult:
        """Handle error responses from agents"""
        error_msg = response.get("error", "Unknown error")
        
        follow_up_questions = [
            f"The task failed with error: '{error_msg}'. Can you retry with different parameters?",
            "What alternative approach can we take to complete this task?"
        ]
        
        improvements = [
            "Investigate root cause of the error",
            "Consider alternative data sources or methods",
            "Verify input parameters and retry"
        ]
        
        return CritiqueResult(
            overall_quality=ResponseQuality.UNACCEPTABLE,
            score=0,
            critiques=[{
                "category": CritiqueCategory.COMPLETENESS.value,
                "severity": "critical",
                "issue": f"Task failed with error: {error_msg}"
            }],
            follow_up_questions=follow_up_questions,
            suggested_improvements=improvements,
            needs_follow_up=True,
            confidence=100
        )
    
    def _score_to_quality(self, score: float) -> ResponseQuality:
        """Convert numeric score to quality rating - More lenient scoring"""
        if score >= 85:
            return ResponseQuality.EXCELLENT
        elif score >= 65:
            return ResponseQuality.GOOD
        elif score >= 40:  # More lenient threshold
            return ResponseQuality.ACCEPTABLE
        elif score >= 20:
            return ResponseQuality.POOR
        else:
            return ResponseQuality.UNACCEPTABLE
    
    def generate_follow_up_task(self, original_task: Dict[str, Any], 
                               critique: CritiqueResult) -> Optional[Dict[str, Any]]:
        """
        Generate a follow-up task based on critique results.
        
        Args:
            original_task: The original task that was critiqued
            critique: Critique results
            
        Returns:
            New task dictionary for follow-up, or None if no follow-up needed
        """
        if not critique.needs_follow_up:
            return None
        
        # Create follow-up task with specific questions
        follow_up_task = {
            "name": f"Follow-up: {original_task.get('name', 'Unknown Task')}",
            "description": f"Address critique issues from previous task",
            "agent_type": original_task.get("agent_type", "unknown"),
            "parameters": original_task.get("parameters", {}),
            "follow_up_questions": critique.follow_up_questions,
            "improvements_requested": critique.suggested_improvements,
            "original_response_score": critique.score,
            "critique_categories": [c.get("category") for c in critique.critiques]
        }
        
        return follow_up_task


class CriticalThinkingEngine:
    """
    Advanced critical thinking engine for the Project Manager Agent.
    
    This engine goes beyond simple validation to provide strategic thinking
    about CRM operations and project outcomes.
    """
    
    def __init__(self):
        self.critic = CRMResponseCritic()
        self.thinking_patterns = {
            "goal_alignment": self._assess_goal_achievement,
            "data_completeness": self._assess_overall_data_quality,
            "business_value": self._assess_risks,
            "next_steps": self._recommend_next_actions
        }
    
    def think_critically(self, project_goal: str, task_results: List[Dict[str, Any]],
                        overall_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Apply critical thinking to project results and provide strategic insights.
        
        Args:
            project_goal: Original project goal
            task_results: Results from all completed tasks
            overall_context: Additional context about the project
            
        Returns:
            Critical thinking analysis with insights and recommendations
        """
        
        analysis = {
            "goal_achievement": self._assess_goal_achievement(project_goal, task_results),
            "data_quality": self._assess_overall_data_quality(task_results),
            "strategic_insights": self._generate_strategic_insights(project_goal, task_results),
            "recommended_actions": self._recommend_next_actions(project_goal, task_results),
            "risk_assessment": self._assess_risks(task_results),
            "success_metrics": self._calculate_success_metrics(task_results)
        }
        
        return analysis
    
    def _assess_goal_achievement(self, goal: str, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess how well the project achieved its stated goal"""
        goal_lower = goal.lower()
        
        # Analyze goal keywords and check if results address them
        goal_keywords = self._extract_goal_keywords(goal_lower)
        addressed_keywords = set()
        
        for result in results:
            result_str = str(result).lower()
            for keyword in goal_keywords:
                if keyword in result_str:
                    addressed_keywords.add(keyword)
        
        achievement_score = len(addressed_keywords) / len(goal_keywords) * 100 if goal_keywords else 0
        
        return {
            "score": achievement_score,
            "goal_keywords": list(goal_keywords),
            "addressed_keywords": list(addressed_keywords),
            "missing_aspects": list(goal_keywords - addressed_keywords),
            "assessment": "excellent" if achievement_score >= 90 else 
                         "good" if achievement_score >= 70 else
                         "partial" if achievement_score >= 50 else "poor"
        }
    
    def _assess_overall_data_quality(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess the overall data quality across all task results"""
        total_fields = 0
        complete_fields = 0
        error_count = 0
        
        for result in results:
            if "error" in result:
                error_count += 1
                continue
            
            # Count fields and completeness
            for key, value in result.items():
                total_fields += 1
                if value and str(value).strip():
                    complete_fields += 1
        
        completeness_rate = (complete_fields / total_fields * 100) if total_fields > 0 else 0
        error_rate = (error_count / len(results) * 100) if results else 0
        
        return {
            "completeness_rate": completeness_rate,
            "error_rate": error_rate,
            "total_fields": total_fields,
            "complete_fields": complete_fields,
            "quality_grade": "A" if completeness_rate >= 90 and error_rate < 5 else
                           "B" if completeness_rate >= 75 and error_rate < 10 else
                           "C" if completeness_rate >= 60 and error_rate < 20 else "F"
        }
    
    def _generate_strategic_insights(self, goal: str, results: List[Dict[str, Any]]) -> List[str]:
        """Generate strategic insights based on project results"""
        insights = []
        
        # Analyze patterns in results
        successful_agents = []
        failed_agents = []
        
        for result in results:
            agent_type = result.get("agent_type", "unknown")
            if "error" in result:
                failed_agents.append(agent_type)
            else:
                successful_agents.append(agent_type)
        
        if successful_agents:
            insights.append(f"Most reliable agents for this type of work: {', '.join(set(successful_agents))}")
        
        if failed_agents:
            insights.append(f"Agents needing improvement: {', '.join(set(failed_agents))}")
        
        # Goal-specific insights
        if "golf" in goal.lower():
            insights.append("Golf industry CRM data often requires specialized management company identification")
        
        if "enrichment" in goal.lower():
            insights.append("Data enrichment success depends heavily on data source availability and quality")
        
        return insights
    
    def _recommend_next_actions(self, goal: str, results: List[Dict[str, Any]]) -> List[str]:
        """Recommend next actions based on project results"""
        actions = []
        
        # Check for incomplete data
        incomplete_results = [r for r in results if "error" in r or not r]
        if incomplete_results:
            actions.append("Retry failed tasks with different parameters or approaches")
        
        # Check for enrichment opportunities
        enrichment_opportunities = self._identify_enrichment_opportunities(results)
        if enrichment_opportunities:
            actions.extend(enrichment_opportunities)
        
        # Goal-specific recommendations
        if "management" in goal.lower() and "company" in goal.lower():
            actions.append("Validate management company relationships with additional sources")
        
        if "arizona" in goal.lower() or "location" in goal.lower():
            actions.append("Consider expanding search to neighboring regions for comprehensive coverage")
        
        return actions
    
    def _assess_risks(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess risks in the project results"""
        risks = {
            "data_accuracy": [],
            "completeness": [],
            "operational": []
        }
        
        # Check for low confidence scores
        for result in results:
            confidence = result.get("confidence") or result.get("match_score")
            if confidence and isinstance(confidence, (int, float)) and confidence < 70:
                risks["data_accuracy"].append(f"Low confidence result: {confidence}%")
        
        # Check for missing critical data
        for result in results:
            if not result or "error" in result:
                risks["operational"].append("Task execution failures detected")
        
        return risks
    
    def _calculate_success_metrics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate overall success metrics"""
        total_tasks = len(results)
        successful_tasks = len([r for r in results if r and "error" not in r])
        
        return {
            "task_success_rate": (successful_tasks / total_tasks * 100) if total_tasks > 0 else 0,
            "total_tasks": total_tasks,
            "successful_tasks": successful_tasks,
            "failed_tasks": total_tasks - successful_tasks
        }
    
    def _extract_goal_keywords(self, goal: str) -> set:
        """Extract key terms from project goal"""
        keywords = set()
        
        # Common CRM goal keywords
        goal_terms = {
            "find", "search", "identify", "enrich", "update", "analyze", "review",
            "golf", "club", "course", "company", "contact", "management", "arizona",
            "hubspot", "data", "fields", "missing", "records"
        }
        
        words = goal.lower().split()
        for word in words:
            clean_word = word.strip(".,!?")
            if clean_word in goal_terms:
                keywords.add(clean_word)
        
        return keywords
    
    def _identify_enrichment_opportunities(self, results: List[Dict[str, Any]]) -> List[str]:
        """Identify opportunities for additional data enrichment"""
        opportunities = []
        
        # Look for partial results that could be improved
        for result in results:
            if isinstance(result, dict):
                # Check for empty or minimal descriptions
                description = result.get("description") or result.get("company_description")
                if description and len(str(description).strip()) < 50:
                    opportunities.append("Expand company descriptions with more detailed information")
                
                # Check for missing industry classification
                if not result.get("industry") and not result.get("industry_classification"):
                    opportunities.append("Add industry classification to company records")
                
                # Check for missing contact information
                if not result.get("email") and not result.get("contact_email"):
                    opportunities.append("Enrich contact email addresses")
        
        return list(set(opportunities))  # Remove duplicates
