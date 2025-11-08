"""Schema introspection utilities for MongoDB collections."""

from typing import Any, Type

from bson import ObjectId
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorCollection
from pydantic import BaseModel
from pydantic.fields import FieldInfo


def serialize_object_id(obj: Any) -> Any:
    """Convert ObjectId to string for JSON serialization."""
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, dict):
        return {k: serialize_object_id(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [serialize_object_id(item) for item in obj]
    return obj


async def infer_schema(
    collection: AsyncIOMotorCollection,
    sample_size: int = 10,
    pydantic_model: Type[BaseModel] | None = None,
) -> dict[str, Any]:
    """Infer schema from collection documents or Pydantic model.

    Args:
        collection: MongoDB collection
        sample_size: Number of documents to sample for schema inference
        pydantic_model: Optional Pydantic model to use for schema inference
            when collection is empty

    Returns:
        Dictionary with field types and examples
    """
    cursor = collection.find().limit(sample_size)
    documents = await cursor.to_list(length=sample_size)

    if not documents:
        # If collection is empty, try to use Pydantic model
        if pydantic_model is not None:
            return infer_schema_from_pydantic(pydantic_model)
        return {"fields": {}, "sample_count": 0}

    # Analyze all documents to determine field types
    field_types: dict[str, set[str]] = {}
    field_examples: dict[str, Any] = {}

    for doc in documents:
        for key, value in doc.items():
            if key == "_id":
                continue

            # Determine type
            value_type = _get_python_type(value)
            if key not in field_types:
                field_types[key] = set()
            field_types[key].add(value_type)

            # Store first example
            if key not in field_examples:
                field_examples[key] = value

    # Build schema
    schema = {
        "fields": {},
        "sample_count": len(documents),
    }

    for field_name, types in field_types.items():
        schema["fields"][field_name] = {
            "type": _determine_primary_type(types),
            "types": sorted(list(types)),
            "example": field_examples.get(field_name),
            "nullable": "NoneType" in types,
        }

    return schema


def _get_python_type(value: Any) -> str:
    """Get Python type name for a value."""
    if value is None:
        return "NoneType"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "str"
    if isinstance(value, list):
        return "list"
    if isinstance(value, dict):
        return "dict"
    if isinstance(value, ObjectId):
        return "ObjectId"
    # Check for datetime types
    type_name = type(value).__name__
    if type_name in ("datetime", "datetime64", "Timestamp"):
        return "datetime"
    return type_name


def _determine_primary_type(types: set[str]) -> str:
    """Determine primary type from a set of types."""
    # Priority order
    priority = [
        "str", "int", "float", "bool", "dict", "list", "ObjectId", "NoneType"
    ]

    for ptype in priority:
        if ptype in types:
            return ptype

    # Return first type if not in priority
    return sorted(types)[0] if types else "str"


def infer_schema_from_pydantic(model: Type[BaseModel]) -> dict[str, Any]:
    """Infer schema from a Pydantic model.

    Args:
        model: Pydantic BaseModel class

    Returns:
        Dictionary with field types and examples matching the format
        returned by infer_schema.
    """
    schema = {
        "fields": {},
        "sample_count": 0,
        "source": "pydantic_model",
    }

    # Get the model's JSON schema
    json_schema = model.model_json_schema()

    # Extract field information
    required_fields = set(json_schema.get("required", []))

    for field_name, field_info in model.model_fields.items():
        # Get field type annotation
        field_type = field_info.annotation

        # Determine Python type from Pydantic field
        python_type = _get_pydantic_field_type(
            field_type, field_info
        )

        # Check if nullable (Optional or Union with None)
        is_nullable = _is_nullable_type(field_type)

        # Get default value or example
        default_value = field_info.default
        if default_value is not ... and default_value is not None:
            # If default is callable (Field(default_factory=...)), use example
            if callable(default_value):
                example = _get_example_for_type(python_type)
            else:
                example = default_value
        else:
            example = _get_example_for_type(python_type)

        schema["fields"][field_name] = {
            "type": python_type,
            "types": [python_type] + (["NoneType"] if is_nullable else []),
            "example": example,
            "nullable": is_nullable or field_name not in required_fields,
        }

    return schema


def _get_pydantic_field_type(field_type: Any, _field_info: FieldInfo) -> str:
    """Get Python type string from Pydantic field type annotation.

    Args:
        field_type: Type annotation from Pydantic field
        field_info: Pydantic FieldInfo object

    Returns:
        String representation of the type
    """
    import typing
    from datetime import datetime

    # Handle Union types (including Optional)
    origin = typing.get_origin(field_type)
    if origin is typing.Union:
        args = typing.get_args(field_type)
        # Filter out NoneType
        non_none_args = [arg for arg in args if arg is not type(None)]
        if non_none_args:
            field_type = non_none_args[0]
            origin = typing.get_origin(field_type)

    # Handle List/List types
    if origin is list:
        return "list"
    if hasattr(typing, "List") and origin is typing.List:
        return "list"
    if origin is dict:
        return "dict"
    if hasattr(typing, "Dict") and origin is typing.Dict:
        return "dict"

    # Handle direct type checks
    if field_type is str or field_type == str:
        return "str"
    if field_type is int or field_type == int:
        return "int"
    if field_type is float or field_type == float:
        return "float"
    if field_type is bool or field_type == bool:
        return "bool"
    if field_type is datetime or field_type == datetime:
        return "datetime"
    if field_type is ObjectId or field_type == ObjectId:
        return "ObjectId"

    # Check if it's a BaseModel (nested model)
    if isinstance(field_type, type) and issubclass(field_type, BaseModel):
        return "dict"

    # Fallback: get type name
    if isinstance(field_type, type):
        type_name = field_type.__name__.lower()
        if type_name == "str":
            return "str"
        if type_name == "int":
            return "int"
        if type_name == "float":
            return "float"
        if type_name == "bool":
            return "bool"
        if "datetime" in type_name:
            return "datetime"

    return "str"  # Default fallback


def _is_nullable_type(field_type: Any) -> bool:
    """Check if a Pydantic field type is nullable.

    Args:
        field_type: Type annotation

    Returns:
        True if the type is nullable (Optional or Union with None)
    """
    import typing

    origin = typing.get_origin(field_type)
    if origin is typing.Union:
        args = typing.get_args(field_type)
        return type(None) in args

    # Check for Optional (which is Union[T, None])
    if hasattr(typing, "Optional"):
        if origin is typing.Optional:
            return True

    return False


def _get_example_for_type(python_type: str) -> Any:
    """Get example value for a Python type.

    Args:
        python_type: String representation of the type

    Returns:
        Example value for the type
    """
    examples = {
        "str": "",
        "int": 0,
        "float": 0.0,
        "bool": False,
        "list": [],
        "dict": {},
        "ObjectId": "",
        "datetime": None,
    }
    return examples.get(python_type, "")


def infer_schema_from_openapi(
    app: FastAPI,
    collection_name: str,
    schema_name: str | None = None,
) -> dict[str, Any] | None:
    """Infer schema from FastAPI OpenAPI/Swagger documentation.

    Args:
        app: FastAPI application instance
        collection_name: Name of the collection
        schema_name: Optional explicit schema name in OpenAPI components.
            If not provided, will try to find schema matching collection name.

    Returns:
        Schema dictionary in the same format as infer_schema,
        or None if not found
    """
    try:
        # Get OpenAPI schema
        # FastAPI caches the schema, so we just call openapi()
        # It will generate it if not already generated
        openapi_schema = app.openapi()

        if not openapi_schema:
            return None

        components = openapi_schema.get("components", {})
        if not components:
            return None

        schemas = components.get("schemas", {})
        if not schemas:
            return None

        # Determine which schema to use
        target_schema_name = schema_name

        # If no explicit schema name, try to find matching schema
        if target_schema_name is None:
            # Try exact match first
            if collection_name in schemas:
                target_schema_name = collection_name
            else:
                # Try case-insensitive match
                target_schema_name = next(
                    (
                        name for name in schemas.keys()
                        if name.lower() == collection_name.lower()
                    ),
                    None,
                )
                # Try plural/singular variations
                if target_schema_name is None:
                    # Try collection name as singular
                    # (e.g., "products" -> "Product")
                    singular = collection_name.rstrip("s")
                    if singular in schemas:
                        target_schema_name = singular
                    else:
                        # Try collection name as plural
                        # (e.g., "product" -> "Product")
                        plural = collection_name + "s"
                        if plural in schemas:
                            target_schema_name = plural
                        else:
                            # Try case-insensitive singular/plural
                            for name in schemas.keys():
                                name_lower = name.lower()
                                if (
                                    name_lower == singular.lower()
                                    or name_lower == plural.lower()
                                ):
                                    target_schema_name = name
                                    break

        if target_schema_name is None:
            return None

        schema_def = schemas.get(target_schema_name)
        if not schema_def:
            return None

        # Convert OpenAPI schema to our format
        return _convert_openapi_schema_to_internal(schema_def, schemas)
    except (AttributeError, KeyError, TypeError, ValueError) as e:
        # Log the error for debugging but return None
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(
            "Failed to infer schema from OpenAPI for collection '%s': %s",
            collection_name,
            e
        )
        return None


def _convert_openapi_schema_to_internal(
    schema_def: dict[str, Any],
    all_schemas: dict[str, Any],
) -> dict[str, Any]:
    """Convert OpenAPI schema definition to internal schema format.

    Args:
        schema_def: OpenAPI schema definition
        all_schemas: All available schemas for resolving references

    Returns:
        Schema in internal format
    """
    schema = {
        "fields": {},
        "sample_count": 0,
        "source": "openapi_schema",
    }

    properties = schema_def.get("properties", {})
    required_fields = set(schema_def.get("required", []))

    for field_name, field_def in properties.items():
        field_type = _get_type_from_openapi_field(field_def, all_schemas)
        field_type_list = field_def.get("type", [])
        is_nullable = (
            field_def.get("nullable", False)
            or "null" in field_type_list
        )

        # Get example or default
        example = field_def.get("example")
        if example is None:
            example = field_def.get("default")
        if example is None:
            example = _get_example_for_type(field_type)

        schema["fields"][field_name] = {
            "type": field_type,
            "types": [field_type] + (["NoneType"] if is_nullable else []),
            "example": example,
            "nullable": is_nullable or field_name not in required_fields,
        }

    return schema


def _get_type_from_openapi_field(
    field_def: dict[str, Any],
    all_schemas: dict[str, Any],
) -> str:
    """Extract Python type from OpenAPI field definition.

    Args:
        field_def: OpenAPI field definition
        all_schemas: All available schemas for resolving references

    Returns:
        Python type string
    """
    # Handle $ref (reference to another schema)
    if "$ref" in field_def:
        ref_path = field_def["$ref"]
        # Extract schema name from #/components/schemas/SchemaName
        schema_name = ref_path.split("/")[-1]
        ref_schema = all_schemas.get(schema_name, {})
        # If it's an object schema, return "dict"
        if ref_schema.get("type") == "object" or "properties" in ref_schema:
            return "dict"
        # Otherwise, try to get type from referenced schema
        return ref_schema.get("type", "dict")

    # Handle allOf, anyOf, oneOf
    if "allOf" in field_def:
        # Use first item in allOf
        return _get_type_from_openapi_field(field_def["allOf"][0], all_schemas)
    if "anyOf" in field_def or "oneOf" in field_def:
        # Use first item
        items = field_def.get("anyOf") or field_def.get("oneOf", [])
        if items:
            return _get_type_from_openapi_field(items[0], all_schemas)

    # Get type directly
    field_type = field_def.get("type")

    # Handle array types
    if field_type == "array":
        items = field_def.get("items", {})
        # Check if items is a reference
        if "$ref" in items:
            return "list"
        # For arrays, we return "list" regardless of item type
        return "list"

    # Map OpenAPI types to Python types
    type_mapping = {
        "string": "str",
        "integer": "int",
        "number": "float",
        "boolean": "bool",
        "object": "dict",
        "array": "list",
    }

    # Check for format hints
    format_type = field_def.get("format")
    if format_type == "date-time" or format_type == "date":
        return "datetime"

    # Handle enum (usually strings)
    if "enum" in field_def:
        return "str"

    # Return mapped type or default to str
    return type_mapping.get(field_type, "str")
