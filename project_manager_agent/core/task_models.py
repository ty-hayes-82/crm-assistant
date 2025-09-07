"""
Task models for the Project Manager Agent
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Task priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Task:
    """Represents a task in the project management system"""
    
    id: str
    name: str
    description: str
    agent_type: str  # Which agent should execute this task
    parameters: Dict[str, Any] = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    dependencies: List[str] = field(default_factory=list)  # Task IDs this task depends on
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    def start(self):
        """Mark task as started"""
        self.status = TaskStatus.IN_PROGRESS
        self.started_at = datetime.now()
    
    def complete(self, result: Dict[str, Any]):
        """Mark task as completed with result"""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now()
        self.result = result
    
    def fail(self, error: str):
        """Mark task as failed with error"""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.now()
        self.error = error
    
    def cancel(self):
        """Cancel the task"""
        self.status = TaskStatus.CANCELLED
        self.completed_at = datetime.now()
    
    @property
    def is_ready(self) -> bool:
        """Check if task is ready to execute (all dependencies completed)"""
        return self.status == TaskStatus.PENDING
    
    @property
    def duration(self) -> Optional[float]:
        """Get task duration in seconds"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


@dataclass
class Project:
    """Represents a project containing multiple tasks"""
    
    id: str
    name: str
    description: str
    goal: str
    tasks: List[Task] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    @property
    def status(self) -> str:
        """Get overall project status"""
        if not self.tasks:
            return "empty"
        
        statuses = [task.status for task in self.tasks]
        
        if all(s == TaskStatus.COMPLETED for s in statuses):
            return "completed"
        elif any(s == TaskStatus.FAILED for s in statuses):
            return "failed"
        elif any(s == TaskStatus.IN_PROGRESS for s in statuses):
            return "in_progress"
        else:
            return "pending"
    
    @property
    def progress(self) -> float:
        """Get project completion percentage"""
        if not self.tasks:
            return 0.0
        
        completed = sum(1 for task in self.tasks if task.status == TaskStatus.COMPLETED)
        return (completed / len(self.tasks)) * 100
    
    def add_task(self, task: Task):
        """Add a task to the project"""
        self.tasks.append(task)
    
    def get_ready_tasks(self) -> List[Task]:
        """Get tasks that are ready to execute"""
        completed_task_ids = {task.id for task in self.tasks if task.status == TaskStatus.COMPLETED}
        
        ready_tasks = []
        for task in self.tasks:
            if task.status == TaskStatus.PENDING:
                # Check if all dependencies are completed
                if all(dep_id in completed_task_ids for dep_id in task.dependencies):
                    ready_tasks.append(task)
        
        return ready_tasks
