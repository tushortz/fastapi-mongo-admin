"""Date and datetime display formatting tests."""

from datetime import date, datetime, timezone

from pydantic import BaseModel

from fastapi_mongo_admin.admin.model import ModelAdmin
from fastapi_mongo_admin.formatting import (
    format_date_display,
    format_datetime_display,
)


def test_default_datetime_format() -> None:
    value = datetime(2026, 4, 8, 19, 32)
    assert format_datetime_display(value) == "8 Apr 2026, 7:32pm"


def test_default_datetime_format_morning() -> None:
    value = datetime(2026, 4, 8, 7, 5)
    assert format_datetime_display(value) == "8 Apr 2026, 7:05am"


def test_default_datetime_format_noon() -> None:
    value = datetime(2026, 4, 8, 12, 0)
    assert format_datetime_display(value) == "8 Apr 2026, 12:00pm"


def test_default_date_format() -> None:
    assert format_date_display(date(2026, 4, 8)) == "8 Apr 2026"


def test_datetime_from_iso_string() -> None:
    assert format_datetime_display("2026-04-08T19:32:00") == "8 Apr 2026, 7:32pm"


def test_custom_strftime_format() -> None:
    value = datetime(2026, 4, 8, 19, 32)
    assert format_datetime_display(value, "%Y-%m-%d %H:%M") == "2026-04-08 19:32"


class Event(BaseModel):
    name: str
    starts_at: datetime
    event_date: date


class EventAdmin(ModelAdmin):
    model = Event
    collection_name = "events"
    list_display = ["name", "starts_at", "event_date"]


def test_model_admin_display_value_formats_dates() -> None:
    admin = EventAdmin()
    obj = {
        "name": "Launch",
        "starts_at": "2026-04-08T19:32:00",
        "event_date": "2026-04-08",
    }
    assert admin.display_value(None, obj, "starts_at") == "8 Apr 2026, 7:32pm"
    assert admin.display_value(None, obj, "event_date") == "8 Apr 2026"


def test_model_admin_custom_datetime_format() -> None:
    class CustomAdmin(EventAdmin):
        datetime_format = "%d/%m/%Y %H:%M"

    admin = CustomAdmin()
    obj = {"starts_at": datetime(2026, 4, 8, 19, 32, tzinfo=timezone.utc)}
    assert admin.display_value(None, obj, "starts_at") == "08/04/2026 19:32"
