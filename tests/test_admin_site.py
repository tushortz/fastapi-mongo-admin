"""AdminSite registry tests."""

import pytest
from pydantic import BaseModel

from fastapi_mongo_admin import AdminSite, ModelAdmin


class Item(BaseModel):
    name: str


class ItemAdmin(ModelAdmin):
    collection_name = "items"


def test_register_model() -> None:
    site = AdminSite()
    site.register(Item, ItemAdmin)
    assert "items" in site.get_registered_collections()
    admin = site.get_model_admin("items")
    assert admin is not None
    assert admin.model is Item


def test_register_requires_collection_name() -> None:
    site = AdminSite()
    with pytest.raises(ValueError, match="collection_name"):
        site.register(Item)


def test_duplicate_registration_raises() -> None:
    site = AdminSite()
    site.register(Item, ItemAdmin)
    with pytest.raises(ValueError, match="already registered"):
        site.register(Item, ItemAdmin)


def test_register_view() -> None:
    site = AdminSite()

    async def custom_page() -> dict[str, str]:
        return {"ok": "true"}

    site.register_view("custom", "/custom/", custom_page)
    assert len(site._custom_views) == 1
