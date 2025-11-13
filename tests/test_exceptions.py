"""Tests for custom exceptions."""

import pytest

from fastapi_mongo_admin.exceptions import (
    AdminException,
    CollectionNotFoundError,
    DocumentNotFoundError,
    InvalidQueryError,
    PermissionDeniedError,
    ValidationError,
)


def test_admin_exception_basic():
    """Test basic AdminException."""
    exc = AdminException(
        status_code=400, detail="Test error", error_code="TEST_ERROR", details={"key": "value"}
    )

    assert exc.status_code == 400
    assert exc.detail == "Test error"
    assert exc.error_code == "TEST_ERROR"
    assert exc.details == {"key": "value"}


def test_admin_exception_minimal():
    """Test AdminException with minimal parameters."""
    exc = AdminException(status_code=500, detail="Error")

    assert exc.status_code == 500
    assert exc.detail == "Error"
    assert exc.error_code is None
    assert exc.details == {}


def test_document_not_found_error():
    """Test DocumentNotFoundError."""
    exc = DocumentNotFoundError(document_id="123", collection_name="test_collection")

    assert exc.status_code == 404
    assert "123" in exc.detail
    assert "test_collection" in exc.detail
    assert exc.error_code == "DOCUMENT_NOT_FOUND"
    assert exc.details["document_id"] == "123"
    assert exc.details["collection_name"] == "test_collection"


def test_collection_not_found_error():
    """Test CollectionNotFoundError."""
    exc = CollectionNotFoundError(collection_name="nonexistent")

    assert exc.status_code == 404
    assert "nonexistent" in exc.detail
    assert exc.error_code == "COLLECTION_NOT_FOUND"
    assert exc.details["collection_name"] == "nonexistent"


def test_invalid_query_error():
    """Test InvalidQueryError."""
    exc = InvalidQueryError(detail="Invalid query", query='{"$where": "code"}')

    assert exc.status_code == 400
    assert exc.detail == "Invalid query"
    assert exc.error_code == "INVALID_QUERY"
    assert exc.details["query"] == '{"$where": "code"}'


def test_invalid_query_error_no_query():
    """Test InvalidQueryError without query."""
    exc = InvalidQueryError(detail="Invalid query")

    assert exc.status_code == 400
    assert exc.details == {}


def test_validation_error():
    """Test ValidationError."""
    exc = ValidationError(detail="Invalid value", field="email", value="invalid-email")

    assert exc.status_code == 422
    assert exc.detail == "Invalid value"
    assert exc.error_code == "VALIDATION_ERROR"
    assert exc.details["field"] == "email"
    assert exc.details["value"] == "invalid-email"


def test_validation_error_no_field():
    """Test ValidationError without field."""
    exc = ValidationError(detail="Validation failed")

    assert exc.status_code == 422
    assert exc.details == {}


def test_permission_denied_error():
    """Test PermissionDeniedError."""
    exc = PermissionDeniedError(resource="collection", action="delete")

    assert exc.status_code == 403
    assert "collection" in exc.detail
    assert "delete" in exc.detail
    assert exc.error_code == "PERMISSION_DENIED"
    assert exc.details["resource"] == "collection"
    assert exc.details["action"] == "delete"

