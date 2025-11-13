"""Cursor-based pagination utilities."""

import base64
import json
from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection


async def get_documents_cursor(
    collection: AsyncIOMotorCollection,
    query: dict[str, Any],
    cursor: str | None = None,
    limit: int = 50,
    sort_field: str = "_id",
    sort_direction: int = 1,
) -> dict[str, Any]:
    """Get documents using cursor-based pagination.

    Cursor-based pagination is more efficient than skip/limit for large datasets
    because it doesn't need to scan through skipped documents.

    Args:
        collection: MongoDB collection
        query: MongoDB query
        cursor: Last document cursor from previous page (base64 encoded JSON)
        limit: Number of documents to return
        sort_field: Field to sort by (default: _id)
        sort_direction: Sort direction (1 for ascending, -1 for descending)

    Returns:
        Dictionary with documents, next_cursor, and has_more flag
    """
    # Decode cursor if provided
    last_doc = None
    if cursor:
        try:
            decoded = base64.urlsafe_b64decode(cursor.encode())
            cursor_data = json.loads(decoded.decode())
            last_doc = cursor_data
        except (ValueError, TypeError, json.JSONDecodeError):
            # Invalid cursor, ignore it
            pass

    # Build query with cursor
    mongo_query = query.copy()

    if last_doc:
        # If sorting by _id, use simple cursor
        if sort_field == "_id":
            if sort_direction == 1:
                mongo_query["_id"] = {"$gt": ObjectId(last_doc.get("_id"))}
            else:
                mongo_query["_id"] = {"$lt": ObjectId(last_doc.get("_id"))}
        else:
            # For non-_id sort fields, use compound cursor
            sort_value = last_doc.get(sort_field)
            last_id = ObjectId(last_doc.get("_id"))

            if sort_direction == 1:
                mongo_query["$or"] = [
                    {sort_field: {"$gt": sort_value}},
                    {sort_field: sort_value, "_id": {"$gt": last_id}},
                ]
            else:
                mongo_query["$or"] = [
                    {sort_field: {"$lt": sort_value}},
                    {sort_field: sort_value, "_id": {"$lt": last_id}},
                ]

    # Fetch documents
    cursor_obj = collection.find(mongo_query).sort([(sort_field, sort_direction)]).limit(limit + 1)
    # Collect documents from cursor
    documents = []
    async for doc in cursor_obj:
        documents.append(doc)
        if len(documents) >= limit + 1:
            break

    # Check if there are more documents
    has_more = len(documents) > limit
    if has_more:
        documents = documents[:-1]  # Remove the extra document

    # Generate next cursor
    next_cursor = None
    if has_more and documents:
        last_doc = documents[-1]
        sort_value = last_doc.get(sort_field)
        # Convert ObjectId and other non-serializable types to string
        if isinstance(sort_value, ObjectId):
            sort_value = str(sort_value)
        elif sort_value is not None:
            # Try to serialize, if it fails, convert to string
            try:
                json.dumps(sort_value)
            except (TypeError, ValueError):
                sort_value = str(sort_value)

        last_doc_data = {"_id": str(last_doc["_id"]), sort_field: sort_value}
        cursor_json = json.dumps(last_doc_data)
        next_cursor = base64.urlsafe_b64encode(cursor_json.encode()).decode()

    return {
        "documents": documents,
        "next_cursor": next_cursor,
        "has_more": has_more,
        "limit": limit,
    }


def encode_cursor(document_id: str) -> str:
    """Encode document ID as cursor.

    Args:
        document_id: Document _id as string

    Returns:
        Base64 encoded cursor string
    """
    return base64.urlsafe_b64encode(document_id.encode()).decode()


def decode_cursor(cursor: str) -> str | None:
    """Decode cursor to document ID.

    Args:
        cursor: Base64 encoded cursor string

    Returns:
        Document _id as string or None if invalid
    """
    try:
        decoded = base64.urlsafe_b64decode(cursor.encode())
        return decoded.decode()
    except (ValueError, TypeError):
        return None
