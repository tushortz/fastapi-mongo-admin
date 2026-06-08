Permissions
===========

FastAPI Mongo Admin provides Django-style permission hooks on ``ModelAdmin``.
Each hook returns a boolean indicating whether the current user may perform the
action.

Permission hooks
----------------

.. list-table::
   :header-rows: 1

   * - Method
     - Guards
   * - ``has_view_permission(request, user, obj=None)``
     - Changelist access
   * - ``has_add_permission(request, user)``
     - Add form
   * - ``has_change_permission(request, user, obj=None)``
     - Change form, bulk actions
   * - ``has_delete_permission(request, user, obj=None)``
     - Delete confirmation, bulk delete

Default behavior: all hooks return ``True``.

Basic example
-------------

.. code-block:: python

   class ProductAdmin(ModelAdmin):
       def has_add_permission(self, request, user=None) -> bool:
           return bool(user and user.get("is_staff"))

       def has_change_permission(self, request, user=None, obj=None) -> bool:
           return bool(user and user.get("role") in ("admin", "manager"))

       def has_delete_permission(self, request, user=None, obj=None) -> bool:
           return bool(user and user.get("role") == "admin")

Role-based access
-----------------

.. code-block:: python

   class ProductAdmin(ModelAdmin):
       def has_delete_permission(self, request, user=None, obj=None) -> bool:
           return bool(user and user.get("role") in ("admin", "manager"))

In the ecommerce demo, viewers can browse products but cannot delete them.

Object-level permissions
------------------------

Use the ``obj`` parameter for per-document rules:

.. code-block:: python

   def has_change_permission(self, request, user=None, obj=None) -> bool:
       if not user:
           return False
       if user.get("role") == "admin":
           return True
       if obj and obj.get("owner_id") == user.get("id"):
           return True
       return False

Bulk action permissions
-----------------------

Bulk actions (except ``delete_selected``) require ``has_change_permission``.

The built-in ``delete_selected`` action checks ``has_delete_permission`` before
deleting documents.

Action-level permissions
------------------------

The ``@action`` decorator accepts an optional ``permissions`` list for future
fine-grained control:

.. code-block:: python

   @action("Publish selected", permissions=["can_publish"])
   async def publish_products(self, request, queryset):
       pass

Permission denied responses
---------------------------

When a permission check fails, the admin raises ``PermissionDeniedError`` (HTTP
403). Unauthenticated users receive 401 from your ``auth_dependency``.

How checks are wired
--------------------

The router creates per-action dependencies via ``require_permission()``:

.. code-block:: text

   GET  /admin/{collection}/           → has_view_permission
   GET  /admin/{collection}/add/       → has_add_permission
   POST /admin/{collection}/add/       → has_add_permission
   GET  /admin/{collection}/{id}/change/ → has_change_permission
   POST /admin/{collection}/action/    → has_change_permission (bulk)
   GET  /admin/{collection}/{id}/delete/ → has_delete_permission

The authenticated ``user`` object from your ``auth_dependency`` is passed to
each hook.
