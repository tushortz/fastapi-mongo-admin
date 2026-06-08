Migration from v0.x
===================

Version 2.0 is a major rewrite. This guide covers breaking changes when upgrading
from the legacy React-based admin (v0.x).

Summary of breaking changes
---------------------------

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Change
     - Migration path
   * - React UI removed
     - Admin is now Jinja2 + HTMX at ``/admin``
   * - ``/admin-ui`` mount removed
     - Use ``mount_admin_app()`` → ``/admin``
   * - ``MongoAdmin`` alias removed
     - Use ``AdminSite`` or ``site``
   * - Built-in demo token auth removed
     - Provide ``auth_dependency``
   * - Legacy document routes removed
     - ``/admin/collections/.../documents`` → standard CRUD URLs
   * - Configuration API changed
     - Use ``ModelAdmin`` class attributes and hooks

Step-by-step migration
----------------------

1. Update installation
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   pip install "fastapi-mongo-admin>=2.0.0"

2. Replace mount call
~~~~~~~~~~~~~~~~~~~~~

**Before (v0.x):**

.. code-block:: python

   from fastapi_mongo_admin import MongoAdmin

   admin = MongoAdmin(app, database)

**After (v2):**

.. code-block:: python

   from fastapi_mongo_admin import mount_admin_app, site

   mount_admin_app(app, get_database, admin_site=site, mode="async")

3. Define ModelAdmin classes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

v2 requires explicit ``ModelAdmin`` configuration for each model:

.. code-block:: python

   class ProductAdmin(ModelAdmin):
       model = Product
       collection_name = "products"
       list_display = ["name", "price"]

   site.register(Product, ProductAdmin)

4. Add authentication
~~~~~~~~~~~~~~~~~~~~~

v2 does not include built-in token auth:

.. code-block:: python

   mount_admin_app(app, get_database, auth_dependency=your_auth)

5. Update URL references
~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1

   * - v0.x
     - v2
   * - ``/admin-ui/``
     - ``/admin/``
   * - ``/admin/collections/{name}/documents``
     - ``/admin/{collection}/``
   * - Custom React components
     - Jinja2 template overrides

6. Remove React-specific code
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you customized the React SPA, migrate customizations to:

* ``ModelAdmin`` configuration (list display, filters, actions)
* Jinja2 template overrides
* Custom admin views via ``register_view()``

New features in v2
------------------

Features not available in v0.x:

* Django-style ``ModelAdmin`` with hooks and permissions
* List filters (choice, boolean, date, related, custom)
* Field mapping for legacy MongoDB schemas
* Fieldsets and formfield overrides
* Bulk actions with ``@action`` decorator
* ``list_select_related`` for reference display
* Date hierarchy navigation
* i18n (9 languages) and light/dark themes
* HTMX-powered changelist partial updates
* Sync PyMongo backend support
* CSRF protection with session middleware

Configuration mapping
---------------------

.. list-table::
   :header-rows: 1

   * - v0.x concept
     - v2 equivalent
   * - Collection config dict
     - ``ModelAdmin`` class
   * - Column definitions
     - ``list_display`` + ``@display``
   * - Custom formatters
     - ``@display`` methods
   * - Search config
     - ``search_fields``
   * - Auth middleware
     - ``auth_dependency`` on ``mount_admin_app()``

Need help?
----------

* Run the :doc:`ecommerce-demo` to see v2 patterns in action
* Open an issue on `GitHub <https://github.com/tushortz/fastapi-mongo-admin/issues>`_
