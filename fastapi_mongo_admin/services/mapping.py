"""Field mapping between Pydantic model and MongoDB."""

from __future__ import annotations

from typing import Any


def translate_to_db(data: dict[str, Any], mapping: dict[str, str] | None) -> dict[str, Any]:
    """Translate model field keys to database keys."""
    if not mapping:
        return data
    return {mapping.get(k, k): v for k, v in data.items()}


def translate_from_db(doc: dict[str, Any], mapping: dict[str, str] | None) -> dict[str, Any]:
    """Translate database keys to model field keys."""
    if not mapping:
        return doc
    reverse = {v: k for k, v in mapping.items()}
    return {reverse.get(k, k): v for k, v in doc.items()}


def translate_query(query: dict[str, Any], mapping: dict[str, str] | None) -> dict[str, Any]:
    """Translate query keys including operators."""
    if not mapping:
        return query
    translated: dict[str, Any] = {}
    for key, value in query.items():
        if key.startswith("$"):
            if isinstance(value, list):
                translated[key] = [
                    translate_query(v, mapping) if isinstance(v, dict) else v for v in value
                ]
            elif isinstance(value, dict):
                translated[key] = translate_query(value, mapping)
            else:
                translated[key] = value
            continue
        db_field = mapping.get(key, key)
        if isinstance(value, dict):
            translated[db_field] = translate_query(value, mapping)
        else:
            translated[db_field] = value
    return translated
