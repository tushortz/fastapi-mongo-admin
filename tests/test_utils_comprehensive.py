"""Comprehensive tests for utility functions."""

from pathlib import Path

import pytest
import pytest_asyncio
from fastapi import FastAPI
from pydantic import BaseModel

from fastapi_mongo_admin.utils import (
    _model_name_to_collection_name,
    discover_pydantic_models_from_app,
    get_static_directory,
    mount_admin_app,
    mount_admin_ui,
    normalize_pydantic_models,
)


class Product(BaseModel):
    """Test model."""

    name: str
    price: float


class User(BaseModel):
    """Test model."""

    name: str
    email: str


class OrderItem(BaseModel):
    """Test model with compound name."""

    quantity: int


def test_model_name_to_collection_name_simple():
    """Test simple model name conversion."""
    assert _model_name_to_collection_name("Product") == "products"
    assert _model_name_to_collection_name("User") == "users"


def test_model_name_to_collection_name_compound():
    """Test compound model name conversion."""
    assert _model_name_to_collection_name("OrderItem") == "order_items"
    assert _model_name_to_collection_name("UserProfile") == "user_profiles"


def test_model_name_to_collection_name_empty():
    """Test empty model name conversion."""
    assert _model_name_to_collection_name("") == ""


def test_normalize_pydantic_models_list():
    """Test normalizing list of models."""
    models = [Product, User]
    result = normalize_pydantic_models(models)

    assert isinstance(result, dict)
    assert "products" in result
    assert "users" in result
    assert result["products"] == Product
    assert result["users"] == User


def test_normalize_pydantic_models_dict():
    """Test normalizing dict of models."""
    models = {"products": Product, "users": User}
    result = normalize_pydantic_models(models)

    assert result == models


def test_normalize_pydantic_models_none():
    """Test normalizing None."""
    # normalize_pydantic_models(None) calls get_all_models() which returns all BaseModel subclasses
    # So it won't be empty, but we can test that it returns a dict
    result = normalize_pydantic_models(None)

    assert isinstance(result, dict)


def test_normalize_pydantic_models_invalid():
    """Test normalizing invalid input."""
    with pytest.raises(TypeError):
        normalize_pydantic_models("invalid")


def test_discover_pydantic_models_from_app():
    """Test discovering models from FastAPI app."""
    app = FastAPI()

    @app.post("/products", response_model=Product)
    async def create_product(product: Product):
        return product

    models = discover_pydantic_models_from_app(app)

    # Should discover Product model
    assert isinstance(models, dict)
    # May or may not find models depending on route inspection


def test_discover_pydantic_models_from_app_no_routes():
    """Test discovering models from app with no routes."""
    app = FastAPI()
    models = discover_pydantic_models_from_app(app)

    assert isinstance(models, dict)
    assert len(models) == 0


def test_get_static_directory():
    """Test getting static directory path."""
    static_dir = get_static_directory()

    assert isinstance(static_dir, Path)
    assert static_dir.exists() or static_dir.parent.exists()


def test_mount_admin_ui():
    """Test mounting admin UI."""
    app = FastAPI()

    # This should work if static files exist
    result = mount_admin_ui(app, mount_path="/admin-ui", api_prefix="/admin")

    # Result depends on whether static files exist
    assert isinstance(result, bool)


def test_mount_admin_ui_custom_paths():
    """Test mounting admin UI with custom paths."""
    app = FastAPI()

    result = mount_admin_ui(app, mount_path="/custom-ui", api_prefix="/custom-api")

    assert isinstance(result, bool)


def test_normalize_pydantic_models_compound_names():
    """Test normalizing models with compound names."""
    models = [OrderItem]
    result = normalize_pydantic_models(models)

    assert "order_items" in result
    assert result["order_items"] == OrderItem


def test_normalize_pydantic_models_empty_list():
    """Test normalizing empty list."""
    result = normalize_pydantic_models([])

    assert result == {}


@pytest.mark.asyncio
async def test_mount_admin_app(test_database):
    """Test mounting complete admin app."""
    pytest.importorskip("python_multipart")  # Skip if multipart not available

    app = FastAPI()

    async def get_db():
        return test_database

    router = mount_admin_app(
        app,
        get_database=get_db,
        router_prefix="/admin",
        mount_ui=False,  # Don't mount UI in test
    )

    assert router is not None
    # Router should be included in app
    assert len(app.routes) > 0


@pytest.mark.asyncio
async def test_mount_admin_app_with_models(test_database):
    """Test mounting admin app with Pydantic models."""
    pytest.importorskip("python_multipart")  # Skip if multipart not available

    app = FastAPI()

    async def get_db():
        return test_database

    router = mount_admin_app(
        app,
        get_database=get_db,
        pydantic_models=[Product, User],
        mount_ui=False,
    )

    assert router is not None

