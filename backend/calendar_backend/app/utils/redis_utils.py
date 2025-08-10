"""
Redis Utility Functions
"""

import redis.asyncio as redis
import logging
from typing import Optional
from config.settings import settings

logger = logging.getLogger(__name__)

class RedisClient:
    def __init__(self, client):
        self.client = client
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from Redis by key"""
        try:
            return await self.client.get(key)
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None
    
    async def set(self, key: str, value: str, ex: int = None) -> bool:
        """Set value in Redis with optional expiration time"""
        try:
            await self.client.set(key, value, ex=ex)
            return True
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from Redis"""
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete keys matching pattern"""
        try:
            count = 0
            async for key in self.client.scan_iter(pattern):
                await self.client.delete(key)
                count += 1
            return count
        except Exception as e:
            logger.error(f"Redis delete pattern error: {e}")
            return 0
    
    async def ping(self) -> bool:
        """Check Redis connection"""
        try:
            await self.client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis ping error: {e}")
            return False
    
    async def close(self):
        """Close Redis connection"""
        try:
            await self.client.aclose()
        except Exception as e:
            logger.error(f"Redis close error: {e}")

async def get_redis_client() -> RedisClient:
    """Create and return Redis client"""
    try:
        client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            decode_responses=True
        )
        # Test connection
        await client.ping()
        logger.info("Successfully connected to Redis")
        return RedisClient(client)
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        raise