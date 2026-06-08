Authentication
==============

FastAPI Mongo Admin does not ship with built-in authentication. You provide any
FastAPI-compatible dependency via ``auth_dependency`` when mounting the admin.

Basic setup
-----------

.. code-block:: python

   from fastapi import Depends, HTTPException, status
   from fastapi_mongo_admin import mount_admin_app


   async def get_admin_user():
       # Validate JWT, session cookie, API key, etc.
       user = await validate_token(...)
       if not user:
           raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
       return user


   mount_admin_app(
       app,
       get_database,
       admin_site=site,
       auth_dependency=get_admin_user,
   )

The dependency is injected on every admin route. Return any object (typically a
``dict``) representing the authenticated user.

Global permission gate
----------------------

Add a second dependency for site-wide authorization (e.g. staff-only access):

.. code-block:: python

   async def require_staff(user: dict = Depends(get_admin_user)) -> dict:
       if not user.get("is_staff"):
           raise HTTPException(status_code=403, detail="Staff access required")
       return user


   mount_admin_app(
       app,
       get_database,
       auth_dependency=require_staff,
   )

Or use ``permission_dependency`` for a separate gate that runs on the index page:

.. code-block:: python

   mount_admin_app(
       app,
       get_database,
       auth_dependency=get_admin_user,
       permission_dependency=require_staff,
   )

Bearer token example
--------------------

.. code-block:: python

   from fastapi import Header, HTTPException


   async def get_current_user(
       authorization: str | None = Header(default=None),
   ) -> dict:
       if not authorization or not authorization.startswith("Bearer "):
           raise HTTPException(status_code=401, detail="Not authenticated")
       token = authorization.removeprefix("Bearer ").strip()
       user = await lookup_user_by_token(token)
       if not user:
           raise HTTPException(status_code=401, detail="Invalid token")
       return user

Cookie-based example
--------------------

.. code-block:: python

   from fastapi import Cookie, HTTPException


   async def get_current_user(
       session_id: str | None = Cookie(default=None, alias="session_id"),
   ) -> dict:
       if not session_id:
           raise HTTPException(status_code=401)
       return await get_session_user(session_id)

No authentication (development only)
------------------------------------

Omit ``auth_dependency`` to allow unauthenticated access:

.. code-block:: python

   mount_admin_app(app, get_database, admin_site=site)

**Never use this in production.**

Ecommerce demo auth
-------------------

The repository includes a demo auth module at ``example/ecommerce/auth.py``:

* Tokens: ``admin-token``, ``manager-token``, ``viewer-token``
* Accepts ``Authorization: Bearer <token>`` or ``admin_token`` cookie
* Login shortcut: ``/demo-login?token=admin-token``

See :doc:`ecommerce-demo` for details.

JSON API authentication
-----------------------

The JSON API at ``/admin/api/`` uses the same ``auth_dependency``. Authenticate
API requests the same way as browser requests:

.. code-block:: bash

   curl -H "Authorization: Bearer admin-token" \
        http://localhost:8000/admin/api/products/

Per-model permissions
---------------------

Authentication identifies **who** the user is. Per-model permission hooks
control **what** they can do. See :doc:`permissions`.

CSRF protection
---------------

When ``SessionMiddleware`` is enabled, forms include a CSRF token. The admin
verifies ``csrfmiddlewaretoken`` on all mutating POST requests. Without session
middleware, CSRF verification is skipped.

.. code-block:: python

   from starlette.middleware.sessions import SessionMiddleware

   app.add_middleware(SessionMiddleware, secret_key="change-me-in-production")
