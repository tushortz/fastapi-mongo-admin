"""ModelAdmin hook tests."""

from fastapi_mongo_admin.admin.decorators import action, display
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


def test_permission_hooks() -> None:
    class RestrictedAdmin(ProductAdmin):
        def has_add_permission(self, request, user=None) -> bool:
            return user == "admin"

    admin = RestrictedAdmin(Product)
    assert admin.has_add_permission(None, "admin") is True
    assert admin.has_add_permission(None, "guest") is False
