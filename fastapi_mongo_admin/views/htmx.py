"""HTMX response helpers."""

from __future__ import annotations

from typing import Any

from fastapi import Request
from fastapi.responses import HTMLResponse
from jinja2 import Environment


def is_htmx(request: Request) -> bool:
    """Return whether the request was issued by HTMX.

    Args:
        request: Current HTTP request.

    Returns:
        ``True`` when the ``HX-Request`` header is ``true``.
    """
    return request.headers.get("HX-Request") == "true"


def render_partial(
    env: Environment,
    template_name: str,
    context: dict[str, Any],
    request: Request,
) -> HTMLResponse:
    """Render a partial template for HTMX swaps.

    Args:
        env: Jinja2 environment.
        template_name: Partial template path.
        context: Template context variables.
        request: Current HTTP request (injected into the template).

    Returns:
        HTMLResponse containing the rendered partial.
    """
    template = env.get_template(template_name)
    html = template.render(**context, request=request)
    return HTMLResponse(content=html)
