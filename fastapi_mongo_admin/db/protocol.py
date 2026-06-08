"""Database backend protocols."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class AsyncCollectionBackend(Protocol):
    """Async MongoDB collection operations protocol."""

    async def find(
        self,
        query: dict[str, Any],
        *,
        skip: int = 0,
        limit: int = 100,
        sort: list[tuple[str, int]] | None = None,
        projection: dict[str, int] | None = None,
    ) -> list[dict[str, Any]]:
        """Find documents matching a query.

        Args:
            query: MongoDB filter document.
            skip: Number of documents to skip.
            limit: Maximum documents to return.
            sort: Optional list of ``(field, direction)`` pairs.
            projection: Optional field projection.

        Returns:
            List of matching documents.
        """

    async def find_one(
        self,
        query: dict[str, Any],
        projection: dict[str, int] | None = None,
    ) -> dict[str, Any] | None:
        """Find a single document.

        Args:
            query: MongoDB filter document.
            projection: Optional field projection.

        Returns:
            Matching document or ``None``.
        """

    async def count(self, query: dict[str, Any]) -> int:
        """Count documents matching a query.

        Args:
            query: MongoDB filter document.

        Returns:
            Number of matching documents.
        """

    async def insert_one(self, document: dict[str, Any]) -> str:
        """Insert a document.

        Args:
            document: Document to insert.

        Returns:
            Inserted document id as a string.
        """

    async def update_one(self, query: dict[str, Any], update: dict[str, Any]) -> bool:
        """Update a single document with ``$set``.

        Args:
            query: MongoDB filter document.
            update: Fields to set on the matched document.

        Returns:
            ``True`` if a document was matched or modified.
        """

    async def delete_one(self, query: dict[str, Any]) -> bool:
        """Delete a single document.

        Args:
            query: MongoDB filter document.

        Returns:
            ``True`` if a document was deleted.
        """

    async def delete_many(self, query: dict[str, Any]) -> int:
        """Delete multiple documents.

        Args:
            query: MongoDB filter document.

        Returns:
            Number of deleted documents.
        """


@runtime_checkable
class SyncCollectionBackend(Protocol):
    """Sync MongoDB collection operations protocol."""

    def find(
        self,
        query: dict[str, Any],
        *,
        skip: int = 0,
        limit: int = 100,
        sort: list[tuple[str, int]] | None = None,
        projection: dict[str, int] | None = None,
    ) -> list[dict[str, Any]]:
        """Find documents matching a query.

        Args:
            query: MongoDB filter document.
            skip: Number of documents to skip.
            limit: Maximum documents to return.
            sort: Optional list of ``(field, direction)`` pairs.
            projection: Optional field projection.

        Returns:
            List of matching documents.
        """

    def find_one(
        self,
        query: dict[str, Any],
        projection: dict[str, int] | None = None,
    ) -> dict[str, Any] | None:
        """Find a single document.

        Args:
            query: MongoDB filter document.
            projection: Optional field projection.

        Returns:
            Matching document or ``None``.
        """

    def count(self, query: dict[str, Any]) -> int:
        """Count documents matching a query.

        Args:
            query: MongoDB filter document.

        Returns:
            Number of matching documents.
        """

    def insert_one(self, document: dict[str, Any]) -> str:
        """Insert a document.

        Args:
            document: Document to insert.

        Returns:
            Inserted document id as a string.
        """

    def update_one(self, query: dict[str, Any], update: dict[str, Any]) -> bool:
        """Update a single document with ``$set``.

        Args:
            query: MongoDB filter document.
            update: Fields to set on the matched document.

        Returns:
            ``True`` if a document was matched or modified.
        """

    def delete_one(self, query: dict[str, Any]) -> bool:
        """Delete a single document.

        Args:
            query: MongoDB filter document.

        Returns:
            ``True`` if a document was deleted.
        """

    def delete_many(self, query: dict[str, Any]) -> int:
        """Delete multiple documents.

        Args:
            query: MongoDB filter document.

        Returns:
            Number of deleted documents.
        """
