"""i18n and theme preference tests."""

import pytest
from httpx import AsyncClient

from fastapi_mongo_admin.i18n import get_translator


def test_translator_french() -> None:
    t = get_translator("fr")
    assert t("home") == "Accueil"
    assert t("save") == "Enregistrer"


def test_translator_fallback() -> None:
    t = get_translator("xx")
    assert t("home") == "Home"


def test_translator_arabic_rtl_context() -> None:
    t = get_translator("ar")
    assert t("delete") == "حذف"


@pytest.mark.asyncio
async def test_french_changelist(client: AsyncClient) -> None:
    response = await client.get(
        "/admin/products/",
        cookies={"admin_lang": "fr"},
    )
    assert response.status_code == 200
    assert "Rechercher" in response.text
    assert "Accueil" in response.text


@pytest.mark.asyncio
async def test_dark_theme_attribute(client: AsyncClient) -> None:
    response = await client.get(
        "/admin/",
        cookies={"admin_theme": "dark"},
    )
    assert response.status_code == 200
    assert 'data-theme="dark"' in response.text


@pytest.mark.asyncio
async def test_language_preference_post(client: AsyncClient) -> None:
    response = await client.post(
        "/admin/preferences/",
        data={"lang": "de", "next_url": "/admin/"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.cookies.get("admin_lang") == "de"


@pytest.mark.asyncio
async def test_lang_query_sets_cookie(client: AsyncClient) -> None:
    response = await client.get(
        "/admin/?lang=es",
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.cookies.get("admin_lang") == "es"
