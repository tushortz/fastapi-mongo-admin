"""Schema inference and widget tests."""

from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel

from fastapi_mongo_admin.schemas.inference import (
    format_field_value,
    infer_admin_fields,
    infer_schema_dict,
    prepare_form_fields,
)
from tests.conftest import Product


class Status(str, Enum):
    ACTIVE = "active"
    DRAFT = "draft"


class WidgetModel(BaseModel):
    name: str
    count: int
    price: float
    amount: Decimal
    is_active: bool
    born_on: date
    created_at: datetime
    status: Status
    tier: Literal["bronze", "silver", "gold"]
    optional_status: Optional[Status] = None


def test_infer_admin_fields() -> None:
    fields = infer_admin_fields(Product)
    names = [f.name for f in fields]
    assert "name" in names
    assert "price" in names


def test_infer_schema_dict() -> None:
    schema = infer_schema_dict(Product)
    assert schema["model"] == "Product"
    assert "name" in schema["fields"]


def test_widget_mapping() -> None:
    fields = {f.name: f for f in infer_admin_fields(WidgetModel)}
    assert fields["count"].widget == "number"
    assert fields["count"].step == "1"
    assert fields["price"].widget == "number"
    assert fields["price"].step == "0.01"
    assert fields["amount"].step == "0.01"
    assert fields["is_active"].widget == "checkbox"
    assert fields["born_on"].widget == "date"
    assert fields["created_at"].widget == "datetime-local"
    assert fields["status"].widget == "select"
    assert len(fields["status"].choices) == 2
    assert fields["tier"].widget == "select"
    assert fields["tier"].choices == [("bronze", "bronze"), ("silver", "silver"), ("gold", "gold")]


def test_model_admin_choices_override() -> None:
    fields = infer_admin_fields(
        WidgetModel,
        choices={"tier": [("b", "Bronze"), ("s", "Silver")]},
    )
    tier = next(f for f in fields if f.name == "tier")
    assert tier.widget == "select"
    assert tier.choices == [("b", "Bronze"), ("s", "Silver")]


def test_format_field_value() -> None:
    fields = infer_admin_fields(WidgetModel)
    by_name = {f.name: f for f in fields}

    by_name["born_on"].value = date(2024, 3, 15)
    assert format_field_value(by_name["born_on"]) == "2024-03-15"

    by_name["created_at"].value = datetime(2024, 3, 15, 14, 30, tzinfo=timezone.utc)
    assert format_field_value(by_name["created_at"]) == "2024-03-15T14:30"

    by_name["price"].value = 19.5
    assert format_field_value(by_name["price"]) == "19.50"

    by_name["count"].value = 7
    assert format_field_value(by_name["count"]) == "7"

    by_name["is_active"].value = "true"
    assert format_field_value(by_name["is_active"]) is True


def test_optional_union_syntax_date_and_datetime() -> None:
    """Fields using `date | None` / `datetime | None` must resolve correct widgets."""

    class UnionModel(BaseModel):
        born_on: date | None = None
        created_at: datetime | None = None
        price: Decimal | None = None

    fields = {f.name: f for f in infer_admin_fields(UnionModel)}
    assert fields["born_on"].field_type == "date"
    assert fields["born_on"].widget == "date"
    assert fields["created_at"].field_type == "datetime"
    assert fields["created_at"].widget == "datetime-local"
    assert fields["price"].field_type == "decimal"
    assert fields["price"].widget == "number"


def test_formfield_overrides_widget_and_attrs() -> None:
    """Per-field overrides can change widget type and HTML attributes."""
    fields = infer_admin_fields(
        WidgetModel,
        field_overrides={
            "name": {"widget": "textarea", "rows": 5, "placeholder": "Product name"},
            "born_on": {"min": "1900-01-01", "max": "2024-12-31"},
            "count": {"min": 0, "max": 100},
        },
    )
    by_name = {f.name: f for f in fields}
    assert by_name["name"].widget == "textarea"
    assert by_name["name"].attrs == {"rows": 5, "placeholder": "Product name"}
    assert by_name["born_on"].widget == "date"
    assert by_name["born_on"].attrs["min"] == "1900-01-01"
    assert by_name["born_on"].attrs["max"] == "2024-12-31"
    assert by_name["count"].attrs["min"] == 0
    assert by_name["count"].attrs["max"] == 100


def test_field_widget_from_mapping() -> None:
    from fastapi_mongo_admin.admin.fields.widgets import FieldWidget

    config = FieldWidget.from_mapping({"widget": "email", "maxlength": 120})
    assert config.widget == "email"
    assert config.attrs == {"maxlength": 120}


def test_prepare_form_fields_from_object() -> None:
    fields = prepare_form_fields(
        WidgetModel,
        obj={
            "name": "Test",
            "count": 3,
            "price": 9.9,
            "amount": "12.3",
            "is_active": True,
            "born_on": "2024-01-02",
            "created_at": "2024-01-02T08:15:00Z",
            "status": "active",
            "tier": "gold",
        },
    )
    by_name = {f.name: f for f in fields}
    assert by_name["price"].value == "9.90"
    assert by_name["born_on"].value == "2024-01-02"
    assert by_name["created_at"].value == "2024-01-02T08:15"
    assert by_name["status"].widget == "select"
