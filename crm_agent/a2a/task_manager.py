"""
A2A Task Manager for the CRM agent, implementing the execute() bridge
from the A2A server into the ADK agent, per Google's guide.
"""

from typing import Any

try:
    from a2a.server.task_manager import AgentExecutor, RequestContext, EventQueue, TaskUpdater
    from a2a.server.task_protocols import TaskState, new_task, new_agent_text_message
except Exception:  # If A2A libs not installed, define shims to avoid crashes during import
    AgentExecutor = object  # type: ignore
    def RequestContext(*args: Any, **kwargs: Any) -> Any: return None  # type: ignore
    def EventQueue(*args: Any, **kwargs: Any) -> Any: return None  # type: ignore
    def TaskUpdater(*args: Any, **kwargs: Any) -> Any: return None  # type: ignore
    class TaskState:  # type: ignore
        working = "working"
        completed = "completed"
        failed = "failed"
    def new_task(message: Any) -> Any: return type("Task", (), {"id": "task", "contextId": "ctx"})()  # type: ignore
    def new_agent_text_message(text: str, context_id: str, task_id: str) -> Any: return {"text": text}  # type: ignore

from .agent import CRMA2AAgent


class CRMAgentTaskManager(AgentExecutor):
    def __init__(self) -> None:
        self.agent = CRMA2AAgent()

    async def execute(self, context: "RequestContext", event_queue: "EventQueue") -> None:
        query = context.get_user_input() if hasattr(context, "get_user_input") else ""
        task = context.current_task or new_task(getattr(context, "message", None))
        await event_queue.enqueue_event(task)  # type: ignore[attr-defined]
        updater = TaskUpdater(event_queue, task.id, task.contextId)

        try:
            async for item in self.agent.invoke(query, task.contextId):
                if not item.get("is_task_complete", False):
                    await updater.update_status(
                        TaskState.working,
                        new_agent_text_message(item.get("updates", "Processing..."), task.contextId, task.id),
                    )
                else:
                    message = new_agent_text_message(item.get("content", "Done"), task.contextId, task.id)
                    await updater.update_status(TaskState.completed, message)
                    break
        except Exception as e:
            error_message = f"CRM A2A agent error: {str(e)}"
            await updater.update_status(
                TaskState.failed,
                new_agent_text_message(error_message, task.contextId, task.id),
            )
            raise


