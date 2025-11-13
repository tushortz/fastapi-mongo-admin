"""FastAPI Mongo Admin - Generic CRUD operations and admin UI for MongoDB collections."""

from fastapi_mongo_admin.schema import (
    infer_schema,
    infer_schema_from_openapi,
    infer_schema_from_pydantic,
    serialize_object_id,
)
from fastapi_mongo_admin.utils import (
    discover_pydantic_models_from_app,
    get_static_directory,
    mount_admin_app,
    mount_admin_ui,
    normalize_pydantic_models,
)

from .database import create_optimized_client
from .middleware import setup_middleware
from .router import create_router
from .auth import (
    create_token,
    validate_token,
    check_permission,
    set_auth_function,
    set_permission_checker,
    require_permission,
)

__version__ = "0.1.0"
__all__ = [
    "create_router",
    "create_optimized_client",
    "discover_pydantic_models_from_app",
    "infer_schema",
    "infer_schema_from_openapi",
    "infer_schema_from_pydantic",
    "normalize_pydantic_models",
    "serialize_object_id",
    "get_static_directory",
    "mount_admin_app",
    "mount_admin_ui",
    "setup_middleware",
    "create_token",
    "validate_token",
    "check_permission",
    "set_auth_function",
    "set_permission_checker",
    "require_permission",
]
