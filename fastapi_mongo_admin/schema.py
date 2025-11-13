"""Schema introspection utilities for MongoDB collections."""

import enum
import logging
import typing
from datetime import datetime
from decimal import Decimal
from typing import Any, Type

from bson import ObjectId
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorCollection
from pydantic import BaseModel
from pydantic.fields import FieldInfo

# Handle Pydantic v2 undefined values
try:
    from pydantic_core import PydanticUndefined

    def is_pydantic_undefined(value: Any) -> bool:
        """Check if a value is PydanticUndefined."""
        return value is PydanticUndefined or isinstance(value, type(PydanticUndefined))

except ImportError:
    # Fallback for older Pydantic versions
    PydanticUndefined = None

    def is_pydantic_undefined(value: Any) -> bool:
        """Check if a value is Ellipsis (Pydantic v1 undefined)."""
        return value is ...


def serialize_object_id(obj: Any) -> Any:
    """Convert ObjectId to string for JSON serialization."""
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, dict):
        return {k: serialize_object_id(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [serialize_object_id(item) for item in obj]
    return obj


def ensure_json_serializable(obj: Any) -> Any:
    """Ensure an object is JSON-serializable.

    This function handles PydanticUndefined, FieldInfo objects, and other
    non-serializable types that might appear in schema responses.

    Args:
        obj: Object to make JSON-serializable

    Returns:
        JSON-serializable version of the object
    """
    # Handle PydanticUndefined
    if is_pydantic_undefined(obj):
        return None

    # Handle ObjectId
    if isinstance(obj, ObjectId):
        return str(obj)

    # Handle datetime
    if isinstance(obj, datetime):
        return obj.isoformat()

    # Handle dict
    if isinstance(obj, dict):
        return {k: ensure_json_serializable(v) for k, v in obj.items()}

    # Handle list
    if isinstance(obj, list):
        return [ensure_json_serializable(item) for item in obj]

    # Handle FieldInfo and other Pydantic objects
    if hasattr(obj, "__class__"):
        class_name = obj.__class__.__name__
        if "FieldInfo" in class_name or "PydanticUndefined" in class_name:
            return None

    # For basic types, return as-is
    if isinstance(obj, (str, int, float, bool, type(None))):
        return obj

    # For unknown types, try to convert to string
    try:
        # Check if it's iterable (but not a string)
        if hasattr(obj, "__iter__") and not isinstance(obj, (str, bytes)):
            # If it's iterable but not a basic type, convert to list
            return [ensure_json_serializable(item) for item in obj]
    except (TypeError, AttributeError):
        pass

    # Last resort: convert to string
    try:
        return str(obj)
    except Exception:
        return None


def serialize_for_export(obj: Any) -> Any:
    """Serialize MongoDB objects for export (handles ObjectId, datetime, etc.).

    This function converts MongoDB-specific types to JSON-serializable formats:
    - ObjectId -> string
    - datetime -> ISO format string
    - Other types are passed through

    Args:
        obj: Object to serialize (can be dict, list, or primitive)

    Returns:
        Serialized object suitable for JSON/YAML/CSV export
    """
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: serialize_for_export(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [serialize_for_export(item) for item in obj]
    # Handle other MongoDB types that might not be JSON serializable
    try:
        # Try to convert to string if it's a known MongoDB type
        if hasattr(obj, "__class__") and "bson" in str(type(obj).__module__):
            return str(obj)
    except Exception:
        pass
    return obj


async def infer_schema(
    _collection: AsyncIOMotorCollection,
    _sample_size: int = 10,
    pydantic_model: Type[BaseModel] | None = None,
) -> dict[str, Any]:
    """Infer schema from Pydantic model only.

    Schema is NOT inferred from MongoDB documents.
    Only Pydantic models are used for datatype inference.

    Args:
        _collection: MongoDB collection (not used, kept for API
            compatibility)
        _sample_size: Number of documents to sample (not used, kept
            for API compatibility)
        pydantic_model: Optional Pydantic model to use for schema
            inference

    Returns:
        Dictionary with field types and examples
    """
    # Only use Pydantic model for schema inference
    # Do not analyze MongoDB documents
    if pydantic_model is not None:
        return infer_schema_from_pydantic(pydantic_model)

    # Return empty schema if no Pydantic model provided
    return {"fields": {}, "sample_count": 0}


def infer_schema_from_pydantic(model: Type[BaseModel]) -> dict[str, Any]:
    """Infer schema from a Pydantic model.

    Args:
        model: Pydantic BaseModel class

    Returns:
        Dictionary with field types and examples matching the format
        returned by infer_schema.

    Raises:
        TypeError: If model is not a Pydantic BaseModel
        AttributeError: If model doesn't have required Pydantic attributes
    """
    if not isinstance(model, type) or not issubclass(model, BaseModel):
        raise TypeError(f"Expected Pydantic BaseModel, got {type(model).__name__}")

    schema = {
        "fields": {},
        "sample_count": 0,
        "source": "pydantic_model",
    }

    # Get the model's JSON schema
    try:
        json_schema = model.model_json_schema()
    except Exception as e:
        raise AttributeError(f"Failed to get JSON schema from Pydantic model: {str(e)}") from e

    # Extract field information
    required_fields = set(json_schema.get("required", []))
    properties = json_schema.get("properties", {})

    for field_name, field_info in model.model_fields.items():
        # Get field type annotation
        field_type = field_info.annotation

        # Determine Python type from Pydantic field
        python_type = _get_pydantic_field_type(field_type, field_info)

        # Check if nullable (Optional or Union with None)
        is_nullable = _is_nullable_type(field_type)

        # Get default value or example
        default_value = field_info.default
        # Check for PydanticUndefined (Pydantic v2) or Ellipsis (Pydantic v1)
        is_undefined = is_pydantic_undefined(default_value)

        if not is_undefined and default_value is not None:
            # If default is callable (Field(default_factory=...)), use example
            if callable(default_value):
                example = _get_example_for_type(python_type)
            else:
                # Use default value as example, but ensure it's JSON-serializable
                # Check if value is a basic JSON-serializable type
                if isinstance(default_value, (str, int, float, bool, type(None))):
                    example = default_value
                elif isinstance(default_value, (list, dict)):
                    # For lists and dicts, we could use them, but to be safe,
                    # let's use a simple example to avoid serialization issues
                    example = _get_example_for_type(python_type)
                else:
                    # For any other type (complex objects, etc.), use example
                    # This prevents serialization errors with non-serializable types
                    example = _get_example_for_type(python_type)
        else:
            example = _get_example_for_type(python_type)

        # Check for enum values
        enum_values = _get_enum_values_from_pydantic_field(field_type, field_info)

        # Extract validation constraints from JSON schema properties
        field_json_schema = properties.get(field_name, {})
        constraints = _extract_pydantic_constraints(field_json_schema, python_type)

        # Check for readonly field (from FieldInfo or JSON schema)
        is_readonly = False
        if hasattr(field_info, "json_schema_extra") and field_info.json_schema_extra:
            if isinstance(field_info.json_schema_extra, dict):
                is_readonly = field_info.json_schema_extra.get("readonly", False)
        field_json_schema = properties.get(field_name, {})
        if not is_readonly:
            is_readonly = field_json_schema.get("readOnly", False) or field_json_schema.get(
                "readonly", False
            )

        field_schema = {
            "type": python_type,
            "types": [python_type] + (["NoneType"] if is_nullable else []),
            "example": example,
            "nullable": is_nullable or field_name not in required_fields,
        }
        if enum_values:
            field_schema["enum"] = enum_values
        if constraints:
            field_schema["constraints"] = constraints
        if is_readonly:
            field_schema["readonly"] = True

        schema["fields"][field_name] = field_schema

    return schema


def _get_pydantic_field_type(field_type: Any, _field_info: FieldInfo) -> str:
    """Get Python type string from Pydantic field type annotation.

    Args:
        field_type: Type annotation from Pydantic field
        field_info: Pydantic FieldInfo object

    Returns:
        String representation of the type
    """
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
    if field_type is str:
        return "str"
    if field_type is int:
        return "int"
    if field_type is float:
        return "float"
    if field_type is bool:
        return "bool"
    if field_type is datetime:
        return "datetime"
    if field_type is ObjectId:
        return "ObjectId"

    # Check for Decimal type
    try:
        if field_type is Decimal or field_type == Decimal:
            return "decimal"
    except ImportError:
        pass

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
        if type_name == "decimal":
            return "decimal"
        if "datetime" in type_name:
            return "datetime"

    return "str"  # Default fallback


def _get_enum_values_from_pydantic_field(
    field_type: Any,
    _field_info: FieldInfo,
) -> list[Any] | None:
    """Extract enum values from Pydantic field.

    Args:
        field_type: Type annotation from Pydantic field
        field_info: Pydantic FieldInfo object

    Returns:
        List of enum values if field is an enum, None otherwise
    """
    # Check if it's a Literal type (enum-like)
    origin = typing.get_origin(field_type)
    if origin is typing.Literal:
        args = typing.get_args(field_type)
        if args:
            return list(args)

    # Check if it's an Enum type
    if isinstance(field_type, type) and issubclass(field_type, enum.Enum):
        return [e.value for e in field_type]

    # Check if it's a Union of Literals (common pattern)
    if origin is typing.Union:
        args = typing.get_args(field_type)
        # Filter out None
        non_none_args = [arg for arg in args if arg is not type(None)]
        if len(non_none_args) == 1:
            literal_origin = typing.get_origin(non_none_args[0])
            if literal_origin is typing.Literal:
                literal_args = typing.get_args(non_none_args[0])
                if literal_args:
                    return list(literal_args)

    return None


def _extract_pydantic_constraints(
    field_json_schema: dict[str, Any], python_type: str
) -> dict[str, Any] | None:
    """Extract validation constraints from JSON schema.

    Args:
        field_json_schema: JSON schema dictionary for the field
        python_type: Python type string (str, int, float, etc.)

    Returns:
        Dictionary with constraints or None if no constraints
    """
    constraints = {}

    try:
        # Check for numeric constraints (gt, lt, ge, le)
        if python_type in ("int", "integer", "float", "double", "number"):
            if "minimum" in field_json_schema:
                constraints["ge"] = field_json_schema["minimum"]
            if "exclusiveMinimum" in field_json_schema:
                constraints["gt"] = field_json_schema["exclusiveMinimum"]
            if "maximum" in field_json_schema:
                constraints["le"] = field_json_schema["maximum"]
            if "exclusiveMaximum" in field_json_schema:
                constraints["lt"] = field_json_schema["exclusiveMaximum"]

        # Check for string constraints (min_length, max_length, pattern)
        if python_type in ("str", "string", "text"):
            if "minLength" in field_json_schema:
                constraints["min_length"] = field_json_schema["minLength"]
            if "maxLength" in field_json_schema:
                constraints["max_length"] = field_json_schema["maxLength"]
            if "pattern" in field_json_schema:
                constraints["pattern"] = field_json_schema["pattern"]

    except Exception:
        # If extraction fails, return None
        pass

    return constraints if constraints else None


def _is_nullable_type(field_type: Any) -> bool:
    """Check if a Pydantic field type is nullable.

    Args:
        field_type: Type annotation

    Returns:
        True if the type is nullable (Optional or Union with None)
    """
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
        "str": "some text",
        "string": "some text",
        "text": "some text",
        "int": 42,
        "integer": 42,
        "float": 3.14,
        "double": 3.14,
        "number": 3.14,
        "decimal": 3.14,
        "bool": True,
        "boolean": True,
        "list": ["item1", "item2"],
        "array": ["item1", "item2"],
        "dict": {"key": "value"},
        "object": {"key": "value"},
        "objectid": str(ObjectId()),
        "datetime": datetime.now().isoformat(),
        "date": datetime.now().date().isoformat(),
        "timestamp": datetime.now().isoformat(),
        "time": datetime.now().time().isoformat(),
        "email": "user@example.com",
        "email_str": "user@example.com",
        "url": "https://example.com",
        "uri": "https://example.com",
        "uuid": "550e8400-e29b-41d4-a716-446655440000",
    }
    return examples.get(python_type.lower(), "example")


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

        # If no explicit schema name, try automatic discovery
        if target_schema_name is None:
            # Try exact match first
            if collection_name in schemas:
                target_schema_name = collection_name
            else:
                # Try case-insensitive match
                target_schema_name = next(
                    (name for name in schemas.keys() if name.lower() == collection_name.lower()),
                    None,
                )
                # Try plural/singular variations
                if target_schema_name is None:
                    # Try collection name as singular (capitalize first letter)
                    # (e.g., "products" -> "Product")
                    singular = collection_name.rstrip("s")
                    singular_capitalized = singular.capitalize()
                    if singular_capitalized in schemas:
                        target_schema_name = singular_capitalized
                    elif singular in schemas:
                        target_schema_name = singular
                    else:
                        # Try collection name as plural
                        # (capitalize first letter)
                        # (e.g., "product" -> "Product")
                        plural = collection_name + "s"
                        plural_capitalized = plural.capitalize()
                        if plural_capitalized in schemas:
                            target_schema_name = plural_capitalized
                        elif plural in schemas:
                            target_schema_name = plural
                        else:
                            # Try case-insensitive singular/plural with
                            # capitalization
                            for name in schemas.keys():
                                name_lower = name.lower()
                                if (
                                    name_lower == singular.lower()
                                    or name_lower == plural.lower()
                                    or name_lower == (singular_capitalized.lower())
                                    or name_lower == (plural_capitalized.lower())
                                ):
                                    target_schema_name = name
                                    break

                            # Last resort: try to find any schema that contains
                            # collection name
                            if target_schema_name is None:
                                collection_lower = collection_name.lower()
                                for name in schemas.keys():
                                    name_lower = name.lower()
                                    if (
                                        collection_lower in name_lower
                                        or name_lower in collection_lower
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
        logger = logging.getLogger(__name__)
        logger.debug(
            "Failed to infer schema from OpenAPI for collection '%s': %s", collection_name, e
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
        is_nullable = field_def.get("nullable", False) or "null" in field_type_list

        # Get example or default
        example = field_def.get("example")
        if example is None:
            example = field_def.get("default")
        # Never use None as example - always generate one from type
        if example is None:
            example = _get_example_for_type(field_type)

        # Check for enum values
        enum_values = field_def.get("enum")
        if enum_values and isinstance(enum_values, list):
            # Ensure enum values are serializable
            enum_values = [
                str(v) if not isinstance(v, (str, int, float, bool)) else v for v in enum_values
            ]

        # Check for readonly field
        is_readonly = field_def.get("readOnly", False) or field_def.get("readonly", False)

        field_schema = {
            "type": field_type,
            "types": [field_type] + (["NoneType"] if is_nullable else []),
            "example": example,
            "nullable": is_nullable or field_name not in required_fields,
        }
        if enum_values:
            field_schema["enum"] = enum_values
        if is_readonly:
            field_schema["readonly"] = True

        schema["fields"][field_name] = field_schema

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
    # Check for decimal format
    if format_type == "decimal" or format_type == "money":
        return "decimal"

    # Handle enum (usually strings)
    if "enum" in field_def:
        return "str"

    # Return mapped type or default to str
    return type_mapping.get(field_type, "str")
