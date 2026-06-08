"""FastAPI dependencies for admin."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import Depends, HTTPException, Request, status

from fastapi_mongo_admin.admin.model import ModelAdmin
from fastapi_mongo_admin.admin.site import AdminSite
from fastapi_mongo_admin.exceptions import PermissionDeniedError


def optional_user(auth_dependency: Callable[..., Any] | None) -> Callable[..., Any]:
    """Build an optional authentication dependency.

    Args:
        auth_dependency: User-provided FastAPI dependency, or ``None`` for
            anonymous access.

    Returns:
        The auth dependency when provided, otherwise an async callable that
        returns ``None``.
    """
    if auth_dependency is None:

        async def _anonymous() -> Any:
            return None

        return _anonymous

    return auth_dependency


def require_permission(
    model_admin: ModelAdmin,
    action: str,
    auth_dependency: Callable[..., Any] | None,
) -> Callable[..., Any]:
    """Factory for per-action permission-check dependencies.

    Args:
        model_admin: ModelAdmin whose permission hooks are consulted.
        action: Permission action — ``view``, ``add``, ``change``, or ``delete``.
        auth_dependency: Optional authentication dependency.

    Returns:
        FastAPI dependency that resolves the user and raises
        ``PermissionDeniedError`` when access is denied.

    Raises:
        PermissionDeniedError: When the user lacks the requested permission.
    """
    user_dep = optional_user(auth_dependency)

    async def _check(
        request: Request,
        user: Any = Depends(user_dep),
    ) -> Any:
        check_map = {
            "view": model_admin.has_view_permission,
            "add": model_admin.has_add_permission,
            "change": model_admin.has_change_permission,
            "delete": model_admin.has_delete_permission,
        }
        checker = check_map.get(action, model_admin.has_view_permission)
        if action == "add":
            allowed = checker(request, user)
        else:
            allowed = checker(request, user)
        if not allowed:
            raise PermissionDeniedError(model_admin.collection_name or "model", action)
        return user

    return _check


def verify_csrf(request: Request, admin_site: AdminSite, token: str | None) -> None:
    """Verify CSRF token on mutating requests when a session is present.

    Args:
        request: Current HTTP request.
        admin_site: Admin site providing the expected CSRF token.
        token: Submitted CSRF token from the form.

    Returns:
        None.

    Raises:
        HTTPException: With status 403 when the token does not match.
    """
    if "session" not in request.scope:
        return
    expected = admin_site.get_csrf_token(request)
    if expected and token and expected != token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="CSRF verification failed"
        )
