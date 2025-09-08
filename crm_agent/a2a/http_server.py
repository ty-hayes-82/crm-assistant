#!/usr/bin/env python3
"""
A2A HTTP Server implementation with JSON-RPC 2.0 and Server-Sent Events (SSE).
Provides HTTP transport for the CRM A2A agent with standardized lifecycle management.
"""

import asyncio
import json
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, Optional, AsyncGenerator
from dataclasses import dataclass, asdict
from enum import Enum

try:
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.responses import StreamingResponse
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FastAPI = None
    HTTPException = None
    Request = None
    StreamingResponse = None
    CORSMiddleware = None
    uvicorn = None
    FASTAPI_AVAILABLE = False

from .task_manager import CRMAgentTaskManager
from .agent import create_crm_a2a_agent


# Task lifecycle states
class TaskState(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TaskInfo:
    """Task information for lifecycle tracking."""
    id: str
    context_id: str
    state: TaskState
    created_at: datetime
    updated_at: datetime
    query: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class JsonRpcRequest:
    """JSON-RPC 2.0 request structure."""
    jsonrpc: str
    method: str
    params: Dict[str, Any]
    id: Optional[str] = None


@dataclass
class JsonRpcResponse:
    """JSON-RPC 2.0 response structure."""
    jsonrpc: str
    id: Optional[str]
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None


class CRMA2AHttpServer:
    """A2A HTTP Server for CRM agent with JSON-RPC and SSE support."""
    
    def __init__(self, host: str = "localhost", port: int = 10000):
        if not FASTAPI_AVAILABLE:
            raise ImportError("FastAPI not available. Install with: pip install fastapi uvicorn")
        
        self.host = host
        self.port = port
        self.app = FastAPI(
            title="CRM A2A Agent Server",
            description="A2A HTTP server for CRM agent with JSON-RPC 2.0 and SSE support",
            version="1.0.0"
        )
        
        # Initialize observability system (Phase 9)
        from ..core.observability import get_logger, TraceContext
        self.logger = get_logger("a2a_http_server")
        self.TraceContext = TraceContext
        
        # Add CORS middleware for cross-origin requests
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Task storage (in production, use persistent storage)
        self.tasks: Dict[str, TaskInfo] = {}
        self.task_manager = CRMAgentTaskManager()
        
        # Set up routes
        self._setup_routes()
        
        # Logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _setup_routes(self):
        """Set up HTTP routes for the A2A server."""
        
        @self.app.post("/rpc")
        async def json_rpc_endpoint(request: Request):
            """JSON-RPC 2.0 endpoint for A2A requests."""
            try:
                body = await request.json()
                rpc_request = JsonRpcRequest(**body)
                
                if rpc_request.jsonrpc != "2.0":
                    return JsonRpcResponse(
                        jsonrpc="2.0",
                        id=rpc_request.id,
                        error={"code": -32600, "message": "Invalid Request"}
                    )
                
                # Handle different RPC methods
                if rpc_request.method == "agent.invoke":
                    return await self._handle_agent_invoke(rpc_request)
                elif rpc_request.method == "task.status":
                    return await self._handle_task_status(rpc_request)
                elif rpc_request.method == "task.list":
                    return await self._handle_task_list(rpc_request)
                else:
                    return JsonRpcResponse(
                        jsonrpc="2.0",
                        id=rpc_request.id,
                        error={"code": -32601, "message": "Method not found"}
                    )
                    
            except Exception as e:
                self.logger.error(f"JSON-RPC error: {e}")
                return JsonRpcResponse(
                    jsonrpc="2.0",
                    id=None,
                    error={"code": -32603, "message": "Internal error"}
                )
        
        @self.app.get("/tasks/{task_id}/stream")
        async def task_stream_endpoint(task_id: str):
            """Server-Sent Events endpoint for task progress streaming."""
            if task_id not in self.tasks:
                raise HTTPException(status_code=404, detail="Task not found")
            
            return StreamingResponse(
                self._stream_task_updates(task_id),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                }
            )
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}
        
        @self.app.get("/agent-card")
        async def agent_card_endpoint():
            """Return the A2A Agent Card."""
            from .__main__ import build_agent_card
            return build_agent_card(host=self.host, port=self.port)
    
    async def _handle_agent_invoke(self, request: JsonRpcRequest) -> JsonRpcResponse:
        """Handle agent.invoke JSON-RPC method."""
        try:
            params = request.params
            query = params.get("query", "")
            session_id = params.get("session_id") or str(uuid.uuid4())
            
            # Create task
            task_id = str(uuid.uuid4())
            context_id = session_id
            
            task = TaskInfo(
                id=task_id,
                context_id=context_id,
                state=TaskState.QUEUED,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                query=query
            )
            
            self.tasks[task_id] = task
            
            # Start task execution in background
            asyncio.create_task(self._execute_task(task_id, query, session_id))
            
            return JsonRpcResponse(
                jsonrpc="2.0",
                id=request.id,
                result={
                    "task_id": task_id,
                    "context_id": context_id,
                    "state": TaskState.QUEUED.value,
                    "stream_url": f"http://{self.host}:{self.port}/tasks/{task_id}/stream"
                }
            )
            
        except Exception as e:
            self.logger.error(f"Agent invoke error: {e}")
            return JsonRpcResponse(
                jsonrpc="2.0",
                id=request.id,
                error={"code": -32603, "message": f"Internal error: {str(e)}"}
            )
    
    async def _handle_task_status(self, request: JsonRpcRequest) -> JsonRpcResponse:
        """Handle task.status JSON-RPC method."""
        try:
            task_id = request.params.get("task_id")
            if not task_id or task_id not in self.tasks:
                return JsonRpcResponse(
                    jsonrpc="2.0",
                    id=request.id,
                    error={"code": -32602, "message": "Task not found"}
                )
            
            task = self.tasks[task_id]
            return JsonRpcResponse(
                jsonrpc="2.0",
                id=request.id,
                result=asdict(task)
            )
            
        except Exception as e:
            return JsonRpcResponse(
                jsonrpc="2.0",
                id=request.id,
                error={"code": -32603, "message": f"Internal error: {str(e)}"}
            )
    
    async def _handle_task_list(self, request: JsonRpcRequest) -> JsonRpcResponse:
        """Handle task.list JSON-RPC method."""
        try:
            # Optional filtering by state
            state_filter = request.params.get("state")
            
            tasks = list(self.tasks.values())
            if state_filter:
                tasks = [t for t in tasks if t.state == state_filter]
            
            return JsonRpcResponse(
                jsonrpc="2.0",
                id=request.id,
                result={"tasks": [asdict(task) for task in tasks]}
            )
            
        except Exception as e:
            return JsonRpcResponse(
                jsonrpc="2.0",
                id=request.id,
                error={"code": -32603, "message": f"Internal error: {str(e)}"}
            )
    
    async def _execute_task(self, task_id: str, query: str, session_id: str):
        """Execute CRM agent task asynchronously."""
        try:
            task = self.tasks[task_id]
            task.state = TaskState.RUNNING
            task.updated_at = datetime.now()
            
            # Create A2A agent and execute query
            agent = create_crm_a2a_agent()
            
            result_content = ""
            async for update in agent.invoke(query, session_id):
                if update.get("is_task_complete", False):
                    # Task completed
                    task.state = TaskState.COMPLETED
                    task.result = update
                    result_content = update.get("content", "")
                    break
                else:
                    # Progress update - could emit SSE here
                    pass
            
            task.updated_at = datetime.now()
            self.logger.info(f"Task {task_id} completed successfully")
            
        except Exception as e:
            # Task failed
            task = self.tasks[task_id]
            task.state = TaskState.FAILED
            task.error = str(e)
            task.updated_at = datetime.now()
            self.logger.error(f"Task {task_id} failed: {e}")
    
    async def _stream_task_updates(self, task_id: str) -> AsyncGenerator[str, None]:
        """Stream task updates via Server-Sent Events."""
        last_state = None
        
        while True:
            task = self.tasks.get(task_id)
            if not task:
                yield f"data: {json.dumps({'error': 'Task not found'})}\n\n"
                break
            
            # Send update if state changed
            if task.state != last_state:
                event_data = {
                    "task_id": task_id,
                    "state": task.state.value,
                    "updated_at": task.updated_at.isoformat(),
                }
                
                if task.state == TaskState.COMPLETED and task.result:
                    event_data["result"] = task.result
                elif task.state == TaskState.FAILED and task.error:
                    event_data["error"] = task.error
                
                yield f"data: {json.dumps(event_data)}\n\n"
                last_state = task.state
            
            # Break if task is complete
            if task.state in [TaskState.COMPLETED, TaskState.FAILED]:
                break
            
            # Wait before next check
            await asyncio.sleep(1)
    
    def run(self):
        """Start the HTTP server."""
        self.logger.info(f"Starting CRM A2A HTTP server on {self.host}:{self.port}")
        uvicorn.run(self.app, host=self.host, port=self.port)


def create_crm_a2a_http_server(host: str = "localhost", port: int = 10000) -> CRMA2AHttpServer:
    """Factory function to create CRM A2A HTTP server."""
    return CRMA2AHttpServer(host=host, port=port)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="CRM A2A HTTP Server")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=10000, help="Port to bind to")
    
    args = parser.parse_args()
    
    server = create_crm_a2a_http_server(host=args.host, port=args.port)
    server.run()
