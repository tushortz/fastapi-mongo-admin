FastAPI Mongo Admin
===================

**FastAPI Mongo Admin** is a Django-inspired, server-rendered admin framework for
FastAPI and MongoDB. It provides a full ``ModelAdmin`` configuration API, pluggable
authentication, list filters, bulk actions, Pydantic-driven forms, and support
for both async (Motor) and sync (PyMongo) database backends.

.. image:: https://img.shields.io/badge/version-2.0.0-blue
   :alt: Version 2.0.0

Key capabilities
----------------

* **Django-like registry** — ``site.register(Model, AdminClass)``
* **Server-rendered UI** — Jinja2 + HTMX changelist, add/change forms, delete confirmation
* **List filters** — choice, boolean, date, related, and custom ``ListFilter`` classes
* **Pydantic forms** — validation and widget inference from your models
* **Field mapping** — translate between model field names and legacy MongoDB keys
* **Pluggable auth** — wire any FastAPI ``Depends`` authentication/authorization
* **Sync + async** — ``mode="async"`` (Motor) or ``mode="sync"`` (PyMongo)
* **Customization** — template overrides, hooks, custom admin views
* **JSON API** — ``/admin/api/{collection}/`` (read-only by default; optional ``api_write_methods`` for CRUD + Swagger)
* **i18n + themes** — 9 languages, light/dark mode with cookie persistence
* **Date/time display** — formatted changelist and readonly values (default ``8 Apr 2026, 7:32pm``)
* **Save notifications** — changelist success banner after add/change using the saved item label
* **Nested models** — nested Pydantic models via JSON editor with validation

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   installation
   quickstart
   architecture

.. toctree::
   :maxdepth: 2
   :caption: Core Concepts

   admin-site
   model-admin
   authentication
   permissions

.. toctree::
   :maxdepth: 2
   :caption: Changelist & Forms

   list-filters
   forms-and-fields
   formatting
   field-mapping
   actions

.. toctree::
   :maxdepth: 2
   :caption: Customization

   templates
   custom-views
   hooks
   i18n-theme

.. toctree::
   :maxdepth: 2
   :caption: Reference

   database-backends
   json-api
   urls
   api-reference
   ecommerce-demo
   migration

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
