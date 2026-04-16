# FastAPI Mongo Admin

A professional, Django-inspired admin framework for FastAPI and MongoDB.

FastAPI Mongo Admin v0.2.0+ transforms the library into a strictly registry-based system, providing model-specific API endpoints, automated Swagger documentation, and explicit field mapping between Pydantic models and MongoDB collections.

## Key Features

- **Django-like Registry**: Register models using `site.register(Model, AdminClass)`.
- **Automated Swagger Documentation**: Each registered model gets its own grouped API endpoints with proper request/response schemas.
- **Explicit Field Mapping**: Map model fields to different database keys (e.g., `model.name` -> `db.product_name`).
- **Security by Default**: All discovery and auto-fetching have been removed. Only registered models are exposed.
- **Rich Admin UI**: Built-in React interface for data management, analytics, and bulk operations.
- **High Performance**: Optimized aggregation pipelines for list, search, and analytics.

---

## Installation

```bash
pip install fastapi-mongo-admin
```

---

## Quick Start

### 1. Define your Models and Admin

```python
from pydantic import BaseModel
from fastapi_mongo_admin import ModelAdmin, site

class Product(BaseModel):
    name: str
    price: float
    category: str

class ProductAdmin(ModelAdmin):
    model = Product
    collection_name = "products" # Explicitly mandate collection name
    list_display = ["name", "category", "price"]
    search_fields = ["name"]
    # Map model field 'name' to 'p_name' in MongoDB
    field_mapping = {"name": "p_name"}

# Register your model
site.register(Product, ProductAdmin)
```

### 2. Mount in FastAPI

```python
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi_mongo_admin import mount_admin_app

app = FastAPI()
client = AsyncIOMotorClient("mongodb://localhost:27017")
database = client["my_db"]

async def get_database():
    return database

# Mount the admin - Done!
mount_admin_app(app, get_database, admin_site=site)
```

---

## Detailed Configuration

### ModelAdmin Options

| Option | Description |
|--------|-------------|
| `model` | The Pydantic model for validation and Swagger documentation. |
| `collection_name` | **(Required)** The name of the MongoDB collection. |
| `list_display` | Fields to show in the admin list view table. |
| `search_fields` | Fields to include in text search queries. |
| `list_filter` | Fields to provide as filter options. |
| `list_per_page` | Number of items to display per page (default: 50). |
| `field_mapping` | Dictionary mapping model field names to database field names. |

### API Documentation (Swagger)

The admin generator automatically creates typed routes for each collection:
- `GET /admin/products/` - List products
- `POST /admin/products/` - Create products (validated by Pydantic)
- `GET /admin/products/{id}` - Detail view
- `PUT /admin/products/{id}` - Update product
- `DELETE /admin/products/{id}` - Delete product

---

## Advanced Usage

### Field Mapping

If your database uses different field names than your Pydantic models, use `field_mapping`:

```python
class LegacyAdmin(ModelAdmin):
    model = MyModel
    collection_name = "legacy_data"
    field_mapping = {
        "user_id": "UID",
        "created_at": "ts_created"
    }
```

The service layer will automatically translate queries going into MongoDB and results coming back out, ensuring your FastAPI application only ever sees the model fields.

### Authentication

You can secure the admin by passing an `auth_dependency`:

```python
from fastapi import Depends
from my_auth import get_admin_user

mount_admin_app(
    app, 
    get_database, 
    admin_site=site,
    require_auth=True,
    auth_dependency=get_admin_user
)
```

---

## License

MIT
