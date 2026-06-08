List Filters
============

List filters appear in the changelist sidebar and narrow results by field values.
Configure them via ``ModelAdmin.list_filter``.

Field name filters
------------------

Pass field names to auto-select a filter class based on field type:

.. code-block:: python

   list_filter = ["status", "is_active", "published_at", "category"]

Auto-selection rules
~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1

   * - Field type
     - Filter class
   * - ``bool``
     - ``BooleanFieldListFilter``
   * - ``date`` / ``datetime``
     - ``DateFieldListFilter``
   * - Field in ``choices``
     - ``ChoiceListFilter``
   * - Other
     - ``ChoiceListFilter`` (empty lookups unless choices configured)

Built-in filter classes
-----------------------

BooleanFieldListFilter
~~~~~~~~~~~~~~~~~~~~~~

Filters boolean fields with Yes/No options.

.. code-block:: python

   from fastapi_mongo_admin.admin.filters import BooleanFieldListFilter

   list_filter = ["is_active"]  # auto-selected for bool fields

DateFieldListFilter
~~~~~~~~~~~~~~~~~~~

Predefined date ranges: Today, Past 7 days, This month, This year.

.. code-block:: python

   from fastapi_mongo_admin.admin.filters import DateFieldListFilter

   list_filter = ["published_at", "created_at"]

ChoiceListFilter
~~~~~~~~~~~~~~~~

Filters by discrete values from ``ModelAdmin.choices`` or field metadata:

.. code-block:: python

   choices = {
       "status": [("draft", "Draft"), ("published", "Published")],
   }
   list_filter = ["status"]

RelatedFieldListFilter
~~~~~~~~~~~~~~~~~~~~~~

Filter by ObjectId references to related documents:

.. code-block:: python

   from fastapi_mongo_admin.admin.filters import RelatedFieldListFilter

   class ProductCategoryFilter(RelatedFieldListFilter):
       parameter_name = "category_id"
       related_collection = "categories"
       display_field = "name"

   list_filter = [ProductCategoryFilter]

Custom ListFilter
-----------------

Subclass ``ListFilter`` for full control:

.. code-block:: python

   from fastapi_mongo_admin.admin.filters.base import ListFilter


   class PriceRangeFilter(ListFilter):
       title = "Price range"
       parameter_name = "price_range"

       def lookups(self) -> list[tuple[str, str]]:
           return [
               ("low", "Under $25"),
               ("mid", "$25 – $100"),
               ("high", "Over $100"),
           ]

       def queryset(self, value: str) -> dict:
           if value == "low":
               return {"price": {"$lt": 25}}
           if value == "mid":
               return {"price": {"$gte": 25, "$lte": 100}}
           if value == "high":
               return {"price": {"$gt": 100}}
           return {}

Register the class directly:

.. code-block:: python

   list_filter = [PriceRangeFilter]

Field mapping integration
-------------------------

Filters automatically translate field names through ``field_mapping``. If your
model uses ``sku`` but MongoDB stores ``product_sku``, the filter query targets
the correct database key.

Query parameter names
---------------------

Each filter uses its ``parameter_name`` (defaults to the field name) as the URL
query parameter:

.. code-block:: text

   /admin/products/?status=published&is_active=1

Multiple filters are combined with logical AND.

Date hierarchy
--------------

Separate from list filters, ``date_hierarchy`` adds year/month/day navigation:

.. code-block:: python

   date_hierarchy = "placed_at"

Query params: ``?year=2025``, ``?year=2025&month=6``, ``?year=2025&month=6&day=8``.

See :doc:`api-reference` for filter class APIs.
