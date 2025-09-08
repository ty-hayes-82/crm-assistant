"""
Idempotency System for Phase 9.

This module provides idempotency key generation and management for all HubSpot writes
to ensure safe retries and prevent duplicate operations.
"""

import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Set, Union, List
from abc import ABC, abstractmethod
import threading
from dataclasses import dataclass
from enum import Enum

from pydantic import BaseModel, Field


class OperationType(str, Enum):
    """Types of operations that can be made idempotent."""
    CREATE_CONTACT = "create_contact"
    UPDATE_CONTACT = "update_contact"
    CREATE_COMPANY = "create_company"
    UPDATE_COMPANY = "update_company"
    CREATE_DEAL = "create_deal"
    UPDATE_DEAL = "update_deal"
    CREATE_EMAIL = "create_email"
    CREATE_TASK = "create_task"
    CREATE_NOTE = "create_note"
    CREATE_ASSOCIATION = "create_association"
    DELETE_ASSOCIATION = "delete_association"


@dataclass
class IdempotencyKey:
    """Idempotency key with metadata."""
    key: str
    operation_type: OperationType
    resource_id: Optional[str]
    field_hash: str
    created_at: datetime
    expires_at: datetime
    session_id: Optional[str] = None
    trace_id: Optional[str] = None
    
    def is_expired(self) -> bool:
        """Check if the key is expired."""
        return datetime.utcnow() > self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "key": self.key,
            "operation_type": self.operation_type.value,
            "resource_id": self.resource_id,
            "field_hash": self.field_hash,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "session_id": self.session_id,
            "trace_id": self.trace_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IdempotencyKey':
        """Create from dictionary."""
        return cls(
            key=data["key"],
            operation_type=OperationType(data["operation_type"]),
            resource_id=data.get("resource_id"),
            field_hash=data["field_hash"],
            created_at=datetime.fromisoformat(data["created_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]),
            session_id=data.get("session_id"),
            trace_id=data.get("trace_id")
        )


class OperationResult(BaseModel):
    """Result of an idempotent operation."""
    success: bool
    resource_id: Optional[str] = None
    response_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    was_duplicate: bool = False
    idempotency_key: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class IdempotencyStore(ABC):
    """Abstract base class for idempotency key storage."""
    
    @abstractmethod
    def store_key(self, key: IdempotencyKey, result: Optional[OperationResult] = None) -> None:
        """Store an idempotency key with optional result."""
        pass
    
    @abstractmethod
    def get_key(self, key: str) -> Optional[IdempotencyKey]:
        """Get an idempotency key by key string."""
        pass
    
    @abstractmethod
    def get_result(self, key: str) -> Optional[OperationResult]:
        """Get operation result by idempotency key."""
        pass
    
    @abstractmethod
    def cleanup_expired(self) -> int:
        """Clean up expired keys and return count of removed keys."""
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        pass


class InMemoryIdempotencyStore(IdempotencyStore):
    """In-memory implementation of idempotency store."""
    
    def __init__(self):
        self._keys: Dict[str, IdempotencyKey] = {}
        self._results: Dict[str, OperationResult] = {}
        self._lock = threading.RLock()
    
    def store_key(self, key: IdempotencyKey, result: Optional[OperationResult] = None) -> None:
        """Store an idempotency key with optional result."""
        with self._lock:
            self._keys[key.key] = key
            if result:
                self._results[key.key] = result
    
    def get_key(self, key: str) -> Optional[IdempotencyKey]:
        """Get an idempotency key by key string."""
        with self._lock:
            idem_key = self._keys.get(key)
            if idem_key and idem_key.is_expired():
                # Clean up expired key
                del self._keys[key]
                self._results.pop(key, None)
                return None
            return idem_key
    
    def get_result(self, key: str) -> Optional[OperationResult]:
        """Get operation result by idempotency key."""
        with self._lock:
            # Check if key exists and is not expired
            if not self.exists(key):
                return None
            return self._results.get(key)
    
    def cleanup_expired(self) -> int:
        """Clean up expired keys and return count of removed keys."""
        with self._lock:
            expired_keys = [
                key for key, idem_key in self._keys.items() 
                if idem_key.is_expired()
            ]
            
            for key in expired_keys:
                del self._keys[key]
                self._results.pop(key, None)
            
            return len(expired_keys)
    
    def exists(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        with self._lock:
            idem_key = self._keys.get(key)
            if not idem_key:
                return False
            
            if idem_key.is_expired():
                # Clean up expired key
                del self._keys[key]
                self._results.pop(key, None)
                return False
            
            return True


class IdempotencyManager:
    """
    Manager for idempotency keys and duplicate operation detection.
    
    Provides deterministic key generation and storage for all HubSpot operations
    to ensure safe retries without duplicating data.
    """
    
    def __init__(
        self, 
        store: Optional[IdempotencyStore] = None,
        default_ttl_hours: int = 24
    ):
        self.store = store or InMemoryIdempotencyStore()
        self.default_ttl_hours = default_ttl_hours
    
    def generate_key(
        self,
        operation_type: OperationType,
        resource_id: Optional[str],
        field_data: Dict[str, Any],
        session_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        custom_suffix: Optional[str] = None
    ) -> IdempotencyKey:
        """
        Generate a deterministic idempotency key for an operation.
        
        Args:
            operation_type: Type of operation being performed
            resource_id: ID of the resource being modified (None for creates)
            field_data: Data being written (for hash generation)
            session_id: Current session ID
            trace_id: Current trace ID
            custom_suffix: Optional custom suffix for key uniqueness
            
        Returns:
            IdempotencyKey with deterministic key string
        """
        # Create deterministic hash of field data
        field_hash = self._hash_field_data(field_data)
        
        # Create key components
        key_parts = [
            operation_type.value,
            resource_id or "new",
            field_hash[:16],  # First 16 chars of hash
        ]
        
        if custom_suffix:
            key_parts.append(custom_suffix)
        
        # Generate key string
        key_string = "_".join(key_parts)
        
        # Create expiration time
        expires_at = datetime.utcnow() + timedelta(hours=self.default_ttl_hours)
        
        return IdempotencyKey(
            key=key_string,
            operation_type=operation_type,
            resource_id=resource_id,
            field_hash=field_hash,
            created_at=datetime.utcnow(),
            expires_at=expires_at,
            session_id=session_id,
            trace_id=trace_id
        )
    
    def _hash_field_data(self, field_data: Dict[str, Any]) -> str:
        """Create deterministic hash of field data."""
        # Normalize the data for consistent hashing
        normalized_data = self._normalize_for_hash(field_data)
        
        # Create JSON string with sorted keys
        json_str = json.dumps(normalized_data, sort_keys=True, separators=(',', ':'))
        
        # Generate SHA-256 hash
        return hashlib.sha256(json_str.encode('utf-8')).hexdigest()
    
    def _normalize_for_hash(self, data: Any) -> Any:
        """Normalize data for consistent hashing."""
        if isinstance(data, dict):
            # Remove None values and sort keys
            normalized = {}
            for key, value in data.items():
                if value is not None:
                    normalized[key] = self._normalize_for_hash(value)
            return normalized
        elif isinstance(data, list):
            # Sort lists if they contain comparable items
            try:
                return sorted([self._normalize_for_hash(item) for item in data])
            except TypeError:
                # If items aren't comparable, keep original order
                return [self._normalize_for_hash(item) for item in data]
        elif isinstance(data, (str, int, float, bool)):
            return data
        elif data is None:
            return None
        else:
            # Convert other types to string
            return str(data)
    
    def check_duplicate(self, key: IdempotencyKey) -> Optional[OperationResult]:
        """
        Check if operation is a duplicate and return previous result if so.
        
        Args:
            key: Idempotency key to check
            
        Returns:
            Previous operation result if duplicate, None if new operation
        """
        existing_key = self.store.get_key(key.key)
        if not existing_key:
            return None
        
        # Check if the operation details match
        if (existing_key.operation_type == key.operation_type and
            existing_key.resource_id == key.resource_id and
            existing_key.field_hash == key.field_hash):
            
            # This is a duplicate operation
            result = self.store.get_result(key.key)
            if result:
                # Mark as duplicate
                result.was_duplicate = True
            return result
        
        return None
    
    def record_operation(
        self,
        key: IdempotencyKey,
        success: bool,
        resource_id: Optional[str] = None,
        response_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> OperationResult:
        """
        Record the result of an operation.
        
        Args:
            key: Idempotency key for the operation
            success: Whether operation succeeded
            resource_id: ID of created/modified resource
            response_data: Response data from API
            error_message: Error message if failed
            
        Returns:
            OperationResult with recorded details
        """
        result = OperationResult(
            success=success,
            resource_id=resource_id,
            response_data=response_data,
            error_message=error_message,
            idempotency_key=key.key,
            was_duplicate=False
        )
        
        # Store the key and result
        self.store.store_key(key, result)
        
        return result
    
    def get_operation_history(
        self,
        resource_id: Optional[str] = None,
        operation_type: Optional[OperationType] = None,
        session_id: Optional[str] = None
    ) -> List[OperationResult]:
        """
        Get operation history (limited implementation for in-memory store).
        
        Note: This is a basic implementation. A production system would
        need a more sophisticated query interface.
        """
        # This is a simplified implementation
        # In a real system, you'd want proper indexing and querying
        return []
    
    def cleanup_expired_keys(self) -> int:
        """Clean up expired idempotency keys."""
        return self.store.cleanup_expired()
    
    def create_hubspot_update_key(
        self,
        object_type: str,  # "contact", "company", etc.
        object_id: str,
        properties: Dict[str, Any],
        session_id: Optional[str] = None,
        trace_id: Optional[str] = None
    ) -> IdempotencyKey:
        """
        Create idempotency key for HubSpot update operations.
        
        Args:
            object_type: Type of HubSpot object
            object_id: ID of the object being updated
            properties: Properties being updated
            session_id: Current session ID
            trace_id: Current trace ID
            
        Returns:
            IdempotencyKey for the update operation
        """
        operation_type = {
            "contact": OperationType.UPDATE_CONTACT,
            "company": OperationType.UPDATE_COMPANY,
            "deal": OperationType.UPDATE_DEAL
        }.get(object_type, OperationType.UPDATE_CONTACT)
        
        return self.generate_key(
            operation_type=operation_type,
            resource_id=object_id,
            field_data=properties,
            session_id=session_id,
            trace_id=trace_id
        )
    
    def create_hubspot_create_key(
        self,
        object_type: str,
        properties: Dict[str, Any],
        session_id: Optional[str] = None,
        trace_id: Optional[str] = None
    ) -> IdempotencyKey:
        """
        Create idempotency key for HubSpot create operations.
        
        Args:
            object_type: Type of HubSpot object
            properties: Properties for new object
            session_id: Current session ID
            trace_id: Current trace ID
            
        Returns:
            IdempotencyKey for the create operation
        """
        operation_type = {
            "contact": OperationType.CREATE_CONTACT,
            "company": OperationType.CREATE_COMPANY,
            "deal": OperationType.CREATE_DEAL,
            "email": OperationType.CREATE_EMAIL,
            "task": OperationType.CREATE_TASK,
            "note": OperationType.CREATE_NOTE
        }.get(object_type, OperationType.CREATE_CONTACT)
        
        return self.generate_key(
            operation_type=operation_type,
            resource_id=None,  # No ID for creates
            field_data=properties,
            session_id=session_id,
            trace_id=trace_id
        )


# Global idempotency manager instance
_idempotency_manager: Optional[IdempotencyManager] = None


def get_idempotency_manager() -> IdempotencyManager:
    """Get the global idempotency manager."""
    global _idempotency_manager
    if _idempotency_manager is None:
        _idempotency_manager = IdempotencyManager()
    return _idempotency_manager


def generate_idempotency_key(*args, **kwargs) -> IdempotencyKey:
    """Generate an idempotency key."""
    return get_idempotency_manager().generate_key(*args, **kwargs)


def check_duplicate_operation(key: IdempotencyKey) -> Optional[OperationResult]:
    """Check if operation is a duplicate."""
    return get_idempotency_manager().check_duplicate(key)


def record_operation_result(*args, **kwargs) -> OperationResult:
    """Record operation result."""
    return get_idempotency_manager().record_operation(*args, **kwargs)
