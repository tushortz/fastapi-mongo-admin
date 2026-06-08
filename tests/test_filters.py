"""Filter framework tests."""

from fastapi_mongo_admin.admin.filters import BooleanFieldListFilter, ChoiceListFilter, build_filter_query
from fastapi_mongo_admin.admin.filters.date import build_date_hierarchy_query
from tests.conftest import Product, ProductAdmin


def test_choice_filter_queryset() -> None:
    admin = ProductAdmin(Product)
    flt = ChoiceListFilter(None, {"category": "books"}, admin, "category")  # type: ignore[arg-type]
    assert flt.queryset("books") == {"category": "books"}


def test_boolean_filter_queryset() -> None:
    admin = ProductAdmin(Product)
    flt = BooleanFieldListFilter(None, {}, admin, "active")  # type: ignore[arg-type]
    assert flt.queryset("1") == {"active": True}
    assert flt.queryset("0") == {"active": False}


def test_build_filter_query() -> None:
    admin = ProductAdmin(Product)
    query = build_filter_query(admin, {"category": "books"})
    assert query == {"category": "books"}


def test_date_hierarchy_query() -> None:
    query = build_date_hierarchy_query("created_at", "2024", None, None)
    assert "created_at" in query
    assert "$gte" in query["created_at"]
