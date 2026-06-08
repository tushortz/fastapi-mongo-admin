Custom Admin Views
==================

Register standalone pages in the admin namespace with ``AdminSite.register_view()``.
Use this for dashboards, reports, or any view outside standard CRUD.

Basic registration
------------------

.. code-block:: python

   from fastapi import Request
   from fastapi.responses import HTMLResponse


   async def dashboard(request: Request) -> HTMLResponse:
       return HTMLResponse("""
       <html>
       <head><title>Dashboard</title></head>
       <body>
         <h1>Admin Dashboard</h1>
         <a href="/admin/products/">Products</a>
       </body>
       </html>
       """)


   site.register_view("dashboard", "/dashboard/", dashboard)

Accessible at: ``/admin/dashboard/``

Parameters
----------

.. code-block:: python

   site.register_view(
       name: str,           # Route name (FastAPI internal)
       path: str,           # URL path relative to admin prefix
       endpoint: Callable,   # Async or sync handler
       permission: Callable[[Request, Any], bool] | None = None,
   )

Permission callback
-------------------

Gate access to custom views:

.. code-block:: python

   def admin_only(request: Request, user) -> bool:
       return bool(user and user.get("role") == "admin")

   site.register_view("reports", "/reports/", reports_view, permission=admin_only)

Using admin styles
------------------

Link bundled admin CSS for consistent styling:

.. code-block:: python

   async def dashboard(request: Request) -> HTMLResponse:
       html = """
       <!DOCTYPE html>
       <html lang="en" data-theme="light">
       <head>
         <link rel="stylesheet" href="/admin/static/admin.css">
       </head>
       <body>
         <header class="base-header admin-header">
           <div class="base-header__brand">
             <a href="/admin/">My Admin</a>
           </div>
         </header>
         <main class="base-card admin-main">
           <h1>Dashboard</h1>
         </main>
       </body>
       </html>
       """
       return HTMLResponse(content=html)

Returning Jinja2 templates
--------------------------

For full template integration, render Jinja2 manually or return an
``HTMLResponse`` with rendered content. Custom views are not automatically
wrapped in the admin base layout — you control the full HTML.

Model-specific URLs
-------------------

``ModelAdmin.get_urls()`` registers extra routes under a model prefix:

.. code-block:: python

   class ProductAdmin(ModelAdmin):
       def get_urls(self) -> list[tuple[str, Any]]:
           return [
               ("export/", self.export_view),
           ]

       async def export_view(self, request: Request) -> Response:
           ...

Mounted at: ``/admin/products/export/``

Ecommerce dashboard example
---------------------------

The demo registers a custom dashboard at ``/admin/dashboard/``:

.. code-block:: python

   site.register_view("dashboard", "/dashboard/", ecommerce_dashboard)

See ``example/ecommerce/admin.py`` for the full implementation.
