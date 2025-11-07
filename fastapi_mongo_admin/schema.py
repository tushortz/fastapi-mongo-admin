"""Schema introspection utilities for MongoDB collections."""

from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection


def serialize_object_id(obj: Any) -> Any:
    """Convert ObjectId to string for JSON serialization."""
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, dict):
        return {k: serialize_object_id(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [serialize_object_id(item) for item in obj]
    return obj


async def infer_schema(collection: AsyncIOMotorCollection, sample_size: int = 10) -> dict[str, Any]:
    """Infer schema from collection documents.

    Args:
        collection: MongoDB collection
        sample_size: Number of documents to sample for schema inference

    Returns:
        Dictionary with field types and examples
    """
    cursor = collection.find().limit(sample_size)
    documents = await cursor.to_list(length=sample_size)

    if not documents:
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
    priority = ["str", "int", "float", "bool", "dict", "list", "ObjectId", "NoneType"]

    for ptype in priority:
        if ptype in types:
            return ptype

    # Return first type if not in priority
    return sorted(types)[0] if types else "str"

