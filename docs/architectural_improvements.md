# Architectural Improvements: MCP and A2A Best Practices

## Executive Summary

Based on the analysis of your current architecture against the MCP and A2A standards from the provided article, here are specific recommendations to enhance your system's compliance and effectiveness.

## 1. MCP (Model Context Protocol) Improvements

### 1.1 Current State Assessment

✅ **What's Working Well:**
- MCP toolset integration in `base_agents.py`
- JSON-RPC 2.0 communication pattern
- MCP server implementation (`crm_fastmcp_server/`)
- Tool discovery and registration

⚠️ **Areas for Improvement:**

### 1.2 Implement Missing MCP Components

#### A. MCP Resources (File-like Data Access)
Your current implementation focuses on tools but lacks MCP resources. Add resource support:

```python
# crm_agent/core/mcp_resources.py
from mcp import Resource

class HubSpotDataResource(Resource):
    """Expose HubSpot data as MCP resources."""
    
    def __init__(self):
        super().__init__(
            uri="hubspot://companies",
            name="HubSpot Companies",
            description="Access to HubSpot company records",
            mimeType="application/json"
        )
    
    async def read(self) -> str:
        """Return company data as JSON string."""
        # Implementation here
        pass
```

#### B. MCP Prompts (Pre-written Templates)
Add prompt templates for common CRM operations:

```python
# crm_agent/core/mcp_prompts.py
from mcp import Prompt

COMPANY_ENRICHMENT_PROMPT = Prompt(
    name="enrich_company",
    description="Template for company data enrichment",
    template="""
    Enrich the following company record with accurate, verifiable information:
    
    Company: {company_name}
    Domain: {domain}
    Current Data: {current_data}
    
    Focus on: {focus_areas}
    
    Requirements:
    - Include source URLs for all claims
    - Verify information recency
    - Follow data quality standards
    """
)
```

#### C. Standardize MCP Client-Server Architecture
Currently, you have mixed patterns. Standardize to proper MCP architecture:

```python
# crm_agent/core/mcp_client.py
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters

class StandardizedMCPClient:
    """Standardized MCP client following protocol specifications."""
    
    def __init__(self):
        self.server_params = StdioServerParameters(
            command="python",
            args=["-m", "crm_fastmcp_server.stdio_server"]
        )
        self.session = None
    
    async def initialize(self):
        """Initialize MCP connection with proper lifecycle."""
        # Implement proper MCP initialization sequence
        pass
```

### 1.3 Enhance Tool Standardization

Replace the current mixed approach with standardized MCP tools:

```python
# crm_agent/tools/mcp_hubspot_tools.py
from mcp import Tool

class HubSpotCompanyTool(Tool):
    """Standardized MCP tool for HubSpot company operations."""
    
    name = "hubspot_company_update"
    description = "Update HubSpot company with enriched data"
    
    input_schema = {
        "type": "object",
        "properties": {
            "company_id": {"type": "string"},
            "properties": {"type": "object"},
            "source_urls": {"type": "array", "items": {"type": "string"}}
        },
        "required": ["company_id", "properties", "source_urls"]
    }
```

## 2. A2A (Agent-to-Agent) Enhancements

### 2.1 Current State Assessment

✅ **What's Excellent:**
- Complete A2A implementation with Agent Card
- JSON-RPC 2.0 + SSE streaming
- Task lifecycle management
- Proper skill definitions

### 2.2 Enhance Agent Card Metadata

Expand your Agent Card with richer metadata following A2A best practices:

```python
# crm_agent/a2a/__main__.py - Enhanced Agent Card
def build_enhanced_agent_card(host: str = "localhost", port: int = 10000):
    return {
        "name": "CRMCoordinator",
        "version": "1.0.0",
        "description": "A2A-compatible CRM Coordinator agent with expanded skills",
        "url": f"http://{host}:{port}/",
        
        # Enhanced metadata
        "vendor": "Swoop Golf",
        "category": "crm_automation",
        "tags": ["crm", "hubspot", "golf", "enrichment"],
        "license": "proprietary",
        "documentation_url": "https://github.com/your-org/crm-assistant/docs",
        
        # Capability negotiation
        "capabilities": {
            "streaming": True,
            "batch_processing": True,
            "async_tasks": True,
            "rate_limiting": {"requests_per_minute": 60},
            "max_concurrent_tasks": 5
        },
        
        # Enhanced authentication
        "auth": {
            "type": "bearer",
            "description": "Requires HubSpot Private App access token",
            "environment_variable": "PRIVATE_APP_ACCESS_TOKEN",
            "scopes": ["crm.objects.companies.write", "crm.objects.contacts.write"]
        },
        
        # Service level agreements
        "sla": {
            "response_time_ms": 5000,
            "availability": "99.9%",
            "support_contact": "support@swoopgolf.com"
        },
        
        # Enhanced skills with I/O schemas
        "skills": [
            {
                "id": "course.profile.extract",
                "name": "Course Profile Extraction",
                "description": "Extract comprehensive golf course profiles",
                "version": "1.0.0",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "company_name": {"type": "string"},
                        "domain": {"type": "string", "format": "uri"},
                        "focus_areas": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["company_name"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "profile": {"type": "object"},
                        "confidence_score": {"type": "number", "minimum": 0, "maximum": 1},
                        "source_urls": {"type": "array", "items": {"type": "string"}}
                    }
                },
                "examples": [
                    {
                        "input": {"company_name": "Pebble Beach Golf Links"},
                        "output": {"profile": {"management_company": "Pebble Beach Company"}}
                    }
                ]
            }
            # ... other skills with full schemas
        ]
    }
```

### 2.3 Implement Advanced A2A Features

#### A. Agent Discovery and Registry
```python
# crm_agent/a2a/discovery.py
class A2AAgentRegistry:
    """Registry for discovering and managing A2A agents."""
    
    def __init__(self):
        self.agents = {}
        self.capabilities_index = {}
    
    def register_agent(self, agent_card: dict):
        """Register an agent and index its capabilities."""
        agent_id = agent_card["name"]
        self.agents[agent_id] = agent_card
        
        # Index capabilities for discovery
        for skill in agent_card.get("skills", []):
            capability = skill["id"]
            if capability not in self.capabilities_index:
                self.capabilities_index[capability] = []
            self.capabilities_index[capability].append(agent_id)
    
    def find_agents_by_capability(self, capability: str) -> List[str]:
        """Find agents that provide a specific capability."""
        return self.capabilities_index.get(capability, [])
```

#### B. Enhanced Task Management
```python
# crm_agent/a2a/enhanced_task_manager.py
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any
import asyncio

class TaskPriority(Enum):
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
    dependencies: List[str]  # Task IDs this task depends on
    timeout_seconds: Optional[int] = None
    retry_count: int = 0
    max_retries: int = 3
    metadata: Dict[str, Any] = None

class EnhancedTaskManager:
    """Enhanced task manager with priority queues and dependencies."""
    
    def __init__(self):
        self.priority_queues = {
            TaskPriority.URGENT: asyncio.Queue(),
            TaskPriority.HIGH: asyncio.Queue(),
            TaskPriority.MEDIUM: asyncio.Queue(),
            TaskPriority.LOW: asyncio.Queue()
        }
        self.dependency_graph = {}
        
    async def enqueue_task(self, task: EnhancedTaskInfo):
        """Enqueue task based on priority and dependencies."""
        if task.dependencies:
            # Check if dependencies are satisfied
            await self._wait_for_dependencies(task)
        
        queue = self.priority_queues[task.priority]
        await queue.put(task)
```

### 2.4 Implement A2A Security Best Practices

```python
# crm_agent/a2a/security.py
import jwt
from typing import Optional

class A2ASecurityManager:
    """Security manager for A2A communications."""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
    
    def generate_agent_token(self, agent_id: str, capabilities: List[str]) -> str:
        """Generate JWT token for agent authentication."""
        payload = {
            "agent_id": agent_id,
            "capabilities": capabilities,
            "iss": "crm-coordinator",
            "exp": datetime.utcnow() + timedelta(hours=24)
        }
        return jwt.encode(payload, self.secret_key, algorithm="HS256")
    
    def validate_agent_token(self, token: str) -> Optional[Dict]:
        """Validate agent authentication token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            return payload
        except jwt.InvalidTokenError:
            return None
```

## 3. Unified Protocol Architecture

### 3.1 Create Protocol Abstraction Layer

```python
# crm_agent/core/protocol_layer.py
from abc import ABC, abstractmethod
from typing import Any, Dict, AsyncIterator

class ProtocolClient(ABC):
    """Abstract protocol client for unified tool access."""
    
    @abstractmethod
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool through the protocol."""
        pass
    
    @abstractmethod
    async def list_capabilities(self) -> List[str]:
        """List available capabilities."""
        pass

class MCPProtocolClient(ProtocolClient):
    """MCP protocol client implementation."""
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        # Use standardized MCP client
        pass

class A2AProtocolClient(ProtocolClient):
    """A2A protocol client implementation."""
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        # Use A2A JSON-RPC client
        pass

class UnifiedProtocolManager:
    """Manages multiple protocol clients with automatic routing."""
    
    def __init__(self):
        self.clients = {
            "mcp": MCPProtocolClient(),
            "a2a": A2AProtocolClient()
        }
        self.capability_routing = {}  # Map capabilities to protocols
    
    async def call_capability(self, capability: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Route capability call to appropriate protocol."""
        protocol = self.capability_routing.get(capability, "mcp")
        client = self.clients[protocol]
        return await client.call_tool(capability, arguments)
```

## 4. Configuration and Deployment Improvements

### 4.1 Environment-Specific Configuration

```python
# crm_agent/core/config.py
from pydantic import BaseSettings
from typing import Optional, List

class MCPConfig(BaseSettings):
    """MCP-specific configuration."""
    server_command: str = "python"
    server_args: List[str] = ["-m", "crm_fastmcp_server.stdio_server"]
    timeout_seconds: int = 30
    max_connections: int = 10
    
class A2AConfig(BaseSettings):
    """A2A-specific configuration."""
    host: str = "localhost"
    port: int = 10000
    max_concurrent_tasks: int = 5
    rate_limit_rpm: int = 60
    auth_secret_key: Optional[str] = None
    
class CRMConfig(BaseSettings):
    """Main CRM configuration."""
    mcp: MCPConfig = MCPConfig()
    a2a: A2AConfig = A2AConfig()
    hubspot_token: str
    environment: str = "development"
    
    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"
```

### 4.2 Docker Deployment Configuration

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application
COPY . .

# Expose A2A server port
EXPOSE 10000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:10000/health || exit 1

# Start A2A server
CMD ["python", "-m", "crm_agent.a2a.http_server"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  crm-coordinator:
    build: .
    ports:
      - "10000:10000"
    environment:
      - PRIVATE_APP_ACCESS_TOKEN=${HUBSPOT_TOKEN}
      - A2A__HOST=0.0.0.0
      - A2A__PORT=10000
    volumes:
      - ./configs:/app/configs:ro
    restart: unless-stopped
    
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    restart: unless-stopped
```

## 5. Testing and Validation Improvements

### 5.1 MCP Protocol Tests

```python
# tests/protocol/test_mcp_compliance.py
import pytest
from crm_agent.core.mcp_client import StandardizedMCPClient

@pytest.mark.asyncio
async def test_mcp_initialization_sequence():
    """Test proper MCP initialization sequence."""
    client = StandardizedMCPClient()
    
    # Test initialization request/response
    await client.initialize()
    assert client.session is not None
    
    # Test capabilities exchange
    capabilities = await client.get_server_capabilities()
    assert "tools" in capabilities
    
@pytest.mark.asyncio
async def test_mcp_tool_call_format():
    """Test MCP tool call follows JSON-RPC 2.0 format."""
    client = StandardizedMCPClient()
    await client.initialize()
    
    # Test tool call format
    result = await client.call_tool("search_companies", {"query": "test"})
    assert "result" in result or "error" in result
```

### 5.2 A2A Protocol Tests

```python
# tests/protocol/test_a2a_compliance.py
import pytest
import httpx
from crm_agent.a2a.http_server import create_crm_a2a_http_server

@pytest.mark.asyncio
async def test_agent_card_format():
    """Test Agent Card follows A2A specification."""
    from crm_agent.a2a.__main__ import build_agent_card
    
    card = build_agent_card()
    
    # Required A2A fields
    assert "name" in card
    assert "skills" in card
    assert "capabilities" in card
    
    # Validate skill format
    for skill in card["skills"]:
        assert "id" in skill
        assert "name" in skill
        assert "description" in skill

@pytest.mark.asyncio
async def test_json_rpc_compliance():
    """Test JSON-RPC 2.0 compliance."""
    server = create_crm_a2a_http_server(port=10001)
    
    async with httpx.AsyncClient() as client:
        response = await client.post("http://localhost:10001/rpc", json={
            "jsonrpc": "2.0",
            "method": "agent.invoke",
            "params": {"query": "test"},
            "id": 1
        })
        
        result = response.json()
        assert result["jsonrpc"] == "2.0"
        assert "result" in result or "error" in result
        assert result["id"] == 1
```

## 6. Implementation Priority

### Phase 1: Critical Improvements (Week 1)
1. ✅ Standardize MCP client-server architecture
2. ✅ Enhance Agent Card with full schemas
3. ✅ Implement unified protocol layer
4. ✅ Add comprehensive testing

### Phase 2: Advanced Features (Week 2)
1. ✅ Implement MCP resources and prompts
2. ✅ Add A2A security and authentication
3. ✅ Create agent discovery system
4. ✅ Enhanced task management with priorities

### Phase 3: Production Readiness (Week 3)
1. ✅ Docker deployment configuration
2. ✅ Monitoring and observability
3. ✅ Load balancing and scaling
4. ✅ Documentation and examples

## 7. Success Metrics

- **MCP Compliance**: 100% protocol specification adherence
- **A2A Compliance**: Full Agent Card and task lifecycle support
- **Performance**: <500ms average response time for tool calls
- **Reliability**: 99.9% uptime with proper error handling
- **Interoperability**: Works with other MCP/A2A compliant systems

---

**Next Steps**: Begin with Phase 1 implementations, focusing on standardizing the MCP client-server architecture and enhancing the Agent Card metadata.
