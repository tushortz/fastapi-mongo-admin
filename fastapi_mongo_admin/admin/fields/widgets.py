"""Widget type constants and per-field override configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

TEXT = "text"
TEXTAREA = "textarea"
NUMBER = "number"
CHECKBOX = "checkbox"
SELECT = "select"
DATE = "date"
DATETIME = "datetime-local"
EMAIL = "email"
JSON_EDITOR = "json"
OBJECT_ID = "objectid"
HIDDEN = "hidden"

STEP_INTEGER = "1"
STEP_DECIMAL = "0.01"


def widget_for_type(field_type: str, *, has_choices: bool = False) -> str:
    """Map an inferred field type to an HTML widget name.

    Args:
        field_type: Inferred admin field type.
        has_choices: Whether the field has discrete choices.

    Returns:
        Widget name string.
    """
    if has_choices:
        return SELECT
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
