"""FastAPI Mongo Admin - Generic CRUD operations and admin UI for MongoDB collections."""

from fastapi_mongo_admin.schema import infer_schema, serialize_object_id
from fastapi_mongo_admin.utils import get_static_directory, mount_admin_ui

from .router import create_router

__version__ = "0.0.1"
__all__ = [
    "create_router",
    "infer_schema",
    "serialize_object_id",
    "get_static_directory",
    "mount_admin_ui",
]
