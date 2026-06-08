"""Admin field metadata."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AdminField:
    """Metadata for rendering a single admin form field.

    Attributes:
        name: Model field name.
        field_type: Inferred admin field type (``str``, ``int``, ``bool``, etc.).
        label: Human-readable field label.
        required: Whether the field is required on the form.
        readonly: Whether the field is read-only.
        widget: HTML widget type (``text``, ``select``, ``checkbox``, etc.).
        choices: Select choices as ``(value, label)`` tuples.
        help_text: Optional help text.
        value: Current field value for the form.
        step: HTML ``step`` attribute for numeric inputs.
        attrs: Extra HTML attributes for the widget.
    """

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
