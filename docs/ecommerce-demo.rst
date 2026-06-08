Ecommerce Demo
==============

The repository includes a full-featured ecommerce demo that exercises every
major admin capability. Use it to explore features, test customizations, and
as a reference implementation.

Quick start
-----------

.. code-block:: bash

   # From repository root
   docker compose -f example/docker-compose.yml up -d
   uv sync --group dev
   uv run python -m example.ecommerce.seed
   uv run python -m example.ecommerce.main

Open in browser:

.. list-table::
   :header-rows: 1

   * - URL
     - Description
   * - http://localhost:8000/
     - Landing page
   * - http://localhost:8000/demo-login?token=admin-token
     - Login as admin
   * - http://localhost:8000/admin/
     - Admin index
   * - http://localhost:8000/admin/products/
     - Product changelist
   * - http://localhost:8000/admin/dashboard/
     - Custom dashboard view

Project structure
-----------------

.. code-block:: text

   example/
   ├── docker-compose.yml
   ├── templates/admin/          # Template overrides
   └── ecommerce/
       ├── main.py                 # FastAPI app
       ├── models.py               # 7 Pydantic models
       ├── admin.py                # ModelAdmin classes
       ├── auth.py                 # Demo authentication
       └── seed.py                 # Sample data

Registered collections
----------------------

.. list-table::
   :header-rows: 1

   * - Collection
     - Model
     - Highlights
   * - ``categories``
     - Category
     - Fieldsets, boolean filter
   * - ``brands``
     - Brand
     - Search, ordering
   * - ``products``
     - Product
     - Richest model: fieldsets, field mapping, bulk actions, date hierarchy
   * - ``customers``
     - Customer
     - ``@display`` full name, loyalty tier choices
   * - ``orders``
     - Order
     - Nested line items, date hierarchy, select related
   * - ``reviews``
     - Review
     - Approve bulk action, rating filter
   * - ``coupons``
     - Coupon
     - Formfield overrides, enum choices

Features demonstrated
---------------------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Feature
     - Location
   * - Fieldsets
     - Product, Customer, Order change forms
   * - ``@display`` columns
     - Product price, Customer full name
   * - List filters
     - Status, loyalty tier, payment status
   * - Date hierarchy
     - Product ``published_at``, Order ``placed_at``
   * - ``list_select_related``
     - Product → category/brand; Order → customer
   * - Field mapping
     - ``sku`` ↔ ``product_sku``, ``cost_price`` ↔ ``unit_cost``
   * - Bulk actions
     - Publish/archive/feature products; approve reviews
   * - ``save_model`` hook
     - Auto-sets ``updated_at`` on products
   * - ``has_delete_permission``
     - Only admin/manager can delete products
   * - Custom admin view
     - ``/admin/dashboard/``
   * - Template overrides
     - ``EcommerceAdminSite(template_dirs=[...])``
   * - i18n + theme
     - Header language selector and theme toggle

Authentication
--------------

Demo tokens (development only):

.. list-table::
   :header-rows: 1

   * - Token
     - Role
     - Can delete products?
   * - ``admin-token``
     - admin
     - Yes
   * - ``manager-token``
     - manager
     - Yes
   * - ``viewer-token``
     - viewer
     - No

Login sets an ``admin_token`` cookie via ``/demo-login?token=admin-token``.

API access:

.. code-block:: bash

   curl -H "Authorization: Bearer admin-token" \
        http://localhost:8000/admin/api/products/

Seeding
-------

.. code-block:: bash

   uv run python -m example.ecommerce.seed

Environment variables:

.. list-table::
   :header-rows: 1

   * - Variable
     - Default
   * - ``MONGODB_URL``
     - ``mongodb://localhost:27017``
   * - ``MONGODB_DB``
     - ``ecommerce_demo``

Seeded data: 3 categories, 3 brands, 6 products, 3 customers, 3 orders, 2
reviews, 2 coupons.

Environment variables (app)
---------------------------

.. list-table::
   :header-rows: 1

   * - Variable
     - Default
     - Description
   * - ``MONGODB_URL``
     - ``mongodb://localhost:27017``
     - Connection string
   * - ``MONGODB_DB``
     - ``ecommerce_demo``
     - Database name
   * - ``HOST``
     - ``127.0.0.1``
     - Uvicorn bind host
   * - ``PORT``
     - ``8000``
     - Uvicorn port

Customization recipes
---------------------

The demo source code in ``example/ecommerce/admin.py`` is the best reference
for real-world patterns. Key files:

* ``admin.py`` — all ``ModelAdmin`` configurations
* ``models.py`` — rich Pydantic models with enums, nested objects, decimals
* ``auth.py`` — replace with your production auth
* ``main.py`` — ``mount_admin_app()`` wiring

See also ``example/README.md`` in the repository for troubleshooting.
