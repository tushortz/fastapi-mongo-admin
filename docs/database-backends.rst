Database Backends
=================

FastAPI Mongo Admin supports both async (Motor) and sync (PyMongo) MongoDB
backends through a protocol-based abstraction.

Async mode (Motor)
------------------

Recommended for FastAPI applications using async route handlers.

.. code-block:: python

   from motor.motor_asyncio import AsyncIOMotorClient
   from fastapi_mongo_admin import mount_admin_app

   client = AsyncIOMotorClient("mongodb://localhost:27017")
   database = client["my_db"]


   async def get_database():
       return database


   mount_admin_app(app, get_database, admin_site=site, mode="async")

``get_database`` can be sync or async — the router awaits the result when needed.

Sync mode (PyMongo)
-------------------

For applications already using synchronous PyMongo or when Motor is not desired.

.. code-block:: python

   from pymongo import MongoClient
   from fastapi_mongo_admin import mount_admin_app

   client = MongoClient("mongodb://localhost:27017")
   db = client["my_db"]

   mount_admin_app(app, lambda: db, admin_site=site, mode="sync")

Route handlers remain async; the repository calls sync PyMongo methods internally.

Backend protocol
----------------

Both backends implement a common interface in ``fastapi_mongo_admin.db.protocol``:

.. list-table::
   :header-rows: 1

   * - Method
     - Purpose
   * - ``find(query, skip, limit, sort)``
     - Query documents with pagination
   * - ``find_one(query)``
     - Fetch single document
   * - ``count(query)``
     - Count matching documents
   * - ``insert_one(document)``
     - Insert and return ID
   * - ``update_one(query, document)``
     - Replace/update document
   * - ``delete_one(query)``
     - Delete single document
   * - ``delete_many(ids)``
     - Bulk delete by IDs

CollectionRepository
--------------------

The repository wraps a backend and adds:

* Pydantic validation on create/update
* Field mapping translation
* ``save_model`` / ``delete_model`` hooks
* Changelist query building (search, filters, ordering)
* ``list_select_related`` resolution

Related backends
----------------

When ``list_select_related`` is configured, the repository creates additional
backend instances for related collections:

.. code-block:: python

   list_select_related = {"category_id": "categories"}

Motor backends are used in async mode; PyMongo backends in sync mode.

BSON serialization
------------------

Documents are serialized for templates and JSON API via ``serialize_document()``:

* ``ObjectId`` → string
* ``datetime`` / ``date`` → ISO format
* ``Decimal128`` / ``Decimal`` → string
* Nested dicts and lists → recursive serialization
* ``_id`` is also exposed as ``id``

Before writing to MongoDB, ``prepare_for_mongodb()`` converts:

* ``Decimal`` → ``Decimal128``
* ``date`` → ``datetime`` at midnight UTC

Connection configuration
------------------------

Use standard MongoDB connection strings:

.. code-block:: python

   MONGODB_URL = "mongodb://user:pass@host:27017/my_db?authSource=admin"
   client = AsyncIOMotorClient(MONGODB_URL)

For connection pool tuning, see MongoDB driver documentation. The admin does
not manage connection lifecycle — your ``get_database`` callable owns the client.

Testing with mongomock
----------------------

The test suite uses ``mongomock`` for in-memory MongoDB simulation:

.. code-block:: python

   import mongomock

   client = mongomock.MongoClient()
   db = client["test_db"]

   mount_admin_app(app, lambda: db, mode="sync")

See :doc:`api-reference` for backend and repository APIs.
