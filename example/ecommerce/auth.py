"""Demo authentication for the ecommerce example."""

from __future__ import annotations

from typing import Any

from fastapi import Cookie, Header, HTTPException, status

# Demo users — replace with real JWT/session validation in production.
DEMO_USERS: dict[str, dict[str, Any]] = {
    "admin-token": {"id": "u1", "email": "admin@shop.test", "role": "admin", "is_staff": True},
    "manager-token": {"id": "u2", "email": "manager@shop.test", "role": "manager", "is_staff": True},
    "viewer-token": {"id": "u3", "email": "viewer@shop.test", "role": "viewer", "is_staff": True},
}

TOKEN_COOKIE = "admin_token"


def resolve_user_from_token(token: str | None) -> dict[str, Any]:
    """Look up demo user by token string."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Visit /demo-login or send Authorization: Bearer admin-token",
        )
    user = DEMO_USERS.get(token)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return user


async def get_current_user(
    authorization: str | None = Header(default=None),
    admin_token: str | None = Cookie(default=None, alias=TOKEN_COOKIE),
) -> dict[str, Any]:
    """Validate Bearer header or demo cookie token."""
    token: str | None = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ").strip()
    elif admin_token:
        token = admin_token
    return resolve_user_from_token(token)


async def require_staff(user: dict[str, Any]) -> dict[str, Any]:
    """Global permission gate — only staff may access admin."""
    if not user.get("is_staff"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Staff access required")
    return user
