"""ModelAdmin configurations for the ecommerce demo."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

from fastapi import Request
from fastapi.responses import HTMLResponse

from fastapi_mongo_admin import AdminSite, ModelAdmin, action, display
from example.ecommerce.models import (
    Brand,
    Category,
    Coupon,
    Customer,
    DiscountType,
    LoyaltyTier,
    Order,
    OrderStatus,
    PaymentStatus,
    Product,
    ProductStatus,
    Review,
)

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"


class EcommerceAdminSite(AdminSite):
    """Admin site with ecommerce branding and template overrides."""

    site_header = "Ecommerce Admin"
    site_title = "Shop Manager"
    index_title = "Store administration"


def create_admin_site() -> EcommerceAdminSite:
    """Create a fresh admin site instance for the demo app."""
    return EcommerceAdminSite(template_dirs=[TEMPLATE_DIR])


class CategoryAdmin(ModelAdmin):
    """Category changelist and form configuration."""

    model = Category
    collection_name = "categories"
    list_display = ["name", "slug", "is_active", "sort_order", "created_at"]
    list_display_links = ["name"]
    list_filter = ["is_active"]
    search_fields = ["name", "slug", "description"]
    ordering = ["sort_order", "name"]
    list_per_page = 20
    fieldsets = [
        (None, {"fields": ["name", "slug", "description", "parent_id"]}),
        ("Display", {"fields": ["is_active", "sort_order", "image_url"]}),
        ("Timestamps", {"fields": ["created_at"]}),
    ]
    readonly_fields = ["created_at"]
    formfield_overrides = {
        "description": {"widget": "textarea", "rows": 5},
    }


class BrandAdmin(ModelAdmin):
    """Brand management."""

    model = Brand
    collection_name = "brands"
    list_display = ["name", "country", "is_active", "founded_year"]
    search_fields = ["name", "country"]
    list_filter = ["is_active", "country"]
    ordering = ["name"]


class ProductAdmin(ModelAdmin):
    """Product admin with fieldsets, filters, and bulk actions."""

    model = Product
    collection_name = "products"
    list_display = [
        "name",
        "sku",
        "price_display",
        "stock_quantity",
        "status",
        "is_featured",
        "category_id",
        "published_at",
    ]
    list_display_links = ["name", "sku"]
    list_filter = ["status", "is_featured", "is_taxable", "category_id"]
    search_fields = ["name", "sku", "slug", "short_description", "tags"]
    list_per_page = 25
    ordering = ["-created_at"]
    date_hierarchy = "published_at"
    list_select_related = {"category_id": "categories", "brand_id": "brands"}
    readonly_fields = ["created_at", "updated_at"]
    actions = ["delete_selected", "publish_products", "archive_products", "mark_featured"]
    choices = {
        "status": [(s.value, s.name.replace("_", " ").title()) for s in ProductStatus],
    }
    field_mapping = {
        "sku": "product_sku",
        "cost_price": "unit_cost",
    }
    fieldsets = [
        ("Basic info", {"fields": ["name", "sku", "slug", "short_description", "description"]}),
        ("Pricing", {"fields": ["price", "compare_at_price", "cost_price", "is_taxable"]}),
        (
            "Inventory",
            {"fields": ["stock_quantity", "low_stock_threshold", "weight_kg", "dimensions"]},
        ),
        ("Catalog", {"fields": ["category_id", "brand_id", "tags", "status", "is_featured"]}),
        ("SEO", {"fields": ["meta_title", "meta_description"]}),
        ("Advanced", {"fields": ["attributes", "created_at", "updated_at", "published_at"]}),
    ]

    @display(description="Price", ordering="price")
    def price_display(self, obj: dict[str, Any]) -> str:
        price = obj.get("price", 0)
        return f"${Decimal(str(price)):,.2f}"

    @display(description="Low stock?")
    def low_stock_badge(self, obj: dict[str, Any]) -> str:
        qty = int(obj.get("stock_quantity", 0))
        threshold = int(obj.get("low_stock_threshold", 5))
        return "YES" if qty <= threshold else "no"

    @action("Publish selected products")
    async def publish_products(self, request: Request, queryset: list[dict[str, Any]]) -> None:
        _ = request
        for _item in queryset:
            pass  # Hook: call repository or service layer in a real app

    @action("Archive selected products")
    async def archive_products(self, request: Request, queryset: list[dict[str, Any]]) -> None:
        _ = request, queryset

    @action("Mark as featured")
    async def mark_featured(self, request: Request, queryset: list[dict[str, Any]]) -> None:
        _ = request, queryset

    async def save_model(
        self,
        request: Request | None,
        obj: dict[str, Any],
        form_data: dict[str, Any],
        is_new: bool,
    ) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        form_data["updated_at"] = now.isoformat()
        if is_new:
            form_data.setdefault("created_at", now.isoformat())
        return form_data

    def has_delete_permission(
        self,
        request: Request | None,
        user: Any = None,
        obj: dict[str, Any] | None = None,
    ) -> bool:
        return bool(user and user.get("role") in ("admin", "manager"))


class CustomerAdmin(ModelAdmin):
    """Customer profiles with loyalty tiers."""

    model = Customer
    collection_name = "customers"
    list_display = [
        "full_name",
        "email",
        "loyalty_tier",
        "total_orders",
        "lifetime_value",
        "is_active",
        "created_at",
    ]
    list_display_links = ["full_name", "email"]
    search_fields = ["email", "first_name", "last_name", "phone"]
    list_filter = ["loyalty_tier", "is_active", "marketing_opt_in"]
    ordering = ["-created_at"]
    choices = {
        "loyalty_tier": [(t.value, t.name.title()) for t in LoyaltyTier],
    }
    fieldsets = [
        ("Identity", {"fields": ["email", "first_name", "last_name", "phone", "date_of_birth"]}),
        ("Preferences", {"fields": ["loyalty_tier", "marketing_opt_in", "is_active"]}),
        ("Address", {"fields": ["default_shipping"]}),
        ("Metrics", {"fields": ["total_orders", "lifetime_value", "notes", "created_at"]}),
    ]

    @display(description="Name")
    def full_name(self, obj: dict[str, Any]) -> str:
        return f"{obj.get('first_name', '')} {obj.get('last_name', '')}".strip()


class OrderAdmin(ModelAdmin):
    """Order management with date hierarchy and payment filters."""

    model = Order
    collection_name = "orders"
    list_display = [
        "order_number",
        "customer_id",
        "status",
        "payment_status",
        "total",
        "currency",
        "placed_at",
    ]
    list_display_links = ["order_number"]
    list_filter = ["status", "payment_status", "currency"]
    search_fields = ["order_number", "coupon_code", "notes"]
    ordering = ["-placed_at"]
    date_hierarchy = "placed_at"
    list_select_related = {"customer_id": "customers"}
    list_per_page = 30
    choices = {
        "status": [(s.value, s.name.title()) for s in OrderStatus],
        "payment_status": [(s.value, s.name.replace("_", " ").title()) for s in PaymentStatus],
        "currency": [("USD", "USD"), ("EUR", "EUR"), ("GBP", "GBP")],
    }
    fieldsets = [
        (
            "Order",
            {"fields": ["order_number", "customer_id", "status", "payment_status", "placed_at"]},
        ),
        (
            "Amounts",
            {
                "fields": [
                    "currency",
                    "subtotal",
                    "tax_amount",
                    "shipping_cost",
                    "discount_amount",
                    "total",
                ]
            },
        ),
        ("Items", {"fields": ["line_items", "coupon_code"]}),
        ("Addresses", {"fields": ["shipping_address", "billing_address"]}),
        ("Notes", {"fields": ["notes", "shipped_at"]}),
    ]
    readonly_fields = ["order_number"]


class ReviewAdmin(ModelAdmin):
    """Product reviews moderation."""

    model = Review
    collection_name = "reviews"
    list_display = [
        "title",
        "rating",
        "product_id",
        "is_approved",
        "is_verified_purchase",
        "created_at",
    ]
    list_filter = ["rating", "is_approved", "is_verified_purchase"]
    search_fields = ["title", "body"]
    ordering = ["-created_at"]
    list_select_related = {"product_id": "products", "customer_id": "customers"}
    actions = ["delete_selected", "approve_reviews"]

    @action("Approve selected reviews")
    async def approve_reviews(self, request: Request, queryset: list[dict[str, Any]]) -> None:
        _ = request, queryset


class CouponAdmin(ModelAdmin):
    """Promotional coupons."""

    model = Coupon
    collection_name = "coupons"
    list_display = [
        "code",
        "discount_type",
        "discount_value",
        "used_count",
        "is_active",
        "valid_until",
    ]
    list_filter = ["discount_type", "is_active"]
    search_fields = ["code", "description"]
    ordering = ["-valid_from"]
    choices = {
        "discount_type": [(d.value, d.name.title()) for d in DiscountType],
    }
    formfield_overrides = {
        "description": {"widget": "textarea", "rows": 3},
        "valid_from": {"min": "2020-01-01"},
        "valid_until": {"max": "2099-12-31"},
    }


async def ecommerce_dashboard(request: Request) -> HTMLResponse:
    """Custom admin dashboard page."""
    _ = request
    html = """
    <!DOCTYPE html>
    <html lang="en" data-theme="light">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>Dashboard | Ecommerce Admin</title>
      <link rel="stylesheet" href="/admin/static/admin.css">
    </head>
    <body>
    <header class="base-header admin-header">
      <div class="base-header__inner header-inner">
        <div class="base-header__brand branding"><a href="/admin/">Ecommerce Admin</a></div>
      </div>
    </header>
    <div class="base-layout admin-container">
      <main class="base-card admin-main">
        <h1 class="base-heading-1">Store dashboard</h1>
        <p class="base-text-secondary">Custom admin view registered via <code>site.register_view()</code>.</p>
        <ul>
          <li><a href="/admin/products/">Manage products</a></li>
          <li><a href="/admin/orders/">Manage orders</a></li>
          <li><a href="/admin/customers/">Manage customers</a></li>
        </ul>
      </main>
    </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


def register_admins(site: AdminSite | None = None) -> AdminSite:
    """Register all ecommerce models on the admin site."""
    site = site or create_admin_site()
    site.register(Category, CategoryAdmin)
    site.register(Brand, BrandAdmin)
    site.register(Product, ProductAdmin)
    site.register(Customer, CustomerAdmin)
    site.register(Order, OrderAdmin)
    site.register(Review, ReviewAdmin)
    site.register(Coupon, CouponAdmin)
    site.register_view("dashboard", "/dashboard/", ecommerce_dashboard)
    return site
