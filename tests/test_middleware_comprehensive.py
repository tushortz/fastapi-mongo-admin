"""Comprehensive tests for middleware."""

import time
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from starlette.responses import Response

from fastapi_mongo_admin.middleware import RateLimitMiddleware, setup_middleware


@pytest.mark.asyncio
async def test_rate_limit_middleware_dispatch_exempt():
    """Test dispatch with exempt path."""
    app = FastAPI()
    middleware = RateLimitMiddleware(app, calls=2, period=60, exempt_paths=["/docs"])

    class MockRequest:
        def __init__(self, path):
            self.url = type("url", (), {"path": path})()
            self.client = type("client", (), {"host": "127.0.0.1"})()

    request = MockRequest("/docs")
    call_next = AsyncMock(return_value=Response(content="ok"))

    response = await middleware.dispatch(request, call_next)

    assert response.status_code == 200
    call_next.assert_called_once()


@pytest.mark.asyncio
async def test_rate_limit_middleware_dispatch_rate_limited():
    """Test dispatch when rate limit is exceeded."""
    app = FastAPI()
    middleware = RateLimitMiddleware(app, calls=2, period=60)

    class MockRequest:
        def __init__(self, path):
            self.url = type("url", (), {"path": path})()
            self.client = type("client", (), {"host": "127.0.0.1"})()

    request = MockRequest("/api")
    call_next = AsyncMock(return_value=Response(content="ok"))

    # Fill up the rate limit
    client_ip = middleware.get_client_ip(request)
    now = time.time()
    middleware.clients[client_ip] = [now, now - 10]

    response = await middleware.dispatch(request, call_next)

    assert response.status_code == 429
    call_next.assert_not_called()


@pytest.mark.asyncio
async def test_rate_limit_middleware_dispatch_success():
    """Test successful dispatch with headers."""
    app = FastAPI()
    middleware = RateLimitMiddleware(app, calls=10, period=60)

    class MockRequest:
        def __init__(self, path):
            self.url = type("url", (), {"path": path})()
            self.client = type("client", (), {"host": "127.0.0.1"})()

    request = MockRequest("/api")
    mock_response = Response(content="ok")
    call_next = AsyncMock(return_value=mock_response)

    response = await middleware.dispatch(request, call_next)

    assert response.status_code == 200
    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers
    assert "X-RateLimit-Reset" in response.headers
    call_next.assert_called_once()


@pytest.mark.asyncio
async def test_rate_limit_middleware_cleanup_in_dispatch():
    """Test that old entries are cleaned up during dispatch."""
    app = FastAPI()
    middleware = RateLimitMiddleware(app, calls=10, period=1)

    class MockRequest:
        def __init__(self, path):
            self.url = type("url", (), {"path": path})()
            self.client = type("client", (), {"host": "127.0.0.1"})()

    request = MockRequest("/api")
    call_next = AsyncMock(return_value=Response(content="ok"))

    # Add old entries (outside period)
    client_ip = middleware.get_client_ip(request)
    now = time.time()
    middleware.clients[client_ip] = [now - 2, now - 3]

    response = await middleware.dispatch(request, call_next)

    # Old entries should be cleaned, so we should be under limit
    assert response.status_code == 200
    assert len(middleware.clients[client_ip]) == 1  # Only the new request


@pytest.mark.asyncio
async def test_rate_limit_middleware_headers_calculation():
    """Test rate limit headers are calculated correctly."""
    app = FastAPI()
    middleware = RateLimitMiddleware(app, calls=10, period=60)

    class MockRequest:
        def __init__(self, path):
            self.url = type("url", (), {"path": path})()
            self.client = type("client", (), {"host": "127.0.0.1"})()

    request = MockRequest("/api")
    mock_response = Response(content="ok")
    call_next = AsyncMock(return_value=mock_response)

    # Pre-populate with some requests
    client_ip = middleware.get_client_ip(request)
    now = time.time()
    middleware.clients[client_ip] = [now - 5, now - 10]

    response = await middleware.dispatch(request, call_next)

    assert response.headers["X-RateLimit-Limit"] == "10"
    assert int(response.headers["X-RateLimit-Remaining"]) == 7  # 10 - 3 (2 old + 1 new)
    assert "X-RateLimit-Reset" in response.headers

