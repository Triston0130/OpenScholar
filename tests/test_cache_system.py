# tests/test_cache_system.py
"""
Unit tests for caching system
Tests Redis caching, fallback cache, and cache operations
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
from app.cache.redis_cache import (
    CacheKeyBuilder,
    SimpleCache,
    RedisCache,
    CacheManager
)

class TestCacheKeyBuilder:
    """Test cache key generation"""
    
    def test_search_results_key_generation(self):
        """Test generation of search results cache keys"""
        query = "machine learning"
        params = {"year_start": 2020, "year_end": 2024, "limit": 50}
        
        key1 = CacheKeyBuilder.search_results_key(query, **params)
        key2 = CacheKeyBuilder.search_results_key(query, **params)
        
        # Same parameters should generate same key
        assert key1 == key2
        assert key1.startswith("search_results:")
    
    def test_search_results_key_uniqueness(self):
        """Test that different parameters generate different keys"""
        base_query = "education"
        
        key1 = CacheKeyBuilder.search_results_key(base_query, year_start=2020)
        key2 = CacheKeyBuilder.search_results_key(base_query, year_start=2021)
        
        assert key1 != key2
    
    def test_paper_details_key(self):
        """Test paper details key generation"""
        paper_id = "10.1000/example"
        key = CacheKeyBuilder.paper_details_key(paper_id)
        
        assert key == f"paper_details:{paper_id}"
    
    def test_api_response_key(self):
        """Test API response key generation"""
        api_name = "semantic_scholar"
        query_hash = "abc123"
        
        key = CacheKeyBuilder.api_response_key(api_name, query_hash)
        assert key == f"api_response:{api_name}:{query_hash}"

class TestSimpleCache:
    """Test simple in-memory cache fallback"""
    
    @pytest.mark.asyncio
    async def test_simple_cache_operations(self):
        """Test basic cache operations"""
        cache = SimpleCache()
        await cache.connect()
        
        # Test set and get
        await cache.set("test_key", "test_value", ttl=60)
        value = await cache.get("test_key")
        assert value == "test_value"
        
        # Test non-existent key
        value = await cache.get("non_existent")
        assert value is None
    
    @pytest.mark.asyncio
    async def test_simple_cache_ttl(self):
        """Test TTL functionality in simple cache"""
        cache = SimpleCache()
        await cache.connect()
        
        # Set with very short TTL (this is a mock test)
        await cache.set("short_ttl_key", "value", ttl=1)
        
        # Value should exist immediately
        value = await cache.get("short_ttl_key")
        assert value == "value"
        
        # Simulate TTL expiry by manipulating internal cache
        import datetime
        cache._cache["short_ttl_key"]["expires"] = datetime.datetime.now() - datetime.timedelta(seconds=1)
        
        value = await cache.get("short_ttl_key")
        assert value is None
    
    @pytest.mark.asyncio
    async def test_simple_cache_delete(self):
        """Test cache deletion"""
        cache = SimpleCache()
        await cache.connect()
        
        await cache.set("delete_key", "value")
        assert await cache.get("delete_key") == "value"
        
        deleted = await cache.delete("delete_key")
        assert deleted is True
        assert await cache.get("delete_key") is None

@pytest.mark.asyncio
class TestRedisCache:
    """Test Redis cache implementation"""
    
    async def test_redis_cache_initialization(self):
        """Test Redis cache initialization"""
        with patch('redis.asyncio.from_url') as mock_redis:
            mock_client = AsyncMock()
            mock_client.ping = AsyncMock(return_value=True)
            mock_redis.return_value = mock_client
            
            cache = RedisCache()
            success = await cache.connect()
            
            assert success is True
            assert cache.redis_client is not None
    
    async def test_redis_connection_failure(self):
        """Test Redis connection failure handling"""
        with patch('redis.asyncio.from_url') as mock_redis:
            mock_redis.side_effect = Exception("Connection failed")
            
            cache = RedisCache()
            success = await cache.connect()
            
            assert success is False
            assert cache.redis_client is None
    
    async def test_redis_cache_operations(self):
        """Test Redis cache set/get operations"""
        with patch('redis.asyncio.from_url') as mock_redis:
            mock_client = AsyncMock()
            mock_client.ping = AsyncMock(return_value=True)
            mock_client.set = AsyncMock(return_value=True)
            mock_client.get = AsyncMock(return_value='{"test": "value"}')
            mock_redis.return_value = mock_client
            
            cache = RedisCache()
            await cache.connect()
            
            # Test set
            result = await cache.set("test_key", {"test": "value"}, ttl=300)
            assert result is True
            mock_client.set.assert_called_once()
            
            # Test get
            value = await cache.get("test_key")
            assert value == {"test": "value"}
    
    async def test_redis_cache_serialization(self):
        """Test JSON serialization in Redis cache"""
        with patch('redis.asyncio.from_url') as mock_redis:
            mock_client = AsyncMock()
            mock_client.ping = AsyncMock(return_value=True)
            mock_client.set = AsyncMock(return_value=True)
            mock_redis.return_value = mock_client
            
            cache = RedisCache()
            await cache.connect()
            
            # Test complex object serialization
            complex_data = {
                "papers": [
                    {"title": "Test Paper", "year": 2023},
                    {"title": "Another Paper", "year": 2024}
                ],
                "total": 2
            }
            
            await cache.set("complex_key", complex_data)
            
            # Verify that JSON serialization was called
            call_args = mock_client.set.call_args
            assert "complex_key" in call_args[0]
            # The value should be JSON serialized
            serialized_value = call_args[0][1]
            assert isinstance(serialized_value, str)
            assert "Test Paper" in serialized_value

class TestCacheManager:
    """Test high-level cache manager"""
    
    @pytest.mark.asyncio
    async def test_cache_manager_initialization_redis(self):
        """Test cache manager initialization with Redis"""
        with patch('app.cache.redis_cache.REDIS_AVAILABLE', True), \
             patch('app.cache.redis_cache.RedisCache') as mock_redis_class:
            
            mock_redis = AsyncMock()
            mock_redis.connect = AsyncMock(return_value=True)
            mock_redis_class.return_value = mock_redis
            
            manager = CacheManager()
            await manager.initialize()
            
            assert manager.cache == mock_redis
            mock_redis.connect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cache_manager_fallback_simple_cache(self):
        """Test cache manager fallback to simple cache"""
        with patch('app.cache.redis_cache.REDIS_AVAILABLE', False):
            manager = CacheManager()
            await manager.initialize()
            
            # Should fallback to SimpleCache
            assert isinstance(manager.cache, SimpleCache)
    
    @pytest.mark.asyncio
    async def test_cache_search_results(self):
        """Test caching search results"""
        mock_cache = AsyncMock()
        mock_cache.set = AsyncMock(return_value=True)
        
        manager = CacheManager()
        manager.cache = mock_cache
        
        query = "test query"
        results = {"papers": [], "total": 0}
        
        success = await manager.cache_search_results(query, results)
        assert success is True
        mock_cache.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_search_results(self):
        """Test retrieving cached search results"""
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value={"papers": [], "total": 0})
        
        manager = CacheManager()
        manager.cache = mock_cache
        
        query = "test query"
        results = await manager.get_search_results(query)
        
        assert results == {"papers": [], "total": 0}
        mock_cache.get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cache_paper_details(self):
        """Test caching paper details"""
        mock_cache = AsyncMock()
        mock_cache.set = AsyncMock(return_value=True)
        
        manager = CacheManager()
        manager.cache = mock_cache
        
        paper_id = "10.1000/example"
        paper_data = {"title": "Test Paper", "year": 2023}
        
        success = await manager.cache_paper_details(paper_id, paper_data)
        assert success is True
        mock_cache.set.assert_called_once()

class TestCacheIntegration:
    """Integration tests for cache system"""
    
    @pytest.mark.asyncio
    async def test_cache_manager_complete_flow(self):
        """Test complete cache manager flow with simple cache"""
        manager = CacheManager()
        # Force simple cache for testing
        manager.cache = SimpleCache()
        await manager.cache.connect()
        
        # Test search results caching
        query = "machine learning"
        original_results = {
            "papers": [{"title": "ML Paper", "year": 2023}],
            "total": 1
        }
        
        # Cache results
        success = await manager.cache_search_results(query, original_results)
        assert success is True
        
        # Retrieve results
        cached_results = await manager.get_search_results(query)
        assert cached_results == original_results
        
        # Test paper details caching
        paper_id = "test_paper_id"
        paper_data = {"title": "Test Paper", "authors": ["Author"]}
        
        success = await manager.cache_paper_details(paper_id, paper_data)
        assert success is True
        
        cached_paper = await manager.get_paper_details(paper_id)
        assert cached_paper == paper_data
    
    @pytest.mark.asyncio
    async def test_cache_key_consistency(self):
        """Test that cache keys are consistent across operations"""
        manager = CacheManager()
        manager.cache = SimpleCache()
        await manager.cache.connect()
        
        query = "consistent test"
        params = {"year_start": 2020, "limit": 10}
        
        # Cache with parameters
        await manager.cache_search_results(query, {"test": "data"}, **params)
        
        # Retrieve with same parameters
        result = await manager.get_search_results(query, **params)
        assert result is not None
        
        # Retrieve with different parameters should return None
        result = await manager.get_search_results(query, year_start=2021, limit=10)
        assert result is None

# Mock fixtures for testing
@pytest.fixture
def mock_redis_client():
    """Fixture providing a mock Redis client"""
    client = AsyncMock()
    client.ping = AsyncMock(return_value=True)
    client.set = AsyncMock(return_value=True)
    client.get = AsyncMock(return_value=None)
    client.delete = AsyncMock(return_value=1)
    client.close = AsyncMock()
    return client

@pytest.fixture
def simple_cache():
    """Fixture providing a simple cache instance"""
    return SimpleCache()

if __name__ == "__main__":
    pytest.main([__file__])
