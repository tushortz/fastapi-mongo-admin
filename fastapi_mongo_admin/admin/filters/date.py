"""Date list filter and date hierarchy."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi_mongo_admin.admin.filters.base import ListFilter


class DateFieldListFilter(ListFilter):
    """Filter documents by common date ranges."""

    title: str = ""

    def lookups(self) -> list[tuple[str, str]]:
        """Return preset date range choices.

        Returns:
            List of ``(value, label)`` tuples.
        """
        return [
            ("today", "Today"),
            ("past_7_days", "Past 7 days"),
            ("this_month", "This month"),
            ("this_year", "This year"),
        ]

    def queryset(self, value: str) -> dict[str, Any]:
        """Return a date range filter for the selected preset.

        Args:
            value: Preset key (``today``, ``past_7_days``, etc.).

        Returns:
            MongoDB range filter dict keyed by the database field.
        """
        if not value:
            return {}
        now = datetime.now(timezone.utc)
        db_field = self.db_field()
        if value == "today":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            return {db_field: {"$gte": start, "$lt": start + timedelta(days=1)}}
        if value == "past_7_days":
            return {db_field: {"$gte": now - timedelta(days=7)}}
        if value == "this_month":
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            return {db_field: {"$gte": start}}
        if value == "this_year":
            start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            return {db_field: {"$gte": start}}
        return {}


def build_date_hierarchy_query(
    field: str, year: str | None, month: str | None, day: str | None
) -> dict[str, Any]:
    """Build a date hierarchy drill-down query.

    Args:
        field: Database date/datetime field name.
        year: Selected year string.
        month: Selected month string.
        day: Selected day string.

    Returns:
        MongoDB range filter for the selected hierarchy level.
    """
    if not year:
        return {}
    y = int(year)
    if not month:
        start = datetime(y, 1, 1, tzinfo=timezone.utc)
        end = datetime(y + 1, 1, 1, tzinfo=timezone.utc)
        return {field: {"$gte": start, "$lt": end}}
    m = int(month)
    if not day:
        if m == 12:
            end = datetime(y + 1, 1, 1, tzinfo=timezone.utc)
        else:
            end = datetime(y, m + 1, 1, tzinfo=timezone.utc)
        start = datetime(y, m, 1, tzinfo=timezone.utc)
        return {field: {"$gte": start, "$lt": end}}
    d = int(day)
    start = datetime(y, m, d, tzinfo=timezone.utc)
    end = start + timedelta(days=1)
    return {field: {"$gte": start, "$lt": end}}
