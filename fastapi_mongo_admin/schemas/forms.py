"""Form parsing and Pydantic validation."""

from __future__ import annotations

import json
from typing import Any, Type

from pydantic import BaseModel, ValidationError

from fastapi_mongo_admin.exceptions import ValidationError as AdminValidationError


def parse_form_to_model(model: Type[BaseModel] | None, form_data: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalize form data through Pydantic model."""
    if model is None:
        return form_data
    cleaned: dict[str, Any] = {}
    for name, field_info in model.model_fields.items():
        if name not in form_data:
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
    import typing

    if raw is None:
        return None
    origin = typing.get_origin(annotation)
    if origin is typing.Union:
        args = [a for a in typing.get_args(annotation) if a is not type(None)]
        if args:
            return _coerce_value(raw, args[0])
    if origin in (list, dict) or annotation in (list, dict):
        if isinstance(raw, str):
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return raw
    if annotation is bool:
        if isinstance(raw, str):
            return raw.lower() in ("true", "1", "on", "yes")
    return raw
