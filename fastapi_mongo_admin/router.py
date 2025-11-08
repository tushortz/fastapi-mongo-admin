"""Admin API routes for generic CRUD operations."""

import json
from typing import Any, Callable

from bson import ObjectId
from fastapi import (
    APIRouter, Depends, FastAPI, HTTPException, Query, Request, status,
)
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel

from fastapi_mongo_admin.schema import (
    infer_schema, infer_schema_from_openapi, serialize_object_id,
)


def create_router(
    get_database: Callable[[], AsyncIOMotorDatabase],
    prefix: str = "/admin",
    tags: list[str] | None = None,
    pydantic_models: dict[str, type[BaseModel]] | None = None,
    app: FastAPI | None = None,
    openapi_schema_map: dict[str, str] | None = None,
) -> APIRouter:
    """Create admin router with database dependency.

    Args:
        get_database: Dependency function that returns AsyncIOMotorDatabase
        prefix: Router prefix (default: /admin)
        tags: Router tags (default: ["admin"])
        pydantic_models: Optional mapping of collection names to
            Pydantic models. Used to infer schema when collections
            are empty.
        app: Optional FastAPI app instance. If provided, will attempt
            to infer schemas from OpenAPI/Swagger documentation.
        openapi_schema_map: Optional mapping of collection names to
            OpenAPI schema names. If not provided, will try to match
            collection name to schema name.

    Returns:
        Configured APIRouter instance
    """
    if tags is None:
        tags = ["admin"]

    if pydantic_models is None:
        pydantic_models = {}

    if openapi_schema_map is None:
        openapi_schema_map = {}

    # Store pydantic_models and app for route handlers
    router = APIRouter(prefix=prefix, tags=tags)
    router.pydantic_models = pydantic_models  # type: ignore
    router.app = app  # type: ignore
    router.openapi_schema_map = openapi_schema_map  # type: ignore

    @router.get("/collections")
    async def list_collections(
        db: AsyncIOMotorDatabase = Depends(get_database)
    ):
        """List all collections in the database."""
        try:
            collections = await db.list_collection_names()
            return {"collections": collections}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to list collections: {str(e)}",
            ) from e

    @router.get("/collections/{collection_name}/schema")
    async def get_collection_schema(
        collection_name: str,
        sample_size: int = Query(default=10, ge=1, le=100),
        db: AsyncIOMotorDatabase = Depends(get_database),
        request: Request = None,  # type: ignore
    ):
        """Get schema for a collection by analyzing sample documents.

        If the collection is empty, will attempt to infer schema from:
        1. Registered Pydantic models (pydantic_models parameter)
        2. OpenAPI/Swagger documentation (if app is provided)
        3. Falls back to empty schema if none found
        """
        try:
            collection = db[collection_name]
            # Get Pydantic model for this collection if available
            pydantic_model = router.pydantic_models.get(  # type: ignore
                collection_name
            )

            # Try to infer schema from documents
            schema = await infer_schema(
                collection,
                sample_size=sample_size,
                pydantic_model=pydantic_model,
            )

            # If schema is empty, try OpenAPI to find user-defined models
            if not schema.get("fields"):
                # Try to get app from router first
                app_instance = router.app  # type: ignore

                # If not available, try to get from request
                if app_instance is None and request:
                    try:
                        # Get app from request scope
                        app_instance = request.scope.get("app")
                    except (AttributeError, KeyError):
                        pass

                if app_instance is not None:
                    # Get explicit schema mapping if provided
                    schema_map = router.openapi_schema_map  # type: ignore
                    openapi_schema_name = schema_map.get(collection_name)

                    # Try to infer schema from OpenAPI (auto-discovers models)
                    openapi_schema = infer_schema_from_openapi(
                        app_instance,
                        collection_name,
                        schema_name=openapi_schema_name,
                    )
                    if openapi_schema:
                        schema = openapi_schema

            return schema
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get schema: {str(e)}",
            ) from e

    @router.get("/collections/{collection_name}/documents")
    async def list_documents(
        collection_name: str,
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=50, ge=1, le=1000),
        query: str = Query(
            default=None,
            description="MongoDB query as JSON string or text search"
        ),
        db: AsyncIOMotorDatabase = Depends(get_database),
    ):
        """List documents in a collection with optional search query."""
        try:
            collection = db[collection_name]

            # Build MongoDB query
            mongo_query = {}
            if query:
                # Try to parse as JSON first (for advanced MongoDB queries)
                try:
                    parsed_query = json.loads(query)
                    if isinstance(parsed_query, dict):
                        mongo_query = parsed_query
                        # Convert string ObjectIds to ObjectId instances
                        mongo_query = _convert_object_ids_in_query(mongo_query)
                except (json.JSONDecodeError, ValueError):
                    # If not valid JSON, treat as text search
                    # Create a $or query to search across common string fields
                    searchable_fields = await _get_searchable_fields(
                        collection
                    )
                    mongo_query = {
                        "$or": [
                            {field: {"$regex": query, "$options": "i"}}
                            for field in searchable_fields
                        ]
                    } if query else {}

            cursor = collection.find(mongo_query).skip(skip).limit(limit)
            documents = await cursor.to_list(length=limit)
            total = await collection.count_documents(mongo_query)

            # Serialize ObjectIds
            serialized_docs = [serialize_object_id(doc) for doc in documents]

            return {
                "documents": serialized_docs,
                "total": total,
                "skip": skip,
                "limit": limit,
                "query": query,
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to list documents: {str(e)}",
            ) from e

    @router.get("/collections/{collection_name}/documents/{document_id}")
    async def get_document(
        collection_name: str,
        document_id: str,
        db: AsyncIOMotorDatabase = Depends(get_database),
    ):
        """Get a single document by ID."""
        try:
            collection = db[collection_name]
            document = await collection.find_one(
                {"_id": ObjectId(document_id)}
            )

            if document is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Document not found",
                )

            return serialize_object_id(document)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get document: {str(e)}",
            ) from e

    @router.post("/collections/{collection_name}/documents")
    async def create_document(
        collection_name: str,
        data: dict[str, Any],
        db: AsyncIOMotorDatabase = Depends(get_database),
    ):
        """Create a new document in a collection."""
        try:
            collection = db[collection_name]
            # Remove _id if present (will be auto-generated)
            data.pop("_id", None)
            result = await collection.insert_one(data)
            document = await collection.find_one({"_id": result.inserted_id})

            return serialize_object_id(document)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create document: {str(e)}",
            ) from e

    @router.put("/collections/{collection_name}/documents/{document_id}")
    async def update_document(
        collection_name: str,
        document_id: str,
        data: dict[str, Any],
        db: AsyncIOMotorDatabase = Depends(get_database),
    ):
        """Update a document by ID."""
        try:
            collection = db[collection_name]
            # Remove _id from update data
            data.pop("_id", None)

            result = await collection.find_one_and_update(
                {"_id": ObjectId(document_id)},
                {"$set": data},
                return_document=True,
            )

            if result is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Document not found",
                )

            return serialize_object_id(result)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update document: {str(e)}",
            ) from e

    @router.delete("/collections/{collection_name}/documents/{document_id}")
    async def delete_document(
        collection_name: str,
        document_id: str,
        db: AsyncIOMotorDatabase = Depends(get_database),
    ):
        """Delete a document by ID."""
        try:
            collection = db[collection_name]
            result = await collection.delete_one(
                {"_id": ObjectId(document_id)}
            )

            if result.deleted_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Document not found",
                )

            return {
                "message": "Document deleted successfully",
                "id": document_id
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete document: {str(e)}",
            ) from e

    @router.post("/collections/{collection_name}/documents/search")
    async def search_documents(
        collection_name: str,
        query: dict[str, Any],
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=50, ge=1, le=1000),
        db: AsyncIOMotorDatabase = Depends(get_database),
    ):
        """Search documents in a collection using MongoDB query.

        Args:
            collection_name: Name of the collection
            query: MongoDB query object
                (e.g., {"name": "John", "age": {"$gt": 18}})
            skip: Number of documents to skip
            limit: Maximum number of documents to return

        Returns:
            List of matching documents with pagination info
        """
        try:
            collection = db[collection_name]

            # Convert string ObjectIds to ObjectId instances in query
            mongo_query = _convert_object_ids_in_query(query)

            cursor = collection.find(mongo_query).skip(skip).limit(limit)
            documents = await cursor.to_list(length=limit)
            total = await collection.count_documents(mongo_query)

            # Serialize ObjectIds
            serialized_docs = [serialize_object_id(doc) for doc in documents]

            return {
                "documents": serialized_docs,
                "total": total,
                "skip": skip,
                "limit": limit,
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to search documents: {str(e)}",
            ) from e

    return router


def _convert_object_ids_in_query(
    query: dict[str, Any]
) -> dict[str, Any]:
    """Convert string ObjectIds to ObjectId instances in MongoDB query.

    Args:
        query: MongoDB query dictionary

    Returns:
        Query with ObjectIds converted
    """
    if not isinstance(query, dict):
        return query

    converted = {}
    for key, value in query.items():
        if key == "_id" and isinstance(value, str):
            try:
                converted[key] = ObjectId(value)
            except (ValueError, TypeError):
                converted[key] = value
        elif isinstance(value, dict):
            # Handle MongoDB operators like $in, $nin, etc.
            converted[key] = {}
            for op, op_value in value.items():
                if op in ("$in", "$nin") and isinstance(op_value, list):
                    converted[key][op] = [
                        ObjectId(v) if (
                            isinstance(v, str) and len(v) == 24 and
                            all(c in "0123456789abcdefABCDEF" for c in v)
                        ) else v
                        for v in op_value
                    ]
                elif (op == "$eq" and isinstance(op_value, str) and
                      len(op_value) == 24):
                    try:
                        converted[key][op] = ObjectId(op_value)
                    except (ValueError, TypeError):
                        converted[key][op] = op_value
                else:
                    converted[key][op] = op_value
        elif isinstance(value, list):
            converted[key] = [
                ObjectId(v) if (
                    isinstance(v, str) and len(v) == 24 and
                    all(c in "0123456789abcdefABCDEF" for c in v)
                ) else (
                    _convert_object_ids_in_query(v) if isinstance(v, dict)
                    else v
                )
                for v in value
            ]
        else:
            converted[key] = value

    return converted


async def _get_searchable_fields(collection: Any) -> list[str]:
    """Get list of searchable string fields from collection schema.

    Args:
        collection: MongoDB collection

    Returns:
        List of field names that are likely searchable (string type)
    """
    try:
        # Sample a few documents to infer string fields
        sample = await collection.find().limit(5).to_list(length=5)
        if not sample:
            return ["_id"]  # Fallback to just _id

        string_fields = set()
        for doc in sample:
            for key, value in doc.items():
                if isinstance(value, str) and key != "_id":
                    string_fields.add(key)

        return list(string_fields) if string_fields else ["_id"]
    except (ValueError, TypeError, AttributeError):
        return ["_id"]
