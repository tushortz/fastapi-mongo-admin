"""Custom exceptions for admin module."""

from typing import Any

from fastapi import HTTPException, status


class AdminException(HTTPException):
    """Base exception for admin operations."""

    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        """Initialize admin exception.

        Args:
            status_code: HTTP status code
            detail: Error message
            error_code: Optional error code for client handling
            details: Optional additional error details
        """
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code
        self.details = details or {}


class DocumentNotFoundError(AdminException):
    """Exception raised when a document is not found."""

    def __init__(self, document_id: str, collection_name: str):
        """Initialize document not found error.

        Args:
            document_id: ID of the document not found
            collection_name: Name of the collection
        """
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found in collection {collection_name}",
            error_code="DOCUMENT_NOT_FOUND",
            details={"document_id": document_id, "collection_name": collection_name},
        )


class CollectionNotFoundError(AdminException):
    """Exception raised when a collection is not found."""

    def __init__(self, collection_name: str):
        """Initialize collection not found error.

        Args:
            collection_name: Name of the collection not found
        """
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collection {collection_name} not found",
            error_code="COLLECTION_NOT_FOUND",
            details={"collection_name": collection_name},
        )


class InvalidQueryError(AdminException):
    """Exception raised when a query is invalid."""

    def __init__(self, detail: str, query: str | None = None):
        """Initialize invalid query error.

        Args:
            detail: Error message
            query: The invalid query string
        """
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code="INVALID_QUERY",
            details={"query": query} if query else {},
        )


class ValidationError(AdminException):
    """Exception raised when validation fails."""

    def __init__(self, detail: str, field: str | None = None, value: Any = None):
        """Initialize validation error.

        Args:
            detail: Error message
            field: Field name that failed validation
            value: Value that failed validation
        """
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=detail,
            error_code="VALIDATION_ERROR",
            details={"field": field, "value": value} if field else {},
        )


class PermissionDeniedError(AdminException):
    """Exception raised when permission is denied."""

    def __init__(self, resource: str, action: str):
        """Initialize permission denied error.

        Args:
            resource: Resource that access was denied to
            action: Action that was denied
        """
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied: {action} on {resource}",
            error_code="PERMISSION_DENIED",
            details={"resource": resource, "action": action},
        )
