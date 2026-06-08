"""Base list filter classes."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from fastapi import Request

if TYPE_CHECKING:
    from fastapi_mongo_admin.admin.model import ModelAdmin


class ListFilter:
    """Base class for changelist sidebar filters."""

    title: str = ""
    parameter_name: str = ""

    def __init__(
        self,
        request: Request | None,
        params: dict[str, str],
        model_admin: ModelAdmin,
        field_name: str,
    ) -> None:
        self.request = request
        self.params = params
        self.model_admin = model_admin
        self.field_name = field_name
        self.parameter_name = field_name

    def lookups(self) -> list[tuple[str, str]]:
        """Return (value, label) choices."""
        return []

    def queryset(self, value: str) -> dict[str, Any]:
        """Return MongoDB filter fragment for selected value."""
        if not value:
            return {}
        return {self.field_name: value}

    def choices(self) -> list[dict[str, str]]:
        """Return choices including 'All'."""
        current = self.params.get(self.parameter_name, "")
        items = [{"value": "", "label": "All", "selected": current == ""}]
        for value, label in self.lookups():
            items.append(
                {"value": value, "label": label, "selected": current == value}
            )
        return items

    def db_field(self) -> str:
        """Map model field to database field."""
        mapping = self.model_admin.field_mapping or {}
        return mapping.get(self.field_name, self.field_name)
