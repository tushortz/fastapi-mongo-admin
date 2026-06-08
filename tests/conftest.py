"""Pytest fixtures."""

from __future__ import annotations

import mongomock
import pytest
from bson import ObjectId
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel

from fastapi_mongo_admin import AdminSite, ModelAdmin, mount_admin_app


class Product(BaseModel):
    name: str
    price: float
    category: str
    active: bool = True


class Category(BaseModel):
    name: str


class ProductAdmin(ModelAdmin):
    model = Product
    collection_name = "products"
    list_display = ["name", "category", "price", "active"]
    search_fields = ["name", "category"]
    list_filter = ["category", "active"]
    list_per_page = 10
    choices = {
        "category": [("books", "Books"), ("electronics", "Electronics")],
    }


class CategoryAdmin(ModelAdmin):
    model = Category
    collection_name = "categories"
    list_display = ["name"]


@pytest.fixture
def mock_db() -> mongomock.MongoClient:
    """Return mongomock database with sample data."""
    client = mongomock.MongoClient()
    db = client["test_db"]
    cat_id = ObjectId()
    db.categories.insert_one({"_id": cat_id, "name": "Books"})
    db.products.insert_many(
        [
            {"_id": ObjectId(), "name": "Python Guide", "price": 29.99, "category": "books", "active": True},
            {"_id": ObjectId(), "name": "Laptop", "price": 999.0, "category": "electronics", "active": False},
        ]
    )
    return client


@pytest.fixture
def admin_site() -> AdminSite:
    """Fresh admin site with Product registered."""
    site = AdminSite()
    site.register(Product, ProductAdmin)
    site.register(Category, CategoryAdmin)
    return site


@pytest.fixture
def app(mock_db: mongomock.MongoClient, admin_site: AdminSite) -> FastAPI:
    """FastAPI app with sync admin mounted."""
    application = FastAPI()

    def get_database():
        return mock_db["test_db"]

    mount_admin_app(application, get_database, admin_site=admin_site, mode="sync")
    return application


@pytest.fixture
async def client(app: FastAPI) -> AsyncClient:
    """Async HTTP client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
