"""Form parsing tests."""

from pydantic import BaseModel

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
