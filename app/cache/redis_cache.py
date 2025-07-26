# app/cache/redis_cache.py
"""
Redis-based caching system for OpenScholar
Addresses performance issues identified in audit
"""

import json
import hashlib
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import os

logger = logging.getLogger(__name__)

try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    logger.warning("Redis not available - caching will be disabled")
    REDIS_AVAILABLE = False

class CacheKeyBuilder:
    """Build consistent cache keys for different data types"""
    
    @staticmethod
    def search_results_key(query: str, **params) -> str:
        """Generate cache key for search results"""
        # Create a deterministic hash from search parameters
        search_data = {
            'query': query.lower().strip(),
            **{k: v for k, v in params.items() if v is not None}
        }
        
        # Create hash
        search_string = json.dumps(search_data, sort_keys=True)
        search_hash = hashlib.md5(search_string.encode()).hexdigest()
        
        return f"search_results:{search_hash}"
    
    @staticmethod
    def paper_details_key(paper_id: str) -> str:
        """Generate cache key for paper details"""
        return f"paper_details:{paper_id}"
    
    @staticmethod
    def api_response_key(api_name: str, query_hash: str) -> str:
        """Generate cache key for individual API responses"""
        return f"api_response:{api_name}:{query_hash}"

class SimpleCache:
    """Simple in-memory cache fallback when Redis is not available"""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = 3600  # 1 hour
        self.search_results_ttl = 300  # 5 minutes - search results change frequently
        self.paper_details_ttl = 86400  # 24 hours - paper metadata is more stable
    
    async def connect(self):
        """No-op for simple cache"""
        logger.info("Using simple in-memory cache (Redis not available)")
        return True
    
    async def disconnect(self):
        """No-op for simple cache"""
        pass
    
    async def is_connected(self) -> bool:
        """Simple cache is always 'connected'"""
        return True
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set a value in memory cache with TTL"""
        try:
            expire_time = datetime.now() + timedelta(seconds=ttl or self.default_ttl)
            
            self._cache[key] = {
                'value': value,
                'expires': expire_time
            }
            
            logger.debug(f"Cached in memory: {key}")
            return True
        except Exception as e:
            logger.error(f"Failed to cache {key}: {e}")
            return False
    
    async def get(self, key: str) -> Optional[Any]:
        """Get a value from memory cache"""
        try:
            if key not in self._cache:
                return None
            
            item = self._cache[key]
            
            # Check if expired
            if datetime.now() > item['expires']:
                del self._cache[key]
                return None
            
            logger.debug(f"Cache hit: {key}")
            return item['value']
        except Exception as e:
            logger.error(f"Failed to get cached {key}: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        """Delete a key from memory cache"""
        try:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
        except:
            return False

class RedisCache:
    """Redis cache implementation"""
    
    def __init__(self):
        self.redis_client: Optional[aioredis.Redis] = None
        self.default_ttl = 3600  # 1 hour
        self.search_results_ttl = 300  # 5 minutes - search results change frequently
        self.paper_details_ttl = 86400  # 24 hours - paper metadata is more stable
    
    async def connect(self):
        """Initialize Redis connection"""
        if not REDIS_AVAILABLE:
            return False
        
        try:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            self.redis_client = aioredis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            
            # Test connection
            await self.redis_client.ping()
            logger.info("Successfully connected to Redis")
            return True
            
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}")
            self.redis_client = None
            return False
    
    async def disconnect(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None
    
    async def is_connected(self) -> bool:
        """Check if Redis is connected and responsive"""
        if not self.redis_client:
            return False
        
        try:
            await self.redis_client.ping()
            return True
        except:
            return False
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set a value in Redis cache with TTL"""
        if not await self.is_connected():
            return False
        
        try:
            # Serialize value
            if isinstance(value, (dict, list)):
                serialized_value = json.dumps(value, default=str)
            else:
                serialized_value = str(value)
            
            # Set TTL
            expire_time = ttl or self.default_ttl
            
            # Set value
            result = await self.redis_client.set(key, serialized_value, ex=expire_time)
            
            if result:
                logger.debug(f"Cached in Redis: {key} (TTL: {expire_time}s)")
            
            return bool(result)
            
        except Exception as e:
            logger.error(f"Failed to set Redis cache key {key}: {e}")
            return False
    
    async def get(self, key: str) -> Optional[Any]:
        """Get a value from Redis cache"""
        if not await self.is_connected():
            return None
        
        try:
            value = await self.redis_client.get(key)
            
            if value is None:
                return None
            
            logger.debug(f"Redis cache hit: {key}")
            
            # Try to deserialize as JSON first
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                # Return as string if not JSON
                return value
            
        except Exception as e:
            logger.error(f"Failed to get Redis cache key {key}: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        """Delete a key from Redis cache"""
        if not await self.is_connected():
            return False
        
        try:
            result = await self.redis_client.delete(key)
            return bool(result)
        except Exception as e:
            logger.error(f"Failed to delete Redis cache key {key}: {e}")
            return False

class CacheManager:
    """High-level cache manager that handles both Redis and fallback"""
    
    def __init__(self):
        self.cache = None
        self.key_builder = CacheKeyBuilder()
    
    async def initialize(self):
        """Initialize cache (Redis first, fallback to simple cache)"""
        if REDIS_AVAILABLE:
            redis_cache = RedisCache()
            try:
                # Add timeout to Redis connection attempt
                import asyncio
                connected = await asyncio.wait_for(redis_cache.connect(), timeout=2.0)
                if connected:
                    self.cache = redis_cache
                    logger.info("Using Redis cache")
                    return
            except asyncio.TimeoutError:
                logger.warning("Redis connection timed out, falling back to simple cache")
            except Exception as e:
                logger.warning(f"Redis initialization failed: {e}, falling back to simple cache")
        
        # Fallback to simple cache
        self.cache = SimpleCache()
        await self.cache.connect()
    
    async def cleanup(self):
        """Cleanup cache connections"""
        if self.cache:
            await self.cache.disconnect()
    
    async def cache_search_results(self, query: str, results: Any, **params) -> bool:
        """Cache search results"""
        if not self.cache:
            return False
        
        cache_key = self.key_builder.search_results_key(query, **params)
        
        # Use shorter TTL for search results (5 minutes)
        ttl = getattr(self.cache, 'search_results_ttl', 300)
        
        return await self.cache.set(cache_key, results, ttl=ttl)
    
    async def get_search_results(self, query: str, **params) -> Optional[Any]:
        """Get cached search results"""
        if not self.cache:
            return None
        
        cache_key = self.key_builder.search_results_key(query, **params)
        return await self.cache.get(cache_key)
    
    async def cache_paper_details(self, paper_id: str, paper_data: Any) -> bool:
        """Cache detailed paper information"""
        if not self.cache:
            return False
        
        cache_key = self.key_builder.paper_details_key(paper_id)
        
        # Use longer TTL for paper details (24 hours)
        ttl = getattr(self.cache, 'paper_details_ttl', 86400)
        
        return await self.cache.set(cache_key, paper_data, ttl=ttl)
    
    async def get_paper_details(self, paper_id: str) -> Optional[Any]:
        """Get cached paper details"""
        if not self.cache:
            return None
        
        cache_key = self.key_builder.paper_details_key(paper_id)
        return await self.cache.get(cache_key)

# Global cache instance
_cache_manager: Optional[CacheManager] = None

async def initialize_cache():
    """Initialize the global cache manager"""
    global _cache_manager
    _cache_manager = CacheManager()
    await _cache_manager.initialize()

async def cleanup_cache():
    """Cleanup the global cache manager"""
    global _cache_manager
    if _cache_manager:
        await _cache_manager.cleanup()
        _cache_manager = None

def get_cache_manager() -> Optional[CacheManager]:
    """Get the global cache manager instance"""
    return _cache_manager
