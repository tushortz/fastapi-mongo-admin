"""Pydantic schema inference for admin forms and lists."""

from __future__ import annotations

import enum
import typing
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Type

from bson import ObjectId
from pydantic import BaseModel
from fastapi_mongo_admin.admin.fields.base import AdminField
from fastapi_mongo_admin.admin.fields.widgets import widget_for_type


def serialize_document(doc: dict[str, Any]) -> dict[str, Any]:
    """Convert MongoDB document to JSON-serializable dict."""
    result: dict[str, Any] = {}
    for key, value in doc.items():
        if isinstance(value, ObjectId):
            result[key] = str(value)
        elif isinstance(value, datetime):
            result[key] = value.isoformat()
        elif isinstance(value, date):
            result[key] = value.isoformat()
        elif isinstance(value, dict):
            result[key] = serialize_document(value)
        elif isinstance(value, list):
            result[key] = [
                serialize_document(v) if isinstance(v, dict) else str(v) if isinstance(v, ObjectId) else v
                for v in value
            ]
        else:
            result[key] = value
    if "_id" in result:
        result["id"] = result["_id"]
    return result


def _field_type(annotation: Any) -> str:
    origin = typing.get_origin(annotation)
    if origin is typing.Union:
        args = [a for a in typing.get_args(annotation) if a is not type(None)]
        if args:
            return _field_type(args[0])
    if origin in (list, typing.List):
        return "list"
    if origin in (dict, typing.Dict):
        return "dict"
    if annotation is str:
        return "str"
    if annotation is int:
        return "int"
    if annotation is float:
        return "float"
    if annotation is bool:
        return "bool"
    if annotation is datetime:
        return "datetime"
    if annotation is date:
        return "date"
    if annotation is ObjectId:
        return "ObjectId"
    if annotation is Decimal:
        return "decimal"
    if isinstance(annotation, type) and issubclass(annotation, enum.Enum):
        return "str"
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return "dict"
    return "str"


def infer_admin_fields(
    model: Type[BaseModel] | None,
    *,
    readonly_fields: list[str] | None = None,
    choices: dict[str, list[tuple[Any, str]]] | None = None,
) -> list[AdminField]:
    """Build AdminField list from Pydantic model."""
    if model is None:
        return []
    readonly = set(readonly_fields or [])
    fields: list[AdminField] = []
    for name, field_info in model.model_fields.items():
        ftype = _field_type(field_info.annotation)
        enum_choices: list[tuple[Any, str]] = []
        if choices and name in choices:
            enum_choices = list(choices[name])
        elif isinstance(field_info.annotation, type) and issubclass(field_info.annotation, enum.Enum):
            enum_choices = [(e.value, e.name) for e in field_info.annotation]
        required = field_info.is_required()
        fields.append(
            AdminField(
                name=name,
                field_type=ftype,
                label=name.replace("_", " ").title(),
                required=required,
                readonly=name in readonly,
                widget=widget_for_type(ftype),
                choices=enum_choices,
            )
        )
    return fields


def infer_schema_dict(model: Type[BaseModel]) -> dict[str, Any]:
    """Return schema metadata dict for API responses."""
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
            }
            for f in fields
        },
    }
