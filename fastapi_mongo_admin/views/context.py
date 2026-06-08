"""Template context builders."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

from fastapi import Request

from fastapi_mongo_admin.admin.fields.base import AdminField
from fastapi_mongo_admin.admin.fields.widgets import RELATED_SELECT
from fastapi_mongo_admin.services.repository import RELATED_LOOKUP_MIN_CHARS
from fastapi_mongo_admin.admin.model import ModelAdmin
from fastapi_mongo_admin.admin.site import AdminSite
from fastapi_mongo_admin.i18n import Translator
from fastapi_mongo_admin.schemas.inference import prepare_form_fields
from fastapi_mongo_admin.services.repository import related_object_label
from fastapi_mongo_admin.views.messages import resolve_flash_message
from fastapi_mongo_admin.views.preferences import build_ui_context


def build_index_context(
    admin_site: AdminSite,
    prefix: str,
    request: Request | None = None,
) -> dict[str, Any]:
    """Build admin index page template context.

    Args:
        admin_site: Admin site registry.
        prefix: Admin URL prefix.
        request: Optional current request for UI preferences.

    Returns:
        Template context dict for ``admin/index.html``.
    """
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
    import_errors: list[str] | None = None,
    data_transfer_open: bool = False,
) -> dict[str, Any]:
    """Build changelist template context.

    Args:
        request: Current HTTP request.
        admin_site: Admin site registry.
        model_admin: ModelAdmin for the collection.
        collection: MongoDB collection name.
        prefix: Admin URL prefix.
        page_data: Paginated list data from the repository.
        search: Active search query string.
        filter_params: Active filter query parameters.
        import_errors: Import validation errors for the data transfer panel.
        data_transfer_open: Whether the data transfer drawer should open on load.

    Returns:
        Template context dict for the changelist or result partial.
    """
    filter_params = filter_params or dict(request.query_params)
    str_params = {k: str(v) for k, v in filter_params.items()}
    list_display = model_admin.get_list_display(request)
    list_links = set(model_admin.get_list_display_links(request))
    current_order = str_params.get("o", "")
    columns = []
    for field in list_display:
        sortable = model_admin.get_sortable_field(field) is not None
        sort_asc = current_order == field
        sort_desc = current_order == f"-{field}"
        if sort_asc:
            next_order = f"-{field}"
        elif sort_desc:
            next_order = field
        else:
            next_order = field
        sort_params = {k: v for k, v in str_params.items() if k not in ("page", "o") and v}
        if sortable:
            sort_params["o"] = next_order
        columns.append(
            {
                "name": field,
                "label": _column_label(model_admin, field),
                "link": field in list_links,
                "sortable": sortable,
                "sort_asc": sort_asc,
                "sort_desc": sort_desc,
                "sort_url": f"?{urlencode(sort_params)}" if sortable else "",
            }
        )
    filters = []
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
                    value = related_object_label(obj[related_key])
            cells.append({"name": field, "value": value})
        doc_id = obj.get("id") or obj.get("_id", "")
        rows.append({"id": str(doc_id), "cells": cells})
    query = urlencode({k: v for k, v in filter_params.items() if k != "page" and v})
    success_message, _had_flash = resolve_flash_message(request, translator)
    imported = str_params.get("imported", "")
    if not success_message and imported.isdigit() and int(imported) > 0:
        success_message = translator(
            "imported_success",
            count=int(imported),
            model=model_admin.get_model_name(),
        )
    has_active_filters = any(
        choice.get("selected") and choice.get("value")
        for flt in filters
        for choice in flt["choices"]
    )
    can_import = model_admin.has_add_permission(request)
    can_export = model_admin.has_view_permission(request)
    data_formats = _data_transfer_formats(translator)
    return {
        "site_header": admin_site.site_header,
        "model_name": model_admin.get_model_name(),
        "model_name_plural": model_admin.get_model_name_plural(),
        "collection": collection,
        "prefix": prefix,
        "columns": columns,
        "rows": rows,
        "filters": filters,
        "search": search,
        "has_search": bool(model_admin.get_search_fields()),
        "page": page_data.get("page", 1),
        "num_pages": page_data.get("num_pages", 1),
        "total": page_data.get("total", 0),
        "per_page": page_data.get("per_page", 25),
        "has_add_permission": model_admin.has_add_permission(request),
        "actions": _translate_actions(model_admin.get_actions(), translator),
        "query_string": query,
        "list_editable": model_admin.list_editable or [],
        "csrf_token": admin_site.get_csrf_token(request),
        "success_message": success_message,
        "has_active_filters": has_active_filters,
        "can_import": can_import,
        "can_export": can_export,
        "has_data_transfer": can_import or can_export,
        "data_formats": data_formats,
        "import_errors": import_errors or [],
        "data_transfer_open": data_transfer_open,
        **ui,
    }


def build_bulk_delete_context(
    request: Request,
    admin_site: AdminSite,
    model_admin: ModelAdmin,
    collection: str,
    prefix: str,
    *,
    selected_ids: list[str],
    objects: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build bulk delete confirmation template context.

    Args:
        request: Current HTTP request.
        admin_site: Admin site registry.
        model_admin: ModelAdmin for the collection.
        collection: MongoDB collection name.
        prefix: Admin URL prefix.
        selected_ids: Selected document id strings.
        objects: Selected document dicts.

    Returns:
        Template context dict for bulk delete confirmation.
    """
    list_display = model_admin.get_list_display(request)
    label_field = list_display[0] if list_display else "id"
    rows = []
    for obj in objects:
        doc_id = str(obj.get("id") or obj.get("_id", ""))
        rows.append(
            {
                "id": doc_id,
                "label": model_admin.display_value(request, obj, label_field) or doc_id,
            }
        )
    ui = build_ui_context(request)
    translator: Translator = ui["t"]
    return {
        "site_header": admin_site.site_header,
        "model_name": model_admin.get_model_name(),
        "model_name_plural": model_admin.get_model_name_plural(),
        "collection": collection,
        "prefix": prefix,
        "selected_ids": selected_ids,
        "rows": rows,
        "selected_count": len(selected_ids),
        "csrf_token": admin_site.get_csrf_token(request),
        **ui,
        "bulk_delete_message": translator(
            "bulk_delete_confirm_msg",
            model=model_admin.get_model_name(),
            count=len(selected_ids),
        ),
    }


def _apply_related_form_fields(
    fields: list[AdminField],
    model_admin: ModelAdmin,
    collection: str,
    prefix: str,
    related_initial: dict[str, tuple[Any, str]] | None,
) -> None:
    """Configure searchable related selects for ``list_select_related`` fields."""
    related = model_admin.list_select_related or {}
    if not related:
        return
    admin_choices = model_admin.choices or {}
    for admin_field in fields:
        if admin_field.name not in related or admin_field.name in admin_choices:
            continue
        admin_field.widget = RELATED_SELECT
        admin_field.choices = []
        if related_initial and admin_field.name in related_initial:
            admin_field.choices = [related_initial[admin_field.name]]
        admin_field.attrs["data-related-lookup"] = (
            f"{prefix}/{collection}/related-lookup/{admin_field.name}/"
        )
        admin_field.attrs["data-min-chars"] = str(RELATED_LOOKUP_MIN_CHARS)


def _build_form_fieldsets(
    model_admin: ModelAdmin,
    request: Request | None,
    obj: dict[str, Any] | None,
    fields: list[AdminField],
    *,
    readonly_section_title: str,
) -> list[dict[str, Any]]:
    """Build form fieldsets with readonly fields grouped at the bottom."""
    fields_by_name = {field.name: field for field in fields}
    readonly_fields: list[AdminField] = []
    assigned_readonly: set[str] = set()
    fieldsets: list[dict[str, Any]] = []

    def _collect_readonly(field: AdminField) -> None:
        if field.name not in assigned_readonly:
            readonly_fields.append(field)
            assigned_readonly.add(field.name)

    configured = model_admin.get_fieldsets(request, obj)
    if configured:
        for title, options in configured:
            editable_fields: list[AdminField] = []
            for name in options.get("fields", []):
                field = fields_by_name.get(name)
                if field is None:
                    continue
                if field.readonly:
                    _collect_readonly(field)
                else:
                    editable_fields.append(field)
            if editable_fields:
                fieldsets.append({"title": title, "fields": editable_fields})
    else:
        editable_fields = [field for field in fields if not field.readonly]
        if editable_fields:
            fieldsets.append({"title": None, "fields": editable_fields})

    for field in fields:
        if field.readonly:
            _collect_readonly(field)

    if readonly_fields:
        fieldsets.append({"title": readonly_section_title, "fields": readonly_fields})
    return fieldsets


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
    related_initial: dict[str, tuple[Any, str]] | None = None,
) -> dict[str, Any]:
    """Build add/change form template context.

    Args:
        request: Current HTTP request.
        admin_site: Admin site registry.
        model_admin: ModelAdmin for the collection.
        collection: MongoDB collection name.
        prefix: Admin URL prefix.
        obj: Existing document for edit forms.
        is_new: Whether this is an add form.
        errors: Validation error messages to display.
        related_initial: Current value labels for ``list_select_related`` fields.

    Returns:
        Template context dict for add/change forms.
    """
    readonly = set(model_admin.get_readonly_fields(request, obj))
    fields = prepare_form_fields(
        model_admin.model,
        obj=obj,
        readonly_fields=list(readonly),
        choices=model_admin.choices,
        field_overrides=model_admin.get_formfield_overrides(request, obj),
        display_formatter=model_admin,
    )
    _apply_related_form_fields(fields, model_admin, collection, prefix, related_initial)
    fields = [model_admin.formfield_for_field(admin_field, request, obj) for admin_field in fields]
    ui = build_ui_context(request)
    fieldsets = _build_form_fieldsets(
        model_admin,
        request,
        obj,
        fields,
        readonly_section_title=ui["t"]("readonly_section"),
    )
    doc_id = ""
    if obj:
        doc_id = str(obj.get("id") or obj.get("_id", ""))
    return {
        "site_header": admin_site.site_header,
        "model_name": model_admin.get_model_name(),
        "model_name_plural": model_admin.get_model_name_plural(),
        "collection": collection,
        "prefix": prefix,
        "fieldsets": fieldsets,
        "is_new": is_new,
        "obj_id": doc_id,
        "errors": errors or [],
        "csrf_token": admin_site.get_csrf_token(request),
        **ui,
    }


def _translate_actions(
    actions: list[tuple[str, Any, str]],
    translator: Translator,
) -> list[tuple[str, Any, str]]:
    """Translate built-in bulk action labels.

    Args:
        actions: Action tuples from ``ModelAdmin.get_actions()``.
        translator: Active UI translator.

    Returns:
        Actions with translated labels.
    """
    from fastapi_mongo_admin.admin.actions import DELETE_SELECTED_ACTION

    label_map = {
        DELETE_SELECTED_ACTION: translator("delete_selected"),
    }
    translated: list[tuple[str, Any, str]] = []
    for name, method, label in actions:
        translated.append((name, method, label_map.get(name, label)))
    return translated


def _data_transfer_formats(translator: Translator) -> list[dict[str, str]]:
    """Return supported import/export format options for the UI."""
    return [
        {"value": "json", "label": translator("format_json")},
        {"value": "csv", "label": translator("format_csv")},
        {"value": "yaml", "label": translator("format_yaml")},
        {"value": "toml", "label": translator("format_toml")},
        {"value": "excel", "label": translator("format_excel")},
    ]


def _translate_filter_choices(
    choices: list[dict[str, str]],
    translator: Translator,
) -> list[dict[str, str]]:
    """Translate standard filter choice labels.

    Args:
        choices: Filter choice dicts from ``ListFilter.choices()``.
        translator: Active UI translator.

    Returns:
        Choices with translated ``All``/``Yes``/``No`` labels.
    """
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
    """Resolve the changelist column heading for a field.

    Args:
        model_admin: ModelAdmin providing ``@display`` methods.
        field_name: Column field name.

    Returns:
        Human-readable column label.
    """
    if hasattr(model_admin, field_name):
        method = getattr(model_admin, field_name)
        if getattr(method, "admin_display", False):
            return getattr(method, "short_description", field_name)
    return field_name.replace("_", " ").title()
