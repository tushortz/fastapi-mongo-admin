"""List filters for changelist."""

from fastapi_mongo_admin.admin.filters.base import ListFilter
from fastapi_mongo_admin.admin.filters.boolean import BooleanFieldListFilter
from fastapi_mongo_admin.admin.filters.choice import ChoiceListFilter
from fastapi_mongo_admin.admin.filters.date import DateFieldListFilter, build_date_hierarchy_query
from fastapi_mongo_admin.admin.filters.related import RelatedFieldListFilter

__all__ = [
    "ListFilter",
    "ChoiceListFilter",
    "DateFieldListFilter",
    "BooleanFieldListFilter",
    "RelatedFieldListFilter",
    "build_date_hierarchy_query",
]


def __getattr__(name: str):
    """Lazy export to avoid circular imports.

    Args:
        name: Attribute name requested via ``from module import name``.

    Returns:
        ``build_filter_query`` or ``resolve_list_filters`` when requested.

    Raises:
        AttributeError: When ``name`` is not a lazy export.
    """
    if name in ("build_filter_query", "resolve_list_filters"):
        from fastapi_mongo_admin.admin.filters.registry import (
            build_filter_query,
            resolve_list_filters,
        )

        return {
            "build_filter_query": build_filter_query,
            "resolve_list_filters": resolve_list_filters,
        }[name]
    raise AttributeError(name)
