"""Schema inference tests."""

from tests.conftest import Product
from fastapi_mongo_admin.schemas.inference import infer_admin_fields, infer_schema_dict


def test_infer_admin_fields() -> None:
    fields = infer_admin_fields(Product)
    names = [f.name for f in fields]
    assert "name" in names
    assert "price" in names


def test_infer_schema_dict() -> None:
    schema = infer_schema_dict(Product)
    assert schema["model"] == "Product"
    assert "name" in schema["fields"]
