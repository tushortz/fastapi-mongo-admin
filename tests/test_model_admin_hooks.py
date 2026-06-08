"""ModelAdmin hook tests."""

from datetime import datetime
from unittest.mock import MagicMock

from pydantic import BaseModel

from fastapi_mongo_admin import AdminSite
from fastapi_mongo_admin.admin.actions import DELETE_SELECTED_ACTION
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


def test_default_delete_selected_action() -> None:
    admin = ProductAdmin(Product)
    names = [name for name, _, _ in admin.get_actions()]
    assert names[0] == DELETE_SELECTED_ACTION


def test_action_decorator() -> None:
    class Admin(ProductAdmin):
        actions = ["mark_inactive"]

        @action("Mark inactive")
        def mark_inactive(self, request, queryset) -> None:
            pass

    admin = Admin(Product)
    actions = admin.get_actions()
    names = [name for name, _, _ in actions]
    assert names[0] == DELETE_SELECTED_ACTION
    assert "mark_inactive" in names


def test_readonly_fields_render_at_bottom() -> None:
    class TimestampedProduct(BaseModel):
        name: str
        price: float
        category: str
        active: bool = True
        created_at: datetime | None = None
        updated_at: datetime | None = None

    class TimestampedProductAdmin(ProductAdmin):
        model = TimestampedProduct
        readonly_fields = ["created_at", "updated_at"]
        fieldsets = [
            (None, {"fields": ["name", "price", "category", "active", "created_at", "updated_at"]}),
        ]

    site = AdminSite()
    site.register(TimestampedProduct, TimestampedProductAdmin)
    admin = site.get_registered_models()["products"]
    ctx = build_form_context(
        MagicMock(),
        site,
        admin,
        "products",
        "/admin",
        obj={
            "name": "Phone",
            "price": 9.99,
            "category": "electronics",
            "active": True,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-02T00:00:00",
        },
    )

    fieldset_titles = [fs["title"] for fs in ctx["fieldsets"]]
    assert fieldset_titles[-1] == "Read-only"
    readonly_names = [field.name for field in ctx["fieldsets"][-1]["fields"]]
    assert readonly_names == ["created_at", "updated_at"]
    main_names = [field.name for field in ctx["fieldsets"][0]["fields"]]
    assert "created_at" not in main_names
    assert "updated_at" not in main_names


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
    name_field = next(f for fs in ctx["fieldsets"] for f in fs["fields"] if f.name == "name")
    assert name_field.attrs["placeholder"] == "from hook"


def test_permission_hooks() -> None:
    class RestrictedAdmin(ProductAdmin):
        def has_add_permission(self, request, user=None) -> bool:
            return user == "admin"

    admin = RestrictedAdmin(Product)
    assert admin.has_add_permission(None, "admin") is True
    assert admin.has_add_permission(None, "guest") is False
