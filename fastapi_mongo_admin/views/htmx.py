"""HTMX response helpers."""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import HTMLResponse
from jinja2 import Environment


def is_htmx(request: Request) -> bool:
    """Return True if request is from HTMX."""
    return request.headers.get("HX-Request") == "true"


def render_partial(
    env: Environment,
    template_name: str,
    context: dict,
    request: Request,
) -> HTMLResponse:
    """Render a partial template for HTMX swaps."""
    template = env.get_template(template_name)
    html = template.render(**context, request=request)
    return HTMLResponse(content=html)
