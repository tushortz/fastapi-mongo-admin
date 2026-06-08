"""ModelAdmin hook tests."""

from unittest.mock import MagicMock

from fastapi_mongo_admin import AdminSite
from fastapi_mongo_admin.admin.decorators import action, display
from fastapi_mongo_admin.admin.fields.base import AdminField
from fastapi_mongo_admin.views.context import build_form_context
from tests.conftest import Product, ProductAdmin


def test_display_decorator() -> None:
    class Admin(ProductAdmin):
        @display(description="Product Name")
        def name_display(self, obj: dict) -> str:
            return str(obj.get("name", "")).upper()

    admin = Admin(Product)
    assert admin.name_display({"name": "test"}) == "TEST"
    assert admin.get_list_display() == ["name", "category", "price", "active"]


def test_action_decorator() -> None:
    class Admin(ProductAdmin):
        actions = ["mark_inactive"]

        @action("Mark inactive")
        def mark_inactive(self, request, queryset) -> None:
            pass

    admin = Admin(Product)
    actions = admin.get_actions()
    assert len(actions) == 1
    assert actions[0][0] == "mark_inactive"


def test_formfield_for_field_hook() -> None:
    class CustomAdmin(ProductAdmin):
        def formfield_for_field(
            self,
            field: AdminField,
            request=None,
            obj=None,
        ) -> AdminField:
            if field.name == "name":
                field.attrs["placeholder"] = "from hook"
            return field

    site = AdminSite()
    site.register(Product, CustomAdmin)
    admin = site.get_registered_models()["products"]
    ctx = build_form_context(MagicMock(), site, admin, "products", "/admin")
    name_field = next(
        f for fs in ctx["fieldsets"] for f in fs["fields"] if f.name == "name"
    )
    assert name_field.attrs["placeholder"] == "from hook"


def test_permission_hooks() -> None:
    class RestrictedAdmin(ProductAdmin):
        def has_add_permission(self, request, user=None) -> bool:
            return user == "admin"

    admin = RestrictedAdmin(Product)
    assert admin.has_add_permission(None, "admin") is True
    assert admin.has_add_permission(None, "guest") is False
