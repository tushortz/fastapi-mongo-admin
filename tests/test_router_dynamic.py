import pytest
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi_mongo_admin.admin import AdminSite, ModelAdmin
from fastapi_mongo_admin.router import create_router

class Product(BaseModel):
    name: str
    price: float

@pytest.mark.asyncio
async def test_create_router_dynamic_routes(test_database):
    """Test that create_router generates model-specific routes."""
    site = AdminSite()
    site.register(Product, collection_name="products")
    
    async def get_db():
        return test_database
        
    app = FastAPI()
    router = create_router(get_database=get_db, admin_site=site)
    app.include_router(router)
    
    # Check if routes for 'products' exist
    paths = [r.path for r in app.routes]
    
    # Dynamic model-specific routes (prefixed with /admin)
    assert "/admin/products/" in paths
    assert "/admin/products/{document_id}" in paths
    
    # Core admin routes
    assert "/admin/config" in paths
    assert "/admin/collections" in paths

@pytest.mark.asyncio
async def test_swagger_schema_generation(test_database):
    """Test that generated routes have correct Pydantic models in schema."""
    site = AdminSite()
    site.register(Product, collection_name="products")
    
    async def get_db():
        return test_database
        
    app = FastAPI()
    router = create_router(get_database=get_db, admin_site=site)
    app.include_router(router)
    
    schema = app.openapi()
    
    # Check if Product is in components/schemas
    assert "Product" in schema["components"]["schemas"]
    
    # Check if /admin/products/ POST route uses Product model
    post_path = "/admin/products/"
    assert post_path in schema["paths"]
    assert "post" in schema["paths"][post_path]
    # Check request body content type and schema reference
    request_body = schema["paths"][post_path]["post"]["requestBody"]
    ref = request_body["content"]["application/json"]["schema"]["$ref"]
    assert "Product" in ref

def test_router_tags(test_database):
    """Test that routes are tagged correctly by model."""
    site = AdminSite()
    site.register(Product, collection_name="products")
    
    router = create_router(get_database=lambda: None, admin_site=site)
    
    # Find the post route for products (prefixed with /admin)
    product_routes = [r for r in router.routes if r.path == "/admin/products/"]
    assert len(product_routes) > 0
    for route in product_routes:
        assert "Admin: Products" in route.tags
