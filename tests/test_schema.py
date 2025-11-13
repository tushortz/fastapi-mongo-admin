"""Tests for schema utilities."""

import pytest
from bson import ObjectId
from datetime import datetime

from fastapi_mongo_admin.schema import serialize_for_export, serialize_object_id


def test_serialize_object_id_simple():
    """Test serializing a simple ObjectId."""
    obj_id = ObjectId()
    result = serialize_object_id(obj_id)

    assert isinstance(result, str)
    assert result == str(obj_id)


def test_serialize_object_id_in_dict():
    """Test serializing ObjectId in dictionary."""
    doc = {
        "_id": ObjectId(),
        "user_id": ObjectId(),
        "name": "Test"
    }
    result = serialize_object_id(doc)

    assert isinstance(result["_id"], str)
    assert isinstance(result["user_id"], str)
    assert result["name"] == "Test"


def test_serialize_object_id_in_list():
    """Test serializing ObjectId in list."""
    doc = {
        "tags": [ObjectId(), ObjectId()],
        "name": "Test"
    }
    result = serialize_object_id(doc)

    assert all(isinstance(tag, str) for tag in result["tags"])
    assert result["name"] == "Test"


def test_serialize_object_id_nested():
    """Test serializing ObjectId in nested structures."""
    doc = {
        "_id": ObjectId(),
        "metadata": {
            "created_by": ObjectId(),
            "updated_by": ObjectId()
        }
    }
    result = serialize_object_id(doc)

    assert isinstance(result["_id"], str)
    assert isinstance(result["metadata"]["created_by"], str)
    assert isinstance(result["metadata"]["updated_by"], str)


def test_serialize_object_id_no_objectid():
    """Test serializing document without ObjectId."""
    doc = {
        "name": "Test",
        "value": 123
    }
    result = serialize_object_id(doc)

    assert result == doc


def test_serialize_for_export_objectid():
    """Test serializing ObjectId for export."""
    obj_id = ObjectId()
    result = serialize_for_export(obj_id)

    assert isinstance(result, str)
    assert result == str(obj_id)


def test_serialize_for_export_datetime():
    """Test serializing datetime for export."""
    dt = datetime(2024, 1, 1, 12, 0, 0)
    result = serialize_for_export(dt)

    assert isinstance(result, str)
    assert result == dt.isoformat()


def test_serialize_for_export_dict():
    """Test serializing dictionary for export."""
    doc = {
        "_id": ObjectId(),
        "created_at": datetime(2024, 1, 1, 12, 0, 0),
        "name": "Test"
    }
    result = serialize_for_export(doc)

    assert isinstance(result["_id"], str)
    assert isinstance(result["created_at"], str)
    assert result["name"] == "Test"


def test_serialize_for_export_list():
    """Test serializing list for export."""
    data = [
        ObjectId(),
        datetime(2024, 1, 1, 12, 0, 0),
        "string"
    ]
    result = serialize_for_export(data)

    assert isinstance(result[0], str)
    assert isinstance(result[1], str)
    assert result[2] == "string"


def test_serialize_for_export_nested():
    """Test serializing nested structures for export."""
    doc = {
        "_id": ObjectId(),
        "metadata": {
            "created_at": datetime(2024, 1, 1, 12, 0, 0),
            "tags": [ObjectId(), ObjectId()]
        }
    }
    result = serialize_for_export(doc)

    assert isinstance(result["_id"], str)
    assert isinstance(result["metadata"]["created_at"], str)
    assert all(isinstance(tag, str) for tag in result["metadata"]["tags"])

