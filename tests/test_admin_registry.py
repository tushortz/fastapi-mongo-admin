import pytest
from pydantic import BaseModel
from fastapi_mongo_admin.admin import AdminSite, ModelAdmin

class Product(BaseModel):
    name: str
    price: float

class Category(BaseModel):
    name: str

def test_admin_site_register_basic():
    """Test basic model registration."""
    site = AdminSite()
    site.register(Product, collection_name="products")
    
    assert "products" in site._registry
    admin = site._registry["products"]
    assert isinstance(admin, ModelAdmin)
    assert admin.collection_name == "products"

def test_admin_site_register_with_custom_class():
    """Test registration with custom Admin class."""
    class CustomProductAdmin(ModelAdmin):
        list_display = ["name"]
        collection_name = "my_products"
        
    site = AdminSite()
    site.register(Product, CustomProductAdmin)
    
    admin = site._registry["my_products"]
    assert admin.collection_name == "my_products"
    assert admin.list_display == ["name"]

def test_admin_site_get_models():
    """Test getting registered models."""
    site = AdminSite()
    site.register(Product, collection_name="products")
    site.register(Category, collection_name="categories")
    
    models = site.get_models()
    # site.get_models() returns the registry items' models
    assert Product in [m for m in models]
    assert Category in [m for m in models]

def test_model_admin_defaults():
    """Test ModelAdmin default attributes."""
    admin = ModelAdmin(Product)
    assert admin.model == Product
    assert admin.collection_name is None  # Defaults to None in base class

def test_admin_site_get_pydantic_models():
    """Test getting pydantic models mapping."""
    site = AdminSite()
    site.register(Product, collection_name="products")
    
    mapping = site.get_pydantic_models()
    assert mapping["products"] == Product
