"""
Redis service for caching and data storage.
"""

import json
import logging
from typing import Any, Optional, TypeVar, Union

import redis.asyncio as redis
from redis.asyncio import Redis

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)

T = TypeVar("T")


class RedisService:
    """
    Service for Redis operations including caching and data storage.

    Provides async methods for common Redis operations with automatic
    serialization/deserialization of Python objects.
    """

    def __init__(self, settings: Optional[Settings] = None):
        """
        Initialize Redis service.

        Args:
            settings: Application settings. Uses default if not provided.
        """
        self._settings = settings or get_settings()
        self._client: Optional[Redis] = None
        self._prefix = self._settings.storage_prefix

    async def connect(self) -> None:
        """
        Establish connection to Redis server.

        Raises:
            ConnectionError: If connection to Redis fails.
        """
        # TODO: Implement connection logic
        # - Create Redis connection pool
        # - Handle SSL if configured
        # - Set up connection retry logic
        # - Test connection with ping
        try:
            self._client = redis.from_url(
                self._settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            await self._client.ping()
            logger.info("Connected to Redis successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise ConnectionError(f"Redis connection failed: {e}")

    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            self._client = None
            logger.info("Disconnected from Redis")

    async def get(self, key: str) -> Optional[Any]:
        """
        Get a value from Redis.

        Args:
            key: The cache key.

        Returns:
            The cached value or None if not found.
        """
        # TODO: Implement get logic
        # - Add prefix to key
        # - Deserialize JSON if applicable
        # - Handle connection errors gracefully
        if not self._client:
            raise ConnectionError("Redis client not connected")

        full_key = f"{self._prefix}{key}"
        try:
            value = await self._client.get(full_key)
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return None
        except Exception as e:
            logger.error(f"Redis get error for key {key}: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Set a value in Redis with optional TTL.

        Args:
            key: The cache key.
            value: The value to cache.
            ttl: Time-to-live in seconds. Uses default if not provided.

        Returns:
            True if successful, False otherwise.
        """
        # TODO: Implement set logic
        # - Serialize value to JSON
        # - Apply TTL (use default from settings if not provided)
        # - Handle connection errors gracefully
        if not self._client:
            raise ConnectionError("Redis client not connected")

        full_key = f"{self._prefix}{key}"
        ttl = ttl or self._settings.redis_cache_ttl

        try:
            serialized = json.dumps(value) if not isinstance(value, str) else value
            await self._client.setex(full_key, ttl, serialized)
            return True
        except Exception as e:
            logger.error(f"Redis set error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete a key from Redis.

        Args:
            key: The cache key to delete.

        Returns:
            True if key was deleted, False otherwise.
        """
        # TODO: Implement delete logic
        if not self._client:
            raise ConnectionError("Redis client not connected")

        full_key = f"{self._prefix}{key}"
        try:
            result = await self._client.delete(full_key)
            return result > 0
        except Exception as e:
            logger.error(f"Redis delete error for key {key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in Redis.

        Args:
            key: The cache key to check.

        Returns:
            True if key exists, False otherwise.
        """
        # TODO: Implement exists logic
        if not self._client:
            raise ConnectionError("Redis client not connected")

        full_key = f"{self._prefix}{key}"
        try:
            return await self._client.exists(full_key) > 0
        except Exception as e:
            logger.error(f"Redis exists error for key {key}: {e}")
            return False

    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        """
        Get multiple values from Redis.

        Args:
            keys: List of cache keys.

        Returns:
            Dictionary of key-value pairs.
        """
        # TODO: Implement bulk get logic
        # - Use mget for efficiency
        # - Deserialize values
        if not self._client:
            raise ConnectionError("Redis client not connected")

        full_keys = [f"{self._prefix}{key}" for key in keys]
        try:
            values = await self._client.mget(full_keys)
            result = {}
            for key, value in zip(keys, values):
                if value:
                    try:
                        result[key] = json.loads(value)
                    except json.JSONDecodeError:
                        result[key] = value
            return result
        except Exception as e:
            logger.error(f"Redis mget error: {e}")
            return {}

    async def increment(self, key: str, amount: int = 1) -> int:
        """
        Increment a counter in Redis.

        Args:
            key: The counter key.
            amount: Amount to increment by.

        Returns:
            The new counter value.
        """
        # TODO: Implement increment logic
        if not self._client:
            raise ConnectionError("Redis client not connected")

        full_key = f"{self._prefix}{key}"
        try:
            return await self._client.incrby(full_key, amount)
        except Exception as e:
            logger.error(f"Redis increment error for key {key}: {e}")
            raise

    async def set_hash(self, key: str, mapping: dict[str, Any]) -> bool:
        """
        Set a hash in Redis.

        Args:
            key: The hash key.
            mapping: Dictionary of field-value pairs.

        Returns:
            True if successful.
        """
        # TODO: Implement hash set logic
        if not self._client:
            raise ConnectionError("Redis client not connected")

        full_key = f"{self._prefix}{key}"
        try:
            serialized = {k: json.dumps(v) if not isinstance(v, str) else v for k, v in mapping.items()}
            await self._client.hset(full_key, mapping=serialized)
            return True
        except Exception as e:
            logger.error(f"Redis hset error for key {key}: {e}")
            return False

    async def get_hash(self, key: str) -> Optional[dict[str, Any]]:
        """
        Get a hash from Redis.

        Args:
            key: The hash key.

        Returns:
            Dictionary of field-value pairs or None.
        """
        # TODO: Implement hash get logic
        if not self._client:
            raise ConnectionError("Redis client not connected")

        full_key = f"{self._prefix}{key}"
        try:
            result = await self._client.hgetall(full_key)
            if result:
                return {k: json.loads(v) if v.startswith(('{', '[', '"')) else v for k, v in result.items()}
            return None
        except Exception as e:
            logger.error(f"Redis hgetall error for key {key}: {e}")
            return None

    async def health_check(self) -> bool:
        """
        Check Redis connection health.

        Returns:
            True if Redis is healthy, False otherwise.
        """
        try:
            if self._client:
                await self._client.ping()
                return True
            return False
        except Exception:
            return False


# Global Redis service instance
_redis_service: Optional[RedisService] = None


async def get_redis_service() -> RedisService:
    """
    Get or create the global Redis service instance.

    Returns:
        RedisService instance.
    """
    global _redis_service
    if _redis_service is None:
        _redis_service = RedisService()
        await _redis_service.connect()
    return _redis_service


async def close_redis_service() -> None:
    """Close the global Redis service connection."""
    global _redis_service
    if _redis_service:
        await _redis_service.disconnect()
        _redis_service = None
