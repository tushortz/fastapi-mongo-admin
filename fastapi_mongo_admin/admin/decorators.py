"""Decorators for ModelAdmin display columns and actions."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def display(description: str | None = None, ordering: str | None = None) -> Callable[[F], F]:
    """Mark a ModelAdmin method as a changelist display column.

    Args:
        description: Column heading shown in the changelist.
        ordering: Model field name used when sorting by this column.

    Returns:
        Decorator that sets ``admin_display``, ``short_description``, and
        ``admin_order_field`` on the wrapped function.
    """

    def decorator(func: F) -> F:
        func.admin_display = True  # type: ignore[attr-defined]
        func.short_description = description or func.__name__.replace("_", " ").title()  # type: ignore[attr-defined]
        func.admin_order_field = ordering  # type: ignore[attr-defined]
        return func

    return decorator


def action(description: str, permissions: list[str] | None = None) -> Callable[[F], F]:
    """Mark a ModelAdmin method as a bulk admin action.

    Args:
        description: Action label shown in the changelist actions dropdown.
        permissions: Optional list of required permission names.

    Returns:
        Decorator that sets ``admin_action``, ``short_description``, and
        ``allowed_permissions`` on the wrapped function.
    """

    def decorator(func: F) -> F:
        func.admin_action = True  # type: ignore[attr-defined]
        func.short_description = description  # type: ignore[attr-defined]
        func.allowed_permissions = permissions or []  # type: ignore[attr-defined]
        return func

    return decorator
