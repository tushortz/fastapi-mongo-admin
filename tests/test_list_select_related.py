"""list_select_related tests."""

import mongomock
import pytest
from bson import ObjectId
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel

from fastapi_mongo_admin import AdminSite, mount_admin_app
from fastapi_mongo_admin.admin.model import ModelAdmin
from fastapi_mongo_admin.db.sync_backend import SyncPyMongoBackend
from fastapi_mongo_admin.services.repository import CollectionRepository, related_object_label


class Order(BaseModel):
    title: str
    category_id: str


class OrderAdmin(ModelAdmin):
    model = Order
    collection_name = "orders"
    list_display = ["title", "category_id"]
    list_select_related = {"category_id": "categories"}


@pytest.mark.asyncio
async def test_select_related_enriches_results() -> None:
    client = mongomock.MongoClient()
    db = client["test_db"]
    cat_id = ObjectId()
    db.categories.insert_one({"_id": cat_id, "name": "Books"})
    db.orders.insert_one({"_id": ObjectId(), "title": "Order 1", "category_id": cat_id})

    admin = OrderAdmin(Order)
    backend = SyncPyMongoBackend(db["orders"])
    repo = CollectionRepository(backend, admin)
    repo.set_related_backend("categories", SyncPyMongoBackend(db["categories"]))

    result = await repo.list_documents()
    row = result["results"][0]
    assert "_category_id_related" in row
    assert row["_category_id_related"]["name"] == "Books"


def test_related_object_label_prefers_name() -> None:
    assert related_object_label({"_id": ObjectId(), "name": "Books"}) == "Books"


def test_related_object_label_uses_full_name() -> None:
    assert (
        related_object_label(
            {
                "_id": ObjectId(),
                "first_name": "Ada",
                "last_name": "Lovelace",
                "email": "ada@example.com",
            }
        )
        == "Ada Lovelace"
    )


@pytest.mark.asyncio
async def test_related_form_initial() -> None:
    client = mongomock.MongoClient()
    db = client["test_db"]
    cat_id = ObjectId()
    brand_id = ObjectId()
    db.categories.insert_one({"_id": cat_id, "name": "Electronics"})
    db.brands.insert_one({"_id": brand_id, "name": "Acme"})
    product_id = ObjectId()
    db.products.insert_one(
        {
            "_id": product_id,
            "title": "Phone",
            "category_id": str(cat_id),
            "brand_id": str(brand_id),
        },
    )

    class Product(BaseModel):
        title: str
        category_id: str | None = None
        brand_id: str | None = None

    class ProductAdmin(ModelAdmin):
        model = Product
        collection_name = "products"
        list_select_related = {"category_id": "categories", "brand_id": "brands"}

    admin = ProductAdmin(Product)
    repo = CollectionRepository(SyncPyMongoBackend(db["products"]), admin)
    repo.set_related_backend("categories", SyncPyMongoBackend(db["categories"]))
    repo.set_related_backend("brands", SyncPyMongoBackend(db["brands"]))

    doc = await repo.get_document(str(product_id))
    initial = await repo.get_related_form_initial(doc)
    assert initial["category_id"] == (str(cat_id), "Electronics")
    assert initial["brand_id"] == (str(brand_id), "Acme")


@pytest.mark.asyncio
async def test_search_related_documents_requires_min_chars() -> None:
    client = mongomock.MongoClient()
    db = client["test_db"]
    db.categories.insert_one({"_id": ObjectId(), "name": "Electronics"})

    class Product(BaseModel):
        title: str
        category_id: str | None = None

    class ProductAdmin(ModelAdmin):
        model = Product
        collection_name = "products"
        list_select_related = {"category_id": "categories"}

    admin = ProductAdmin(Product)
    repo = CollectionRepository(SyncPyMongoBackend(db["products"]), admin)
    repo.set_related_backend("categories", SyncPyMongoBackend(db["categories"]))

    assert await repo.search_related_documents("category_id", "e") == []
    matches = await repo.search_related_documents("category_id", "ele")
    assert len(matches) == 1
    assert matches[0][1] == "Electronics"


@pytest.mark.asyncio
async def test_change_form_renders_related_select() -> None:
    client = mongomock.MongoClient()
    db = client["test_db"]
    cat_id = ObjectId()
    product_id = ObjectId()
    db.categories.insert_one({"_id": cat_id, "name": "Electronics"})
    db.products.insert_one(
        {"_id": product_id, "title": "Phone", "category_id": str(cat_id)},
    )

    class Product(BaseModel):
        title: str
        category_id: str | None = None

    class ProductAdmin(ModelAdmin):
        model = Product
        collection_name = "products"
        list_select_related = {"category_id": "categories"}

    site = AdminSite()
    site.register(Product, ProductAdmin)
    app = FastAPI()
    mount_admin_app(app, lambda: db, admin_site=site, mode="sync")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get(f"/admin/products/{product_id}/change/")

    assert response.status_code == 200
    assert 'class="related-select"' in response.text
    assert f'id="id_category_id" value="{cat_id}"' in response.text
    assert 'value="Electronics"' in response.text
    assert "/admin/products/related-lookup/category_id/" in response.text


@pytest.mark.asyncio
async def test_related_lookup_endpoint() -> None:
    client = mongomock.MongoClient()
    db = client["test_db"]
    cat_id = ObjectId()
    db.categories.insert_many(
        [
            {"_id": cat_id, "name": "Electronics"},
            {"_id": ObjectId(), "name": "Books"},
        ]
    )

    class Product(BaseModel):
        title: str
        category_id: str | None = None

    class ProductAdmin(ModelAdmin):
        model = Product
        collection_name = "products"
        list_select_related = {"category_id": "categories"}

    site = AdminSite()
    site.register(Product, ProductAdmin)
    app = FastAPI()
    mount_admin_app(app, lambda: db, admin_site=site, mode="sync")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        short = await ac.get("/admin/products/related-lookup/category_id/?q=e")
        match = await ac.get("/admin/products/related-lookup/category_id/?q=ele")

    assert short.status_code == 200
    assert short.json()["results"] == []
    assert match.status_code == 200
    assert match.json()["results"] == [{"value": str(cat_id), "label": "Electronics"}]
