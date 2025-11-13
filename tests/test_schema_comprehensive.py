"""Comprehensive tests for schema utilities."""

import enum
from datetime import datetime
from decimal import Decimal
from typing import List, Literal, Optional, Union

import pytest
from bson import ObjectId
from fastapi import FastAPI
from pydantic import BaseModel, Field

from fastapi_mongo_admin.schema import (
    infer_schema,
    infer_schema_from_openapi,
    infer_schema_from_pydantic,
    serialize_for_export,
    serialize_object_id,
)


class StatusEnum(str, enum.Enum):
    """Test enum."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"


class ProductModel(BaseModel):
    """Test Pydantic model for schema inference."""

    name: str
    price: float
    description: Optional[str] = None
    active: bool = True


class UserModel(BaseModel):
    """Test Pydantic model with various field types."""

    name: str
    age: int
    email: str
    created_at: datetime


class ModelWithEnum(BaseModel):
    """Test model with enum field."""

    status: StatusEnum
    name: str


class ModelWithLiteral(BaseModel):
    """Test model with Literal type."""

    type: Literal["admin", "user", "guest"]


class ModelWithDecimal(BaseModel):
    """Test model with Decimal field."""

    amount: Decimal
    name: str


class NestedModel(BaseModel):
    """Test nested model."""

    user: UserModel
    metadata: dict


def test_infer_schema_from_pydantic_basic():
    """Test basic schema inference from Pydantic model."""
    schema = infer_schema_from_pydantic(ProductModel)

    assert "fields" in schema
    assert "name" in schema["fields"]
    assert "price" in schema["fields"]
    assert "description" in schema["fields"]
    assert "active" in schema["fields"]

    # Check field types
    assert schema["fields"]["name"]["type"] == "str"
    assert schema["fields"]["price"]["type"] == "float"
    assert schema["fields"]["active"]["type"] == "bool"


def test_infer_schema_from_pydantic_with_datetime():
    """Test schema inference with datetime field."""
    schema = infer_schema_from_pydantic(UserModel)

    assert "created_at" in schema["fields"]
    assert schema["fields"]["created_at"]["type"] == "datetime"


def test_infer_schema_from_pydantic_nullable():
    """Test schema inference with nullable fields."""
    schema = infer_schema_from_pydantic(ProductModel)

    # description is Optional, so should be nullable
    assert schema["fields"]["description"]["nullable"] is True
    # name is required, so should not be nullable
    assert schema["fields"]["name"]["nullable"] is False


@pytest.mark.asyncio
async def test_infer_schema_no_model(test_collection):
    """Test infer_schema without Pydantic model."""
    # The function returns empty schema if no model provided
    schema = await infer_schema(test_collection, pydantic_model=None)

    assert schema == {"fields": {}, "sample_count": 0}


@pytest.mark.asyncio
async def test_infer_schema_with_model(test_collection):
    """Test infer_schema with Pydantic model."""
    schema = await infer_schema(test_collection, pydantic_model=ProductModel)

    assert "fields" in schema
    assert "name" in schema["fields"]


@pytest.mark.asyncio
async def test_infer_schema_from_openapi(test_database):
    """Test schema inference from OpenAPI."""
    app = FastAPI()

    @app.post("/products", response_model=ProductModel)
    async def create_product(product: ProductModel):
        return product

    schema = infer_schema_from_openapi(app, "products", "ProductModel")

    if schema:
        assert "fields" in schema
        # Schema should have fields from TestProduct
        assert "name" in schema["fields"] or "price" in schema["fields"]


@pytest.mark.asyncio
async def test_infer_schema_from_openapi_not_found(test_database):
    """Test schema inference from OpenAPI with non-existent schema."""
    app = FastAPI()
    schema = infer_schema_from_openapi(app, "nonexistent", "NonExistent")

    assert schema is None


def test_infer_schema_from_pydantic_with_enum():
    """Test schema inference with enum field."""
    schema = infer_schema_from_pydantic(ModelWithEnum)

    assert "status" in schema["fields"]
    assert "enum" in schema["fields"]["status"]
    assert len(schema["fields"]["status"]["enum"]) == 3


def test_infer_schema_from_pydantic_with_literal():
    """Test schema inference with Literal type."""
    schema = infer_schema_from_pydantic(ModelWithLiteral)

    assert "type" in schema["fields"]
    assert "enum" in schema["fields"]["type"]
    assert "admin" in schema["fields"]["type"]["enum"]


def test_infer_schema_from_pydantic_with_decimal():
    """Test schema inference with Decimal field."""
    schema = infer_schema_from_pydantic(ModelWithDecimal)

    assert "amount" in schema["fields"]
    assert schema["fields"]["amount"]["type"] == "decimal"


def test_infer_schema_from_pydantic_nested():
    """Test schema inference with nested model."""
    schema = infer_schema_from_pydantic(NestedModel)

    assert "user" in schema["fields"]
    assert schema["fields"]["user"]["type"] == "dict"


def test_infer_schema_from_pydantic_invalid_type():
    """Test schema inference with invalid model type."""
    with pytest.raises(TypeError):
        infer_schema_from_pydantic(str)  # Not a BaseModel


def test_serialize_for_export_primitive():
    """Test serializing primitive types for export."""
    # Primitives should pass through
    assert serialize_for_export("string") == "string"
    assert serialize_for_export(123) == 123
    assert serialize_for_export(45.6) == 45.6
    assert serialize_for_export(True) is True
    assert serialize_for_export(None) is None


def test_serialize_for_export_empty_structures():
    """Test serializing empty structures."""
    assert serialize_for_export({}) == {}
    assert serialize_for_export([]) == []


def test_infer_schema_from_pydantic_with_callable_default():
    """Test schema inference with callable default (default_factory)."""
    class ModelWithFactory(BaseModel):
        items: List[str] = Field(default_factory=list)
        name: str = "default"

    schema = infer_schema_from_pydantic(ModelWithFactory)

    assert "items" in schema["fields"]
    assert "name" in schema["fields"]
    assert schema["fields"]["name"]["example"] == "default"


def test_infer_schema_from_pydantic_with_union():
    """Test schema inference with Union type."""
    class ModelWithUnion(BaseModel):
        value: Union[str, int]
        optional: Union[str, None] = None

    schema = infer_schema_from_pydantic(ModelWithUnion)

    assert "value" in schema["fields"]
    assert "optional" in schema["fields"]
    assert schema["fields"]["optional"]["nullable"] is True


def test_infer_schema_from_pydantic_with_list():
    """Test schema inference with List type."""
    class ModelWithList(BaseModel):
        tags: List[str]
        numbers: List[int] = []

    schema = infer_schema_from_pydantic(ModelWithList)

    assert "tags" in schema["fields"]
    assert schema["fields"]["tags"]["type"] == "list"
    assert schema["fields"]["numbers"]["type"] == "list"


def test_serialize_object_id_complex():
    """Test serializing complex nested structures with ObjectIds."""
    doc = {
        "_id": ObjectId(),
        "user": {
            "profile": {
                "user_id": ObjectId(),
                "tags": [ObjectId(), ObjectId()],
            }
        },
        "items": [
            {"item_id": ObjectId()},
            {"item_id": ObjectId()},
        ],
    }

    result = serialize_object_id(doc)

    assert isinstance(result["_id"], str)
    assert isinstance(result["user"]["profile"]["user_id"], str)
    assert all(isinstance(tag, str) for tag in result["user"]["profile"]["tags"])
    assert all(isinstance(item["item_id"], str) for item in result["items"])


def test_serialize_for_export_complex():
    """Test serializing complex structures for export."""
    doc = {
        "_id": ObjectId(),
        "created_at": datetime(2024, 1, 1, 12, 0, 0),
        "metadata": {
            "user_id": ObjectId(),
            "updated_at": datetime(2024, 1, 2, 12, 0, 0),
        },
        "items": [
            {"id": ObjectId(), "date": datetime(2024, 1, 3, 12, 0, 0)},
        ],
    }

    result = serialize_for_export(doc)

    assert isinstance(result["_id"], str)
    assert isinstance(result["created_at"], str)
    assert isinstance(result["metadata"]["user_id"], str)
    assert isinstance(result["metadata"]["updated_at"], str)
    assert isinstance(result["items"][0]["id"], str)
    assert isinstance(result["items"][0]["date"], str)

