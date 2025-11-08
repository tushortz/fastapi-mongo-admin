"""FastAPI Mongo Admin - Generic CRUD operations and admin UI for MongoDB collections."""

from fastapi_mongo_admin.schema import (
    infer_schema, infer_schema_from_openapi, infer_schema_from_pydantic,
    serialize_object_id,
)
from fastapi_mongo_admin.utils import (
    discover_pydantic_models_from_app, get_static_directory, mount_admin_app,
    mount_admin_ui, normalize_pydantic_models,
)

from .router import create_router

__version__ = "0.0.2"
__all__ = [
    "create_router",
    "discover_pydantic_models_from_app",
    "infer_schema",
    "infer_schema_from_openapi",
    "infer_schema_from_pydantic",
    "normalize_pydantic_models",
    "serialize_object_id",
    "get_static_directory",
    "mount_admin_app",
    "mount_admin_ui",
]
