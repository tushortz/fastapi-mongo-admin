"""Changelist view tests."""

import pytest
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
