"""Pydantic schema inference for admin forms and lists."""

from __future__ import annotations

import enum
import types
import typing
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Type

from bson import ObjectId
from bson.decimal128 import Decimal128
from pydantic import BaseModel

from fastapi_mongo_admin.admin.fields.base import AdminField
from fastapi_mongo_admin.admin.fields.widgets import (
    JSON_EDITOR,
    TEXTAREA,
    FieldWidget,
    apply_field_widget_override,
    step_for_type,
    widget_for_type,
)


def _serialize_value(value: Any) -> Any:
    """Convert a single MongoDB value to a JSON/template-safe Python value.

    Args:
        value: BSON or Python value.

    Returns:
        JSON-serializable value.
    """
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal128):
        return str(value.to_decimal())
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return serialize_document(value)
    if isinstance(value, list):
        return [_serialize_value(item) for item in value]
    return value


def serialize_document(doc: dict[str, Any]) -> dict[str, Any]:
    """Convert a MongoDB document to a JSON-serializable dict.

    Args:
        doc: Raw MongoDB document.

    Returns:
        Serialized document with ``id`` alias for ``_id``.
    """
    result = {key: _serialize_value(value) for key, value in doc.items()}
    if "_id" in result:
        result["id"] = result["_id"]
    return result


def prepare_for_mongodb(value: Any) -> Any:
    """Recursively convert Python values to BSON-encodable types.

    Args:
        value: Python value from a validated model.

    Returns:
        BSON-safe value for insertion/update.
    """
    if isinstance(value, Decimal):
        return Decimal128(str(value))
    if isinstance(value, date) and not isinstance(value, datetime):
        return datetime.combine(value, datetime.min.time())
    if isinstance(value, dict):
        return {key: prepare_for_mongodb(item) for key, item in value.items()}
    if isinstance(value, list):
        return [prepare_for_mongodb(item) for item in value]
    return value


def _unwrap_annotation(annotation: Any) -> Any:
    """Unwrap Optional and other union wrappers.

    Args:
        annotation: Type annotation to unwrap.

    Returns:
        Inner non-``None`` annotation type.
    """
    origin = typing.get_origin(annotation)
    if origin is typing.Union or origin is types.UnionType:
        args = [a for a in typing.get_args(annotation) if a is not type(None)]
        if args:
            return _unwrap_annotation(args[0])
    return annotation


def _field_type(annotation: Any) -> str:
    """Map a Pydantic field annotation to an admin field type string.

    Args:
        annotation: Field type annotation.

    Returns:
        Admin field type name (``str``, ``int``, ``datetime``, etc.).
    """
    inner = _unwrap_annotation(annotation)
    origin = typing.get_origin(inner)
    if origin in (list, typing.List):
        return "list"
    if origin in (dict, typing.Dict):
        return "dict"
    if origin is typing.Literal:
        return "str"
    if inner is str:
        return "str"
    if inner is int:
        return "int"
    if inner is float:
        return "float"
    if inner is bool:
        return "bool"
    if isinstance(inner, type) and issubclass(inner, datetime):
        return "datetime"
    if isinstance(inner, type) and issubclass(inner, date):
        return "date"
    if inner is ObjectId:
        return "ObjectId"
    if inner is Decimal or (isinstance(inner, type) and issubclass(inner, Decimal)):
        return "decimal"
    if isinstance(inner, type) and issubclass(inner, enum.Enum):
        return "str"
    if isinstance(inner, type) and issubclass(inner, BaseModel):
        return "dict"
    return "str"


def _extract_choices(
    annotation: Any,
    field_name: str,
    choices: dict[str, list[tuple[Any, str]]] | None,
) -> list[tuple[Any, str]]:
    """Extract choice options from ModelAdmin config, Enum, or Literal.

    Args:
        annotation: Field type annotation.
        field_name: Model field name.
        choices: Optional ModelAdmin ``choices`` mapping.

    Returns:
        List of ``(value, label)`` tuples.
    """
    if choices and field_name in choices:
        return list(choices[field_name])
    inner = _unwrap_annotation(annotation)
    if isinstance(inner, type) and issubclass(inner, enum.Enum):
        return [(member.value, member.name.replace("_", " ").title()) for member in inner]
    origin = typing.get_origin(inner)
    if origin is typing.Literal:
        return [(value, str(value)) for value in typing.get_args(inner)]
    return []


def format_field_value(field: AdminField) -> Any:
    """Format a field value for HTML form controls.

    Args:
        field: ``AdminField`` with ``value`` and widget metadata.

    Returns:
        Value formatted for the field's widget type.
    """
    value = field.value
    if value is None or value == "":
        return None if field.widget == "select" and not field.required else value

    if field.widget == "checkbox":
        if isinstance(value, str):
            return value.lower() in ("true", "1", "yes", "on")
        return bool(value)

    if field.widget == "date":
        if isinstance(value, datetime):
            return value.date().isoformat()
        if isinstance(value, date):
            return value.isoformat()
        if isinstance(value, str):
            return value.split("T")[0][:10]
        return value

    if field.widget == "datetime-local":
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%dT%H:%M")
        if isinstance(value, str):
            normalized = value.replace("Z", "+00:00")
            try:
                parsed = datetime.fromisoformat(normalized)
                return parsed.strftime("%Y-%m-%dT%H:%M")
            except ValueError:
                cleaned = value.split("+")[0].split(".")[0]
                return cleaned[:16] if len(cleaned) >= 16 else cleaned
        return value

    if field.field_type in ("float", "decimal"):
        try:
            return f"{float(value):.2f}"
        except (TypeError, ValueError):
            return value

    if field.field_type == "int":
        try:
            return str(int(float(value)))
        except (TypeError, ValueError):
            return value

    return value


def _default_widget_attrs(widget: str) -> dict[str, Any]:
    """Return default HTML attributes for built-in widgets.

    Args:
        widget: Widget name.

    Returns:
        Dict of HTML attribute defaults.
    """
    if widget == TEXTAREA:
        return {"rows": 4}
    if widget == JSON_EDITOR:
        return {"rows": 6, "class": "vLargeTextField"}
    return {}


def infer_admin_fields(
    model: Type[BaseModel] | None,
    *,
    readonly_fields: list[str] | None = None,
    choices: dict[str, list[tuple[Any, str]]] | None = None,
    field_overrides: dict[str, FieldWidget | dict[str, Any]] | None = None,
) -> list[AdminField]:
    """Build an ``AdminField`` list from a Pydantic model.

    Args:
        model: Pydantic model class.
        readonly_fields: Field names rendered read-only.
        choices: Per-field select choices.
        field_overrides: Per-field widget overrides.

    Returns:
        List of ``AdminField`` metadata objects.
    """
    if model is None:
        return []
    readonly = set(readonly_fields or [])
    overrides = {
        name: FieldWidget.from_mapping(config) for name, config in (field_overrides or {}).items()
    }
    fields: list[AdminField] = []
    for name, field_info in model.model_fields.items():
        annotation = field_info.annotation
        ftype = _field_type(annotation)
        field_choices = _extract_choices(annotation, name, choices)
        has_choices = bool(field_choices)
        widget = widget_for_type(ftype, has_choices=has_choices)
        admin_field = AdminField(
            name=name,
            field_type=ftype,
            label=name.replace("_", " ").title(),
            required=field_info.is_required(),
            readonly=name in readonly,
            widget=widget,
            choices=field_choices,
            step=step_for_type(ftype) if widget == "number" else None,
            attrs=_default_widget_attrs(widget),
        )
        if name in overrides:
            apply_field_widget_override(admin_field, overrides[name])
        fields.append(admin_field)
    return fields


def prepare_form_fields(
    model: Type[BaseModel] | None,
    *,
    obj: dict[str, Any] | None = None,
    readonly_fields: list[str] | None = None,
    choices: dict[str, list[tuple[Any, str]]] | None = None,
    field_overrides: dict[str, FieldWidget | dict[str, Any]] | None = None,
    display_formatter: Any | None = None,
) -> list[AdminField]:
    """Build admin fields with values formatted for HTML widgets.

    Args:
        model: Pydantic model class.
        obj: Existing document for edit forms.
        readonly_fields: Field names rendered read-only.
        choices: Per-field select choices.
        field_overrides: Per-field widget overrides.
        display_formatter: Optional object with ``format_display_value``.

    Returns:
        List of ``AdminField`` objects with ``value`` populated.
    """
    fields = infer_admin_fields(
        model,
        readonly_fields=readonly_fields,
        choices=choices,
        field_overrides=field_overrides,
    )
    for admin_field in fields:
        if obj is None:
            continue
        if admin_field.name in obj:
            admin_field.value = obj[admin_field.name]
        elif admin_field.name == "id" and "_id" in obj:
            admin_field.value = obj["_id"]
        if admin_field.readonly and display_formatter is not None:
            admin_field.value = display_formatter.format_display_value(
                admin_field.name, admin_field.value
            )
        else:
            admin_field.value = format_field_value(admin_field)
    return fields


def infer_schema_dict(model: Type[BaseModel]) -> dict[str, Any]:
    """Return schema metadata dict for API responses.

    Args:
        model: Pydantic model class.

    Returns:
        Dict with ``model`` name and per-field metadata.
    """
    fields = infer_admin_fields(model)
    return {
        "model": model.__name__,
        "fields": {
            f.name: {
                "type": f.field_type,
                "required": f.required,
                "readonly": f.readonly,
                "widget": f.widget,
                "choices": f.choices,
                "step": f.step,
                "attrs": f.attrs,
            }
            for f in fields
        },
    }
