"""Query building for changelist."""

from __future__ import annotations

import re
from typing import Any

from fastapi_mongo_admin.admin.filters.date import build_date_hierarchy_query
from fastapi_mongo_admin.admin.filters.registry import build_filter_query
from fastapi_mongo_admin.admin.model import ModelAdmin
from fastapi_mongo_admin.services.mapping import translate_query


def build_search_query(search: str, search_fields: list[str], mapping: dict[str, str] | None) -> dict[str, Any]:
    """Build text search query across search_fields."""
    if not search or not search_fields:
        return {}
    fields = search_fields[:10]
    db_fields = [mapping.get(f, f) if mapping else f for f in fields]
    return {
        "$or": [{field: {"$regex": re.escape(search), "$options": "i"}} for field in db_fields]
    }


def parse_ordering(ordering: list[str], mapping: dict[str, str] | None) -> list[tuple[str, int]]:
    """Parse ordering strings to MongoDB sort spec."""
    sort: list[tuple[str, int]] = []
    for item in ordering:
        if item.startswith("-"):
            field = item[1:]
            direction = -1
        else:
            field = item
            direction = 1
        db_field = mapping.get(field, field) if mapping else field
        sort.append((db_field, direction))
    return sort


def build_changelist_query(
    model_admin: ModelAdmin,
    *,
    search: str = "",
    filter_params: dict[str, str] | None = None,
    date_hierarchy_params: dict[str, str] | None = None,
    base_query: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Merge base, filter, search, and date hierarchy queries."""
    mapping = model_admin.field_mapping
    query: dict[str, Any] = dict(base_query or {})
    filter_params = filter_params or {}
    filter_q = build_filter_query(model_admin, filter_params)
    if filter_q:
        query.update(filter_q)
    search_q = build_search_query(search, model_admin.get_search_fields(), mapping)
    if search_q:
        if query:
            query = {"$and": [query, search_q]}
        else:
            query = search_q
    if model_admin.date_hierarchy and date_hierarchy_params:
        db_field = (mapping or {}).get(model_admin.date_hierarchy, model_admin.date_hierarchy)
        dh_q = build_date_hierarchy_query(
            db_field,
            date_hierarchy_params.get("year"),
            date_hierarchy_params.get("month"),
            date_hierarchy_params.get("day"),
        )
        if dh_q:
            if query:
                query = {"$and": [query, dh_q]}
            else:
                query = dh_q
    return translate_query(query, mapping) if mapping else query
