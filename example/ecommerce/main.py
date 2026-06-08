"""FastAPI ecommerce demo application."""

from __future__ import annotations

import os

from fastapi import Depends, FastAPI, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from example.ecommerce.admin import create_admin_site, register_admins
from example.ecommerce.auth import (
    TOKEN_COOKIE, get_current_user, require_staff,
)
from fastapi_mongo_admin import mount_admin_app

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("MONGODB_DB", "ecommerce_demo")


def create_app() -> FastAPI:
    """Build and configure the ecommerce demo FastAPI application."""
    app = FastAPI(
        title="Ecommerce Demo",
        description="Sample store backend with FastAPI Mongo Admin",
        version="1.0.0",
    )
    client = AsyncIOMotorClient(MONGODB_URL)
    database = client[DATABASE_NAME]

    admin_site = register_admins(create_admin_site())

    async def get_database() -> AsyncIOMotorDatabase:
        return database

    async def auth_with_staff(user: dict = Depends(get_current_user)) -> dict:
        return await require_staff(user)

    mount_admin_app(
        app,
        get_database,
        admin_site=admin_site,
        mode="async",
        auth_dependency=auth_with_staff,
        api_write_methods=True,
    )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "database": DATABASE_NAME}

    @app.get("/demo-login", response_class=HTMLResponse, include_in_schema=False)
    async def demo_login(
        token: str = Query(default="admin-token"),
        role: str = Query(default=""),
    ) -> RedirectResponse:
        """Set demo auth cookie and redirect to admin (development only)."""
        chosen = token or role
        if role and not token:
            chosen = f"{role}-token"
        response = RedirectResponse(url="/admin/", status_code=303)
        response.set_cookie(TOKEN_COOKIE, chosen, httponly=True, samesite="lax")
        return response

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    async def root() -> HTMLResponse:
        """Landing page with quick links."""
        return HTMLResponse(
            """
            <html><body style="font-family:sans-serif;max-width:640px;margin:40px auto">
            <h1>Ecommerce Demo</h1>
            <p>Sample store for testing <strong>fastapi-mongo-admin</strong>.</p>
            <ol>
              <li><a href="/demo-login?token=admin-token">Login as admin</a></li>
              <li><a href="/demo-login?token=manager-token">Login as manager</a></li>
              <li><a href="/demo-login?token=viewer-token">Login as viewer</a></li>
              <li><a href="/admin/">Open admin</a> (requires login)</li>
              <li><a href="/admin/dashboard/">Custom dashboard</a></li>
            </ol>
            </body></html>
            """
        )

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "example.ecommerce.main:app",
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "8000")),
        reload=True,
    )
