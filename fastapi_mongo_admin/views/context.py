"""Template context builders."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

from fastapi import Request

from fastapi_mongo_admin.admin.model import ModelAdmin
from fastapi_mongo_admin.admin.site import AdminSite
from fastapi_mongo_admin.i18n import Translator
from fastapi_mongo_admin.schemas.inference import prepare_form_fields
from fastapi_mongo_admin.views.preferences import build_ui_context


def build_index_context(
    admin_site: AdminSite,
    prefix: str,
    request: Request | None = None,
) -> dict[str, Any]:
    """Build admin index context."""
    models = []
    for collection, model_admin in admin_site.get_registered_models().items():
        models.append(
            {
                "collection": collection,
                "name": model_admin.get_model_name(),
                "url": f"{prefix}/{collection}/",
            }
        )
    ctx = {
        "site_header": admin_site.site_header,
        "site_title": admin_site.site_title,
        "index_title": admin_site.index_title,
        "models": sorted(models, key=lambda m: m["name"]),
        "prefix": prefix,
    }
    if request is not None:
        ctx.update(build_ui_context(request))
    return ctx


def build_changelist_context(
    request: Request,
    admin_site: AdminSite,
    model_admin: ModelAdmin,
    collection: str,
    prefix: str,
    page_data: dict[str, Any],
    *,
    search: str = "",
    filter_params: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Build changelist template context."""
    filter_params = filter_params or dict(request.query_params)
    list_display = model_admin.get_list_display(request)
    list_links = set(model_admin.get_list_display_links(request))
    columns = []
    for field in list_display:
        columns.append(
            {
                "name": field,
                "label": _column_label(model_admin, field),
                "link": field in list_links,
            }
        )
    filters = []
    str_params = {k: str(v) for k, v in filter_params.items()}
    ui = build_ui_context(request)
    translator: Translator = ui["t"]
    for flt in model_admin.get_list_filters(request, str_params):
        filters.append(
            {
                "title": flt.title or flt.field_name,
                "parameter_name": flt.parameter_name,
                "choices": _translate_filter_choices(flt.choices(), translator),
            }
        )
    rows = []
    for obj in page_data.get("results", []):
        cells = []
        for field in list_display:
            if field == "id" and "id" not in obj and "_id" in obj:
                value = obj["_id"]
            else:
                value = model_admin.display_value(request, obj, field)
                related_key = f"_{field}_related"
                if related_key in obj and obj[related_key]:
                    value = obj[related_key].get("name", value)
            cells.append({"name": field, "value": value})
        doc_id = obj.get("id") or obj.get("_id", "")
        rows.append({"id": str(doc_id), "cells": cells})
    query = urlencode({k: v for k, v in filter_params.items() if k != "page" and v})
    return {
        "site_header": admin_site.site_header,
        "model_name": model_admin.get_model_name(),
        "collection": collection,
        "prefix": prefix,
        "columns": columns,
        "rows": rows,
        "filters": filters,
        "search": search,
        "page": page_data.get("page", 1),
        "num_pages": page_data.get("num_pages", 1),
        "total": page_data.get("total", 0),
        "per_page": page_data.get("per_page", 25),
        "has_add_permission": model_admin.has_add_permission(request),
        "actions": model_admin.get_actions(),
        "query_string": query,
        "list_editable": model_admin.list_editable or [],
        "csrf_token": admin_site.get_csrf_token(request),
        **ui,
    }


def build_form_context(
    request: Request,
    admin_site: AdminSite,
    model_admin: ModelAdmin,
    collection: str,
    prefix: str,
    *,
    obj: dict[str, Any] | None = None,
    is_new: bool = False,
    errors: list[str] | None = None,
) -> dict[str, Any]:
    """Build add/change form context."""
    readonly = set(model_admin.get_readonly_fields(request, obj))
    fields = prepare_form_fields(
        model_admin.model,
        obj=obj,
        readonly_fields=list(readonly),
        choices=model_admin.choices,
        field_overrides=model_admin.get_formfield_overrides(request, obj),
    )
    fields = [
        model_admin.formfield_for_field(admin_field, request, obj) for admin_field in fields
    ]
    fieldsets = []
    for title, options in model_admin.get_fieldsets(request, obj):
        field_names = options.get("fields", [])
        fieldsets.append(
            {
                "title": title,
                "fields": [f for f in fields if f.name in field_names],
            }
        )
    if not fieldsets:
        fieldsets = [{"title": None, "fields": fields}]
    doc_id = ""
    if obj:
        doc_id = str(obj.get("id") or obj.get("_id", ""))
    return {
        "site_header": admin_site.site_header,
        "model_name": model_admin.get_model_name(),
        "collection": collection,
        "prefix": prefix,
        "fieldsets": fieldsets,
        "is_new": is_new,
        "obj_id": doc_id,
        "errors": errors or [],
        "csrf_token": admin_site.get_csrf_token(request),
        **build_ui_context(request),
    }


def _translate_filter_choices(
    choices: list[dict[str, str]],
    translator: Translator,
) -> list[dict[str, str]]:
    """Translate standard filter choice labels."""
    label_map = {
        "All": translator("all"),
        "Yes": translator("yes"),
        "No": translator("no"),
    }
    translated: list[dict[str, str]] = []
    for choice in choices:
        item = dict(choice)
        item["label"] = label_map.get(choice.get("label", ""), choice.get("label", ""))
        translated.append(item)
    return translated


def _column_label(model_admin: ModelAdmin, field_name: str) -> str:
    if hasattr(model_admin, field_name):
        method = getattr(model_admin, field_name)
        if getattr(method, "admin_display", False):
            return getattr(method, "short_description", field_name)
    return field_name.replace("_", " ").title()
