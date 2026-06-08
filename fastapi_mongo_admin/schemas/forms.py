"""Form parsing and Pydantic validation."""

from __future__ import annotations

import json
import types
import typing
from typing import Any, Type

from pydantic import BaseModel, ValidationError

from fastapi_mongo_admin.exceptions import ValidationError as AdminValidationError


def _unwrap_annotation(annotation: Any) -> Any:
    """Unwrap Optional and union annotations.

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


def _is_bool_field(annotation: Any) -> bool:
    """Return whether a model field annotation is boolean.

    Args:
        annotation: Field type annotation.

    Returns:
        ``True`` when the field is a ``bool``.
    """
    return _unwrap_annotation(annotation) is bool


def _is_optional(annotation: Any) -> bool:
    """Return whether a field annotation is optional.

    Args:
        annotation: Field type annotation.

    Returns:
        ``True`` when ``None`` is allowed.
    """
    origin = typing.get_origin(annotation)
    if origin is typing.Union or origin is types.UnionType:
        return type(None) in typing.get_args(annotation)
    return False


def _is_list_annotation(annotation: Any) -> bool:
    """Return whether a field annotation is a list type."""
    inner = _unwrap_annotation(annotation)
    origin = typing.get_origin(inner)
    return origin in (list, typing.List) or inner is list


def _is_dict_annotation(annotation: Any) -> bool:
    """Return whether a field annotation is a dict or mapping type."""
    inner = _unwrap_annotation(annotation)
    origin = typing.get_origin(inner)
    return origin in (dict, typing.Dict) or inner is dict


def _is_nested_model(annotation: Any) -> bool:
    """Return whether a field annotation is a nested Pydantic model.

    Args:
        annotation: Field type annotation.

    Returns:
        ``True`` for nested ``BaseModel`` types.
    """
    inner = _unwrap_annotation(annotation)
    return isinstance(inner, type) and issubclass(inner, BaseModel)


def _is_empty_nested_value(value: Any) -> bool:
    """Return whether a nested value is effectively empty.

    Args:
        value: Raw nested field value.

    Returns:
        ``True`` for ``None``, empty strings, ``{}``, or ``[]``.
    """
    if value is None:
        return True
    if isinstance(value, str) and value.strip() in ("", "{}", "[]", "null"):
        return True
    if isinstance(value, (dict, list)) and not value:
        return True
    return False


def _parse_json_value(raw: str) -> Any:
    """Parse a JSON string from a form field.

    Args:
        raw: JSON string from a form control.

    Returns:
        Parsed Python value, or the original string on decode failure.
    """
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def parse_form_to_model(
    model: Type[BaseModel] | None,
    form_data: dict[str, Any],
    *,
    existing: dict[str, Any] | None = None,
    readonly_fields: list[str] | None = None,
) -> dict[str, Any]:
    """Validate and normalize form or JSON data through a Pydantic model.

    Args:
        model: Pydantic model class, or ``None`` to pass data through unchanged.
        form_data: Raw submitted field values.
        existing: Existing document for partial updates.
        readonly_fields: Field names preserved from ``existing`` when omitted.

    Returns:
        Validated document dict from ``model.model_dump()``.

    Raises:
        AdminValidationError: When Pydantic validation fails.
    """
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
    except ValidationError as exc:
        raise AdminValidationError(str(exc)) from exc
    return instance.model_dump()


def _coerce_value(raw: Any, annotation: Any) -> Any:
    """Coerce form string values to appropriate Python types.

    Args:
        raw: Raw submitted value.
        annotation: Target field type annotation.

    Returns:
        Coerced value suitable for Pydantic validation.
    """
    inner = _unwrap_annotation(annotation)
    optional = _is_optional(annotation)
    if raw is None:
        return None
    if _is_empty_nested_value(raw) and optional:
        return None
    if _is_nested_model(annotation):
        if isinstance(raw, str):
            raw = _parse_json_value(raw)
        if _is_empty_nested_value(raw) and optional:
            return None
        return raw
    if _is_list_annotation(annotation):
        if isinstance(raw, str):
            parsed = _parse_json_value(raw)
            if isinstance(parsed, dict):
                return []
            if isinstance(parsed, list):
                return parsed
            if _is_empty_nested_value(parsed) and optional:
                return None
            return parsed
        if isinstance(raw, dict):
            return []
        if isinstance(raw, list):
            return raw
    if _is_dict_annotation(annotation):
        if isinstance(raw, str):
            parsed = _parse_json_value(raw)
            if _is_empty_nested_value(parsed) and optional:
                return None
            return parsed
    if inner is bool:
        if isinstance(raw, str):
            return raw.lower() in ("true", "1", "on", "yes")
        return bool(raw)
    return raw
