"""Admin registry and configuration."""

from fastapi_mongo_admin.admin.decorators import action, display
from fastapi_mongo_admin.admin.model import ModelAdmin
from fastapi_mongo_admin.admin.site import AdminSite, site

__all__ = ["AdminSite", "ModelAdmin", "site", "display", "action"]
