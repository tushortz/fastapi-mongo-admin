"""Tests for service layer."""

import pytest

from fastapi_mongo_admin.services import CollectionService


@pytest.mark.asyncio
async def test_list_documents_optimized(collection_service, test_collection):
    """Test optimized document listing."""
    result = await collection_service.list_documents_optimized(
        collection_name="test_collection",
        skip=0,
        limit=10,
    )

    assert "documents" in result
    assert "total" in result
    assert len(result["documents"]) == 3
    assert result["total"] == 3


@pytest.mark.asyncio
async def test_list_documents_with_cursor(collection_service, test_collection):
    """Test cursor-based pagination."""
    result = await collection_service.list_documents_optimized(
        collection_name="test_collection",
        limit=2,
        use_cursor=True,
    )

    assert "documents" in result
    assert "next_cursor" in result
    assert "has_more" in result
    assert len(result["documents"]) == 2
    assert result["has_more"] is True


@pytest.mark.asyncio
async def test_bulk_create(collection_service):
    """Test bulk document creation."""
    documents = [
        {"name": "Bulk 1", "value": 1},
        {"name": "Bulk 2", "value": 2},
    ]

    result = await collection_service.bulk_create_documents(
        collection_name="test_collection",
        documents=documents,
    )

    assert result["inserted_count"] == 2
    assert len(result["inserted_ids"]) == 2


@pytest.mark.asyncio
async def test_bulk_delete(collection_service, test_collection):
    """Test bulk document deletion."""
    # Get document IDs
    cursor = test_collection.find({})
    docs = await cursor.to_list(length=None)
    doc_ids = [str(doc["_id"]) for doc in docs[:2]]

    result = await collection_service.bulk_delete_documents(
        collection_name="test_collection",
        document_ids=doc_ids,
    )

    assert result["deleted_count"] == 2

