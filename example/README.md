# Ecommerce Demo — FastAPI Mongo Admin

A full-featured **test ecommerce store** for exercising [fastapi-mongo-admin](https://github.com/tushortz/fastapi-mongo-admin) v2. It includes rich Pydantic models, seven registered collections, sample seed data, demo authentication, and admin customizations that mirror real-world Django-admin patterns.

Use this project to test changelists, filters, fieldsets, bulk actions, `list_select_related`, field mapping, i18n, light/dark mode, permissions, and custom admin views.

---

## Table of contents

1. [Prerequisites](#prerequisites)
2. [Quick start](#quick-start)
3. [Project structure](#project-structure)
4. [Data models](#data-models)
5. [Admin features demonstrated](#admin-features-demonstrated)
6. [Authentication](#authentication)
7. [Seeding data](#seeding-data)
8. [Running the application](#running-the-application)
9. [Customization guide](#customization-guide)
10. [Environment variables](#environment-variables)
11. [Troubleshooting](#troubleshooting)

---

## Prerequisites

| Requirement | Version |
|-------------|---------|
| Python | 3.10+ |
| MongoDB | 5.0+ (local or Docker) |
| [uv](https://docs.astral.sh/uv/) | latest (recommended) |

Install the parent package from the repository root:

```bash
cd /path/to/fastapi_mongo_admin
uv sync --group dev
```

---

## Quick start

```bash
# 1. Start MongoDB
docker compose -f example/docker-compose.yml up -d

# 2. Seed sample data
uv run python -m example.ecommerce.seed

# 3. Run the demo app
uv run python -m example.ecommerce.main
```

Open in your browser:

| URL | Description |
|-----|-------------|
| http://localhost:8000/ | Demo landing page |
| http://localhost:8000/demo-login?token=admin-token | Login as admin (sets cookie) |
| http://localhost:8000/admin/ | Admin index |
| http://localhost:8000/admin/products/ | Product changelist |
| http://localhost:8000/admin/dashboard/ | Custom admin view |
| http://localhost:8000/health | Health check |

---

## Project structure

```
example/
├── README.md                 # This file
├── docker-compose.yml        # MongoDB for local development
├── templates/                # Optional admin template overrides
│   └── admin/
└── ecommerce/
    ├── main.py               # FastAPI app entry point
    ├── models.py             # Pydantic domain models (many fields)
    ├── admin.py              # ModelAdmin classes + site config
    ├── auth.py               # Demo Bearer/cookie authentication
    └── seed.py               # MongoDB sample data script
```

---

## Data models

Seven collections are registered with the admin. Each model is designed to stress different field types and admin widgets.

### Category (`categories`)

| Field | Type | Notes |
|-------|------|-------|
| name, slug, description | str | Searchable text |
| parent_id | str \| null | Hierarchy reference |
| is_active | bool | Boolean filter |
| sort_order | int | Ordering |
| image_url | str \| null | Optional URL |
| created_at | datetime | Read-only in forms |

### Brand (`brands`)

| Field | Type |
|-------|------|
| name, slug, country, website, description | str |
| is_active | bool |
| founded_year | int \| null |

### Product (`products`) — **richest model**

| Group | Fields |
|-------|--------|
| Basic | name, sku, slug, short_description, description |
| Pricing | price, compare_at_price, cost_price, is_taxable |
| Inventory | stock_quantity, low_stock_threshold, weight_kg, dimensions (nested) |
| Catalog | category_id, brand_id, tags (list), status (enum), is_featured |
| SEO | meta_title, meta_description |
| Advanced | attributes (dict), created_at, updated_at, published_at |

**Field mapping demo:** model field `sku` maps to MongoDB `product_sku`; `cost_price` maps to `unit_cost`. The seed script writes DB field names so you can verify round-trip translation in the admin.

### Customer (`customers`)

| Field | Type |
|-------|------|
| email | EmailStr |
| first_name, last_name, phone | str |
| date_of_birth | date \| null |
| loyalty_tier | enum (bronze/silver/gold/platinum) |
| marketing_opt_in, is_active | bool |
| default_shipping | nested address object |
| total_orders | int |
| lifetime_value | Decimal |
| notes | str |

### Order (`orders`)

| Field | Type |
|-------|------|
| order_number | str (read-only after create) |
| customer_id | reference |
| status, payment_status | enums |
| currency | choice filter |
| line_items | list of nested objects |
| subtotal, tax_amount, shipping_cost, discount_amount, total | Decimal |
| shipping_address, billing_address | nested objects |
| coupon_code, notes | str |
| placed_at, shipped_at | datetime (date hierarchy on placed_at) |

### Review (`reviews`)

| Field | Type |
|-------|------|
| product_id, customer_id | references |
| rating | int (1–5) |
| title, body | str |
| is_verified_purchase, is_approved | bool |
| helpful_count | int |

### Coupon (`coupons`)

| Field | Type |
|-------|------|
| code, description | str |
| discount_type | enum (percentage/fixed) |
| discount_value, min_order_value | Decimal |
| max_uses, used_count | int |
| is_active | bool |
| valid_from, valid_until | datetime |

---

## Admin features demonstrated

| Feature | Where to see it |
|---------|-----------------|
| **Fieldsets** | Product, Customer, Order change forms |
| **list_display + @display** | Product price column, Customer full name |
| **list_filter** | Product status, Customer loyalty tier, Order payment status |
| **search_fields** | All major models |
| **date_hierarchy** | Product (`published_at`), Order (`placed_at`) |
| **list_select_related** | Product → category/brand; Order → customer; Review → product/customer |
| **field_mapping** | Product `sku` ↔ `product_sku` |
| **Bulk actions** | Publish / archive / feature products; approve reviews |
| **save_model hook** | Auto-sets `updated_at` on product save |
| **has_delete_permission** | Only admin/manager can delete products |
| **Custom admin view** | `/admin/dashboard/` |
| **Template override dir** | `example/templates/` registered on `EcommerceAdminSite` |
| **i18n** | Header language selector (9 languages) |
| **Light/dark mode** | Header theme toggle |

---

## Authentication

The demo uses **token-based auth** for development. Do not use this in production.

### Demo tokens

| Token | Role | Can delete products? |
|-------|------|----------------------|
| `admin-token` | admin | Yes |
| `manager-token` | manager | Yes |
| `viewer-token` | viewer | No |

### Browser login

Visit `/demo-login?token=admin-token` — sets an `admin_token` cookie and redirects to `/admin/`.

### API / curl

```bash
curl -H "Authorization: Bearer admin-token" http://localhost:8000/admin/api/products/
```

### Replacing with real auth

Edit `example/ecommerce/auth.py` and wire your JWT/session validation in `get_current_user()`. Pass the dependency to `mount_admin_app`:

```python
mount_admin_app(app, get_database, admin_site=ecommerce_site, auth_dependency=your_dependency)
```

Implement per-model rules on `ModelAdmin`:

```python
def has_change_permission(self, request, user=None, obj=None) -> bool:
    return user.get("role") in ("admin", "manager")
```

---

## Seeding data

The seed script clears and repopulates all seven collections with realistic sample documents.

```bash
# Default: mongodb://localhost:27017, database ecommerce_demo
uv run python -m example.ecommerce.seed
```

Custom connection:

```bash
MONGODB_URL=mongodb://user:pass@host:27017 uv run python -m example.ecommerce.seed
MONGODB_DB=my_shop uv run python -m example.ecommerce.seed
```

Seeded data highlights:

- 3 categories, 3 brands, 6 products (including draft and low-stock items)
- 3 customers across loyalty tiers
- 3 orders in different statuses and currencies
- 2 reviews (one pending approval)
- 2 active coupons

---

## Running the application

### Development server

```bash
uv run python -m example.ecommerce.main
```

With auto-reload (default):

```bash
RELOAD=true uv run python -m example.ecommerce.main
```

### Uvicorn directly

```bash
uv run uvicorn example.ecommerce.main:app --reload --host 0.0.0.0 --port 8000
```

Ensure you run commands from the **repository root** so the `example` package resolves.

---

## Customization guide

### 1. Add a new model

**Step 1 — Define the Pydantic model** in `ecommerce/models.py`:

```python
class Warehouse(BaseModel):
    name: str
    code: str
    is_active: bool = True
```

**Step 2 — Create a ModelAdmin** in `ecommerce/admin.py`:

```python
class WarehouseAdmin(ModelAdmin):
    model = Warehouse
    collection_name = "warehouses"
    list_display = ["name", "code", "is_active"]
    search_fields = ["name", "code"]
```

**Step 3 — Register it** inside `register_admins()`:

```python
site.register(Warehouse, WarehouseAdmin)
```

Restart the app. The new model appears on the admin index.

---

### 2. Customize changelist columns

Use `list_display` with field names or `@display` methods:

```python
@display(description="Margin", ordering="price")
def margin(self, obj: dict) -> str:
    price = float(obj.get("price", 0))
    cost = float(obj.get("cost_price", 0))
    return f"{((price - cost) / price * 100):.1f}%" if price else "—"
```

Add `"margin"` to `list_display`.

---

### 3. Add bulk actions

```python
@action("Deactivate selected")
async def deactivate_selected(self, request, queryset: list[dict]) -> None:
    for doc in queryset:
        # await repository.update(...)
        pass
```

List the method name in `actions = ["deactivate_selected"]`.

---

### 4. Field mapping (legacy MongoDB keys)

When your database uses different field names than your Pydantic model:

```python
class ProductAdmin(ModelAdmin):
    field_mapping = {
        "sku": "product_sku",
        "cost_price": "unit_cost",
    }
```

The admin translates on read and write automatically.

---

### 5. Override admin templates

Place templates in `example/templates/admin/` (already registered via `EcommerceAdminSite(template_dirs=[...])`).

Jinja2 searches your directory **before** the bundled package templates.

Per-model override:

```python
class ProductAdmin(ModelAdmin):
    change_list_template = "admin/product_change_list.html"
```

Copy the bundled `change_list.html` from `fastapi_mongo_admin/templates/admin/` as a starting point.

---

### 6. Custom admin pages

```python
async def my_report(request: Request) -> HTMLResponse:
    return HTMLResponse("<h1>Report</h1>")

site.register_view("report", "/reports/", my_report)
```

Available at `/admin/reports/`.

---

### 7. Site branding

Edit `EcommerceAdminSite` in `admin.py`:

```python
class EcommerceAdminSite(AdminSite):
    site_header = "My Store Admin"
    site_title = "Store Manager"
    index_title = "Welcome"
```

---

### 8. Theme and language

Built into the admin header — no extra configuration required.

- Toggle light/dark with the sun/moon button
- Select language from the dropdown (en, fr, pt, ru, it, ch, es, de, ar)
- Preferences persist via cookies

Force via URL: `/admin/products/?lang=fr&theme=dark`

---

### 9. Sync MongoDB mode

If you use PyMongo instead of Motor:

```python
from pymongo import MongoClient
client = MongoClient(MONGODB_URL)

mount_admin_app(app, lambda: client[DATABASE_NAME], admin_site=ecommerce_site, mode="sync")
```

---

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MONGODB_URL` | `mongodb://localhost:27017` | MongoDB connection string |
| `MONGODB_DB` | `ecommerce_demo` | Database name |
| `HOST` | `0.0.0.0` | Uvicorn bind host |
| `PORT` | `8000` | Uvicorn port |
| `RELOAD` | `true` | Auto-reload in dev |

---

## Troubleshooting

### `ModuleNotFoundError: No module named 'example'`

Run commands from the **repository root**, not from inside `example/`:

```bash
cd /path/to/fastapi_mongo_admin
uv run python -m example.ecommerce.main
```

### Admin returns 401

Visit `/demo-login?token=admin-token` first, or send `Authorization: Bearer admin-token`.

### Empty changelists

Run the seed script:

```bash
uv run python -m example.ecommerce.seed
```

### MongoDB connection refused

Start MongoDB:

```bash
docker compose -f example/docker-compose.yml up -d
```

### Product SKU not showing after manual DB insert

Remember `field_mapping`: MongoDB stores `product_sku`, not `sku`. Either use mapped keys in MongoDB or remove `field_mapping` from `ProductAdmin`.

---

## Next steps

- Replace demo auth with your production identity provider
- Add repository logic inside `save_model` / bulk action hooks
- Create custom templates for high-traffic models
- Extend seed data for load-testing pagination and filters
- Point the JSON API (`/admin/api/{collection}/`) at your frontend tooling

For full library documentation, see the [main README](../README.md).
