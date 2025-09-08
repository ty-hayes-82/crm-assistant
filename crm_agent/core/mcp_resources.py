"""
MCP Resources implementation for file-like data access.
Provides standardized resource access following MCP protocol.
"""

from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
import json
import os
from datetime import datetime

try:
    from mcp import Resource
    MCP_AVAILABLE = True
except ImportError:
    # Fallback if MCP not available
    class Resource:
        def __init__(self, uri: str, name: str, description: str, mimeType: str):
            self.uri = uri
            self.name = name
            self.description = description
            self.mimeType = mimeType
    MCP_AVAILABLE = False


class BaseMCPResource(Resource, ABC):
    """Base class for MCP resources with common functionality."""
    
    def __init__(self, uri: str, name: str, description: str, mimeType: str = "application/json"):
        super().__init__(uri=uri, name=name, description=description, mimeType=mimeType)
        self._cache = None
        self._cache_timestamp = None
        self._cache_ttl = 300  # 5 minutes
    
    @abstractmethod
    async def _fetch_data(self) -> Any:
        """Fetch the actual data. Must be implemented by subclasses."""
        pass
    
    async def read(self) -> str:
        """Read resource data with caching."""
        now = datetime.now()
        
        # Check cache validity
        if (self._cache is not None and 
            self._cache_timestamp is not None and 
            (now - self._cache_timestamp).seconds < self._cache_ttl):
            return self._cache
        
        # Fetch fresh data
        data = await self._fetch_data()
        
        # Serialize based on mime type
        if self.mimeType == "application/json":
            result = json.dumps(data, indent=2, default=str)
        else:
            result = str(data)
        
        # Update cache
        self._cache = result
        self._cache_timestamp = now
        
        return result


class HubSpotDataResource(BaseMCPResource):
    """Expose HubSpot data as MCP resources."""
    
    def __init__(self, resource_type: str = "companies"):
        self.resource_type = resource_type
        uri = f"hubspot://{resource_type}"
        name = f"HubSpot {resource_type.title()}"
        description = f"Access to HubSpot {resource_type} records"
        
        super().__init__(uri=uri, name=name, description=description)
    
    async def _fetch_data(self) -> Dict[str, Any]:
        """Fetch HubSpot data using existing connectors."""
        try:
            from ...scripts.hubspot_safe_connector import HubSpotSafeConnector
            connector = HubSpotSafeConnector()
            
            if self.resource_type == "companies":
                # Get recent companies with key properties
                companies = connector.search_companies(limit=100)
                return {
                    "resource_type": "companies",
                    "count": len(companies),
                    "last_updated": datetime.now().isoformat(),
                    "data": companies
                }
            elif self.resource_type == "contacts":
                # Get recent contacts
                contacts = connector.search_contacts(limit=100)
                return {
                    "resource_type": "contacts", 
                    "count": len(contacts),
                    "last_updated": datetime.now().isoformat(),
                    "data": contacts
                }
            else:
                return {"error": f"Unsupported resource type: {self.resource_type}"}
                
        except Exception as e:
            return {
                "error": f"Failed to fetch {self.resource_type}: {str(e)}",
                "resource_type": self.resource_type,
                "last_updated": datetime.now().isoformat()
            }


class ConfigurationResource(BaseMCPResource):
    """Expose system configuration as MCP resource."""
    
    def __init__(self, config_type: str = "hubspot_mapping"):
        self.config_type = config_type
        uri = f"config://{config_type}"
        name = f"Configuration: {config_type.replace('_', ' ').title()}"
        description = f"System configuration for {config_type}"
        
        super().__init__(uri=uri, name=name, description=description)
    
    async def _fetch_data(self) -> Dict[str, Any]:
        """Load configuration from files."""
        try:
            config_dir = os.path.join(os.path.dirname(__file__), "..", "configs")
            
            if self.config_type == "hubspot_mapping":
                config_file = os.path.join(config_dir, "hubspot_field_mapping.json")
            elif self.config_type == "lead_scoring":
                config_file = os.path.join(config_dir, "lead_scoring_config.json")
            elif self.config_type == "outreach_personalization":
                config_file = os.path.join(config_dir, "outreach_personalization_config.json")
            elif self.config_type == "role_taxonomy":
                config_file = os.path.join(config_dir, "role_taxonomy_config.json")
            else:
                return {"error": f"Unknown config type: {self.config_type}"}
            
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
                
                return {
                    "config_type": self.config_type,
                    "file_path": config_file,
                    "last_modified": datetime.fromtimestamp(os.path.getmtime(config_file)).isoformat(),
                    "data": config_data
                }
            else:
                return {"error": f"Config file not found: {config_file}"}
                
        except Exception as e:
            return {"error": f"Failed to load config {self.config_type}: {str(e)}"}


class SessionStateResource(BaseMCPResource):
    """Expose session state as MCP resource."""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        uri = f"session://{session_id}"
        name = f"Session State: {session_id}"
        description = f"Current state for session {session_id}"
        
        super().__init__(uri=uri, name=name, description=description)
    
    async def _fetch_data(self) -> Dict[str, Any]:
        """Get session state from session store."""
        try:
            from ..core.session_store import get_session_store
            session_store = get_session_store()
            
            state = session_store.get_state(self.session_id)
            
            return {
                "session_id": self.session_id,
                "last_updated": datetime.now().isoformat(),
                "state_keys": list(state.keys()) if state else [],
                "data": state or {}
            }
            
        except Exception as e:
            return {
                "error": f"Failed to get session state: {str(e)}",
                "session_id": self.session_id
            }


class LogResource(BaseMCPResource):
    """Expose system logs as MCP resource."""
    
    def __init__(self, log_type: str = "crm_coordinator", lines: int = 100):
        self.log_type = log_type
        self.lines = lines
        uri = f"logs://{log_type}"
        name = f"Logs: {log_type}"
        description = f"Recent {lines} lines from {log_type} logs"
        
        super().__init__(uri=uri, name=name, description=description, mimeType="text/plain")
    
    async def _fetch_data(self) -> str:
        """Read recent log entries."""
        try:
            log_dir = os.path.join(os.path.dirname(__file__), "..", "..", "logs")
            log_file = os.path.join(log_dir, f"{self.log_type}.log")
            
            if os.path.exists(log_file):
                # Read last N lines
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                
                recent_lines = lines[-self.lines:] if len(lines) > self.lines else lines
                return ''.join(recent_lines)
            else:
                return f"Log file not found: {log_file}"
                
        except Exception as e:
            return f"Failed to read logs: {str(e)}"


class MCPResourceRegistry:
    """Registry for managing MCP resources."""
    
    def __init__(self):
        self.resources: Dict[str, BaseMCPResource] = {}
        self._register_default_resources()
    
    def _register_default_resources(self):
        """Register default system resources."""
        # HubSpot resources
        self.register_resource(HubSpotDataResource("companies"))
        self.register_resource(HubSpotDataResource("contacts"))
        
        # Configuration resources
        self.register_resource(ConfigurationResource("hubspot_mapping"))
        self.register_resource(ConfigurationResource("lead_scoring"))
        self.register_resource(ConfigurationResource("outreach_personalization"))
        self.register_resource(ConfigurationResource("role_taxonomy"))
        
        # Log resources
        self.register_resource(LogResource("crm_coordinator"))
        self.register_resource(LogResource("hubspot_api"))
        self.register_resource(LogResource("a2a_server"))
    
    def register_resource(self, resource: BaseMCPResource):
        """Register a resource in the registry."""
        self.resources[resource.uri] = resource
    
    def get_resource(self, uri: str) -> Optional[BaseMCPResource]:
        """Get a resource by URI."""
        return self.resources.get(uri)
    
    def list_resources(self) -> List[Dict[str, str]]:
        """List all available resources."""
        return [
            {
                "uri": resource.uri,
                "name": resource.name,
                "description": resource.description,
                "mimeType": resource.mimeType
            }
            for resource in self.resources.values()
        ]
    
    def create_session_resource(self, session_id: str) -> SessionStateResource:
        """Create and register a session-specific resource."""
        resource = SessionStateResource(session_id)
        self.register_resource(resource)
        return resource


# Global resource registry
_resource_registry = None


def get_mcp_resource_registry() -> MCPResourceRegistry:
    """Get the global MCP resource registry."""
    global _resource_registry
    if _resource_registry is None:
        _resource_registry = MCPResourceRegistry()
    return _resource_registry


# Convenience functions
async def read_hubspot_companies() -> str:
    """Read HubSpot companies as MCP resource."""
    registry = get_mcp_resource_registry()
    resource = registry.get_resource("hubspot://companies")
    if resource:
        return await resource.read()
    return json.dumps({"error": "HubSpot companies resource not found"})


async def read_hubspot_contacts() -> str:
    """Read HubSpot contacts as MCP resource."""
    registry = get_mcp_resource_registry()
    resource = registry.get_resource("hubspot://contacts")
    if resource:
        return await resource.read()
    return json.dumps({"error": "HubSpot contacts resource not found"})


async def read_configuration(config_type: str) -> str:
    """Read system configuration as MCP resource."""
    registry = get_mcp_resource_registry()
    resource = registry.get_resource(f"config://{config_type}")
    if resource:
        return await resource.read()
    return json.dumps({"error": f"Configuration resource not found: {config_type}"})


async def read_session_state(session_id: str) -> str:
    """Read session state as MCP resource."""
    registry = get_mcp_resource_registry()
    
    # Create session resource if it doesn't exist
    resource_uri = f"session://{session_id}"
    resource = registry.get_resource(resource_uri)
    if not resource:
        resource = registry.create_session_resource(session_id)
    
    return await resource.read()
