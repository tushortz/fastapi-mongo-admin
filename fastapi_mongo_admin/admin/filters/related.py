"""Related field list filter for ObjectId references."""

from __future__ import annotations

from typing import Any

from bson import ObjectId
from bson.errors import InvalidId

from fastapi_mongo_admin.admin.filters.base import ListFilter


class RelatedFieldListFilter(ListFilter):
    """Filter by related document ObjectId."""

    related_collection: str = ""
    related_field: str = "_id"
    display_field: str = "name"

    def lookups(self) -> list[tuple[str, str]]:
        return []

    def queryset(self, value: str) -> dict[str, Any]:
        if not value:
            return {}
        db_field = self.db_field()
        try:
            oid = ObjectId(value)
            return {db_field: oid}
        except (InvalidId, TypeError):
            return {db_field: value}
