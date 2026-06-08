Architecture
============

FastAPI Mongo Admin follows a layered architecture inspired by Django's admin,
adapted for MongoDB document stores.

High-level overview
-------------------

.. code-block:: text

   FastAPI App
       │
       ├── mount_admin_app()
       │       │
       │       ├── create_admin_router()     ← routes, Jinja2, HTMX
       │       │       ├── AdminSite         ← model registry
       │       │       ├── ModelAdmin        ← per-model config + hooks
       │       │       └── CollectionRepository
       │       │               ├── AsyncMotorBackend  (mode="async")
       │       │               └── SyncPyMongoBackend (mode="sync")
       │       │
       │       └── StaticFiles (/admin/static/)
       │
       └── Your application routes

Core components
---------------

AdminSite
   Central registry. Maps ``collection_name`` → ``ModelAdmin`` instance.
   Supports custom views, template directories, and site branding.

ModelAdmin
   Per-model configuration: list display, filters, fieldsets, permissions,
   hooks, and bulk actions. Subclass and override methods for customization.

CollectionRepository
   CRUD operations with field mapping translation, Pydantic validation,
   ``list_select_related`` lookups, and changelist query building.

List filters
   Sidebar filters on the changelist. Resolved from field names or custom
   ``ListFilter`` subclasses. Combined into a MongoDB query fragment.

Schema inference
   Pydantic model fields are inspected to infer form widgets (text, number,
   checkbox, JSON editor, date, etc.) and validate submitted form data.

Request flow: changelist
------------------------

1. User visits ``GET /admin/{collection}/``
2. Router resolves ``ModelAdmin`` from ``AdminSite`` registry
3. ``CollectionRepository.list_documents()`` builds query from:
   - ``get_queryset()`` hook (base filter)
   - Search fields (``$or`` regex on configured fields)
   - Active list filters (sidebar)
   - Date hierarchy params (``year``, ``month``, ``day``)
4. Results are serialized (BSON → JSON-safe), related docs resolved
5. ``build_changelist_context()`` prepares Jinja2 context
6. Template renders (full page or HTMX partial for pagination)

Request flow: add/change form
-----------------------------

1. ``GET`` renders form with fieldsets from ``get_fieldsets()``
2. ``POST`` parses multipart form data
3. CSRF token verified (when session middleware is enabled)
4. ``parse_form_to_model()`` validates through Pydantic
5. ``save_model()`` hook mutates data before persistence
6. ``translate_to_db()`` applies field mapping
7. ``prepare_for_mongodb()`` converts Decimals, dates, etc.
8. Backend inserts or updates the document

HTMX integration
----------------

The changelist uses HTMX for partial page updates. When an HTMX request is
detected (``HX-Request`` header), only the result table partial is returned
instead of the full page. This enables fast pagination and filtering without
full page reloads.

Template resolution
-------------------

Jinja2 searches template directories in this order:

1. Directories passed to ``AdminSite(template_dirs=[...])``
2. Bundled package templates in ``fastapi_mongo_admin/templates/``

Per-model template overrides (``change_list_template``, etc.) reference paths
relative to these search directories.
