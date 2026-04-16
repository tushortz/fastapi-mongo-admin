from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pydantic import BaseModel
from datetime import datetime
from fastapi_mongo_admin import mount_admin_app, ModelAdmin, site

# Define your Pydantic models
class Product(BaseModel):
    name: str
    price: float
    category: str
    in_stock: bool

class User(BaseModel):
    username: str
    email: str
    is_active: bool = True
    created_at: datetime = datetime.now()
    role: str = "user"

# Define custom admin (optional)
class ProductAdmin(ModelAdmin):
    model = Product
    collection_name = "products"
    list_display = ["name", "category", "price", "in_stock"]
    search_fields = ["name", "category"]
    # Mapping model field 'name' to 'product_name' in MongoDB
    field_mapping = {
        "name": "product_name"
    }

class UserAdmin(ModelAdmin):
    collection_name = "users"
    list_display = ["username", "email", "created_at", "role"]
    search_fields = ["username", "email"]
    list_filter = ["is_active"]
    list_per_page = 10 

# site.register(Model, AdminClass) is the standard way to register
site.register(Product, ProductAdmin)
site.register(User, UserAdmin)

# Initialize FastAPI app
app = FastAPI(title="FastAPI Mongo Admin: Django-style")

# Set up MongoDB connection
client = AsyncIOMotorClient("mongodb://localhost:27017")
database = client["example_db"]

# Create database dependency function
async def get_database() -> AsyncIOMotorDatabase:
    return database

# Mount admin - Clean and explicit
mount_admin_app(
    app,
    get_database,
    admin_site=site,
)

if __name__ == "__main__":
    import uvicorn

    print("Starting server...")
    print("Admin UI: http://localhost:8000/admin-ui/admin.html")
    print("API Docs: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
