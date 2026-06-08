"""Example FastAPI app with FastAPI Mongo Admin v2."""

from __future__ import annotations

import uvicorn
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel

from fastapi_mongo_admin import ModelAdmin, action, display, mount_admin_app, site


class Category(BaseModel):
    name: str


class Product(BaseModel):
    name: str
    price: float
    category: str
    active: bool = True


class CategoryAdmin(ModelAdmin):
    model = Category
    collection_name = "categories"
    list_display = ["name"]
    search_fields = ["name"]


class ProductAdmin(ModelAdmin):
    model = Product
    collection_name = "products"
    list_display = ["name", "category", "price", "active"]
    list_filter = ["category", "active"]
    search_fields = ["name", "category"]
    list_per_page = 20
    choices = {
        "category": [("books", "Books"), ("electronics", "Electronics")],
    }
    list_select_related = {"category": "categories"}

    @display(description="Product")
    def product_name(self, obj: dict) -> str:
        return str(obj.get("name", ""))

    @action("Mark inactive")
    async def mark_inactive(self, request, queryset: list[dict]) -> None:
        """Example bulk action hook."""
        _ = request, queryset


async def optional_user() -> dict[str, str]:
    """Demo auth — replace with real JWT/session validation."""
    return {"id": "demo", "is_staff": True}


def create_app() -> FastAPI:
    """Create and configure the demo application."""
    app = FastAPI(title="FastAPI Mongo Admin Demo")
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    database = client["demo_db"]

    site.register(Category, CategoryAdmin)
    site.register(Product, ProductAdmin)

    async def get_database():
        return database

    mount_admin_app(
        app,
        get_database,
        admin_site=site,
        mode="async",
        auth_dependency=optional_user,
    )
    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run("example_usage:app", host="0.0.0.0", port=8000, reload=True)
