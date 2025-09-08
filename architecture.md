# CRM Assistant Architecture: MCP and A2A Compliance

## Executive Summary

The CRM Assistant implements a hybrid architecture that combines **Model Context Protocol (MCP)** for tool integration and **Agent-to-Agent (A2A)** for multi-agent collaboration, following the patterns described in modern agentic AI architectures. This document outlines how our system aligns with these standards and provides architectural guidance for future development.

## 1. Architecture Overview

### 1.1 Core Architectural Patterns

Our system implements three complementary architectural patterns:

1. **MCP (Model Context Protocol)** - For external tool and data source integration
2. **A2A (Agent-to-Agent Protocol)** - For inter-agent communication and collaboration
3. **ADK (Agent Development Kit)** - For agent orchestration and workflow management

```
┌─────────────────────────────────────────────────────────────────┐
│                    CRM Assistant Architecture                   │
├─────────────────────────────────────────────────────────────────┤
│  A2A Layer (Agent-to-Agent Communication)                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Agent Card: CRMCoordinator                              │   │
│  │ Skills: course.profile.extract, contact.roles.infer,   │   │
│  │         hubspot.sync, lead.score.compute, etc.         │   │
│  │ Transport: JSON-RPC 2.0 + SSE                          │   │
│  └─────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│  ADK Orchestration Layer                                        │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐   │
│  │ Coordinator     │ │ Sequential      │ │ Parallel        │   │
│  │ Agents          │ │ Workflows       │ │ Fan-out         │   │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│  MCP Layer (Tool Integration)                                   │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐   │
│  │ HubSpot CRM     │ │ Web Search      │ │ Data Sources    │   │
│  │ OpenAPI Tools   │ │ Tools           │ │ (LinkedIn, etc) │   │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Current Implementation Status

✅ **A2A Implementation**: Complete with Agent Card, JSON-RPC 2.0, and SSE streaming  
✅ **MCP Integration**: Partial implementation with MCP toolsets and external tool calls  
✅ **ADK Orchestration**: Full implementation with coordinator patterns  

## 2. A2A (Agent-to-Agent) Architecture

### 2.1 Implementation Location
- **Primary A2A Module**: `crm_agent/a2a/`
- **Agent Card Builder**: `crm_agent/a2a/__main__.py`
- **A2A Agent Wrapper**: `crm_agent/a2a/agent.py`
- **HTTP Server**: `crm_agent/a2a/http_server.py`
- **Task Manager**: `crm_agent/a2a/task_manager.py`

### 2.2 Agent Card Structure

Our Agent Card exposes 5 core skills following the `<domain>.<capability>.<action>` naming convention:

```json
{
  "name": "CRMCoordinator",
  "skills": [
    {
      "id": "course.profile.extract",
      "name": "Course Profile Extraction",
      "description": "Extract comprehensive golf course profiles including management company, amenities, and key personnel."
    },
    {
      "id": "contact.roles.infer", 
      "name": "Contact Role Inference",
      "description": "Infer contact roles and decision-making tier from job titles and company context."
    },
    {
      "id": "hubspot.sync",
      "name": "HubSpot Synchronization", 
      "description": "Synchronize enriched data to HubSpot CRM with approval workflow and idempotency."
    },
    {
      "id": "lead.score.compute",
      "name": "Lead Score Computation",
      "description": "Compute fit and intent scores for leads based on configurable criteria."
    },
    {
      "id": "outreach.generate",
      "name": "Personalized Outreach Generation",
      "description": "Generate grounded, role-aware email drafts and create engagement tasks."
    }
  ]
}
```

### 2.3 Task Lifecycle Management

The A2A implementation follows the standard task lifecycle:

1. **QUEUED** → Task received and queued for processing
2. **RUNNING** → Task being executed by agent
3. **COMPLETED** → Task finished successfully with results
4. **FAILED** → Task failed with error information

### 2.4 Communication Protocols

- **JSON-RPC 2.0**: For request/response patterns
- **Server-Sent Events (SSE)**: For streaming task updates
- **HTTP Transport**: RESTful endpoints for task management

## 3. MCP (Model Context Protocol) Architecture

### 3.1 Current MCP Integration

Our system implements MCP patterns in several areas:

#### 3.1.1 MCP Toolset Integration (`crm_agent/core/base_agents.py`)
```python
# Standard MCP toolset for all CRM agents
mcp_toolset = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command='python',
            args=['-m', 'crm_fastmcp_server.stdio_server'],
        ),
        timeout=30,
    ),
)
```

#### 3.1.2 MCP Tool Calls (Found in multiple agents)
```python
def call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
    """Call a tool via the MCP server."""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "call_tool",
        "params": {
            "name": tool_name,
            "arguments": arguments or {}
        }
    }
    # Send to MCP server at localhost:8081/mcp
```

#### 3.1.3 MCP Server Implementation
- **Server Module**: `crm_fastmcp_server/`
- **STDIO Server**: `crm_fastmcp_server/stdio_server.py`
- **MCP Tools**: HubSpot CRM tools exposed via MCP protocol

### 3.2 MCP Tools Catalog

Our MCP server exposes the following tool categories:

- **HubSpot CRM Tools**: `search_companies`, `get_company_details`, `create_contact`, `update_contact`, etc.
- **Search Tools**: `web_search`, `fetch_url`
- **Data Tools**: `get_company_metadata`, `generate_company_report`
- **Communication Tools**: `send_email`, `create_task`, `notify_slack`

### 3.3 MCP vs Direct API Integration

The system uses a hybrid approach:

- **MCP Tools**: For standardized, reusable operations (web search, basic CRUD)
- **OpenAPI Tools**: For complex HubSpot operations with full schema validation
- **Direct HTTP**: For specialized integrations (LinkedIn, external APIs)

## 4. System Architecture Layers

### 4.1 Layer 1: External Integrations (MCP Layer)

```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   HubSpot CRM   │  │   Web Search    │  │  External APIs  │
│   (OpenAPI)     │  │   (MCP Tools)   │  │  (HTTP/REST)    │
└─────────────────┘  └─────────────────┘  └─────────────────┘
         │                     │                     │
         └─────────────────────┼─────────────────────┘
                               │
                    ┌─────────────────┐
                    │   MCP Server    │
                    │  (localhost:    │
                    │    8081/mcp)    │
                    └─────────────────┘
```

### 4.2 Layer 2: Agent Orchestration (ADK Layer)

```
┌─────────────────────────────────────────────────────────────────┐
│                    CRM Coordinator                              │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐   │
│  │ Lead Scoring    │ │ Outreach        │ │ Data Quality    │   │
│  │ Agent           │ │ Personalizer    │ │ Agent           │   │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │           Enrichment Pipeline (Sequential)              │   │
│  │ Query → Web → LinkedIn → Summarize → Resolve → Update  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │         Parallel Retrieval (Fan-out/Gather)            │   │
│  │    Web Search ║ LinkedIn ║ Company Data ║ Email        │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 4.3 Layer 3: A2A Communication (Protocol Layer)

```
┌─────────────────────────────────────────────────────────────────┐
│                    A2A HTTP Server                             │
│                   (localhost:10000)                            │
├─────────────────────────────────────────────────────────────────┤
│  POST /rpc          │  GET /tasks/{id}/stream  │  GET /health   │
│  (JSON-RPC 2.0)     │  (Server-Sent Events)   │  (Status)      │
├─────────────────────────────────────────────────────────────────┤
│  Methods:                                                       │
│  • agent.invoke     • task.status     • task.list              │
└─────────────────────────────────────────────────────────────────┘
```

## 5. Architectural Compliance Assessment

### 5.1 MCP Compliance

| **MCP Standard** | **Implementation Status** | **Location** |
|------------------|---------------------------|--------------|
| Client-Server Architecture | ✅ Implemented | `crm_fastmcp_server/` |
| JSON-RPC 2.0 Transport | ✅ Implemented | MCP tool calls |
| Tool Discovery | ✅ Implemented | Tool catalog |
| Resource Access | ⚠️ Partial | File/data resources |
| Prompt Templates | ❌ Not Implemented | - |

### 5.2 A2A Compliance

| **A2A Standard** | **Implementation Status** | **Location** |
|------------------|---------------------------|--------------|
| Agent Card | ✅ Implemented | `crm_agent/a2a/__main__.py` |
| Task Management | ✅ Implemented | Task lifecycle |
| JSON-RPC 2.0 | ✅ Implemented | HTTP server |
| Server-Sent Events | ✅ Implemented | Streaming updates |
| Capability Discovery | ✅ Implemented | Skills in Agent Card |
| Authentication | ⚠️ Bearer token placeholder | Auth config |

## 6. Agent Registry and Factory Pattern

### 6.1 Registry Implementation

The system implements a sophisticated registry pattern for agent management:

```python
# crm_agent/core/factory.py
class CRMAgentRegistry(AgentRegistry):
    """Registry for CRM-specific agent creation and management."""
    
    def register(self, name: str, factory: Callable, metadata: Dict):
        """Register an agent factory with metadata."""
    
    def create_agent(self, name: str, **kwargs) -> BaseAgent:
        """Create an agent instance by name."""
```

### 6.2 Registered Agent Types

The registry contains 20+ specialized agents:

- **Core Agents**: `crm_enrichment`, `company_intelligence`, `contact_intelligence`
- **Workflow Agents**: `crm_enrichment_pipeline`, `field_enrichment_workflow`
- **Specialized Agents**: `lead_scoring`, `outreach_personalizer`, `company_management_enrichment`
- **Retrieval Agents**: `crm_web_retriever`, `crm_linkedin_retriever`, `crm_company_data_retriever`

## 7. Data Flow Architecture

### 7.1 Enrichment Pipeline Flow

```
Input (Company/Contact) → Gap Detection → Parallel Retrieval → Synthesis → Quality Gate → HubSpot Update
      ↓                      ↓                ↓                ↓            ↓              ↓
   Session State      Query Planning    Web/LinkedIn/APIs   Normalization  Validation   Idempotency
```

### 7.2 A2A Request Flow

```
A2A Client → JSON-RPC Request → Task Queue → Agent Execution → SSE Streaming → Final Response
     ↓             ↓                ↓             ↓               ↓               ↓
External Agent  HTTP Server    Task Manager   CRM Coordinator  Progress Updates  Results
```

## 8. Observability and Production Readiness

### 8.1 Observability Implementation (Phase 9)

- **Structured Logging**: `crm_agent/core/observability.py`
- **Trace Context**: End-to-end tracing with `trace_id`
- **Session Management**: Pluggable session store (in-memory, Redis)
- **Audit Trail**: Before/after states with evidence URLs

### 8.2 Idempotency and Reliability

- **Idempotency Keys**: All HubSpot writes are idempotent
- **Retry Logic**: Configurable retry with exponential backoff
- **State Recovery**: Session persistence across process restarts

## 9. Security and Policy Enforcement

### 9.1 Policy Framework (Phase 8)

- **Web Scraping Policy**: Robots.txt compliance, rate limiting
- **Data Privacy**: PII detection and tagging
- **Content Filtering**: Paywall bypass prevention
- **Quality Gates**: Confidence thresholds for automated updates

### 9.2 Authentication and Authorization

- **HubSpot**: Private App tokens with scoped permissions
- **A2A**: Bearer token authentication (configurable)
- **MCP**: Local STDIO connection (secure by default)

## 10. Architectural Recommendations

### 10.1 MCP Enhancements

1. **Implement Prompt Templates**: Add MCP prompt templates for common operations
2. **Resource Management**: Implement MCP resources for file and data access
3. **Tool Versioning**: Add version management for MCP tools
4. **Connection Pooling**: Optimize MCP server connections

### 10.2 A2A Enhancements

1. **Authentication**: Implement production-ready authentication
2. **Rate Limiting**: Add request rate limiting and quotas
3. **Monitoring**: Add metrics and health monitoring
4. **Documentation**: Auto-generate API documentation from Agent Card

### 10.3 Integration Improvements

1. **Unified Tool Interface**: Standardize tool calling across MCP and OpenAPI
2. **Schema Validation**: Add comprehensive input/output validation
3. **Error Handling**: Implement consistent error handling patterns
4. **Testing**: Add integration tests for MCP and A2A protocols

## 11. Future Architecture Evolution

### 11.1 Multi-Domain A2A Services

Following the roadmap pattern, future A2A services should follow:

```
<domain>_agent/
├── a2a/
│   ├── __main__.py      # Agent Card builder
│   ├── agent.py         # A2A wrapper
│   ├── http_server.py   # JSON-RPC + SSE server
│   └── task_manager.py  # Task lifecycle management
├── agents/              # Domain-specific agents
├── core/                # Shared infrastructure
└── configs/             # Configuration files
```

### 11.2 Protocol Standardization

1. **Unified Protocol Layer**: Abstract MCP and A2A protocols behind common interface
2. **Service Discovery**: Implement automatic service discovery for A2A agents
3. **Load Balancing**: Add load balancing for high-availability deployments
4. **Message Queuing**: Implement async message queuing for long-running tasks

## 12. Conclusion

The CRM Assistant successfully implements a hybrid MCP/A2A architecture that provides:

- **MCP Integration**: For standardized tool access and external system integration
- **A2A Compliance**: For inter-agent communication and collaboration
- **Production Readiness**: With observability, idempotency, and policy enforcement
- **Scalability**: Through modular agent registry and factory patterns

This architecture positions the system for future growth while maintaining compliance with emerging agentic AI standards.

---

**Document Version**: 1.0  
**Last Updated**: January 2025  
**Compliance Standards**: MCP 1.0, A2A 1.0, ADK 2.0+
