"""list_select_related tests."""

import mongomock
import pytest
from bson import ObjectId

from fastapi_mongo_admin.db.sync_backend import SyncPyMongoBackend
from fastapi_mongo_admin.services.repository import CollectionRepository
from pydantic import BaseModel

from fastapi_mongo_admin.admin.model import ModelAdmin


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
