"""Seed MongoDB with sample ecommerce data."""

from __future__ import annotations

import asyncio
import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

NOW = datetime.now(timezone.utc)


def _oid() -> ObjectId:
    return ObjectId()


async def seed_database(db_name: str = "ecommerce_demo", mongo_url: str | None = None) -> None:
    """Insert sample categories, products, customers, orders, reviews, and coupons."""
    url = mongo_url or os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    client = AsyncIOMotorClient(url)
    db = client[db_name]

    await db.categories.delete_many({})
    await db.brands.delete_many({})
    await db.products.delete_many({})
    await db.customers.delete_many({})
    await db.orders.delete_many({})
    await db.reviews.delete_many({})
    await db.coupons.delete_many({})

    electronics_id = _oid()
    clothing_id = _oid()
    home_id = _oid()

    await db.categories.insert_many(
        [
            {
                "_id": electronics_id,
                "name": "Electronics",
                "slug": "electronics",
                "description": "Gadgets, devices, and accessories",
                "is_active": True,
                "sort_order": 1,
                "created_at": NOW,
            },
            {
                "_id": clothing_id,
                "name": "Clothing",
                "slug": "clothing",
                "description": "Apparel and fashion",
                "is_active": True,
                "sort_order": 2,
                "created_at": NOW,
            },
            {
                "_id": home_id,
                "name": "Home & Garden",
                "slug": "home-garden",
                "description": "Furniture and decor",
                "is_active": True,
                "sort_order": 3,
                "created_at": NOW,
            },
        ]
    )

    brand_ids = [_oid(), _oid(), _oid()]
    await db.brands.insert_many(
        [
            {
                "_id": brand_ids[0],
                "name": "TechNova",
                "slug": "technova",
                "country": "US",
                "is_active": True,
                "founded_year": 2010,
            },
            {
                "_id": brand_ids[1],
                "name": "UrbanWear",
                "slug": "urbanwear",
                "country": "UK",
                "is_active": True,
                "founded_year": 2005,
            },
            {
                "_id": brand_ids[2],
                "name": "GreenHome",
                "slug": "greenhome",
                "country": "DE",
                "is_active": True,
                "founded_year": 2018,
            },
        ]
    )

    product_ids = [_oid() for _ in range(6)]
    await db.products.insert_many(
        [
            {
                "_id": product_ids[0],
                "name": "Wireless Noise-Cancelling Headphones",
                "product_sku": "WH-1000",
                "slug": "wireless-headphones",
                "short_description": "Premium over-ear headphones",
                "description": "Industry-leading noise cancellation with 30-hour battery life.",
                "price": Decimal("249.99"),
                "compare_at_price": Decimal("299.99"),
                "unit_cost": Decimal("120.00"),
                "category_id": electronics_id,
                "brand_id": brand_ids[0],
                "stock_quantity": 85,
                "low_stock_threshold": 10,
                "weight_kg": 0.35,
                "dimensions": {"length_cm": 20, "width_cm": 18, "height_cm": 8},
                "tags": ["audio", "wireless", "bestseller"],
                "status": "active",
                "is_featured": True,
                "is_taxable": True,
                "meta_title": "Wireless Headphones | TechNova",
                "attributes": {"color": "black", "bluetooth": "5.3"},
                "created_at": NOW - timedelta(days=30),
                "updated_at": NOW,
                "published_at": NOW - timedelta(days=28),
            },
            {
                "_id": product_ids[1],
                "name": "Smart Fitness Watch",
                "product_sku": "FW-200",
                "slug": "fitness-watch",
                "short_description": "Track health metrics 24/7",
                "description": "Heart rate, GPS, sleep tracking, and 50+ sport modes.",
                "price": Decimal("179.00"),
                "unit_cost": Decimal("75.00"),
                "category_id": electronics_id,
                "brand_id": brand_ids[0],
                "stock_quantity": 42,
                "low_stock_threshold": 8,
                "weight_kg": 0.05,
                "tags": ["wearable", "fitness"],
                "status": "active",
                "is_featured": True,
                "is_taxable": True,
                "created_at": NOW - timedelta(days=20),
                "updated_at": NOW,
                "published_at": NOW - timedelta(days=18),
            },
            {
                "_id": product_ids[2],
                "name": "Organic Cotton T-Shirt",
                "product_sku": "TS-ORG-01",
                "slug": "organic-cotton-tee",
                "short_description": "Soft sustainable everyday tee",
                "description": "100% organic cotton, pre-shrunk, unisex fit.",
                "price": Decimal("29.99"),
                "unit_cost": Decimal("8.50"),
                "category_id": clothing_id,
                "brand_id": brand_ids[1],
                "stock_quantity": 200,
                "low_stock_threshold": 25,
                "weight_kg": 0.2,
                "tags": ["organic", "basics"],
                "status": "active",
                "is_featured": False,
                "is_taxable": True,
                "created_at": NOW - timedelta(days=60),
                "updated_at": NOW,
                "published_at": NOW - timedelta(days=55),
            },
            {
                "_id": product_ids[3],
                "name": "Winter Parka Jacket",
                "product_sku": "JK-WIN-42",
                "slug": "winter-parka",
                "short_description": "Waterproof insulated parka",
                "description": "Rated to -20°C with removable faux-fur hood.",
                "price": Decimal("189.99"),
                "compare_at_price": Decimal("229.99"),
                "unit_cost": Decimal("70.00"),
                "category_id": clothing_id,
                "brand_id": brand_ids[1],
                "stock_quantity": 3,
                "low_stock_threshold": 5,
                "weight_kg": 1.2,
                "tags": ["outerwear", "winter"],
                "status": "out_of_stock",
                "is_featured": False,
                "is_taxable": True,
                "created_at": NOW - timedelta(days=90),
                "updated_at": NOW,
                "published_at": NOW - timedelta(days=80),
            },
            {
                "_id": product_ids[4],
                "name": "Ceramic Planter Set",
                "product_sku": "PL-CER-3",
                "slug": "ceramic-planter-set",
                "short_description": "Set of 3 minimalist planters",
                "description": "Hand-glazed ceramic with drainage holes.",
                "price": Decimal("45.00"),
                "unit_cost": Decimal("15.00"),
                "category_id": home_id,
                "brand_id": brand_ids[2],
                "stock_quantity": 60,
                "low_stock_threshold": 10,
                "weight_kg": 2.5,
                "tags": ["garden", "decor"],
                "status": "active",
                "is_featured": True,
                "is_taxable": True,
                "created_at": NOW - timedelta(days=15),
                "updated_at": NOW,
                "published_at": NOW - timedelta(days=10),
            },
            {
                "_id": product_ids[5],
                "name": "Draft Product — Not Published",
                "product_sku": "DRAFT-001",
                "slug": "draft-product",
                "short_description": "Internal draft listing",
                "description": "This product is in draft status for admin testing.",
                "price": Decimal("9.99"),
                "unit_cost": Decimal("3.00"),
                "category_id": electronics_id,
                "stock_quantity": 0,
                "tags": ["draft"],
                "status": "draft",
                "is_featured": False,
                "is_taxable": True,
                "created_at": NOW,
                "updated_at": NOW,
            },
        ]
    )

    customer_ids = [_oid(), _oid(), _oid()]
    await db.customers.insert_many(
        [
            {
                "_id": customer_ids[0],
                "email": "alice@example.com",
                "first_name": "Alice",
                "last_name": "Johnson",
                "phone": "+1-555-0101",
                "loyalty_tier": "gold",
                "marketing_opt_in": True,
                "is_active": True,
                "total_orders": 12,
                "lifetime_value": Decimal("1842.50"),
                "default_shipping": {
                    "line1": "123 Oak Street",
                    "city": "Portland",
                    "state": "OR",
                    "postal_code": "97201",
                    "country": "US",
                },
                "created_at": NOW - timedelta(days=400),
            },
            {
                "_id": customer_ids[1],
                "email": "bob@example.com",
                "first_name": "Bob",
                "last_name": "Smith",
                "phone": "+1-555-0102",
                "loyalty_tier": "silver",
                "marketing_opt_in": False,
                "is_active": True,
                "total_orders": 4,
                "lifetime_value": Decimal("320.00"),
                "created_at": NOW - timedelta(days=120),
            },
            {
                "_id": customer_ids[2],
                "email": "carol@example.com",
                "first_name": "Carol",
                "last_name": "Nguyen",
                "loyalty_tier": "bronze",
                "marketing_opt_in": True,
                "is_active": False,
                "total_orders": 1,
                "lifetime_value": Decimal("29.99"),
                "created_at": NOW - timedelta(days=30),
            },
        ]
    )

    await db.orders.insert_many(
        [
            {
                "_id": _oid(),
                "order_number": "ORD-2026-0001",
                "customer_id": customer_ids[0],
                "status": "delivered",
                "payment_status": "captured",
                "currency": "USD",
                "line_items": [
                    {
                        "product_id": str(product_ids[0]),
                        "sku": "WH-1000",
                        "name": "Wireless Noise-Cancelling Headphones",
                        "quantity": 1,
                        "unit_price": Decimal("249.99"),
                        "discount": Decimal("0.00"),
                    }
                ],
                "subtotal": Decimal("249.99"),
                "tax_amount": Decimal("20.00"),
                "shipping_cost": Decimal("0.00"),
                "discount_amount": Decimal("0.00"),
                "total": Decimal("269.99"),
                "placed_at": NOW - timedelta(days=5),
                "shipped_at": NOW - timedelta(days=3),
            },
            {
                "_id": _oid(),
                "order_number": "ORD-2026-0002",
                "customer_id": customer_ids[1],
                "status": "shipped",
                "payment_status": "captured",
                "currency": "USD",
                "line_items": [
                    {
                        "product_id": str(product_ids[2]),
                        "sku": "TS-ORG-01",
                        "name": "Organic Cotton T-Shirt",
                        "quantity": 2,
                        "unit_price": Decimal("29.99"),
                        "discount": Decimal("0.00"),
                    }
                ],
                "subtotal": Decimal("59.98"),
                "tax_amount": Decimal("4.80"),
                "shipping_cost": Decimal("5.99"),
                "total": Decimal("70.77"),
                "coupon_code": "WELCOME10",
                "placed_at": NOW - timedelta(days=2),
            },
            {
                "_id": _oid(),
                "order_number": "ORD-2026-0003",
                "customer_id": customer_ids[0],
                "status": "pending",
                "payment_status": "unpaid",
                "currency": "EUR",
                "line_items": [],
                "subtotal": Decimal("45.00"),
                "tax_amount": Decimal("3.60"),
                "shipping_cost": Decimal("8.00"),
                "total": Decimal("56.60"),
                "placed_at": NOW - timedelta(hours=6),
            },
        ]
    )

    await db.reviews.insert_many(
        [
            {
                "_id": _oid(),
                "product_id": product_ids[0],
                "customer_id": customer_ids[0],
                "rating": 5,
                "title": "Best headphones I've owned",
                "body": "Incredible sound quality and the battery lasts forever.",
                "is_verified_purchase": True,
                "is_approved": True,
                "helpful_count": 14,
                "created_at": NOW - timedelta(days=3),
            },
            {
                "_id": _oid(),
                "product_id": product_ids[2],
                "customer_id": customer_ids[1],
                "rating": 4,
                "title": "Great quality tee",
                "body": "Soft fabric, fits true to size.",
                "is_verified_purchase": True,
                "is_approved": False,
                "helpful_count": 2,
                "created_at": NOW - timedelta(days=1),
            },
        ]
    )

    await db.coupons.insert_many(
        [
            {
                "_id": _oid(),
                "code": "WELCOME10",
                "description": "10% off first order",
                "discount_type": "percentage",
                "discount_value": Decimal("10"),
                "min_order_value": Decimal("25.00"),
                "max_uses": 1000,
                "used_count": 142,
                "is_active": True,
                "valid_from": NOW - timedelta(days=90),
                "valid_until": NOW + timedelta(days=90),
            },
            {
                "_id": _oid(),
                "code": "FLAT20",
                "description": "$20 off orders over $100",
                "discount_type": "fixed",
                "discount_value": Decimal("20.00"),
                "min_order_value": Decimal("100.00"),
                "max_uses": 500,
                "used_count": 88,
                "is_active": True,
                "valid_from": NOW - timedelta(days=30),
                "valid_until": NOW + timedelta(days=60),
            },
        ]
    )

    print(f"Seeded database '{db_name}' with sample ecommerce data.")
    client.close()


def main() -> None:
    """CLI entry point for seeding."""
    asyncio.run(seed_database())


if __name__ == "__main__":
    main()
