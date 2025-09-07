"""
Task orchestration engine for the Project Manager Agent
"""

import asyncio
from typing import Dict, Any, List, Optional, Callable
from .task_models import Task, TaskStatus, Project
import uuid
import sys
import os

# Add the parent directory to the path to import crm_agent
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))


class TaskOrchestrator:
    """Orchestrates task execution across multiple agents"""
    
    def __init__(self):
        self.agent_registry = {}
        self.running_tasks = {}
        
    def register_agent(self, agent_type: str, agent_factory: Callable):
        """Register an agent factory for a specific agent type"""
        self.agent_registry[agent_type] = agent_factory
        
    def get_agent(self, agent_type: str):
        """Get an agent instance by type"""
        if agent_type not in self.agent_registry:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        return self.agent_registry[agent_type]()
    
    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """Execute a single task"""
        print(f"🚀 Starting task: {task.name}")
        task.start()
        
        try:
            # Get the appropriate agent
            agent = self.get_agent(task.agent_type)
            
            # Execute the task based on its type
            if task.agent_type == "crm_agent":
                result = await self._execute_crm_task(agent, task)
            elif task.agent_type == "company_management_agent":
                result = await self._execute_company_management_task(agent, task)
            else:
                result = await self._execute_generic_task(agent, task)
            
            task.complete(result)
            print(f"✅ Completed task: {task.name}")
            return result
            
        except Exception as e:
            error_msg = f"Task failed: {str(e)}"
            task.fail(error_msg)
            print(f"❌ Failed task: {task.name} - {error_msg}")
            return {"error": error_msg}
    
    async def _execute_crm_task(self, agent, task: Task) -> Dict[str, Any]:
        """Execute a CRM-specific task using real agents"""
        # Use the actual CRM agent to execute the task
        if hasattr(agent, 'run'):
            return agent.run(**task.parameters)
        else:
            return {"error": f"Agent does not support execution"}
    
    async def _execute_company_management_task(self, agent, task: Task) -> Dict[str, Any]:
        """Execute a company management task"""
        company_name = task.parameters.get("company_name")
        company_id = task.parameters.get("company_id")
        
        print(f"   🏌️ Identifying management company for: {company_name}")
        
        # Use the actual company management agent
        result = agent.run(company_name, company_id)
        return result
    
    async def _execute_generic_task(self, agent, task: Task) -> Dict[str, Any]:
        """Execute a generic task"""
        # For other agent types, try to call a run method with parameters
        if hasattr(agent, 'run'):
            return agent.run(**task.parameters)
        else:
            return {"error": f"Agent {task.agent_type} does not support generic execution"}
    
    async def execute_project(self, project: Project) -> Dict[str, Any]:
        """Execute all tasks in a project"""
        print(f"🎯 Starting project: {project.name}")
        print(f"   Goal: {project.goal}")
        print(f"   Tasks: {len(project.tasks)}")
        
        results = {}
        
        # Execute tasks respecting dependencies
        while True:
            ready_tasks = project.get_ready_tasks()
            
            if not ready_tasks:
                # Check if all tasks are completed
                incomplete_tasks = [t for t in project.tasks if t.status == TaskStatus.PENDING]
                if not incomplete_tasks:
                    break  # All tasks completed
                else:
                    # There are pending tasks but none are ready - circular dependency or error
                    for task in incomplete_tasks:
                        task.fail("Circular dependency or unmet dependencies")
                    break
            
            # Execute ready tasks (could be done in parallel in the future)
            for task in ready_tasks:
                result = await self.execute_task(task)
                results[task.id] = result
        
        # Generate project summary
        completed = sum(1 for t in project.tasks if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in project.tasks if t.status == TaskStatus.FAILED)
        
        project_result = {
            "project_id": project.id,
            "status": project.status,
            "progress": project.progress,
            "total_tasks": len(project.tasks),
            "completed_tasks": completed,
            "failed_tasks": failed,
            "task_results": results
        }
        
        print(f"📊 Project completed: {completed}/{len(project.tasks)} tasks successful")
        return project_result
