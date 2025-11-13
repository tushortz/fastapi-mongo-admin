"""Tests for pagination utilities."""

import base64
import json
from unittest.mock import MagicMock

import pytest
from bson import ObjectId

from fastapi_mongo_admin.pagination import (
    decode_cursor,
    encode_cursor,
    get_documents_cursor,
)
from tests.conftest import MockCursor


@pytest.mark.asyncio
async def test_get_documents_cursor_basic(test_collection):
    """Test basic cursor pagination."""
    result = await get_documents_cursor(
        collection=test_collection,
        query={},
        limit=2,
    )

    assert "documents" in result
    assert "next_cursor" in result
    assert "has_more" in result
    assert "limit" in result
    assert len(result["documents"]) == 2
    assert result["has_more"] is True
    assert result["limit"] == 2


@pytest.mark.asyncio
async def test_get_documents_cursor_no_more(test_collection):
    """Test cursor pagination when no more documents."""
    result = await get_documents_cursor(
        collection=test_collection,
        query={},
        limit=10,
    )

    assert len(result["documents"]) == 3
    assert result["has_more"] is False
    assert result["next_cursor"] is None


@pytest.mark.asyncio
async def test_get_documents_cursor_with_cursor(test_collection):
    """Test cursor pagination with provided cursor."""
    # Get first page
    first_result = await get_documents_cursor(
        collection=test_collection,
        query={},
        limit=1,
    )

    assert first_result["has_more"] is True
    assert first_result["next_cursor"] is not None

    # Get second page using cursor
    second_result = await get_documents_cursor(
        collection=test_collection,
        query={},
        cursor=first_result["next_cursor"],
        limit=1,
    )

    assert len(second_result["documents"]) == 1
    assert second_result["documents"][0]["_id"] != first_result["documents"][0]["_id"]


@pytest.mark.asyncio
async def test_get_documents_cursor_with_query(test_collection):
    """Test cursor pagination with query filter."""
    result = await get_documents_cursor(
        collection=test_collection,
        query={"active": True},
        limit=10,
    )

    assert len(result["documents"]) == 2  # Only active documents
    assert all(doc["active"] is True for doc in result["documents"])


@pytest.mark.asyncio
async def test_get_documents_cursor_sort_field(test_collection):
    """Test cursor pagination with custom sort field."""
    result = await get_documents_cursor(
        collection=test_collection,
        query={},
        sort_field="value",
        sort_direction=1,
        limit=2,
    )

    assert len(result["documents"]) == 2
    # Verify sorting
    values = [doc["value"] for doc in result["documents"]]
    assert values == sorted(values)


@pytest.mark.asyncio
async def test_get_documents_cursor_descending(test_collection):
    """Test cursor pagination with descending sort."""
    result = await get_documents_cursor(
        collection=test_collection,
        query={},
        sort_field="value",
        sort_direction=-1,
        limit=2,
    )

    assert len(result["documents"]) == 2
    # Verify descending sort
    values = [doc["value"] for doc in result["documents"]]
    assert values == sorted(values, reverse=True)


@pytest.mark.asyncio
async def test_get_documents_cursor_invalid_cursor(test_collection):
    """Test cursor pagination with invalid cursor."""
    result = await get_documents_cursor(
        collection=test_collection,
        query={},
        cursor="invalid_cursor_string",
        limit=10,
    )

    # Should ignore invalid cursor and return all documents
    assert len(result["documents"]) == 3


@pytest.mark.asyncio
async def test_get_documents_cursor_empty_collection(test_collection):
    """Test cursor pagination with empty collection."""
    # Override find to return empty cursor
    test_collection.find = MagicMock(return_value=MockCursor([]))

    result = await get_documents_cursor(
        collection=test_collection,
        query={},
        limit=10,
    )

    assert len(result["documents"]) == 0
    assert result["has_more"] is False
    assert result["next_cursor"] is None


def test_encode_cursor():
    """Test cursor encoding."""
    doc_id = str(ObjectId())
    encoded = encode_cursor(doc_id)

    assert isinstance(encoded, str)
    assert len(encoded) > 0
    # Should be base64 decodable
    decoded = base64.urlsafe_b64decode(encoded.encode()).decode()
    assert decoded == doc_id


def test_decode_cursor():
    """Test cursor decoding."""
    doc_id = str(ObjectId())
    encoded = encode_cursor(doc_id)
    decoded = decode_cursor(encoded)

    assert decoded == doc_id


def test_decode_cursor_invalid():
    """Test decoding invalid cursor."""
    result = decode_cursor("invalid_cursor")
    assert result is None


def test_decode_cursor_empty():
    """Test decoding empty cursor."""
    # Empty string can be decoded (returns empty string), so test with invalid base64
    result = decode_cursor("!!!invalid!!!")
    assert result is None

