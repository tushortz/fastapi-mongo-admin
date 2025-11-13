"""Additional tests for schema utilities to improve coverage."""

import pytest
from fastapi import FastAPI
from pydantic import BaseModel

from fastapi_mongo_admin.schema import (
    _convert_openapi_schema_to_internal,
    _get_example_for_type,
    _get_type_from_openapi_field,
    infer_schema_from_openapi,
)


def test_get_example_for_type():
    """Test getting examples for different types."""
    assert _get_example_for_type("str") == ""
    assert _get_example_for_type("int") == 0
    assert _get_example_for_type("float") == 0.0
    assert _get_example_for_type("decimal") == 0.0
    assert _get_example_for_type("bool") is False
    assert _get_example_for_type("list") == []
    assert _get_example_for_type("dict") == {}
    assert _get_example_for_type("ObjectId") == ""
    assert _get_example_for_type("datetime") is None
    assert _get_example_for_type("unknown") == ""


def test_get_type_from_openapi_field_ref():
    """Test getting type from OpenAPI field with $ref."""
    field_def = {"$ref": "#/components/schemas/User"}
    all_schemas = {
        "User": {"type": "object", "properties": {"name": {"type": "string"}}}
    }

    result = _get_type_from_openapi_field(field_def, all_schemas)
    assert result == "dict"


def test_get_type_from_openapi_field_ref_no_type():
    """Test getting type from OpenAPI field with $ref but no type."""
    field_def = {"$ref": "#/components/schemas/User"}
    all_schemas = {"User": {"properties": {"name": {"type": "string"}}}}

    result = _get_type_from_openapi_field(field_def, all_schemas)
    assert result == "dict"


def test_get_type_from_openapi_field_allof():
    """Test getting type from OpenAPI field with allOf."""
    field_def = {
        "allOf": [{"type": "string"}]
    }
    all_schemas = {}

    result = _get_type_from_openapi_field(field_def, all_schemas)
    assert result == "str"


def test_get_type_from_openapi_field_anyof():
    """Test getting type from OpenAPI field with anyOf."""
    field_def = {
        "anyOf": [{"type": "integer"}]
    }
    all_schemas = {}

    result = _get_type_from_openapi_field(field_def, all_schemas)
    assert result == "int"


def test_get_type_from_openapi_field_oneof():
    """Test getting type from OpenAPI field with oneOf."""
    field_def = {
        "oneOf": [{"type": "number"}]
    }
    all_schemas = {}

    result = _get_type_from_openapi_field(field_def, all_schemas)
    assert result == "float"


def test_get_type_from_openapi_field_array():
    """Test getting type from OpenAPI field with array type."""
    field_def = {"type": "array", "items": {"type": "string"}}
    all_schemas = {}

    result = _get_type_from_openapi_field(field_def, all_schemas)
    assert result == "list"


def test_get_type_from_openapi_field_array_ref():
    """Test getting type from OpenAPI field with array and $ref items."""
    field_def = {
        "type": "array",
        "items": {"$ref": "#/components/schemas/Item"}
    }
    all_schemas = {"Item": {"type": "object"}}

    result = _get_type_from_openapi_field(field_def, all_schemas)
    assert result == "list"


def test_get_type_from_openapi_field_datetime():
    """Test getting type from OpenAPI field with date-time format."""
    field_def = {"type": "string", "format": "date-time"}
    all_schemas = {}

    result = _get_type_from_openapi_field(field_def, all_schemas)
    assert result == "datetime"


def test_get_type_from_openapi_field_date():
    """Test getting type from OpenAPI field with date format."""
    field_def = {"type": "string", "format": "date"}
    all_schemas = {}

    result = _get_type_from_openapi_field(field_def, all_schemas)
    assert result == "datetime"


def test_get_type_from_openapi_field_decimal():
    """Test getting type from OpenAPI field with decimal format."""
    field_def = {"type": "number", "format": "decimal"}
    all_schemas = {}

    result = _get_type_from_openapi_field(field_def, all_schemas)
    assert result == "decimal"


def test_get_type_from_openapi_field_money():
    """Test getting type from OpenAPI field with money format."""
    field_def = {"type": "number", "format": "money"}
    all_schemas = {}

    result = _get_type_from_openapi_field(field_def, all_schemas)
    assert result == "decimal"


def test_get_type_from_openapi_field_enum():
    """Test getting type from OpenAPI field with enum."""
    field_def = {"type": "string", "enum": ["option1", "option2"]}
    all_schemas = {}

    result = _get_type_from_openapi_field(field_def, all_schemas)
    assert result == "str"


def test_get_type_from_openapi_field_unknown():
    """Test getting type from OpenAPI field with unknown type."""
    field_def = {"type": "unknown_type"}
    all_schemas = {}

    result = _get_type_from_openapi_field(field_def, all_schemas)
    assert result == "str"  # Default fallback


def test_convert_openapi_schema_to_internal_basic():
    """Test converting basic OpenAPI schema to internal format."""
    schema_def = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"}
        },
        "required": ["name"]
    }
    all_schemas = {}

    result = _convert_openapi_schema_to_internal(schema_def, all_schemas)

    assert "fields" in result
    assert "name" in result["fields"]
    assert "age" in result["fields"]
    assert result["fields"]["name"]["nullable"] is False
    assert result["fields"]["age"]["nullable"] is True


def test_convert_openapi_schema_to_internal_with_enum():
    """Test converting OpenAPI schema with enum."""
    schema_def = {
        "type": "object",
        "properties": {
            "status": {
                "type": "string",
                "enum": ["active", "inactive"]
            }
        }
    }
    all_schemas = {}

    result = _convert_openapi_schema_to_internal(schema_def, all_schemas)

    assert "status" in result["fields"]
    assert "enum" in result["fields"]["status"]
    assert result["fields"]["status"]["enum"] == ["active", "inactive"]


def test_convert_openapi_schema_to_internal_with_example():
    """Test converting OpenAPI schema with example."""
    schema_def = {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "example": "John Doe"
            }
        }
    }
    all_schemas = {}

    result = _convert_openapi_schema_to_internal(schema_def, all_schemas)

    assert result["fields"]["name"]["example"] == "John Doe"


def test_convert_openapi_schema_to_internal_with_default():
    """Test converting OpenAPI schema with default."""
    schema_def = {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "default": "Default Name"
            }
        }
    }
    all_schemas = {}

    result = _convert_openapi_schema_to_internal(schema_def, all_schemas)

    assert result["fields"]["name"]["example"] == "Default Name"


@pytest.mark.asyncio
async def test_infer_schema_from_openapi_no_components(test_database):
    """Test inferring schema from OpenAPI with no components."""
    app = FastAPI()

    # Mock openapi to return schema without components
    original_openapi = app.openapi

    def mock_openapi():
        return {"info": {"title": "Test"}}

    app.openapi = mock_openapi

    result = infer_schema_from_openapi(app, "test_collection")

    assert result is None


@pytest.mark.asyncio
async def test_infer_schema_from_openapi_no_schemas(test_database):
    """Test inferring schema from OpenAPI with no schemas."""
    app = FastAPI()

    # Mock openapi to return schema without schemas
    def mock_openapi():
        return {"components": {}}

    app.openapi = mock_openapi

    result = infer_schema_from_openapi(app, "test_collection")

    assert result is None

