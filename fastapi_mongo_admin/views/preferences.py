"""Theme and language preferences."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

from fastapi import Request, Response
from fastapi.responses import RedirectResponse

from fastapi_mongo_admin.i18n import (
    DEFAULT_LANGUAGE,
    SUPPORTED_LANGUAGES,
    get_translator,
)

LANG_COOKIE = "admin_lang"
THEME_COOKIE = "admin_theme"
COOKIE_MAX_AGE = 60 * 60 * 24 * 365


def resolve_language(request: Request) -> str:
    """Resolve the active UI language from query params or cookies.

    Args:
        request: Current HTTP request.

    Returns:
        Supported language code.
    """
    query_lang = request.query_params.get("lang")
    if query_lang and query_lang in SUPPORTED_LANGUAGES:
        return query_lang
    cookie_lang = request.cookies.get(LANG_COOKIE, DEFAULT_LANGUAGE)
    return cookie_lang if cookie_lang in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE


def resolve_theme(request: Request) -> str:
    """Resolve the active UI theme from query params or cookies.

    Args:
        request: Current HTTP request.

    Returns:
        ``light`` or ``dark``.
    """
    query_theme = request.query_params.get("theme")
    if query_theme in ("light", "dark"):
        return query_theme
    cookie_theme = request.cookies.get(THEME_COOKIE, "light")
    return cookie_theme if cookie_theme in ("light", "dark") else "light"


def build_ui_context(request: Request) -> dict[str, Any]:
    """Build i18n and theme context for Jinja templates.

    Args:
        request: Current HTTP request.

    Returns:
        Dict with ``lang``, ``theme``, ``is_rtl``, ``t``, ``languages``, and
        ``return_url`` keys.
    """
    lang = resolve_language(request)
    theme = resolve_theme(request)
    translator = get_translator(lang)
    return {
        "lang": lang,
        "theme": theme,
        "is_rtl": lang == "ar",
        "t": translator,
        "languages": SUPPORTED_LANGUAGES,
        "return_url": _safe_return_url(request),
    }


def apply_preference_cookies(response: Response, request: Request) -> None:
    """Persist ``lang``/``theme`` query params onto response cookies.

    Args:
        response: HTTP response to mutate.
        request: Current HTTP request.

    Returns:
        None.
    """
    lang = request.query_params.get("lang")
    if lang and lang in SUPPORTED_LANGUAGES:
        response.set_cookie(
            LANG_COOKIE, lang, max_age=COOKIE_MAX_AGE, httponly=False, samesite="lax"
        )
    theme = request.query_params.get("theme")
    if theme in ("light", "dark"):
        response.set_cookie(
            THEME_COOKIE, theme, max_age=COOKIE_MAX_AGE, httponly=False, samesite="lax"
        )


def set_preference_cookies(
    response: Response, *, lang: str | None = None, theme: str | None = None
) -> None:
    """Set language and/or theme cookies on a response.

    Args:
        response: HTTP response to mutate.
        lang: Optional language code.
        theme: Optional theme name (``light`` or ``dark``).

    Returns:
        None.
    """
    if lang and lang in SUPPORTED_LANGUAGES:
        response.set_cookie(
            LANG_COOKIE, lang, max_age=COOKIE_MAX_AGE, httponly=False, samesite="lax"
        )
    if theme in ("light", "dark"):
        response.set_cookie(
            THEME_COOKIE, theme, max_age=COOKIE_MAX_AGE, httponly=False, samesite="lax"
        )


def redirect_with_preferences(request: Request, _fallback: str = "") -> RedirectResponse | None:
    """Redirect once when ``lang``/``theme`` query params are present.

    Args:
        request: Current HTTP request.
        _fallback: Unused legacy parameter.

    Returns:
        RedirectResponse that strips preference params and sets cookies, or
        ``None`` when no preference params are present.
    """
    lang = request.query_params.get("lang")
    theme = request.query_params.get("theme")
    if not lang and not theme:
        return None
    if lang and lang not in SUPPORTED_LANGUAGES:
        lang = None
    if theme and theme not in ("light", "dark"):
        theme = None
    if not lang and not theme:
        return None

    params = {k: v for k, v in request.query_params.items() if k not in ("lang", "theme")}
    path = request.url.path
    query = urlencode(params)
    target = f"{path}?{query}" if query else path
    response = RedirectResponse(url=target, status_code=303)
    set_preference_cookies(response, lang=lang, theme=theme)
    return response


def _safe_return_url(request: Request) -> str:
    """Return the current path and query without preference params.

    Args:
        request: Current HTTP request.

    Returns:
        Relative URL string safe for hidden form fields.
    """
    params = {k: v for k, v in request.query_params.items() if k not in ("lang", "theme")}
    path = request.url.path
    query = urlencode(params)
    return f"{path}?{query}" if query else path
