#!/usr/bin/env python3
"""
Tests for Idempotency System (Phase 9).

Tests idempotency key generation, duplicate detection,
and retry safety for HubSpot operations.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import threading
import time

from crm_agent.core.idempotency import (
    IdempotencyManager,
    IdempotencyKey,
    OperationResult,
    OperationType,
    InMemoryIdempotencyStore,
    get_idempotency_manager,
    generate_idempotency_key,
    check_duplicate_operation,
    record_operation_result
)


class TestIdempotencyKey:
    """Test suite for idempotency key model."""
    
    def test_key_creation(self):
        """Test idempotency key creation."""
        key = IdempotencyKey(
            key="test_key",
            operation_type=OperationType.UPDATE_CONTACT,
            resource_id="12345",
            field_hash="abc123",
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        
        assert key.key == "test_key"
        assert key.operation_type == OperationType.UPDATE_CONTACT
        assert key.resource_id == "12345"
        assert not key.is_expired()
    
    def test_key_expiration(self):
        """Test key expiration logic."""
        # Create expired key
        expired_key = IdempotencyKey(
            key="expired_key",
            operation_type=OperationType.CREATE_CONTACT,
            resource_id=None,
            field_hash="def456",
            created_at=datetime.utcnow() - timedelta(hours=25),
            expires_at=datetime.utcnow() - timedelta(hours=1)
        )
        
        assert expired_key.is_expired()
    
    def test_key_serialization(self):
        """Test key serialization to/from dict."""
        original_key = IdempotencyKey(
            key="serialize_test",
            operation_type=OperationType.CREATE_EMAIL,
            resource_id="email_123",
            field_hash="ghi789",
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=12),
            session_id="test_session",
            trace_id="test_trace"
        )
        
        # Serialize to dict
        key_dict = original_key.to_dict()
        
        # Deserialize from dict
        restored_key = IdempotencyKey.from_dict(key_dict)
        
        assert restored_key.key == original_key.key
        assert restored_key.operation_type == original_key.operation_type
        assert restored_key.resource_id == original_key.resource_id
        assert restored_key.session_id == original_key.session_id


class TestInMemoryIdempotencyStore:
    """Test suite for in-memory idempotency store."""
    
    @pytest.fixture
    def store(self):
        """Create fresh store for each test."""
        return InMemoryIdempotencyStore()
    
    def test_store_and_retrieve_key(self, store):
        """Test storing and retrieving idempotency keys."""
        key = IdempotencyKey(
            key="test_store",
            operation_type=OperationType.UPDATE_COMPANY,
            resource_id="company_123",
            field_hash="store_hash",
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        
        # Store key
        store.store_key(key)
        
        # Retrieve key
        retrieved_key = store.get_key("test_store")
        
        assert retrieved_key is not None
        assert retrieved_key.key == "test_store"
        assert retrieved_key.operation_type == OperationType.UPDATE_COMPANY
    
    def test_store_key_with_result(self, store):
        """Test storing key with operation result."""
        key = IdempotencyKey(
            key="test_result",
            operation_type=OperationType.CREATE_TASK,
            resource_id=None,
            field_hash="result_hash",
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        
        result = OperationResult(
            success=True,
            resource_id="task_456",
            idempotency_key="test_result"
        )
        
        # Store key with result
        store.store_key(key, result)
        
        # Retrieve result
        retrieved_result = store.get_result("test_result")
        
        assert retrieved_result is not None
        assert retrieved_result.success is True
        assert retrieved_result.resource_id == "task_456"
    
    def test_key_existence_check(self, store):
        """Test key existence checking."""
        key = IdempotencyKey(
            key="existence_test",
            operation_type=OperationType.CREATE_CONTACT,
            resource_id=None,
            field_hash="exist_hash",
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        
        # Should not exist initially
        assert not store.exists("existence_test")
        
        # Store key
        store.store_key(key)
        
        # Should exist now
        assert store.exists("existence_test")
    
    def test_expired_key_cleanup(self, store):
        """Test automatic cleanup of expired keys."""
        # Create expired key
        expired_key = IdempotencyKey(
            key="expired_cleanup",
            operation_type=OperationType.UPDATE_CONTACT,
            resource_id="contact_789",
            field_hash="expired_hash",
            created_at=datetime.utcnow() - timedelta(hours=25),
            expires_at=datetime.utcnow() - timedelta(hours=1)
        )
        
        # Store expired key
        store.store_key(expired_key)
        
        # Should not exist (cleaned up automatically)
        assert not store.exists("expired_cleanup")
        assert store.get_key("expired_cleanup") is None
    
    def test_cleanup_expired_method(self, store):
        """Test explicit cleanup of expired keys."""
        # Create mix of valid and expired keys
        valid_key = IdempotencyKey(
            key="valid_key",
            operation_type=OperationType.CREATE_DEAL,
            resource_id=None,
            field_hash="valid_hash",
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        
        expired_key = IdempotencyKey(
            key="expired_key",
            operation_type=OperationType.UPDATE_DEAL,
            resource_id="deal_123",
            field_hash="expired_hash",
            created_at=datetime.utcnow() - timedelta(hours=25),
            expires_at=datetime.utcnow() - timedelta(hours=1)
        )
        
        store.store_key(valid_key)
        store.store_key(expired_key)
        
        # Cleanup expired keys
        cleaned_count = store.cleanup_expired()
        
        assert cleaned_count == 1
        assert store.exists("valid_key")
        assert not store.exists("expired_key")


class TestIdempotencyManager:
    """Test suite for idempotency manager."""
    
    @pytest.fixture
    def manager(self):
        """Create fresh manager for each test."""
        return IdempotencyManager()
    
    def test_key_generation_deterministic(self, manager):
        """Test that key generation is deterministic."""
        field_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "555-1234"
        }
        
        # Generate same key twice
        key1 = manager.generate_key(
            operation_type=OperationType.UPDATE_CONTACT,
            resource_id="contact_123",
            field_data=field_data,
            session_id="test_session"
        )
        
        key2 = manager.generate_key(
            operation_type=OperationType.UPDATE_CONTACT,
            resource_id="contact_123",
            field_data=field_data,
            session_id="test_session"
        )
        
        # Keys should be identical
        assert key1.key == key2.key
        assert key1.field_hash == key2.field_hash
    
    def test_key_generation_different_data(self, manager):
        """Test that different data produces different keys."""
        field_data1 = {"name": "John Doe", "email": "john@example.com"}
        field_data2 = {"name": "Jane Doe", "email": "jane@example.com"}
        
        key1 = manager.generate_key(
            operation_type=OperationType.UPDATE_CONTACT,
            resource_id="contact_123",
            field_data=field_data1
        )
        
        key2 = manager.generate_key(
            operation_type=OperationType.UPDATE_CONTACT,
            resource_id="contact_123",
            field_data=field_data2
        )
        
        # Keys should be different
        assert key1.key != key2.key
        assert key1.field_hash != key2.field_hash
    
    def test_data_normalization_for_hashing(self, manager):
        """Test that data normalization produces consistent hashes."""
        # Different representations of same data
        data1 = {"name": "John", "age": 30, "active": True, "notes": None}
        data2 = {"age": 30, "name": "John", "active": True}  # Different order, no None
        data3 = {"name": "John", "age": 30, "active": True, "notes": None, "extra": None}
        
        hash1 = manager._hash_field_data(data1)
        hash2 = manager._hash_field_data(data2)
        hash3 = manager._hash_field_data(data3)
        
        # All should produce same hash (None values removed, order normalized)
        assert hash1 == hash2 == hash3
    
    def test_duplicate_detection(self, manager):
        """Test duplicate operation detection."""
        field_data = {"name": "Test Contact", "email": "test@example.com"}
        
        # Generate key
        key = manager.generate_key(
            operation_type=OperationType.CREATE_CONTACT,
            resource_id=None,
            field_data=field_data
        )
        
        # First check - should not be duplicate
        duplicate_result = manager.check_duplicate(key)
        assert duplicate_result is None
        
        # Record operation result
        result = manager.record_operation(
            key=key,
            success=True,
            resource_id="contact_new_123",
            response_data={"id": "contact_new_123"}
        )
        
        # Generate same key again
        key2 = manager.generate_key(
            operation_type=OperationType.CREATE_CONTACT,
            resource_id=None,
            field_data=field_data
        )
        
        # Second check - should be duplicate
        duplicate_result = manager.check_duplicate(key2)
        assert duplicate_result is not None
        assert duplicate_result.was_duplicate is True
        assert duplicate_result.resource_id == "contact_new_123"
    
    def test_hubspot_update_key_creation(self, manager):
        """Test HubSpot-specific update key creation."""
        properties = {
            "firstname": "John",
            "lastname": "Doe",
            "email": "john.doe@example.com"
        }
        
        key = manager.create_hubspot_update_key(
            object_type="contact",
            object_id="contact_456",
            properties=properties,
            session_id="hubspot_session"
        )
        
        assert key.operation_type == OperationType.UPDATE_CONTACT
        assert key.resource_id == "contact_456"
        assert key.session_id == "hubspot_session"
        assert "update_contact" in key.key
    
    def test_hubspot_create_key_creation(self, manager):
        """Test HubSpot-specific create key creation."""
        properties = {
            "name": "New Company",
            "domain": "newcompany.com",
            "industry": "Technology"
        }
        
        key = manager.create_hubspot_create_key(
            object_type="company",
            properties=properties,
            trace_id="create_trace"
        )
        
        assert key.operation_type == OperationType.CREATE_COMPANY
        assert key.resource_id is None  # No ID for creates
        assert key.trace_id == "create_trace"
        assert "create_company" in key.key
    
    def test_concurrent_key_generation(self, manager):
        """Test thread safety of key generation."""
        field_data = {"name": "Concurrent Test", "value": 42}
        results = []
        
        def generate_key_worker():
            key = manager.generate_key(
                operation_type=OperationType.UPDATE_CONTACT,
                resource_id="concurrent_test",
                field_data=field_data
            )
            results.append(key.key)
        
        # Start multiple threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=generate_key_worker)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # All keys should be identical (deterministic)
        assert len(set(results)) == 1
        assert len(results) == 10
    
    def test_operation_result_recording(self, manager):
        """Test recording operation results."""
        key = IdempotencyKey(
            key="result_test",
            operation_type=OperationType.CREATE_EMAIL,
            resource_id=None,
            field_hash="result_hash",
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        
        result = manager.record_operation(
            key=key,
            success=True,
            resource_id="email_789",
            response_data={"engagement_id": "email_789"},
            error_message=None
        )
        
        assert result.success is True
        assert result.resource_id == "email_789"
        assert result.idempotency_key == "result_test"
        assert result.was_duplicate is False
        assert isinstance(result.timestamp, datetime)


class TestOperationResult:
    """Test suite for operation result model."""
    
    def test_result_creation(self):
        """Test operation result creation."""
        result = OperationResult(
            success=True,
            resource_id="test_resource",
            response_data={"status": "created"},
            idempotency_key="test_key",
            was_duplicate=False
        )
        
        assert result.success is True
        assert result.resource_id == "test_resource"
        assert result.was_duplicate is False
        assert isinstance(result.timestamp, datetime)
    
    def test_failed_result(self):
        """Test failed operation result."""
        result = OperationResult(
            success=False,
            error_message="API rate limit exceeded",
            idempotency_key="failed_key"
        )
        
        assert result.success is False
        assert result.error_message == "API rate limit exceeded"
        assert result.resource_id is None


class TestGlobalFunctions:
    """Test suite for global convenience functions."""
    
    def test_global_manager_singleton(self):
        """Test that global manager is singleton."""
        manager1 = get_idempotency_manager()
        manager2 = get_idempotency_manager()
        
        assert manager1 is manager2
    
    def test_global_key_generation(self):
        """Test global key generation function."""
        key = generate_idempotency_key(
            operation_type=OperationType.CREATE_TASK,
            resource_id=None,
            field_data={"subject": "Test Task"}
        )
        
        assert isinstance(key, IdempotencyKey)
        assert key.operation_type == OperationType.CREATE_TASK
    
    def test_global_duplicate_check(self):
        """Test global duplicate check function."""
        key = generate_idempotency_key(
            operation_type=OperationType.UPDATE_COMPANY,
            resource_id="company_global",
            field_data={"name": "Global Test Company"}
        )
        
        # Should not be duplicate initially
        duplicate = check_duplicate_operation(key)
        assert duplicate is None
        
        # Record operation
        result = record_operation_result(
            key=key,
            success=True,
            resource_id="company_global"
        )
        
        # Now should be duplicate
        duplicate = check_duplicate_operation(key)
        assert duplicate is not None
        assert duplicate.was_duplicate is True


class TestRetryScenarios:
    """Test suite for retry scenarios and failure recovery."""
    
    def test_successful_retry_prevention(self):
        """Test that successful operations prevent unnecessary retries."""
        manager = IdempotencyManager()
        
        # Simulate initial successful operation
        field_data = {"subject": "Important Email", "body": "Test content"}
        key = manager.generate_key(
            operation_type=OperationType.CREATE_EMAIL,
            resource_id=None,
            field_data=field_data
        )
        
        # Record successful operation
        manager.record_operation(
            key=key,
            success=True,
            resource_id="email_success_123"
        )
        
        # Simulate retry attempt
        retry_key = manager.generate_key(
            operation_type=OperationType.CREATE_EMAIL,
            resource_id=None,
            field_data=field_data
        )
        
        # Should detect as duplicate
        duplicate_result = manager.check_duplicate(retry_key)
        assert duplicate_result is not None
        assert duplicate_result.success is True
        assert duplicate_result.resource_id == "email_success_123"
    
    def test_failed_operation_retry_allowed(self):
        """Test that failed operations allow retries."""
        manager = IdempotencyManager()
        
        field_data = {"name": "Retry Test Contact"}
        key = manager.generate_key(
            operation_type=OperationType.CREATE_CONTACT,
            resource_id=None,
            field_data=field_data
        )
        
        # Record failed operation
        manager.record_operation(
            key=key,
            success=False,
            error_message="Network timeout"
        )
        
        # Simulate retry with same data
        retry_key = manager.generate_key(
            operation_type=OperationType.CREATE_CONTACT,
            resource_id=None,
            field_data=field_data
        )
        
        # Should detect as duplicate but allow retry since original failed
        duplicate_result = manager.check_duplicate(retry_key)
        assert duplicate_result is not None
        assert duplicate_result.success is False
        assert duplicate_result.error_message == "Network timeout"
    
    def test_partial_failure_scenarios(self):
        """Test handling of partial failures and recovery."""
        manager = IdempotencyManager()
        
        # Simulate batch operation where some items succeed and some fail
        batch_data = [
            {"name": "Contact 1", "email": "contact1@example.com"},
            {"name": "Contact 2", "email": "contact2@example.com"},
            {"name": "Contact 3", "email": "contact3@example.com"}
        ]
        
        keys = []
        for i, contact_data in enumerate(batch_data):
            key = manager.generate_key(
                operation_type=OperationType.CREATE_CONTACT,
                resource_id=None,
                field_data=contact_data,
                custom_suffix=f"batch_{i}"
            )
            keys.append(key)
        
        # Simulate partial success
        manager.record_operation(keys[0], True, "contact_1_success")
        manager.record_operation(keys[1], False, error_message="Validation error")
        manager.record_operation(keys[2], True, "contact_3_success")
        
        # Check retry behavior
        for i, key in enumerate(keys):
            duplicate = manager.check_duplicate(key)
            assert duplicate is not None
            
            if i == 1:  # Failed operation
                assert duplicate.success is False
            else:  # Successful operations
                assert duplicate.success is True
