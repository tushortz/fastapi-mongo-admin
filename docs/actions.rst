Actions
=======

Bulk actions let administrators operate on multiple selected documents from the
changelist. Actions are methods on ``ModelAdmin`` decorated with ``@action``.

Defining actions
----------------

.. code-block:: python

   from fastapi import Request
   from fastapi_mongo_admin import action


   class ProductAdmin(ModelAdmin):
       actions = ["delete_selected", "publish_products", "archive_products"]

       @action("Publish selected products")
       async def publish_products(
           self, request: Request, queryset: list[dict]
       ) -> None:
           for doc in queryset:
               # Update doc in your service layer
               pass

       @action("Archive selected products")
       async def archive_products(
           self, request: Request, queryset: list[dict]
       ) -> None:
           pass

The ``@action`` decorator
-------------------------

.. code-block:: python

   @action(description: str, permissions: list[str] | None = None)

* ``description`` — label shown in the action dropdown
* ``permissions`` — optional permission names (reserved for future use)

Actions can be sync or async. The router awaits async methods automatically.

Built-in delete action
----------------------

``delete_selected`` is provided by default:

.. code-block:: python

   DELETE_SELECTED_ACTION = "delete_selected"

Behavior:

1. Checks ``has_delete_permission`` for the current user
2. Calls ``delete_model()`` hook on each selected document
3. Executes ``repo.delete_many()`` for the selected IDs

Control which actions appear
----------------------------

Explicit list
~~~~~~~~~~~~~

.. code-block:: python

   actions = ["delete_selected", "publish_products"]

Only listed actions (plus resolved custom actions) appear in the dropdown.

Disable all actions
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   actions = []

Default (``actions = None``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Includes ``delete_selected`` plus all ``@action``-decorated methods.

How bulk actions work
---------------------

1. User selects rows via checkboxes on the changelist
2. Chooses an action from the dropdown and clicks "Go"
3. ``POST /admin/{collection}/action/`` with:
   - ``action`` — action name
   - ``_selected_action`` — list of document IDs
   - ``csrfmiddlewaretoken`` — CSRF token (when sessions enabled)
4. Router fetches each document, invokes the action method
5. Redirects back to the changelist

The ``queryset`` parameter
--------------------------

Each action receives the list of selected documents as Python dicts (already
serialized and field-mapped). Use document IDs for repository operations:

.. code-block:: python

   @action("Approve selected reviews")
   async def approve_reviews(self, request, queryset: list[dict]) -> None:
       db = ...  # obtain from your app context
       ids = [doc["id"] for doc in queryset]
       await db.reviews.update_many(
           {"_id": {"$in": ids}},
           {"$set": {"is_approved": True}},
       )

For production apps, inject your repository or service layer rather than
accessing the database directly in the action.

See :doc:`api-reference` for action decorator and helper APIs.
