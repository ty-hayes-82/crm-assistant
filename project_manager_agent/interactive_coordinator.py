"""
Interactive Project Manager Coordinator with Chat Interface
Shows real-time A2A communication between Project Manager and CRM agents
"""

import sys
import os
import asyncio
import time
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from typing import Dict, Any, List, Optional
from google.adk.agents import LlmAgent
from .core.task_models import Project, Task, TaskStatus, TaskPriority
from .core.critique_system import CRMResponseCritic, CriticalThinkingEngine, ResponseQuality
from .chat_interface import ChatInterface, MessageType, format_agent_response
import uuid
from datetime import datetime

# Import CRM agent factory
from crm_agent.core.factory import crm_agent_registry


class InteractiveProjectManagerAgent(LlmAgent):
    """
    Interactive Project Manager Agent with real-time chat display.
    Shows A2A communication as it happens.
    """
    
    def __init__(self, **kwargs):
        super().__init__(
            name="InteractiveProjectManagerAgent",
            model='gemini-2.5-flash',
            instruction="""
You are an intelligent Project Manager Agent that orchestrates complex CRM operations.
You communicate with users and coordinate with specialized CRM agents to achieve goals.
            """,
            **kwargs
        )
        # Initialize project management components
        self._init_project_management()
    
    def _init_project_management(self):
        """Initialize project management components"""
        # Store as private attributes to avoid Pydantic validation
        self._projects = {}
        self._chat = ChatInterface()
        self._available_agents = {}
        self._critic = CRMResponseCritic()
        self._thinking_engine = CriticalThinkingEngine()
        self._critique_history = {}
        self._register_agents()
    
    @property
    def projects(self):
        return self._projects
    
    @property
    def chat(self):
        return self._chat
    
    @property
    def available_agents(self):
        return self._available_agents
    
    def _register_agents(self):
        """Register available CRM agents"""
        try:
            self._available_agents = {
                "company_intelligence": crm_agent_registry.create_agent("company_intelligence"),
                "contact_intelligence": crm_agent_registry.create_agent("contact_intelligence"), 
                "crm_enrichment": crm_agent_registry.create_agent("crm_enrichment"),
                "company_management_enrichment": crm_agent_registry.create_agent("company_management_enrichment"),
                "field_enrichment_manager": crm_agent_registry.create_agent("field_enrichment_manager")
            }
            
            self.chat.add_message(
                MessageType.SYSTEM,
                f"🤖 Registered {len(self.available_agents)} CRM agents for coordination"
            )
        except Exception as e:
            self.chat.add_message(
                MessageType.SYSTEM,
                f"⚠️ Error registering agents: {str(e)}"
            )
    
    async def start_interactive_session(self):
        """Start an interactive chat session"""
        
        # Welcome and get user goal
        goal = self.chat.start_session()
        
        if not goal or goal.lower() in ['quit', 'exit']:
            self.chat.add_message(MessageType.PROJECT_MANAGER, "👋 Goodbye!")
            return
        
        # Execute the goal with chat display
        await self.execute_goal_with_chat(goal)
        
        # Ask if user wants to continue
        continue_session = self.chat.get_user_input("Would you like to set another goal? (yes/no)")
        if continue_session.lower().startswith('y'):
            await self.start_interactive_session()
        else:
            self.chat.add_message(MessageType.PROJECT_MANAGER, "👋 Session ended. Thank you!")
    
    async def execute_goal_with_chat(self, goal: str, context: Dict[str, Any] = None):
        """Execute a goal with real-time chat display"""
        
        self.chat.display_separator("GOAL ANALYSIS")
        
        # Analyze and break down the goal
        self.chat.add_message(
            MessageType.PROJECT_MANAGER,
            f"🎯 Analyzing goal: '{goal}'"
        )
        
        await asyncio.sleep(0.1)  # Brief delay for UI responsiveness
        
        # Create project plan
        project = self._create_project_plan_with_chat(goal, context or {})
        
        # Store project
        self.projects[project.id] = project
        
        # Show project plan
        self._display_project_plan(project)
        
        # Execute project with chat updates
        result = await self._execute_project_with_chat(project)
        
        # Show final results
        self.chat.show_project_summary(result)
        
        return result
    
    def _create_project_plan_with_chat(self, goal: str, context: Dict[str, Any]) -> Project:
        """Create project plan with chat updates"""
        
        self.chat.add_message(
            MessageType.PROJECT_MANAGER,
            "📋 Creating project plan..."
        )
        
        project_id = str(uuid.uuid4())[:8]
        
        project = Project(
            id=project_id,
            name=f"CRM Goal: {goal[:50]}{'...' if len(goal) > 50 else ''}",
            description=goal,
            goal=goal
        )
        
        # Parse goal and create tasks
        tasks = self._parse_goal_to_tasks_with_chat(goal, context)
        
        for task in tasks:
            project.add_task(task)
        
        return project
    
    def _parse_goal_to_tasks_with_chat(self, goal: str, context: Dict[str, Any]) -> List[Task]:
        """Parse goal into tasks with chat updates"""
        
        self.chat.add_message(
            MessageType.PROJECT_MANAGER,
            "🔍 Analyzing goal components..."
        )
        
        goal_lower = goal.lower()
        tasks = []
        
        # Pattern matching with chat updates
        if "mansion ridge" in goal_lower or ("golf club" in goal_lower and "ridge" in goal_lower):
            self.chat.add_message(
                MessageType.PROJECT_MANAGER,
                "🏌️ Detected: Single golf club analysis (Mansion Ridge)"
            )
            
            # Task 1: Company intelligence
            details_task = Task(
                id=f"intel_{uuid.uuid4().hex[:6]}",
                name="Company Intelligence Analysis",
                description="Gather comprehensive company information",
                agent_type="company_intelligence",
                parameters={"company_name": "The Golf Club at Mansion Ridge"},
                priority=TaskPriority.HIGH
            )
            tasks.append(details_task)
            
            # Task 2: Management company identification
            mgmt_task = Task(
                id=f"mgmt_{uuid.uuid4().hex[:6]}",
                name="Management Company Identification",
                description="Identify and set parent company relationship",
                agent_type="company_management_enrichment",
                parameters={
                    "company_name": "The Golf Club at Mansion Ridge",
                    "company_id": "hubspot_mansion_ridge"
                },
                dependencies=[details_task.id],
                priority=TaskPriority.HIGH
            )
            tasks.append(mgmt_task)
            
        elif "arizona" in goal_lower and "golf" in goal_lower:
            self.chat.add_message(
                MessageType.PROJECT_MANAGER,
                "🌵 Detected: Arizona golf clubs discovery and enrichment"
            )
            
            # Task 1: Search for Arizona clubs using company intelligence
            search_task = Task(
                id=f"search_{uuid.uuid4().hex[:6]}",
                name="Search Arizona Golf Clubs",
                description="Find all golf clubs in Arizona using intelligence gathering",
                agent_type="company_intelligence",
                parameters={
                    "location": "Arizona",
                    "company_type": "Golf Course",
                    "search_criteria": ["Public", "Private", "Semi-Private"]
                },
                priority=TaskPriority.HIGH
            )
            tasks.append(search_task)
            
            # Task 2: Enrich found companies using field enrichment manager
            enrich_task = Task(
                id=f"enrich_{uuid.uuid4().hex[:6]}",
                name="Enrich Company Data",
                description="Systematically enrich missing fields for found companies",
                agent_type="field_enrichment_manager",
                parameters={"target_fields": ["description", "annual_revenue", "management_company"]},
                dependencies=[search_task.id],
                priority=TaskPriority.MEDIUM
            )
            tasks.append(enrich_task)
            
        else:
            self.chat.add_message(
                MessageType.PROJECT_MANAGER,
                "🔧 Detected: General CRM analysis task"
            )
            
            # Generic analysis task
            analysis_task = Task(
                id=f"analysis_{uuid.uuid4().hex[:6]}",
                name="Goal Analysis",
                description=f"Analyze and execute: {goal}",
                agent_type="company_intelligence",
                parameters={"goal": goal, "context": context},
                priority=TaskPriority.MEDIUM
            )
            tasks.append(analysis_task)
        
        return tasks
    
    def _display_project_plan(self, project: Project):
        """Display the project plan in chat"""
        
        self.chat.display_separator("PROJECT PLAN")
        
        plan_msg = f"📊 Project: {project.name}\n"
        plan_msg += f"🎯 Goal: {project.goal}\n"
        plan_msg += f"📋 Tasks: {len(project.tasks)}\n\n"
        plan_msg += "Task Breakdown:"
        
        for i, task in enumerate(project.tasks, 1):
            plan_msg += f"\n  {i}. {task.name}"
            plan_msg += f"\n     Agent: {task.agent_type}"
            if task.dependencies:
                plan_msg += f"\n     Depends on: {', '.join(task.dependencies)}"
        
        self.chat.add_message(MessageType.PROJECT_MANAGER, plan_msg)
        
        # Show task progress
        task_list = [{"name": task.name, "status": task.status.value} for task in project.tasks]
        self.chat.show_task_progress(task_list)
    
    async def _execute_project_with_chat(self, project: Project) -> Dict[str, Any]:
        """Execute project with real-time chat updates"""
        
        self.chat.display_separator("PROJECT EXECUTION")
        
        self.chat.add_message(
            MessageType.PROJECT_MANAGER,
            f"🚀 Starting project execution with {len(project.tasks)} tasks"
        )
        
        results = {}
        
        # Execute tasks with dependencies
        while True:
            ready_tasks = project.get_ready_tasks()
            
            if not ready_tasks:
                incomplete_tasks = [t for t in project.tasks if t.status == TaskStatus.PENDING]
                if not incomplete_tasks:
                    break  # All tasks completed
                else:
                    # Handle circular dependencies
                    for task in incomplete_tasks:
                        task.fail("Unmet dependencies")
                    break
            
            # Execute each ready task
            for task in ready_tasks:
                result = await self._execute_task_with_chat(task)
                results[task.id] = result
                
                # Update task progress display
                task_list = [{"name": t.name, "status": t.status.value} for t in project.tasks]
                current_task = None
                for t in project.tasks:
                    if t.status == TaskStatus.IN_PROGRESS:
                        current_task = t.name
                        break
                
                if not current_task:  # No tasks in progress, show completed status
                    self.chat.add_message(
                        MessageType.PROJECT_MANAGER,
                        f"✅ Task completed: {task.name}"
                    )
        
        # Generate final results
        completed = sum(1 for t in project.tasks if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in project.tasks if t.status == TaskStatus.FAILED)
        
        return {
            "project_id": project.id,
            "status": project.status,
            "progress": project.progress,
            "total_tasks": len(project.tasks),
            "completed_tasks": completed,
            "failed_tasks": failed,
            "task_results": results
        }
    
    async def _execute_task_with_chat(self, task: Task) -> Dict[str, Any]:
        """Execute a single task with chat updates"""
        
        self.chat.add_message(
            MessageType.PROJECT_MANAGER,
            f"🎯 Executing: {task.name}"
        )
        
        task.start()
        
        # Show agent communication
        agent_name = task.agent_type.replace('_', ' ').title()
        
        self.chat.show_agent_communication(
            "Project Manager",
            agent_name,
            f"Execute task: {task.description}"
        )
        
        # Brief delay for UI responsiveness
        await asyncio.sleep(0.1)
        
        try:
            # Execute the task based on type
            if task.agent_type == "company_management_enrichment":
                result = await self._execute_management_task(task)
            elif task.agent_type == "company_intelligence":
                result = await self._execute_intelligence_task(task)
            elif task.agent_type == "field_enrichment_manager":
                result = await self._execute_field_enrichment_task(task)
            elif task.agent_type == "crm_enrichment":
                result = await self._execute_crm_enrichment_task(task)
            else:
                result = {"status": "completed", "message": "Task executed successfully"}
            
            # Format and show agent response
            response_text = format_agent_response(task.agent_type, result)
            self.chat.show_agent_communication(
                "Project Manager",
                agent_name,
                "",  # No outgoing message for response
                response_text
            )
            
            # Critique the response
            critique = self._critique_task_result_with_chat(task, result)
            
            # Show critique results in chat
            self._display_critique_results(task, critique)
            
            # Generate follow-up if needed
            if critique.needs_follow_up:
                follow_up_task = self._create_follow_up_task_with_chat(task, critique)
                if follow_up_task:
                    # Execute follow-up immediately
                    self.chat.add_message(
                        MessageType.PROJECT_MANAGER,
                        f"🔄 Executing follow-up for better results..."
                    )
                    follow_up_result = await self._execute_task_with_chat(follow_up_task)
                    # Use follow-up result if it's better
                    if not follow_up_result.get("error"):
                        result.update(follow_up_result)
            
            task.complete(result)
            return result
            
        except Exception as e:
            error_msg = f"Task failed: {str(e)}"
            task.fail(error_msg)
            
            self.chat.show_agent_communication(
                "Project Manager",
                agent_name,
                "",
                f"❌ Error: {error_msg}"
            )
            
            return {"error": error_msg}
    
    async def _execute_management_task(self, task: Task) -> Dict[str, Any]:
        """Execute management company identification task"""
        
        company_name = task.parameters.get("company_name")
        company_id = task.parameters.get("company_id", "test_id")
        
        # Use the actual company management agent
        if "company_management_enrichment" in self.available_agents:
            agent = self.available_agents["company_management_enrichment"]
            result = agent.run(company_name, company_id)
            return result
        else:
            return {"error": "Company management enrichment agent not available"}
    
    async def _execute_intelligence_task(self, task: Task) -> Dict[str, Any]:
        """Execute company intelligence task using real agent"""
        if "company_intelligence" in self.available_agents:
            agent = self.available_agents["company_intelligence"]
            result = agent.run(**task.parameters)
            return result
        else:
            return {"error": "Company intelligence agent not available"}
    
    async def _execute_field_enrichment_task(self, task: Task) -> Dict[str, Any]:
        """Execute field enrichment task using real agent"""
        if "field_enrichment_manager" in self.available_agents:
            agent = self.available_agents["field_enrichment_manager"]
            result = agent.run(**task.parameters)
            return result
        else:
            return {"error": "Field enrichment manager agent not available"}
    
    async def _execute_crm_enrichment_task(self, task: Task) -> Dict[str, Any]:
        """Execute CRM enrichment task using real agent"""
        if "crm_enrichment" in self.available_agents:
            agent = self.available_agents["crm_enrichment"]
            result = agent.run(**task.parameters)
            return result
        else:
            return {"error": "CRM enrichment agent not available"}
    
    def _critique_task_result_with_chat(self, task: Task, result: Dict[str, Any]):
        """Critique task result with chat display"""
        critique = self._critic.critique_response(
            agent_type=task.agent_type,
            task_description=task.description,
            response=result,
            context=task.parameters
        )
        
        # Store critique
        self._critique_history[task.id] = critique
        
        return critique
    
    def _display_critique_results(self, task: Task, critique):
        """Display critique results in chat"""
        if critique.overall_quality in [ResponseQuality.EXCELLENT, ResponseQuality.GOOD]:
            self.chat.add_message(
                MessageType.PROJECT_MANAGER,
                f"✅ Response quality: {critique.overall_quality.value.title()} (Score: {critique.score:.0f}/100)"
            )
        elif critique.overall_quality == ResponseQuality.ACCEPTABLE:
            self.chat.add_message(
                MessageType.PROJECT_MANAGER,
                f"⚠️ Response quality: {critique.overall_quality.value.title()} (Score: {critique.score:.0f}/100)"
            )
        else:
            self.chat.add_message(
                MessageType.PROJECT_MANAGER,
                f"❌ Response quality: {critique.overall_quality.value.title()} (Score: {critique.score:.0f}/100)"
            )
            
            # Show specific issues
            if critique.critiques:
                issues = [c.get("issue", "") for c in critique.critiques[:2]]  # Show top 2 issues
                for issue in issues:
                    if issue:
                        self.chat.add_message(
                            MessageType.PROJECT_MANAGER,
                            f"   🔍 Issue: {issue}"
                        )
    
    def _create_follow_up_task_with_chat(self, original_task: Task, critique):
        """Create follow-up task with chat notification"""
        if not critique.needs_follow_up:
            return None
        
        follow_up_id = f"followup_{original_task.id}_{uuid.uuid4().hex[:4]}"
        
        # Create enhanced parameters with critique guidance
        enhanced_params = original_task.parameters.copy()
        enhanced_params.update({
            "follow_up_questions": critique.follow_up_questions,
            "improvement_areas": critique.suggested_improvements,
            "original_score": critique.score
        })
        
        follow_up_task = Task(
            id=follow_up_id,
            name=f"Follow-up: {original_task.name}",
            description=f"Address critique issues and improve response quality",
            agent_type=original_task.agent_type,
            parameters=enhanced_params,
            priority=TaskPriority.HIGH
        )
        
        # Show follow-up questions in chat
        if critique.follow_up_questions:
            self.chat.add_message(
                MessageType.PROJECT_MANAGER,
                f"🤔 Follow-up questions for {original_task.agent_type}:"
            )
            for question in critique.follow_up_questions[:3]:  # Show top 3 questions
                self.chat.add_message(
                    MessageType.PROJECT_MANAGER,
                    f"   ❓ {question}"
                )
        
        return follow_up_task


def create_interactive_project_manager(**kwargs) -> InteractiveProjectManagerAgent:
    """Create an Interactive Project Manager Agent instance."""
    return InteractiveProjectManagerAgent(**kwargs)
