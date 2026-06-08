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
        """Initialize a list filter instance.

        Args:
            request: Current HTTP request.
            params: Active query parameters.
            model_admin: Parent ModelAdmin configuration.
            field_name: Model field this filter applies to.
        """
        self.request = request
        self.params = params
        self.model_admin = model_admin
        self.field_name = field_name
        self.parameter_name = field_name

    def lookups(self) -> list[tuple[str, str]]:
        """Return filter choice values and labels.

        Returns:
            List of ``(value, label)`` tuples excluding the "All" option.
        """
        return []

    def queryset(self, value: str) -> dict[str, Any]:
        """Return a MongoDB filter fragment for the selected value.

        Args:
            value: Selected filter value from the query string.

        Returns:
            MongoDB filter dict, or empty dict when no filter applies.
        """
        if not value:
            return {}
        return {self.field_name: value}

    def choices(self) -> list[dict[str, str]]:
        """Return sidebar choices including an "All" option.

        Returns:
            List of choice dicts with ``value``, ``label``, and ``selected`` keys.
        """
        current = self.params.get(self.parameter_name, "")
        items = [{"value": "", "label": "All", "selected": current == ""}]
        for value, label in self.lookups():
            items.append({"value": value, "label": label, "selected": current == value})
        return items

    def db_field(self) -> str:
        """Map the model field name to the database field name.

        Returns:
            Database field name after applying ``field_mapping``.
        """
        mapping = self.model_admin.field_mapping or {}
        return mapping.get(self.field_name, self.field_name)
