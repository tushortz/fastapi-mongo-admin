URL Reference
=============

Default admin routes when mounted with ``router_prefix="/admin"``.

Site routes
-----------

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - URL
     - Description
   * - ``GET /admin/``
     - Admin index (model list)
   * - ``POST /admin/preferences/``
     - Set language/theme cookies
   * - ``GET /admin/static/{path}``
     - CSS, JavaScript, and assets

Model CRUD routes
-----------------

For each registered collection ``{collection}``:

.. list-table::
   :header-rows: 1
   :widths: 45 55

   * - URL
     - Description
   * - ``GET /admin/{collection}/``
     - Changelist (filters, search, pagination)
   * - ``GET /admin/{collection}/add/``
     - Add form
   * - ``POST /admin/{collection}/add/``
     - Create document
   * - ``GET /admin/{collection}/{id}/change/``
     - Change form
   * - ``POST /admin/{collection}/{id}/change/``
     - Update document
   * - ``GET /admin/{collection}/{id}/delete/``
     - Delete confirmation
   * - ``POST /admin/{collection}/{id}/delete/``
     - Delete document
   * - ``POST /admin/{collection}/action/``
     - Bulk action

Changelist query parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1

   * - Parameter
     - Description
   * - ``page``
     - Page number
   * - ``q``
     - Search text
   * - ``all``
     - Set to ``1`` to show all (up to ``list_max_show_all``)
   * - ``year``, ``month``, ``day``
     - Date hierarchy drill-down
   * - Filter params
     - One per active list filter (e.g. ``status=published``)
   * - ``lang``, ``theme``
     - Set preference cookies (redirects once)

JSON API routes
---------------

.. list-table::
   :header-rows: 1

   * - URL
     - Description
   * - ``GET /admin/api/{collection}/``
     - List documents (paginated JSON)
   * - ``GET /admin/api/{collection}/{id}``
     - Single document JSON

Custom views
------------

Registered via ``site.register_view(name, path, endpoint)``:

.. code-block:: text

   GET /admin{path}

Example: ``register_view("dashboard", "/dashboard/", handler)`` →
``GET /admin/dashboard/``

Model-specific URLs
-------------------

Registered via ``ModelAdmin.get_urls()``:

.. code-block:: text

   GET /admin/{collection}/{custom_path}

Example: ``("export/", handler)`` → ``GET /admin/products/export/``

Custom router prefix
--------------------

.. code-block:: python

   mount_admin_app(app, get_database, router_prefix="/manage")

All routes are prefixed with ``/manage`` instead of ``/admin``.

Mounting manually
-----------------

For advanced setups, use ``create_admin_router()`` directly:

.. code-block:: python

   from fastapi_mongo_admin import create_admin_router

   router = create_admin_router(
       admin_site,
       get_database,
       prefix="/admin",
       mode="async",
       auth_dependency=get_user,
   )
   app.include_router(router)

This gives full control over router inclusion order and middleware scope.
