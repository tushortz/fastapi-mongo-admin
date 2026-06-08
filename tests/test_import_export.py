"""Import and export data transfer tests."""

import json

import pytest
from httpx import AsyncClient

from fastapi_mongo_admin.services.import_export import (
    export_documents,
    normalize_format,
    parse_import_payload,
    sanitize_import_record,
)
from tests.conftest import Product, ProductAdmin


def test_export_documents_json() -> None:
    payload = export_documents([{"id": "1", "name": "Phone"}], "json")
    data = json.loads(payload.decode("utf-8"))
    assert data == [{"id": "1", "name": "Phone"}]


def test_export_documents_csv() -> None:
    payload = export_documents([{"name": "Phone", "price": 9.99}], "csv")
    text = payload.decode("utf-8")
    assert "name,price" in text
    assert "Phone" in text


def test_parse_import_payload_requires_array() -> None:
    with pytest.raises(Exception):
        parse_import_payload(b'{"name": "Phone"}', "json")


def test_sanitize_import_record_removes_ids() -> None:
    cleaned = sanitize_import_record({"_id": "abc", "id": "abc", "name": "Phone"})
    assert cleaned == {"name": "Phone"}


def test_normalize_format_aliases() -> None:
    assert normalize_format("yml") == "yaml"
    assert normalize_format("xlsx") == "excel"


@pytest.mark.asyncio
async def test_changelist_shows_data_transfer_fab(client: AsyncClient) -> None:
    response = await client.get("/admin/products/")
    assert response.status_code == 200
    assert 'id="data-transfer-toggle"' in response.text
    assert "Import / Export" in response.text
    assert 'value="export_selected"' not in response.text


@pytest.mark.asyncio
async def test_export_selected_downloads_json(client: AsyncClient, mock_db) -> None:
    doc = mock_db["test_db"].products.find_one({"name": "Python Guide"})
    doc_id = str(doc["_id"])

    response = await client.post(
        "/admin/products/export/",
        data={
            "format": "json",
            "scope": "selected",
            "_selected_action": doc_id,
        },
        follow_redirects=False,
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert "attachment" in response.headers.get("content-disposition", "")
    data = json.loads(response.content.decode("utf-8"))
    assert len(data) == 1
    assert data[0]["name"] == "Python Guide"


@pytest.mark.asyncio
async def test_export_all_downloads_csv(client: AsyncClient) -> None:
    response = await client.post(
        "/admin/products/export/",
        data={"format": "csv", "scope": "all"},
        follow_redirects=False,
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert b"name" in response.content


@pytest.mark.asyncio
async def test_import_json_creates_documents(client: AsyncClient, mock_db) -> None:
    payload = json.dumps(
        [
            {
                "name": "Imported Widget",
                "price": 12.5,
                "category": "electronics",
                "active": True,
            }
        ]
    ).encode("utf-8")

    response = await client.post(
        "/admin/products/import/",
        data={"format": "json"},
        files={"import_file": ("products.json", payload, "application/json")},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/admin/products/?imported=1"
    assert mock_db["test_db"].products.find_one({"name": "Imported Widget"}) is not None


@pytest.mark.asyncio
async def test_import_invalid_file_shows_errors(client: AsyncClient) -> None:
    response = await client.post(
        "/admin/products/import/",
        data={"format": "json"},
        files={"import_file": ("products.json", b"not-json", "application/json")},
        follow_redirects=False,
    )
    assert response.status_code == 400
    assert "data-transfer__errors" in response.text


def test_builtin_actions_exclude_import_export() -> None:
    class AdminNoCustom(ProductAdmin):
        actions: list[str] = []

    names = [name for name, _, _ in AdminNoCustom(Product).get_actions()]
    assert names == ["delete_selected"]
