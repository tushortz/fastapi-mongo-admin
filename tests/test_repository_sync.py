"""Sync repository tests."""

import mongomock
import pytest
from fastapi_mongo_admin.db.sync_backend import SyncPyMongoBackend
from fastapi_mongo_admin.services.repository import CollectionRepository
from tests.conftest import Product, ProductAdmin


@pytest.fixture
def repo(mock_db: mongomock.MongoClient) -> CollectionRepository:
    db = mock_db["test_db"]
    admin = ProductAdmin(Product)
    backend = SyncPyMongoBackend(db["products"])
    return CollectionRepository(backend, admin)


@pytest.mark.asyncio
async def test_list_documents(repo: CollectionRepository) -> None:
    result = await repo.list_documents(page=1)
    assert result["total"] == 2
    assert len(result["results"]) == 2


@pytest.mark.asyncio
async def test_get_document(repo: CollectionRepository, mock_db: mongomock.MongoClient) -> None:
    doc_id = str(mock_db["test_db"].products.find_one()["_id"])
    doc = await repo.get_document(doc_id)
    assert "name" in doc


@pytest.mark.asyncio
async def test_create_and_delete(repo: CollectionRepository) -> None:
    doc_id = await repo.create_document(
        {"name": "New", "price": "5.0", "category": "books", "active": "on"}
    )
    doc = await repo.get_document(doc_id)
    assert doc["name"] == "New"
    deleted = await repo.delete_document(doc_id)
    assert deleted is True
