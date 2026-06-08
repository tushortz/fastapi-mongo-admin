"""Form parsing and Pydantic validation."""

from __future__ import annotations

import json
import types
import typing
from typing import Any, Type

from pydantic import BaseModel, ValidationError

from fastapi_mongo_admin.exceptions import ValidationError as AdminValidationError


def _unwrap_annotation(annotation: Any) -> Any:
    """Unwrap Optional and union annotations."""
    origin = typing.get_origin(annotation)
    if origin is typing.Union or origin is types.UnionType:
        args = [a for a in typing.get_args(annotation) if a is not type(None)]
        if args:
            return _unwrap_annotation(args[0])
    return annotation


def _is_bool_field(annotation: Any) -> bool:
    """Return whether a model field annotation is a boolean."""
    return _unwrap_annotation(annotation) is bool


def parse_form_to_model(
    model: Type[BaseModel] | None,
    form_data: dict[str, Any],
    *,
    existing: dict[str, Any] | None = None,
    readonly_fields: list[str] | None = None,
) -> dict[str, Any]:
    """Validate and normalize form data through Pydantic model."""
    if model is None:
        return form_data
    readonly = set(readonly_fields or [])
    cleaned: dict[str, Any] = {}
    for name, field_info in model.model_fields.items():
        if name in readonly and name not in form_data:
            if existing is not None and name in existing:
                cleaned[name] = existing[name]
            continue
        if name not in form_data:
            if _is_bool_field(field_info.annotation):
                cleaned[name] = False
            continue
        raw = form_data[name]
        if raw == "" and not field_info.is_required():
            continue
        cleaned[name] = _coerce_value(raw, field_info.annotation)
    try:
        instance = model.model_validate(cleaned)
        return instance.model_dump()
    except ValidationError as exc:
        raise AdminValidationError(str(exc)) from exc


def _coerce_value(raw: Any, annotation: Any) -> Any:
    """Coerce form string values to appropriate types."""
    inner = _unwrap_annotation(annotation)
    if raw is None:
        return None
    origin = typing.get_origin(inner)
    if origin in (list, dict) or inner in (list, dict):
        if isinstance(raw, str):
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return raw
    if inner is bool:
        if isinstance(raw, str):
            return raw.lower() in ("true", "1", "on", "yes")
        return bool(raw)
    return raw
