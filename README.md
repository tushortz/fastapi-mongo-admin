# FastAPI Mongo Admin

A powerful FastAPI package that provides generic CRUD operations and a built-in admin UI for MongoDB collections. Perfect for rapid prototyping, database administration, and building admin interfaces for your MongoDB databases.

## Description

FastAPI Mongo Admin is a comprehensive solution for managing MongoDB databases through a beautiful web interface. It automatically generates REST APIs and provides a full-featured admin panel with the following features:

## Screenshots

### List View
![List View](images/list.png)

![Detail View](images/detail.png)

- **Full CRUD Operations**: Create, read, update, and delete documents through REST endpoints or the web UI
- **Intelligent Schema Inference**: Automatically detects collection schemas from existing documents, Pydantic models, or OpenAPI schemas
- **Modern Admin UI**: React-based interface with dark mode, responsive design, and multi-language support (8 languages)
- **Advanced Data Management**: Search, filter, sort, paginate, and bulk operations on documents
- **Analytics Dashboard**: Generate charts and visualizations from your data with customizable aggregations
- **Data Import/Export**: Export collections to JSON, CSV, HTML, XML, YAML, TOML formats or import data from files
- **Type Safety**: Full type hints, async/await support, and Pydantic v2 integration
- **Zero Configuration**: Works out of the box with minimal setup - just connect to your MongoDB database

### Analytics Dashboard
![Analytics Dashboard](images/analytics.png)


### Core Features

- **Generic CRUD Operations** - Create, Read, Update, Delete operations for any MongoDB collection through REST endpoints or the web UI
- **Intelligent Schema Inference** - Automatically analyze and infer collection schemas from existing documents, Pydantic models, or OpenAPI schemas
- **Pydantic Model Support** - Infer schemas from Pydantic models when collections are empty
  - Flexible model input formats: list, dict, or auto-discovery
  - Smart model matching with plural/singular conversion
  - Explicit control with dict format or automatic with list format
- **OpenAPI Schema Discovery** - Automatically discover and use Pydantic models from your FastAPI app's OpenAPI/Swagger documentation
- **Convenience Setup** - `mount_admin_app()` function to set up router and UI in one call

### Admin UI Features

- **Built-in Admin UI** - Beautiful React-based web interface for database management with Tailwind CSS and reactive state management
- **Dark Mode Support** - Toggle between light and dark themes with persistent preference and CSS file switching (no flicker on page reload)
- **Internationalization (i18n)** - Multi-language support with 8 languages (English, French, Russian, Spanish, Portuguese, Chinese, Italian, German)
  - Automatic browser language detection on first visit
  - Language preference persistence in localStorage
  - Seamless language switching with instant UI updates
  - Comprehensive translations for all UI components
- **Advanced Filtering & Search** - Server-side filtering with case-insensitive text search, enum matching, and date filtering
- **Sortable Tables** - Click column headers to sort data ascending/descending
- **Paginated Forms** - Forms automatically paginated with 5 fields per page for better UX
- **Analytics Dashboard** - Generate charts and visualizations from your data with customizable aggregations (count, sum, average, min, max)
- **Data Import/Export** - Export collections to JSON, CSV, HTML, XML, YAML, TOML formats or import data from files
- **Bulk Operations** - Select and delete multiple documents at once
- **Field Selection** - Choose which fields to display in the document table
- **Responsive Design** - Works seamlessly on desktop and mobile devices

### Technical Features

- **Automatic ObjectId Serialization** - Seamless JSON serialization of MongoDB ObjectIds
- **Type Hints & Async Support** - Full type hints and async/await support throughout
- **Error Handling** - Comprehensive error handling and validation
- **FastAPI Integration** - Seamlessly integrates with FastAPI applications
- **Zero Configuration** - Works out of the box with minimal setup - just connect to your MongoDB database

## Setup Instructions

### Prerequisites

Before installing FastAPI Mongo Admin, ensure you have:

- **Python 3.9+** (Python 3.10+ recommended for full type support)
- **MongoDB** installed and running (local or remote)
- **pip** or **Poetry** for package management

### Step 1: Install FastAPI Mongo Admin

#### Option A: Using pip

```bash
# Basic installation
pip install fastapi-mongo-admin

# With export functionality (for YAML, TOML, and other export formats)
pip install fastapi-mongo-admin[export]

# For development (includes dev dependencies)
pip install fastapi-mongo-admin[dev]
```

#### Option B: Using Poetry

```bash
# Basic installation
poetry add fastapi-mongo-admin

# With export functionality
poetry add fastapi-mongo-admin[export]

# For development
poetry add fastapi-mongo-admin[dev] --group dev
```

### Step 2: Create Your FastAPI Application

Create a new file `main.py`:

```python
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from fastapi_mongo_admin import mount_admin_app

# Initialize FastAPI app
app = FastAPI(title="My MongoDB Admin App")

# Set up MongoDB connection
client = AsyncIOMotorClient("mongodb://localhost:27017")
database = client["my_database"]

# Create database dependency function
async def get_database() -> AsyncIOMotorDatabase:
    """Get database instance."""
    return database

# Mount admin app (router + UI) in one call
mount_admin_app(
    app,
    get_database,
    router_prefix="/admin",
    ui_mount_path="/admin-ui"
)
```

### Step 3: Run the Application

```bash
# Install uvicorn if not already installed
pip install uvicorn

# Run the application
uvicorn main:app --reload
```

The application will start on `http://localhost:8000` by default.

### Step 4: Access the Admin Interface

Once the application is running:

1. **API Documentation (Swagger UI)**: http://localhost:8000/docs
2. **Admin UI**: http://localhost:8000/admin-ui/admin.html

### Step 5: Verify Setup

1. Open the Admin UI in your browser
2. You should see a sidebar with your MongoDB collections
3. Click on a collection to browse documents
4. Try creating a new document using the "Create Document" button

### Configuration Options

#### Environment Variables

For production, use environment variables:

```python
import os
from motor.motor_asyncio import AsyncIOMotorClient

# Get connection string from environment
mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
db_name = os.getenv("MONGODB_DB_NAME", "my_database")

client = AsyncIOMotorClient(mongodb_url)
database = client[db_name]
```

Create a `.env` file:
```env
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=my_database
```

#### MongoDB Connection with Authentication

```python
from motor.motor_asyncio import AsyncIOMotorClient

client = AsyncIOMotorClient(
    "mongodb://username:password@localhost:27017",
    authSource="admin"
)
database = client["my_database"]
```

### Requirements

- **Python**: 3.9+ (3.10+ recommended)
- **FastAPI**: 0.68.0+
- **Motor**: 2.5.0+ (async MongoDB driver)
- **PyMongo**: 4.0.0+
- **Pydantic**: 2.0.0+ (v2 only, <3.0.0)

**Note:** The codebase uses Python 3.10+ type union syntax (`|`). For full Python 3.9 compatibility, you may need to use `typing.Union` or `typing.Optional` instead.

## Quick Start

After completing the setup instructions above, you're ready to use FastAPI Mongo Admin! Here's a quick reference:

### Minimal Example

```python
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from fastapi_mongo_admin import mount_admin_app

app = FastAPI(title="My MongoDB Admin App")
client = AsyncIOMotorClient("mongodb://localhost:27017")
database = client["my_database"]

async def get_database() -> AsyncIOMotorDatabase:
    return database

mount_admin_app(app, get_database, router_prefix="/admin", ui_mount_path="/admin-ui")
```

### Running the Application

```bash
uvicorn main:app --reload
```

Then access:
- **API Documentation**: http://localhost:8000/docs
- **Admin UI**: http://localhost:8000/admin-ui/admin.html

## Detailed Usage Guide

### 1. Setting Up MongoDB Connection

#### Basic Connection

```python
from motor.motor_asyncio import AsyncIOMotorClient

client = AsyncIOMotorClient("mongodb://localhost:27017")
database = client["my_database"]
```

#### Connection with Authentication

```python
from motor.motor_asyncio import AsyncIOMotorClient

client = AsyncIOMotorClient(
    "mongodb://username:password@localhost:27017",
    authSource="admin"
)
database = client["my_database"]
```

#### Connection with Environment Variables

```python
import os
from motor.motor_asyncio import AsyncIOMotorClient

mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
db_name = os.getenv("MONGODB_DB_NAME", "my_database")

client = AsyncIOMotorClient(mongodb_url)
database = client[db_name]
```

### 2. Creating the Admin Router

The `create_router` function accepts a database dependency function and optional configuration:

```python
from fastapi_mongo_admin import create_router

# Basic usage
admin_router = create_router(get_database)

# With custom prefix
admin_router = create_router(
    get_database,
    prefix="/api/v1/admin"
)

# With custom prefix and tags
admin_router = create_router(
    get_database,
    prefix="/admin",
    tags=["admin", "database", "management"]
)

# With Pydantic models for schema inference
from pydantic import BaseModel

class Product(BaseModel):
    name: str
    price: float
    description: str | None = None

# Dict format: exact matching (case-insensitive fallback)
pydantic_models = {"products": Product}  # Matches 'products' collection
# OR (exact key match, no auto-conversion)
pydantic_models = {"Product": Product}  # Matches 'Product' collection (not 'products')

# List format: auto-detects and converts
pydantic_models = [Product]  # Auto-converts to 'products' from model name

admin_router = create_router(
    get_database,
    pydantic_models=pydantic_models
)

# With automatic OpenAPI schema discovery
admin_router = create_router(
    get_database,
    app=app,  # Pass FastAPI app for auto-discovery
    # Optional: map collection names to schema names
    openapi_schema_map={"products": "Product"}
)
```

### 3. Mounting the Admin UI

The admin UI provides a web interface for managing your MongoDB collections:

#### Option 1: Using `mount_admin_ui` (Manual Setup)

```python
from fastapi_mongo_admin import create_router, mount_admin_ui

# Create router
admin_router = create_router(
    get_database,
    prefix="/admin",
    ui_mount_path="/admin-ui"  # Optional: include admin UI URL in API docs
)
app.include_router(admin_router)

# Mount UI separately - api_prefix should match router prefix
mount_admin_ui(app, mount_path="/admin-ui", api_prefix="/admin")
```

#### Option 2: Using `mount_admin_app` (Convenience Function)

The `mount_admin_app` function combines router creation and UI mounting in one call:

```python
from fastapi_mongo_admin import mount_admin_app

# Mount everything at once (router + UI)
admin_router = mount_admin_app(
    app,
    get_database,
    router_prefix="/admin",
    ui_mount_path="/admin-ui",
    mount_ui=True  # Set to False to skip UI mounting
)

# With Pydantic models (flexible matching supported)
from pydantic import BaseModel

class Product(BaseModel):
    name: str
    price: float

# Dict format: exact matching
admin_router = mount_admin_app(
    app,
    get_database,
    pydantic_models={"products": Product}  # Matches 'products' collection exactly
)
# OR (exact key match)
admin_router = mount_admin_app(
    app,
    get_database,
    pydantic_models={"Product": Product}  # Matches 'Product' collection (not 'products')
)

# List format: auto-detects and converts
admin_router = mount_admin_app(
    app,
    get_database,
    pydantic_models=[Product]  # Auto-converts to 'products' collection
)

# With explicit model mapping
admin_router = mount_admin_app(
    app,
    get_database,
    pydantic_models={"my_products": Product}
)
```

### 4. Complete Example

Here's a complete example with error handling and logging:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from fastapi_mongo_admin import create_router, mount_admin_ui
import logging

logger = logging.getLogger(__name__)

# MongoDB connection
client = AsyncIOMotorClient("mongodb://localhost:27017")
database = client["my_database"]

async def get_database() -> AsyncIOMotorDatabase:
    """Get database instance."""
    return database

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting application...")
    yield
    # Shutdown
    logger.info("Shutting down application...")
    client.close()

app = FastAPI(
    title="MongoDB Admin API",
    description="Admin interface for MongoDB",
    version="1.0.0",
    lifespan=lifespan
)

# Create and include admin router
admin_router = create_router(
    get_database,
    prefix="/admin",
    tags=["admin"]
)
app.include_router(admin_router)

# Mount admin UI
if mount_admin_ui(app, mount_path="/admin-ui", api_prefix="/admin"):
    logger.info("Admin UI available at /admin-ui/admin.html")
```

## API Reference

### Admin Information Endpoint

#### Get Admin Router Information

```http
GET /admin/
```

**Response:**
```json
{
  "prefix": "/admin",
  "collections_endpoint": "/admin/collections",
  "status": "ok",
  "admin_ui_url": "/admin-ui/admin.html"
}
```

**Note:** The `admin_ui_url` field is only included if the admin UI is mounted and the `ui_mount_path` parameter is provided when creating the router.

### Collections Endpoints

#### List All Collections

```http
GET /admin/collections
```

**Response:**
```json
{
  "collections": ["users", "products", "orders"]
}
```

#### Get Collection Schema

```http
GET /admin/collections/{collection_name}/schema?sample_size=10
```

**Parameters:**
- `collection_name` (path): Name of the collection
- `sample_size` (query, optional): Number of documents to sample (default: 10, max: 100)

**Schema Inference Priority:**

The system uses intelligent model matching:
- **Always**: Exact collection name matches and case-insensitive matching
- **Only for list format**: Singular/plural variations and automatic model name to collection name conversion
- **For dict format**: Exact key matching only (no auto-conversion) - gives you explicit control

**Schema Inference Priority:**
1. Existing documents in the collection (if any)
2. Registered Pydantic models (if provided via `pydantic_models` parameter)
3. OpenAPI/Swagger schemas (if `app` parameter is provided)
4. Empty schema (fallback)

**Response:**
```json
{
  "fields": {
    "name": {
      "type": "str",
      "types": ["str"],
      "example": "John Doe",
      "nullable": false
    },
    "age": {
      "type": "int",
      "types": ["int"],
      "example": 30,
      "nullable": false
    }
  },
  "sample_count": 10,
  "source": "documents"
}
```

**Response (from Pydantic model):**
```json
{
  "fields": {
    "name": {
      "type": "str",
      "types": ["str"],
      "example": "",
      "nullable": false
    },
    "price": {
      "type": "float",
      "types": ["float"],
      "example": 0.0,
      "nullable": false
    }
  },
  "sample_count": 0,
  "source": "pydantic_model"
}
```

**Response (from OpenAPI):**
```json
{
  "fields": {
    "name": {
      "type": "str",
      "types": ["str"],
      "example": "",
      "nullable": false
    }
  },
  "sample_count": 0,
  "source": "openapi_schema"
}
```

### Documents Endpoints

#### List Documents

```http
GET /admin/collections/{collection_name}/documents?skip=0&limit=50&sort_field=name&sort_order=asc
```

**Parameters:**
- `collection_name` (path): Name of the collection
- `skip` (query, optional): Number of documents to skip (default: 0)
- `limit` (query, optional): Maximum number of documents to return (default: 50, max: 1000)
- `sort_field` (query, optional): Field name to sort by
- `sort_order` (query, optional): Sort order - 'asc' or 'desc' (default: 'asc')

**Response:**
```json
{
  "documents": [
    {
      "_id": "507f1f77bcf86cd799439011",
      "name": "John Doe",
      "age": 30
    }
  ],
  "total": 100,
  "skip": 0,
  "limit": 50
}
```

#### Search Documents

```http
POST /admin/collections/{collection_name}/documents/search?skip=0&limit=50&sort_field=name&sort_order=asc
Content-Type: application/json

{
  "name": {"$regex": "John", "$options": "i"},
  "age": {"$gte": 18}
}
```

**Parameters:**
- `collection_name` (path): Name of the collection
- `skip` (query, optional): Number of documents to skip (default: 0)
- `limit` (query, optional): Maximum number of documents to return (default: 50, max: 1000)
- `sort_field` (query, optional): Field name to sort by
- `sort_order` (query, optional): Sort order - 'asc' or 'desc' (default: 'asc')

**Request Body:**
- MongoDB query object (JSON)

**Response:**
```json
{
  "documents": [
    {
      "_id": "507f1f77bcf86cd799439011",
      "name": "John Doe",
      "age": 30
    }
  ],
  "total": 25,
  "skip": 0,
  "limit": 50
}
```

#### Get Single Document

```http
GET /admin/collections/{collection_name}/documents/{document_id}
```

**Response:**
```json
{
  "_id": "507f1f77bcf86cd799439011",
  "name": "John Doe",
  "age": 30,
  "email": "john@example.com"
}
```

#### Create Document

```http
POST /admin/collections/{collection_name}/documents
Content-Type: application/json

{
  "name": "Jane Doe",
  "age": 25,
  "email": "jane@example.com"
}
```

**Response:**
```json
{
  "_id": "507f1f77bcf86cd799439012",
  "name": "Jane Doe",
  "age": 25,
  "email": "jane@example.com"
}
```

#### Update Document

```http
PUT /admin/collections/{collection_name}/documents/{document_id}
Content-Type: application/json

{
  "age": 26,
  "email": "jane.updated@example.com"
}
```

**Response:**
```json
{
  "_id": "507f1f77bcf86cd799439012",
  "name": "Jane Doe",
  "age": 26,
  "email": "jane.updated@example.com"
}
```

#### Delete Document

```http
DELETE /admin/collections/{collection_name}/documents/{document_id}
```

**Response:**
```json
{
  "message": "Document deleted successfully",
  "id": "507f1f77bcf86cd799439012"
}
```

## Advanced Usage

### Using Pydantic Models for Schema Inference

When your collections are empty, you can use Pydantic models to define the schema. The system provides flexible model matching that handles various naming conventions:

**Model Matching Features:**
- **Exact match**: Direct collection name to model key matching (always tried first)
- **Case-insensitive**: Handles 'Users' vs 'users' automatically (always tried)
- **Singular/Plural variations**: Only when models are passed as a list - automatically matches 'User' ↔ 'users', 'Product' ↔ 'products'
- **Automatic conversion**: When using list format, model names like 'User' are automatically converted to 'users' collection name

**Important:** When passing a dictionary, the keys are matched exactly (with case-insensitive fallback). No automatic plural/singular conversion is performed. This allows you to have explicit control over the mapping.

```python
from fastapi import FastAPI
from pydantic import BaseModel, Field
from fastapi_mongo_admin import create_router

# Define your Pydantic models
class Product(BaseModel):
    name: str = Field(..., description="Product name")
    price: float = Field(..., gt=0, description="Product price")
    description: str | None = Field(None, description="Product description")
    in_stock: bool = Field(default=True, description="In stock status")
    tags: list[str] = Field(default_factory=list)

class User(BaseModel):
    email: str = Field(..., description="User email")
    name: str = Field(..., description="User name")
    age: int | None = Field(None, ge=0, le=150)

app = FastAPI()

# Option 1: Explicit mapping (recommended for clarity and exact control)
# Keys are matched exactly (case-insensitive fallback only)
pydantic_models = {
    "products": Product,  # Matches 'products' collection exactly
    "users": User,        # Matches 'users' collection exactly
}

# Option 2: Use model names as keys - matches exactly, no auto-conversion
# If you use "User" as key, it will match "User" collection, NOT "users"
pydantic_models = {
    "User": User,        # Matches 'User' collection (exact match)
    "Product": Product,  # Matches 'Product' collection (exact match)
}

# Option 3: Pass as list - auto-detects and converts collection names
# This is the only format that does automatic plural/singular conversion
pydantic_models = [User, Product]  # Auto-converts to {"users": User, "products": Product}

# Create router with Pydantic models
admin_router = create_router(
    get_database,
    prefix="/admin",
    pydantic_models=pydantic_models
)
```

**Note:**
- Option 1 and 3 will match 'users' and 'products' collections
- Option 2 will match 'User' and 'Product' collections (exact key matching)
- Use list format (Option 3) if you want automatic plural/singular conversion
- Use dict format (Options 1 or 2) if you want explicit, exact control over the mapping

### Automatic OpenAPI Schema Discovery

The package can automatically discover Pydantic models from your FastAPI application's OpenAPI/Swagger schema:

```python
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi_mongo_admin import create_router

# Define your models anywhere in your code
class Product(BaseModel):
    name: str
    price: float
    description: str | None = None

class User(BaseModel):
    email: str
    name: str
    age: int | None = None

app = FastAPI()

# Just pass the app - models are auto-discovered!
admin_router = create_router(
    get_database,
    prefix="/admin",
    app=app,  # Enables automatic model discovery
)

app.include_router(admin_router)
```

**How it works:**
- The system automatically scans your OpenAPI schema for Pydantic models
- Collection names are matched to model names (case-insensitive)
- Handles singular/plural variations (e.g., "products" → "Product")
- Falls back gracefully if no matching model is found

**Manual Schema Mapping:**

If your collection name doesn't match the model name, provide explicit mapping:

```python
admin_router = create_router(
    get_database,
    app=app,
    openapi_schema_map={
        "my_products": "Product",  # Collection → Model
        "customers": "User",       # Different names
    }
)
```

### Using Schema Utilities

The package provides utilities for schema introspection and ObjectId serialization:

```python
from fastapi_mongo_admin import (
    infer_schema,
    infer_schema_from_pydantic,
    infer_schema_from_openapi,
    serialize_object_id
)
from motor.motor_asyncio import AsyncIOMotorCollection
from pydantic import BaseModel
from bson import ObjectId

# Infer schema from a collection
async def analyze_collection(collection: AsyncIOMotorCollection):
    schema = await infer_schema(collection, sample_size=20)
    print(f"Collection has {len(schema['fields'])} fields")
    for field_name, field_info in schema['fields'].items():
        print(f"{field_name}: {field_info['type']}")

# Infer schema from Pydantic model
class Product(BaseModel):
    name: str
    price: float

schema = infer_schema_from_pydantic(Product)
print(schema)  # {'fields': {...}, 'sample_count': 0, 'source': 'pydantic_model'}

# Infer schema from OpenAPI
from fastapi import FastAPI
app = FastAPI()
schema = infer_schema_from_openapi(app, "products", schema_name="Product")

# Serialize ObjectIds in documents
document = {
    "_id": ObjectId(),
    "user_id": ObjectId(),
    "tags": [ObjectId(), ObjectId()],
    "metadata": {
        "created_by": ObjectId()
    }
}

serialized = serialize_object_id(document)
# All ObjectIds are now strings
```

### Custom Database Dependency with Error Handling

```python
from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

async def get_database() -> AsyncIOMotorDatabase:
    """Get database with error handling."""
    try:
        # Check if database is accessible
        await database.client.admin.command("ping")
        return database
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Database connection failed: {str(e)}"
        )
```

### Integration with FastAPI Dependencies

```python
from fastapi import Depends
from fastapi_mongo_admin import create_router

# Use FastAPI's dependency injection
async def get_database() -> AsyncIOMotorDatabase:
    return database

# The router will use this dependency
admin_router = create_router(get_database)
app.include_router(admin_router)
```

### Multiple Database Support

```python
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi_mongo_admin import create_router

app = FastAPI()

# Connect to multiple databases
client = AsyncIOMotorClient("mongodb://localhost:27017")
db1 = client["database1"]
db2 = client["database2"]

async def get_db1():
    return db1

async def get_db2():
    return db2

# Create separate routers for each database
admin_router_1 = create_router(get_db1, prefix="/admin/db1")
admin_router_2 = create_router(get_db2, prefix="/admin/db2")

app.include_router(admin_router_1)
app.include_router(admin_router_2)
```

## Using the Admin UI

The admin UI provides a web-based interface for managing your MongoDB collections:

1. **Access the UI**: Navigate to `http://localhost:8000/admin-ui/admin.html`
2. **Select Language**: Use the language selector in the header to switch between 8 supported languages (English, French, Russian, Spanish, Portuguese, Chinese, Italian, German). Your preference is automatically saved and the UI detects your browser language on first visit.
3. **Toggle Dark Mode**: Click the theme toggle button to switch between light and dark themes (preference is saved, no flicker on page reload)
4. **Select Collection**: Choose a collection from the sidebar
5. **View Documents**: Browse documents with pagination and search
6. **Sort Data**: Click any column header to sort ascending/descending
7. **Filter Documents**: Use filters for enum, boolean, and date fields
8. **Search**: Search across text fields with case-insensitive matching
9. **Create Documents**: Use paginated forms (5 fields per page) to create new documents
10. **Edit Documents**: Click on a document to edit it with paginated form
11. **View Document Details**: Click on `_id` to view full document details
12. **Delete Documents**: Delete documents with confirmation modal
13. **View Schema**: See the inferred schema for each collection
14. **Navigate ObjectIds**: Click on ObjectId fields to navigate to referenced documents

**Features:**
- **Responsive Design**: Built with Tailwind CSS
- **Internationalization**: Support for 8 languages with automatic browser language detection
- **Dark Mode**: Toggle between light and dark themes with persistent preference (no flicker on reload)
- **Reactive UI**: Custom reactive state management with Store pattern
- **Type Preservation**: Maintains data types when creating/editing documents
- **Smart Forms**: Form fields automatically generated based on schema types with pagination
- **Sortable Tables**: Click headers to sort by any column
- **Advanced Filtering**: Server-side filtering with enum, boolean, date, and text field support
- **Collapsible Sidebar**: Toggle sidebar visibility
- **Modal Dialogs**: Centered modals for viewing and editing

## Error Handling

The package includes comprehensive error handling:

- **404 Not Found**: When a document or collection doesn't exist
- **500 Internal Server Error**: For database connection issues
- **Validation Errors**: For invalid query parameters

Example error response:

```json
{
  "detail": "Document not found"
}
```

## Best Practices

### 1. Environment Variables

Always use environment variables for sensitive configuration:

```python
import os
from motor.motor_asyncio import AsyncIOMotorClient

mongodb_url = os.getenv("MONGODB_URL")
client = AsyncIOMotorClient(mongodb_url)
```

### 2. Connection Pooling

Motor handles connection pooling automatically, but you can configure it:

```python
client = AsyncIOMotorClient(
    "mongodb://localhost:27017",
    maxPoolSize=50,
    minPoolSize=10
)
```

### 3. Security Considerations

**Important**: The admin endpoints provide full access to your database. In production:

- Add authentication/authorization middleware
- Restrict access to admin endpoints
- Use HTTPS
- Limit access by IP address
- Consider using environment-specific configurations

Example with authentication:

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != "your-secret-token":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    return credentials.credentials

# Protect admin router
admin_router = create_router(get_database, prefix="/admin")
app.include_router(admin_router, dependencies=[Depends(verify_token)])
```

### 4. Logging

Enable logging for debugging:

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Log database operations
logger.info(f"Connected to database: {database.name}")
```

## Troubleshooting

### Common Issues

#### 1. Connection Refused

```
Error: [Errno 61] Connection refused
```

**Solution**: Ensure MongoDB is running and the connection string is correct.

#### 2. Authentication Failed

```
Error: Authentication failed
```

**Solution**: Check your MongoDB credentials and authSource.

#### 3. Admin UI Not Loading

**Solution**: Ensure the static files are properly mounted:

```python
# Check if mount was successful
if mount_admin_ui(app, mount_path="/admin-ui"):
    print("Admin UI mounted successfully")
else:
    print("Failed to mount - check static files")
```

#### 4. ObjectId Serialization Issues

If you encounter serialization errors, ensure you're using the provided utility:

```python
from fastapi_mongo_admin import serialize_object_id

# Serialize before returning
return serialize_object_id(document)
```

## Development

### Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/tushortz/fastapi-mongo-admin.git
cd fastapi-mongo-admin

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black fastapi_mongo_admin/

# Lint code
ruff check fastapi_mongo_admin/
```

## Examples

### Basic Example

See the `example_usage.py` file in the package for a complete working example.

### Example with Pydantic Models

```python
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pydantic import BaseModel, Field
from fastapi_mongo_admin import create_router, mount_admin_ui

# Define your Pydantic models
class Product(BaseModel):
    name: str = Field(..., description="Product name")
    price: float = Field(..., gt=0)
    description: str | None = None
    in_stock: bool = Field(default=True)

class User(BaseModel):
    email: str
    name: str
    age: int | None = None

app = FastAPI(title="MongoDB Admin with Models")

client = AsyncIOMotorClient("mongodb://localhost:27017")
database = client["my_database"]

async def get_database() -> AsyncIOMotorDatabase:
    return database

# Option 1: Explicit Pydantic models
pydantic_models = {
    "products": Product,
    "users": User,
}
admin_router = create_router(
    get_database,
    prefix="/admin",
    pydantic_models=pydantic_models
)

# Option 2: Automatic discovery from OpenAPI
admin_router = create_router(
    get_database,
    prefix="/admin",
    app=app,  # Auto-discovers Product and User models
)

app.include_router(admin_router)
mount_admin_ui(app, mount_path="/admin-ui", api_prefix="/admin")
```

### Example with Automatic Schema Discovery

```python
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi_mongo_admin import create_router, mount_admin_ui

# Define models - they'll be auto-discovered!
class Product(BaseModel):
    name: str
    price: float
    description: str | None = None

app = FastAPI()

# Create router with app for auto-discovery
admin_router = create_router(
    get_database,
    app=app,  # Enables automatic model discovery
)

app.include_router(admin_router)
mount_admin_ui(app, mount_path="/admin-ui", api_prefix="/admin")
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License - see LICENSE file for details.

## Support

- **Issues**: https://github.com/tushortz/fastapi-mongo-admin/issues
- **Documentation**: https://github.com/tushortz/fastapi-mongo-admin#readme


