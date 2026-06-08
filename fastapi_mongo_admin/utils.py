"""Mount helpers for FastAPI applications."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any, Literal, Union

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.database import Database

from fastapi_mongo_admin.admin.site import AdminSite, site as default_site
from fastapi_mongo_admin.views.router import create_admin_router


def get_static_directory() -> Path:
    """Return the packaged static assets directory.

    Returns:
        Path to the ``fastapi_mongo_admin/static`` package directory.
    """
    return Path(__file__).parent / "static"


def mount_admin_app(
    app: FastAPI,
    get_database: Callable[
        ..., Union[AsyncIOMotorDatabase, Database, Awaitable[AsyncIOMotorDatabase]]
    ],
    *,
    admin_site: AdminSite | None = None,
    router_prefix: str = "/admin",
    mode: Literal["async", "sync"] = "async",
    auth_dependency: Callable[..., Any] | None = None,
    permission_dependency: Callable[..., Any] | None = None,
    api_write_methods: bool = False,
) -> None:
    """Mount the admin UI, JSON API, and static files on a FastAPI application.

    Args:
        app: FastAPI application to extend.
        get_database: Callable returning a Motor database, PyMongo database, or
            awaitable that resolves to one.
        admin_site: Admin site registry. Defaults to the global ``site`` singleton.
        router_prefix: URL prefix for admin routes (default ``/admin``).
        mode: MongoDB access mode — ``async`` (Motor) or ``sync`` (PyMongo).
        auth_dependency: Optional FastAPI dependency injected on admin routes.
        permission_dependency: Optional dependency checked before the admin index.
        api_write_methods: When ``True``, register ``POST``, ``PUT``, ``PATCH``, and
            ``DELETE`` JSON API routes and include them in OpenAPI (``/docs``).
            When ``False`` (default), only ``GET`` list/detail routes are registered
            and documented.

    Returns:
        None. Mutates ``app`` by including the admin router and static mount.
    """
    admin_site = admin_site or default_site
    static_mount = f"{router_prefix}/static"
    router = create_admin_router(
        admin_site,
        get_database,
        prefix=router_prefix,
        mode=mode,
        auth_dependency=auth_dependency,
        permission_dependency=permission_dependency,
        static_url=static_mount,
        api_write_methods=api_write_methods,
    )
    app.include_router(router)
    static_dir = get_static_directory() / "admin"
    if static_dir.exists():
        app.mount(static_mount, StaticFiles(directory=str(static_dir)), name="admin-static")
