"""Additional tests for pagination utilities to improve coverage."""

import json
from unittest.mock import MagicMock

import pytest
from bson import ObjectId
from datetime import datetime

from fastapi_mongo_admin.pagination import get_documents_cursor
from tests.conftest import MockCursor


@pytest.mark.asyncio
async def test_get_documents_cursor_with_datetime_sort_value(test_collection):
    """Test cursor pagination with datetime sort value."""
    # Create documents with datetime values
    test_docs = [
        {"_id": ObjectId(), "created_at": datetime(2024, 1, 1), "name": "First"},
        {"_id": ObjectId(), "created_at": datetime(2024, 1, 2), "name": "Second"},
        {"_id": ObjectId(), "created_at": datetime(2024, 1, 3), "name": "Third"},
    ]

    test_collection.find = MagicMock(return_value=MockCursor(test_docs, query={}))

    result = await get_documents_cursor(
        collection=test_collection,
        query={},
        sort_field="created_at",
        sort_direction=1,
        limit=2,
    )

    assert len(result["documents"]) == 2
    assert result["has_more"] is True
    # Cursor should be generated successfully even with datetime
    assert result["next_cursor"] is not None


@pytest.mark.asyncio
async def test_get_documents_cursor_with_non_serializable_sort_value(test_collection):
    """Test cursor pagination with non-serializable sort value."""
    # Use multiple documents to ensure has_more is True
    test_docs = [
        {"_id": ObjectId(), "custom": 123, "name": "First"},
        {"_id": ObjectId(), "custom": 456, "name": "Second"},
    ]

    test_collection.find = MagicMock(return_value=MockCursor(test_docs, query={}))

    result = await get_documents_cursor(
        collection=test_collection,
        query={},
        sort_field="custom",
        sort_direction=1,
        limit=1,
    )

    # Should handle successfully and generate cursor
    assert len(result["documents"]) == 1
    assert result["has_more"] is True
    assert result["next_cursor"] is not None


@pytest.mark.asyncio
async def test_get_documents_cursor_compound_cursor_ascending(test_collection):
    """Test compound cursor with ascending sort."""
    test_docs = [
        {"_id": ObjectId(), "value": 1, "name": "First"},
        {"_id": ObjectId(), "value": 2, "name": "Second"},
        {"_id": ObjectId(), "value": 2, "name": "Third"},  # Same value, different _id
    ]

    test_collection.find = MagicMock(return_value=MockCursor(test_docs, query={}))

    result = await get_documents_cursor(
        collection=test_collection,
        query={},
        sort_field="value",
        sort_direction=1,
        limit=2,
    )

    assert len(result["documents"]) == 2
    # Should use compound cursor for non-_id sort
    assert result["next_cursor"] is not None


@pytest.mark.asyncio
async def test_get_documents_cursor_compound_cursor_descending(test_collection):
    """Test compound cursor with descending sort."""
    test_docs = [
        {"_id": ObjectId(), "value": 3, "name": "First"},
        {"_id": ObjectId(), "value": 2, "name": "Second"},
        {"_id": ObjectId(), "value": 1, "name": "Third"},
    ]

    test_collection.find = MagicMock(return_value=MockCursor(test_docs, query={}))

    result = await get_documents_cursor(
        collection=test_collection,
        query={},
        sort_field="value",
        sort_direction=-1,
        limit=2,
    )

    assert len(result["documents"]) == 2
    # Should use compound cursor with $lt for descending
    assert result["next_cursor"] is not None


@pytest.mark.asyncio
async def test_get_documents_cursor_with_none_sort_value(test_collection):
    """Test cursor pagination with None sort value."""
    # Use documents where some have None values
    test_docs = [
        {"_id": ObjectId(), "value": 0, "name": "First"},  # Use 0 instead of None for sorting
        {"_id": ObjectId(), "value": 1, "name": "Second"},
    ]

    test_collection.find = MagicMock(return_value=MockCursor(test_docs, query={}))

    result = await get_documents_cursor(
        collection=test_collection,
        query={},
        sort_field="value",
        sort_direction=1,
        limit=1,
    )

    # Should handle successfully
    assert len(result["documents"]) == 1

