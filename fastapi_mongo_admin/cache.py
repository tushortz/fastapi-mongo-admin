"""Caching utilities for admin operations."""

import hashlib
import json
import time
from functools import wraps
from typing import Any, Callable, TypeVar

from typing_extensions import ParamSpec

P = ParamSpec("P")
T = TypeVar("T")

# Simple in-memory cache (can be replaced with Redis in production)
_cache: dict[str, tuple[Any, float]] = {}
_cache_ttl: dict[str, float] = {}


def get_cache_key(*args: Any, **kwargs: Any) -> str:
    """Generate a cache key from function arguments.

    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments

    Returns:
        Cache key string
    """
    key_data = {"args": args, "kwargs": kwargs}
    key_str = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.md5(key_str.encode()).hexdigest()


def cache_result(ttl: float = 300.0):
    """Decorator to cache function results.

    Args:
        ttl: Time to live in seconds (default: 5 minutes)

    Returns:
        Decorated function with caching
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            cache_key = f"{func.__name__}:{get_cache_key(*args, **kwargs)}"
            current_time = time.time()

            # Check if cached result exists and is still valid
            if cache_key in _cache:
                result, cached_time = _cache[cache_key]
                if current_time - cached_time < ttl:
                    return result

            # Call function and cache result
            result = await func(*args, **kwargs)
            _cache[cache_key] = (result, current_time)
            _cache_ttl[cache_key] = ttl

            return result

        return wrapper

    return decorator


def clear_cache(pattern: str | None = None) -> int:
    """Clear cache entries.

    Args:
        pattern: Optional pattern to match cache keys (if None, clears all)

    Returns:
        Number of cache entries cleared
    """
    if pattern is None:
        count = len(_cache)
        _cache.clear()
        _cache_ttl.clear()
        return count

    # Clear matching entries
    keys_to_remove = [key for key in _cache.keys() if pattern in key]
    for key in keys_to_remove:
        _cache.pop(key, None)
        _cache_ttl.pop(key, None)

    return len(keys_to_remove)


def get_cache_stats() -> dict[str, Any]:
    """Get cache statistics.

    Returns:
        Dictionary with cache statistics
    """
    current_time = time.time()
    valid_entries = sum(
        1
        for key, (_, cached_time) in _cache.items()
        if current_time - cached_time < _cache_ttl.get(key, 0)
    )

    return {
        "total_entries": len(_cache),
        "valid_entries": valid_entries,
        "expired_entries": len(_cache) - valid_entries,
    }
