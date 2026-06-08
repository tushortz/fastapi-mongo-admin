"""Change form view tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_add_form(client: AsyncClient) -> None:
    response = await client.get("/admin/products/add/")
    assert response.status_code == 200
    assert "Add Product" in response.text


@pytest.mark.asyncio
async def test_create_product(client: AsyncClient) -> None:
    response = await client.post(
        "/admin/products/add/",
        data={
            "name": "Tablet",
            "price": "199.99",
            "category": "electronics",
            "active": "on",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert "/change/" in response.headers["location"]


@pytest.mark.asyncio
async def test_change_form(client: AsyncClient, mock_db) -> None:
    doc_id = str(mock_db["test_db"].products.find_one({"name": "Python Guide"})["_id"])
    response = await client.get(f"/admin/products/{doc_id}/change/")
    assert response.status_code == 200
    assert "Python Guide" in response.text
