"""PyMongo sync collection backend."""

from __future__ import annotations

from typing import Any

from bson import ObjectId
from pymongo.collection import Collection


class SyncPyMongoBackend:
    """Sync backend wrapping a PyMongo collection."""

    def __init__(self, collection: Collection) -> None:
        """Initialize the backend.

        Args:
            collection: PyMongo collection handle.
        """
        self._collection = collection

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
        cursor = self._collection.find(query, projection)
        if sort:
            cursor = cursor.sort(sort)
        return list(cursor.skip(skip).limit(limit))

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
        return self._collection.find_one(query, projection)

    def count(self, query: dict[str, Any]) -> int:
        """Count documents matching a query.

        Args:
            query: MongoDB filter document.

        Returns:
            Number of matching documents.
        """
        return self._collection.count_documents(query)

    def insert_one(self, document: dict[str, Any]) -> str:
        """Insert a document.

        Args:
            document: Document to insert.

        Returns:
            Inserted document id as a string.
        """
        result = self._collection.insert_one(document)
        return str(result.inserted_id)

    def update_one(self, query: dict[str, Any], update: dict[str, Any]) -> bool:
        """Update a single document with ``$set``.

        Args:
            query: MongoDB filter document.
            update: Fields to set on the matched document.

        Returns:
            ``True`` if a document was matched or modified.
        """
        result = self._collection.update_one(query, {"$set": update})
        return result.modified_count > 0 or result.matched_count > 0

    def delete_one(self, query: dict[str, Any]) -> bool:
        """Delete a single document.

        Args:
            query: MongoDB filter document.

        Returns:
            ``True`` if a document was deleted.
        """
        result = self._collection.delete_one(query)
        return result.deleted_count > 0

    def delete_many(self, query: dict[str, Any]) -> int:
        """Delete multiple documents.

        Args:
            query: MongoDB filter document.

        Returns:
            Number of deleted documents.
        """
        result = self._collection.delete_many(query)
        return result.deleted_count

    def find_by_ids(
        self, ids: list[Any], projection: dict[str, int] | None = None
    ) -> list[dict[str, Any]]:
        """Batch fetch documents by ``_id``.

        Args:
            ids: Iterable of document ids (``ObjectId`` or strings).
            projection: Optional field projection.

        Returns:
            List of matching documents.
        """
        object_ids = []
        for doc_id in ids:
            if isinstance(doc_id, ObjectId):
                object_ids.append(doc_id)
            else:
                try:
                    object_ids.append(ObjectId(str(doc_id)))
                except Exception:
                    continue
        if not object_ids:
            return []
        return self.find({"_id": {"$in": object_ids}}, limit=len(object_ids), projection=projection)
