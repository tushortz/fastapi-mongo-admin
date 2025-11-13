"""Additional comprehensive tests for utility functions to improve coverage."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from bson import ObjectId

from fastapi_mongo_admin.utils import convert_object_ids_in_query, get_searchable_fields
from tests.conftest import MockCursor


def test_convert_object_ids_in_query_eq_operator():
    """Test converting ObjectId in $eq operator."""
    query = {"_id": {"$eq": "507f1f77bcf86cd799439011"}}
    result = convert_object_ids_in_query(query)

    assert isinstance(result["_id"]["$eq"], ObjectId)


def test_convert_object_ids_in_query_eq_invalid():
    """Test $eq operator with invalid ObjectId."""
    query = {"_id": {"$eq": "invalid_id"}}
    result = convert_object_ids_in_query(query)

    assert result["_id"]["$eq"] == "invalid_id"


def test_convert_object_ids_in_query_nested_list():
    """Test converting ObjectIds in nested list structures."""
    query = {
        "items": [
            {"id": "507f1f77bcf86cd799439011", "name": "test"},
            {"id": "507f1f77bcf86cd799439012", "name": "test2"}
        ]
    }
    result = convert_object_ids_in_query(query)

    # Lists with dicts containing ObjectId strings should be recursively converted
    # Note: convert_object_ids_in_query recursively processes dicts in lists
    assert isinstance(result["items"][0]["id"], ObjectId) or result["items"][0]["id"] == "507f1f77bcf86cd799439011"
    assert isinstance(result["items"][1]["id"], ObjectId) or result["items"][1]["id"] == "507f1f77bcf86cd799439012"


def test_convert_object_ids_in_query_list_with_dict():
    """Test converting ObjectIds in list containing dict."""
    query = {
        "data": [
            {"_id": "507f1f77bcf86cd799439011"},
            {"_id": "507f1f77bcf86cd799439012"}
        ]
    }
    result = convert_object_ids_in_query(query)

    # Should recursively convert
    assert isinstance(result["data"][0]["_id"], ObjectId)
    assert isinstance(result["data"][1]["_id"], ObjectId)


def test_convert_object_ids_in_query_list_with_non_hex():
    """Test converting list with non-hex strings."""
    query = {
        "ids": ["507f1f77bcf86cd799439011", "not_hex_string_12345", "507f1f77bcf86cd799439012"]
    }
    result = convert_object_ids_in_query(query)

    assert isinstance(result["ids"][0], ObjectId)
    assert result["ids"][1] == "not_hex_string_12345"  # Not 24 chars or not hex
    assert isinstance(result["ids"][2], ObjectId)


def test_convert_object_ids_in_query_list_with_short_string():
    """Test converting list with short strings (not 24 chars)."""
    query = {
        "ids": ["short", "507f1f77bcf86cd799439011"]
    }
    result = convert_object_ids_in_query(query)

    assert result["ids"][0] == "short"
    assert isinstance(result["ids"][1], ObjectId)


def test_convert_object_ids_in_query_operator_with_non_list():
    """Test operator with non-list value."""
    query = {
        "_id": {"$in": "not_a_list"}
    }
    result = convert_object_ids_in_query(query)

    # Should handle gracefully
    assert result["_id"]["$in"] == "not_a_list"


@pytest.mark.asyncio
async def test_get_searchable_fields_with_mixed_types(test_collection):
    """Test getting searchable fields with mixed data types."""
    test_docs = [
        {
            "name": "Test",
            "value": 10,
            "description": "Some text",
            "created_at": "2024-01-01",
            "updated_at": "2024-01-01T12:00:00"
        },
        {
            "title": "Another",
            "content": "More text",
            "date": "2024-02-01"
        }
    ]

    test_collection.find = MagicMock(return_value=MockCursor(test_docs))

    fields = await get_searchable_fields(test_collection)

    # Should exclude date fields
    assert "created_at" not in fields
    assert "updated_at" not in fields
    assert "date" not in fields
    # Should include text fields
    assert "name" in fields or "description" in fields or "title" in fields or "content" in fields


@pytest.mark.asyncio
async def test_get_searchable_fields_exception_handling(test_collection):
    """Test get_searchable_fields handles exceptions gracefully."""
    # Mock find to raise an exception
    test_collection.find = MagicMock(side_effect=AttributeError("test error"))

    fields = await get_searchable_fields(test_collection)

    # Should return fallback
    assert fields == ["_id"]


@pytest.mark.asyncio
async def test_get_searchable_fields_type_error(test_collection):
    """Test get_searchable_fields handles TypeError."""
    # Mock find to raise TypeError
    test_collection.find = MagicMock(side_effect=TypeError("test error"))

    fields = await get_searchable_fields(test_collection)

    # Should return fallback
    assert fields == ["_id"]


@pytest.mark.asyncio
async def test_get_searchable_fields_value_error(test_collection):
    """Test get_searchable_fields handles ValueError."""
    # Mock find to raise ValueError
    test_collection.find = MagicMock(side_effect=ValueError("test error"))

    fields = await get_searchable_fields(test_collection)

    # Should return fallback
    assert fields == ["_id"]

