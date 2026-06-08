"""Pydantic models for the ecommerce demo."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel, EmailStr, Field


class ProductStatus(str, Enum):
    """Product lifecycle status."""

    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    OUT_OF_STOCK = "out_of_stock"


class OrderStatus(str, Enum):
    """Order fulfillment status."""

    PENDING = "pending"
    PAID = "paid"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentStatus(str, Enum):
    """Payment processing status."""

    UNPAID = "unpaid"
    AUTHORIZED = "authorized"
    CAPTURED = "captured"
    FAILED = "failed"
    REFUNDED = "refunded"


class DiscountType(str, Enum):
    """Coupon discount calculation type."""

    PERCENTAGE = "percentage"
    FIXED = "fixed"


class LoyaltyTier(str, Enum):
    """Customer loyalty program tier."""

    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"


class Category(BaseModel):
    """Product category with hierarchy support."""

    name: str
    slug: str
    description: str = ""
    parent_id: str | None = None
    is_active: bool = True
    sort_order: int = 0
    image_url: str | None = None
    created_at: datetime | None = None


class Brand(BaseModel):
    """Product brand / manufacturer."""

    name: str
    slug: str
    country: str = ""
    website: str | None = None
    description: str = ""
    is_active: bool = True
    founded_year: int | None = None


class ProductDimensions(BaseModel):
    """Physical dimensions in centimeters."""

    length_cm: float = 0.0
    width_cm: float = 0.0
    height_cm: float = 0.0


class Product(BaseModel):
    """Full product catalog entry with pricing, inventory, and SEO fields."""

    name: str
    sku: str
    slug: str
    short_description: str = ""
    description: str = ""
    price: Decimal = Field(ge=0)
    compare_at_price: Decimal | None = None
    cost_price: Decimal | None = None
    category_id: str | None = None
    brand_id: str | None = None
    stock_quantity: int = Field(default=0, ge=0)
    low_stock_threshold: int = Field(default=5, ge=0)
    weight_kg: float = Field(default=0.0, ge=0)
    dimensions: ProductDimensions | None = None
    tags: list[str] = Field(default_factory=list)
    status: ProductStatus = ProductStatus.DRAFT
    is_featured: bool = False
    is_taxable: bool = True
    meta_title: str | None = None
    meta_description: str | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    published_at: datetime | None = None


class CustomerAddress(BaseModel):
    """Embedded shipping or billing address."""

    line1: str
    line2: str = ""
    city: str
    state: str = ""
    postal_code: str
    country: str = "US"


class Customer(BaseModel):
    """Registered shopper profile."""

    email: EmailStr
    first_name: str
    last_name: str
    phone: str | None = None
    date_of_birth: date | None = None
    loyalty_tier: LoyaltyTier = LoyaltyTier.BRONZE
    marketing_opt_in: bool = False
    default_shipping: CustomerAddress | None = None
    notes: str = ""
    is_active: bool = True
    total_orders: int = 0
    lifetime_value: Decimal = Decimal("0.00")
    created_at: datetime | None = None


class OrderLineItem(BaseModel):
    """Single line on an order."""

    product_id: str
    sku: str
    name: str
    quantity: int = Field(ge=1)
    unit_price: Decimal = Field(ge=0)
    discount: Decimal = Field(default=Decimal("0.00"), ge=0)


class Order(BaseModel):
    """Customer purchase order."""

    order_number: str
    customer_id: str | None = None
    status: OrderStatus = OrderStatus.PENDING
    payment_status: PaymentStatus = PaymentStatus.UNPAID
    currency: str = "USD"
    line_items: list[OrderLineItem] = Field(default_factory=list)
    subtotal: Decimal = Decimal("0.00")
    tax_amount: Decimal = Decimal("0.00")
    shipping_cost: Decimal = Decimal("0.00")
    discount_amount: Decimal = Decimal("0.00")
    total: Decimal = Decimal("0.00")
    shipping_address: CustomerAddress | None = None
    billing_address: CustomerAddress | None = None
    coupon_code: str | None = None
    notes: str = ""
    placed_at: datetime | None = None
    shipped_at: datetime | None = None


class Review(BaseModel):
    """Product review submitted by a customer."""

    product_id: str
    customer_id: str | None = None
    rating: int = Field(ge=1, le=5)
    title: str
    body: str = ""
    is_verified_purchase: bool = False
    is_approved: bool = False
    helpful_count: int = 0
    created_at: datetime | None = None


class Coupon(BaseModel):
    """Promotional discount code."""

    code: str
    description: str = ""
    discount_type: DiscountType
    discount_value: Decimal = Field(gt=0)
    min_order_value: Decimal | None = None
    max_uses: int | None = None
    used_count: int = 0
    is_active: bool = True
    valid_from: datetime | None = None
    valid_until: datetime | None = None
