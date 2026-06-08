"""ModelAdmin base class with Django-admin-style hooks."""

from __future__ import annotations

from typing import Any, Type

from fastapi import Request
from pydantic import BaseModel

from fastapi_mongo_admin.admin.actions import (
    BUILTIN_ACTIONS,
    DELETE_SELECTED_ACTION,
    get_model_actions,
)
from fastapi_mongo_admin.admin.fields.base import AdminField
from fastapi_mongo_admin.admin.fields.widgets import FieldWidget
from fastapi_mongo_admin.admin.filters.base import ListFilter
from fastapi_mongo_admin.admin.filters.registry import resolve_list_filters
from fastapi_mongo_admin.formatting import format_date_display, format_datetime_display
from fastapi_mongo_admin.schemas.inference import _field_type


def _pluralize_label(label: str) -> str:
    """Pluralize a short English model label.

    Args:
        label: Singular model name.

    Returns:
        Pluralized label for display strings.
    """
    if not label:
        return label
    lower = label.lower()
    if lower.endswith(("s", "x", "z", "ch", "sh")):
        return f"{label}es"
    if len(label) > 1 and label.endswith("y") and label[-2].lower() not in "aeiou":
        return f"{label[:-1]}ies"
    return f"{label}s"


class ModelAdmin:
    """Configuration and hooks for a registered Pydantic model.

    Subclass to customize changelist columns, filters, forms, permissions,
    and document lifecycle behavior.
    """

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
        """Initialize ModelAdmin, optionally binding a Pydantic model.

        Args:
            model: Pydantic model class for validation and form inference.
        """
        if model is not None:
            self.model = model

    def get_model_name(self) -> str:
        """Return the human-readable model name.

        Returns:
            Model class name, or ``collection_name`` when no model is set.
        """
        if self.model is None:
            return self.collection_name or "Model"
        return self.model.__name__

    def get_model_name_plural(self) -> str:
        """Return the plural human-readable model name.

        Returns:
            Pluralized model label for result counts and bulk messages.
        """
        return _pluralize_label(self.get_model_name())

    def get_list_display(self, request: Request | None = None) -> list[str]:
        """Return changelist column field names.

        Args:
            request: Current HTTP request (unused by default).

        Returns:
            Column names from ``list_display``, model fields, or ``["_id"]``.
        """
        if self.list_display:
            return list(self.list_display)
        if self.model is not None:
            return list(self.model.model_fields.keys())[:5]
        return ["_id"]

    def get_list_display_links(self, request: Request | None = None) -> list[str]:
        """Return changelist columns that link to the change form.

        Args:
            request: Current HTTP request (unused by default).

        Returns:
            Clickable column names; defaults to the first list display column.
        """
        if self.list_display_links is not None:
            return list(self.list_display_links)
        display = self.get_list_display(request)
        return [display[0]] if display else []

    def get_search_fields(self) -> list[str]:
        """Return searchable model field names.

        Returns:
            Field names from ``search_fields``, or an empty list.
        """
        return list(self.search_fields or [])

    def get_ordering(self) -> list[str]:
        """Return default changelist ordering.

        Returns:
            Ordering list; prefix fields with ``-`` for descending.
            Defaults to ``["-_id"]``.
        """
        return list(self.ordering or ["-_id"])

    def get_sortable_field(self, column_name: str) -> str | None:
        """Return the database field used to sort a changelist column.

        Args:
            column_name: ``list_display`` column or ``@display`` method name.

        Returns:
            Sortable model field name, or ``None`` when the column is not sortable.
        """
        if hasattr(self, column_name) and callable(getattr(self, column_name)):
            method = getattr(self, column_name)
            if getattr(method, "admin_display", False):
                order_field = getattr(method, "admin_order_field", None)
                return str(order_field) if order_field else None
        if self.model is not None and column_name in self.model.model_fields:
            return column_name
        return None

    def get_readonly_fields(
        self, request: Request | None = None, obj: dict[str, Any] | None = None
    ) -> list[str]:
        """Return readonly form field names.

        Args:
            request: Current HTTP request.
            obj: Existing document on change forms.

        Returns:
            Readonly field names from ``readonly_fields``.
        """
        return list(self.readonly_fields or [])

    def get_formfield_overrides(
        self,
        request: Request | None = None,
        obj: dict[str, Any] | None = None,
    ) -> dict[str, FieldWidget]:
        """Return per-field widget overrides for the change form.

        Args:
            request: Current HTTP request.
            obj: Existing document on change forms.

        Returns:
            Mapping of field name to ``FieldWidget`` instances.
        """
        overrides = self.formfield_overrides or {}
        return {name: FieldWidget.from_mapping(config) for name, config in overrides.items()}

    def formfield_for_field(
        self,
        field: AdminField,
        request: Request | None = None,
        obj: dict[str, Any] | None = None,
    ) -> AdminField:
        """Customize a single form field after defaults and overrides.

        Args:
            field: ``AdminField`` metadata to customize.
            request: Current HTTP request.
            obj: Existing document on change forms.

        Returns:
            Modified ``AdminField`` (default implementation returns unchanged).
        """
        return field

    def get_fieldsets(
        self, request: Request | None = None, obj: dict[str, Any] | None = None
    ) -> list[tuple[str | None, dict[str, list[str]]]]:
        """Return grouped fieldsets for the change form.

        Args:
            request: Current HTTP request.
            obj: Existing document on change forms.

        Returns:
            List of ``(title, {"fields": [...]})`` tuples.
        """
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
        """Instantiate sidebar list filters from configuration.

        Args:
            request: Current HTTP request.
            params: Active query parameters.

        Returns:
            Initialized ``ListFilter`` instances.
        """
        return resolve_list_filters(self, self.list_filter or [], request=request, params=params)

    def get_actions(self) -> list[tuple[str, Any, str]]:
        """Return enabled bulk actions for the changelist.

        Returns:
            List of ``(name, method, label)`` tuples. ``delete_selected`` is
            always included first.
        """
        registered = {name: method for name, method, _ in get_model_actions(self)}
        builtin = [
            (DELETE_SELECTED_ACTION, self._delete_selected_action, DELETE_SELECTED_ACTION),
        ]
        if self.actions is None:
            custom_names = list(registered.keys())
        else:
            custom_names = [
                name
                for name in self.actions
                if name not in BUILTIN_ACTIONS and name in registered
            ]
        custom = [
            (name, registered[name], getattr(registered[name], "short_description", name))
            for name in custom_names
        ]
        return [*builtin, *custom]

    def _delete_selected_action(
        self, request: Request | None, queryset: list[dict[str, Any]]
    ) -> None:
        """Placeholder for the built-in bulk delete action.

        Args:
            request: Current HTTP request.
            queryset: Selected documents (handled by the admin router).

        Returns:
            None.
        """
        _ = request, queryset

    def get_queryset(self, request: Request | None, base_query: dict[str, Any]) -> dict[str, Any]:
        """Customize the base MongoDB query for changelist operations.

        Args:
            request: Current HTTP request.
            base_query: Starting query dict (usually empty).

        Returns:
            Modified base query merged with filters and search.
        """
        return base_query

    async def save_model(
        self,
        request: Request | None,
        obj: dict[str, Any],
        form_data: dict[str, Any],
        is_new: bool,
    ) -> dict[str, Any]:
        """Hook called before persisting a document.

        Args:
            request: Current HTTP request.
            obj: Existing document dict (empty on create).
            form_data: Validated form data to persist.
            is_new: Whether this is a new document.

        Returns:
            Data dict to write to MongoDB.
        """
        return form_data

    async def delete_model(self, request: Request | None, obj: dict[str, Any]) -> None:
        """Hook called before deleting a document.

        Args:
            request: Current HTTP request.
            obj: Document dict about to be deleted.

        Returns:
            None.
        """

    def has_view_permission(
        self, request: Request | None, user: Any = None, obj: dict[str, Any] | None = None
    ) -> bool:
        """Return whether the user can view the changelist and detail pages.

        Args:
            request: Current HTTP request.
            user: Authenticated user from ``auth_dependency``.
            obj: Optional document for object-level checks.

        Returns:
            ``True`` by default.
        """
        return True

    def has_add_permission(self, request: Request | None, user: Any = None) -> bool:
        """Return whether the user can add documents.

        Args:
            request: Current HTTP request.
            user: Authenticated user from ``auth_dependency``.

        Returns:
            ``True`` by default.
        """
        return True

    def has_change_permission(
        self, request: Request | None, user: Any = None, obj: dict[str, Any] | None = None
    ) -> bool:
        """Return whether the user can change documents.

        Args:
            request: Current HTTP request.
            user: Authenticated user from ``auth_dependency``.
            obj: Optional document for object-level checks.

        Returns:
            ``True`` by default.
        """
        return True

    def has_delete_permission(
        self, request: Request | None, user: Any = None, obj: dict[str, Any] | None = None
    ) -> bool:
        """Return whether the user can delete documents.

        Args:
            request: Current HTTP request.
            user: Authenticated user from ``auth_dependency``.
            obj: Optional document for object-level checks.

        Returns:
            ``True`` by default.
        """
        return True

    def get_urls(self) -> list[tuple[str, Any]]:
        """Return extra ``(path, handler)`` pairs under the model URL prefix.

        Returns:
            List of relative path/handler pairs for custom model views.
        """
        return []

    def get_date_format(self) -> str | None:
        """Return the strftime-style format for date display.

        Returns:
            Custom format string, or ``None`` for the default ``8 Apr 2026``.
        """
        return self.date_format

    def get_datetime_format(self) -> str | None:
        """Return the strftime-style format for datetime display.

        Returns:
            Custom format string, or ``None`` for the default ``8 Apr 2026, 7:32pm``.
        """
        return self.datetime_format

    def format_date_value(self, value: Any) -> str:
        """Format a date value for changelist and readonly display.

        Args:
            value: Raw date value.

        Returns:
            Formatted date string.
        """
        return format_date_display(value, self.get_date_format())

    def format_datetime_value(self, value: Any) -> str:
        """Format a datetime value for changelist and readonly display.

        Args:
            value: Raw datetime value.

        Returns:
            Formatted datetime string.
        """
        return format_datetime_display(value, self.get_datetime_format())

    def _field_type_for_name(self, field_name: str) -> str | None:
        """Return the inferred admin field type for a model field.

        Args:
            field_name: Model field name.

        Returns:
            Admin field type string, or ``None`` when unknown.
        """
        if self.model is None:
            return None
        field = self.model.model_fields.get(field_name)
        if field is None:
            return None
        return _field_type(field.annotation)

    def boolean_display_cell(
        self,
        field_name: str,
        obj: dict[str, Any],
        *,
        true_label: str,
        false_label: str,
    ) -> dict[str, Any] | None:
        """Return colored-label metadata for a boolean changelist cell.

        Args:
            field_name: Model field name.
            obj: Row document dict.
            true_label: Localized label for ``True``.
            false_label: Localized label for ``False``.

        Returns:
            Dict with ``boolean`` and ``label`` keys, or ``None`` when not boolean.
        """
        if field_name not in obj or self._field_type_for_name(field_name) != "bool":
            return None
        raw = obj[field_name]
        if not isinstance(raw, bool):
            return None
        return {
            "boolean": raw,
            "label": true_label if raw else false_label,
        }

    def format_display_value(self, field_name: str, value: Any) -> Any:
        """Apply date/datetime display formatting when applicable.

        Args:
            field_name: Model field name.
            value: Raw field value.

        Returns:
            Formatted value for display.
        """
        if value in (None, ""):
            return value
        ftype = self._field_type_for_name(field_name)
        if ftype == "datetime":
            return self.format_datetime_value(value)
        if ftype == "date":
            return self.format_date_value(value)
        return value

    def display_value(self, request: Request | None, obj: dict[str, Any], field_name: str) -> Any:
        """Resolve a changelist cell value including ``@display`` methods.

        Args:
            request: Current HTTP request.
            obj: Row document dict.
            field_name: Column field name.

        Returns:
            Display value for the cell.
        """
        if hasattr(self, field_name) and callable(getattr(self, field_name)):
            method = getattr(self, field_name)
            if getattr(method, "admin_display", False):
                return method(obj)
        if field_name in obj:
            return self.format_display_value(field_name, obj[field_name])
        return ""

    def object_repr(self, request: Request | None, obj: dict[str, Any]) -> str:
        """Return a human-readable label for flash messages and confirmations.

        Args:
            request: Current HTTP request.
            obj: Document dict.

        Returns:
            Best-effort human-readable object label.
        """
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
