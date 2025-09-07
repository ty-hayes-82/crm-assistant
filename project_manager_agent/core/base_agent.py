"""
Base Project Manager Agent class using ADK framework
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from google.adk.agents import LlmAgent
from .task_models import Project, Task


class BaseProjectManagerAgent(LlmAgent, ABC):
    """Base class for project management agents"""
    
    def __init__(self, name: str, **kwargs):
        super().__init__(name=name, **kwargs)
        self.projects: Dict[str, Project] = {}
        self.active_project: Optional[Project] = None
    
    @abstractmethod
    def create_project_plan(self, goal: str, context: Dict[str, Any] = None) -> Project:
        """
        Create a project plan from a high-level goal.
        
        Args:
            goal: The high-level goal or objective
            context: Additional context information
            
        Returns:
            A Project containing the planned tasks
        """
        pass
    
    @abstractmethod
    def execute_project(self, project: Project) -> Dict[str, Any]:
        """
        Execute a project by orchestrating its tasks.
        
        Args:
            project: The project to execute
            
        Returns:
            Execution results and summary
        """
        pass
    
    def get_project_status(self, project_id: str) -> Dict[str, Any]:
        """Get the status of a project"""
        if project_id not in self.projects:
            return {"error": f"Project {project_id} not found"}
        
        project = self.projects[project_id]
        return {
            "project_id": project_id,
            "name": project.name,
            "status": project.status,
            "progress": project.progress,
            "tasks": len(project.tasks),
            "completed_tasks": sum(1 for t in project.tasks if t.status.value == "completed"),
            "failed_tasks": sum(1 for t in project.tasks if t.status.value == "failed")
        }
    
    def list_projects(self) -> List[Dict[str, Any]]:
        """List all projects"""
        return [
            {
                "id": project.id,
                "name": project.name,
                "status": project.status,
                "progress": project.progress,
                "created_at": project.created_at.isoformat()
            }
            for project in self.projects.values()
        ]
