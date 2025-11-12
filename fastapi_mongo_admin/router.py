"""Admin API routes for generic CRUD operations."""

import json
from typing import Any, Callable

from bson import ObjectId
from fastapi import (
    APIRouter,
    Depends,
    FastAPI,
    File,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel

from fastapi_mongo_admin.schema import (
    infer_schema,
    infer_schema_from_openapi,
    serialize_for_export,
    serialize_object_id,
)


def create_router(
    get_database: Callable[[], AsyncIOMotorDatabase],
    prefix: str = "/admin",
    tags: list[str] | None = None,
    pydantic_models: dict[str, type[BaseModel]] | list[type[BaseModel]] | None = None,
    app: FastAPI | None = None,
    auto_discover_models: bool = True,
    openapi_schema_map: dict[str, str] | None = None,
    ui_mount_path: str | None = None,
) -> APIRouter:
    """Create admin router with database dependency.

    Args:
        get_database: Dependency function that returns AsyncIOMotorDatabase
        prefix: Router prefix (default: /admin)
        tags: Router tags (default: ["admin"])
        pydantic_models: Optional models in multiple formats:
            - dict[str, type[BaseModel]]: Explicit mapping
            - list[type[BaseModel]]: List of models (auto-detect names)
            - None: Auto-discover from app if auto_discover_models=True
        app: Optional FastAPI app instance. If provided, will attempt
            to infer schemas from OpenAPI/Swagger documentation.
        auto_discover_models: Whether to auto-discover models from app
            if pydantic_models is None (default: True)
        openapi_schema_map: Optional mapping of collection names to
            OpenAPI schema names. If not provided, will try to match
            collection name to schema name.
        ui_mount_path: Optional path where the admin UI is mounted.
            If provided, will be included in the API documentation.

    Returns:
        Configured APIRouter instance
    """
    from fastapi_mongo_admin.utils import (
        discover_pydantic_models_from_app, normalize_pydantic_models,
    )

    if tags is None:
        tags = ["mongo admin"]

    # Track if models were originally a list (for flexible matching) or dict (exact matching)
    models_were_list = isinstance(pydantic_models, list)

    # Normalize models input
    normalized_models = normalize_pydantic_models(pydantic_models)

    # Auto-discover models from app if enabled and no models provided
    if auto_discover_models and not normalized_models and app is not None:
        discovered_models = discover_pydantic_models_from_app(app)
        if discovered_models:
            normalized_models = discovered_models
            # Auto-discovered models should use flexible matching
            models_were_list = True

    # Use normalized models or empty dict
    pydantic_models = normalized_models if normalized_models else {}

    if openapi_schema_map is None:
        openapi_schema_map = {}

    # Store pydantic_models and app for route handlers
    router = APIRouter(prefix=prefix, tags=tags)
    router.pydantic_models = pydantic_models  # type: ignore
    router.app = app  # type: ignore
    router.openapi_schema_map = openapi_schema_map  # type: ignore
    router._models_were_list = models_were_list  # type: ignore
    router.ui_mount_path = ui_mount_path  # type: ignore

    @router.get(
        "/",
        summary="Admin Router Information",
        description=(
            "Get admin router information including API endpoints and admin UI URL. "
            "Use this endpoint to discover available admin functionality."
        ),
        responses={
            200: {
                "description": "Admin router information",
                "content": {
                    "application/json": {
                        "example": {
                            "prefix": "/admin",
                            "collections_endpoint": "/admin/collections",
                            "status": "ok",
                            "admin_ui_url": "/admin-ui/admin.html",
                        }
                    }
                },
            }
        },
    )
    async def admin_info():
        """Get admin router information for API discovery.

        Returns information about the admin router including:
        - API prefix
        - Collections endpoint
        - Admin UI URL (if mounted)
        """
        response = {
            "prefix": prefix,
            "collections_endpoint": f"{prefix}/collections",
            "status": "ok",
        }

        # Add admin UI URL if mount path is provided
        if ui_mount_path:
            response["admin_ui_url"] = f"{ui_mount_path}/admin.html"

        return response

    @router.get("/config")
    async def get_admin_config():
        """Get admin configuration including API base path.

        This endpoint is used by the admin UI to discover the correct API base path.
        """
        return {
            "api_base": prefix,
            "prefix": prefix,
            "collections_endpoint": f"{prefix}/collections",
            "admin_ui_url": f"{ui_mount_path}/admin.html" if ui_mount_path else None,
        }

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
        """Get schema for a collection from Pydantic models only.

        Schema inference priority:
        1. Registered Pydantic models (pydantic_models parameter)
        2. OpenAPI/Swagger documentation (if app is provided)
        3. Falls back to empty schema if none found

        Note: Schema is NOT inferred from MongoDB documents.
        Only Pydantic models are used for datatype inference.
        """
        try:
            collection = db[collection_name]
            import logging

            logger = logging.getLogger(__name__)

            # Get Pydantic model for this collection if available
            pydantic_models_dict = router.pydantic_models  # type: ignore
            models_were_list = getattr(router, "_models_were_list", False)  # type: ignore
            pydantic_model = None

            if pydantic_models_dict:
                # Try exact match first
                pydantic_model = pydantic_models_dict.get(collection_name)

                # If not found, try case-insensitive match
                if pydantic_model is None:
                    collection_lower = collection_name.lower()
                    for key, model in pydantic_models_dict.items():
                        if key.lower() == collection_lower:
                            pydantic_model = model
                            break

                # Only do flexible matching (plural/singular conversion) if models were originally a list
                # If a dict was passed, respect the exact keys provided
                if pydantic_model is None and models_were_list:
                    # Try singular/plural variations
                    # Try removing 's' (plural -> singular)
                    if collection_name.endswith("s") and len(collection_name) > 1:
                        singular = collection_name[:-1]
                        pydantic_model = pydantic_models_dict.get(singular)
                        # Also try capitalized version
                        if pydantic_model is None:
                            singular_cap = singular.capitalize()
                            pydantic_model = pydantic_models_dict.get(singular_cap)

                    # Try adding 's' (singular -> plural)
                    if pydantic_model is None:
                        plural = collection_name + "s"
                        pydantic_model = pydantic_models_dict.get(plural)

                    # Try model name to collection name conversion in reverse
                    if pydantic_model is None:
                        from fastapi_mongo_admin.utils import (
                            _model_name_to_collection_name,
                        )

                        for key, model in pydantic_models_dict.items():
                            # Convert model name to collection name and compare
                            inferred_collection = _model_name_to_collection_name(key)
                            if inferred_collection.lower() == collection_name.lower():
                                pydantic_model = model
                                break

            schema = {"fields": {}, "sample_count": 0}

            # Try to infer schema from registered Pydantic model first
            if pydantic_model is not None:
                try:
                    schema = await infer_schema(
                        collection,
                        _sample_size=sample_size,
                        pydantic_model=pydantic_model,
                    )
                    if schema.get("fields"):
                        logger.info(
                            "Successfully inferred schema from Pydantic model for "
                            "collection '%s' (found %d fields)",
                            collection_name,
                            len(schema.get("fields", {})),
                        )
                    else:
                        logger.warning(
                            "Pydantic model found for collection '%s' but schema "
                            "inference returned no fields",
                            collection_name,
                        )
                except Exception as e:
                    # If Pydantic inference fails, log and continue to OpenAPI
                    logger.error(
                        "Failed to infer schema from Pydantic model for " "collection '%s': %s",
                        collection_name,
                        str(e),
                        exc_info=True,
                    )
                    schema = {"fields": {}, "sample_count": 0}
            else:
                logger.debug(
                    "No Pydantic model registered for collection '%s' in " "pydantic_models dict",
                    collection_name,
                )

            # If schema is still empty, try OpenAPI (explicit mapping first, then auto-discovery)
            if not schema.get("fields"):
                # Get app from router (should be set when creating router)
                app_instance = router.app  # type: ignore

                if app_instance is not None:
                    # Get explicit schema mapping if provided (priority)
                    schema_map = router.openapi_schema_map  # type: ignore
                    openapi_schema_name = schema_map.get(collection_name) if schema_map else None

                    # Try to infer schema from OpenAPI
                    # First try explicit mapping, then auto-discovery
                    try:
                        openapi_schema = infer_schema_from_openapi(
                            app_instance,
                            collection_name,
                            schema_name=openapi_schema_name,  # None triggers auto-discovery
                        )
                        if openapi_schema and openapi_schema.get("fields"):
                            schema = openapi_schema
                            source = "explicit mapping" if openapi_schema_name else "auto-discovery"
                            logger.info(
                                "Successfully inferred schema from OpenAPI for "
                                "collection '%s' via %s (found %d fields)",
                                collection_name,
                                source,
                                len(openapi_schema.get("fields", {})),
                            )
                        else:
                            if openapi_schema_name:
                                logger.warning(
                                    "OpenAPI schema '%s' not found or has no fields "
                                    "for collection '%s'",
                                    openapi_schema_name,
                                    collection_name,
                                )
                            else:
                                logger.debug(
                                    "No matching OpenAPI schema found via "
                                    "auto-discovery for collection '%s'",
                                    collection_name,
                                )
                    except Exception as e:
                        # Log OpenAPI inference failure but don't fail the request
                        logger.error(
                            "Failed to infer schema from OpenAPI for " "collection '%s': %s",
                            collection_name,
                            str(e),
                            exc_info=True,
                        )
                else:
                    logger.debug(
                        "No FastAPI app instance available for OpenAPI schema "
                        "discovery. Pass app parameter to create_router() to enable "
                        "auto-discovery."
                    )

            # Add diagnostic info to schema response for debugging
            if not schema.get("fields"):
                # Get schema_map for diagnostics
                schema_map = router.openapi_schema_map  # type: ignore
                app_instance = router.app  # type: ignore

                logger.warning(
                    "Schema detection failed for collection '%s'. "
                    "Registered models: %s, OpenAPI mappings: %s, App available: %s",
                    collection_name,
                    list(pydantic_models_dict.keys()) if pydantic_models_dict else [],
                    list(schema_map.keys()) if schema_map else [],
                    app_instance is not None,
                )
                # Include diagnostic info in response
                schema["_diagnostic"] = {
                    "collection_name": collection_name,
                    "has_pydantic_models": bool(pydantic_models_dict),
                    "registered_models": (
                        list(pydantic_models_dict.keys()) if pydantic_models_dict else []
                    ),
                    "has_openapi_map": bool(schema_map),
                    "openapi_mappings": dict(schema_map) if schema_map else {},
                    "has_app": app_instance is not None,
                    "pydantic_model_found": pydantic_model is not None,
                }

            return schema
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.exception("Error in get_collection_schema")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get schema: {str(e)}",
            ) from e

    @router.get("/collections/{collection_name}/documents")
    async def list_documents(
        collection_name: str,
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=50, ge=1, le=1000),
        query: str = Query(default=None, description="MongoDB query as JSON string or text search"),
        sort_field: str = Query(default=None, description="Field name to sort by"),
        sort_order: str = Query(
            default="asc", description="Sort order: 'asc' or 'desc'", pattern="^(asc|desc)$"
        ),
        db: AsyncIOMotorDatabase = Depends(get_database),
    ):
        """List documents in a collection with optional search query and sorting."""
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
                    searchable_fields = await _get_searchable_fields(collection)
                    mongo_query = (
                        {
                            "$or": [
                                {field: {"$regex": query, "$options": "i"}}
                                for field in searchable_fields
                            ]
                        }
                        if query
                        else {}
                    )

            # Build sort specification
            sort_spec = []
            if sort_field:
                sort_direction = 1 if sort_order == "asc" else -1
                sort_spec = [(sort_field, sort_direction)]

            cursor = collection.find(mongo_query)
            if sort_spec:
                cursor = cursor.sort(sort_spec)
            cursor = cursor.skip(skip).limit(limit)
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

    @router.post("/collections/{collection_name}/documents/search")
    async def search_documents(
        collection_name: str,
        query: dict[str, Any],
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=50, ge=1, le=1000),
        sort_field: str = Query(default=None, description="Field name to sort by"),
        sort_order: str = Query(
            default="asc", description="Sort order: 'asc' or 'desc'", pattern="^(asc|desc)$"
        ),
        db: AsyncIOMotorDatabase = Depends(get_database),
    ):
        """Search documents in a collection using MongoDB query.

        Args:
            collection_name: Name of the collection
            query: MongoDB query object
                (e.g., {"name": "John", "age": {"$gt": 18}})
            skip: Number of documents to skip
            limit: Maximum number of documents to return
            sort_field: Field name to sort by
            sort_order: Sort order: 'asc' or 'desc'

        Returns:
            List of matching documents with pagination info
        """
        try:
            collection = db[collection_name]

            # Convert string ObjectIds to ObjectId instances in query
            mongo_query = _convert_object_ids_in_query(query)

            # Build sort specification
            sort_spec = []
            if sort_field:
                sort_direction = 1 if sort_order == "asc" else -1
                sort_spec = [(sort_field, sort_direction)]

            cursor = collection.find(mongo_query)
            if sort_spec:
                cursor = cursor.sort(sort_spec)
            cursor = cursor.skip(skip).limit(limit)
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

    @router.get("/collections/{collection_name}/fields/{field_name}/autocomplete")
    async def get_field_autocomplete(
        collection_name: str,
        field_name: str,
        query: str = Query(default="", min_length=3),
        limit: int = Query(default=10, ge=1, le=50),
        db: AsyncIOMotorDatabase = Depends(get_database),
    ):
        """Get autocomplete suggestions for a field based on previous records.

        Args:
            collection_name: Name of the collection
            field_name: Name of the field to get suggestions for
            query: Search query (minimum 3 characters)
            limit: Maximum number of suggestions to return

        Returns:
            List of unique field values matching the query
        """
        try:
            collection = db[collection_name]

            # Get distinct values for the field that match the query
            match_stage = {
                field_name: {"$exists": True, "$ne": None, "$regex": f"^{query}", "$options": "i"}
            }

            pipeline = [
                {"$match": match_stage},
                {"$group": {"_id": f"${field_name}"}},
                {"$sort": {"_id": 1}},
                {"$limit": limit},
            ]

            cursor = collection.aggregate(pipeline)
            results = await cursor.to_list(length=limit)

            # Extract values and filter out None/null
            suggestions = [item["_id"] for item in results if item.get("_id") is not None]

            # Convert to strings and ensure uniqueness
            unique_suggestions = list(dict.fromkeys(str(s) for s in suggestions))

            return {"suggestions": unique_suggestions[:limit]}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get autocomplete: {str(e)}",
            ) from e

    @router.get("/collections/{collection_name}/analytics")
    async def get_collection_analytics(
        collection_name: str,
        field: str = Query(..., description="Field name to aggregate"),
        group_by: str = Query(
            default=None, description="Optional field to group by (for time series or categories)"
        ),
        aggregation_type: str = Query(
            default="count", description="Type of aggregation: count, sum, avg, min, max"
        ),
        limit: int = Query(default=100, ge=1, le=1000),
        db: AsyncIOMotorDatabase = Depends(get_database),
    ):
        """Get analytics data for a collection field.

        Args:
            collection_name: Name of the collection
            field: Field name to aggregate
            group_by: Optional field to group by (e.g., date field for time series)
            aggregation_type: Type of aggregation (count, sum, avg, min, max)
            limit: Maximum number of results to return

        Returns:
            Aggregated data suitable for charting
        """
        try:
            collection = db[collection_name]

            # Build aggregation pipeline
            pipeline = []

            # Match stage to filter out null values
            match_conditions = {field: {"$exists": True, "$ne": None}}
            if group_by:
                match_conditions[group_by] = {"$exists": True, "$ne": None}
            pipeline.append({"$match": match_conditions})

            # Group stage
            if group_by:
                # When group_by is specified, group by the group_by field
                # and aggregate the field values
                group_stage = {"_id": f"${group_by}"}
            else:
                # Group by field only (for counting occurrences or aggregating)
                group_stage = {"_id": f"${field}"}

            # Add aggregation based on type
            if aggregation_type == "count":
                group_stage["count"] = {"$sum": 1}
            elif aggregation_type == "sum":
                # Only sum if field is numeric
                group_stage["sum"] = {"$sum": f"${field}"}
            elif aggregation_type == "avg":
                group_stage["avg"] = {"$avg": f"${field}"}
            elif aggregation_type == "min":
                group_stage["min"] = {"$min": f"${field}"}
            elif aggregation_type == "max":
                group_stage["max"] = {"$max": f"${field}"}
            else:
                group_stage["count"] = {"$sum": 1}

            pipeline.append({"$group": group_stage})

            # Sort and limit
            pipeline.append({"$sort": {"_id": 1}})
            pipeline.append({"$limit": limit})

            # Execute aggregation
            cursor = collection.aggregate(pipeline)
            results = await cursor.to_list(length=limit)

            # Format results for charting
            formatted_results = []
            for item in results:
                if group_by:
                    # When grouped, label is the group_by value
                    # and data is the aggregated field value
                    formatted_results.append(
                        {
                            "label": str(item["_id"]),
                            "data": item.get("count")
                            or item.get("sum")
                            or item.get("avg")
                            or item.get("min")
                            or item.get("max", 0),
                        }
                    )
                else:
                    # When not grouped, label is the field value
                    # and data is the aggregation result
                    formatted_results.append(
                        {
                            "label": str(item["_id"]),
                            "data": item.get("count")
                            or item.get("sum")
                            or item.get("avg")
                            or item.get("min")
                            or item.get("max", 0),
                        }
                    )

            return {
                "field": field,
                "group_by": group_by,
                "aggregation_type": aggregation_type,
                "data": formatted_results,
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get analytics: {str(e)}",
            ) from e

    @router.get("/collections/{collection_name}/export")
    async def export_collection(
        collection_name: str,
        export_format: str = Query(
            default="json",
            description="Export format: json, yaml, csv, toml, html, xml",
            pattern="^(json|yaml|csv|toml|html|xml)$",
            alias="format",
        ),
        query: str = Query(default=None, description="MongoDB query as JSON string"),
        db: AsyncIOMotorDatabase = Depends(get_database),
    ):
        """Export collection documents in various formats."""
        try:
            import io

            from fastapi import Response

            collection = db[collection_name]

            # Build MongoDB query
            mongo_query = {}
            if query:
                try:
                    parsed_query = json.loads(query)
                    if isinstance(parsed_query, dict):
                        mongo_query = _convert_object_ids_in_query(parsed_query)
                except (json.JSONDecodeError, ValueError):
                    pass

            # Fetch all documents matching query
            cursor = collection.find(mongo_query)
            documents = await cursor.to_list(length=None)

            # Serialize MongoDB types (ObjectId, datetime, etc.) for export
            serialized_docs = [serialize_for_export(doc) for doc in documents]

            # Initialize variables
            content = ""
            media_type = "application/json"
            filename = f"{collection_name}.json"

            # Export based on format
            if export_format == "json":
                content = json.dumps(serialized_docs, indent=2, ensure_ascii=False)
                media_type = "application/json"
                filename = f"{collection_name}.json"

            elif export_format == "yaml":
                try:
                    import yaml

                    content = yaml.dump(
                        serialized_docs, default_flow_style=False, allow_unicode=True
                    )
                    media_type = "application/x-yaml"
                    filename = f"{collection_name}.yaml"
                except ImportError as exc:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="PyYAML is required for YAML export. Install with: pip install pyyaml",
                    ) from exc

            elif export_format == "csv":
                if not serialized_docs:
                    content = ""
                else:
                    import csv

                    output = io.StringIO()
                    # Get all unique keys from all documents
                    all_keys = set()
                    for doc in serialized_docs:
                        all_keys.update(doc.keys())
                    fieldnames = sorted(all_keys)

                    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
                    writer.writeheader()
                    for doc in serialized_docs:
                        # Convert complex types to strings
                        row = {}
                        for key in fieldnames:
                            value = doc.get(key, "")
                            if isinstance(value, (dict, list)):
                                row[key] = json.dumps(value)
                            else:
                                row[key] = str(value) if value is not None else ""
                        writer.writerow(row)
                    content = output.getvalue()
                media_type = "text/csv"
                filename = f"{collection_name}.csv"

            elif export_format == "toml":
                try:
                    import tomli_w

                    # TOML doesn't support arrays of tables directly, so we'll use a wrapper
                    toml_data = {"documents": serialized_docs}
                    content = tomli_w.dumps(toml_data)
                    media_type = "application/toml"
                    filename = f"{collection_name}.toml"
                except ImportError as exc:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="tomli-w is required for TOML export. Install with: pip install tomli-w",
                    ) from exc

            elif export_format == "html":
                # Generate HTML table
                if not serialized_docs:
                    content = "<html><body><p>No documents found</p></body></html>"
                else:
                    all_keys = set()
                    for doc in serialized_docs:
                        all_keys.update(doc.keys())
                    keys = sorted(all_keys)

                    html = ["<html><head><title>Export</title>"]
                    html.append("<style>")
                    html.append("table { border-collapse: collapse; width: 100%; }")
                    html.append(
                        "th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }"
                    )
                    html.append("th { background-color: #f2f2f2; }")
                    html.append("</style></head><body>")
                    html.append(f"<h1>{collection_name}</h1>")
                    html.append(f"<p>Total documents: {len(serialized_docs)}</p>")
                    html.append("<table>")
                    html.append("<thead><tr>")
                    for key in keys:
                        html.append(f"<th>{key}</th>")
                    html.append("</tr></thead><tbody>")

                    for doc in serialized_docs:
                        html.append("<tr>")
                        for key in keys:
                            value = doc.get(key, "")
                            if isinstance(value, (dict, list)):
                                value_str = json.dumps(value)
                            else:
                                value_str = str(value) if value is not None else ""
                            html.append(f"<td>{value_str}</td>")
                        html.append("</tr>")

                    html.append("</tbody></table></body></html>")
                    content = "\n".join(html)
                media_type = "text/html"
                filename = f"{collection_name}.html"

            elif export_format == "xml":
                import xml.etree.ElementTree as ET
                from xml.dom import minidom

                # Create root element
                root = ET.Element("collection")
                root.set("name", collection_name)
                root.set("count", str(len(serialized_docs)))

                # Add documents
                for doc in serialized_docs:
                    doc_elem = ET.SubElement(root, "document")
                    _dict_to_xml(doc, doc_elem)

                # Convert to string with pretty formatting
                rough_string = ET.tostring(root, encoding="unicode")
                reparsed = minidom.parseString(rough_string)
                content = reparsed.toprettyxml(indent="  ")
                media_type = "application/xml"
                filename = f"{collection_name}.xml"
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported export format: {export_format}",
                )

            return Response(
                content=content.encode("utf-8"),
                media_type=media_type,
                headers={"Content-Disposition": f'attachment; filename="{filename}"'},
            )

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to export collection: {str(e)}",
            ) from e

    @router.post("/collections/{collection_name}/import")
    async def import_collection(
        collection_name: str,
        file: UploadFile = File(...),
        import_format: str = Query(
            default="json",
            description="Import format: json, yaml, csv, toml",
            pattern="^(json|yaml|csv|toml)$",
            alias="format",
        ),
        overwrite: bool = Query(
            default=False, description="Overwrite existing documents with same _id"
        ),
        db: AsyncIOMotorDatabase = Depends(get_database),
    ):
        """Import documents into a collection from various formats."""
        try:
            collection = db[collection_name]
            content = await file.read()
            text_content = content.decode("utf-8")

            documents = []

            if import_format == "json":
                try:
                    data = json.loads(text_content)
                    if isinstance(data, list):
                        documents = data
                    elif isinstance(data, dict):
                        documents = [data]
                    else:
                        raise ValueError("JSON must be an object or array")
                except json.JSONDecodeError as e:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid JSON: {str(e)}",
                    ) from e

            elif import_format == "yaml":
                try:
                    import yaml

                    data = yaml.safe_load(text_content)
                    if isinstance(data, list):
                        documents = data
                    elif isinstance(data, dict):
                        # Check if it's a single document or wrapper
                        if "documents" in data and isinstance(data["documents"], list):
                            documents = data["documents"]
                        else:
                            documents = [data]
                    else:
                        raise ValueError("YAML must be an object or array")
                except ImportError as exc:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="PyYAML is required for YAML import. Install with: pip install pyyaml",
                    ) from exc
                except yaml.YAMLError as e:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid YAML: {str(e)}",
                    ) from e

            elif import_format == "csv":
                import csv
                import io

                reader = csv.DictReader(io.StringIO(text_content))
                for row in reader:
                    # Parse JSON strings back to objects
                    doc = {}
                    for key, value in row.items():
                        if value:
                            # Try to parse as JSON first
                            try:
                                doc[key] = json.loads(value)
                            except (json.JSONDecodeError, ValueError):
                                # Keep as string
                                doc[key] = value
                        else:
                            doc[key] = None
                    documents.append(doc)

            elif import_format == "toml":
                try:
                    import tomli

                    data = tomli.loads(text_content)
                    if "documents" in data and isinstance(data["documents"], list):
                        documents = data["documents"]
                    elif isinstance(data, dict):
                        documents = [data]
                    else:
                        raise ValueError("TOML must contain documents array or be an object")
                except ImportError as exc:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="tomli is required for TOML import. Install with: pip install tomli",
                    ) from exc
                except Exception as e:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid TOML: {str(e)}",
                    ) from e
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported import format: {import_format}",
                )

            if not documents:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No documents found in file",
                )

            # Process documents
            inserted_count = 0
            updated_count = 0
            errors = []

            for doc in documents:
                try:
                    # Convert string _id to ObjectId if present
                    if "_id" in doc:
                        if isinstance(doc["_id"], str):
                            try:
                                doc["_id"] = ObjectId(doc["_id"])
                            except (ValueError, TypeError):
                                pass

                    if "_id" in doc and overwrite:
                        # Update existing document
                        result = await collection.replace_one({"_id": doc["_id"]}, doc, upsert=True)
                        if result.upserted_id:
                            inserted_count += 1
                        else:
                            updated_count += 1
                    else:
                        # Insert new document (remove _id if present to let MongoDB generate it)
                        doc_id = doc.pop("_id", None)
                        result = await collection.insert_one(doc)
                        inserted_count += 1
                        if doc_id:
                            doc["_id"] = doc_id

                except Exception as e:
                    errors.append(f"Error processing document: {str(e)}")

            return {
                "message": "Import completed",
                "inserted": inserted_count,
                "updated": updated_count,
                "total": len(documents),
                "errors": errors if errors else None,
            }

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to import collection: {str(e)}",
            ) from e

    return router


def _dict_to_xml(data: Any, parent: Any, element_name: str = "item") -> None:
    """Convert a dictionary, list, or primitive value to XML elements.

    Args:
        data: Data to convert (dict, list, or primitive)
        parent: Parent XML element to attach children to
        element_name: Name for the XML element (used for list items and root)
    """
    import re
    import xml.etree.ElementTree as ET

    def sanitize_xml_name(name: str) -> str:
        """Sanitize a string to be a valid XML element name."""
        # XML element names must start with a letter or underscore
        # and can contain letters, digits, hyphens, underscores, and periods
        if not name:
            return "item"
        # Replace invalid characters with underscore
        name = re.sub(r"[^a-zA-Z0-9_\-.]", "_", name)
        # Ensure it starts with a letter or underscore
        if name and name[0].isdigit():
            name = "_" + name
        return name or "item"

    if isinstance(data, dict):
        for key, value in data.items():
            sanitized_key = sanitize_xml_name(str(key))
            child = ET.SubElement(parent, sanitized_key)
            _dict_to_xml(value, child)
    elif isinstance(data, list):
        for item in data:
            child = ET.SubElement(parent, element_name)
            _dict_to_xml(item, child)
    else:
        # Primitive value (string, number, boolean, None)
        if data is None:
            parent.text = ""
        else:
            parent.text = str(data)


def _convert_object_ids_in_query(query: dict[str, Any]) -> dict[str, Any]:
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
                        (
                            ObjectId(v)
                            if (
                                isinstance(v, str)
                                and len(v) == 24
                                and all(c in "0123456789abcdefABCDEF" for c in v)
                            )
                            else v
                        )
                        for v in op_value
                    ]
                elif op == "$eq" and isinstance(op_value, str) and len(op_value) == 24:
                    try:
                        converted[key][op] = ObjectId(op_value)
                    except (ValueError, TypeError):
                        converted[key][op] = op_value
                else:
                    converted[key][op] = op_value
        elif isinstance(value, list):
            converted[key] = [
                (
                    ObjectId(v)
                    if (
                        isinstance(v, str)
                        and len(v) == 24
                        and all(c in "0123456789abcdefABCDEF" for c in v)
                    )
                    else (_convert_object_ids_in_query(v) if isinstance(v, dict) else v)
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
