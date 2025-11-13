"""Utility functions for admin module."""

import inspect
import logging
import re
import sys
from pathlib import Path
from typing import Any, Callable

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.routing import APIRoute
from fastapi.staticfiles import StaticFiles
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel


def discover_pydantic_models_from_app(
    app: FastAPI,
) -> dict[str, type[BaseModel]]:
    """Automatically discover Pydantic models from a FastAPI app.

    This function scans the FastAPI app's OpenAPI schema to find all
    Pydantic models that are registered as request/response models.

    Args:
        app: FastAPI application instance

    Returns:
        Dictionary mapping collection names (inferred from model names)
        to Pydantic model classes

    Example:
        ```python
        from fastapi import FastAPI
        from fastapi_mongo_admin import discover_pydantic_models_from_app

        app = FastAPI()

        # Models are automatically discovered
        models = discover_pydantic_models_from_app(app)
        # Returns: {"products": Product, "users": User, ...}
        ```
    """
    models = {}

    try:
        # Get OpenAPI schema
        openapi_schema = app.openapi()
        if not openapi_schema:
            return models

        components = openapi_schema.get("components", {})
        schemas = components.get("schemas", {})
        if not schemas:
            return models

        # Try to find the actual Pydantic model classes
        # by inspecting the app's routes and their dependencies
        for route in app.routes:
            if isinstance(route, APIRoute):
                # Check response model
                if route.response_model:
                    model_name = route.response_model.__name__
                    collection_name = _model_name_to_collection_name(model_name)
                    if collection_name not in models:
                        models[collection_name] = route.response_model

                # Check request body models from route dependencies
                for dependency in route.dependencies:
                    # Check if dependency has a model
                    if hasattr(dependency, "dependant"):
                        for param in dependency.dependant.body_params:
                            if hasattr(param, "annotation"):
                                model = param.annotation
                                if isinstance(model, type) and issubclass(model, BaseModel):
                                    model_name = model.__name__
                                    collection_name = _model_name_to_collection_name(model_name)
                                    if collection_name not in models:
                                        models[collection_name] = model

        # Also check OpenAPI schemas and try to match with app's models
        # This is a fallback if route inspection doesn't find models
        if not models:
            # Try to find models by name in the app's module
            # Get all BaseModel subclasses from modules imported by the app
            for _module_name, module in sys.modules.items():
                if module and hasattr(module, "__file__"):
                    try:
                        for _name, obj in inspect.getmembers(module):
                            if (
                                inspect.isclass(obj)
                                and issubclass(obj, BaseModel)
                                and obj is not BaseModel
                            ):
                                model_name = obj.__name__
                                collection_name = _model_name_to_collection_name(model_name)
                                # Check if this model is in OpenAPI schemas
                                if model_name in schemas:
                                    if collection_name not in models:
                                        models[collection_name] = obj
                    except (ImportError, AttributeError, TypeError):
                        # Skip modules that can't be inspected
                        continue

    except Exception:
        # If discovery fails, return empty dict
        # This is not a critical error
        pass

    return models


def _model_name_to_collection_name(model_name: str) -> str:
    """Convert a Pydantic model name to a collection name.

    Examples:
        "Product" -> "products"
        "User" -> "users"
        "OrderItem" -> "order_items"
        "UserProfile" -> "user_profiles"
    """
    # Simple pluralization: add 's' to snake_case name
    # For more complex cases, users can provide explicit mapping
    if not model_name:
        return model_name

    # Convert PascalCase to snake_case

    # Insert underscore before capital letters (except the first one)
    # This converts "OrderItem" -> "Order_Item"
    snake_case = re.sub(r"(?<!^)(?=[A-Z])", "_", model_name)
    # Convert to lowercase
    lower = snake_case.lower()
    # Add 's' for plural (simple rule)
    return lower + "s"


def get_all_models():
    """Get all Pydantic models from the current module."""
    all_models = set()

    def recurse(subclasses):
        for cls in subclasses:
            if not cls.__module__.startswith("fastapi"):
                all_models.add(cls)
            recurse(cls.__subclasses__())

    recurse(BaseModel.__subclasses__())
    return list(all_models)


def normalize_pydantic_models(
    models: dict[str, type[BaseModel]] | list[type[BaseModel]] | None,
) -> dict[str, type[BaseModel]]:
    """Normalize Pydantic models input to a dictionary.

    Accepts models in multiple formats:
    - dict[str, type[BaseModel]]: Direct mapping (returned as-is)
    - list[type[BaseModel]]: List of models (auto-detect collection names)
    - None: Empty dict

    Args:
        models: Models in any supported format

    Returns:
        Dictionary mapping collection names to model classes

    Example:
        ```python
        # As dict (explicit mapping)
        models = {"products": Product, "users": User}

        # As list (auto-detect collection names)
        models = [Product, User]  # -> {"products": Product, "users": User}
        ```
    """
    if models is None:
        models = get_all_models()

    if not models:
        return {}

    if isinstance(models, dict):
        return models

    if isinstance(models, list):
        result = {}
        for model in models:
            if isinstance(model, type) and issubclass(model, BaseModel):
                collection_name = _model_name_to_collection_name(model.__name__)
                result[collection_name] = model
        return result

    raise TypeError(f"Expected dict, list, or None, got {type(models).__name__}")


def get_static_directory() -> Path:
    """Get the path to the admin static files directory."""
    return Path(__file__).parent / "static"


def mount_admin_ui(app, mount_path: str = "/admin-ui", api_prefix: str = "/admin") -> bool:
    """Mount the admin UI static files to the FastAPI app.

    Args:
        app: FastAPI application instance
        mount_path: Path to mount the admin UI (default: /admin-ui)
        api_prefix: API router prefix to inject into admin.html (default: /admin)

    Returns:
        True if successfully mounted, False otherwise
    """
    try:
        static_dir = get_static_directory()
        if not static_dir.exists():
            return False

        admin_html_path = static_dir / "admin.html"
        if not admin_html_path.exists():
            return False

        # Read admin.html content
        admin_html_content = admin_html_path.read_text(encoding="utf-8")

        # Inject API configuration script before the closing </head> tag
        # Escape single quotes in paths to prevent JavaScript injection
        api_prefix_escaped = api_prefix.replace("'", "\\'").replace("\\", "\\\\")
        mount_path_escaped = mount_path.replace("'", "\\'").replace("\\", "\\\\")

        config_script = f"""
    <script>
      // Injected API configuration
      window.ADMIN_CONFIG = {{
        API_BASE: '{api_prefix_escaped}',
        UI_MOUNT_PATH: '{mount_path_escaped}'
      }};
    </script>
"""
        # Insert config script before closing </head> tag
        if "</head>" in admin_html_content:
            admin_html_content = admin_html_content.replace("</head>", f"{config_script}</head>")
        else:
            # Fallback: insert before first <script> tag
            admin_html_content = admin_html_content.replace(
                "<script>", f"{config_script}<script>", 1
            )

        # Create custom route for admin.html with injected config
        @app.get(f"{mount_path}/admin.html", response_class=HTMLResponse, include_in_schema=False)
        async def serve_admin_html():
            """Serve admin.html with injected API configuration."""
            return admin_html_content

        # Mount other static files (CSS, JS, etc.) if directories exist
        static_files_dir = static_dir
        css_dir = static_files_dir / "css"
        js_dir = static_files_dir / "js"

        if css_dir.exists():
            app.mount(
                f"{mount_path}/css",
                StaticFiles(directory=str(css_dir)),
                name="admin-ui-css",
            )
        if js_dir.exists():
            app.mount(
                f"{mount_path}/js",
                StaticFiles(directory=str(js_dir)),
                name="admin-ui-js",
            )

        # Mount uploads directory for file serving
        uploads_dir = static_files_dir / "uploads"
        if uploads_dir.exists() or True:  # Create if doesn't exist
            uploads_dir.mkdir(parents=True, exist_ok=True)
            app.mount(
                f"{mount_path}/uploads",
                StaticFiles(directory=str(uploads_dir)),
                name="admin-ui-uploads",
            )

        return True
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to mount admin UI: {e}", exc_info=True)
        return False


def mount_admin_app(
    app: FastAPI,
    get_database: Callable[[], AsyncIOMotorDatabase],
    router_prefix: str = "/admin",
    router_tags: list[str] | None = None,
    ui_mount_path: str = "/admin-ui",
    mount_ui: bool = True,
    pydantic_models: dict[str, type[BaseModel]] | list[type[BaseModel]] | None = None,
    auto_discover_models: bool = True,
    openapi_schema_map: dict[str, str] | None = None,
    require_auth: bool = False,
    auth_dependency: Callable | None = None,
) -> Any:
    """Mount the complete admin app (router + UI) to a FastAPI application.

    This is a convenience function that creates the admin router, includes it
    in the app, and optionally mounts the admin UI in a single call.

    Args:
        app: FastAPI application instance to mount the admin app to
        get_database: Dependency function that returns AsyncIOMotorDatabase
        router_prefix: Router prefix (default: /admin)
        router_tags: Router tags (default: ["admin"])
        ui_mount_path: Path to mount the admin UI (default: /admin-ui)
        mount_ui: Whether to mount the admin UI (default: True)
        pydantic_models: Optional models in multiple formats:
            - dict[str, type[BaseModel]]: Explicit mapping
            - list[type[BaseModel]]: List of models (auto-detect names)
            - None: Auto-discover from app if auto_discover_models=True
        auto_discover_models: Whether to auto-discover models from app
            if pydantic_models is None (default: True)
        openapi_schema_map: Optional mapping of collection names to OpenAPI
            schema names

    Returns:
        The created APIRouter instance

    Example:
        ```python
        from fastapi import FastAPI
        from fastapi_mongo_admin import mount_admin_app

        app = FastAPI()

        async def get_database():
            return database

        # Option 1: Auto-discover models from app
        admin_router = mount_admin_app(app, get_database)

        # Option 2: Pass models as list (auto-detect collection names)
        from pydantic import BaseModel
        class Product(BaseModel):
            name: str
            price: float

        admin_router = mount_admin_app(
            app,
            get_database,
            pydantic_models=[Product]  # Auto-detects "products" collection
        )

        # Option 3: Explicit mapping
        admin_router = mount_admin_app(
            app,
            get_database,
            pydantic_models={"my_products": Product}
        )
        ```
    """
    from fastapi_mongo_admin.router import create_router

    # Normalize and merge models
    normalized_models = normalize_pydantic_models(pydantic_models)

    # Auto-discover models from app if enabled and no models provided
    if auto_discover_models and not normalized_models:
        discovered_models = discover_pydantic_models_from_app(app)
        if discovered_models:
            normalized_models = discovered_models

    # Create the admin router
    admin_router = create_router(
        get_database=get_database,
        prefix=router_prefix,
        tags=router_tags,
        app=app,
        pydantic_models=normalized_models if normalized_models else None,
        openapi_schema_map=openapi_schema_map,
        ui_mount_path=ui_mount_path if mount_ui else None,
    )

    # Include router in app
    app.include_router(admin_router)

    # Optionally mount the admin UI
    if mount_ui:
        mount_admin_ui(app, mount_path=ui_mount_path, api_prefix=router_prefix)

    return admin_router


def convert_object_ids_in_query(query: dict[str, Any]) -> dict[str, Any]:
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
            except (ValueError, TypeError, InvalidId):
                # InvalidId may not always be a subclass of ValueError in all pymongo versions
                converted[key] = value
        elif isinstance(value, dict):
            # Handle MongoDB operators like $in, $nin, etc.
            converted[key] = {}
            for op, op_value in value.items():
                if op in ("$in", "$nin") and isinstance(op_value, list):
                    converted_list = []
                    for v in op_value:
                        if (
                            isinstance(v, str)
                            and len(v) == 24
                            and all(c in "0123456789abcdefABCDEF" for c in v)
                        ):
                            try:
                                converted_list.append(ObjectId(v))
                            except (ValueError, TypeError, InvalidId):
                                converted_list.append(v)
                        else:
                            converted_list.append(v)
                    converted[key][op] = converted_list
                elif op == "$eq" and isinstance(op_value, str) and len(op_value) == 24:
                    try:
                        converted[key][op] = ObjectId(op_value)
                    except (ValueError, TypeError, InvalidId):
                        converted[key][op] = op_value
                else:
                    converted[key][op] = op_value
        elif isinstance(value, list):
            converted_list = []
            for v in value:
                if (
                    isinstance(v, str)
                    and len(v) == 24
                    and all(c in "0123456789abcdefABCDEF" for c in v)
                ):
                    try:
                        converted_list.append(ObjectId(v))
                    except (ValueError, TypeError, InvalidId):
                        converted_list.append(
                            convert_object_ids_in_query(v) if isinstance(v, dict) else v
                        )
                else:
                    converted_list.append(
                        convert_object_ids_in_query(v) if isinstance(v, dict) else v
                    )
            converted[key] = converted_list
        else:
            converted[key] = value

    return converted


async def get_searchable_fields(collection: Any) -> list[str]:
    """Get list of searchable string fields from collection schema.

    Excludes enum fields and date/datetime fields from search.
    Note: Without schema information, date detection is based on value patterns.

    Args:
        collection: MongoDB collection

    Returns:
        List of field names that are likely searchable (string type)
    """
    try:
        # Sample a few documents to infer string fields
        cursor = collection.find().limit(5)
        sample = []
        async for doc in cursor:
            sample.append(doc)
            if len(sample) >= 5:
                break
        if not sample:
            return ["_id"]  # Fallback to just _id

        # Pattern to detect ISO date strings (YYYY-MM-DD or ISO datetime)
        date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2})?")

        string_fields = set()
        potential_date_fields = set()

        for doc in sample:
            for key, value in doc.items():
                if isinstance(value, str) and key != "_id":
                    # Check if value looks like a date (ISO format)
                    if date_pattern.match(value):
                        potential_date_fields.add(key)
                    else:
                        string_fields.add(key)

        # Remove fields that appear to be dates from searchable fields
        string_fields -= potential_date_fields

        return list(string_fields) if string_fields else ["_id"]
    except (ValueError, TypeError, AttributeError):
        return ["_id"]
