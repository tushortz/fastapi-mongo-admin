"""Tests for service layer."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from bson import ObjectId

from fastapi_mongo_admin.services import CollectionService
from tests.conftest import MOCK_DOCUMENTS


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
async def test_list_documents_optimized_with_query(collection_service, test_collection):
    """Test optimized document listing with query."""
    query = json.dumps({"active": True})
    result = await collection_service.list_documents_optimized(
        collection_name="test_collection",
        query=query,
        limit=10,
    )

    assert result["total"] == 2  # Only active documents
    assert all(doc["active"] is True for doc in result["documents"])


@pytest.mark.asyncio
async def test_list_documents_optimized_with_text_search(collection_service, test_collection):
    """Test optimized document listing with text search."""
    result = await collection_service.list_documents_optimized(
        collection_name="test_collection",
        query="Test 1",  # Text search
        limit=10,
    )

    assert result["total"] >= 1
    assert any("Test 1" in str(doc.values()) for doc in result["documents"])


@pytest.mark.asyncio
async def test_list_documents_optimized_with_sort(collection_service, test_collection):
    """Test optimized document listing with sorting."""
    result = await collection_service.list_documents_optimized(
        collection_name="test_collection",
        sort_field="value",
        sort_order="asc",
        limit=10,
    )

    values = [doc["value"] for doc in result["documents"]]
    assert values == sorted(values)


@pytest.mark.asyncio
async def test_list_documents_optimized_limit_enforcement(collection_service, test_collection):
    """Test that limit is enforced at maximum."""
    result = await collection_service.list_documents_optimized(
        collection_name="test_collection",
        limit=500,  # Exceeds max of 200
    )

    assert result["limit"] == 200
    assert len(result["documents"]) <= 200


@pytest.mark.asyncio
async def test_list_documents_optimized_with_fields(collection_service, test_collection):
    """Test optimized document listing with field projection."""
    result = await collection_service.list_documents_optimized(
        collection_name="test_collection",
        fields=["name", "value"],
        limit=10,
    )

    # All documents should only have specified fields + _id
    for doc in result["documents"]:
        assert "_id" in doc
        assert "name" in doc or "value" in doc
        # Should not have other fields
        assert "active" not in doc or len(doc) <= 3  # _id + name + value


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
async def test_list_documents_with_cursor_next_page(collection_service, test_collection):
    """Test cursor-based pagination with next page."""
    # Get first page
    first_result = await collection_service.list_documents_optimized(
        collection_name="test_collection",
        limit=1,
        use_cursor=True,
    )

    assert first_result["has_more"] is True
    assert first_result["next_cursor"] is not None

    # Get second page
    second_result = await collection_service.list_documents_optimized(
        collection_name="test_collection",
        limit=1,
        cursor=first_result["next_cursor"],
        use_cursor=True,
    )

    assert len(second_result["documents"]) == 1
    assert second_result["documents"][0]["_id"] != first_result["documents"][0]["_id"]


@pytest.mark.asyncio
async def test_search_documents_optimized(collection_service, test_collection):
    """Test optimized document search."""
    query = {"active": True}
    result = await collection_service.search_documents_optimized(
        collection_name="test_collection",
        query=query,
        limit=10,
    )

    assert "documents" in result
    assert "total" in result
    assert result["total"] == 2
    assert all(doc["active"] is True for doc in result["documents"])


@pytest.mark.asyncio
async def test_search_documents_optimized_with_sort(collection_service, test_collection):
    """Test optimized document search with sorting."""
    query = {}
    result = await collection_service.search_documents_optimized(
        collection_name="test_collection",
        query=query,
        sort_field="value",
        sort_order="desc",
        limit=10,
    )

    values = [doc["value"] for doc in result["documents"]]
    assert values == sorted(values, reverse=True)


@pytest.mark.asyncio
async def test_search_documents_optimized_empty_result(collection_service, test_collection):
    """Test optimized document search with no results."""
    query = {"nonexistent": "value"}
    result = await collection_service.search_documents_optimized(
        collection_name="test_collection",
        query=query,
        limit=10,
    )

    assert result["total"] == 0
    assert len(result["documents"]) == 0


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
async def test_bulk_create_empty_list(collection_service):
    """Test bulk document creation with empty list."""
    # insert_many requires non-empty list, so this should raise an error
    with pytest.raises((ValueError, TypeError)):
        await collection_service.bulk_create_documents(
            collection_name="test_collection",
            documents=[],
        )


@pytest.mark.asyncio
async def test_bulk_update_documents(collection_service, test_collection):
    """Test bulk document update."""
    # Mock document IDs
    doc_id_1 = str(ObjectId())
    doc_id_2 = str(ObjectId())

    updates = [
        {"_id": doc_id_1, "data": {"name": "Updated 1"}},
        {"_id": doc_id_2, "data": {"name": "Updated 2"}},
    ]

    # Mock bulk_write to return modified_count
    mock_bulk_result = AsyncMock()
    mock_bulk_result.modified_count = 2
    test_collection.bulk_write = AsyncMock(return_value=mock_bulk_result)

    result = await collection_service.bulk_update_documents(
        collection_name="test_collection",
        updates=updates,
    )

    assert result["updated_count"] == 2


@pytest.mark.asyncio
async def test_bulk_delete(collection_service, test_collection):
    """Test bulk document deletion."""
    # Use actual document IDs from MOCK_DOCUMENTS
    doc_ids = [str(MOCK_DOCUMENTS[0]["_id"]), str(MOCK_DOCUMENTS[1]["_id"])]

    result = await collection_service.bulk_delete_documents(
        collection_name="test_collection",
        document_ids=doc_ids,
    )

    assert result["deleted_count"] == 2


@pytest.mark.asyncio
async def test_bulk_delete_invalid_ids(collection_service):
    """Test bulk document deletion with invalid IDs."""
    # Invalid IDs are filtered out gracefully (InvalidId is caught as ValueError)
    result = await collection_service.bulk_delete_documents(
        collection_name="test_collection",
        document_ids=["invalid_id_1", "invalid_id_2"],
    )

    # Invalid IDs are skipped, so deleted_count should be 0
    assert result["deleted_count"] == 0
    assert result["total"] == 2


@pytest.mark.asyncio
async def test_bulk_delete_empty_list(collection_service):
    """Test bulk document deletion with empty list."""
    result = await collection_service.bulk_delete_documents(
        collection_name="test_collection",
        document_ids=[],
    )

    assert result["deleted_count"] == 0
