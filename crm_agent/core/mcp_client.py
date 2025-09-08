"""
Standardized MCP client implementation following protocol specifications.
Provides proper MCP initialization sequence and lifecycle management.
"""

from typing import Dict, Any, List, Optional, AsyncIterator
import asyncio
import json
import logging
from contextlib import asynccontextmanager

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    MCP_AVAILABLE = True
except ImportError:
    # Fallback if MCP not available
    class ClientSession:
        pass
    class StdioServerParameters:
        def __init__(self, command: str, args: List[str]):
            self.command = command
            self.args = args
    MCP_AVAILABLE = False

from ..core.observability import get_logger


class StandardizedMCPClient:
    """Standardized MCP client following protocol specifications."""
    
    def __init__(self, server_command: str = "python", 
                 server_args: Optional[List[str]] = None):
        """
        Initialize MCP client with server parameters.
        
        Args:
            server_command: Command to start MCP server
            server_args: Arguments for server command
        """
        self.logger = get_logger("mcp_client")
        
        if server_args is None:
            server_args = ["-m", "crm_fastmcp_server.stdio_server"]
        
        self.server_params = StdioServerParameters(
            command=server_command,
            args=server_args
        )
        
        self.session: Optional[ClientSession] = None
        self.server_capabilities: Dict[str, Any] = {}
        self.client_capabilities: Dict[str, Any] = {
            "roots": {
                "listChanged": True
            },
            "sampling": {}
        }
        self._initialized = False
        self._connection_lock = asyncio.Lock()
    
    async def initialize(self) -> bool:
        """
        Initialize MCP connection with proper lifecycle.
        
        Returns:
            True if initialization successful, False otherwise
        """
        async with self._connection_lock:
            if self._initialized and self.session:
                return True
            
            try:
                self.logger.info("Initializing MCP client connection")
                
                if not MCP_AVAILABLE:
                    self.logger.warning("MCP not available, using fallback mode")
                    self._initialized = True
                    return True
                
                # Create STDIO client session
                async with stdio_client(self.server_params) as (read, write):
                    async with ClientSession(read, write) as session:
                        self.session = session
                        
                        # Initialize connection
                        init_result = await session.initialize()
                        self.server_capabilities = init_result.capabilities
                        
                        self.logger.info(
                            f"MCP client initialized successfully",
                            extra={
                                "server_capabilities": list(self.server_capabilities.keys()),
                                "client_capabilities": list(self.client_capabilities.keys())
                            }
                        )
                        
                        self._initialized = True
                        return True
                        
            except Exception as e:
                self.logger.error(f"Failed to initialize MCP client: {e}")
                self._initialized = False
                return False
    
    async def get_server_capabilities(self) -> Dict[str, Any]:
        """Get server capabilities after initialization."""
        if not self._initialized:
            await self.initialize()
        return self.server_capabilities.copy()
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools from MCP server."""
        if not self._initialized:
            await self.initialize()
        
        if not MCP_AVAILABLE or not self.session:
            # Fallback tool list
            return [
                {
                    "name": "search_companies",
                    "description": "Search for companies in HubSpot",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "limit": {"type": "integer", "default": 10}
                        },
                        "required": ["query"]
                    }
                },
                {
                    "name": "get_company_details",
                    "description": "Get detailed company information",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "company_id": {"type": "string"}
                        },
                        "required": ["company_id"]
                    }
                }
            ]
        
        try:
            tools_result = await self.session.list_tools()
            return tools_result.tools
        except Exception as e:
            self.logger.error(f"Failed to list tools: {e}")
            return []
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a tool through MCP protocol.
        
        Args:
            tool_name: Name of tool to call
            arguments: Tool arguments
            
        Returns:
            Tool execution result
        """
        if not self._initialized:
            await self.initialize()
        
        if not MCP_AVAILABLE or not self.session:
            # Fallback to direct HTTP call
            return await self._fallback_tool_call(tool_name, arguments)
        
        try:
            self.logger.debug(f"Calling MCP tool: {tool_name}", extra={"arguments": arguments})
            
            result = await self.session.call_tool(tool_name, arguments)
            
            self.logger.debug(f"MCP tool call successful: {tool_name}")
            
            # Extract content from MCP response
            if hasattr(result, 'content') and result.content:
                if len(result.content) == 1 and hasattr(result.content[0], 'text'):
                    # Single text response
                    try:
                        return json.loads(result.content[0].text)
                    except json.JSONDecodeError:
                        return {"text": result.content[0].text}
                else:
                    # Multiple content items
                    return {"content": [item.text if hasattr(item, 'text') else str(item) 
                                      for item in result.content]}
            
            return {"result": str(result)}
            
        except Exception as e:
            self.logger.error(f"MCP tool call failed: {tool_name} - {e}")
            return {"error": str(e)}
    
    async def _fallback_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback tool call using direct HTTP when MCP not available."""
        import httpx
        
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "call_tool",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:8081/mcp",
                    json=payload,
                    timeout=30
                )
                response.raise_for_status()
                
                result = response.json()
                
                if "error" in result:
                    return {"error": result["error"]}
                
                # Extract content from MCP response format
                mcp_result = result.get("result", {})
                if "content" in mcp_result and mcp_result["content"]:
                    content_text = mcp_result["content"][0].get("text", "{}")
                    try:
                        return json.loads(content_text)
                    except json.JSONDecodeError:
                        return {"raw_text": content_text}
                
                return mcp_result
                
        except Exception as e:
            self.logger.error(f"Fallback tool call failed: {tool_name} - {e}")
            return {"error": str(e)}
    
    async def list_resources(self) -> List[Dict[str, Any]]:
        """List available resources from MCP server."""
        if not self._initialized:
            await self.initialize()
        
        if not MCP_AVAILABLE or not self.session:
            # Fallback resource list
            from .mcp_resources import get_mcp_resource_registry
            registry = get_mcp_resource_registry()
            return registry.list_resources()
        
        try:
            resources_result = await self.session.list_resources()
            return resources_result.resources
        except Exception as e:
            self.logger.error(f"Failed to list resources: {e}")
            return []
    
    async def read_resource(self, uri: str) -> str:
        """
        Read a resource by URI.
        
        Args:
            uri: Resource URI to read
            
        Returns:
            Resource content as string
        """
        if not self._initialized:
            await self.initialize()
        
        if not MCP_AVAILABLE or not self.session:
            # Fallback to local resource registry
            from .mcp_resources import get_mcp_resource_registry
            registry = get_mcp_resource_registry()
            resource = registry.get_resource(uri)
            if resource:
                return await resource.read()
            return json.dumps({"error": f"Resource not found: {uri}"})
        
        try:
            result = await self.session.read_resource(uri)
            
            if hasattr(result, 'contents') and result.contents:
                # Return first content item
                content = result.contents[0]
                if hasattr(content, 'text'):
                    return content.text
                else:
                    return str(content)
            
            return json.dumps({"error": f"No content for resource: {uri}"})
            
        except Exception as e:
            self.logger.error(f"Failed to read resource {uri}: {e}")
            return json.dumps({"error": str(e)})
    
    async def list_prompts(self) -> List[Dict[str, Any]]:
        """List available prompts from MCP server."""
        if not self._initialized:
            await self.initialize()
        
        if not MCP_AVAILABLE or not self.session:
            # Fallback prompt list
            from .mcp_prompts import get_mcp_prompt_registry
            registry = get_mcp_prompt_registry()
            return registry.list_prompts()
        
        try:
            prompts_result = await self.session.list_prompts()
            return prompts_result.prompts
        except Exception as e:
            self.logger.error(f"Failed to list prompts: {e}")
            return []
    
    async def get_prompt(self, name: str, arguments: Optional[Dict[str, Any]] = None) -> str:
        """
        Get and render a prompt by name.
        
        Args:
            name: Prompt name
            arguments: Prompt arguments for rendering
            
        Returns:
            Rendered prompt content
        """
        if not self._initialized:
            await self.initialize()
        
        if not MCP_AVAILABLE or not self.session:
            # Fallback to local prompt registry
            from .mcp_prompts import get_mcp_prompt_registry
            registry = get_mcp_prompt_registry()
            if arguments:
                return registry.render_prompt(name, **arguments)
            else:
                prompt = registry.get_prompt(name)
                return prompt.template if prompt else f"Prompt not found: {name}"
        
        try:
            result = await self.session.get_prompt(name, arguments or {})
            
            if hasattr(result, 'messages') and result.messages:
                # Combine all message content
                content_parts = []
                for message in result.messages:
                    if hasattr(message, 'content'):
                        if hasattr(message.content, 'text'):
                            content_parts.append(message.content.text)
                        else:
                            content_parts.append(str(message.content))
                return "\n".join(content_parts)
            
            return f"No content for prompt: {name}"
            
        except Exception as e:
            self.logger.error(f"Failed to get prompt {name}: {e}")
            return f"Error getting prompt {name}: {str(e)}"
    
    @asynccontextmanager
    async def session_context(self):
        """Context manager for MCP session lifecycle."""
        try:
            await self.initialize()
            yield self
        finally:
            await self.close()
    
    async def close(self):
        """Close MCP connection."""
        if self.session:
            try:
                # MCP sessions are typically closed by context manager
                self.session = None
                self._initialized = False
                self.logger.info("MCP client connection closed")
            except Exception as e:
                self.logger.error(f"Error closing MCP client: {e}")


class MCPClientPool:
    """Pool of MCP clients for concurrent operations."""
    
    def __init__(self, pool_size: int = 5):
        self.pool_size = pool_size
        self.clients: List[StandardizedMCPClient] = []
        self.available_clients: asyncio.Queue = asyncio.Queue()
        self.logger = get_logger("mcp_client_pool")
        self._initialized = False
    
    async def initialize(self):
        """Initialize client pool."""
        if self._initialized:
            return
        
        self.logger.info(f"Initializing MCP client pool with {self.pool_size} clients")
        
        for i in range(self.pool_size):
            client = StandardizedMCPClient()
            await client.initialize()
            self.clients.append(client)
            await self.available_clients.put(client)
        
        self._initialized = True
    
    @asynccontextmanager
    async def get_client(self) -> StandardizedMCPClient:
        """Get a client from the pool."""
        if not self._initialized:
            await self.initialize()
        
        client = await self.available_clients.get()
        try:
            yield client
        finally:
            await self.available_clients.put(client)
    
    async def close_all(self):
        """Close all clients in the pool."""
        for client in self.clients:
            await client.close()
        self.clients.clear()
        self._initialized = False


# Global client instances
_default_client: Optional[StandardizedMCPClient] = None
_client_pool: Optional[MCPClientPool] = None


async def get_mcp_client() -> StandardizedMCPClient:
    """Get the default MCP client instance."""
    global _default_client
    if _default_client is None:
        _default_client = StandardizedMCPClient()
        await _default_client.initialize()
    return _default_client


async def get_mcp_client_pool() -> MCPClientPool:
    """Get the MCP client pool instance."""
    global _client_pool
    if _client_pool is None:
        _client_pool = MCPClientPool()
        await _client_pool.initialize()
    return _client_pool


# Convenience functions
async def mcp_call_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Call an MCP tool using the default client."""
    client = await get_mcp_client()
    return await client.call_tool(tool_name, arguments)


async def mcp_read_resource(uri: str) -> str:
    """Read an MCP resource using the default client."""
    client = await get_mcp_client()
    return await client.read_resource(uri)


async def mcp_get_prompt(name: str, arguments: Optional[Dict[str, Any]] = None) -> str:
    """Get an MCP prompt using the default client."""
    client = await get_mcp_client()
    return await client.get_prompt(name, arguments)


async def mcp_list_capabilities() -> Dict[str, List[Dict[str, Any]]]:
    """List all MCP capabilities (tools, resources, prompts)."""
    client = await get_mcp_client()
    
    return {
        "tools": await client.list_tools(),
        "resources": await client.list_resources(),
        "prompts": await client.list_prompts()
    }
