"""Tests for utility functions."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from bson import ObjectId

from fastapi import FastAPI
from fastapi_mongo_admin.utils import (
    _model_name_to_collection_name,
    convert_object_ids_in_query,
    get_static_directory,
    mount_admin_app,
    mount_admin_ui,
)
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


def test_model_name_to_collection_name():
    """Test model name to collection name conversion."""
    assert _model_name_to_collection_name("Product") == "products"
    assert _model_name_to_collection_name("OrderItem") == "order_items"
    assert _model_name_to_collection_name("Category") == "categories"
    assert _model_name_to_collection_name("") == ""


def test_get_static_directory():
    """Test getting static directory path."""
    static_dir = get_static_directory()
    assert static_dir.exists()
    assert (static_dir / "admin.html").exists()


def test_mount_admin_ui():
    """Test mounting admin UI."""
    app = FastAPI()
    result = mount_admin_ui(app)
    assert result is True
    # Verify routes were added
    paths = [r.path for r in app.routes]
    assert "/admin-ui/admin.html" in paths


@pytest.mark.asyncio
async def test_mount_admin_app(mock_database):
    """Test mounting admin app."""
    app = FastAPI()
    async def get_db():
        return mock_database
    
    router = mount_admin_app(app, get_database=get_db)
    assert router is not None
    # Verify router in app
    paths = [r.path for r in app.routes]
    assert any(p.startswith("/admin") for p in paths)

