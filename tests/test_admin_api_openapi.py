"""OpenAPI schema tests for admin JSON API."""

from __future__ import annotations

import mongomock
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel

from fastapi_mongo_admin import AdminSite, ModelAdmin, mount_admin_app


class Item(BaseModel):
    name: str
    price: float


class ItemAdmin(ModelAdmin):
    model = Item
    collection_name = "items"
    list_display = ["name", "price"]


def _build_app(*, api_write_methods: bool = False) -> FastAPI:
    client = mongomock.MongoClient()
    db = client["test_db"]
    site = AdminSite()
    site.register(Item, ItemAdmin)
    app = FastAPI()
    mount_admin_app(
        app,
        lambda: db,
        admin_site=site,
        mode="sync",
        api_write_methods=api_write_methods,
    )
    return app


def _admin_api_methods(openapi: dict) -> dict[str, set[str]]:
    methods_by_path: dict[str, set[str]] = {}
    for path, operations in openapi["paths"].items():
        if not path.startswith("/admin/api/"):
            continue
        methods_by_path[path] = {method.upper() for method in operations if method != "parameters"}
    return methods_by_path


def test_openapi_lists_only_get_by_default() -> None:
    app = _build_app()
    methods_by_path = _admin_api_methods(app.openapi())

    assert methods_by_path
    for methods in methods_by_path.values():
        assert methods == {"GET"}


def test_openapi_includes_write_methods_when_enabled() -> None:
    app = _build_app(api_write_methods=True)
    methods_by_path = _admin_api_methods(app.openapi())

    assert methods_by_path["/admin/api/items/"] == {"GET", "POST"}
    assert methods_by_path["/admin/api/items/{doc_id}"] == {"GET", "PUT", "PATCH", "DELETE"}


@pytest.mark.asyncio
async def test_write_api_routes_registered_only_when_enabled() -> None:
    read_only_app = _build_app()
    write_app = _build_app(api_write_methods=True)

    read_only_paths = read_only_app.openapi()["paths"]
    write_paths = write_app.openapi()["paths"]

    assert "post" not in read_only_paths["/admin/api/items/"]
    assert "post" in write_paths["/admin/api/items/"]
    assert "delete" not in read_only_paths["/admin/api/items/{doc_id}"]
    assert "delete" in write_paths["/admin/api/items/{doc_id}"]


@pytest.mark.asyncio
async def test_write_api_create_and_delete() -> None:
    app = _build_app(api_write_methods=True)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_response = await client.post(
            "/admin/api/items/",
            json={"name": "Widget", "price": 9.99},
        )
        assert create_response.status_code == 201
        doc_id = create_response.json()["id"]

        delete_response = await client.delete(f"/admin/api/items/{doc_id}")
        assert delete_response.status_code == 204

        missing_response = await client.get(f"/admin/api/items/{doc_id}")
        assert missing_response.status_code == 404
