"""Filter resolution and query building."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fastapi import Request

from fastapi_mongo_admin.admin.filters.base import ListFilter
from fastapi_mongo_admin.admin.filters.boolean import BooleanFieldListFilter
from fastapi_mongo_admin.admin.filters.choice import ChoiceListFilter
from fastapi_mongo_admin.admin.filters.date import DateFieldListFilter

if TYPE_CHECKING:
    from fastapi_mongo_admin.admin.model import ModelAdmin


def resolve_list_filters(
    model_admin: ModelAdmin,
    list_filter: list[str | type[ListFilter]],
    request: Request | None = None,
    params: dict[str, str] | None = None,
) -> list[ListFilter]:
    """Instantiate filters from ModelAdmin.list_filter."""
    params = params or {}
    filters: list[ListFilter] = []
    for item in list_filter:
        if isinstance(item, str):
            field_name = item
            filter_cls = _default_filter_for_field(model_admin, field_name)
            filters.append(filter_cls(request, params, model_admin, field_name))  # type: ignore[arg-type]
        elif isinstance(item, type) and issubclass(item, ListFilter):
            field_name = item.parameter_name or "filter"
            filters.append(item(request, params, model_admin, field_name))  # type: ignore[arg-type]
    return filters


def _default_filter_for_field(model_admin: ModelAdmin, field_name: str) -> type[ListFilter]:
    """Pick a default filter class based on field metadata."""
    if model_admin.model is None:
        return ChoiceListFilter
    field = model_admin.model.model_fields.get(field_name)
    if field is None:
        return ChoiceListFilter
    annotation = field.annotation
    type_name = str(annotation).lower()
    if "bool" in type_name:
        return BooleanFieldListFilter
    if "date" in type_name or "datetime" in type_name:
        return DateFieldListFilter
    if model_admin.choices and field_name in (model_admin.choices or {}):
        return ChoiceListFilter
    return ChoiceListFilter


def build_filter_query(
    model_admin: ModelAdmin,
    request_params: dict[str, str],
    request: Request | None = None,
) -> dict[str, Any]:
    """Merge all active list filter queries."""
    params = {k: v for k, v in request_params.items() if v}
    filters = resolve_list_filters(
        model_admin, model_admin.list_filter or [], request=request, params=params
    )
    query: dict[str, Any] = {}
    for flt in filters:
        value = params.get(flt.parameter_name, "")
        if not value:
            continue
        fragment = flt.queryset(value)
        db_fragment = {}
        mapping = model_admin.field_mapping or {}
        for key, val in fragment.items():
            db_key = mapping.get(key, key)
            db_fragment[db_key] = val
        query.update(db_fragment)
    return query
