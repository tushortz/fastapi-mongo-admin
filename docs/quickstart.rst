Quick Start
===========

This guide walks through the minimum steps to get a working admin interface.

1. Define Pydantic models
-------------------------

.. code-block:: python

   from pydantic import BaseModel


   class Product(BaseModel):
       name: str
       price: float
       category: str
       active: bool = True

2. Create ModelAdmin classes
----------------------------

.. code-block:: python

   from fastapi_mongo_admin import ModelAdmin, site, display, action
   from fastapi import Request


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
       async def deactivate_selected(
           self, request: Request, queryset: list[dict]
       ) -> None:
           # Implement bulk deactivation in your service layer
           pass


   site.register(Product, ProductAdmin)

3. Mount in FastAPI (async)
---------------------------

.. code-block:: python

   from fastapi import FastAPI
   from motor.motor_asyncio import AsyncIOMotorClient
   from fastapi_mongo_admin import mount_admin_app

   app = FastAPI()
   client = AsyncIOMotorClient("mongodb://localhost:27017")
   database = client["my_db"]


   async def get_database():
       return database


   mount_admin_app(app, get_database, admin_site=site, mode="async")

4. Sync MongoDB (PyMongo)
-------------------------

.. code-block:: python

   from pymongo import MongoClient
   from fastapi_mongo_admin import mount_admin_app

   client = MongoClient("mongodb://localhost:27017")
   db = client["my_db"]

   mount_admin_app(app, lambda: db, admin_site=site, mode="sync")

5. Visit the admin
------------------

Start your application and open:

.. code-block:: text

   http://localhost:8000/admin/

You should see the admin index with your registered models. Click a model to
open its changelist, add documents, edit existing ones, and run bulk actions.

Add authentication
------------------

Without an ``auth_dependency``, the admin is publicly accessible. In production,
always provide authentication:

.. code-block:: python

   from fastapi import Depends, HTTPException


   async def get_admin_user():
       # Validate JWT, session, or API key
       return {"id": "user-1", "is_staff": True}


   mount_admin_app(
       app,
       get_database,
       admin_site=site,
       auth_dependency=get_admin_user,
   )

See :doc:`authentication` for detailed patterns.

Complete example
----------------

A full ecommerce demo with seven collections, seed data, and customization
examples lives in the repository under ``example/ecommerce/``. See
:doc:`ecommerce-demo` for setup instructions.
