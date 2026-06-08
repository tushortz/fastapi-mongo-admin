"""Admin action helpers."""

from __future__ import annotations

from typing import Any, Callable


def get_model_actions(model_admin: Any) -> list[tuple[str, Callable[..., Any], str]]:
    """Collect registered admin actions from a ModelAdmin instance."""
    actions: list[tuple[str, Callable[..., Any], str]] = []
    for name in dir(model_admin):
        if name.startswith("_"):
            continue
        method = getattr(model_admin, name)
        if callable(method) and getattr(method, "admin_action", False):
            description = getattr(method, "short_description", name)
            actions.append((name, method, description))
    return actions
