# FastAPI Mongo Admin

A Django-inspired, server-rendered admin framework for FastAPI and MongoDB.

**v2.0.0** replaces the legacy React SPA with a Jinja2 + HTMX admin interface, a full `ModelAdmin` configuration API, pluggable authentication, and support for both async (Motor) and sync (PyMongo) MongoDB backends.

## Key Features

- **Django-like registry** — `site.register(Model, AdminClass)`
- **Server-rendered admin UI** — changelist, add/change forms, delete confirmation, bulk actions
- **List filters** — choice, boolean, date, related, and custom `ListFilter` classes
- **Pydantic-driven forms** — validation and schema inference from your models
- **Field mapping** — map model fields to different MongoDB keys
- **Pluggable auth** — wire any FastAPI `Depends` authentication/authorization
- **Sync + async MongoDB** — `mode="async"` (Motor) or `mode="sync"` (PyMongo)
- **Customization** — template overrides, `ModelAdmin` hooks, custom admin views
- **JSON API** — `/admin/api/{collection}/` for programmatic access
- **Light/dark mode** — theme toggle with cookie + localStorage persistence
- **i18n** — built-in UI translations for `en`, `fr`, `pt`, `ru`, `it`, `ch`, `es`, `de`, `ar` (English default)
- **Date/time display** — human-readable changelist and readonly formatting (default: `8 Apr 2026, 7:32pm`)
- **Save notifications** — success banner on the changelist after add/change, using the saved item's label
- **Nested models** — nested Pydantic models edited as JSON and validated on save

## Breaking Changes (v0.x → v2)

- React UI and `/admin-ui` mount removed; admin lives at `/admin`
- `MongoAdmin` alias removed; use `AdminSite` or `site`
- Built-in demo token auth removed; provide `auth_dependency`
- Legacy `/admin/collections/.../documents` routes removed

## Installation

```bash
# Using uv (recommended)
uv add fastapi-mongo-admin

# Or pip
pip install fastapi-mongo-admin
```

## Quick Start

### 1. Define models and admin classes

```python
from pydantic import BaseModel
from fastapi_mongo_admin import ModelAdmin, site, display, action
from fastapi_mongo_admin.admin.filters import ChoiceListFilter, DateFieldListFilter


class Product(BaseModel):
    name: str
    price: float
    category: str
    active: bool = True


class ProductAdmin(ModelAdmin):
    model = Product
    collection_name = "products"
    list_display = ["name", "category", "price", "active"]
    list_filter = ["category", "active"]
    search_fields = ["name", "category"]
    list_per_page = 25
    choices = {
        "category": [("books", "Books"), ("electronics", "Electronics")],
    }

    @display(description="Name")
    def name_upper(self, obj: dict) -> str:
        return str(obj.get("name", "")).upper()

    @action("Deactivate selected")
    async def deactivate_selected(self, request, queryset: list[dict]) -> None:
        pass


site.register(Product, ProductAdmin)
```

### 2. Mount in FastAPI (async)

```python
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi_mongo_admin import mount_admin_app

app = FastAPI()
client = AsyncIOMotorClient("mongodb://localhost:27017")
database = client["my_db"]


async def get_database():
    return database


mount_admin_app(app, get_database, admin_site=site, mode="async")
```

### 3. Sync MongoDB

```python
from pymongo import MongoClient
from fastapi_mongo_admin import mount_admin_app

client = MongoClient("mongodb://localhost:27017")
db = client["my_db"]

mount_admin_app(app, lambda: db, admin_site=site, mode="sync")
```

Visit `http://localhost:8000/admin/` for the admin index.

## Authentication

Pass any FastAPI-compatible dependency:

```python
from fastapi import Depends, HTTPException


async def get_admin_user():
  # Your JWT/session validation here
  return {"id": "user-1", "is_staff": True}


mount_admin_app(
    app,
    get_database,
    admin_site=site,
    auth_dependency=get_admin_user,
)
```

Override per-model permissions on `ModelAdmin`:

```python
class ProductAdmin(ModelAdmin):
    def has_add_permission(self, request, user=None) -> bool:
        return bool(user and user.get("is_staff"))
```

## ModelAdmin Options

| Option | Description |
|--------|-------------|
| `model` | Pydantic model for validation |
| `collection_name` | MongoDB collection (required) |
| `list_display` | Changelist columns (fields or `@display` methods) |
| `list_display_links` | Clickable columns |
| `list_filter` | Field names or `ListFilter` subclasses |
| `search_fields` | Text search fields |
| `list_per_page` | Pagination size (default 25) |
| `ordering` | Default sort, e.g. `["-created_at"]` |
| `date_hierarchy` | Date drill-down field |
| `list_select_related` | `{"field": "collection"}` for related lookups |
| `fieldsets` | Grouped change form layout |
| `readonly_fields` | Non-editable fields |
| `field_mapping` | Model field → DB field mapping |
| `actions` | Bulk action method names |
| `choices` | Choice lookups for filters/forms |
| `date_format` | Display format for `date` fields (default: `8 Apr 2026`) |
| `datetime_format` | Display format for `datetime` fields (default: `8 Apr 2026, 7:32pm`) |

## Date and Time Display

`date` and `datetime` fields are formatted automatically on changelists and readonly form fields. Form inputs still use ISO values for HTML date/datetime pickers.

Default formats:

- **Date:** `8 Apr 2026`
- **Datetime:** `8 Apr 2026, 7:32pm`

Customize per model:

```python
class OrderAdmin(ModelAdmin):
    date_format = "j M Y"                  # Django-style tokens
    datetime_format = "%d/%m/%Y %H:%M"     # or standard strftime
```

Override completely:

```python
def format_datetime_value(self, value) -> str:
    return my_formatter(value)
```

## Save Notifications

After a successful add or change, the admin redirects to the changelist and shows a one-time success banner:

- **Add:** `"Widget Pro" was added successfully.`
- **Change:** `"Widget Pro" was saved successfully.`

The label comes from `ModelAdmin.object_repr()` (first `list_display_links` column, then `list_display`, then common fields like `name`).

## Nested Pydantic Models

Nested models (e.g. `CustomerAddress` inside `Customer`) render as JSON editors. Empty `{}` for optional nested fields is treated as `None`. Example:

```json
{
  "line1": "1 Main St",
  "city": "Boston",
  "postal_code": "02101",
  "country": "US"
}
```

## Theme and Language

The admin header includes a **theme toggle** (light/dark) and a **language selector**.

- Theme is stored in the `admin_theme` cookie and `localStorage`
- Language is stored in the `admin_lang` cookie (default: `en`)
- Arabic (`ar`) enables RTL layout automatically
- You can also set preferences via query string: `?lang=fr&theme=dark` (sets cookies and redirects)

## Template Customization

```python
from pathlib import Path

site = AdminSite(template_dirs=[Path("myapp/templates")])

class ProductAdmin(ModelAdmin):
    change_list_template = "myapp/admin/product_change_list.html"
```

Register custom views:

```python
async def reports(request):
    return {"report": "data"}

site.register_view("Reports", "/reports/", reports)
```

## URL Scheme

| URL | View |
|-----|------|
| `GET /admin/` | Admin index |
| `GET /admin/{collection}/` | Changelist |
| `GET /admin/{collection}/add/` | Add form |
| `GET/POST /admin/{collection}/{id}/change/` | Change form |
| `POST /admin/{collection}/{id}/delete/` | Delete |
| `POST /admin/{collection}/action/` | Bulk actions |
| `GET /admin/api/{collection}/` | JSON list API |

## Ecommerce demo

A full test store with seven collections, rich field types, seed data, and customization examples lives in [`example/`](example/README.md):

```bash
docker compose -f example/docker-compose.yml up -d
uv run python -m example.ecommerce.seed
uv run python -m example.ecommerce.main
# → http://localhost:8000/demo-login?token=admin-token
```

## Documentation

Full documentation is built with Sphinx and hosted on Read the Docs:

- **Online:** https://fastapi-mongo-admin.readthedocs.io/
- **Build locally:** `make docs` (output in `docs/_build/html/`)

## Development

```bash
make install   # uv sync --group dev
make test      # pytest
make lint      # ruff
make secure    # bandit + pysentry-rs
make docs      # build Sphinx HTML docs
make help      # list all targets
```

## License

MIT
