"""Auth integration tests."""

import mongomock
import pytest
from fastapi import FastAPI, HTTPException
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel

from fastapi_mongo_admin import AdminSite, ModelAdmin, mount_admin_app


class Secret(BaseModel):
    value: str


class SecretAdmin(ModelAdmin):
    model = Secret
    collection_name = "secrets"
    list_display = ["value"]

    def has_view_permission(self, request, user=None, obj=None) -> bool:
        return user is not None


def _auth_admin():
    def get_user():
        raise HTTPException(status_code=401, detail="Unauthorized")

    return get_user


@pytest.fixture
def secured_app() -> FastAPI:
    client = mongomock.MongoClient()
    db = client["test_db"]
    site = AdminSite()
    site.register(Secret, SecretAdmin)

    app = FastAPI()

    async def get_current_user():
        return {"id": "user-1"}

    mount_admin_app(
        app,
        lambda: db,
        admin_site=site,
        mode="sync",
        auth_dependency=get_current_user,
    )
    return app


@pytest.mark.asyncio
async def test_authenticated_access(secured_app: FastAPI) -> None:
    transport = ASGITransport(app=secured_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/admin/secrets/")
        assert response.status_code == 200
