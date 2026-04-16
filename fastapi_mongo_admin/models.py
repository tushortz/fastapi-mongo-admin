"""Pydantic models for request/response validation."""

from typing import Any

from pydantic import BaseModel, Field, field_validator


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
