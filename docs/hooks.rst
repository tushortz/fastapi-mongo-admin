Lifecycle Hooks
===============

``ModelAdmin`` provides hooks to customize data access and persistence without
overriding the router.

Query hooks
-----------

get_queryset
~~~~~~~~~~~~

Add a base filter applied to all changelist queries:

.. code-block:: python

   def get_queryset(self, request, base_query: dict) -> dict:
       # Only show non-archived products by default
       return {**base_query, "status": {"$ne": "archived"}}

Called before search, filters, and date hierarchy are applied.

Persistence hooks
-----------------

save_model
~~~~~~~~~~

Mutate validated form data before insert or update:

.. code-block:: python

   from datetime import datetime, timezone


   async def save_model(
       self,
       request,
       obj: dict,
       form_data: dict,
       is_new: bool,
   ) -> dict:
       now = datetime.now(timezone.utc).isoformat()
       form_data["updated_at"] = now
       if is_new:
           form_data.setdefault("created_at", now)
       return form_data

Parameters:

* ``request`` — FastAPI request (or ``None``)
* ``obj`` — existing document (empty dict on create)
* ``form_data`` — Pydantic-validated data
* ``is_new`` — ``True`` on add, ``False`` on change

Return the (possibly modified) dict to persist.

delete_model
~~~~~~~~~~~~

Called before each document is deleted (single or bulk):

.. code-block:: python

   async def delete_model(self, request, obj: dict) -> None:
       # Cascade delete related records, audit log, etc.
       await cleanup_related(obj["id"])

Not called if permission check fails.

Display hooks
-------------

display_value
~~~~~~~~~~~~~

Override how changelist cell values are resolved:

.. code-block:: python

   def display_value(self, request, obj: dict, field_name: str):
       value = super().display_value(request, obj, field_name)
       if field_name == "status":
           return value.upper()
       return value

By default, checks for ``@display`` methods, then raw document fields.

Form hooks
----------

formfield_for_field
~~~~~~~~~~~~~~~~~~~

Customize a single form field after defaults and overrides:

.. code-block:: python

   def formfield_for_field(self, field, request=None, obj=None):
       if field.name == "slug" and obj is None:
           field.attrs["readonly"] = True
       return field

get_readonly_fields
~~~~~~~~~~~~~~~~~~~

Dynamic readonly fields based on context:

.. code-block:: python

   def get_readonly_fields(self, request, obj=None):
       readonly = list(self.readonly_fields or [])
       if obj and obj.get("status") == "published":
           readonly.append("price")
       return readonly

get_fieldsets
~~~~~~~~~~~~~

Dynamic form layout:

.. code-block:: python

   def get_fieldsets(self, request, obj=None):
       fieldsets = super().get_fieldsets(request, obj)
       if obj and obj.get("role") != "admin":
           # Hide advanced section for non-admins
           return [fs for fs in fieldsets if fs[0] != "Advanced"]
       return fieldsets

Permission hooks
----------------

See :doc:`permissions` for ``has_view_permission``, ``has_add_permission``,
``has_change_permission``, and ``has_delete_permission``.

Hook execution order
--------------------

**Create flow:**

.. code-block:: text

   POST form → parse_form_to_model() → save_model() → translate_to_db()
             → prepare_for_mongodb() → backend.insert_one()

**Update flow:**

.. code-block:: text

   POST form → parse_form_to_model() → save_model() → translate_to_db()
             → prepare_for_mongodb() → backend.update_one()

**Delete flow:**

.. code-block:: text

   delete_model() → backend.delete_one()  (or delete_many for bulk)

**Changelist flow:**

.. code-block:: text

   get_queryset() → build_changelist_query() → backend.find()
                 → serialize → display_value() per cell
