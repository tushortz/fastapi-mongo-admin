"""Changelist view tests."""

import mongomock
import pytest
from bson import ObjectId
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_admin_index(client: AsyncClient) -> None:
    response = await client.get("/admin/")
    assert response.status_code == 200
    assert "Product" in response.text
    assert "Category" in response.text


@pytest.mark.asyncio
async def test_changelist(client: AsyncClient) -> None:
    response = await client.get("/admin/products/")
    assert response.status_code == 200
    assert "Python Guide" in response.text
    assert "Laptop" in response.text


@pytest.mark.asyncio
async def test_changelist_search(client: AsyncClient) -> None:
    response = await client.get("/admin/products/", params={"q": "Python"})
    assert response.status_code == 200
    assert "Python Guide" in response.text
    assert 'class="search-form search-form--inline"' in response.text
    assert 'class="changelist-toolbar"' in response.text


@pytest.mark.asyncio
async def test_changelist_hides_search_without_search_fields(client: AsyncClient) -> None:
    """Models without search_fields must not render the search form."""
    response = await client.get("/admin/categories/")
    assert response.status_code == 200
    assert 'class="search-form"' not in response.text


@pytest.mark.asyncio
async def test_changelist_filter(client: AsyncClient) -> None:
    response = await client.get("/admin/products/", params={"category": "books"})
    assert response.status_code == 200
    assert "Python Guide" in response.text


@pytest.mark.asyncio
async def test_htmx_partial(client: AsyncClient) -> None:
    response = await client.get(
        "/admin/products/",
        params={"page": 1},
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 200
    assert "results-table" in response.text


@pytest.mark.asyncio
async def test_changelist_page_query_param(
    client: AsyncClient, mock_db: mongomock.MongoClient
) -> None:
    """Page query param is reflected in pagination links and loads the correct page."""
    db = mock_db["test_db"]
    for i in range(11):
        db.products.insert_one(
            {
                "_id": ObjectId(),
                "name": f"Item {i}",
                "price": 1.0,
                "category": "books",
                "active": True,
            }
        )

    page_two = await client.get("/admin/products/", params={"page": 2})
    assert page_two.status_code == 200
    assert "Item 0" in page_two.text
    assert 'hx-get="/admin/products/?page=1' in page_two.text
    assert 'hx-push-url="true"' in page_two.text

    page_one = await client.get("/admin/products/", params={"page": 1})
    assert page_one.status_code == 200
    assert 'hx-get="/admin/products/?page=2' in page_one.text
