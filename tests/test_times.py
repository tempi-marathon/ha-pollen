"""Tests for provider timestamp parsing."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

from custom_components.pollen.times import generated_at_iso, parse_generated_at


def test_parse_naive_applies_utc_offset() -> None:
    dt = parse_generated_at("2026-06-19T12:00", utc_offset_seconds=7200)
    assert dt == datetime(2026, 6, 19, 12, 0, tzinfo=timezone(timedelta(hours=2)))


def test_parse_naive_defaults_to_utc() -> None:
    dt = parse_generated_at("2026-06-19T12:00")
    assert dt == datetime(2026, 6, 19, 12, 0, tzinfo=UTC)


def test_parse_preserves_existing_offset() -> None:
    dt = parse_generated_at("2026-06-19T12:00:00+01:00", utc_offset_seconds=7200)
    assert dt is not None
    assert dt.utcoffset() == timedelta(hours=1)


def test_parse_invalid_and_empty() -> None:
    assert parse_generated_at(None) is None
    assert parse_generated_at("") is None
    assert parse_generated_at("not-a-time") is None


def test_generated_at_iso_includes_offset() -> None:
    assert (
        generated_at_iso("2026-06-19T12:00", utc_offset_seconds=3600)
        == "2026-06-19T12:00:00+01:00"
    )
