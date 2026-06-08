"""Admin field metadata."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AdminField:
    """Metadata for rendering a form field."""

    name: str
    field_type: str
    label: str
    required: bool = False
    readonly: bool = False
    widget: str = "text"
    choices: list[tuple[Any, str]] = field(default_factory=list)
    help_text: str = ""
    value: Any = None
    step: str | None = None
    attrs: dict[str, Any] = field(default_factory=dict)
