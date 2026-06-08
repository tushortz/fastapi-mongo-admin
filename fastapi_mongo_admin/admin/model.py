"""ModelAdmin base class with Django-admin-style hooks."""

from __future__ import annotations

from typing import Any, Type

from fastapi import Request
from pydantic import BaseModel

from fastapi_mongo_admin.admin.actions import DELETE_SELECTED_ACTION, get_model_actions
from fastapi_mongo_admin.admin.fields.base import AdminField
from fastapi_mongo_admin.admin.fields.widgets import FieldWidget
from fastapi_mongo_admin.admin.filters.base import ListFilter
from fastapi_mongo_admin.admin.filters.registry import resolve_list_filters
from fastapi_mongo_admin.formatting import format_date_display, format_datetime_display
from fastapi_mongo_admin.schemas.inference import _field_type


class ModelAdmin:
    """Configuration and hooks for a registered Pydantic model."""

    model: Type[BaseModel] | None = None
    collection_name: str | None = None
    list_display: list[str] | None = None
    list_display_links: list[str] | None = None
    list_editable: list[str] | None = None
    list_filter: list[str | type[ListFilter]] | None = None
    search_fields: list[str] | None = None
    list_per_page: int = 25
    list_max_show_all: int = 200
    ordering: list[str] | None = None
    date_hierarchy: str | None = None
    list_select_related: dict[str, str] | None = None
    fieldsets: list[tuple[str | None, dict[str, list[str]]]] | None = None
    readonly_fields: list[str] | None = None
    field_mapping: dict[str, str] | None = None
    actions: list[str] | None = None
    choices: dict[str, list[tuple[Any, str]]] | None = None
    formfield_overrides: dict[str, FieldWidget | dict[str, Any]] | None = None
    date_format: str | None = None
    datetime_format: str | None = None

    change_list_template: str = "admin/change_list.html"
    change_form_template: str = "admin/change_form.html"
    delete_confirmation_template: str = "admin/delete_confirmation.html"
    delete_selected_confirmation_template: str = "admin/delete_selected_confirmation.html"

    def __init__(self, model: Type[BaseModel] | None = None) -> None:
        if model is not None:
            self.model = model

    def get_model_name(self) -> str:
        """Return human-readable model name."""
        if self.model is None:
            return self.collection_name or "Model"
        return self.model.__name__

    def get_list_display(self, request: Request | None = None) -> list[str]:
        """Return columns for changelist."""
        if self.list_display:
            return list(self.list_display)
        if self.model is not None:
            return list(self.model.model_fields.keys())[:5]
        return ["_id"]

    def get_list_display_links(self, request: Request | None = None) -> list[str]:
        """Return clickable changelist columns."""
        if self.list_display_links is not None:
            return list(self.list_display_links)
        display = self.get_list_display(request)
        return [display[0]] if display else []

    def get_search_fields(self) -> list[str]:
        """Return searchable field names."""
        return list(self.search_fields or [])

    def get_ordering(self) -> list[str]:
        """Return default ordering (prefix with '-' for descending)."""
        return list(self.ordering or ["-_id"])

    def get_readonly_fields(self, request: Request | None = None, obj: dict[str, Any] | None = None) -> list[str]:
        """Return readonly fields for change form."""
        return list(self.readonly_fields or [])

    def get_formfield_overrides(
        self,
        request: Request | None = None,
        obj: dict[str, Any] | None = None,
    ) -> dict[str, FieldWidget]:
        """Return per-field widget overrides for the change form."""
        overrides = self.formfield_overrides or {}
        return {name: FieldWidget.from_mapping(config) for name, config in overrides.items()}

    def formfield_for_field(
        self,
        field: AdminField,
        request: Request | None = None,
        obj: dict[str, Any] | None = None,
    ) -> AdminField:
        """Hook to customize a single form field after defaults and overrides."""
        return field

    def get_fieldsets(self, request: Request | None = None, obj: dict[str, Any] | None = None) -> list[tuple[str | None, dict[str, list[str]]]]:
        """Return grouped fieldsets for change form."""
        if self.fieldsets:
            return list(self.fieldsets)
        if self.model is None:
            return [(None, {"fields": []})]
        fields = list(self.model.model_fields.keys())
        return [(None, {"fields": fields})]

    def get_list_filters(
        self,
        request: Request | None = None,
        params: dict[str, str] | None = None,
    ) -> list[ListFilter]:
        """Instantiate list filters from configuration."""
        return resolve_list_filters(self, self.list_filter or [], request=request, params=params)

    def get_actions(self) -> list[tuple[str, Any, str]]:
        """Return enabled bulk actions."""
        registered = {name: method for name, method, _ in get_model_actions(self)}
        delete_action = (
            DELETE_SELECTED_ACTION,
            self._delete_selected_action,
            DELETE_SELECTED_ACTION,
        )
        custom = [
            (name, registered[name], getattr(registered[name], "short_description", name))
            for name in registered
        ]
        if self.actions is None:
            return [delete_action, *custom]
        if not self.actions:
            return []
        resolved: list[tuple[str, Any, str]] = []
        for name in self.actions:
            if name == DELETE_SELECTED_ACTION:
                resolved.append(delete_action)
            elif name in registered:
                resolved.append(
                    (name, registered[name], getattr(registered[name], "short_description", name))
                )
        return resolved

    def _delete_selected_action(self, request: Request | None, queryset: list[dict[str, Any]]) -> None:
        """Placeholder for the built-in bulk delete action (handled by the admin router)."""
        _ = request, queryset

    def get_queryset(self, request: Request | None, base_query: dict[str, Any]) -> dict[str, Any]:
        """Hook to customize base MongoDB query."""
        return base_query

    async def save_model(
        self,
        request: Request | None,
        obj: dict[str, Any],
        form_data: dict[str, Any],
        is_new: bool,
    ) -> dict[str, Any]:
        """Hook called before persisting a document."""
        return form_data

    async def delete_model(self, request: Request | None, obj: dict[str, Any]) -> None:
        """Hook called before deleting a document."""

    def has_view_permission(self, request: Request | None, user: Any = None, obj: dict[str, Any] | None = None) -> bool:
        """Return whether user can view."""
        return True

    def has_add_permission(self, request: Request | None, user: Any = None) -> bool:
        """Return whether user can add."""
        return True

    def has_change_permission(self, request: Request | None, user: Any = None, obj: dict[str, Any] | None = None) -> bool:
        """Return whether user can change."""
        return True

    def has_delete_permission(self, request: Request | None, user: Any = None, obj: dict[str, Any] | None = None) -> bool:
        """Return whether user can delete."""
        return True

    def get_urls(self) -> list[tuple[str, Any]]:
        """Return extra (path, handler) pairs relative to model prefix."""
        return []

    def get_date_format(self) -> str | None:
        """Return strftime-style format for date display (default: ``8 Apr 2026``)."""
        return self.date_format

    def get_datetime_format(self) -> str | None:
        """Return strftime-style format for datetime display (default: ``8 Apr 2026, 7:32pm``)."""
        return self.datetime_format

    def format_date_value(self, value: Any) -> str:
        """Format a date value for display."""
        return format_date_display(value, self.get_date_format())

    def format_datetime_value(self, value: Any) -> str:
        """Format a datetime value for display."""
        return format_datetime_display(value, self.get_datetime_format())

    def _field_type_for_name(self, field_name: str) -> str | None:
        """Return inferred field type for a model field name."""
        if self.model is None:
            return None
        field = self.model.model_fields.get(field_name)
        if field is None:
            return None
        return _field_type(field.annotation)

    def format_display_value(self, field_name: str, value: Any) -> Any:
        """Apply date/datetime display formatting when applicable."""
        if value in (None, ""):
            return value
        ftype = self._field_type_for_name(field_name)
        if ftype == "datetime":
            return self.format_datetime_value(value)
        if ftype == "date":
            return self.format_date_value(value)
        return value

    def display_value(self, request: Request | None, obj: dict[str, Any], field_name: str) -> Any:
        """Resolve a list_display value including callables and @display methods."""
        if hasattr(self, field_name) and callable(getattr(self, field_name)):
            method = getattr(self, field_name)
            if getattr(method, "admin_display", False):
                return method(obj)
        if field_name in obj:
            return self.format_display_value(field_name, obj[field_name])
        return ""

    def object_repr(self, request: Request | None, obj: dict[str, Any]) -> str:
        """Return a human-readable label for an object (flash messages, etc.)."""
        for field_name in self.get_list_display_links(request):
            value = self.display_value(request, obj, field_name)
            if value not in (None, ""):
                return str(value)
        for field_name in self.get_list_display(request):
            value = self.display_value(request, obj, field_name)
            if value not in (None, ""):
                return str(value)
        for key in ("name", "title", "slug", "email", "order_number", "code"):
            if obj.get(key) not in (None, ""):
                return str(obj[key])
        doc_id = obj.get("id") or obj.get("_id", "")
        if doc_id:
            return str(doc_id)
        return self.get_model_name()
