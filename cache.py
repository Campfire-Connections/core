"""
Cache helpers for commonly reused aggregates.
"""

from django.core.cache import cache
from typing import Callable, Any

CACHE_TIMEOUT = 60 * 5


def cache_key(prefix: str, identifier: Any) -> str:
    """
    Build a consistent cache key.
    """
    return f"{prefix}:{identifier}"


def cached(key: str, ttl: int, producer: Callable[[], Any]) -> Any:
    """
    Return cached value for key or compute via producer and store.
    """
    value = cache.get(key)
    if value is not None:
        return value
    value = producer()
    cache.set(key, value, ttl)
    return value
