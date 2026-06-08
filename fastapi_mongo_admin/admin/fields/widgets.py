"""Widget type constants and per-field override configuration."""

from __future__ import annotations

import enum
import types
import typing
from dataclasses import dataclass, field
from typing import Any

TEXT = "text"
TEXTAREA = "textarea"
NUMBER = "number"
CHECKBOX = "checkbox"
SELECT = "select"
RELATED_SELECT = "related_select"
DATE = "date"
DATETIME = "datetime-local"
EMAIL = "email"
JSON_EDITOR = "json"
TAGS = "tags"
OBJECT_ID = "objectid"
HIDDEN = "hidden"

STEP_INTEGER = "1"
STEP_DECIMAL = "0.01"


def _unwrap_annotation(annotation: Any) -> Any:
    """Unwrap Optional and union annotations."""
    origin = typing.get_origin(annotation)
    if origin is typing.Union or origin is types.UnionType:
        args = [arg for arg in typing.get_args(annotation) if arg is not type(None)]
        if args:
            return _unwrap_annotation(args[0])
    return annotation


def is_primitive_list(annotation: Any) -> bool:
    """Return whether an annotation is a list of primitive scalar values."""
    inner = _unwrap_annotation(annotation)
    origin = typing.get_origin(inner)
    if origin not in (list, typing.List):
        return False
    args = typing.get_args(inner)
    if not args:
        return True
    element = _unwrap_annotation(args[0])
    if element is str or element in (int, float, bool):
        return True
    if isinstance(element, type) and issubclass(element, enum.Enum):
        return True
    if typing.get_origin(element) is typing.Literal:
        return True
    return False


def widget_for_type(
    field_type: str,
    *,
    has_choices: bool = False,
    annotation: Any = None,
) -> str:
    """Map an inferred field type to an HTML widget name.

    Args:
        field_type: Inferred admin field type.
        has_choices: Whether the field has discrete choices.
        annotation: Original field annotation for list element detection.

    Returns:
        Widget name string.
    """
    if has_choices:
        return SELECT
    if field_type == "list" and annotation is not None and is_primitive_list(annotation):
        return TAGS
    mapping = {
        "str": TEXT,
        "int": NUMBER,
        "float": NUMBER,
        "decimal": NUMBER,
        "bool": CHECKBOX,
        "datetime": DATETIME,
        "date": DATE,
        "list": JSON_EDITOR,
        "dict": JSON_EDITOR,
        "ObjectId": OBJECT_ID,
    }
    return mapping.get(field_type, TEXT)


def step_for_type(field_type: str) -> str | None:
    """Return the HTML ``step`` attribute for numeric field types.

    Args:
        field_type: Inferred admin field type.

    Returns:
        Step string for numeric widgets, or ``None``.
    """
    if field_type == "int":
        return STEP_INTEGER
    if field_type in ("float", "decimal"):
        return STEP_DECIMAL
    return None


@dataclass
class FieldWidget:
    """Override default widget and HTML attributes for a model field."""

    widget: str | None = None
    """Widget name override."""

    attrs: dict[str, Any] = field(default_factory=dict)
    """Extra HTML attributes merged onto the rendered control."""

    @classmethod
    def from_mapping(cls, data: FieldWidget | dict[str, Any]) -> FieldWidget:
        """Build from a FieldWidget instance or shorthand dict.

        Args:
            data: ``FieldWidget`` or dict with optional ``widget`` key plus
                HTML attribute overrides.

        Returns:
            Normalized ``FieldWidget`` instance.
        """
        if isinstance(data, FieldWidget):
            return data
        mapping = dict(data)
        widget = mapping.pop("widget", None)
        return cls(widget=widget, attrs=mapping)


def apply_field_widget_override(
    admin_field: Any,
    override: FieldWidget | dict[str, Any],
) -> None:
    """Apply a widget override onto an ``AdminField``.

    Args:
        admin_field: ``AdminField`` instance to mutate.
        override: ``FieldWidget`` or shorthand dict.

    Returns:
        None.
    """
    config = FieldWidget.from_mapping(override)
    if config.widget:
        admin_field.widget = config.widget
    admin_field.attrs.update(config.attrs)
