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
        """Initialize a translator for one language.

        Args:
            language: Active language code.
            messages: Message catalog for the active language.
            fallback: Fallback catalog (typically English).
        """
        self.language = language
        self._messages = messages
        self._fallback = fallback

    def gettext(self, key: str, **kwargs: Any) -> str:
        """Return a translated string for a message key.

        Args:
            key: Message key.
            **kwargs: Optional ``str.format`` placeholders.

        Returns:
            Translated string, or the key itself when missing.
        """
        text = self._messages.get(key, self._fallback.get(key, key))
        if kwargs:
            return text.format(**kwargs)
        return text

    def __call__(self, key: str, **kwargs: Any) -> str:
        """Alias for template usage (``t('key')``).

        Args:
            key: Message key.
            **kwargs: Optional ``str.format`` placeholders.

        Returns:
            Translated string.
        """
        return self.gettext(key, **kwargs)
