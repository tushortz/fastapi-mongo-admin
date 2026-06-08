"""Internationalization for admin UI."""

from fastapi_mongo_admin.i18n.translator import (
    DEFAULT_LANGUAGE,
    RTL_LANGUAGES,
    SUPPORTED_LANGUAGES,
    Translator,
)
from fastapi_mongo_admin.i18n.translations import MESSAGES

__all__ = [
    "DEFAULT_LANGUAGE",
    "SUPPORTED_LANGUAGES",
    "RTL_LANGUAGES",
    "Translator",
    "MESSAGES",
    "get_translator",
]


def get_translator(language: str) -> Translator:
    """Return translator for language, falling back to English."""
    lang = language if language in MESSAGES else DEFAULT_LANGUAGE
    return Translator(lang, MESSAGES[lang], MESSAGES[DEFAULT_LANGUAGE])
