"""Field mapping tests."""

from fastapi_mongo_admin.services.mapping import translate_from_db, translate_query, translate_to_db


def test_translate_to_db() -> None:
    mapping = {"name": "product_name"}
    assert translate_to_db({"name": "x"}, mapping) == {"product_name": "x"}


def test_translate_from_db() -> None:
    mapping = {"name": "product_name"}
    assert translate_from_db({"product_name": "x"}, mapping) == {"name": "x"}


def test_translate_query_operators() -> None:
    mapping = {"name": "product_name"}
    query = {"$or": [{"name": "a"}]}
    result = translate_query(query, mapping)
    assert result == {"$or": [{"product_name": "a"}]}
