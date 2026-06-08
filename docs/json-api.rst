JSON API
========

In addition to the server-rendered UI, FastAPI Mongo Admin exposes a read-only
JSON API under ``/admin/api/``.

Endpoints
---------

List documents
~~~~~~~~~~~~~~

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
~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   GET /admin/api/{collection}/{doc_id}

Response: serialized document dict with ``id`` field.

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
   * - 404
     - Document not found (detail endpoint)

Use cases
---------

* Frontend tooling that consumes admin data
* Internal dashboards and reporting scripts
* Integration tests verifying data state
* Mobile admin clients

Limitations
-----------

The JSON API is **read-only**. Create, update, and delete operations are
available only through the HTML admin UI (or by extending the router).

Filtering via the JSON API currently supports search (``q``) but not list filter
query parameters. Use the HTML changelist for full filter support, or query
MongoDB directly in your application.

Custom prefix
-------------

If you mount the admin at a custom prefix, API paths adjust accordingly:

.. code-block:: python

   mount_admin_app(app, get_database, router_prefix="/manage")

API available at: ``/manage/api/{collection}/``
