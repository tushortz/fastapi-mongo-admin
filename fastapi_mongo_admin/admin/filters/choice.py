"""Choice list filter."""

from __future__ import annotations

from typing import Any

from fastapi_mongo_admin.admin.filters.base import ListFilter


class ChoiceListFilter(ListFilter):
    """Filter by discrete choice values."""

    title: str = ""

    def lookups(self) -> list[tuple[str, str]]:
        choices = (self.model_admin.choices or {}).get(self.field_name, [])
        if choices:
            return [(str(v), str(label)) for v, label in choices]
        if self.model_admin.model is not None:
            field = self.model_admin.model.model_fields.get(self.field_name)
            if field is not None:
                metadata = getattr(field, "json_schema_extra", None) or {}
                if isinstance(metadata, dict) and "choices" in metadata:
                    return [(str(val), str(label)) for val, label in metadata["choices"]]
        return []

    def queryset(self, value: str) -> dict[str, Any]:
        if not value:
            return {}
        db_field = self.db_field()
        return {db_field: value}
