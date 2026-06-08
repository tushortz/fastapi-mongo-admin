"""Pluralization helpers and changelist count tests."""

import pytest
from httpx import AsyncClient

from fastapi_mongo_admin.admin.model import _pluralize_label
from tests.conftest import Product, ProductAdmin


def test_pluralize_label() -> None:
    assert _pluralize_label("Product") == "Products"
    assert _pluralize_label("Category") == "Categories"
    assert _pluralize_label("Box") == "Boxes"


def test_model_name_plural() -> None:
    assert ProductAdmin(Product).get_model_name_plural() == "Products"


@pytest.mark.asyncio
async def test_changelist_pluralizes_result_count(client: AsyncClient) -> None:
    response = await client.get("/admin/products/")
    assert response.status_code == 200
    assert "Products" in response.text
