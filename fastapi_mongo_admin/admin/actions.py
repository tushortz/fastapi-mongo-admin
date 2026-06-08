"""Admin action helpers."""

from __future__ import annotations

from typing import Any, Callable

DELETE_SELECTED_ACTION = "delete_selected"


async def run_delete_selected(
    model_admin: Any,
    request: Any,
    repo: Any,
    docs: list[dict[str, Any]],
    doc_ids: list[str],
) -> int:
    """Delete selected documents after calling ``delete_model`` hooks.

    Args:
        model_admin: ModelAdmin instance with lifecycle hooks.
        request: Current HTTP request.
        repo: Collection repository for bulk delete.
        docs: Selected document dicts.
        doc_ids: Selected document id strings.

    Returns:
        Number of documents deleted from the database.
    """
    for doc in docs:
        await model_admin.delete_model(request, doc)
    if not doc_ids:
        return 0
    return await repo.delete_many(doc_ids)


def get_model_actions(model_admin: Any) -> list[tuple[str, Callable[..., Any], str]]:
    """Collect ``@action``-decorated methods from a ModelAdmin instance.

    Args:
        model_admin: ModelAdmin instance to inspect.

    Returns:
        List of ``(name, method, short_description)`` tuples.
    """
    actions: list[tuple[str, Callable[..., Any], str]] = []
    for name in dir(model_admin):
        if name.startswith("_"):
            continue
        method = getattr(model_admin, name)
        if callable(method) and getattr(method, "admin_action", False):
            description = getattr(method, "short_description", name)
            actions.append((name, method, description))
    return actions
