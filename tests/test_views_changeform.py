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
    assert response.headers["location"] == "/admin/products/"
    assert response.cookies.get("admin_flash") == "added"
    assert response.cookies.get("admin_flash_repr") == "Tablet"


@pytest.mark.asyncio
async def test_change_form(client: AsyncClient, mock_db) -> None:
    doc_id = str(mock_db["test_db"].products.find_one({"name": "Python Guide"})["_id"])
    response = await client.get(f"/admin/products/{doc_id}/change/")
    assert response.status_code == 200
    assert "Python Guide" in response.text


@pytest.mark.asyncio
async def test_uncheck_boolean_on_save(client: AsyncClient, mock_db) -> None:
    """Unchecked checkboxes must persist as False after save."""
    doc = mock_db["test_db"].products.find_one({"name": "Python Guide"})
    doc_id = str(doc["_id"])
    assert doc["active"] is True

    response = await client.post(
        f"/admin/products/{doc_id}/change/",
        data={
            "name": "Python Guide",
            "price": str(doc["price"]),
            "category": doc["category"],
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/admin/products/"
    assert response.cookies.get("admin_flash") == "changed"
    assert "Python Guide" in (response.cookies.get("admin_flash_repr") or "")

    updated = mock_db["test_db"].products.find_one({"_id": doc["_id"]})
    assert updated["active"] is False


@pytest.mark.asyncio
async def test_save_shows_success_message_on_changelist(client: AsyncClient, mock_db) -> None:
    """After save, changelist displays a success banner."""
    doc = mock_db["test_db"].products.find_one({"name": "Python Guide"})
    doc_id = str(doc["_id"])

    response = await client.post(
        f"/admin/products/{doc_id}/change/",
        data={
            "name": "Python Guide",
            "price": str(doc["price"]),
            "category": doc["category"],
            "active": "on",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "base-banner--positive" in response.text
    assert "Python Guide" in response.text
    assert "was saved successfully" in response.text
