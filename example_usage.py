"""Example usage of fastapi-mongo-admin package."""

from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from fastapi_mongo_admin import create_router, mount_admin_ui

# Initialize FastAPI app
app = FastAPI(title="MongoDB Admin Example")

# Set up MongoDB connection
client = AsyncIOMotorClient("mongodb://localhost:27017")
database = client["example_db"]


# Create database dependency function
async def get_database() -> AsyncIOMotorDatabase:
    """Get database instance."""
    return database


# Create admin router with database dependency
admin_router = create_router(
    get_database,
    prefix="/admin",
    tags=["admin"],
)

# Include router in app
app.include_router(admin_router)

# Mount admin UI (optional)
if mount_admin_ui(app, mount_path="/admin-ui"):
    print("Admin UI mounted at /admin-ui/admin.html")
else:
    print("Failed to mount admin UI")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

