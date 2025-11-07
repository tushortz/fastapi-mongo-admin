"""Admin API routes for generic CRUD operations."""

from typing import Any, Callable

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from fastapi_mongo_admin.schema import infer_schema, serialize_object_id


def create_router(
    get_database: Callable[[], AsyncIOMotorDatabase],
    prefix: str = "/admin",
    tags: list[str] | None = None,
) -> APIRouter:
    """Create admin router with database dependency.

    Args:
        get_database: Dependency function that returns AsyncIOMotorDatabase
        prefix: Router prefix (default: /admin)
        tags: Router tags (default: ["admin"])

    Returns:
        Configured APIRouter instance
    """
    if tags is None:
        tags = ["admin"]

    router = APIRouter(prefix=prefix, tags=tags)

    @router.get("/collections")
    async def list_collections(db: AsyncIOMotorDatabase = Depends(get_database)):
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
    ):
        """Get schema for a collection by analyzing sample documents."""
        try:
            collection = db[collection_name]
            schema = await infer_schema(collection, sample_size=sample_size)
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
        db: AsyncIOMotorDatabase = Depends(get_database),
    ):
        """List documents in a collection."""
        try:
            collection = db[collection_name]
            cursor = collection.find().skip(skip).limit(limit)
            documents = await cursor.to_list(length=limit)
            total = await collection.count_documents({})

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
            document = await collection.find_one({"_id": ObjectId(document_id)})

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
            result = await collection.delete_one({"_id": ObjectId(document_id)})

            if result.deleted_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Document not found",
                )

            return {"message": "Document deleted successfully", "id": document_id}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete document: {str(e)}",
            ) from e

    return router
