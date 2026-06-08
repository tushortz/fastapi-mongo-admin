Field Mapping
=============

When your MongoDB documents use different field names than your Pydantic model,
``field_mapping`` translates between them transparently.

Use cases
---------

* Legacy databases with non-standard key names
* Gradual schema migration (old keys in DB, new names in code)
* MongoDB conventions (``product_sku``) vs Python conventions (``sku``)

Configuration
-------------

.. code-block:: python

   class ProductAdmin(ModelAdmin):
       field_mapping = {
           "sku": "product_sku",       # model field → DB key
           "cost_price": "unit_cost",
       }

The mapping is **model field name → MongoDB key**.

What gets translated
--------------------

Read operations
~~~~~~~~~~~~~~~

Documents fetched from MongoDB are translated to model field names before
display in changelists and forms.

Write operations
~~~~~~~~~~~~~~~~

Form data validated through Pydantic uses model field names, then translated
to database keys before insert/update.

Queries
~~~~~~~

Search, filters, ordering, and date hierarchy queries are translated to use
database field names.

List filters
~~~~~~~~~~~~

Filter ``queryset()`` fragments are automatically remapped.

Example
-------

**Pydantic model:**

.. code-block:: python

   class Product(BaseModel):
       sku: str
       cost_price: float

**MongoDB document:**

.. code-block:: json

   {
     "_id": "...",
     "product_sku": "WIDGET-001",
     "unit_cost": 12.50,
     "name": "Widget"
   }

**Admin display:** The changelist and forms show ``sku`` and ``cost_price`` with
values from ``product_sku`` and ``unit_cost``.

**Manual inserts:** When inserting documents directly into MongoDB, use the
database key names (``product_sku``, not ``sku``).

Implementation
--------------

Translation functions live in ``fastapi_mongo_admin.services.mapping``:
``translate_to_db``, ``translate_from_db``, and ``translate_query``. Reverse
mapping for reads is built automatically from the forward mapping.

See :doc:`api-reference` for function signatures.

Troubleshooting
---------------

**Field shows empty after manual DB insert**

You inserted using the model field name instead of the mapped database key.
Either use mapped keys in MongoDB or remove ``field_mapping``.

**Filter returns no results**

Ensure filter values match the data type stored in MongoDB. Field mapping
handles key translation but not value transformation.

**Search does not find documents**

``search_fields`` use model field names; the repository translates them to
database keys before querying.
