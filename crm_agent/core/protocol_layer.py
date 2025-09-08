"""
Unified Protocol Abstraction Layer for MCP and A2A.
Provides a common interface for tool access across different protocols.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, AsyncIterator
from enum import Enum
import asyncio
import httpx
from dataclasses import dataclass

from .observability import get_logger


class ProtocolType(Enum):
    """Supported protocol types."""
    MCP = "mcp"
    A2A = "a2a"
    HTTP = "http"
    OPENAPI = "openapi"


@dataclass
class ProtocolCapability:
    """Represents a capability available through a protocol."""
    name: str
    description: str
    protocol: ProtocolType
    endpoint: Optional[str] = None
    schema: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ProtocolResponse:
    """Standard response format across protocols."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    protocol: Optional[ProtocolType] = None
    metadata: Optional[Dict[str, Any]] = None


class ProtocolClient(ABC):
    """Abstract protocol client for unified tool access."""
    
    def __init__(self, protocol_type: ProtocolType):
        self.protocol_type = protocol_type
        self.logger = get_logger(f"protocol_client_{protocol_type.value}")
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the protocol client."""
        pass
    
    @abstractmethod
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> ProtocolResponse:
        """Call a tool through the protocol."""
        pass
    
    @abstractmethod
    async def list_capabilities(self) -> List[ProtocolCapability]:
        """List available capabilities."""
        pass
    
    @abstractmethod
    async def get_capability(self, name: str) -> Optional[ProtocolCapability]:
        """Get details about a specific capability."""
        pass
    
    async def close(self):
        """Close the protocol client."""
        pass


class MCPProtocolClient(ProtocolClient):
    """MCP protocol client implementation."""
    
    def __init__(self):
        super().__init__(ProtocolType.MCP)
        self._mcp_client = None
    
    async def initialize(self) -> bool:
        """Initialize MCP client connection."""
        try:
            from .mcp_client import get_mcp_client
            self._mcp_client = await get_mcp_client()
            self.logger.info("MCP protocol client initialized")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize MCP client: {e}")
            return False
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> ProtocolResponse:
        """Call an MCP tool."""
        if not self._mcp_client:
            await self.initialize()
        
        try:
            result = await self._mcp_client.call_tool(tool_name, arguments)
            
            if "error" in result:
                return ProtocolResponse(
                    success=False,
                    error=result["error"],
                    protocol=ProtocolType.MCP
                )
            
            return ProtocolResponse(
                success=True,
                data=result,
                protocol=ProtocolType.MCP
            )
            
        except Exception as e:
            self.logger.error(f"MCP tool call failed: {tool_name} - {e}")
            return ProtocolResponse(
                success=False,
                error=str(e),
                protocol=ProtocolType.MCP
            )
    
    async def list_capabilities(self) -> List[ProtocolCapability]:
        """List MCP tools as capabilities."""
        if not self._mcp_client:
            await self.initialize()
        
        try:
            tools = await self._mcp_client.list_tools()
            capabilities = []
            
            for tool in tools:
                capability = ProtocolCapability(
                    name=tool["name"],
                    description=tool.get("description", ""),
                    protocol=ProtocolType.MCP,
                    schema=tool.get("inputSchema"),
                    metadata={"tool_data": tool}
                )
                capabilities.append(capability)
            
            return capabilities
            
        except Exception as e:
            self.logger.error(f"Failed to list MCP capabilities: {e}")
            return []
    
    async def get_capability(self, name: str) -> Optional[ProtocolCapability]:
        """Get MCP tool details."""
        capabilities = await self.list_capabilities()
        for capability in capabilities:
            if capability.name == name:
                return capability
        return None


class A2AProtocolClient(ProtocolClient):
    """A2A protocol client implementation."""
    
    def __init__(self, base_url: str = "http://localhost:10000"):
        super().__init__(ProtocolType.A2A)
        self.base_url = base_url.rstrip("/")
        self._agent_card = None
    
    async def initialize(self) -> bool:
        """Initialize A2A client by fetching agent card."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/agent-card")
                response.raise_for_status()
                self._agent_card = response.json()
            
            self.logger.info(f"A2A protocol client initialized for {self._agent_card['name']}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize A2A client: {e}")
            return False
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> ProtocolResponse:
        """Call an A2A skill."""
        if not self._agent_card:
            await self.initialize()
        
        try:
            # Make JSON-RPC request
            rpc_request = {
                "jsonrpc": "2.0",
                "method": "agent.invoke",
                "params": {
                    "skill": tool_name,
                    "arguments": arguments
                },
                "id": 1
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/rpc",
                    json=rpc_request,
                    timeout=30.0
                )
                response.raise_for_status()
                
                result = response.json()
                
                if "error" in result:
                    return ProtocolResponse(
                        success=False,
                        error=result["error"]["message"],
                        protocol=ProtocolType.A2A
                    )
                
                return ProtocolResponse(
                    success=True,
                    data=result.get("result"),
                    protocol=ProtocolType.A2A
                )
                
        except Exception as e:
            self.logger.error(f"A2A skill call failed: {tool_name} - {e}")
            return ProtocolResponse(
                success=False,
                error=str(e),
                protocol=ProtocolType.A2A
            )
    
    async def list_capabilities(self) -> List[ProtocolCapability]:
        """List A2A skills as capabilities."""
        if not self._agent_card:
            await self.initialize()
        
        capabilities = []
        
        if self._agent_card:
            for skill in self._agent_card.get("skills", []):
                capability = ProtocolCapability(
                    name=skill["id"],
                    description=skill.get("description", ""),
                    protocol=ProtocolType.A2A,
                    schema={
                        "input": skill.get("input_schema"),
                        "output": skill.get("output_schema")
                    },
                    metadata={"skill_data": skill}
                )
                capabilities.append(capability)
        
        return capabilities
    
    async def get_capability(self, name: str) -> Optional[ProtocolCapability]:
        """Get A2A skill details."""
        capabilities = await self.list_capabilities()
        for capability in capabilities:
            if capability.name == name:
                return capability
        return None


class HTTPProtocolClient(ProtocolClient):
    """HTTP/REST protocol client implementation."""
    
    def __init__(self, base_url: str, auth_headers: Optional[Dict[str, str]] = None):
        super().__init__(ProtocolType.HTTP)
        self.base_url = base_url.rstrip("/")
        self.auth_headers = auth_headers or {}
    
    async def initialize(self) -> bool:
        """Initialize HTTP client."""
        self.logger.info(f"HTTP protocol client initialized for {self.base_url}")
        return True
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> ProtocolResponse:
        """Make HTTP request."""
        try:
            # Map tool name to HTTP method and path
            method = arguments.get("method", "POST")
            path = arguments.get("path", f"/{tool_name}")
            data = arguments.get("data", {})
            params = arguments.get("params", {})
            
            url = f"{self.base_url}{path}"
            
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=method,
                    url=url,
                    json=data if method in ["POST", "PUT", "PATCH"] else None,
                    params=params,
                    headers=self.auth_headers,
                    timeout=30.0
                )
                
                response.raise_for_status()
                
                # Try to parse JSON, fallback to text
                try:
                    result_data = response.json()
                except:
                    result_data = response.text
                
                return ProtocolResponse(
                    success=True,
                    data=result_data,
                    protocol=ProtocolType.HTTP,
                    metadata={
                        "status_code": response.status_code,
                        "headers": dict(response.headers)
                    }
                )
                
        except Exception as e:
            self.logger.error(f"HTTP request failed: {tool_name} - {e}")
            return ProtocolResponse(
                success=False,
                error=str(e),
                protocol=ProtocolType.HTTP
            )
    
    async def list_capabilities(self) -> List[ProtocolCapability]:
        """List HTTP endpoints as capabilities."""
        # This would typically be populated from OpenAPI spec or configuration
        return []
    
    async def get_capability(self, name: str) -> Optional[ProtocolCapability]:
        """Get HTTP endpoint details."""
        return None


class OpenAPIProtocolClient(ProtocolClient):
    """OpenAPI protocol client implementation."""
    
    def __init__(self, spec_url: str = None, spec_data: Dict = None):
        super().__init__(ProtocolType.OPENAPI)
        self.spec_url = spec_url
        self.spec_data = spec_data
        self._openapi_tool = None
    
    async def initialize(self) -> bool:
        """Initialize OpenAPI client."""
        try:
            from ..core.factory import create_hubspot_openapi_tool
            self._openapi_tool = create_hubspot_openapi_tool()
            self.logger.info("OpenAPI protocol client initialized")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize OpenAPI client: {e}")
            return False
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> ProtocolResponse:
        """Call OpenAPI operation."""
        if not self._openapi_tool:
            await self.initialize()
        
        try:
            # Extract OpenAPI operation parameters
            path_params = arguments.get("path_params", {})
            query_params = arguments.get("query_params", {})
            body = arguments.get("body", {})
            
            result = self._openapi_tool.call_operation(
                operation_id=tool_name,
                path_params=path_params,
                query_params=query_params,
                body=body
            )
            
            return ProtocolResponse(
                success=True,
                data=result,
                protocol=ProtocolType.OPENAPI
            )
            
        except Exception as e:
            self.logger.error(f"OpenAPI operation failed: {tool_name} - {e}")
            return ProtocolResponse(
                success=False,
                error=str(e),
                protocol=ProtocolType.OPENAPI
            )
    
    async def list_capabilities(self) -> List[ProtocolCapability]:
        """List OpenAPI operations as capabilities."""
        # This would extract operations from the OpenAPI spec
        return []
    
    async def get_capability(self, name: str) -> Optional[ProtocolCapability]:
        """Get OpenAPI operation details."""
        return None


class UnifiedProtocolManager:
    """Manages multiple protocol clients with automatic routing."""
    
    def __init__(self):
        self.clients: Dict[ProtocolType, ProtocolClient] = {}
        self.capability_routing: Dict[str, ProtocolType] = {}
        self.fallback_protocol = ProtocolType.MCP
        self.logger = get_logger("unified_protocol_manager")
    
    def register_client(self, client: ProtocolClient):
        """Register a protocol client."""
        self.clients[client.protocol_type] = client
        self.logger.info(f"Registered {client.protocol_type.value} protocol client")
    
    async def initialize_all_clients(self) -> Dict[ProtocolType, bool]:
        """Initialize all registered clients."""
        results = {}
        
        for protocol_type, client in self.clients.items():
            try:
                success = await client.initialize()
                results[protocol_type] = success
                if success:
                    await self._index_client_capabilities(client)
            except Exception as e:
                self.logger.error(f"Failed to initialize {protocol_type.value} client: {e}")
                results[protocol_type] = False
        
        return results
    
    async def _index_client_capabilities(self, client: ProtocolClient):
        """Index capabilities from a client for routing."""
        try:
            capabilities = await client.list_capabilities()
            for capability in capabilities:
                self.capability_routing[capability.name] = client.protocol_type
                
            self.logger.debug(
                f"Indexed {len(capabilities)} capabilities from {client.protocol_type.value}"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to index capabilities from {client.protocol_type.value}: {e}")
    
    async def call_capability(self, capability: str, arguments: Dict[str, Any],
                            preferred_protocol: Optional[ProtocolType] = None) -> ProtocolResponse:
        """
        Route capability call to appropriate protocol.
        
        Args:
            capability: Capability name to call
            arguments: Arguments for the capability
            preferred_protocol: Preferred protocol to use
            
        Returns:
            Response from the selected protocol
        """
        # Determine which protocol to use
        protocol = preferred_protocol or self.capability_routing.get(capability, self.fallback_protocol)
        
        client = self.clients.get(protocol)
        if not client:
            return ProtocolResponse(
                success=False,
                error=f"No client available for protocol: {protocol.value}"
            )
        
        self.logger.debug(
            f"Routing {capability} to {protocol.value}",
            extra={
                "capability": capability,
                "protocol": protocol.value,
                "preferred": preferred_protocol.value if preferred_protocol else None
            }
        )
        
        # Make the call
        response = await client.call_tool(capability, arguments)
        
        # If call fails and we have fallback options, try them
        if not response.success and preferred_protocol is None:
            for fallback_protocol in self.clients:
                if fallback_protocol != protocol:
                    fallback_client = self.clients[fallback_protocol]
                    self.logger.info(f"Trying fallback protocol: {fallback_protocol.value}")
                    
                    fallback_response = await fallback_client.call_tool(capability, arguments)
                    if fallback_response.success:
                        return fallback_response
        
        return response
    
    async def list_all_capabilities(self) -> Dict[ProtocolType, List[ProtocolCapability]]:
        """List capabilities from all protocols."""
        all_capabilities = {}
        
        for protocol_type, client in self.clients.items():
            try:
                capabilities = await client.list_capabilities()
                all_capabilities[protocol_type] = capabilities
            except Exception as e:
                self.logger.error(f"Failed to list capabilities from {protocol_type.value}: {e}")
                all_capabilities[protocol_type] = []
        
        return all_capabilities
    
    async def get_capability_info(self, capability: str) -> Optional[ProtocolCapability]:
        """Get detailed information about a capability."""
        protocol = self.capability_routing.get(capability)
        if not protocol:
            return None
        
        client = self.clients.get(protocol)
        if not client:
            return None
        
        return await client.get_capability(capability)
    
    def get_routing_info(self) -> Dict[str, Any]:
        """Get protocol routing information."""
        return {
            "capability_routing": {
                capability: protocol.value 
                for capability, protocol in self.capability_routing.items()
            },
            "registered_protocols": [protocol.value for protocol in self.clients.keys()],
            "fallback_protocol": self.fallback_protocol.value,
            "total_capabilities": len(self.capability_routing)
        }
    
    async def close_all_clients(self):
        """Close all protocol clients."""
        for client in self.clients.values():
            try:
                await client.close()
            except Exception as e:
                self.logger.error(f"Error closing {client.protocol_type.value} client: {e}")


# Global protocol manager
_protocol_manager: Optional[UnifiedProtocolManager] = None


async def get_protocol_manager() -> UnifiedProtocolManager:
    """Get the global protocol manager instance."""
    global _protocol_manager
    if _protocol_manager is None:
        _protocol_manager = UnifiedProtocolManager()
        
        # Register default clients
        _protocol_manager.register_client(MCPProtocolClient())
        _protocol_manager.register_client(A2AProtocolClient())
        
        # Initialize all clients
        await _protocol_manager.initialize_all_clients()
    
    return _protocol_manager


# Convenience functions
async def call_unified_capability(capability: str, arguments: Dict[str, Any],
                                preferred_protocol: Optional[str] = None) -> ProtocolResponse:
    """Call a capability through the unified protocol layer."""
    manager = await get_protocol_manager()
    
    protocol = None
    if preferred_protocol:
        try:
            protocol = ProtocolType(preferred_protocol)
        except ValueError:
            pass
    
    return await manager.call_capability(capability, arguments, protocol)


async def list_unified_capabilities() -> Dict[str, List[Dict[str, Any]]]:
    """List all capabilities across protocols."""
    manager = await get_protocol_manager()
    all_capabilities = await manager.list_all_capabilities()
    
    # Convert to serializable format
    result = {}
    for protocol_type, capabilities in all_capabilities.items():
        result[protocol_type.value] = [
            {
                "name": cap.name,
                "description": cap.description,
                "protocol": cap.protocol.value,
                "schema": cap.schema
            }
            for cap in capabilities
        ]
    
    return result


async def get_unified_capability_info(capability: str) -> Optional[Dict[str, Any]]:
    """Get information about a specific capability."""
    manager = await get_protocol_manager()
    capability_info = await manager.get_capability_info(capability)
    
    if capability_info:
        return {
            "name": capability_info.name,
            "description": capability_info.description,
            "protocol": capability_info.protocol.value,
            "schema": capability_info.schema,
            "metadata": capability_info.metadata
        }
    
    return None
