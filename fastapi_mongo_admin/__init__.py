"""FastAPI Mongo Admin — Django-inspired admin for MongoDB."""

from fastapi_mongo_admin.admin import AdminSite, ModelAdmin, action, display, site
from fastapi_mongo_admin.schemas.inference import serialize_document
from fastapi_mongo_admin.utils import mount_admin_app
from fastapi_mongo_admin.views import create_admin_router

__version__ = "2.0.0"
__all__ = [
    "AdminSite",
    "ModelAdmin",
    "site",
    "display",
    "action",
    "mount_admin_app",
    "create_admin_router",
    "serialize_document",
    "__version__",
]
