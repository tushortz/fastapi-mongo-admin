"""Changelist column ordering tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_sort_by_name_ascending(client: AsyncClient) -> None:
    response = await client.get("/admin/products/", params={"o": "name"})
    assert response.status_code == 200
    name_laptop = response.text.find("Laptop")
    name_python = response.text.find("Python Guide")
    assert name_laptop != -1 and name_python != -1
    assert name_laptop < name_python


@pytest.mark.asyncio
async def test_sort_by_name_descending(client: AsyncClient) -> None:
    response = await client.get("/admin/products/", params={"o": "-name"})
    assert response.status_code == 200
    name_laptop = response.text.find("Laptop")
    name_python = response.text.find("Python Guide")
    assert name_laptop != -1 and name_python != -1
    assert name_python < name_laptop


@pytest.mark.asyncio
async def test_sortable_column_header_link(client: AsyncClient) -> None:
    response = await client.get("/admin/products/")
    assert response.status_code == 200
    assert 'class="sortable-header"' in response.text
    assert "o=name" in response.text
