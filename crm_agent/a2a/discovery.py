"""
A2A Agent Discovery and Registry implementation.
Provides capability-based agent discovery and management.
"""

from typing import Dict, List, Optional, Any, Set
import asyncio
import json
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import httpx

from ..core.observability import get_logger


@dataclass
class AgentRegistration:
    """Agent registration information."""
    agent_id: str
    name: str
    url: str
    capabilities: List[str]
    tags: List[str]
    version: str
    last_seen: datetime
    health_status: str = "unknown"  # healthy, unhealthy, unknown
    response_time_ms: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class CapabilityMatch:
    """Result of capability matching."""
    agent_id: str
    capability: str
    confidence: float
    match_reason: str
    agent_metadata: Dict[str, Any]


class A2AAgentRegistry:
    """Registry for discovering and managing A2A agents."""
    
    def __init__(self, health_check_interval: int = 300):  # 5 minutes
        self.agents: Dict[str, AgentRegistration] = {}
        self.capabilities_index: Dict[str, Set[str]] = {}
        self.tags_index: Dict[str, Set[str]] = {}
        self.health_check_interval = health_check_interval
        self.logger = get_logger("a2a_discovery")
        self._health_check_task: Optional[asyncio.Task] = None
        self._running = False
    
    def register_agent(self, agent_card: Dict[str, Any]) -> bool:
        """
        Register an agent and index its capabilities.
        
        Args:
            agent_card: A2A agent card with capabilities
            
        Returns:
            True if registration successful, False otherwise
        """
        try:
            agent_id = agent_card["name"]
            
            # Extract capabilities from skills
            capabilities = []
            for skill in agent_card.get("skills", []):
                capabilities.append(skill["id"])
            
            # Create registration
            registration = AgentRegistration(
                agent_id=agent_id,
                name=agent_card.get("name", ""),
                url=agent_card.get("url", ""),
                capabilities=capabilities,
                tags=agent_card.get("tags", []),
                version=agent_card.get("version", "1.0.0"),
                last_seen=datetime.now(),
                metadata=agent_card
            )
            
            # Store registration
            self.agents[agent_id] = registration
            
            # Index capabilities
            for capability in capabilities:
                if capability not in self.capabilities_index:
                    self.capabilities_index[capability] = set()
                self.capabilities_index[capability].add(agent_id)
            
            # Index tags
            for tag in registration.tags:
                if tag not in self.tags_index:
                    self.tags_index[tag] = set()
                self.tags_index[tag].add(agent_id)
            
            self.logger.info(
                f"Registered agent: {agent_id}",
                extra={
                    "agent_id": agent_id,
                    "capabilities": capabilities,
                    "tags": registration.tags,
                    "url": registration.url
                }
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register agent: {e}")
            return False
    
    def unregister_agent(self, agent_id: str) -> bool:
        """
        Unregister an agent and remove from indices.
        
        Args:
            agent_id: ID of agent to unregister
            
        Returns:
            True if unregistration successful, False otherwise
        """
        if agent_id not in self.agents:
            return False
        
        try:
            registration = self.agents[agent_id]
            
            # Remove from capabilities index
            for capability in registration.capabilities:
                if capability in self.capabilities_index:
                    self.capabilities_index[capability].discard(agent_id)
                    if not self.capabilities_index[capability]:
                        del self.capabilities_index[capability]
            
            # Remove from tags index
            for tag in registration.tags:
                if tag in self.tags_index:
                    self.tags_index[tag].discard(agent_id)
                    if not self.tags_index[tag]:
                        del self.tags_index[tag]
            
            # Remove agent
            del self.agents[agent_id]
            
            self.logger.info(f"Unregistered agent: {agent_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to unregister agent {agent_id}: {e}")
            return False
    
    def find_agents_by_capability(self, capability: str) -> List[str]:
        """
        Find agents that provide a specific capability.
        
        Args:
            capability: Capability to search for
            
        Returns:
            List of agent IDs that provide the capability
        """
        return list(self.capabilities_index.get(capability, set()))
    
    def find_agents_by_tag(self, tag: str) -> List[str]:
        """
        Find agents that have a specific tag.
        
        Args:
            tag: Tag to search for
            
        Returns:
            List of agent IDs with the tag
        """
        return list(self.tags_index.get(tag, set()))
    
    def find_best_agent_for_capability(self, capability: str, 
                                     preferences: Optional[Dict[str, Any]] = None) -> Optional[CapabilityMatch]:
        """
        Find the best agent for a specific capability based on preferences.
        
        Args:
            capability: Capability needed
            preferences: Optional preferences for agent selection
            
        Returns:
            Best capability match or None if no agents found
        """
        candidate_agents = self.find_agents_by_capability(capability)
        
        if not candidate_agents:
            return None
        
        preferences = preferences or {}
        matches = []
        
        for agent_id in candidate_agents:
            registration = self.agents[agent_id]
            
            # Calculate match confidence based on various factors
            confidence = 1.0
            match_reasons = []
            
            # Health status factor
            if registration.health_status == "healthy":
                confidence *= 1.0
                match_reasons.append("healthy")
            elif registration.health_status == "unhealthy":
                confidence *= 0.5
                match_reasons.append("unhealthy")
            else:
                confidence *= 0.8
                match_reasons.append("unknown_health")
            
            # Response time factor
            if registration.response_time_ms:
                if registration.response_time_ms < 1000:  # < 1 second
                    confidence *= 1.0
                    match_reasons.append("fast_response")
                elif registration.response_time_ms < 5000:  # < 5 seconds
                    confidence *= 0.9
                    match_reasons.append("moderate_response")
                else:
                    confidence *= 0.7
                    match_reasons.append("slow_response")
            
            # Tag preferences
            preferred_tags = preferences.get("tags", [])
            if preferred_tags:
                matching_tags = set(registration.tags) & set(preferred_tags)
                if matching_tags:
                    confidence *= 1.2
                    match_reasons.append(f"preferred_tags:{','.join(matching_tags)}")
            
            # Version preferences
            preferred_version = preferences.get("version")
            if preferred_version and registration.version == preferred_version:
                confidence *= 1.1
                match_reasons.append(f"preferred_version:{preferred_version}")
            
            # Last seen factor (prefer recently active agents)
            time_since_seen = datetime.now() - registration.last_seen
            if time_since_seen < timedelta(minutes=5):
                confidence *= 1.0
                match_reasons.append("recently_active")
            elif time_since_seen < timedelta(hours=1):
                confidence *= 0.9
                match_reasons.append("moderately_active")
            else:
                confidence *= 0.7
                match_reasons.append("inactive")
            
            match = CapabilityMatch(
                agent_id=agent_id,
                capability=capability,
                confidence=confidence,
                match_reason=" | ".join(match_reasons),
                agent_metadata=asdict(registration)
            )
            
            matches.append(match)
        
        # Sort by confidence and return best match
        matches.sort(key=lambda x: x.confidence, reverse=True)
        return matches[0] if matches else None
    
    def list_all_agents(self) -> List[Dict[str, Any]]:
        """List all registered agents with their information."""
        return [asdict(registration) for registration in self.agents.values()]
    
    def get_agent_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific agent."""
        registration = self.agents.get(agent_id)
        return asdict(registration) if registration else None
    
    def get_capability_coverage(self) -> Dict[str, int]:
        """Get coverage statistics for all capabilities."""
        return {
            capability: len(agents) 
            for capability, agents in self.capabilities_index.items()
        }
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """Get overall registry statistics."""
        total_agents = len(self.agents)
        healthy_agents = sum(1 for a in self.agents.values() if a.health_status == "healthy")
        total_capabilities = len(self.capabilities_index)
        
        return {
            "total_agents": total_agents,
            "healthy_agents": healthy_agents,
            "unhealthy_agents": total_agents - healthy_agents,
            "total_capabilities": total_capabilities,
            "capabilities_coverage": self.get_capability_coverage(),
            "last_updated": datetime.now().isoformat()
        }
    
    async def start_health_monitoring(self):
        """Start background health monitoring for registered agents."""
        if self._running:
            return
        
        self._running = True
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        self.logger.info("Started A2A agent health monitoring")
    
    async def stop_health_monitoring(self):
        """Stop background health monitoring."""
        self._running = False
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Stopped A2A agent health monitoring")
    
    async def _health_check_loop(self):
        """Background loop for checking agent health."""
        while self._running:
            try:
                await self._check_all_agents_health()
                await asyncio.sleep(self.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in health check loop: {e}")
                await asyncio.sleep(60)  # Wait before retrying
    
    async def _check_all_agents_health(self):
        """Check health of all registered agents."""
        health_check_tasks = []
        
        for agent_id, registration in self.agents.items():
            task = asyncio.create_task(self._check_agent_health(agent_id, registration))
            health_check_tasks.append(task)
        
        if health_check_tasks:
            await asyncio.gather(*health_check_tasks, return_exceptions=True)
    
    async def _check_agent_health(self, agent_id: str, registration: AgentRegistration):
        """Check health of a specific agent."""
        try:
            start_time = time.time()
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Try to get agent health endpoint
                health_url = f"{registration.url.rstrip('/')}/health"
                response = await client.get(health_url)
                
                response_time = (time.time() - start_time) * 1000  # Convert to ms
                
                if response.status_code == 200:
                    registration.health_status = "healthy"
                    registration.response_time_ms = response_time
                    registration.last_seen = datetime.now()
                else:
                    registration.health_status = "unhealthy"
                    registration.response_time_ms = response_time
                
        except Exception as e:
            self.logger.debug(f"Health check failed for agent {agent_id}: {e}")
            registration.health_status = "unhealthy"
            registration.response_time_ms = None
    
    async def discover_agents_from_urls(self, agent_urls: List[str]) -> int:
        """
        Discover and register agents from a list of URLs.
        
        Args:
            agent_urls: List of agent base URLs to discover
            
        Returns:
            Number of agents successfully registered
        """
        registered_count = 0
        
        for url in agent_urls:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    # Try to get agent card
                    card_url = f"{url.rstrip('/')}/agent-card"
                    response = await client.get(card_url)
                    
                    if response.status_code == 200:
                        agent_card = response.json()
                        if self.register_agent(agent_card):
                            registered_count += 1
                    
            except Exception as e:
                self.logger.debug(f"Failed to discover agent from {url}: {e}")
        
        self.logger.info(f"Discovered {registered_count} agents from {len(agent_urls)} URLs")
        return registered_count


class A2ACapabilityRouter:
    """Router for directing requests to appropriate A2A agents."""
    
    def __init__(self, registry: A2AAgentRegistry):
        self.registry = registry
        self.logger = get_logger("a2a_router")
    
    async def route_capability_request(self, capability: str, arguments: Dict[str, Any],
                                     preferences: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Route a capability request to the best available agent.
        
        Args:
            capability: Capability being requested
            arguments: Arguments for the capability
            preferences: Optional agent selection preferences
            
        Returns:
            Result from the selected agent
        """
        # Find best agent for capability
        match = self.registry.find_best_agent_for_capability(capability, preferences)
        
        if not match:
            return {
                "error": f"No agents available for capability: {capability}",
                "capability": capability
            }
        
        # Route request to selected agent
        try:
            agent_registration = self.registry.agents[match.agent_id]
            
            self.logger.info(
                f"Routing {capability} to agent {match.agent_id}",
                extra={
                    "capability": capability,
                    "agent_id": match.agent_id,
                    "confidence": match.confidence,
                    "match_reason": match.match_reason
                }
            )
            
            # Make A2A request
            async with httpx.AsyncClient(timeout=30.0) as client:
                rpc_request = {
                    "jsonrpc": "2.0",
                    "method": "agent.invoke",
                    "params": {
                        "capability": capability,
                        "arguments": arguments
                    },
                    "id": 1
                }
                
                rpc_url = f"{agent_registration.url.rstrip('/')}/rpc"
                response = await client.post(rpc_url, json=rpc_request)
                response.raise_for_status()
                
                result = response.json()
                
                # Update agent last seen
                agent_registration.last_seen = datetime.now()
                
                return {
                    "result": result.get("result"),
                    "agent_id": match.agent_id,
                    "capability": capability,
                    "confidence": match.confidence
                }
                
        except Exception as e:
            self.logger.error(f"Failed to route {capability} to {match.agent_id}: {e}")
            
            # Mark agent as unhealthy
            if match.agent_id in self.registry.agents:
                self.registry.agents[match.agent_id].health_status = "unhealthy"
            
            return {
                "error": f"Failed to execute {capability}: {str(e)}",
                "agent_id": match.agent_id,
                "capability": capability
            }


# Global registry instance
_global_registry: Optional[A2AAgentRegistry] = None


def get_a2a_registry() -> A2AAgentRegistry:
    """Get the global A2A agent registry."""
    global _global_registry
    if _global_registry is None:
        _global_registry = A2AAgentRegistry()
    return _global_registry


def get_a2a_router() -> A2ACapabilityRouter:
    """Get the global A2A capability router."""
    registry = get_a2a_registry()
    return A2ACapabilityRouter(registry)


# Convenience functions
async def register_self_as_a2a_agent(host: str = "localhost", port: int = 10000):
    """Register this CRM agent in the global registry."""
    from .__main__ import build_agent_card
    
    registry = get_a2a_registry()
    agent_card = build_agent_card(host=host, port=port)
    return registry.register_agent(agent_card)


async def discover_a2a_agents(discovery_urls: List[str]) -> int:
    """Discover A2A agents from a list of URLs."""
    registry = get_a2a_registry()
    return await registry.discover_agents_from_urls(discovery_urls)


async def find_agent_for_capability(capability: str, 
                                  preferences: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """Find the best agent for a capability."""
    registry = get_a2a_registry()
    match = registry.find_best_agent_for_capability(capability, preferences)
    return match.agent_id if match else None


async def route_to_agent(capability: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Route a capability request to the best available agent."""
    router = get_a2a_router()
    return await router.route_capability_request(capability, arguments)
