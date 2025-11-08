"""Example usage of fastapi-mongo-admin package."""

from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from fastapi_mongo_admin import mount_admin_app

# Initialize FastAPI app
app = FastAPI(title="MongoDB Admin Example")

# Set up MongoDB connection
client = AsyncIOMotorClient("mongodb://localhost:27017")
database = client["example_db"]


# Create database dependency function
async def get_database() -> AsyncIOMotorDatabase:
    """Get database instance."""
    return database


# Mount admin app (router + UI) in one call - simplest way!
admin_router = mount_admin_app(
    app,
    get_database,
    router_prefix="/admin",
    ui_mount_path="/admin-ui",
)

# Alternative: Manual setup (if you need more control)
# from fastapi_mongo_admin import create_router, mount_admin_ui
# admin_router = create_router(get_database, prefix="/admin", tags=["admin"])
# app.include_router(admin_router)
# mount_admin_ui(app, mount_path="/admin-ui")

if __name__ == "__main__":
    import uvicorn

    print("Starting server...")
    print("Admin UI: http://localhost:8000/admin-ui/admin.html")
    print("API Docs: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)

