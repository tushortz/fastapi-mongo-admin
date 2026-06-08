"""Translation helper for admin UI."""

from __future__ import annotations

from typing import Any

DEFAULT_LANGUAGE = "en"

SUPPORTED_LANGUAGES: dict[str, str] = {
    "en": "English",
    "fr": "Français",
    "pt": "Português",
    "ru": "Русский",
    "it": "Italiano",
    "ch": "中文",
    "es": "Español",
    "de": "Deutsch",
    "ar": "العربية",
}

RTL_LANGUAGES = frozenset({"ar"})


class Translator:
    """Lookup translated strings with optional format placeholders."""

    def __init__(self, language: str, messages: dict[str, str], fallback: dict[str, str]) -> None:
        self.language = language
        self._messages = messages
        self._fallback = fallback

    def gettext(self, key: str, **kwargs: Any) -> str:
        """Return translated string for key."""
        text = self._messages.get(key, self._fallback.get(key, key))
        if kwargs:
            return text.format(**kwargs)
        return text

    def __call__(self, key: str, **kwargs: Any) -> str:
        """Alias for template usage."""
        return self.gettext(key, **kwargs)
