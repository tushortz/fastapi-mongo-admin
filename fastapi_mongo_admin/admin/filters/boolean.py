"""Boolean list filter."""

from __future__ import annotations

from typing import Any

from fastapi_mongo_admin.admin.filters.base import ListFilter


class BooleanFieldListFilter(ListFilter):
    """Filter boolean fields with Yes/No choices."""

    title: str = ""

    def lookups(self) -> list[tuple[str, str]]:
        """Return Yes/No filter choices.

        Returns:
            List of ``(value, label)`` tuples.
        """
        return [("1", "Yes"), ("0", "No")]

    def queryset(self, value: str) -> dict[str, Any]:
        """Return a boolean equality filter.

        Args:
            value: Selected filter value (``1``/``0`` or truthy strings).

        Returns:
            MongoDB filter dict keyed by the database field.
        """
        if not value:
            return {}
        db_field = self.db_field()
        return {db_field: value in ("1", "true", "True", "yes")}
