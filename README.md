# FastAPI Mongo Admin

A powerful FastAPI package that provides generic CRUD operations and a built-in admin UI for MongoDB collections. Perfect for rapid prototyping, database administration, and building admin interfaces for your MongoDB databases.

## Features

- **Generic CRUD Operations** - Create, Read, Update, Delete operations for any MongoDB collection
- **Schema Introspection** - Automatically analyze and infer collection schemas
- **Built-in Admin UI** - Beautiful web interface for database management
- **Automatic ObjectId Serialization** - Seamless JSON serialization of MongoDB ObjectIds
- **Type Hints & Async Support** - Full type hints and async/await support
- **Error Handling** - Comprehensive error handling and validation
- **FastAPI Integration** - Seamlessly integrates with FastAPI applications

## Installation

### Using pip

```bash
pip install fastapi-mongo-admin
```

### Using Poetry

```bash
poetry add fastapi-mongo-admin
```

### Requirements

- Python 3.11+
- FastAPI 0.115.0+
- Motor 3.6.0+
- PyMongo 4.10.1+

## Quick Start

### Basic Setup

Here's a minimal example to get you started:

```python
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from fastapi_mongo_admin import create_router, mount_admin_ui

# Initialize FastAPI app
app = FastAPI(title="My MongoDB Admin App")

# Set up MongoDB connection
client = AsyncIOMotorClient("mongodb://localhost:27017")
database = client["my_database"]

# Create database dependency function
async def get_database() -> AsyncIOMotorDatabase:
    """Get database instance."""
    return database

# Create and include admin router
admin_router = create_router(get_database, prefix="/admin")
app.include_router(admin_router)

# Mount admin UI (optional but recommended)
mount_admin_ui(app, mount_path="/admin-ui")
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
```

### 3. Mounting the Admin UI

The admin UI provides a web interface for managing your MongoDB collections:

```python
from fastapi_mongo_admin import mount_admin_ui

# Mount at default path
mount_admin_ui(app, mount_path="/admin-ui")

# Mount at custom path
if mount_admin_ui(app, mount_path="/my-admin"):
    print("Admin UI mounted successfully")
else:
    print("Failed to mount admin UI")
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
if mount_admin_ui(app, mount_path="/admin-ui"):
    logger.info("Admin UI available at /admin-ui/admin.html")
```

## API Reference

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
  "sample_count": 10
}
```

### Documents Endpoints

#### List Documents

```http
GET /admin/collections/{collection_name}/documents?skip=0&limit=50
```

**Parameters:**
- `collection_name` (path): Name of the collection
- `skip` (query, optional): Number of documents to skip (default: 0)
- `limit` (query, optional): Maximum number of documents to return (default: 50, max: 1000)

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

### Using Schema Utilities

The package provides utilities for schema introspection and ObjectId serialization:

```python
from fastapi_mongo_admin import infer_schema, serialize_object_id
from motor.motor_asyncio import AsyncIOMotorCollection
from bson import ObjectId

# Infer schema from a collection
async def analyze_collection(collection: AsyncIOMotorCollection):
    schema = await infer_schema(collection, sample_size=20)
    print(f"Collection has {len(schema['fields'])} fields")
    for field_name, field_info in schema['fields'].items():
        print(f"{field_name}: {field_info['type']}")

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
2. **Select Collection**: Choose a collection from the dropdown
3. **View Documents**: Browse documents with pagination
4. **Create Documents**: Use the form to create new documents
5. **Edit Documents**: Click on a document to edit it
6. **Delete Documents**: Delete documents with confirmation
7. **View Schema**: See the inferred schema for each collection

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

See the `example_usage.py` file in the package for a complete working example.

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


