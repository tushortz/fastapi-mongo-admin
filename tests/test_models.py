"""Tests for Pydantic models."""

import pytest
from pydantic import ValidationError

from fastapi_mongo_admin.models import (
    BulkCreateRequest,
    BulkDeleteRequest,
    BulkUpdateRequest,
    DocumentQuery,
    ExportRequest,
    ImportRequest,
)


def test_document_query_defaults():
    """Test DocumentQuery with default values."""
    query = DocumentQuery()

    assert query.query is None
    assert query.skip == 0
    assert query.limit == 100
    assert query.sort_field is None
    assert query.sort_order == "asc"


def test_document_query_custom_values():
    """Test DocumentQuery with custom values."""
    query = DocumentQuery(
        query='{"name": "test"}',
        skip=10,
        limit=50,
        sort_field="name",
        sort_order="desc",
    )

    assert query.query == '{"name": "test"}'
    assert query.skip == 10
    assert query.limit == 50
    assert query.sort_field == "name"
    assert query.sort_order == "desc"


def test_document_query_validation_dangerous_operator():
    """Test DocumentQuery validation with dangerous operator."""
    with pytest.raises(ValidationError) as exc_info:
        DocumentQuery(query='{"$where": "this.name == test"}')

    assert "Dangerous operator" in str(exc_info.value)


def test_document_query_validation_multiple_dangerous():
    """Test DocumentQuery validation with multiple dangerous operators."""
    with pytest.raises(ValidationError):
        DocumentQuery(query='{"$eval": "code", "$function": "func"}')


def test_document_query_validation_safe_query():
    """Test DocumentQuery validation with safe query."""
    query = DocumentQuery(query='{"name": "test", "age": {"$gt": 18}}')
    assert query.query == '{"name": "test", "age": {"$gt": 18}}'


def test_document_query_validation_skip_limits():
    """Test DocumentQuery validation with skip and limit constraints."""
    # Valid skip
    query = DocumentQuery(skip=0)
    assert query.skip == 0

    query = DocumentQuery(skip=100000)
    assert query.skip == 100000

    # Invalid skip
    with pytest.raises(ValidationError):
        DocumentQuery(skip=-1)

    # Valid limit
    query = DocumentQuery(limit=1)
    assert query.limit == 1

    query = DocumentQuery(limit=200)
    assert query.limit == 200

    # Invalid limit
    with pytest.raises(ValidationError):
        DocumentQuery(limit=0)

    with pytest.raises(ValidationError):
        DocumentQuery(limit=201)


def test_document_query_validation_sort_order():
    """Test DocumentQuery validation with sort order."""
    query = DocumentQuery(sort_order="asc")
    assert query.sort_order == "asc"

    query = DocumentQuery(sort_order="desc")
    assert query.sort_order == "desc"

    with pytest.raises(ValidationError):
        DocumentQuery(sort_order="invalid")


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


def test_export_request_defaults():
    """Test ExportRequest with default values."""
    request = ExportRequest()

    assert request.format == "json"
    assert request.query is None
    assert request.fields is None


def test_export_request_custom():
    """Test ExportRequest with custom values."""
    request = ExportRequest(
        format="csv", query='{"active": true}', fields=["name", "email"]
    )

    assert request.format == "csv"
    assert request.query == '{"active": true}'
    assert request.fields == ["name", "email"]


def test_export_request_invalid_format():
    """Test ExportRequest with invalid format."""
    with pytest.raises(ValidationError):
        ExportRequest(format="invalid")


def test_import_request_defaults():
    """Test ImportRequest with default values."""
    request = ImportRequest()

    assert request.format == "json"
    assert request.overwrite is False


def test_import_request_custom():
    """Test ImportRequest with custom values."""
    request = ImportRequest(format="yaml", overwrite=True)

    assert request.format == "yaml"
    assert request.overwrite is True


def test_import_request_invalid_format():
    """Test ImportRequest with invalid format."""
    with pytest.raises(ValidationError):
        ImportRequest(format="invalid")

