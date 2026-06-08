AdminSite
=========

The ``AdminSite`` is the central registry for models and custom admin pages.
It mirrors Django's ``AdminSite`` pattern.

Default site
------------

A global ``site`` instance is exported from the package:

.. code-block:: python

   from fastapi_mongo_admin import site, ModelAdmin

   site.register(Product, ProductAdmin)

Custom AdminSite
----------------

Create a dedicated site for branding, template overrides, or multi-tenant apps:

.. code-block:: python

   from pathlib import Path
   from fastapi_mongo_admin import AdminSite

   class EcommerceAdminSite(AdminSite):
       site_header = "Ecommerce Admin"
       site_title = "Shop Manager"
       index_title = "Store administration"

   admin_site = EcommerceAdminSite(template_dirs=[Path("myapp/templates")])

Branding attributes
~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1

   * - Attribute
     - Default
     - Used in
   * - ``site_header``
     - ``"FastAPI Mongo Admin"``
     - Page header on all admin pages
   * - ``site_title``
     - ``"Admin"``
     - Browser title suffix
   * - ``index_title``
     - ``"Site administration"``
     - Admin index page heading

Registering models
------------------

Single model
~~~~~~~~~~~~

.. code-block:: python

   site.register(Product, ProductAdmin)

Multiple models with the same admin class
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   site.register([Category, Brand], CatalogAdmin)

Inline options
~~~~~~~~~~~~~~

Pass options as keyword arguments to override ``ModelAdmin`` attributes:

.. code-block:: python

   site.register(
       Product,
       ProductAdmin,
       list_display=["name", "price"],
       list_per_page=50,
   )

``collection_name`` is required — either on the ``ModelAdmin`` class or as a
registration option. Duplicate collection names raise ``ValueError``.

Registering custom views
------------------------

Add pages outside the standard CRUD flow:

.. code-block:: python

   from fastapi import Request
   from fastapi.responses import HTMLResponse


   async def reports(request: Request) -> HTMLResponse:
       return HTMLResponse("<h1>Reports</h1>")


   site.register_view("Reports", "/reports/", reports)

The view is mounted at ``/admin/reports/`` (relative to your router prefix).
An optional ``permission`` callable can gate access:

.. code-block:: python

   def staff_only(request: Request, user) -> bool:
       return bool(user and user.get("is_staff"))

   site.register_view("Reports", "/reports/", reports, permission=staff_only)

Template directories
--------------------

Override bundled templates by registering a search path:

.. code-block:: python

   from pathlib import Path

   site = AdminSite(template_dirs=[Path("myapp/templates")])

Jinja2 resolves templates from your directories **before** the package defaults.
See :doc:`templates` for override patterns.

CSRF tokens
-----------

When your FastAPI app uses ``SessionMiddleware``, the admin reads a
``csrf_token`` from the session and includes it in forms. Mutating requests
(POST add/change/delete/action) verify the token automatically.

.. code-block:: python

   from starlette.middleware.sessions import SessionMiddleware

   app.add_middleware(SessionMiddleware, secret_key="your-secret-key")

See :doc:`api-reference` for the full ``AdminSite`` API.
