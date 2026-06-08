"""Bulk delete action tests."""

import pytest
from httpx import AsyncClient

from fastapi_mongo_admin.admin.actions import DELETE_SELECTED_ACTION
from fastapi_mongo_admin.admin.decorators import action
from tests.conftest import Product, ProductAdmin


@pytest.mark.asyncio
async def test_changelist_shows_delete_selected(client: AsyncClient) -> None:
    response = await client.get("/admin/products/")
    assert response.status_code == 200
    assert "Delete selected" in response.text


@pytest.mark.asyncio
async def test_bulk_delete_requires_confirmation(client: AsyncClient, mock_db) -> None:
    doc = mock_db["test_db"].products.find_one({"name": "Python Guide"})
    doc_id = str(doc["_id"])

    response = await client.post(
        "/admin/products/action/",
        data={
            "action": "delete_selected",
            "_selected_action": doc_id,
        },
        follow_redirects=False,
    )
    assert response.status_code == 200
    assert "Are you sure?" in response.text
    assert "Python Guide" in response.text
    assert mock_db["test_db"].products.find_one({"_id": doc["_id"]}) is not None


@pytest.mark.asyncio
async def test_bulk_delete_after_confirmation(client: AsyncClient, mock_db) -> None:
    doc = mock_db["test_db"].products.find_one({"name": "Python Guide"})
    doc_id = str(doc["_id"])

    response = await client.post(
        "/admin/products/action/",
        data={
            "action": "delete_selected",
            "_selected_action": doc_id,
            "confirm": "1",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert mock_db["test_db"].products.find_one({"_id": doc["_id"]}) is None


def test_explicit_actions_always_include_delete() -> None:
    class AdminWithAction(ProductAdmin):
        actions = ["mark_inactive"]

        @action("Mark inactive")
        def mark_inactive(self, request, queryset) -> None:
            pass

    names = [name for name, _, _ in AdminWithAction(Product).get_actions()]
    assert DELETE_SELECTED_ACTION in names
    assert "mark_inactive" in names
    assert names[0] == DELETE_SELECTED_ACTION


def test_empty_actions_list_still_includes_delete() -> None:
    class AdminNoCustom(ProductAdmin):
        actions: list[str] = []

    names = [name for name, _, _ in AdminNoCustom(Product).get_actions()]
    assert names == [DELETE_SELECTED_ACTION]
