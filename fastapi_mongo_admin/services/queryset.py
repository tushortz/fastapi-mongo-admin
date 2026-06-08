"""Query building for changelist."""

from __future__ import annotations

import re
from typing import Any

from fastapi_mongo_admin.admin.filters.date import build_date_hierarchy_query
from fastapi_mongo_admin.admin.filters.registry import build_filter_query
from fastapi_mongo_admin.admin.model import ModelAdmin
from fastapi_mongo_admin.services.mapping import translate_query

RELATED_SEARCH_FIELDS = (
    "name",
    "title",
    "slug",
    "email",
    "first_name",
    "last_name",
    "order_number",
    "code",
)


def build_related_search_query(search: str) -> dict[str, Any]:
    """Build a case-insensitive regex query across common related-document labels.

    Args:
        search: User search string (at least two characters).

    Returns:
        MongoDB ``$or`` regex query, or empty dict when search is blank.
    """
    if not search:
        return {}
    pattern = {"$regex": re.escape(search), "$options": "i"}
    return {"$or": [{field: pattern} for field in RELATED_SEARCH_FIELDS]}


def build_search_query(
    search: str, search_fields: list[str], mapping: dict[str, str] | None
) -> dict[str, Any]:
    """Build a case-insensitive regex search query across fields.

    Args:
        search: User search string.
        search_fields: Model field names to search.
        mapping: Optional field mapping to database keys.

    Returns:
        MongoDB ``$or`` regex query, or empty dict when search is blank.
    """
    if not search or not search_fields:
        return {}
    fields = search_fields[:10]
    db_fields = [mapping.get(f, f) if mapping else f for f in fields]
    return {"$or": [{field: {"$regex": re.escape(search), "$options": "i"}} for field in db_fields]}


def resolve_changelist_ordering(
    model_admin: ModelAdmin, filter_params: dict[str, str] | None
) -> list[str]:
    """Resolve ordering from ``?o=`` query param or ModelAdmin defaults.

    Args:
        model_admin: ModelAdmin providing default ordering and sortable columns.
        filter_params: Request query parameters (may include ``o``).

    Returns:
        List of ordering strings (prefix ``-`` for descending).
    """
    params = filter_params or {}
    raw = params.get("o", "").strip()
    if not raw:
        return model_admin.get_ordering()
    descending = raw.startswith("-")
    column = raw[1:] if descending else raw
    sort_field = model_admin.get_sortable_field(column)
    if sort_field is None:
        return model_admin.get_ordering()
    prefix = "-" if descending else ""
    return [f"{prefix}{sort_field}"]


def parse_ordering(ordering: list[str], mapping: dict[str, str] | None) -> list[tuple[str, int]]:
    """Parse ordering strings to a MongoDB sort specification.

    Args:
        ordering: List of field names; prefix ``-`` for descending.
        mapping: Optional field mapping to database keys.

    Returns:
        List of ``(db_field, direction)`` tuples for PyMongo/Motor ``sort``.
    """
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
    """Merge base, filter, search, and date hierarchy queries.

    Args:
        model_admin: ModelAdmin providing filters, search fields, and mapping.
        search: Changelist search string.
        filter_params: Active list-filter query parameters.
        date_hierarchy_params: Optional ``year``/``month``/``day`` drill-down params.
        base_query: Base query from ``get_queryset``.

    Returns:
        Combined MongoDB filter document.
    """
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
