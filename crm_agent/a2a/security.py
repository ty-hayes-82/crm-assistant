"""
A2A Security Manager for authentication and authorization.
Provides JWT-based authentication and capability-based authorization.
"""

import jwt
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Set
from dataclasses import dataclass, asdict
from enum import Enum
import os

from ..core.observability import get_logger


class TokenType(Enum):
    """Types of authentication tokens."""
    ACCESS = "access"
    REFRESH = "refresh"
    API_KEY = "api_key"


@dataclass
class AgentCredentials:
    """Credentials for an A2A agent."""
    agent_id: str
    api_key: str
    api_secret: str
    capabilities: List[str]
    scopes: List[str]
    created_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool = True
    metadata: Dict[str, Any] = None


@dataclass
class TokenClaims:
    """Claims contained in a JWT token."""
    agent_id: str
    token_type: TokenType
    capabilities: List[str]
    scopes: List[str]
    issued_at: datetime
    expires_at: datetime
    issuer: str = "crm-coordinator"
    subject: Optional[str] = None
    audience: Optional[str] = None


class A2ASecurityManager:
    """Security manager for A2A communications."""
    
    def __init__(self, secret_key: Optional[str] = None):
        """
        Initialize security manager.
        
        Args:
            secret_key: JWT signing secret. If None, generates a random key.
        """
        self.secret_key = secret_key or os.getenv("A2A_SECRET_KEY") or self._generate_secret_key()
        self.algorithm = "HS256"
        self.access_token_lifetime = timedelta(hours=24)
        self.refresh_token_lifetime = timedelta(days=30)
        self.api_key_lifetime = timedelta(days=365)
        
        # Storage for credentials and tokens
        self.agent_credentials: Dict[str, AgentCredentials] = {}
        self.revoked_tokens: Set[str] = set()
        self.rate_limits: Dict[str, Dict[str, Any]] = {}
        
        self.logger = get_logger("a2a_security")
    
    def _generate_secret_key(self) -> str:
        """Generate a secure random secret key."""
        return secrets.token_urlsafe(64)
    
    def _hash_api_key(self, api_key: str) -> str:
        """Hash an API key for secure storage."""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    def register_agent(self, agent_id: str, capabilities: List[str], 
                      scopes: Optional[List[str]] = None,
                      expires_in_days: Optional[int] = None) -> AgentCredentials:
        """
        Register a new agent and generate credentials.
        
        Args:
            agent_id: Unique identifier for the agent
            capabilities: List of capabilities the agent can access
            scopes: List of permission scopes
            expires_in_days: Number of days until credentials expire
            
        Returns:
            Generated credentials for the agent
        """
        # Generate API key and secret
        api_key = f"a2a_{agent_id}_{secrets.token_urlsafe(32)}"
        api_secret = secrets.token_urlsafe(64)
        
        # Calculate expiration
        expires_at = None
        if expires_in_days:
            expires_at = datetime.now() + timedelta(days=expires_in_days)
        
        # Create credentials
        credentials = AgentCredentials(
            agent_id=agent_id,
            api_key=api_key,
            api_secret=api_secret,
            capabilities=capabilities,
            scopes=scopes or [],
            created_at=datetime.now(),
            expires_at=expires_at
        )
        
        # Store credentials (hash the API key)
        self.agent_credentials[self._hash_api_key(api_key)] = credentials
        
        self.logger.info(
            f"Registered agent: {agent_id}",
            extra={
                "agent_id": agent_id,
                "capabilities": capabilities,
                "scopes": scopes,
                "expires_at": expires_at.isoformat() if expires_at else None
            }
        )
        
        return credentials
    
    def revoke_agent_credentials(self, agent_id: str) -> bool:
        """
        Revoke credentials for an agent.
        
        Args:
            agent_id: ID of agent to revoke
            
        Returns:
            True if revocation successful, False otherwise
        """
        for hashed_key, credentials in self.agent_credentials.items():
            if credentials.agent_id == agent_id:
                credentials.is_active = False
                self.logger.info(f"Revoked credentials for agent: {agent_id}")
                return True
        
        return False
    
    def generate_agent_token(self, api_key: str, api_secret: str,
                           token_type: TokenType = TokenType.ACCESS,
                           custom_claims: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Generate JWT token for agent authentication.
        
        Args:
            api_key: Agent API key
            api_secret: Agent API secret
            token_type: Type of token to generate
            custom_claims: Additional claims to include
            
        Returns:
            JWT token string or None if authentication fails
        """
        # Validate credentials
        hashed_key = self._hash_api_key(api_key)
        credentials = self.agent_credentials.get(hashed_key)
        
        if not credentials or not credentials.is_active:
            self.logger.warning(f"Invalid or inactive credentials for API key: {api_key[:10]}...")
            return None
        
        if credentials.api_secret != api_secret:
            self.logger.warning(f"Invalid API secret for agent: {credentials.agent_id}")
            return None
        
        # Check expiration
        if credentials.expires_at and datetime.now() > credentials.expires_at:
            self.logger.warning(f"Expired credentials for agent: {credentials.agent_id}")
            return None
        
        # Determine token lifetime
        if token_type == TokenType.ACCESS:
            lifetime = self.access_token_lifetime
        elif token_type == TokenType.REFRESH:
            lifetime = self.refresh_token_lifetime
        else:
            lifetime = self.api_key_lifetime
        
        # Create token claims
        now = datetime.now()
        claims = TokenClaims(
            agent_id=credentials.agent_id,
            token_type=token_type,
            capabilities=credentials.capabilities,
            scopes=credentials.scopes,
            issued_at=now,
            expires_at=now + lifetime
        )
        
        # Build JWT payload
        payload = {
            "agent_id": claims.agent_id,
            "token_type": claims.token_type.value,
            "capabilities": claims.capabilities,
            "scopes": claims.scopes,
            "iss": claims.issuer,
            "iat": int(claims.issued_at.timestamp()),
            "exp": int(claims.expires_at.timestamp()),
            "jti": secrets.token_urlsafe(16)  # Unique token ID
        }
        
        # Add custom claims
        if custom_claims:
            payload.update(custom_claims)
        
        # Generate token
        try:
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            
            self.logger.debug(
                f"Generated {token_type.value} token for agent: {credentials.agent_id}",
                extra={
                    "agent_id": credentials.agent_id,
                    "token_type": token_type.value,
                    "expires_at": claims.expires_at.isoformat()
                }
            )
            
            return token
            
        except Exception as e:
            self.logger.error(f"Failed to generate token: {e}")
            return None
    
    def validate_agent_token(self, token: str) -> Optional[TokenClaims]:
        """
        Validate agent authentication token.
        
        Args:
            token: JWT token to validate
            
        Returns:
            Token claims if valid, None otherwise
        """
        try:
            # Decode token
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Check if token is revoked
            token_id = payload.get("jti")
            if token_id and token_id in self.revoked_tokens:
                self.logger.warning("Attempted use of revoked token")
                return None
            
            # Create claims object
            claims = TokenClaims(
                agent_id=payload["agent_id"],
                token_type=TokenType(payload["token_type"]),
                capabilities=payload["capabilities"],
                scopes=payload["scopes"],
                issued_at=datetime.fromtimestamp(payload["iat"]),
                expires_at=datetime.fromtimestamp(payload["exp"]),
                issuer=payload.get("iss", "unknown"),
                subject=payload.get("sub"),
                audience=payload.get("aud")
            )
            
            self.logger.debug(f"Validated token for agent: {claims.agent_id}")
            return claims
            
        except jwt.ExpiredSignatureError:
            self.logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            self.logger.warning(f"Invalid token: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Token validation error: {e}")
            return None
    
    def revoke_token(self, token: str) -> bool:
        """
        Revoke a specific token.
        
        Args:
            token: JWT token to revoke
            
        Returns:
            True if revocation successful, False otherwise
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            token_id = payload.get("jti")
            
            if token_id:
                self.revoked_tokens.add(token_id)
                self.logger.info(f"Revoked token: {token_id}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to revoke token: {e}")
            return False
    
    def check_capability_permission(self, claims: TokenClaims, 
                                   required_capability: str) -> bool:
        """
        Check if token has permission for a specific capability.
        
        Args:
            claims: Token claims
            required_capability: Capability being requested
            
        Returns:
            True if permission granted, False otherwise
        """
        # Check if capability is explicitly allowed
        if required_capability in claims.capabilities:
            return True
        
        # Check for wildcard capabilities
        for capability in claims.capabilities:
            if capability.endswith(".*"):
                prefix = capability[:-2]
                if required_capability.startswith(prefix + "."):
                    return True
        
        # Check for admin capability
        if "admin.*" in claims.capabilities:
            return True
        
        self.logger.warning(
            f"Permission denied for capability: {required_capability}",
            extra={
                "agent_id": claims.agent_id,
                "required_capability": required_capability,
                "agent_capabilities": claims.capabilities
            }
        )
        
        return False
    
    def check_scope_permission(self, claims: TokenClaims, required_scope: str) -> bool:
        """
        Check if token has permission for a specific scope.
        
        Args:
            claims: Token claims
            required_scope: Scope being requested
            
        Returns:
            True if permission granted, False otherwise
        """
        return required_scope in claims.scopes or "admin" in claims.scopes
    
    def apply_rate_limit(self, agent_id: str, endpoint: str, 
                        requests_per_minute: int = 60) -> bool:
        """
        Apply rate limiting for an agent and endpoint.
        
        Args:
            agent_id: ID of the agent
            endpoint: Endpoint being accessed
            requests_per_minute: Maximum requests allowed per minute
            
        Returns:
            True if request allowed, False if rate limited
        """
        current_time = datetime.now()
        key = f"{agent_id}:{endpoint}"
        
        if key not in self.rate_limits:
            self.rate_limits[key] = {
                "requests": [],
                "blocked_until": None
            }
        
        rate_limit_data = self.rate_limits[key]
        
        # Check if currently blocked
        if (rate_limit_data["blocked_until"] and 
            current_time < rate_limit_data["blocked_until"]):
            return False
        
        # Clean old requests (older than 1 minute)
        minute_ago = current_time - timedelta(minutes=1)
        rate_limit_data["requests"] = [
            req_time for req_time in rate_limit_data["requests"]
            if req_time > minute_ago
        ]
        
        # Check rate limit
        if len(rate_limit_data["requests"]) >= requests_per_minute:
            # Block for 1 minute
            rate_limit_data["blocked_until"] = current_time + timedelta(minutes=1)
            
            self.logger.warning(
                f"Rate limit exceeded for agent {agent_id} on endpoint {endpoint}",
                extra={
                    "agent_id": agent_id,
                    "endpoint": endpoint,
                    "requests_per_minute": requests_per_minute,
                    "blocked_until": rate_limit_data["blocked_until"].isoformat()
                }
            )
            
            return False
        
        # Record this request
        rate_limit_data["requests"].append(current_time)
        return True
    
    def get_security_stats(self) -> Dict[str, Any]:
        """Get security manager statistics."""
        active_agents = sum(1 for creds in self.agent_credentials.values() if creds.is_active)
        expired_agents = sum(1 for creds in self.agent_credentials.values() 
                           if creds.expires_at and datetime.now() > creds.expires_at)
        
        return {
            "total_agents": len(self.agent_credentials),
            "active_agents": active_agents,
            "expired_agents": expired_agents,
            "revoked_tokens": len(self.revoked_tokens),
            "rate_limited_endpoints": len(self.rate_limits),
            "token_lifetimes": {
                "access_hours": self.access_token_lifetime.total_seconds() / 3600,
                "refresh_days": self.refresh_token_lifetime.days,
                "api_key_days": self.api_key_lifetime.days
            }
        }
    
    def export_agent_credentials(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Export agent credentials for backup or transfer.
        
        Args:
            agent_id: ID of agent to export
            
        Returns:
            Serialized credentials or None if not found
        """
        for credentials in self.agent_credentials.values():
            if credentials.agent_id == agent_id:
                creds_dict = asdict(credentials)
                # Remove sensitive data
                creds_dict.pop("api_secret", None)
                creds_dict["created_at"] = credentials.created_at.isoformat()
                if credentials.expires_at:
                    creds_dict["expires_at"] = credentials.expires_at.isoformat()
                return creds_dict
        
        return None


# Global security manager instance
_security_manager: Optional[A2ASecurityManager] = None


def get_a2a_security_manager() -> A2ASecurityManager:
    """Get the global A2A security manager."""
    global _security_manager
    if _security_manager is None:
        _security_manager = A2ASecurityManager()
    return _security_manager


# Convenience functions
def register_agent_credentials(agent_id: str, capabilities: List[str], 
                             scopes: Optional[List[str]] = None) -> AgentCredentials:
    """Register credentials for an A2A agent."""
    security_manager = get_a2a_security_manager()
    return security_manager.register_agent(agent_id, capabilities, scopes)


def generate_agent_access_token(api_key: str, api_secret: str) -> Optional[str]:
    """Generate an access token for an agent."""
    security_manager = get_a2a_security_manager()
    return security_manager.generate_agent_token(api_key, api_secret, TokenType.ACCESS)


def validate_agent_request(token: str, required_capability: str) -> Optional[TokenClaims]:
    """
    Validate an agent request with capability check.
    
    Returns:
        Token claims if valid and authorized, None otherwise
    """
    security_manager = get_a2a_security_manager()
    
    # Validate token
    claims = security_manager.validate_agent_token(token)
    if not claims:
        return None
    
    # Check capability permission
    if not security_manager.check_capability_permission(claims, required_capability):
        return None
    
    # Apply rate limiting
    if not security_manager.apply_rate_limit(claims.agent_id, required_capability):
        return None
    
    return claims


def create_security_middleware():
    """Create FastAPI middleware for A2A security."""
    from fastapi import Request, HTTPException
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    
    security_scheme = HTTPBearer()
    
    async def verify_token(credentials: HTTPAuthorizationCredentials = security_scheme):
        """Verify JWT token from Authorization header."""
        claims = validate_agent_request(credentials.credentials, "basic.access")
        if not claims:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        return claims
    
    return verify_token
