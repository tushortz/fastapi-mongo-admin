"""Flash messages for post-redirect feedback."""

from __future__ import annotations

from fastapi import Request, Response
from fastapi.responses import RedirectResponse

from fastapi_mongo_admin.i18n import Translator

FLASH_COOKIE = "admin_flash"
FLASH_REPR_COOKIE = "admin_flash_repr"
FLASH_MAX_AGE = 60
FLASH_ADDED = "added"
FLASH_CHANGED = "changed"


def set_flash_cookie(response: RedirectResponse, flash_type: str, object_repr: str) -> None:
    """Attach one-time flash cookies to a redirect response."""
    cookie_kwargs = {
        "max_age": FLASH_MAX_AGE,
        "httponly": False,
        "samesite": "lax",
        "path": "/",
    }
    response.set_cookie(FLASH_COOKIE, flash_type, **cookie_kwargs)
    response.set_cookie(FLASH_REPR_COOKIE, object_repr, **cookie_kwargs)


def redirect_to_changelist(
    prefix: str,
    collection: str,
    flash_type: str,
    object_repr: str,
) -> RedirectResponse:
    """Redirect to the model changelist with a flash message."""
    response = RedirectResponse(url=f"{prefix}/{collection}/", status_code=303)
    set_flash_cookie(response, flash_type, object_repr)
    return response


def resolve_flash_message(request: Request, translator: Translator) -> tuple[str | None, bool]:
    """Return translated flash text and whether a flash cookie was present."""
    flash_type = request.cookies.get(FLASH_COOKIE)
    if flash_type not in (FLASH_ADDED, FLASH_CHANGED):
        return None, False
    object_repr = request.cookies.get(FLASH_REPR_COOKIE, "")
    if not object_repr:
        return None, True
    if flash_type == FLASH_ADDED:
        return translator("saved_added", object=object_repr), True
    return translator("saved_changed", object=object_repr), True


def clear_flash_cookie(response: Response) -> None:
    """Remove flash cookies after they have been displayed."""
    response.delete_cookie(FLASH_COOKIE, path="/")
    response.delete_cookie(FLASH_REPR_COOKIE, path="/")
