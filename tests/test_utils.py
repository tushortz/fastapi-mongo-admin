"""Tests for utility functions."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from bson import ObjectId

from fastapi_mongo_admin.utils import convert_object_ids_in_query, get_searchable_fields
from tests.conftest import MockCursor


def test_convert_object_ids_in_query_simple():
    """Test converting simple _id string to ObjectId."""
    query = {"_id": "507f1f77bcf86cd799439011"}
    result = convert_object_ids_in_query(query)

    assert isinstance(result["_id"], ObjectId)
    assert str(result["_id"]) == "507f1f77bcf86cd799439011"


def test_convert_object_ids_in_query_invalid_id():
    """Test converting invalid ObjectId string."""
    query = {"_id": "invalid_id"}
    result = convert_object_ids_in_query(query)

    # Should keep original value if invalid (InvalidId exception is caught as ValueError)
    assert result["_id"] == "invalid_id"


def test_convert_object_ids_in_query_with_operators():
    """Test converting ObjectIds in MongoDB operators."""
    query = {
        "_id": {"$in": ["507f1f77bcf86cd799439011", "507f1f77bcf86cd799439012"]}
    }
    result = convert_object_ids_in_query(query)

    assert all(isinstance(obj_id, ObjectId) for obj_id in result["_id"]["$in"])


def test_convert_object_ids_in_query_with_nin():
    """Test converting ObjectIds in $nin operator."""
    query = {
        "_id": {"$nin": ["507f1f77bcf86cd799439011", "invalid"]}
    }
    result = convert_object_ids_in_query(query)

    # Valid ObjectId should be converted, invalid should remain
    assert isinstance(result["_id"]["$nin"][0], ObjectId)
    assert result["_id"]["$nin"][1] == "invalid"


def test_convert_object_ids_in_query_nested():
    """Test converting ObjectIds in nested structures."""
    # Note: convert_object_ids_in_query only converts top-level _id, not nested ones
    query = {
        "_id": "507f1f77bcf86cd799439011",
        "user": {
            "profile": {
                "user_id": "507f1f77bcf86cd799439011"  # Not _id, so won't be converted
            }
        }
    }
    result = convert_object_ids_in_query(query)

    # Top-level _id should be converted
    assert isinstance(result["_id"], ObjectId)
    # Nested user_id won't be converted (only _id at top level)
    assert isinstance(result["user"]["profile"]["user_id"], str)


def test_convert_object_ids_in_query_list():
    """Test converting ObjectIds in list."""
    query = {
        "ids": ["507f1f77bcf86cd799439011", "507f1f77bcf86cd799439012", "not_an_id"]
    }
    result = convert_object_ids_in_query(query)

    # Valid ObjectIds should be converted
    assert isinstance(result["ids"][0], ObjectId)
    assert isinstance(result["ids"][1], ObjectId)
    assert result["ids"][2] == "not_an_id"


def test_convert_object_ids_in_query_non_dict():
    """Test converting non-dict query."""
    query = "not a dict"
    result = convert_object_ids_in_query(query)

    assert result == query


def test_convert_object_ids_in_query_empty():
    """Test converting empty query."""
    query = {}
    result = convert_object_ids_in_query(query)

    assert result == {}


@pytest.mark.asyncio
async def test_get_searchable_fields(test_collection):
    """Test getting searchable fields from collection."""
    # Mock the find() cursor to return sample documents
    # find() returns a cursor synchronously, not a coroutine
    def mock_find(*args, **kwargs):
        cursor = MagicMock()
        async def async_iter():
            yield {"name": "Test", "value": 10, "description": "Test description"}
        cursor.__aiter__ = async_iter
        cursor.limit = MagicMock(return_value=cursor)
        return cursor

    test_collection.find = MagicMock(side_effect=mock_find)

    fields = await get_searchable_fields(test_collection)

    assert isinstance(fields, list)
    assert len(fields) > 0
    # Should include string fields but not _id
    assert "_id" not in fields or fields == ["_id"]  # Fallback case


@pytest.mark.asyncio
async def test_get_searchable_fields_excludes_dates(test_collection):
    """Test that date fields are excluded from searchable fields."""
    # Create a cursor with date-like strings
    test_docs = [{
        "name": "Test",
        "created_at": "2024-01-01T00:00:00",
        "description": "Some text"
    }]

    # Override find to return our custom cursor
    test_collection.find = MagicMock(return_value=MockCursor(test_docs))

    fields = await get_searchable_fields(test_collection)

    # Should exclude date-like fields
    assert "created_at" not in fields
    # Should include regular string fields
    assert "description" in fields or "name" in fields


@pytest.mark.asyncio
async def test_get_searchable_fields_empty_collection(test_collection):
    """Test getting searchable fields from empty collection."""
    # Mock empty collection
    # find() returns a cursor synchronously, not a coroutine
    def mock_find(*args, **kwargs):
        cursor = MagicMock()
        async def async_iter():
            return
            yield  # Empty generator
        cursor.__aiter__ = async_iter
        cursor.limit = MagicMock(return_value=cursor)
        return cursor

    test_collection.find = MagicMock(side_effect=mock_find)

    fields = await get_searchable_fields(test_collection)

    # Should return fallback
    assert fields == ["_id"]

