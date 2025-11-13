"""Pydantic models for request/response validation."""

from typing import Any

from pydantic import BaseModel, Field, field_validator


class DocumentQuery(BaseModel):
    """Model for document query parameters."""

    query: str | None = Field(None, max_length=10000, description="MongoDB query as JSON string")
    skip: int = Field(0, ge=0, le=100000, description="Number of documents to skip")
    limit: int = Field(100, ge=1, le=200, description="Maximum number of documents to return")
    sort_field: str | None = Field(None, description="Field name to sort by")
    sort_order: str = Field("asc", pattern="^(asc|desc)$", description="Sort order")

    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str | None) -> str | None:
        """Validate query string for dangerous operators.

        Args:
            v: Query string to validate

        Returns:
            Validated query string

        Raises:
            ValueError: If query contains dangerous operators
        """
        if not v:
            return v

        # Prevent dangerous MongoDB operators
        dangerous_ops = ["$where", "$eval", "$function", "$js"]
        query_lower = v.lower()
        for op in dangerous_ops:
            if op in query_lower:
                raise ValueError(f"Dangerous operator {op} is not allowed for security reasons")

        return v


class BulkCreateRequest(BaseModel):
    """Model for bulk create request."""

    documents: list[dict[str, Any]] = Field(..., min_length=1, max_length=1000)

    @field_validator("documents")
    @classmethod
    def validate_documents(cls, v: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Validate documents list.

        Args:
            v: List of documents

        Returns:
            Validated documents list

        Raises:
            ValueError: If documents list is invalid
        """
        if not isinstance(v, list):
            raise ValueError("Documents must be a list")
        if len(v) > 1000:
            raise ValueError("Cannot create more than 1000 documents at once")
        return v


class BulkUpdateRequest(BaseModel):
    """Model for bulk update request."""

    updates: list[dict[str, Any]] = Field(..., min_length=1, max_length=1000)

    @field_validator("updates")
    @classmethod
    def validate_updates(cls, v: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Validate updates list.

        Args:
            v: List of update operations

        Returns:
            Validated updates list

        Raises:
            ValueError: If updates list is invalid
        """
        if not isinstance(v, list):
            raise ValueError("Updates must be a list")
        if len(v) > 1000:
            raise ValueError("Cannot update more than 1000 documents at once")
        for update in v:
            if "_id" not in update:
                raise ValueError("Each update must have an _id field")
            if "data" not in update:
                raise ValueError("Each update must have a data field")
        return v


class BulkDeleteRequest(BaseModel):
    """Model for bulk delete request."""

    document_ids: list[str] = Field(..., min_length=1, max_length=1000)

    @field_validator("document_ids")
    @classmethod
    def validate_document_ids(cls, v: list[str]) -> list[str]:
        """Validate document IDs list.

        Args:
            v: List of document IDs

        Returns:
            Validated document IDs list

        Raises:
            ValueError: If document IDs list is invalid
        """
        if not isinstance(v, list):
            raise ValueError("Document IDs must be a list")
        if len(v) > 1000:
            raise ValueError("Cannot delete more than 1000 documents at once")
        return v


class ExportRequest(BaseModel):
    """Model for export request."""

    format: str = Field("json", pattern="^(json|yaml|csv|toml|html|xml)$")
    query: str | None = Field(None, max_length=10000)
    fields: list[str] | None = Field(None, description="Specific fields to export")


class ImportRequest(BaseModel):
    """Model for import request."""

    format: str = Field("json", pattern="^(json|yaml|csv|toml)$")
    overwrite: bool = Field(False, description="Overwrite existing documents with same _id")
