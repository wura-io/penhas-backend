"""
Redis client for caching and key-value storage
Port from Perl Penhas::KeyValueStorage
"""
import os
import redis
from typing import Optional, Callable, Any
import json


class RedisClient:
    """
    Redis client singleton for caching and KV operations
    Matches Perl's Penhas::KeyValueStorage behavior
    """
    _instance: Optional['RedisClient'] = None
    
    def __init__(self):
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        self.redis = redis.from_url(redis_url, decode_responses=True)
        self.namespace = os.getenv('REDIS_NS', 'penhas:')
    
    @classmethod
    def instance(cls) -> 'RedisClient':
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def get_namespaced_key(self, key: str) -> str:
        """Add namespace prefix to key"""
        return f"{self.namespace}{key}"
    
    def get(self, key: str) -> Optional[str]:
        """Get value from Redis with namespace"""
        return self.redis.get(self.get_namespaced_key(key))
    
    def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """Set value in Redis with namespace"""
        return self.redis.set(self.get_namespaced_key(key), value, ex=ex)
    
    def setex(self, key: str, seconds: int, value: str) -> bool:
        """Set value with expiration"""
        return self.redis.setex(self.get_namespaced_key(key), seconds, value)
    
    def delete(self, key: str) -> int:
        """Delete key from Redis"""
        return self.redis.delete(self.get_namespaced_key(key))
    
    def exists(self, key: str) -> bool:
        """Check if key exists"""
        return bool(self.redis.exists(self.get_namespaced_key(key)))
    
    def redis_get_cached_or_execute(
        self, 
        cache_key: str, 
        ttl: int, 
        callback: Callable[[], Any]
    ) -> Any:
        """
        Get cached value or execute callback and cache result
        Matches Perl's redis_get_cached_or_execute
        """
        # Try to get from cache
        cached = self.get(cache_key)
        if cached is not None:
            # Return cached value (empty string is valid)
            return cached
        
        # Execute callback
        result = callback()
        
        # Cache the result
        if result is not None:
            self.setex(cache_key, ttl, str(result))
        
        return result
    
    def incr(self, key: str) -> int:
        """Increment counter"""
        return self.redis.incr(self.get_namespaced_key(key))
    
    def expire(self, key: str, seconds: int) -> bool:
        """Set expiration on key"""
        return bool(self.redis.expire(self.get_namespaced_key(key), seconds))
    
    def lock_and_wait(self, lock_key: str, timeout: int = 10) -> bool:
        """
        Acquire a lock (simplified version)
        Matches Perl's lock_and_wait behavior
        """
        lock_key = f"lock:{lock_key}"
        return bool(self.set(lock_key, "1", ex=timeout))
    
    def unlock(self, lock_key: str) -> None:
        """Release a lock"""
        lock_key = f"lock:{lock_key}"
        self.delete(lock_key)


# Global instance getter
def get_redis() -> RedisClient:
    """Get Redis client instance"""
    return RedisClient.instance()

