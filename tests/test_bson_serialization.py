"""BSON encoding/decoding helpers."""

from datetime import date, datetime
from decimal import Decimal

import mongomock
import pytest
from bson import BSON
from bson.decimal128 import Decimal128
from pydantic import BaseModel, Field

from fastapi_mongo_admin.admin.model import ModelAdmin
from fastapi_mongo_admin.db.sync_backend import SyncPyMongoBackend
from fastapi_mongo_admin.schemas.inference import prepare_for_mongodb, serialize_document
from fastapi_mongo_admin.services.repository import CollectionRepository


class PricedItem(BaseModel):
    name: str
    price: Decimal = Field(ge=0)
    compare_at_price: Decimal | None = None
    born_on: date | None = None


class PricedItemAdmin(ModelAdmin):
    model = PricedItem
    collection_name = "priced_items"


def test_prepare_for_mongodb_encodes_decimal_and_date() -> None:
    payload = prepare_for_mongodb(
        {
            "price": Decimal("10.50"),
            "compare_at_price": Decimal("12.00"),
            "born_on": date(2024, 6, 8),
        }
    )
    BSON.encode(payload)
    assert isinstance(payload["price"], Decimal128)
    assert payload["price"].to_decimal() == Decimal("10.50")
    assert isinstance(payload["born_on"], datetime)


def test_serialize_document_decodes_decimal128() -> None:
    doc = {
        "_id": "abc",
        "price": Decimal128("19.99"),
        "born_on": datetime(2024, 6, 8, 0, 0),
    }
    serialized = serialize_document(doc)
    assert serialized["price"] == "19.99"
    assert serialized["born_on"] == "2024-06-08T00:00:00"
    assert serialized["id"] == "abc"


@pytest.fixture
def priced_repo(mock_db: mongomock.MongoClient) -> CollectionRepository:
    db = mock_db["test_db"]
    admin = PricedItemAdmin(PricedItem)
    backend = SyncPyMongoBackend(db["priced_items"])
    return CollectionRepository(backend, admin)


@pytest.mark.asyncio
async def test_repository_create_decimal_document(priced_repo: CollectionRepository) -> None:
    doc_id = await priced_repo.create_document(
        {
            "name": "Coupon",
            "price": "10",
            "compare_at_price": "12.50",
            "born_on": "2024-01-15",
        }
    )
    doc = await priced_repo.get_document(doc_id)
    assert doc["name"] == "Coupon"
    assert doc["price"] == "10"
    assert doc["compare_at_price"] == "12.50"
    assert doc["born_on"].startswith("2024-01-15")
