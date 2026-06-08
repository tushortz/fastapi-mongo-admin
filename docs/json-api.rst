JSON API
========

In addition to the server-rendered UI, FastAPI Mongo Admin exposes a JSON API
under ``/admin/api/``. By default the API is **read-only** and only ``GET``
endpoints appear in OpenAPI (``/docs``).

Enable write endpoints
----------------------

Pass ``api_write_methods=True`` to ``mount_admin_app()`` or
``create_admin_router()`` to register ``POST``, ``PUT``, ``PATCH``, and ``DELETE``
routes and include them in Swagger:

.. code-block:: python

   mount_admin_app(
       app,
       get_database,
       admin_site=site,
       auth_dependency=get_admin_user,
       api_write_methods=True,
   )

When ``api_write_methods`` is ``False`` (default), write routes are not
registered at all — ``/docs`` lists only ``GET`` operations.

Endpoints
---------

Read (always available)
~~~~~~~~~~~~~~~~~~~~~~~

List documents
^^^^^^^^^^^^^^

.. code-block:: text

   GET /admin/api/{collection}/

Query parameters:

.. list-table::
   :header-rows: 1

   * - Parameter
     - Description
   * - ``page``
     - Page number (default: 1)
   * - ``q``
     - Search query (searches ``search_fields``)

Response:

.. code-block:: json

   {
     "results": [
       {"id": "...", "name": "Widget", "price": "29.99"}
     ],
     "total": 42,
     "page": 1,
     "per_page": 25,
     "num_pages": 2
   }

Get single document
^^^^^^^^^^^^^^^^^^^

.. code-block:: text

   GET /admin/api/{collection}/{doc_id}

Response: serialized document dict with ``id`` field.

Write (``api_write_methods=True``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1

   * - Method
     - URL
     - Description
   * - ``POST``
     - ``/admin/api/{collection}/``
     - Create document (JSON body). Returns ``201`` with the created document.
   * - ``PUT``
     - ``/admin/api/{collection}/{doc_id}``
     - Update document (JSON body). Returns the updated document.
   * - ``PATCH``
     - ``/admin/api/{collection}/{doc_id}``
     - Partial update (JSON body). Returns the updated document.
   * - ``DELETE``
     - ``/admin/api/{collection}/{doc_id}``
     - Delete document. Returns ``204 No Content``.

Write requests use the same Pydantic validation and ``ModelAdmin`` hooks as the
HTML forms. Permissions are enforced via ``has_add_permission``,
``has_change_permission``, and ``has_delete_permission``.

Example create:

.. code-block:: bash

   curl -X POST -H "Authorization: Bearer your-token" \
        -H "Content-Type: application/json" \
        -d '{"name": "Widget", "price": 9.99}' \
        "http://localhost:8000/admin/api/products/"

OpenAPI / Swagger
-----------------

FastAPI's ``/docs`` reflects the configured API surface:

.. list-table::
   :header-rows: 1

   * - ``api_write_methods``
     - Documented methods
   * - ``False`` (default)
     - ``GET`` only
   * - ``True``
     - ``GET``, ``POST``, ``PUT``, ``PATCH``, ``DELETE``

Authentication
--------------

The JSON API uses the same ``auth_dependency`` as the HTML admin. Include your
auth credentials on every request:

.. code-block:: bash

   curl -H "Authorization: Bearer your-token" \
        "http://localhost:8000/admin/api/products/?page=1&q=widget"

Errors
------

.. list-table::
   :header-rows: 1

   * - Status
     - Cause
   * - 401
     - Missing or invalid authentication
   * - 403
     - Permission denied for the requested action
   * - 404
     - Document not found (detail/update/delete endpoints)
   * - 422
     - Pydantic validation failure on write requests

Use cases
---------

* Frontend tooling that consumes admin data
* Internal dashboards and reporting scripts
* Integration tests verifying data state
* Mobile admin clients
* Headless CRUD when ``api_write_methods=True``

Limitations
-----------

Filtering via the JSON API currently supports search (``q``) but not list filter
query parameters. Use the HTML changelist for full filter support, or query
MongoDB directly in your application.

Custom prefix
-------------

If you mount the admin at a custom prefix, API paths adjust accordingly:

.. code-block:: python

   mount_admin_app(app, get_database, router_prefix="/manage")

API available at: ``/manage/api/{collection}/``
