Installation
============

Requirements
------------

* Python 3.10 or newer
* MongoDB 5.0+ (local, Docker, or Atlas)
* FastAPI application

Install the package
-------------------

Using **uv** (recommended):

.. code-block:: bash

   uv add fastapi-mongo-admin

Using **pip**:

.. code-block:: bash

   pip install fastapi-mongo-admin

Development install
-------------------

Clone the repository and install with dev dependencies:

.. code-block:: bash

   git clone https://github.com/tushortz/fastapi-mongo-admin.git
   cd fastapi-mongo-admin
   uv sync --group dev

Core dependencies (installed automatically):

.. list-table::
   :header-rows: 1

   * - Package
     - Purpose
   * - ``fastapi``
     - Web framework and routing
   * - ``motor``
     - Async MongoDB driver
   * - ``pymongo``
     - Sync MongoDB driver
   * - ``pydantic``
     - Model validation and schema inference
   * - ``jinja2``
     - Server-rendered admin templates
   * - ``python-multipart``
     - Form data parsing

Optional: MongoDB via Docker
----------------------------

For local development, start MongoDB with the included compose file:

.. code-block:: bash

   docker compose -f example/docker-compose.yml up -d

Verify the connection:

.. code-block:: bash

   mongosh mongodb://localhost:27017

Next steps
----------

Continue to :doc:`quickstart` to mount the admin in your FastAPI application.
