"""Middleware for admin operations."""

import time
from collections import defaultdict
from typing import Callable

from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware.

    Limits the number of requests per IP address per time window.
    """

    def __init__(
        self,
        app,
        calls: int = 100,
        period: int = 60,
        exempt_paths: list[str] | None = None,
    ):
        """Initialize rate limit middleware.

        Args:
            app: FastAPI application
            calls: Number of allowed calls per period
            period: Time period in seconds
            exempt_paths: List of paths to exempt from rate limiting
        """
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.exempt_paths = exempt_paths or []
        self.clients: dict[str, list[float]] = defaultdict(list)

    def get_client_ip(self, request: Request) -> str:
        """Get client IP address.

        Args:
            request: FastAPI request

        Returns:
            Client IP address
        """
        if request.client:
            return request.client.host
        return "unknown"

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting.

        Args:
            request: FastAPI request
            call_next: Next middleware/route handler

        Returns:
            Response with rate limit headers
        """
        # Check if path is exempt
        if any(request.url.path.startswith(path) for path in self.exempt_paths):
            return await call_next(request)

        client_ip = self.get_client_ip(request)
        now = time.time()

        # Clean old entries
        self.clients[client_ip] = [
            timestamp for timestamp in self.clients[client_ip] if now - timestamp < self.period
        ]

        # Check rate limit
        if len(self.clients[client_ip]) >= self.calls:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": f"Rate limit exceeded: {self.calls} requests per {self.period} seconds",
                        "details": {
                            "limit": self.calls,
                            "period": self.period,
                            "retry_after": self.period,
                        },
                    }
                },
                headers={
                    "Retry-After": str(self.period),
                    "X-RateLimit-Limit": str(self.calls),
                    "X-RateLimit-Remaining": "0",
                },
            )

        # Add current request
        self.clients[client_ip].append(now)

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        remaining = self.calls - len(self.clients[client_ip])
        response.headers["X-RateLimit-Limit"] = str(self.calls)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(now + self.period))

        return response


def setup_middleware(app, rate_limit: bool = True, compression: bool = True):
    """Setup middleware for FastAPI app.

    Args:
        app: FastAPI application
        rate_limit: Whether to enable rate limiting
        compression: Whether to enable compression
    """
    if compression:
        from fastapi.middleware.gzip import GZipMiddleware

        app.add_middleware(GZipMiddleware, minimum_size=1000)

    if rate_limit:
        app.add_middleware(
            RateLimitMiddleware,
            calls=100,  # 100 requests
            period=60,  # per 60 seconds
            exempt_paths=["/docs", "/openapi.json", "/redoc"],  # Exempt API docs
        )
