Forms and Fields
================

Change forms are generated automatically from your Pydantic model. The admin
infers field types, widgets, and validation rules without manual form classes.

Widget inference
----------------

Pydantic field annotations map to HTML widgets:

.. list-table::
   :header-rows: 1

   * - Python type
     - Widget
   * - ``str``
     - Text input
   * - ``int``, ``float``, ``Decimal``
     - Number input (with appropriate ``step``)
   * - ``bool``
     - Checkbox
   * - ``date``
     - Date picker
   * - ``datetime``
     - Datetime-local picker
   * - ``list``, ``dict``
     - JSON editor (textarea)
   * - Nested ``BaseModel``
     - JSON editor (textarea)
   * - ``ObjectId``
     - ObjectId text input
   * - Field with ``choices``
     - Select dropdown

Enum fields and fields with ``choices`` configured on ``ModelAdmin`` render as
select dropdowns.

Formfield overrides
-------------------

Override widgets and HTML attributes per field:

.. code-block:: python

   class ProductAdmin(ModelAdmin):
       formfield_overrides = {
           "description": {"widget": "textarea", "rows": 8},
           "valid_from": {"min": "2020-01-01"},
           "valid_until": {"max": "2099-12-31"},
       }

Available widget constants (from ``FieldWidget``):

.. code-block:: python

   from fastapi_mongo_admin.admin.fields.widgets import (
       TEXT, TEXTAREA, NUMBER, CHECKBOX, SELECT,
       DATE, DATETIME, EMAIL, JSON_EDITOR, OBJECT_ID, HIDDEN,
   )

Shorthand dict syntax
~~~~~~~~~~~~~~~~~~~~~

The ``widget`` key sets the widget type; remaining keys become HTML attributes:

.. code-block:: python

   formfield_overrides = {
       "notes": {"widget": "textarea", "rows": 5, "placeholder": "Internal notes"},
   }

FieldWidget dataclass
~~~~~~~~~~~~~~~~~~~~~

For explicit configuration:

.. code-block:: python

   from fastapi_mongo_admin import FieldWidget

   formfield_overrides = {
       "description": FieldWidget(widget="textarea", attrs={"rows": 10}),
   }

Per-field hook
--------------

Customize individual fields after defaults and overrides are applied:

.. code-block:: python

   def formfield_for_field(self, field, request=None, obj=None):
       if field.name == "slug" and obj is None:
           field.attrs["placeholder"] = "auto-generated-from-name"
       return field

Fieldsets
---------

Organize fields into labeled groups on the change form:

.. code-block:: python

   fieldsets = [
       (None, {"fields": ["name", "slug"]}),
       ("Pricing", {"fields": ["price", "compare_at_price"]}),
       ("SEO", {"fields": ["meta_title", "meta_description"], "classes": ["collapse"]}),
   ]

Readonly fields
---------------

Fields listed in ``readonly_fields`` are displayed but not editable:

.. code-block:: python

   readonly_fields = ["created_at", "updated_at", "order_number"]

On update, readonly values not present in the POST body are preserved from the
existing document.

Form validation
---------------

Submitted form data passes through Pydantic validation via
``parse_form_to_model()``:

* Missing optional fields are omitted
* Missing boolean fields default to ``False``
* JSON strings in list/dict/nested-model fields are parsed with ``json.loads``
* Empty ``{}`` / ``[]`` for optional nested fields is treated as ``None``
* Validation errors render on the form with HTTP 422

Complex field types
-------------------

Nested Pydantic models
~~~~~~~~~~~~~~~~~~~~~~

Fields typed as a nested ``BaseModel`` (e.g. ``CustomerAddress`` inside
``Customer``) render as a JSON editor. Submit valid JSON:

.. code-block:: json

   {
     "line1": "1 Main St",
     "city": "Boston",
     "postal_code": "02101",
     "country": "US"
   }

Leave optional nested fields empty (``{}``) to store ``None``.

Nested objects (``dict``)
~~~~~~~~~~~~~~~~~~~~~~~~~

Rendered as JSON editor. Users edit raw JSON in a textarea.

Lists
~~~~~

Also rendered as JSON editor. Useful for ``line_items``, ``tags``, etc.

Decimals
~~~~~~~~

Stored as ``Decimal128`` in MongoDB. Displayed and edited as strings to preserve
precision.

Dates and datetimes
~~~~~~~~~~~~~~~~~~~

**Form inputs** use ISO format strings (``YYYY-MM-DD`` / ``YYYY-MM-DDTHH:MM``).
Date-only values are converted to datetime at midnight UTC before MongoDB
insertion.

**Display** on changelists and readonly fields uses human-readable formatting.
See :doc:`formatting` (default: ``8 Apr 2026, 7:32pm`` for datetimes).

Booleans
~~~~~~~~

Checkboxes. Unchecked boxes submit as ``False`` (not omitted).

Choices in forms
----------------

Configure ``choices`` on ``ModelAdmin`` to populate select widgets:

.. code-block:: python

   choices = {
       "currency": [("USD", "USD"), ("EUR", "EUR"), ("GBP", "GBP")],
   }

See :doc:`api-reference` for ``prepare_form_fields`` and ``FieldWidget``.
