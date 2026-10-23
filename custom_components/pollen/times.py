"""Timezone helpers for provider timestamps (stdlib only)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone


def parse_generated_at(
    value: str | None,
    *,
    utc_offset_seconds: int = 0,
) -> datetime | None:
    """Parse an Open-Meteo local time into a timezone-aware datetime.

    Open-Meteo with ``timezone=auto`` returns naive ISO local times plus a
    separate ``utc_offset_seconds``. TIMESTAMP sensors require tz-aware values.
    """
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(
            tzinfo=timezone(timedelta(seconds=utc_offset_seconds))
        )
    return parsed


def generated_at_iso(
    value: str | None,
    *,
    utc_offset_seconds: int = 0,
) -> str | None:
    """Return an ISO-8601 string with timezone, or None if unparsable."""
    parsed = parse_generated_at(value, utc_offset_seconds=utc_offset_seconds)
    return parsed.isoformat() if parsed is not None else None
