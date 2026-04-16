"""Tests for Pydantic models."""

import pytest
from pydantic import ValidationError

from fastapi_mongo_admin.models import (
    BulkCreateRequest,
    BulkDeleteRequest,
    BulkUpdateRequest,
)


def test_bulk_create_request_valid():
    """Test BulkCreateRequest with valid data."""
    request = BulkCreateRequest(documents=[{"name": "Test 1"}, {"name": "Test 2"}])

    assert len(request.documents) == 2
    assert request.documents[0]["name"] == "Test 1"


def test_bulk_create_request_empty():
    """Test BulkCreateRequest with empty list."""
    with pytest.raises(ValidationError):
        BulkCreateRequest(documents=[])


def test_bulk_create_request_too_many():
    """Test BulkCreateRequest with too many documents."""
    documents = [{"name": f"Test {i}"} for i in range(1001)]
    with pytest.raises(ValidationError):
        BulkCreateRequest(documents=documents)


def test_bulk_create_request_not_list():
    """Test BulkCreateRequest with non-list input."""
    with pytest.raises(ValidationError):
        BulkCreateRequest(documents={"name": "Test"})


def test_bulk_update_request_valid():
    """Test BulkUpdateRequest with valid data."""
    request = BulkUpdateRequest(
        updates=[
            {"_id": "507f1f77bcf86cd799439011", "data": {"name": "Updated 1"}},
            {"_id": "507f1f77bcf86cd799439012", "data": {"name": "Updated 2"}},
        ]
    )

    assert len(request.updates) == 2
    assert request.updates[0]["_id"] == "507f1f77bcf86cd799439011"


def test_bulk_update_request_missing_id():
    """Test BulkUpdateRequest with missing _id."""
    with pytest.raises(ValidationError):
        BulkUpdateRequest(updates=[{"data": {"name": "Test"}}])


def test_bulk_update_request_missing_data():
    """Test BulkUpdateRequest with missing data."""
    with pytest.raises(ValidationError):
        BulkUpdateRequest(updates=[{"_id": "507f1f77bcf86cd799439011"}])


def test_bulk_update_request_empty():
    """Test BulkUpdateRequest with empty list."""
    with pytest.raises(ValidationError):
        BulkUpdateRequest(updates=[])


def test_bulk_update_request_too_many():
    """Test BulkUpdateRequest with too many updates."""
    updates = [
        {"_id": f"507f1f77bcf86cd79943{i:04d}", "data": {"name": f"Test {i}"}}
        for i in range(1001)
    ]
    with pytest.raises(ValidationError):
        BulkUpdateRequest(updates=updates)


def test_bulk_delete_request_valid():
    """Test BulkDeleteRequest with valid data."""
    request = BulkDeleteRequest(
        document_ids=["507f1f77bcf86cd799439011", "507f1f77bcf86cd799439012"]
    )

    assert len(request.document_ids) == 2


def test_bulk_delete_request_empty():
    """Test BulkDeleteRequest with empty list."""
    with pytest.raises(ValidationError):
        BulkDeleteRequest(document_ids=[])


def test_bulk_delete_request_too_many():
    """Test BulkDeleteRequest with too many IDs."""
    document_ids = [f"507f1f77bcf86cd79943{i:04d}" for i in range(1001)]
    with pytest.raises(ValidationError):
        BulkDeleteRequest(document_ids=document_ids)


def test_bulk_delete_request_not_list():
    """Test BulkDeleteRequest with non-list input."""
    with pytest.raises(ValidationError):
        BulkDeleteRequest(document_ids="507f1f77bcf86cd799439011")

