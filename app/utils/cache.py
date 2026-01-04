"""
Caching utilities and decorators.
"""

import functools
import hashlib
import json
import logging
from collections.abc import Callable
from typing import Any, TypeVar

from app.services.redis_service import RedisService, get_redis_service

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


class CacheManager:
    """
    Manager for cache operations.

    Provides methods for caching, retrieval, and invalidation.
    """

    def __init__(self, redis_service: RedisService | None = None):
        """
        Initialize cache manager.

        Args:
            redis_service: Redis service for cache storage.
        """
        self._redis = redis_service
        self._prefix = "cache:"

    async def get(self, key: str) -> Any | None:
        """
        Get a cached value.

        Args:
            key: The cache key.

        Returns:
            The cached value or None.
        """
        if not self._redis:
            return None

        try:
            return await self._redis.get(f"{self._prefix}{key}")
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> bool:
        """
        Set a cached value.

        Args:
            key: The cache key.
            value: The value to cache.
            ttl: Time-to-live in seconds.

        Returns:
            True if successful.
        """
        if not self._redis:
            return False

        try:
            return await self._redis.set(f"{self._prefix}{key}", value, ttl)
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete a cached value.

        Args:
            key: The cache key.

        Returns:
            True if deleted.
        """
        if not self._redis:
            return False

        try:
            return await self._redis.delete(f"{self._prefix}{key}")
        except Exception as e:
            logger.warning(f"Cache delete error: {e}")
            return False

    async def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching a pattern.

        Args:
            pattern: The key pattern to invalidate.

        Returns:
            Number of keys invalidated.
        """
        # TODO: Implement pattern-based invalidation
        # - Scan for matching keys
        # - Delete all matches
        return 0


# Global cache instance
_cache: CacheManager | None = None


async def get_cache() -> CacheManager:
    """Get or create the global cache manager."""
    global _cache
    if _cache is None:
        redis_service = await get_redis_service()
        _cache = CacheManager(redis_service)
    return _cache


# Convenience functions
async def cache(key: str, value: Any, ttl: int | None = None) -> bool:
    """
    Cache a value.

    Args:
        key: The cache key.
        value: The value to cache.
        ttl: Time-to-live in seconds.

    Returns:
        True if successful.
    """
    cache_manager = await get_cache()
    return await cache_manager.set(key, value, ttl)


async def invalidate_cache(key: str) -> bool:
    """
    Invalidate a cached value.

    Args:
        key: The cache key.

    Returns:
        True if invalidated.
    """
    cache_manager = await get_cache()
    return await cache_manager.delete(key)


def cached(
    key_prefix: str,
    ttl: int | None = None,
    key_builder: Callable[..., str] | None = None,
) -> Callable[[F], F]:
    """
    Decorator for caching async function results.

    Args:
        key_prefix: Prefix for cache keys.
        ttl: Time-to-live in seconds.
        key_builder: Optional function to build cache key from args.

    Returns:
        Decorated function.

    Example:
        @cached("user", ttl=300)
        async def get_user(user_id: str):
            return await fetch_user(user_id)
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                # Default key builder using args hash
                key_data = {
                    "args": [str(a) for a in args],
                    "kwargs": {k: str(v) for k, v in sorted(kwargs.items())},
                }
                key_hash = hashlib.md5(json.dumps(key_data, sort_keys=True).encode()).hexdigest()[
                    :16
                ]
                cache_key = f"{key_prefix}:{func.__name__}:{key_hash}"

            # Try to get from cache
            cache_manager = await get_cache()
            cached_value = await cache_manager.get(cache_key)

            if cached_value is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_value

            # Call function and cache result
            logger.debug(f"Cache miss for {cache_key}")
            result = await func(*args, **kwargs)

            if result is not None:
                await cache_manager.set(cache_key, result, ttl)

            return result

        return wrapper  # type: ignore

    return decorator


def cache_key_from_request(
    *include_params: str,
    include_user: bool = True,
) -> Callable[..., str]:
    """
    Build a cache key from request parameters.

    Args:
        include_params: Request parameter names to include.
        include_user: Whether to include user ID.

    Returns:
        Key builder function.

    Example:
        @cached("validation", key_builder=cache_key_from_request("type", "level"))
        async def validate(request: Request, type: str, level: str):
            ...
    """

    def builder(*args, **kwargs) -> str:
        key_parts = []

        # Extract user ID if available and requested
        if include_user:
            user = kwargs.get("current_user") or kwargs.get("user")
            if user and hasattr(user, "id"):
                key_parts.append(f"user:{user.id}")

        # Include specified parameters
        for param in include_params:
            if param in kwargs:
                value = kwargs[param]
                if hasattr(value, "model_dump"):
                    # Pydantic model
                    value = json.dumps(value.model_dump(), sort_keys=True)
                key_parts.append(f"{param}:{value}")

        return ":".join(key_parts) if key_parts else "default"

    return builder
