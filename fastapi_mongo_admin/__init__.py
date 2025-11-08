"""FastAPI Mongo Admin - Generic CRUD operations and admin UI for MongoDB collections."""

from fastapi_mongo_admin.schema import (
    infer_schema,
    infer_schema_from_openapi,
    infer_schema_from_pydantic,
    serialize_object_id,
)
from fastapi_mongo_admin.utils import get_static_directory, mount_admin_ui

from .router import create_router

__version__ = "0.0.1"
__all__ = [
    "create_router",
    "infer_schema",
    "infer_schema_from_openapi",
    "infer_schema_from_pydantic",
    "serialize_object_id",
    "get_static_directory",
    "mount_admin_ui",
]
