"""Admin API routes for generic CRUD operations."""

import csv
import io
import json
import logging
import re
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Callable, Optional, Type, Union
from xml.dom import minidom

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import (APIRouter, Depends, FastAPI, File, HTTPException, Query,
                     Response, UploadFile, status)
from fastapi.responses import StreamingResponse
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel

from fastapi_mongo_admin.cache import (cache_result, clear_cache,
                                       get_cache_stats)
from fastapi_mongo_admin.exceptions import InvalidQueryError
from fastapi_mongo_admin.models import (BulkCreateRequest, BulkDeleteRequest,
                                        BulkUpdateRequest)
from fastapi_mongo_admin.schema import (ensure_json_serializable, infer_schema,
                                        infer_schema_from_openapi,
                                        serialize_for_export,
                                        serialize_object_id)
from fastapi_mongo_admin.services import CollectionService
from fastapi_mongo_admin.utils import convert_object_ids_in_query

# Optional dependencies - try to import but don't fail if not available
try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

try:
    import tomli
except ImportError:
    tomli = None  # type: ignore

try:
    import tomli_w
except ImportError:
    tomli_w = None  # type: ignore

logger = logging.getLogger(__name__)


def create_router(
    get_database: Callable[[], AsyncIOMotorDatabase],
    prefix: str = "/admin",
    tags: Optional[list[str]] = None,
    admin_site: Optional[Any] = None,
    app: Optional[FastAPI] = None,
    openapi_schema_map: Optional[dict[str, str]] = None,
    ui_mount_path: Optional[str] = None,
    require_auth: bool = False,
    auth_dependency: Optional[Callable] = None,
) -> APIRouter:
    """
    Create a Django-like admin router with automated Swagger documentation.
    
    This factory function generates a main router that includes dynamically
    generated sub-routers for each registered model, providing typed
    request/response schemas in OpenAPI.
    """
    if tags is None:
        tags = ["Admin"]

    # Set up authentication dependency
    if require_auth and auth_dependency:
        auth_dep = Depends(auth_dependency)
    elif require_auth:
        from fastapi_mongo_admin.auth import get_current_user
        auth_dep = Depends(get_current_user)
    else:
        auth_dep = None

    # Storage for models
    pydantic_models = admin_site.get_pydantic_models() if admin_site else {}

    # Main router
    main_router = APIRouter(prefix=prefix, tags=tags)
    main_router.admin_site = admin_site # type: ignore
    main_router.pydantic_models = pydantic_models # type: ignore

    def get_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> CollectionService:
        return CollectionService(db)

    # --- Core Admin Routes ---

    @main_router.get("/config", summary="Admin UI Configuration")
    async def get_admin_config():
        """Returns configuration for the React Admin UI."""
        return {
            "api_base": prefix,
            "prefix": prefix,
            "collections_endpoint": f"{prefix}/collections",
            "admin_ui_url": f"{ui_mount_path}/admin.html" if ui_mount_path else None,
        }

    @main_router.get("/collections", summary="Registered Collections")
    async def list_collections():
        """Returns the list of collections registered in the admin site."""
        if admin_site:
            return {"collections": admin_site.get_registered_collections()}
        return {"collections": []}

    # --- Dynamic Model-specific Routes ---

    if admin_site:
        for collection_name, model_admin in admin_site._registry.items():
            model_tags = [f"Admin: {collection_name.capitalize()}"]
            model_class = model_admin.model
            mapping = model_admin.field_mapping

            # Create a specific router for this model to get pretty Swagger docs
            model_router = APIRouter(prefix=f"/{collection_name}", tags=model_tags)

            # Register standard CRUD operations
            _register_model_crud(
                model_router, 
                collection_name, 
                model_class, 
                mapping, 
                model_admin, 
                get_service, 
                get_database,
                auth_dep
            )
            
            main_router.include_router(model_router)

    # --- UI Compatibility Layer (Legacy Paths) ---
    # These paths are used by the React UI and are hidden from Swagger
    _register_ui_compatibility_routes(main_router, admin_site, get_service, get_database, auth_dep)

    return main_router

def _register_model_crud(
    router: APIRouter,
    collection_name: str,
    model_class: Optional[Type[BaseModel]],
    mapping: Optional[dict[str, str]],
    model_admin: Any,
    get_service: Callable,
    get_database: Callable,
    auth_dep: Any,
):
    """Internal helper to add CRUD routes to a model-specific router."""
    
    @router.get("/schema", summary=f"Schema for {collection_name}")
    async def get_schema(db: AsyncIOMotorDatabase = Depends(get_database)):
        from fastapi_mongo_admin.schema import infer_schema
        schema = await infer_schema(db[collection_name], pydantic_model=model_class)
        schema["admin_config"] = {
            "list_display": model_admin.list_display,
            "search_fields": model_admin.search_fields,
            "list_filter": model_admin.list_filter,
            "list_per_page": model_admin.list_per_page,
        }
        return ensure_json_serializable(schema)

    @router.get("/", summary=f"List {collection_name}")
    async def list_docs(
        skip: int = Query(0, ge=0),
        limit: int = Query(50, ge=1, le=200),
        query: Optional[str] = None,
        sort_field: Optional[str] = None,
        sort_order: str = Query("asc", pattern="^(asc|desc)$"),
        service: CollectionService = Depends(get_service),
    ):
        return await service.list_documents_optimized(
            collection_name, skip, limit, query, sort_field, sort_order, 
            field_mapping=mapping
        )

    @router.get("/{document_id}", summary=f"Get {collection_name}")
    async def get_doc(
        document_id: str,
        db: AsyncIOMotorDatabase = Depends(get_database),
        service: CollectionService = Depends(get_service),
    ):
        try:
            collection = db[collection_name]
            doc = await collection.find_one({"_id": ObjectId(document_id)})
            if not doc:
                raise HTTPException(404, "Document not found")
            
            # Apply reverse mapping for output
            translated = service._translate_result(doc, mapping or {})
            return serialize_object_id(translated)
        except InvalidId:
            raise HTTPException(400, "Invalid document ID")

    @router.post("/", summary=f"Create {collection_name}")
    async def create_doc(
        data: dict[str, Any] if not model_class else model_class, # type: ignore
        db: AsyncIOMotorDatabase = Depends(get_database),
        service: CollectionService = Depends(get_service),
    ):
        collection = db[collection_name]
        body = data.model_dump() if hasattr(data, "model_dump") else data
        
        # Apply mapping
        if mapping:
            body = service._translate_query(body, mapping)
            
        body.pop("_id", None)
        result = await collection.insert_one(body)
        doc = await collection.find_one({"_id": result.inserted_id})
        
        # Translate back
        translated = service._translate_result(doc, mapping or {})
        return serialize_object_id(translated)

    @router.put("/{document_id}", summary=f"Update {collection_name}")
    async def update_doc(
        document_id: str,
        data: dict[str, Any] if not model_class else model_class, # type: ignore
        db: AsyncIOMotorDatabase = Depends(get_database),
        service: CollectionService = Depends(get_service),
        user=auth_dep
    ):
        collection = db[collection_name]
        body = data.model_dump(exclude_unset=True) if hasattr(data, "model_dump") else data
        
        # Apply mapping
        if mapping:
            body = service._translate_query(body, mapping)
            
        body.pop("_id", None)
        
        result = await collection.find_one_and_update(
            {"_id": ObjectId(document_id)},
            {"$set": body},
            return_document=True
        )
        if not result:
            raise HTTPException(404, "Document not found")
            
        # Translate back
        translated = service._translate_result(result, mapping or {})
        return serialize_object_id(translated)

    @router.delete("/{document_id}", summary=f"Delete {collection_name}")
    async def delete_doc(
        document_id: str,
        db: AsyncIOMotorDatabase = Depends(get_database)
    ):
        try:
            result = await db[collection_name].delete_one({"_id": ObjectId(document_id)})
            if result.deleted_count == 0:
                raise HTTPException(404, "Document not found")
            return {"message": "Deleted successfully", "id": document_id}
        except InvalidId:
            raise HTTPException(400, "Invalid document ID")

def _register_ui_compatibility_routes(router: APIRouter, admin_site, get_service, get_database, auth_dep):
    """Maintains /collections/{collection_name}/... endpoints for the React UI."""
    
    @router.get("/collections/{collection_name}/schema", include_in_schema=False)
    async def ui_get_schema(collection_name: str, db: AsyncIOMotorDatabase = Depends(get_database)):
        model_admin = admin_site.get_model_admin(collection_name) if admin_site else None
        model_class = model_admin.model if model_admin else None
        from fastapi_mongo_admin.schema import infer_schema
        schema = await infer_schema(db[collection_name], pydantic_model=model_class)
        if model_admin:
            schema["admin_config"] = {
                "list_display": model_admin.list_display,
                "search_fields": model_admin.search_fields,
                "list_filter": model_admin.list_filter,
                "list_per_page": model_admin.list_per_page,
            }
        return ensure_json_serializable(schema)

    @router.get("/collections/{collection_name}/documents", include_in_schema=False)
    async def ui_list_docs(
        collection_name: str,
        skip: int = 0,
        limit: int = 50,
        query: Optional[str] = None,
        sort_field: Optional[str] = None,
        sort_order: str = "asc",
        service: CollectionService = Depends(get_service),
    ):
        model_admin = admin_site.get_model_admin(collection_name) if admin_site else None
        mapping = model_admin.field_mapping if model_admin else None
        return await service.list_documents_optimized(
            collection_name, skip, limit, query, sort_field, sort_order, 
            field_mapping=mapping
        )

    # Simplified Detail, Create, Update for UI
    @router.get("/collections/{collection_name}/documents/{document_id}", include_in_schema=False)
    async def ui_get_doc(
        collection_name: str,
        document_id: str,
        db: AsyncIOMotorDatabase = Depends(get_database),
        service: CollectionService = Depends(get_service),
    ):
        model_admin = admin_site.get_model_admin(collection_name) if admin_site else None
        mapping = model_admin.field_mapping if model_admin else None
        doc = await db[collection_name].find_one({"_id": ObjectId(document_id)})
        if not doc: raise HTTPException(404)
        return serialize_object_id(service._translate_result(doc, mapping or {}))

    @router.post("/collections/{collection_name}/documents", include_in_schema=False)
    async def ui_create_doc(
        collection_name: str,
        data: dict[str, Any],
        db: AsyncIOMotorDatabase = Depends(get_database),
        service: CollectionService = Depends(get_service),
    ):
        model_admin = admin_site.get_model_admin(collection_name) if admin_site else None
        mapping = model_admin.field_mapping if model_admin else None
        if mapping: data = service._translate_query(data, mapping)
        data.pop("_id", None)
        result = await db[collection_name].insert_one(data)
        doc = await db[collection_name].find_one({"_id": result.inserted_id})
        return serialize_object_id(service._translate_result(doc, mapping or {}))

    @router.put("/collections/{collection_name}/documents/{document_id}", include_in_schema=False)
    async def ui_update_doc(
        collection_name: str,
        document_id: str,
        data: dict[str, Any],
        db: AsyncIOMotorDatabase = Depends(get_database),
        service: CollectionService = Depends(get_service),
    ):
        model_admin = admin_site.get_model_admin(collection_name) if admin_site else None
        mapping = model_admin.field_mapping if model_admin else None
        if mapping: data = service._translate_query(data, mapping)
        data.pop("_id", None)
        result = await db[collection_name].find_one_and_update(
            {"_id": ObjectId(document_id)}, {"$set": data}, return_document=True
        )
        if not result: raise HTTPException(404)
        return serialize_object_id(service._translate_result(result, mapping or {}))

    @router.delete("/collections/{collection_name}/documents/{document_id}", include_in_schema=False)
    async def ui_delete_doc(collection_name: str, document_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
        await db[collection_name].delete_one({"_id": ObjectId(document_id)})
        return {"status": "ok"}


async def _stream_export(
    collection: Any,
    mongo_query: dict[str, Any],
    export_format: str,
    collection_name: str,
) -> StreamingResponse:
    """Stream large exports to avoid memory issues.

    Args:
        collection: MongoDB collection
        mongo_query: MongoDB query
        export_format: Export format
        collection_name: Collection name

    Returns:
        StreamingResponse with exported data
    """

    async def generate_json():
        """Generate JSON export stream."""
        yield "[\n"
        first = True
        async for doc in collection.find(mongo_query):
            if not first:
                yield ",\n"
            first = False
            serialized = serialize_for_export(doc)
            yield json.dumps(serialized, ensure_ascii=False)
        yield "\n]"

    async def generate_csv():
        """Generate CSV export stream."""
        # Get fieldnames from first document
        first_doc = await collection.find_one(mongo_query)
        if not first_doc:
            return

        all_keys = sorted(set(first_doc.keys()))
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=all_keys, extrasaction="ignore")
        writer.writeheader()
        yield output.getvalue()
        output.seek(0)
        output.truncate(0)

        # Stream remaining documents
        async for doc in collection.find(mongo_query):
            serialized = serialize_for_export(doc)
            row = {}
            for key in all_keys:
                value = serialized.get(key, "")
                if isinstance(value, (dict, list)):
                    row[key] = json.dumps(value)
                else:
                    row[key] = str(value) if value is not None else ""
            writer.writerow(row)
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)

    if export_format == "json":
        return StreamingResponse(
            generate_json(),
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{collection_name}.json"'},
        )
    elif export_format == "csv":
        return StreamingResponse(
            generate_csv(),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{collection_name}.csv"'},
        )

    # Fallback to non-streaming for other formats
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Streaming not supported for format: {export_format}",
    )


def _dict_to_xml(data: Any, parent: Any, element_name: str = "item") -> None:
    """Convert a dictionary, list, or primitive value to XML elements.

    Args:
        data: Data to convert (dict, list, or primitive)
        parent: Parent XML element to attach children to
        element_name: Name for the XML element (used for list items and root)
    """

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
