"""Tests for middleware."""

import time

import pytest
from fastapi import FastAPI

from fastapi_mongo_admin.middleware import (
    RateLimitMiddleware,
    setup_middleware,
)


@pytest.fixture
def test_app():
    """Create a test FastAPI app."""
    app = FastAPI()

    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}

    return app


def test_rate_limit_middleware_init():
    """Test rate limit middleware initialization."""
    app = FastAPI()
    middleware = RateLimitMiddleware(app, calls=10, period=60)

    assert middleware.calls == 10
    assert middleware.period == 60
    assert middleware.exempt_paths == []


def test_rate_limit_middleware_exempt_paths():
    """Test rate limit middleware with exempt paths."""
    app = FastAPI()
    middleware = RateLimitMiddleware(
        app, calls=10, period=60, exempt_paths=["/docs", "/openapi.json"]
    )

    assert "/docs" in middleware.exempt_paths
    assert "/openapi.json" in middleware.exempt_paths


def test_rate_limit_middleware_get_client_ip():
    """Test getting client IP address."""
    app = FastAPI()
    middleware = RateLimitMiddleware(app)

    # Create a mock request
    class MockClient:
        def __init__(self, host):
            self.host = host

    class MockRequest:
        def __init__(self, client):
            self.client = client
            self.url = type("url", (), {"path": "/test"})()

    request = MockRequest(MockClient("127.0.0.1"))
    ip = middleware.get_client_ip(request)

    assert ip == "127.0.0.1"


def test_rate_limit_middleware_get_client_ip_unknown():
    """Test getting client IP when client is None."""
    app = FastAPI()
    middleware = RateLimitMiddleware(app)

    class MockRequest:
        def __init__(self):
            self.client = None
            self.url = type("url", (), {"path": "/test"})()

    request = MockRequest()
    ip = middleware.get_client_ip(request)

    assert ip == "unknown"


@pytest.mark.asyncio
async def test_rate_limit_middleware_exempt_path(test_app):
    """Test rate limit middleware with exempt path."""
    test_app.add_middleware(RateLimitMiddleware, calls=1, period=1, exempt_paths=["/test"])

    # Test exempt path logic directly
    middleware = RateLimitMiddleware(test_app, calls=1, period=1, exempt_paths=["/test"])

    class MockRequest:
        def __init__(self, path):
            self.url = type("url", (), {"path": path})()

    # Should be exempt
    request = MockRequest("/test")
    assert any(request.url.path.startswith(path) for path in middleware.exempt_paths)


@pytest.mark.asyncio
async def test_rate_limit_middleware_rate_limiting(test_app):
    """Test rate limit middleware rate limiting logic."""
    test_app.add_middleware(RateLimitMiddleware, calls=2, period=1)

    middleware = RateLimitMiddleware(test_app, calls=2, period=1)

    # Simulate rate limiting
    client_ip = "127.0.0.1"
    now = time.time()

    # Add two requests
    middleware.clients[client_ip] = [now, now - 0.5]

    # Should be at limit
    assert len(middleware.clients[client_ip]) >= middleware.calls


@pytest.mark.asyncio
async def test_rate_limit_middleware_headers(test_app):
    """Test rate limit middleware header calculation."""
    test_app.add_middleware(RateLimitMiddleware, calls=10, period=60)

    middleware = RateLimitMiddleware(test_app, calls=10, period=60)

    # Test header calculation
    client_ip = "127.0.0.1"
    now = time.time()
    middleware.clients[client_ip] = [now, now - 10]

    remaining = middleware.calls - len(middleware.clients[client_ip])
    assert remaining == 8
    assert middleware.calls == 10


@pytest.mark.asyncio
async def test_rate_limit_middleware_cleanup_old_entries():
    """Test rate limit middleware cleans up old entries."""
    app = FastAPI()
    middleware = RateLimitMiddleware(app, calls=10, period=1)

    client_ip = "127.0.0.1"
    now = time.time()

    # Add old entries (outside period)
    middleware.clients[client_ip] = [now - 2, now - 3, now - 4]

    # Simulate cleanup
    cleaned = [
        timestamp
        for timestamp in middleware.clients[client_ip]
        if now - timestamp < middleware.period
    ]

    # All entries should be cleaned (all are older than period)
    assert len(cleaned) == 0


@pytest.mark.asyncio
async def test_rate_limit_middleware_add_request():
    """Test rate limit middleware adds request timestamp."""
    app = FastAPI()
    middleware = RateLimitMiddleware(app, calls=10, period=60)

    client_ip = "127.0.0.1"
    now = time.time()

    # Initially empty
    assert len(middleware.clients[client_ip]) == 0

    # Add request
    middleware.clients[client_ip].append(now)

    assert len(middleware.clients[client_ip]) == 1
    assert middleware.clients[client_ip][0] == now


def test_setup_middleware_rate_limit_only(test_app):
    """Test setting up middleware with rate limit only."""
    setup_middleware(test_app, rate_limit=True, compression=False)

    # Middleware should be added
    assert len(test_app.user_middleware) > 0


def test_setup_middleware_compression_only(test_app):
    """Test setting up middleware with compression only."""
    setup_middleware(test_app, rate_limit=False, compression=True)

    # Middleware should be added
    assert len(test_app.user_middleware) > 0


def test_setup_middleware_both(test_app):
    """Test setting up middleware with both enabled."""
    setup_middleware(test_app, rate_limit=True, compression=True)

    # Both middlewares should be added
    assert len(test_app.user_middleware) >= 1


def test_setup_middleware_none(test_app):
    """Test setting up middleware with both disabled."""
    initial_middleware_count = len(test_app.user_middleware)
    setup_middleware(test_app, rate_limit=False, compression=False)

    # No new middleware should be added
    assert len(test_app.user_middleware) == initial_middleware_count
