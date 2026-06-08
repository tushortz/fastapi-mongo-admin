"""Admin registry and configuration."""

from fastapi_mongo_admin.admin.decorators import action, display
from fastapi_mongo_admin.admin.fields.widgets import FieldWidget
from fastapi_mongo_admin.admin.model import ModelAdmin
from fastapi_mongo_admin.admin.site import AdminSite, site

__all__ = ["AdminSite", "ModelAdmin", "FieldWidget", "site", "display", "action"]
