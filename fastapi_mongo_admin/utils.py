"""Utility functions for admin module."""

import logging
import re
from pathlib import Path
from typing import Any, Callable, Optional, Union

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import FastAPI, APIRouter
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from motor.motor_asyncio import AsyncIOMotorDatabase


def _model_name_to_collection_name(name: str) -> str:
    """Internal helper to convert model name to collection name.
    
    Example: Product -> products, UserProfile -> user_profiles
    """
    if not name:
        return name
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    lower = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    # Simple pluralization
    if lower.endswith('y'):
        return lower[:-1] + "ies"
    if not lower.endswith('s'):
        return lower + "s"
    return lower


def get_static_directory() -> Path:
    """Get the path to the admin static files directory."""
    return Path(__file__).parent / "static"


def mount_admin_ui(app: FastAPI, mount_path: str = "/admin-ui", api_prefix: str = "/admin") -> bool:
    """Mount the admin UI static files to the FastAPI app."""
    try:
        static_dir = get_static_directory()
        if not static_dir.exists():
            return False

        admin_html_path = static_dir / "admin.html"
        if not admin_html_path.exists():
            return False

        # Read admin.html content
        admin_html_content = admin_html_path.read_text(encoding="utf-8")

        # Inject API configuration
        api_prefix_escaped = api_prefix.replace("'", "\\'").replace("\\", "\\\\")
        mount_path_escaped = mount_path.replace("'", "\\'").replace("\\", "\\\\")

        config_script = f"""
    <script>
      window.ADMIN_CONFIG = {{
        API_BASE: '{api_prefix_escaped}',
        UI_MOUNT_PATH: '{mount_path_escaped}'
      }};
    </script>
"""
        if "</head>" in admin_html_content:
            admin_html_content = admin_html_content.replace("</head>", f"{config_script}</head>")
        else:
            admin_html_content = admin_html_content.replace("<script>", f"{config_script}<script>", 1)

        @app.get(f"{mount_path}/admin.html", response_class=HTMLResponse, include_in_schema=False)
        async def serve_admin_html():
            return admin_html_content

        # Mount static files
        css_dir = static_dir / "css"
        js_dir = static_dir / "js"
        uploads_dir = static_dir / "uploads"
        uploads_dir.mkdir(parents=True, exist_ok=True)

        if css_dir.exists():
            app.mount(f"{mount_path}/css", StaticFiles(directory=str(css_dir)), name="admin-ui-css")
        if js_dir.exists():
            app.mount(f"{mount_path}/js", StaticFiles(directory=str(js_dir)), name="admin-ui-js")
        
        app.mount(f"{mount_path}/uploads", StaticFiles(directory=str(uploads_dir)), name="admin-ui-uploads")

        return True
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to mount admin UI: {e}", exc_info=True)
        return False


def mount_admin_app(
    app: FastAPI,
    get_database: Callable[[], AsyncIOMotorDatabase],
    admin_site: Optional[Any] = None,
    router_prefix: str = "/admin",
    router_tags: Optional[list[str]] = None,
    ui_mount_path: str = "/admin-ui",
    mount_ui: bool = True,
) -> APIRouter:
    """
    Mount the Django-like admin in a FastAPI application.
    
    Args:
        app: FastAPI instance
        get_database: Dependency for MongoDB connection
        admin_site: Registered AdminSite instance
        router_prefix: Prefix for API endpoints
        router_tags: Swagger tags
        ui_mount_path: Where to serve the React UI
        mount_ui: Whether to enable the UI
    """
    from fastapi_mongo_admin.router import create_router

    admin_router = create_router(
        get_database=get_database,
        prefix=router_prefix,
        tags=router_tags,
        admin_site=admin_site,
        ui_mount_path=ui_mount_path if mount_ui else None,
    )

    app.include_router(admin_router)

    if mount_ui:
        mount_admin_ui(app, mount_path=ui_mount_path, api_prefix=router_prefix)

    return admin_router


def convert_object_ids_in_query(query: dict[str, Any]) -> dict[str, Any]:
    """Convert string ObjectIds to ObjectId instances in MongoDB query."""
    if not isinstance(query, dict):
        return query

    converted = {}
    for key, value in query.items():
        if key == "_id" and isinstance(value, str):
            try:
                converted[key] = ObjectId(value)
            except (ValueError, TypeError, InvalidId):
                converted[key] = value
        elif isinstance(value, dict):
            converted[key] = {}
            for op, op_val in value.items():
                if op in ("$in", "$nin") and isinstance(op_val, list):
                    conv_list = []
                    for v in op_val:
                        if isinstance(v, str) and len(v) == 24:
                            try:
                                conv_list.append(ObjectId(v))
                            except (ValueError, TypeError, InvalidId):
                                conv_list.append(v)
                        else:
                            conv_list.append(v)
                    converted[key][op] = conv_list
                else:
                    converted[key][op] = op_val
        elif isinstance(value, list):
            conv_list = []
            for v in value:
                if isinstance(v, str) and len(v) == 24:
                    try:
                        conv_list.append(ObjectId(v))
                    except (ValueError, TypeError, InvalidId):
                        conv_list.append(v)
                else:
                    conv_list.append(v)
            converted[key] = conv_list
        else:
            converted[key] = value
    return converted
