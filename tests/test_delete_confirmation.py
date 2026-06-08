"""Delete confirmation flow tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_single_delete_requires_confirmation(client: AsyncClient, mock_db) -> None:
    doc = mock_db["test_db"].products.find_one({"name": "Python Guide"})
    doc_id = str(doc["_id"])

    confirm_page = await client.get(f"/admin/products/{doc_id}/delete/")
    assert confirm_page.status_code == 200
    assert "Are you sure?" in confirm_page.text

    direct_delete = await client.post(
        f"/admin/products/{doc_id}/delete/",
        data={},
        follow_redirects=False,
    )
    assert direct_delete.status_code == 303
    assert mock_db["test_db"].products.find_one({"_id": doc["_id"]}) is None
