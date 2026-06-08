ModelAdmin
==========

``ModelAdmin`` is the configuration class for each registered model. It controls
changelist columns, filters, forms, permissions, and lifecycle hooks.

Basic configuration
-------------------

.. code-block:: python

   class ProductAdmin(ModelAdmin):
       model = Product                    # Pydantic model
       collection_name = "products"       # MongoDB collection (required)
       list_display = ["name", "price", "active"]
       list_display_links = ["name"]
       list_filter = ["category", "active"]
       search_fields = ["name", "category"]
       list_per_page = 25
       ordering = ["-created_at"]

Configuration reference
-----------------------

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Option
     - Description
   * - ``model``
     - Pydantic ``BaseModel`` for validation and form inference
   * - ``collection_name``
     - MongoDB collection name (required)
   * - ``list_display``
     - Changelist columns — field names or ``@display`` methods
   * - ``list_display_links``
     - Clickable columns (default: first column)
   * - ``list_editable``
     - Fields editable inline on the changelist
   * - ``list_filter``
     - Field names or ``ListFilter`` subclasses
   * - ``search_fields``
     - Fields searched with case-insensitive regex
   * - ``list_per_page``
     - Pagination size (default: 25)
   * - ``list_max_show_all``
     - Max rows when "show all" is selected (default: 200)
   * - ``ordering``
     - Default sort; prefix with ``-`` for descending
   * - ``date_hierarchy``
     - Field name for year/month/day drill-down navigation
   * - ``list_select_related``
     - ``{"field": "collection"}`` for related document lookups
   * - ``fieldsets``
     - Grouped change form layout
   * - ``readonly_fields``
     - Non-editable fields on change forms
   * - ``field_mapping``
     - Model field → MongoDB key mapping
   * - ``actions``
     - Enabled bulk action method names
   * - ``choices``
     - Choice lookups for filters and select widgets
   * - ``formfield_overrides``
     - Per-field widget and HTML attribute overrides
   * - ``date_format``
     - Display format for ``date`` fields (default: ``8 Apr 2026``)
   * - ``datetime_format``
     - Display format for ``datetime`` fields (default: ``8 Apr 2026, 7:32pm``)

Template overrides
~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1

   * - Attribute
     - Default template
   * - ``change_list_template``
     - ``admin/change_list.html``
   * - ``change_form_template``
     - ``admin/change_form.html``
   * - ``delete_confirmation_template``
     - ``admin/delete_confirmation.html``

Display columns
---------------

Field names
~~~~~~~~~~~

Reference model fields directly in ``list_display``:

.. code-block:: python

   list_display = ["name", "price", "active"]

``@display`` decorator
~~~~~~~~~~~~~~~~~~~~~~

Add computed columns with custom rendering:

.. code-block:: python

   from fastapi_mongo_admin import display


   @display(description="Price", ordering="price")
   def price_display(self, obj: dict) -> str:
       return f"${obj.get('price', 0):,.2f}"

The ``ordering`` parameter enables sortable columns (maps to the underlying field).

Fieldsets
---------

Group fields on add/change forms:

.. code-block:: python

   fieldsets = [
       ("Basic info", {"fields": ["name", "sku", "description"]}),
       ("Pricing", {"fields": ["price", "compare_at_price", "is_taxable"]}),
       ("Timestamps", {"fields": ["created_at", "updated_at"]}),
   ]

If ``fieldsets`` is not set, all model fields appear in a single group.

Readonly fields
---------------

.. code-block:: python

   readonly_fields = ["created_at", "updated_at", "order_number"]

Readonly fields are displayed but not submitted on update. Existing values are
preserved when the field is absent from the form POST.

Choices
-------

Provide discrete values for filters and select form widgets:

.. code-block:: python

   choices = {
       "status": [
           ("draft", "Draft"),
           ("published", "Published"),
           ("archived", "Archived"),
       ],
   }

Enum fields can be generated dynamically:

.. code-block:: python

   choices = {
       "status": [(s.value, s.name.replace("_", " ").title()) for s in ProductStatus],
   }

Date hierarchy
--------------

Enable year → month → day drill-down on a date/datetime field:

.. code-block:: python

   date_hierarchy = "published_at"

Navigation links appear above the changelist. Query params ``year``, ``month``,
and ``day`` filter results progressively.

List select related
-------------------

Resolve ObjectId references to related documents for display:

.. code-block:: python

   list_select_related = {
       "category_id": "categories",
       "brand_id": "brands",
   }

On the changelist, related documents are fetched and their ``name`` field is
shown instead of the raw ObjectId.

Date and time display
---------------------

``date`` and ``datetime`` fields are auto-formatted on changelists and readonly
form fields. See :doc:`formatting` for defaults and customization.

Object representation
---------------------

``object_repr(request, obj)`` returns a human-readable label for an object. It is
used for:

* Save success messages (``"Widget Pro" was saved successfully.``)
* Bulk delete confirmation rows

Override to customize the label shown in flash messages.

Configurable methods
--------------------

Override these methods for dynamic behavior:

.. list-table::
   :header-rows: 1

   * - Method
     - Purpose
   * - ``get_list_display(request)``
     - Dynamic changelist columns
   * - ``get_list_display_links(request)``
     - Dynamic link columns
   * - ``get_search_fields()``
     - Dynamic search fields
   * - ``get_ordering()``
     - Dynamic default ordering
   * - ``get_readonly_fields(request, obj)``
     - Context-dependent readonly fields
   * - ``get_fieldsets(request, obj)``
     - Dynamic form layout
   * - ``get_list_filters(request, params)``
     - Custom filter instantiation
   * - ``get_actions()``
     - Control which bulk actions are available
   * - ``get_queryset(request, base_query)``
     - Add base MongoDB filter to all queries
   * - ``get_formfield_overrides(request, obj)``
     - Dynamic widget overrides
   * - ``formfield_for_field(field, request, obj)``
     - Per-field customization hook
   * - ``format_date_value(value)``
     - Custom date display formatting
   * - ``format_datetime_value(value)``
     - Custom datetime display formatting
   * - ``object_repr(request, obj)``
     - Human-readable label for flash messages
   * - ``display_value(request, obj, field_name)``
     - Resolve changelist cell values (includes date/datetime formatting)

See :doc:`hooks` for lifecycle hooks (``save_model``, ``delete_model``, etc.).
See :doc:`formatting` for date/time display and save notifications.

See :doc:`api-reference` for the full ``ModelAdmin`` API.
