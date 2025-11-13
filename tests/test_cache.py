"""Tests for cache utilities."""

import time

import pytest

from fastapi_mongo_admin.cache import (
    cache_result,
    clear_cache,
    get_cache_stats,
)


@pytest.mark.asyncio
async def test_cache_result_basic():
    """Test basic caching functionality."""
    call_count = 0

    @cache_result(ttl=1.0)
    async def test_function(x):
        nonlocal call_count
        call_count += 1
        return x * 2

    # First call should execute function
    result1 = await test_function(5)
    assert result1 == 10
    assert call_count == 1

    # Second call should use cache
    result2 = await test_function(5)
    assert result2 == 10
    assert call_count == 1  # Should not increment


@pytest.mark.asyncio
async def test_cache_result_different_args():
    """Test caching with different arguments."""
    call_count = 0

    @cache_result(ttl=1.0)
    async def test_function_diff_args(x):
        nonlocal call_count
        call_count += 1
        return x * 2

    # Clear cache before test
    clear_cache()

    result1 = await test_function_diff_args(5)
    result2 = await test_function_diff_args(10)

    assert result1 == 10
    assert result2 == 20
    assert call_count == 2  # Different args should call function


@pytest.mark.asyncio
async def test_cache_result_ttl_expiry():
    """Test cache TTL expiration."""
    call_count = 0

    @cache_result(ttl=0.1)  # Very short TTL
    async def test_function_ttl(x):
        nonlocal call_count
        call_count += 1
        return x * 2

    # Clear cache before test
    clear_cache()

    # First call
    result1 = await test_function_ttl(5)
    assert call_count == 1

    # Second call (within TTL) - should use cache
    result2 = await test_function_ttl(5)
    assert call_count == 1

    # Wait for TTL to expire
    time.sleep(0.2)

    # Third call (after TTL) - should call function again
    result3 = await test_function_ttl(5)
    assert call_count == 2


@pytest.mark.asyncio
async def test_cache_result_with_kwargs():
    """Test caching with keyword arguments."""
    call_count = 0

    @cache_result(ttl=1.0)
    async def test_function_kwargs(x, y=10):
        nonlocal call_count
        call_count += 1
        return x + y

    # Clear cache before test
    clear_cache()

    result1 = await test_function_kwargs(5, y=10)
    result2 = await test_function_kwargs(5, y=10)  # Same kwargs
    result3 = await test_function_kwargs(5, y=20)  # Different kwargs

    assert result1 == 15
    assert result2 == 15
    assert result3 == 25
    assert call_count == 2  # Should cache same kwargs


@pytest.mark.asyncio
async def test_clear_cache():
    """Test clearing cache."""
    call_count = 0

    @cache_result(ttl=10.0)
    async def test_function_clear(x):
        nonlocal call_count
        call_count += 1
        return x * 2

    # Clear cache before test
    clear_cache()

    # Call and cache
    await test_function_clear(5)
    assert call_count == 1

    # Call again - should use cache
    await test_function_clear(5)
    assert call_count == 1

    # Clear cache
    clear_cache()

    # Call again - should execute function
    await test_function_clear(5)
    assert call_count == 2


@pytest.mark.asyncio
async def test_get_cache_stats():
    """Test getting cache statistics."""
    @cache_result(ttl=1.0)
    async def test_function_stats(x):
        return x * 2

    # Clear cache before test
    clear_cache()

    # Make some calls
    await test_function_stats(5)
    await test_function_stats(5)  # Cached
    await test_function_stats(10)

    stats = get_cache_stats()

    assert "total_entries" in stats
    assert "valid_entries" in stats
    assert "expired_entries" in stats
    assert stats["total_entries"] >= 2  # At least 2 unique calls
    assert stats["valid_entries"] >= 2  # At least 2 valid entries

