"""Display formatting for date and datetime values."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

DEFAULT_DATE_FORMAT = "j M Y"
DEFAULT_DATETIME_FORMAT = "j M Y, g:ia"


def parse_datetime(value: Any) -> datetime | None:
    """Parse a datetime from BSON, ISO string, or date.

    Args:
        value: Input value to parse.

    Returns:
        Parsed ``datetime``, or ``None`` when parsing fails.
    """
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time())
    if isinstance(value, str):
        normalized = value.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(normalized)
        except ValueError:
            try:
                return datetime.strptime(value[:10], "%Y-%m-%d")
            except ValueError:
                return None
    return None


def parse_date(value: Any) -> date | None:
    """Parse a date from BSON, ISO string, or datetime.

    Args:
        value: Input value to parse.

    Returns:
        Parsed ``date``, or ``None`` when parsing fails.
    """
    if value is None or value == "":
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            parsed = parse_datetime(value)
            return parsed.date() if parsed else None
    return None


def _format_default_date(value: date) -> str:
    """Format as ``8 Apr 2026``.

    Args:
        value: Date to format.

    Returns:
        Human-readable date string.
    """
    return f"{value.day} {value.strftime('%b')} {value.year}"


def _format_default_datetime(value: datetime) -> str:
    """Format as ``8 Apr 2026, 7:32pm``.

    Args:
        value: Datetime to format.

    Returns:
        Human-readable datetime string.
    """
    day = value.day
    month = value.strftime("%b")
    year = value.year
    hour24 = value.hour
    period = "am" if hour24 < 12 else "pm"
    hour12 = hour24 % 12 or 12
    return f"{day} {month} {year}, {hour12}:{value.minute:02d}{period}"


def _apply_strftime(value: datetime, fmt: str) -> str:
    """Apply strftime or Django-style tokens (``j M Y, g:ia``).

    Args:
        value: Datetime to format.
        fmt: Format string using ``%`` tokens or Django-style tokens.

    Returns:
        Formatted datetime string.
    """
    if "%" in fmt:
        return value.strftime(fmt)
    mapping = {
        "j": str(value.day),
        "M": value.strftime("%b"),
        "Y": str(value.year),
        "g": str(value.hour % 12 or 12),
        "i": f"{value.minute:02d}",
        "a": "am" if value.hour < 12 else "pm",
    }
    result = fmt
    for token, replacement in mapping.items():
        result = result.replace(token, replacement)
    return result


def format_date_display(value: Any, fmt: str | None = None) -> str:
    """Format a value for date display in lists and readonly fields.

    Args:
        value: Raw field value.
        fmt: Optional custom format string.

    Returns:
        Formatted date string, or ``""`` for empty values.
    """
    if value in (None, ""):
        return ""
    parsed = parse_date(value)
    if parsed is None:
        return str(value)
    if fmt in (None, DEFAULT_DATE_FORMAT):
        return _format_default_date(parsed)
    as_dt = datetime.combine(parsed, datetime.min.time())
    return _apply_strftime(as_dt, fmt)


def format_datetime_display(value: Any, fmt: str | None = None) -> str:
    """Format a value for datetime display in lists and readonly fields.

    Args:
        value: Raw field value.
        fmt: Optional custom format string.

    Returns:
        Formatted datetime string, or ``""`` for empty values.
    """
    if value in (None, ""):
        return ""
    parsed = parse_datetime(value)
    if parsed is None:
        return str(value)
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
    if fmt in (None, DEFAULT_DATETIME_FORMAT):
        return _format_default_datetime(parsed)
    return _apply_strftime(parsed, fmt)
