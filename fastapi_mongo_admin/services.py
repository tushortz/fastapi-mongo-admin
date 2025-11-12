"""Service layer for admin operations - business logic separation."""

import json
import logging
from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase

from fastapi_mongo_admin.pagination import get_documents_cursor
from fastapi_mongo_admin.schema import serialize_for_export, serialize_object_id

logger = logging.getLogger(__name__)


class CollectionService:
    """Service for collection operations."""

    def __init__(self, db: AsyncIOMotorDatabase):
        """Initialize collection service.

        Args:
            db: MongoDB database instance
        """
        self.db = db

    async def list_documents_optimized(
        self,
        collection_name: str,
        skip: int = 0,
        limit: int = 50,
        query: str | None = None,
        sort_field: str | None = None,
        sort_order: str = "asc",
        cursor: str | None = None,
        use_cursor: bool = False,
    ) -> dict[str, Any]:
        """List documents with optimized query using aggregation pipeline.

        Uses a single aggregation pipeline to get both documents and count,
        which is more efficient than separate find() and count_documents() calls.

        Args:
            collection_name: Name of the collection
            skip: Number of documents to skip
            limit: Maximum number of documents to return
            query: MongoDB query as JSON string or text search
            sort_field: Field name to sort by
            sort_order: Sort order ('asc' or 'desc')

        Returns:
            Dictionary with documents and total count
        """
        from fastapi_mongo_admin.router import _convert_object_ids_in_query, _get_searchable_fields

        collection = self.db[collection_name]

        # Build MongoDB query
        mongo_query = {}
        if query:
            try:
                parsed_query = json.loads(query)
                if isinstance(parsed_query, dict):
                    mongo_query = _convert_object_ids_in_query(parsed_query)
            except (json.JSONDecodeError, ValueError):
                # Text search
                searchable_fields = await _get_searchable_fields(collection)
                mongo_query = (
                    {
                        "$or": [
                            {field: {"$regex": query, "$options": "i"}} for field in searchable_fields
                        ]
                    }
                    if query
                    else {}
                )

        # Use cursor-based pagination for better performance on large datasets
        if use_cursor:
            sort_direction = 1 if sort_order == "asc" else -1
            sort_field_final = sort_field or "_id"

            cursor_result = await get_documents_cursor(
                collection=collection,
                query=mongo_query,
                cursor=cursor,
                limit=limit,
                sort_field=sort_field_final,
                sort_direction=sort_direction,
            )

            # Serialize ObjectIds
            serialized_docs = [serialize_object_id(doc) for doc in cursor_result["documents"]]

            return {
                "documents": serialized_docs,
                "next_cursor": cursor_result["next_cursor"],
                "has_more": cursor_result["has_more"],
                "limit": limit,
                "query": query,
                "pagination_type": "cursor",
            }

        # Build sort specification
        sort_spec = []
        if sort_field:
            sort_direction = 1 if sort_order == "asc" else -1
            sort_spec = [(sort_field, sort_direction)]

        # Use aggregation pipeline for optimized query
        pipeline = [{"$match": mongo_query}]

        # Add sort stage
        if sort_spec:
            pipeline.append({"$sort": {sort_spec[0][0]: sort_spec[0][1]}})

        # Use $facet to get both data and count in one query
        pipeline.append(
            {
                "$facet": {
                    "data": [{"$skip": skip}, {"$limit": limit}],
                    "total": [{"$count": "count"}],
                }
            }
        )

        result = await collection.aggregate(pipeline).to_list(length=1)
        if not result or not result[0]:
            return {"documents": [], "total": 0, "skip": skip, "limit": limit}

        facet_result = result[0]
        documents = facet_result.get("data", [])
        total_count = facet_result.get("total", [{}])[0].get("count", 0) if facet_result.get("total") else 0

        # Serialize ObjectIds
        serialized_docs = [serialize_object_id(doc) for doc in documents]

        return {
            "documents": serialized_docs,
            "total": total_count,
            "skip": skip,
            "limit": limit,
            "query": query,
            "pagination_type": "offset",
        }

    async def search_documents_optimized(
        self,
        collection_name: str,
        query: dict[str, Any],
        skip: int = 0,
        limit: int = 50,
        sort_field: str | None = None,
        sort_order: str = "asc",
    ) -> dict[str, Any]:
        """Search documents with optimized query.

        Args:
            collection_name: Name of the collection
            query: MongoDB query dictionary
            skip: Number of documents to skip
            limit: Maximum number of documents to return
            sort_field: Field name to sort by
            sort_order: Sort order ('asc' or 'desc')

        Returns:
            Dictionary with documents and total count
        """
        from fastapi_mongo_admin.router import _convert_object_ids_in_query

        collection = self.db[collection_name]

        # Convert string ObjectIds to ObjectId instances in query
        mongo_query = _convert_object_ids_in_query(query)

        # Build sort specification
        sort_spec = []
        if sort_field:
            sort_direction = 1 if sort_order == "asc" else -1
            sort_spec = [(sort_field, sort_direction)]

        # Use aggregation pipeline
        pipeline = [{"$match": mongo_query}]

        if sort_spec:
            pipeline.append({"$sort": {sort_spec[0][0]: sort_spec[0][1]}})

        pipeline.append(
            {
                "$facet": {
                    "data": [{"$skip": skip}, {"$limit": limit}],
                    "total": [{"$count": "count"}],
                }
            }
        )

        result = await collection.aggregate(pipeline).to_list(length=1)
        if not result or not result[0]:
            return {"documents": [], "total": 0, "skip": skip, "limit": limit}

        facet_result = result[0]
        documents = facet_result.get("data", [])
        total_count = facet_result.get("total", [{}])[0].get("count", 0) if facet_result.get("total") else 0

        # Serialize ObjectIds
        serialized_docs = [serialize_object_id(doc) for doc in documents]

        return {
            "documents": serialized_docs,
            "total": total_count,
            "skip": skip,
            "limit": limit,
        }

    async def bulk_create_documents(
        self, collection_name: str, documents: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Bulk insert documents for better performance.

        Args:
            collection_name: Name of the collection
            documents: List of documents to insert

        Returns:
            Dictionary with insertion results
        """
        collection = self.db[collection_name]

        # Remove _id from all documents (will be auto-generated)
        for doc in documents:
            doc.pop("_id", None)

        result = await collection.insert_many(documents)
        return {
            "inserted_count": len(result.inserted_ids),
            "inserted_ids": [str(id) for id in result.inserted_ids],
        }

    async def bulk_update_documents(
        self,
        collection_name: str,
        updates: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Bulk update documents.

        Args:
            collection_name: Name of the collection
            updates: List of update operations, each with _id and data

        Returns:
            Dictionary with update results
        """
        collection = self.db[collection_name]

        updated_count = 0
        errors = []

        for update_op in updates:
            try:
                doc_id = update_op.get("_id")
                data = update_op.get("data", {})

                if not doc_id:
                    errors.append("Missing _id in update operation")
                    continue

                # Convert string _id to ObjectId
                if isinstance(doc_id, str):
                    try:
                        doc_id = ObjectId(doc_id)
                    except (ValueError, TypeError):
                        errors.append(f"Invalid _id format: {doc_id}")
                        continue

                # Remove _id from update data
                data.pop("_id", None)

                result = await collection.replace_one({"_id": doc_id}, data)
                if result.modified_count > 0:
                    updated_count += 1
            except Exception as e:
                errors.append(f"Error updating document {update_op.get('_id')}: {str(e)}")

        return {
            "updated_count": updated_count,
            "total": len(updates),
            "errors": errors if errors else None,
        }

    async def bulk_delete_documents(
        self, collection_name: str, document_ids: list[str]
    ) -> dict[str, Any]:
        """Bulk delete documents.

        Args:
            collection_name: Name of the collection
            document_ids: List of document IDs to delete

        Returns:
            Dictionary with deletion results
        """
        collection = self.db[collection_name]

        # Convert string IDs to ObjectIds
        object_ids = []
        for doc_id in document_ids:
            try:
                object_ids.append(ObjectId(doc_id))
            except (ValueError, TypeError):
                continue

        if not object_ids:
            return {"deleted_count": 0, "total": len(document_ids)}

        result = await collection.delete_many({"_id": {"$in": object_ids}})
        return {
            "deleted_count": result.deleted_count,
            "total": len(document_ids),
        }

