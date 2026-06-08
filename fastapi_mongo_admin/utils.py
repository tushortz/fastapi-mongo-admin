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
    """Return packaged static files directory."""
    return Path(__file__).parent / "static"


def mount_admin_app(
    app: FastAPI,
    get_database: Callable[..., Union[AsyncIOMotorDatabase, Database, Awaitable[AsyncIOMotorDatabase]]],
    *,
    admin_site: AdminSite | None = None,
    router_prefix: str = "/admin",
    mode: Literal["async", "sync"] = "async",
    auth_dependency: Callable[..., Any] | None = None,
    permission_dependency: Callable[..., Any] | None = None,
    api_write_methods: bool = False,
) -> None:
    """Mount Django-style admin UI and JSON API on a FastAPI app."""
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
