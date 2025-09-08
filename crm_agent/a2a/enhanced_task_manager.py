"""
Enhanced A2A Task Manager with priority queues and dependencies.
Provides advanced task lifecycle management for A2A operations.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any, List, Set
import asyncio
import uuid
from datetime import datetime, timedelta
import json

from .http_server import TaskState, TaskInfo
from ..core.observability import get_logger


class TaskPriority(Enum):
    """Task priority levels."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4


@dataclass
class EnhancedTaskInfo:
    """Enhanced task information with priority and dependencies."""
    id: str
    context_id: str
    state: TaskState
    priority: TaskPriority
    created_at: datetime
    updated_at: datetime
    query: str
    
    # Enhanced fields
    dependencies: List[str] = field(default_factory=list)  # Task IDs this task depends on
    dependents: List[str] = field(default_factory=list)   # Task IDs that depend on this task
    timeout_seconds: Optional[int] = None
    retry_count: int = 0
    max_retries: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    # Execution tracking
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_time_ms: Optional[float] = None
    
    # Resource requirements
    resource_requirements: Dict[str, Any] = field(default_factory=dict)
    allocated_resources: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskExecutionContext:
    """Context for task execution."""
    task: EnhancedTaskInfo
    session_id: str
    user_id: str = "default"
    trace_id: Optional[str] = None
    parent_task_id: Optional[str] = None
    execution_environment: Dict[str, Any] = field(default_factory=dict)


class TaskDependencyManager:
    """Manages task dependencies and execution ordering."""
    
    def __init__(self):
        self.dependency_graph: Dict[str, Set[str]] = {}  # task_id -> set of dependencies
        self.dependents_graph: Dict[str, Set[str]] = {}  # task_id -> set of dependents
        self.completed_tasks: Set[str] = set()
        self.failed_tasks: Set[str] = set()
        self.logger = get_logger("task_dependency_manager")
    
    def add_dependency(self, task_id: str, dependency_id: str):
        """Add a dependency relationship."""
        if task_id not in self.dependency_graph:
            self.dependency_graph[task_id] = set()
        self.dependency_graph[task_id].add(dependency_id)
        
        if dependency_id not in self.dependents_graph:
            self.dependents_graph[dependency_id] = set()
        self.dependents_graph[dependency_id].add(task_id)
    
    def remove_dependency(self, task_id: str, dependency_id: str):
        """Remove a dependency relationship."""
        if task_id in self.dependency_graph:
            self.dependency_graph[task_id].discard(dependency_id)
        if dependency_id in self.dependents_graph:
            self.dependents_graph[dependency_id].discard(task_id)
    
    def get_dependencies(self, task_id: str) -> Set[str]:
        """Get all dependencies for a task."""
        return self.dependency_graph.get(task_id, set())
    
    def get_dependents(self, task_id: str) -> Set[str]:
        """Get all dependents of a task."""
        return self.dependents_graph.get(task_id, set())
    
    def are_dependencies_satisfied(self, task_id: str) -> bool:
        """Check if all dependencies for a task are satisfied."""
        dependencies = self.get_dependencies(task_id)
        return all(dep_id in self.completed_tasks for dep_id in dependencies)
    
    def mark_task_completed(self, task_id: str):
        """Mark a task as completed."""
        self.completed_tasks.add(task_id)
        self.failed_tasks.discard(task_id)  # Remove from failed if it was there
    
    def mark_task_failed(self, task_id: str):
        """Mark a task as failed."""
        self.failed_tasks.add(task_id)
        self.completed_tasks.discard(task_id)  # Remove from completed if it was there
    
    def get_ready_tasks(self, all_tasks: Dict[str, EnhancedTaskInfo]) -> List[str]:
        """Get tasks that are ready to execute (dependencies satisfied)."""
        ready_tasks = []
        
        for task_id, task in all_tasks.items():
            if (task.state == TaskState.QUEUED and 
                self.are_dependencies_satisfied(task_id)):
                ready_tasks.append(task_id)
        
        return ready_tasks
    
    def detect_circular_dependencies(self) -> List[List[str]]:
        """Detect circular dependencies in the task graph."""
        visited = set()
        rec_stack = set()
        cycles = []
        
        def dfs(node: str, path: List[str]):
            if node in rec_stack:
                # Found a cycle
                cycle_start = path.index(node)
                cycles.append(path[cycle_start:] + [node])
                return
            
            if node in visited:
                return
            
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in self.dependency_graph.get(node, set()):
                dfs(neighbor, path.copy())
            
            rec_stack.remove(node)
        
        for task_id in self.dependency_graph:
            if task_id not in visited:
                dfs(task_id, [])
        
        return cycles


class ResourceManager:
    """Manages resource allocation for tasks."""
    
    def __init__(self, max_concurrent_tasks: int = 10, max_memory_mb: int = 1024):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.max_memory_mb = max_memory_mb
        self.current_tasks = 0
        self.allocated_memory_mb = 0
        self.resource_locks: Dict[str, asyncio.Lock] = {}
        self.logger = get_logger("resource_manager")
    
    async def allocate_resources(self, task: EnhancedTaskInfo) -> bool:
        """
        Allocate resources for a task.
        
        Returns:
            True if resources allocated successfully, False otherwise
        """
        required_slots = task.resource_requirements.get("concurrent_slots", 1)
        required_memory = task.resource_requirements.get("memory_mb", 100)
        
        # Check if resources are available
        if (self.current_tasks + required_slots > self.max_concurrent_tasks or
            self.allocated_memory_mb + required_memory > self.max_memory_mb):
            return False
        
        # Allocate resources
        self.current_tasks += required_slots
        self.allocated_memory_mb += required_memory
        
        task.allocated_resources = {
            "concurrent_slots": required_slots,
            "memory_mb": required_memory,
            "allocated_at": datetime.now().isoformat()
        }
        
        self.logger.debug(
            f"Allocated resources for task {task.id}",
            extra={
                "task_id": task.id,
                "slots": required_slots,
                "memory_mb": required_memory,
                "total_slots": self.current_tasks,
                "total_memory": self.allocated_memory_mb
            }
        )
        
        return True
    
    def release_resources(self, task: EnhancedTaskInfo):
        """Release resources allocated to a task."""
        if not task.allocated_resources:
            return
        
        slots = task.allocated_resources.get("concurrent_slots", 0)
        memory = task.allocated_resources.get("memory_mb", 0)
        
        self.current_tasks = max(0, self.current_tasks - slots)
        self.allocated_memory_mb = max(0, self.allocated_memory_mb - memory)
        
        self.logger.debug(
            f"Released resources for task {task.id}",
            extra={
                "task_id": task.id,
                "slots": slots,
                "memory_mb": memory,
                "remaining_slots": self.current_tasks,
                "remaining_memory": self.allocated_memory_mb
            }
        )
        
        task.allocated_resources = {}
    
    def get_resource_usage(self) -> Dict[str, Any]:
        """Get current resource usage statistics."""
        return {
            "current_tasks": self.current_tasks,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "allocated_memory_mb": self.allocated_memory_mb,
            "max_memory_mb": self.max_memory_mb,
            "utilization": {
                "tasks": self.current_tasks / self.max_concurrent_tasks,
                "memory": self.allocated_memory_mb / self.max_memory_mb
            }
        }


class EnhancedTaskManager:
    """Enhanced task manager with priority queues and dependencies."""
    
    def __init__(self, max_concurrent_tasks: int = 10):
        self.tasks: Dict[str, EnhancedTaskInfo] = {}
        self.priority_queues = {
            TaskPriority.URGENT: asyncio.Queue(),
            TaskPriority.HIGH: asyncio.Queue(),
            TaskPriority.MEDIUM: asyncio.Queue(),
            TaskPriority.LOW: asyncio.Queue()
        }
        
        self.dependency_manager = TaskDependencyManager()
        self.resource_manager = ResourceManager(max_concurrent_tasks)
        
        self.logger = get_logger("enhanced_task_manager")
        self._running = False
        self._worker_tasks: List[asyncio.Task] = []
        self._scheduler_task: Optional[asyncio.Task] = None
    
    async def create_task(self, 
                         query: str,
                         context_id: str,
                         priority: TaskPriority = TaskPriority.MEDIUM,
                         dependencies: Optional[List[str]] = None,
                         timeout_seconds: Optional[int] = None,
                         metadata: Optional[Dict[str, Any]] = None,
                         resource_requirements: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a new enhanced task.
        
        Returns:
            Task ID of the created task
        """
        task_id = str(uuid.uuid4())
        
        task = EnhancedTaskInfo(
            id=task_id,
            context_id=context_id,
            state=TaskState.QUEUED,
            priority=priority,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            query=query,
            dependencies=dependencies or [],
            timeout_seconds=timeout_seconds,
            metadata=metadata or {},
            resource_requirements=resource_requirements or {}
        )
        
        self.tasks[task_id] = task
        
        # Add dependencies
        for dep_id in task.dependencies:
            self.dependency_manager.add_dependency(task_id, dep_id)
        
        self.logger.info(
            f"Created task {task_id}",
            extra={
                "task_id": task_id,
                "priority": priority.name,
                "dependencies": dependencies,
                "context_id": context_id
            }
        )
        
        return task_id
    
    async def enqueue_task(self, task_id: str):
        """Enqueue a task for execution based on priority and dependencies."""
        if task_id not in self.tasks:
            raise ValueError(f"Task not found: {task_id}")
        
        task = self.tasks[task_id]
        
        # Check if dependencies are satisfied
        if not self.dependency_manager.are_dependencies_satisfied(task_id):
            self.logger.debug(f"Task {task_id} waiting for dependencies")
            return
        
        # Add to appropriate priority queue
        queue = self.priority_queues[task.priority]
        await queue.put(task_id)
        
        self.logger.debug(f"Enqueued task {task_id} with priority {task.priority.name}")
    
    async def get_next_task(self) -> Optional[str]:
        """Get the next task to execute based on priority."""
        # Try queues in priority order
        for priority in [TaskPriority.URGENT, TaskPriority.HIGH, TaskPriority.MEDIUM, TaskPriority.LOW]:
            queue = self.priority_queues[priority]
            try:
                task_id = await asyncio.wait_for(queue.get(), timeout=0.1)
                return task_id
            except asyncio.TimeoutError:
                continue
        
        return None
    
    async def execute_task(self, task_id: str) -> Dict[str, Any]:
        """Execute a specific task."""
        if task_id not in self.tasks:
            raise ValueError(f"Task not found: {task_id}")
        
        task = self.tasks[task_id]
        
        # Allocate resources
        if not await self.resource_manager.allocate_resources(task):
            return {"error": "Insufficient resources", "task_id": task_id}
        
        try:
            # Update task state
            task.state = TaskState.RUNNING
            task.started_at = datetime.now()
            task.updated_at = datetime.now()
            
            self.logger.info(f"Executing task {task_id}")
            
            # Create execution context
            context = TaskExecutionContext(
                task=task,
                session_id=task.context_id,
                trace_id=task.metadata.get("trace_id")
            )
            
            # Execute the task (delegate to existing A2A agent)
            from .agent import create_crm_a2a_agent
            agent = create_crm_a2a_agent()
            
            result_content = ""
            async for update in agent.invoke(task.query, task.context_id):
                if update.get("is_task_complete", False):
                    result_content = update.get("content", "")
                    task.result = update
                    break
            
            # Update task completion
            task.state = TaskState.COMPLETED
            task.completed_at = datetime.now()
            task.execution_time_ms = (task.completed_at - task.started_at).total_seconds() * 1000
            task.updated_at = datetime.now()
            
            # Mark as completed in dependency manager
            self.dependency_manager.mark_task_completed(task_id)
            
            # Enqueue dependent tasks
            dependents = self.dependency_manager.get_dependents(task_id)
            for dependent_id in dependents:
                if dependent_id in self.tasks:
                    await self.enqueue_task(dependent_id)
            
            self.logger.info(
                f"Task {task_id} completed successfully",
                extra={
                    "task_id": task_id,
                    "execution_time_ms": task.execution_time_ms,
                    "dependents_triggered": len(dependents)
                }
            )
            
            return {"success": True, "result": task.result}
            
        except Exception as e:
            # Handle task failure
            task.state = TaskState.FAILED
            task.error = str(e)
            task.updated_at = datetime.now()
            
            # Mark as failed in dependency manager
            self.dependency_manager.mark_task_failed(task_id)
            
            self.logger.error(f"Task {task_id} failed: {e}")
            
            # Handle retries
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.state = TaskState.QUEUED
                await self.enqueue_task(task_id)
                return {"retry": True, "attempt": task.retry_count}
            
            return {"error": str(e), "task_id": task_id}
            
        finally:
            # Always release resources
            self.resource_manager.release_resources(task)
    
    async def start_workers(self, num_workers: int = 3):
        """Start background worker tasks."""
        if self._running:
            return
        
        self._running = True
        
        # Start scheduler
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        
        # Start workers
        for i in range(num_workers):
            worker_task = asyncio.create_task(self._worker_loop(f"worker-{i}"))
            self._worker_tasks.append(worker_task)
        
        self.logger.info(f"Started {num_workers} task workers and scheduler")
    
    async def stop_workers(self):
        """Stop all background workers."""
        self._running = False
        
        # Stop scheduler
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
        
        # Stop workers
        for worker_task in self._worker_tasks:
            worker_task.cancel()
        
        if self._worker_tasks:
            await asyncio.gather(*self._worker_tasks, return_exceptions=True)
        
        self._worker_tasks.clear()
        self.logger.info("Stopped all task workers")
    
    async def _scheduler_loop(self):
        """Background scheduler loop to enqueue ready tasks."""
        while self._running:
            try:
                # Find tasks ready for execution
                ready_tasks = self.dependency_manager.get_ready_tasks(self.tasks)
                
                for task_id in ready_tasks:
                    await self.enqueue_task(task_id)
                
                # Check for timed out tasks
                await self._check_timeouts()
                
                await asyncio.sleep(1)  # Check every second
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in scheduler loop: {e}")
                await asyncio.sleep(5)
    
    async def _worker_loop(self, worker_name: str):
        """Background worker loop to execute tasks."""
        while self._running:
            try:
                task_id = await self.get_next_task()
                if task_id:
                    await self.execute_task(task_id)
                else:
                    await asyncio.sleep(0.1)  # Brief pause if no tasks
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in worker {worker_name}: {e}")
                await asyncio.sleep(1)
    
    async def _check_timeouts(self):
        """Check for and handle timed out tasks."""
        current_time = datetime.now()
        
        for task_id, task in self.tasks.items():
            if (task.state == TaskState.RUNNING and 
                task.timeout_seconds and
                task.started_at and
                (current_time - task.started_at).seconds > task.timeout_seconds):
                
                self.logger.warning(f"Task {task_id} timed out")
                task.state = TaskState.FAILED
                task.error = "Task execution timeout"
                task.updated_at = current_time
                
                # Release resources
                self.resource_manager.release_resources(task)
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific task."""
        task = self.tasks.get(task_id)
        if not task:
            return None
        
        return {
            "id": task.id,
            "context_id": task.context_id,
            "state": task.state.value,
            "priority": task.priority.name,
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat(),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "execution_time_ms": task.execution_time_ms,
            "retry_count": task.retry_count,
            "dependencies": task.dependencies,
            "dependents": list(self.dependency_manager.get_dependents(task_id)),
            "resource_usage": task.allocated_resources,
            "error": task.error,
            "result": task.result
        }
    
    def get_manager_stats(self) -> Dict[str, Any]:
        """Get comprehensive task manager statistics."""
        state_counts = {}
        priority_counts = {}
        
        for task in self.tasks.values():
            # Count by state
            state = task.state.value
            state_counts[state] = state_counts.get(state, 0) + 1
            
            # Count by priority
            priority = task.priority.name
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        return {
            "total_tasks": len(self.tasks),
            "state_counts": state_counts,
            "priority_counts": priority_counts,
            "resource_usage": self.resource_manager.get_resource_usage(),
            "dependency_stats": {
                "total_dependencies": len(self.dependency_manager.dependency_graph),
                "completed_tasks": len(self.dependency_manager.completed_tasks),
                "failed_tasks": len(self.dependency_manager.failed_tasks)
            },
            "queue_sizes": {
                priority.name: queue.qsize() 
                for priority, queue in self.priority_queues.items()
            },
            "workers_running": self._running,
            "active_workers": len(self._worker_tasks)
        }
