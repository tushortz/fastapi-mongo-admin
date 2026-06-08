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
    """Map inferred type to HTML widget."""
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
    """Return HTML step attribute for numeric fields."""
    if field_type == "int":
        return STEP_INTEGER
    if field_type in ("float", "decimal"):
        return STEP_DECIMAL
    return None


@dataclass
class FieldWidget:
    """Override default widget and HTML attributes for a model field."""

    widget: str | None = None
    attrs: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, data: FieldWidget | dict[str, Any]) -> FieldWidget:
        """Build from a FieldWidget or a shorthand dict (widget key + HTML attrs)."""
        if isinstance(data, FieldWidget):
            return data
        mapping = dict(data)
        widget = mapping.pop("widget", None)
        return cls(widget=widget, attrs=mapping)


def apply_field_widget_override(
    admin_field: Any,
    override: FieldWidget | dict[str, Any],
) -> None:
    """Apply widget override and HTML attrs onto an AdminField."""
    config = FieldWidget.from_mapping(override)
    if config.widget:
        admin_field.widget = config.widget
    admin_field.attrs.update(config.attrs)
