"""Form parsing tests."""

from pydantic import BaseModel

from example.ecommerce.models import Customer, CustomerAddress
from fastapi_mongo_admin.schemas.forms import parse_form_to_model


class ToggleModel(BaseModel):
    name: str
    is_active: bool = True
    is_featured: bool = False


class TimestampedModel(BaseModel):
    name: str
    created_at: str | None = None


def test_unchecked_checkbox_is_false() -> None:
    """Unchecked checkboxes are omitted from POST data and must parse as False."""
    result = parse_form_to_model(ToggleModel, {"name": "Item"})
    assert result["is_active"] is False
    assert result["is_featured"] is False


def test_checked_checkbox_is_true() -> None:
    result = parse_form_to_model(
        ToggleModel,
        {"name": "Item", "is_active": "on", "is_featured": "on"},
    )
    assert result["is_active"] is True
    assert result["is_featured"] is True


def test_readonly_field_preserved_on_update() -> None:
    result = parse_form_to_model(
        TimestampedModel,
        {"name": "Updated"},
        existing={"created_at": "2024-06-08T12:00:00"},
        readonly_fields=["created_at"],
    )
    assert result["name"] == "Updated"
    assert result["created_at"] == "2024-06-08T12:00:00"


def test_optional_nested_model_empty_json_is_none() -> None:
    """Empty JSON object for optional nested models must parse as None."""
    result = parse_form_to_model(
        Customer,
        {
            "email": "user@example.com",
            "first_name": "Ada",
            "last_name": "Lovelace",
            "default_shipping": "{}",
        },
    )
    assert result["default_shipping"] is None


def test_nested_model_json_string_is_parsed() -> None:
    """Nested Pydantic models submitted via JSON editor must validate."""
    result = parse_form_to_model(
        Customer,
        {
            "email": "user@example.com",
            "first_name": "Ada",
            "last_name": "Lovelace",
            "default_shipping": (
                '{"line1": "1 Main St", "city": "Boston", "postal_code": "02101", "country": "US"}'
            ),
        },
    )
    assert result["default_shipping"] == {
        "line1": "1 Main St",
        "line2": "",
        "city": "Boston",
        "state": "",
        "postal_code": "02101",
        "country": "US",
    }


class TaggedModel(BaseModel):
    name: str
    tags: list[str] = []


def test_empty_tags_parse_as_list() -> None:
    """Tags submitted as empty JSON array or legacy object must parse as list."""
    result = parse_form_to_model(TaggedModel, {"name": "Item", "tags": "[]"})
    assert result["tags"] == []

    legacy = parse_form_to_model(TaggedModel, {"name": "Item", "tags": "{}"})
    assert legacy["tags"] == []


def test_tags_json_array_is_parsed() -> None:
    result = parse_form_to_model(
        TaggedModel,
        {"name": "Item", "tags": '["sale", "featured"]'},
    )
    assert result["tags"] == ["sale", "featured"]


def test_nested_model_dict_value_is_accepted() -> None:
    address = CustomerAddress(line1="1 Main St", city="Boston", postal_code="02101")
    result = parse_form_to_model(
        Customer,
        {
            "email": "user@example.com",
            "first_name": "Ada",
            "last_name": "Lovelace",
            "default_shipping": address.model_dump(),
        },
    )
    assert result["default_shipping"]["city"] == "Boston"
