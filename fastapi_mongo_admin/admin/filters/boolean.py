"""Boolean list filter."""

from __future__ import annotations

from typing import Any

from fastapi_mongo_admin.admin.filters.base import ListFilter


class BooleanFieldListFilter(ListFilter):
    """Filter boolean fields."""

    title = "By boolean"

    def lookups(self) -> list[tuple[str, str]]:
        return [("1", "Yes"), ("0", "No")]

    def queryset(self, value: str) -> dict[str, Any]:
        if not value:
            return {}
        db_field = self.db_field()
        return {db_field: value in ("1", "true", "True", "yes")}
