#!/usr/bin/env python3
"""
Tests for Session Store System (Phase 9).

Tests pluggable session storage with in-memory and Redis backends,
session persistence, and recovery scenarios.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import threading
import time
import tempfile

from crm_agent.core.session_store import (
    SessionManager,
    InMemorySessionStore,
    RedisSessionStore,
    SessionMetadata,
    SessionNotFoundError,
    SessionExpiredError,
    SessionStoreError,
    get_session_manager,
    create_redis_session_manager,
    create_session,
    get_session,
    update_session
)
from crm_agent.core.state_models import CRMSessionState, create_initial_crm_state


class TestSessionMetadata:
    """Test suite for session metadata model."""
    
    def test_metadata_creation(self):
        """Test session metadata creation."""
        metadata = SessionMetadata(
            session_id="test_session",
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=1),
            size_bytes=1024
        )
        
        assert metadata.session_id == "test_session"
        assert metadata.size_bytes == 1024
        assert metadata.version == "1.0.0"


class TestInMemorySessionStore:
    """Test suite for in-memory session store."""
    
    @pytest.fixture
    def store(self):
        """Create fresh store for each test."""
        return InMemorySessionStore(default_ttl_seconds=3600)
    
    @pytest.fixture
    def sample_session(self):
        """Create sample session state."""
        return create_initial_crm_state(
            contact_email="test@example.com",
            company_domain="example.com",
            session_id="test_session"
        )
    
    def test_store_and_retrieve_session(self, store, sample_session):
        """Test storing and retrieving session."""
        # Store session
        store.store_session("test_session", sample_session, ttl_seconds=3600)
        
        # Retrieve session
        retrieved_session = store.get_session("test_session")
        
        assert retrieved_session.session_id == "test_session"
        assert retrieved_session.contact_email == "test@example.com"
        assert retrieved_session.company_domain == "example.com"
    
    def test_session_not_found(self, store):
        """Test handling of non-existent sessions."""
        with pytest.raises(SessionNotFoundError):
            store.get_session("nonexistent_session")
    
    def test_session_expiration(self, store, sample_session):
        """Test session expiration handling."""
        # Store session with very short TTL
        store.store_session("short_ttl_session", sample_session, ttl_seconds=1)
        
        # Should be retrievable immediately
        retrieved = store.get_session("short_ttl_session")
        assert retrieved.session_id == "short_ttl_session"
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Should be expired now
        with pytest.raises(SessionExpiredError):
            store.get_session("short_ttl_session")
    
    def test_session_existence_check(self, store, sample_session):
        """Test session existence checking."""
        # Should not exist initially
        assert not store.exists("existence_test")
        
        # Store session
        store.store_session("existence_test", sample_session)
        
        # Should exist now
        assert store.exists("existence_test")
    
    def test_session_deletion(self, store, sample_session):
        """Test session deletion."""
        # Store session
        store.store_session("delete_test", sample_session)
        assert store.exists("delete_test")
        
        # Delete session
        deleted = store.delete_session("delete_test")
        assert deleted is True
        assert not store.exists("delete_test")
        
        # Deleting non-existent session should return False
        deleted_again = store.delete_session("delete_test")
        assert deleted_again is False
    
    def test_list_sessions(self, store):
        """Test listing sessions."""
        # Create multiple sessions
        sessions = []
        for i in range(5):
            session = create_initial_crm_state(session_id=f"list_test_{i}")
            store.store_session(f"list_test_{i}", session)
            sessions.append(session)
        
        # List all sessions
        session_list = store.list_sessions()
        assert len(session_list) == 5
        
        # Test limit
        limited_list = store.list_sessions(limit=3)
        assert len(limited_list) == 3
        
        # Test offset
        offset_list = store.list_sessions(offset=2, limit=2)
        assert len(offset_list) == 2
    
    def test_cleanup_expired_sessions(self, store):
        """Test cleanup of expired sessions."""
        # Create mix of valid and expired sessions
        valid_session = create_initial_crm_state(session_id="valid")
        expired_session = create_initial_crm_state(session_id="expired")
        
        store.store_session("valid", valid_session, ttl_seconds=3600)
        store.store_session("expired", expired_session, ttl_seconds=1)
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Cleanup expired
        cleaned_count = store.cleanup_expired()
        assert cleaned_count == 1
        
        # Valid session should still exist
        assert store.exists("valid")
        assert not store.exists("expired")
    
    def test_storage_statistics(self, store, sample_session):
        """Test storage statistics."""
        # Store some sessions
        for i in range(3):
            session = create_initial_crm_state(session_id=f"stats_test_{i}")
            store.store_session(f"stats_test_{i}", session)
        
        stats = store.get_stats()
        
        assert stats["store_type"] == "in_memory"
        assert stats["total_sessions"] == 3
        assert stats["total_size_bytes"] > 0
        assert stats["average_size_bytes"] > 0
    
    def test_concurrent_access(self, store):
        """Test thread safety of session store."""
        results = []
        
        def worker(worker_id):
            session = create_initial_crm_state(session_id=f"concurrent_{worker_id}")
            store.store_session(f"concurrent_{worker_id}", session)
            
            retrieved = store.get_session(f"concurrent_{worker_id}")
            results.append(retrieved.session_id)
        
        # Start multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=worker, args=[i])
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # All operations should succeed
        assert len(results) == 10
        assert len(set(results)) == 10  # All unique


class TestRedisSessionStore:
    """Test suite for Redis session store (with mocking)."""
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client."""
        with patch('crm_agent.core.session_store.redis') as mock_redis_module:
            mock_client = MagicMock()
            mock_redis_module.from_url.return_value = mock_client
            
            # Mock successful ping
            mock_client.ping.return_value = True
            
            yield mock_client
    
    def test_redis_store_creation(self, mock_redis):
        """Test Redis store creation."""
        store = RedisSessionStore(
            redis_url="redis://localhost:6379",
            key_prefix="test:",
            default_ttl_seconds=1800
        )
        
        assert store.key_prefix == "test:"
        assert store.default_ttl_seconds == 1800
        mock_redis.ping.assert_called_once()
    
    def test_redis_store_session(self, mock_redis):
        """Test storing session in Redis."""
        store = RedisSessionStore()
        session = create_initial_crm_state(session_id="redis_test")
        
        # Mock Redis operations
        mock_redis.setex.return_value = True
        mock_redis.set.return_value = True
        
        # Store session
        store.store_session("redis_test", session, ttl_seconds=3600)
        
        # Verify Redis calls
        assert mock_redis.setex.call_count >= 1  # At least one setex call
    
    def test_redis_get_session(self, mock_redis):
        """Test retrieving session from Redis."""
        store = RedisSessionStore()
        session = create_initial_crm_state(session_id="redis_get_test")
        
        # Mock Redis get to return serialized session
        serialized_session = session.model_dump_json()
        mock_redis.get.return_value = serialized_session
        
        # Retrieve session
        retrieved = store.get_session("redis_get_test")
        
        assert retrieved.session_id == "redis_get_test"
        mock_redis.get.assert_called()
    
    def test_redis_session_not_found(self, mock_redis):
        """Test Redis session not found handling."""
        store = RedisSessionStore()
        
        # Mock Redis get to return None
        mock_redis.get.return_value = None
        
        with pytest.raises(SessionNotFoundError):
            store.get_session("nonexistent")
    
    def test_redis_connection_error(self):
        """Test Redis connection error handling."""
        with patch('crm_agent.core.session_store.redis') as mock_redis_module:
            mock_client = MagicMock()
            mock_redis_module.from_url.return_value = mock_client
            
            # Mock connection failure
            mock_client.ping.side_effect = Exception("Connection failed")
            
            with pytest.raises(SessionStoreError):
                RedisSessionStore()
    
    def test_redis_import_error_handling(self):
        """Test handling when Redis is not installed."""
        with patch('crm_agent.core.session_store.redis', None):
            # Should raise ImportError when Redis module not available
            with pytest.raises(ImportError):
                RedisSessionStore()


class TestSessionManager:
    """Test suite for session manager."""
    
    @pytest.fixture
    def manager(self):
        """Create session manager with in-memory store."""
        return SessionManager(default_ttl_seconds=3600)
    
    def test_create_session(self, manager):
        """Test session creation."""
        session = manager.create_session(
            contact_email="manager@example.com",
            company_domain="manager.com",
            ttl_seconds=7200
        )
        
        assert session.contact_email == "manager@example.com"
        assert session.company_domain == "manager.com"
        assert session.session_id is not None
    
    def test_get_and_update_session(self, manager):
        """Test getting and updating sessions."""
        # Create session
        session = manager.create_session(session_id="update_test")
        
        # Modify session
        session.contact_data = {"name": "Updated Name"}
        
        # Update session
        manager.update_session("update_test", session)
        
        # Retrieve updated session
        retrieved = manager.get_session("update_test")
        assert retrieved.contact_data["name"] == "Updated Name"
    
    def test_session_existence_and_deletion(self, manager):
        """Test session existence check and deletion."""
        # Create session
        session = manager.create_session(session_id="delete_manager_test")
        
        # Should exist
        assert manager.session_exists("delete_manager_test")
        
        # Delete session
        deleted = manager.delete_session("delete_manager_test")
        assert deleted is True
        
        # Should not exist anymore
        assert not manager.session_exists("delete_manager_test")
    
    def test_list_sessions(self, manager):
        """Test listing sessions through manager."""
        # Create multiple sessions
        for i in range(3):
            manager.create_session(session_id=f"list_manager_{i}")
        
        sessions = manager.list_sessions()
        assert len(sessions) >= 3
        
        # Test filtering
        limited = manager.list_sessions(limit=2)
        assert len(limited) == 2
    
    def test_cleanup_and_stats(self, manager):
        """Test cleanup and statistics through manager."""
        # Create sessions
        manager.create_session(session_id="cleanup_test_1")
        manager.create_session(session_id="cleanup_test_2")
        
        # Get stats
        stats = manager.get_stats()
        assert stats["total_sessions"] >= 2
        assert stats["store_type"] == "InMemorySessionStore"
    
    def test_health_check(self, manager):
        """Test session manager health check."""
        health = manager.health_check()
        
        assert "healthy" in health
        assert "store_type" in health
        assert health["healthy"] is True
    
    def test_health_check_failure(self):
        """Test health check with store failure."""
        # Create manager with mock store that fails
        mock_store = Mock()
        mock_store.store_session.side_effect = Exception("Store failure")
        
        manager = SessionManager(store=mock_store)
        health = manager.health_check()
        
        assert health["healthy"] is False
        assert "error" in health


class TestGlobalFunctions:
    """Test suite for global convenience functions."""
    
    def test_global_session_manager_singleton(self):
        """Test that global session manager is singleton."""
        manager1 = get_session_manager()
        manager2 = get_session_manager()
        
        assert manager1 is manager2
    
    def test_global_create_session(self):
        """Test global create_session function."""
        session = create_session(
            contact_email="global@example.com",
            session_id="global_test"
        )
        
        assert session.contact_email == "global@example.com"
        assert session.session_id == "global_test"
    
    def test_global_get_session(self):
        """Test global get_session function."""
        # Create session first
        created = create_session(session_id="global_get_test")
        
        # Retrieve using global function
        retrieved = get_session("global_get_test")
        
        assert retrieved.session_id == "global_get_test"
    
    def test_global_update_session(self):
        """Test global update_session function."""
        # Create and modify session
        session = create_session(session_id="global_update_test")
        session.contact_data = {"updated": True}
        
        # Update using global function
        update_session("global_update_test", session)
        
        # Verify update
        retrieved = get_session("global_update_test")
        assert retrieved.contact_data["updated"] is True
    
    def test_create_redis_session_manager_fallback(self):
        """Test Redis session manager creation with fallback."""
        # Mock Redis import failure
        with patch('crm_agent.core.session_store.RedisSessionStore') as mock_redis_store:
            mock_redis_store.side_effect = ImportError("Redis not available")
            
            # Should fallback to in-memory store
            manager = create_redis_session_manager()
            
            assert isinstance(manager, SessionManager)
            # Should use in-memory store as fallback
            assert isinstance(manager.store, InMemorySessionStore)


class TestSessionPersistenceAndRecovery:
    """Test suite for session persistence and recovery scenarios."""
    
    def test_session_state_preservation(self):
        """Test that session state is properly preserved."""
        manager = SessionManager()
        
        # Create session with complex state
        session = manager.create_session(session_id="preservation_test")
        session.contact_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "555-1234"
        }
        session.company_data = {
            "name": "Test Company",
            "industry": "Technology"
        }
        session.enrichment_results = [
            {"source": "web", "data": {"revenue": "10M"}}
        ]
        session.lead_scores = {"fit": 85, "intent": 70, "total": 78}
        
        # Update session
        manager.update_session("preservation_test", session)
        
        # Retrieve and verify all data preserved
        retrieved = manager.get_session("preservation_test")
        
        assert retrieved.contact_data["name"] == "John Doe"
        assert retrieved.company_data["industry"] == "Technology"
        assert len(retrieved.enrichment_results) == 1
        assert retrieved.lead_scores["total"] == 78
    
    def test_session_recovery_after_failure(self):
        """Test session recovery scenarios."""
        manager = SessionManager()
        
        # Create session
        session = manager.create_session(session_id="recovery_test")
        session.contact_data = {"name": "Recovery Test"}
        manager.update_session("recovery_test", session)
        
        # Simulate system restart by creating new manager
        new_manager = SessionManager(store=manager.store)
        
        # Should be able to recover session
        recovered = new_manager.get_session("recovery_test")
        assert recovered.contact_data["name"] == "Recovery Test"
    
    def test_partial_failure_handling(self):
        """Test handling of partial failures in session operations."""
        manager = SessionManager()
        
        # Create session
        session = manager.create_session(session_id="partial_failure_test")
        
        # Mock store failure on update
        original_store = manager.store
        manager.store = Mock(spec=original_store)
        manager.store.store_session.side_effect = Exception("Storage failure")
        
        # Update should raise exception
        with pytest.raises(Exception):
            manager.update_session("partial_failure_test", session)
        
        # Restore original store
        manager.store = original_store
        
        # Original session should still be retrievable
        retrieved = manager.get_session("partial_failure_test")
        assert retrieved.session_id == "partial_failure_test"
    
    def test_concurrent_session_access(self):
        """Test concurrent access to same session."""
        manager = SessionManager()
        session = manager.create_session(session_id="concurrent_test")
        
        results = []
        errors = []
        
        def worker(worker_id):
            try:
                # Get session
                s = manager.get_session("concurrent_test")
                
                # Modify session
                s.contact_data[f"worker_{worker_id}"] = f"data_{worker_id}"
                
                # Update session
                manager.update_session("concurrent_test", s)
                
                results.append(worker_id)
            except Exception as e:
                errors.append((worker_id, str(e)))
        
        # Start multiple workers
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=[i])
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Should have some successful operations
        assert len(results) > 0
        
        # Final session should contain some worker data
        final_session = manager.get_session("concurrent_test")
        worker_keys = [key for key in final_session.contact_data.keys() if key.startswith("worker_")]
        assert len(worker_keys) > 0
    
    def test_session_expiration_and_cleanup(self):
        """Test session expiration and automatic cleanup."""
        manager = SessionManager(default_ttl_seconds=2)  # Short TTL for testing
        
        # Create session
        session = manager.create_session(session_id="expiration_test")
        
        # Should exist initially
        assert manager.session_exists("expiration_test")
        
        # Wait for expiration
        time.sleep(2.1)
        
        # Should be expired/cleaned up
        with pytest.raises((SessionNotFoundError, SessionExpiredError)):
            manager.get_session("expiration_test")
    
    def test_large_session_data_handling(self):
        """Test handling of large session data."""
        manager = SessionManager()
        
        # Create session with large data
        session = manager.create_session(session_id="large_data_test")
        
        # Add large amount of data
        large_data = {f"item_{i}": f"data_{i}" * 100 for i in range(1000)}
        session.contact_data = large_data
        
        # Should be able to store and retrieve
        manager.update_session("large_data_test", session)
        retrieved = manager.get_session("large_data_test")
        
        assert len(retrieved.contact_data) == 1000
        assert retrieved.contact_data["item_500"] == "data_500" * 100
