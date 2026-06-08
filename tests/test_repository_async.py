"""Async repository tests with mocked async backend."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from bson import ObjectId

from fastapi_mongo_admin.services.repository import CollectionRepository
from tests.conftest import Product, ProductAdmin


@pytest.fixture
def async_repo() -> CollectionRepository:
    """Async repository with mocked backend."""
    backend = MagicMock()
    doc_id = ObjectId()
    backend.find = AsyncMock(
        return_value=[
            {"_id": doc_id, "name": "Async Item", "price": 1.0, "category": "books", "active": True}
        ]
    )
    backend.count = AsyncMock(return_value=1)
    admin = ProductAdmin(Product)
    repo = CollectionRepository(backend, admin)
    repo._is_async = True
    return repo


@pytest.mark.asyncio
async def test_async_list(async_repo: CollectionRepository) -> None:
    result = await async_repo.list_documents()
    assert result["total"] == 1
    assert result["results"][0]["name"] == "Async Item"
