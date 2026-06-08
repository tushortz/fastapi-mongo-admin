Template Customization
======================

The admin UI is rendered with Jinja2 templates. You can override any template
by providing files in a custom directory registered on ``AdminSite``.

Template search order
---------------------

1. Paths in ``AdminSite(template_dirs=[...])``
2. Bundled package templates in ``fastapi_mongo_admin/templates/``

Your templates take precedence when filenames match.

Site-wide template directory
----------------------------

.. code-block:: python

   from pathlib import Path
   from fastapi_mongo_admin import AdminSite

   site = AdminSite(template_dirs=[Path("myapp/templates")])

Place overrides at the same relative paths as the bundled templates:

.. code-block:: text

   myapp/templates/
   └── admin/
       ├── index.html
       ├── change_list.html
       ├── change_form.html
       ├── delete_confirmation.html
       └── partials/
           └── result_list.html

Per-model template overrides
----------------------------

.. code-block:: python

   class ProductAdmin(ModelAdmin):
       change_list_template = "admin/product_change_list.html"
       change_form_template = "admin/product_change_form.html"
       delete_confirmation_template = "admin/product_delete.html"

Bundled templates
-----------------

.. list-table::
   :header-rows: 1

   * - Template
     - Purpose
   * - ``admin/index.html``
     - Admin home page (model list)
   * - ``admin/change_list.html``
     - Changelist with filters, search, pagination
   * - ``admin/change_form.html``
     - Add and change forms
   * - ``admin/delete_confirmation.html``
     - Delete confirmation page
   * - ``admin/partials/result_list.html``
     - HTMX partial for changelist table

Starting from bundled templates
-------------------------------

Copy a template from the package as a starting point:

.. code-block:: bash

   cp fastapi_mongo_admin/templates/admin/change_list.html \
      myapp/templates/admin/change_list.html

Template context variables
--------------------------

Index (``admin/index.html``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1

   * - Variable
     - Description
   * - ``site_header``, ``site_title``, ``index_title``
     - Branding from ``AdminSite``
   * - ``models``
     - List of ``{collection, name, url}``
   * - ``prefix``
     - Admin URL prefix (e.g. ``/admin``)
   * - ``lang``, ``theme``, ``is_rtl``, ``t``, ``languages``
     - i18n and theme context

Changelist (``admin/change_list.html``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1

   * - Variable
     - Description
   * - ``model_name``, ``collection``, ``prefix``
     - Model identification
   * - ``columns``
     - ``{name, label, link}`` for each column
   * - ``rows``
     - ``{id, cells: [{name, value}]}}`` for each document
   * - ``filters``
     - Sidebar filter definitions with choices
   * - ``search``, ``page``, ``num_pages``, ``total``, ``per_page``
     - Pagination and search state
   * - ``actions``
     - Bulk action dropdown options
   * - ``has_add_permission``
     - Whether to show "Add" button
   * - ``csrf_token``
     - CSRF token for forms
   * - ``query_string``
     - Current filter/search query string

Change form (``admin/change_form.html``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1

   * - Variable
     - Description
   * - ``fieldsets``
     - ``{title, fields: [AdminField]}`` groups
   * - ``is_new``
     - True on add form
   * - ``obj``, ``obj_id``
     - Existing document and ID (change form)
   * - ``errors``
     - Validation error messages
   * - ``has_change_permission``, ``has_delete_permission``
     - Permission flags

Translation helper
~~~~~~~~~~~~~~~~~~

Use ``{{ t('key') }}`` or ``{{ t('key', count=5) }}`` for translated strings.

Static assets
-------------

CSS and JavaScript are served from ``/admin/static/``. Reference in templates:

.. code-block:: html

   <link rel="stylesheet" href="{{ static_url }}/admin.css">

The ``static_url`` variable is injected automatically (e.g. ``/admin/static``).

HTMX partials
-------------

When customizing the changelist, preserve the partial template at
``admin/partials/result_list.html`` for HTMX pagination to work. The partial
should contain only the table and pagination elements.

Ecommerce example
-----------------

The demo registers ``example/templates/`` on ``EcommerceAdminSite``. See
:doc:`ecommerce-demo`.
