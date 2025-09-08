"""
Pluggable Session Store System for Phase 9.

This module provides pluggable session storage with support for in-memory
and Redis backends, maintaining the same interface as the existing system.
"""

import json
import pickle
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union
import threading
from pathlib import Path

from pydantic import BaseModel, Field

from .state_models import CRMSessionState


class SessionStoreError(Exception):
    """Base exception for session store operations."""
    pass


class SessionNotFoundError(SessionStoreError):
    """Raised when a session is not found."""
    pass


class SessionExpiredError(SessionStoreError):
    """Raised when a session has expired."""
    pass


class SessionMetadata(BaseModel):
    """Metadata for session storage."""
    session_id: str
    created_at: datetime
    last_accessed: datetime
    expires_at: Optional[datetime] = None
    size_bytes: Optional[int] = None
    version: str = "1.0.0"


class SessionStore(ABC):
    """Abstract base class for session storage implementations."""
    
    @abstractmethod
    def store_session(
        self, 
        session_id: str, 
        state: CRMSessionState,
        ttl_seconds: Optional[int] = None
    ) -> None:
        """
        Store a session state.
        
        Args:
            session_id: Unique session identifier
            state: Session state to store
            ttl_seconds: Time to live in seconds (None for no expiration)
        """
        pass
    
    @abstractmethod
    def get_session(self, session_id: str) -> CRMSessionState:
        """
        Retrieve a session state.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Session state
            
        Raises:
            SessionNotFoundError: If session doesn't exist
            SessionExpiredError: If session has expired
        """
        pass
    
    @abstractmethod
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            True if session was deleted, False if not found
        """
        pass
    
    @abstractmethod
    def exists(self, session_id: str) -> bool:
        """
        Check if a session exists and is not expired.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            True if session exists and is valid
        """
        pass
    
    @abstractmethod
    def list_sessions(
        self, 
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[SessionMetadata]:
        """
        List session metadata.
        
        Args:
            limit: Maximum number of sessions to return
            offset: Number of sessions to skip
            
        Returns:
            List of session metadata
        """
        pass
    
    @abstractmethod
    def cleanup_expired(self) -> int:
        """
        Clean up expired sessions.
        
        Returns:
            Number of sessions cleaned up
        """
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics.
        
        Returns:
            Dictionary with storage stats
        """
        pass


class InMemorySessionStore(SessionStore):
    """In-memory implementation of session store."""
    
    def __init__(self, default_ttl_seconds: int = 3600):
        self._sessions: Dict[str, CRMSessionState] = {}
        self._metadata: Dict[str, SessionMetadata] = {}
        self._lock = threading.RLock()
        self.default_ttl_seconds = default_ttl_seconds
    
    def store_session(
        self, 
        session_id: str, 
        state: CRMSessionState,
        ttl_seconds: Optional[int] = None
    ) -> None:
        """Store a session state in memory."""
        ttl = ttl_seconds or self.default_ttl_seconds
        expires_at = datetime.utcnow() + timedelta(seconds=ttl) if ttl > 0 else None
        
        with self._lock:
            self._sessions[session_id] = state
            
            # Calculate approximate size
            try:
                serialized = pickle.dumps(state)
                size_bytes = len(serialized)
            except Exception:
                size_bytes = None
            
            self._metadata[session_id] = SessionMetadata(
                session_id=session_id,
                created_at=state.created_at,
                last_accessed=datetime.utcnow(),
                expires_at=expires_at,
                size_bytes=size_bytes
            )
    
    def get_session(self, session_id: str) -> CRMSessionState:
        """Retrieve a session state from memory."""
        with self._lock:
            if session_id not in self._sessions:
                raise SessionNotFoundError(f"Session {session_id} not found")
            
            metadata = self._metadata[session_id]
            
            # Check expiration
            if metadata.expires_at and datetime.utcnow() > metadata.expires_at:
                # Clean up expired session
                del self._sessions[session_id]
                del self._metadata[session_id]
                raise SessionExpiredError(f"Session {session_id} has expired")
            
            # Update last accessed time
            metadata.last_accessed = datetime.utcnow()
            
            return self._sessions[session_id]
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session from memory."""
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                del self._metadata[session_id]
                return True
            return False
    
    def exists(self, session_id: str) -> bool:
        """Check if session exists and is not expired."""
        with self._lock:
            if session_id not in self._sessions:
                return False
            
            metadata = self._metadata[session_id]
            if metadata.expires_at and datetime.utcnow() > metadata.expires_at:
                # Clean up expired session
                del self._sessions[session_id]
                del self._metadata[session_id]
                return False
            
            return True
    
    def list_sessions(
        self, 
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[SessionMetadata]:
        """List session metadata."""
        with self._lock:
            # Clean up expired sessions first
            self.cleanup_expired()
            
            sessions = list(self._metadata.values())
            sessions.sort(key=lambda x: x.last_accessed, reverse=True)
            
            if offset > 0:
                sessions = sessions[offset:]
            
            if limit:
                sessions = sessions[:limit]
            
            return sessions
    
    def cleanup_expired(self) -> int:
        """Clean up expired sessions."""
        with self._lock:
            now = datetime.utcnow()
            expired_sessions = [
                session_id for session_id, metadata in self._metadata.items()
                if metadata.expires_at and now > metadata.expires_at
            ]
            
            for session_id in expired_sessions:
                del self._sessions[session_id]
                del self._metadata[session_id]
            
            return len(expired_sessions)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        with self._lock:
            total_size = sum(
                metadata.size_bytes or 0 
                for metadata in self._metadata.values()
            )
            
            return {
                "store_type": "in_memory",
                "total_sessions": len(self._sessions),
                "total_size_bytes": total_size,
                "average_size_bytes": total_size // len(self._sessions) if self._sessions else 0
            }


class RedisSessionStore(SessionStore):
    """Redis implementation of session store."""
    
    def __init__(
        self, 
        redis_url: str = "redis://localhost:6379",
        key_prefix: str = "crm_session:",
        default_ttl_seconds: int = 3600,
        serialization: str = "json"  # "json" or "pickle"
    ):
        try:
            import redis
            self.redis_available = True
        except ImportError:
            self.redis_available = False
            raise ImportError(
                "Redis not available. Install with: pip install redis"
            )
        
        self.redis_client = redis.from_url(redis_url, decode_responses=(serialization == "json"))
        self.key_prefix = key_prefix
        self.default_ttl_seconds = default_ttl_seconds
        self.serialization = serialization
        
        # Test connection
        try:
            self.redis_client.ping()
        except Exception as e:
            raise SessionStoreError(f"Failed to connect to Redis: {e}")
    
    def _session_key(self, session_id: str) -> str:
        """Get Redis key for session."""
        return f"{self.key_prefix}{session_id}"
    
    def _metadata_key(self, session_id: str) -> str:
        """Get Redis key for session metadata."""
        return f"{self.key_prefix}meta:{session_id}"
    
    def _serialize_state(self, state: CRMSessionState) -> Union[str, bytes]:
        """Serialize session state."""
        if self.serialization == "json":
            return state.model_dump_json()
        else:
            return pickle.dumps(state)
    
    def _deserialize_state(self, data: Union[str, bytes]) -> CRMSessionState:
        """Deserialize session state."""
        if self.serialization == "json":
            return CRMSessionState.model_validate_json(data)
        else:
            return pickle.loads(data)
    
    def store_session(
        self, 
        session_id: str, 
        state: CRMSessionState,
        ttl_seconds: Optional[int] = None
    ) -> None:
        """Store a session state in Redis."""
        ttl = ttl_seconds or self.default_ttl_seconds
        
        # Serialize session state
        serialized_state = self._serialize_state(state)
        
        # Store session data
        session_key = self._session_key(session_id)
        if ttl > 0:
            self.redis_client.setex(session_key, ttl, serialized_state)
        else:
            self.redis_client.set(session_key, serialized_state)
        
        # Store metadata
        expires_at = datetime.utcnow() + timedelta(seconds=ttl) if ttl > 0 else None
        size_bytes = len(serialized_state) if isinstance(serialized_state, (str, bytes)) else None
        
        metadata = SessionMetadata(
            session_id=session_id,
            created_at=state.created_at,
            last_accessed=datetime.utcnow(),
            expires_at=expires_at,
            size_bytes=size_bytes
        )
        
        metadata_key = self._metadata_key(session_id)
        metadata_data = metadata.model_dump_json()
        
        if ttl > 0:
            self.redis_client.setex(metadata_key, ttl, metadata_data)
        else:
            self.redis_client.set(metadata_key, metadata_data)
    
    def get_session(self, session_id: str) -> CRMSessionState:
        """Retrieve a session state from Redis."""
        session_key = self._session_key(session_id)
        serialized_state = self.redis_client.get(session_key)
        
        if serialized_state is None:
            raise SessionNotFoundError(f"Session {session_id} not found")
        
        # Update last accessed time in metadata
        metadata_key = self._metadata_key(session_id)
        metadata_data = self.redis_client.get(metadata_key)
        
        if metadata_data:
            try:
                metadata = SessionMetadata.model_validate_json(metadata_data)
                metadata.last_accessed = datetime.utcnow()
                
                # Get TTL and update metadata
                ttl = self.redis_client.ttl(session_key)
                if ttl > 0:
                    self.redis_client.setex(metadata_key, ttl, metadata.model_dump_json())
                else:
                    self.redis_client.set(metadata_key, metadata.model_dump_json())
            except Exception:
                # Ignore metadata update errors
                pass
        
        # Deserialize and return session state
        return self._deserialize_state(serialized_state)
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session from Redis."""
        session_key = self._session_key(session_id)
        metadata_key = self._metadata_key(session_id)
        
        # Delete both session data and metadata
        deleted_count = self.redis_client.delete(session_key, metadata_key)
        return deleted_count > 0
    
    def exists(self, session_id: str) -> bool:
        """Check if session exists in Redis."""
        session_key = self._session_key(session_id)
        return self.redis_client.exists(session_key) > 0
    
    def list_sessions(
        self, 
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[SessionMetadata]:
        """List session metadata from Redis."""
        # Get all metadata keys
        pattern = f"{self.key_prefix}meta:*"
        metadata_keys = self.redis_client.keys(pattern)
        
        sessions = []
        for key in metadata_keys:
            try:
                metadata_data = self.redis_client.get(key)
                if metadata_data:
                    metadata = SessionMetadata.model_validate_json(metadata_data)
                    sessions.append(metadata)
            except Exception:
                # Skip invalid metadata
                continue
        
        # Sort by last accessed time
        sessions.sort(key=lambda x: x.last_accessed, reverse=True)
        
        # Apply offset and limit
        if offset > 0:
            sessions = sessions[offset:]
        
        if limit:
            sessions = sessions[:limit]
        
        return sessions
    
    def cleanup_expired(self) -> int:
        """Clean up expired sessions (Redis handles this automatically)."""
        # Redis automatically expires keys with TTL
        # This method is here for interface compatibility
        return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        # Get all session keys
        session_pattern = f"{self.key_prefix}*"
        session_keys = self.redis_client.keys(session_pattern)
        
        # Filter out metadata keys
        data_keys = [key for key in session_keys if not key.endswith(":meta")]
        
        total_size = 0
        for key in data_keys:
            try:
                size = self.redis_client.memory_usage(key)
                if size:
                    total_size += size
            except Exception:
                # Ignore errors getting memory usage
                pass
        
        return {
            "store_type": "redis",
            "total_sessions": len(data_keys),
            "total_size_bytes": total_size,
            "average_size_bytes": total_size // len(data_keys) if data_keys else 0,
            "redis_info": self._get_redis_info()
        }
    
    def _get_redis_info(self) -> Dict[str, Any]:
        """Get Redis server information."""
        try:
            info = self.redis_client.info()
            return {
                "redis_version": info.get("redis_version"),
                "used_memory": info.get("used_memory"),
                "connected_clients": info.get("connected_clients"),
                "total_commands_processed": info.get("total_commands_processed")
            }
        except Exception:
            return {}


class SessionManager:
    """
    High-level session manager with pluggable storage backend.
    
    Provides the same interface as the existing session management
    but with pluggable storage and better error handling.
    """
    
    def __init__(
        self, 
        store: Optional[SessionStore] = None,
        default_ttl_seconds: int = 3600
    ):
        self.store = store or InMemorySessionStore(default_ttl_seconds)
        self.default_ttl_seconds = default_ttl_seconds
    
    def create_session(
        self, 
        contact_email: Optional[str] = None,
        company_domain: Optional[str] = None,
        session_id: Optional[str] = None,
        ttl_seconds: Optional[int] = None
    ) -> CRMSessionState:
        """
        Create a new session.
        
        Args:
            contact_email: Contact email for the session
            company_domain: Company domain for the session
            session_id: Custom session ID (generated if None)
            ttl_seconds: Time to live in seconds
            
        Returns:
            New session state
        """
        from .state_models import create_initial_crm_state
        
        state = create_initial_crm_state(
            contact_email=contact_email,
            company_domain=company_domain,
            session_id=session_id
        )
        
        self.store.store_session(
            state.session_id, 
            state, 
            ttl_seconds or self.default_ttl_seconds
        )
        
        return state
    
    def get_session(self, session_id: str) -> CRMSessionState:
        """Get a session by ID."""
        return self.store.get_session(session_id)
    
    def update_session(
        self, 
        session_id: str, 
        state: CRMSessionState,
        ttl_seconds: Optional[int] = None
    ) -> None:
        """Update a session."""
        state.update_timestamp()
        self.store.store_session(
            session_id, 
            state, 
            ttl_seconds or self.default_ttl_seconds
        )
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        return self.store.delete_session(session_id)
    
    def session_exists(self, session_id: str) -> bool:
        """Check if session exists."""
        return self.store.exists(session_id)
    
    def list_sessions(self, **kwargs) -> List[SessionMetadata]:
        """List sessions."""
        return self.store.list_sessions(**kwargs)
    
    def cleanup_expired(self) -> int:
        """Clean up expired sessions."""
        return self.store.cleanup_expired()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get session storage statistics."""
        return self.store.get_stats()
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on session storage."""
        try:
            # Try to create, retrieve, and delete a test session
            test_session_id = f"health_check_{datetime.utcnow().timestamp()}"
            test_state = self.create_session(session_id=test_session_id, ttl_seconds=60)
            
            retrieved_state = self.get_session(test_session_id)
            success = retrieved_state.session_id == test_session_id
            
            self.delete_session(test_session_id)
            
            return {
                "healthy": success,
                "store_type": type(self.store).__name__,
                "stats": self.get_stats()
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "store_type": type(self.store).__name__
            }


# Global session manager instance
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Get the global session manager."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager


def create_redis_session_manager(redis_url: str = "redis://localhost:6379") -> SessionManager:
    """Create session manager with Redis backend."""
    try:
        redis_store = RedisSessionStore(redis_url=redis_url)
        return SessionManager(store=redis_store)
    except ImportError:
        # Fallback to in-memory store if Redis not available
        return SessionManager()


# Convenience functions
def create_session(*args, **kwargs) -> CRMSessionState:
    """Create a new session."""
    return get_session_manager().create_session(*args, **kwargs)


def get_session(session_id: str) -> CRMSessionState:
    """Get a session by ID."""
    return get_session_manager().get_session(session_id)


def update_session(session_id: str, state: CRMSessionState) -> None:
    """Update a session."""
    get_session_manager().update_session(session_id, state)
