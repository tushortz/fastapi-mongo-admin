"""Test script to verify OpenAPI schema inference."""

from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pydantic import BaseModel, Field

from fastapi_mongo_admin import create_router, mount_admin_ui


# Define a Pydantic model
class Product(BaseModel):
    """Product model for testing."""
    name: str = Field(..., description="Product name")
    price: float = Field(..., gt=0, description="Product price")
    description: str | None = Field(None, description="Product description")
    in_stock: bool = Field(default=True, description="In stock status")


# Initialize FastAPI app
app = FastAPI(title="Test OpenAPI Inference")

# Set up MongoDB connection
client = AsyncIOMotorClient("mongodb://localhost:27017")
database = client["test_db"]


async def get_database() -> AsyncIOMotorDatabase:
    """Get database instance."""
    return database


# Create router WITH the app instance
# The app parameter enables automatic discovery of Pydantic models
# from your FastAPI application's OpenAPI schema
admin_router = create_router(
    get_database,
    prefix="/api/v1/admin",
    tags=["admin"],
    app=app,  # Pass the app instance - enables auto-discovery!
    # Optional: map collection name to schema name if different
    # Only needed if collection name doesn't match model name
    # openapi_schema_map={"products": "Product"}
)

# Include router in app
app.include_router(admin_router)

# Mount admin UI
mount_admin_ui(app, mount_path="/admin-ui")

if __name__ == "__main__":
    import uvicorn
    print("Starting server...")
    print("Access admin UI at: http://localhost:8000/admin-ui/admin.html")
    print("OpenAPI docs at: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)


