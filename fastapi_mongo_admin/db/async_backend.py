"""Motor async collection backend."""

from __future__ import annotations

from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection


class AsyncMotorBackend:
    """Async backend wrapping Motor collection."""

    def __init__(self, collection: AsyncIOMotorCollection) -> None:
        self._collection = collection

    async def find(
        self,
        query: dict[str, Any],
        *,
        skip: int = 0,
        limit: int = 100,
        sort: list[tuple[str, int]] | None = None,
        projection: dict[str, int] | None = None,
    ) -> list[dict[str, Any]]:
        cursor = self._collection.find(query, projection)
        if sort:
            cursor = cursor.sort(sort)
        cursor = cursor.skip(skip).limit(limit)
        return await cursor.to_list(length=limit)

    async def find_one(
        self,
        query: dict[str, Any],
        projection: dict[str, int] | None = None,
    ) -> dict[str, Any] | None:
        return await self._collection.find_one(query, projection)

    async def count(self, query: dict[str, Any]) -> int:
        return await self._collection.count_documents(query)

    async def insert_one(self, document: dict[str, Any]) -> str:
        result = await self._collection.insert_one(document)
        return str(result.inserted_id)

    async def update_one(self, query: dict[str, Any], update: dict[str, Any]) -> bool:
        result = await self._collection.update_one(query, {"$set": update})
        return result.modified_count > 0 or result.matched_count > 0

    async def delete_one(self, query: dict[str, Any]) -> bool:
        result = await self._collection.delete_one(query)
        return result.deleted_count > 0

    async def delete_many(self, query: dict[str, Any]) -> int:
        result = await self._collection.delete_many(query)
        return result.deleted_count

    async def find_by_ids(self, ids: list[Any], projection: dict[str, int] | None = None) -> list[dict[str, Any]]:
        """Batch fetch documents by _id."""
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
        return await self.find({"_id": {"$in": object_ids}}, limit=len(object_ids), projection=projection)
