"""Utility functions for admin module."""

from pathlib import Path
from typing import Any, Callable

from fastapi import FastAPI
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
        from fastapi.routing import APIRoute

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
            import inspect
            import sys

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
        "OrderItem" -> "orderitems"
    """
    # Simple pluralization: add 's' to lowercase name
    # For more complex cases, users can provide explicit mapping
    if not model_name:
        return model_name

    # Convert PascalCase to lowercase
    import re

    # Insert space before capital letters
    spaced = re.sub(r"(?<!^)(?=[A-Z])", " ", model_name)
    # Convert to lowercase and replace spaces with nothing
    lower = spaced.lower().replace(" ", "")
    # Add 's' for plural (simple rule)
    return lower + "s"


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


def mount_admin_ui(app, mount_path: str = "/admin-ui") -> bool:
    """Mount the admin UI static files to the FastAPI app.

    Args:
        app: FastAPI application instance
        mount_path: Path to mount the admin UI (default: /admin-ui)

    Returns:
        True if successfully mounted, False otherwise
    """
    try:
        static_dir = get_static_directory()
        if static_dir.exists():
            app.mount(
                mount_path, StaticFiles(directory=str(static_dir), html=True), name="admin-ui"
            )
            return True
        return False
    except Exception:
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
    )

    # Include router in app
    app.include_router(admin_router)

    # Optionally mount the admin UI
    if mount_ui:
        mount_admin_ui(app, mount_path=ui_mount_path)

    return admin_router
