"""Tests for Open-Meteo pollen parsing and HTTP client."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest
from custom_components.pollen.open_meteo import (
    OpenMeteoError,
    OutOfCoverageError,
    daily_peaks,
    fetch_pollen,
    parse_response,
)


def _payload(
    *,
    current: dict,
    hourly_times: list[str],
    hourly: dict[str, list],
    latitude: float = 52.5,
    longitude: float = 13.4,
) -> dict:
    return {
        "latitude": latitude,
        "longitude": longitude,
        "current": {"time": "2026-06-19T12:00", **current},
        "hourly": {"time": hourly_times, **hourly},
    }


def _null_species() -> dict[str, None]:
    return {
        "alder_pollen": None,
        "birch_pollen": None,
        "grass_pollen": None,
        "mugwort_pollen": None,
        "olive_pollen": None,
        "ragweed_pollen": None,
    }


def _zero_species() -> dict[str, float]:
    return {
        "alder_pollen": 0.0,
        "birch_pollen": 0.0,
        "grass_pollen": 0.0,
        "mugwort_pollen": 0.0,
        "olive_pollen": 0.0,
        "ragweed_pollen": 0.0,
    }


class _FakeResponse:
    """Minimal aiohttp response double."""

    def __init__(
        self,
        *,
        status: int = 200,
        json_data: Any = None,
        text: str = "",
        json_error: Exception | None = None,
    ) -> None:
        self.status = status
        self._json_data = json_data
        self._text = text
        self._json_error = json_error

    async def text(self) -> str:
        return self._text

    async def json(self, content_type: Any = None) -> Any:
        if self._json_error is not None:
            raise self._json_error
        return self._json_data

    async def __aenter__(self) -> _FakeResponse:
        return self

    async def __aexit__(self, *args: object) -> None:
        return None


class _FakeSession:
    def __init__(self, response: _FakeResponse) -> None:
        self._response = response
        self.last_get: dict[str, Any] | None = None

    def get(
        self, url: str, *, params: Any = None, timeout: Any = None
    ) -> _FakeResponse:
        self.last_get = {"url": url, "params": params, "timeout": timeout}
        return self._response


def test_daily_peaks_take_max_per_day() -> None:
    times = [
        "2026-06-19T00:00",
        "2026-06-19T12:00",
        "2026-06-20T00:00",
        "2026-06-20T18:00",
    ]
    values = [10.0, 40.0, None, 15.0]
    peaks = daily_peaks(times, values)
    assert [(p.date, p.value) for p in peaks] == [
        ("2026-06-19", 40.0),
        ("2026-06-20", 15.0),
    ]


def test_parse_in_coverage_builds_readings_and_overall() -> None:
    times = ["2026-06-19T00:00", "2026-06-19T01:00", "2026-06-20T00:00"]
    data = _payload(
        current={
            "alder_pollen": 0.0,
            "birch_pollen": 25.0,
            "grass_pollen": 60.0,
            "mugwort_pollen": 0.0,
            "olive_pollen": 0.0,
            "ragweed_pollen": 0.0,
        },
        hourly_times=times,
        hourly={
            "alder_pollen": [0.0, 0.0, 0.0],
            "birch_pollen": [20.0, 30.0, 10.0],
            "grass_pollen": [40.0, 60.0, 55.0],
            "mugwort_pollen": [0.0, 0.0, 0.0],
            "olive_pollen": [0.0, 0.0, 0.0],
            "ragweed_pollen": [0.0, 0.0, 0.0],
        },
    )
    snap = parse_response(data, requested_lat=52.52, requested_lon=13.41)
    assert snap.provider == "open_meteo"
    assert snap.in_coverage is True
    assert snap.readings["grass"].current == 60.0
    assert snap.readings["grass"].level_label == "high"
    assert snap.readings["birch"].level_label == "low"
    assert snap.overall_level_label == "high"
    assert snap.dominant_species == "grass"
    assert len(snap.readings["grass"].forecast_hourly) == 3
    assert snap.readings["grass"].forecast_daily[0].value == 60.0
    assert snap.overall_hourly()[1].value == 60.0
    assert "Open-Meteo" in snap.attribution


def test_parse_all_null_is_out_of_coverage() -> None:
    times = ["2026-06-19T00:00"]
    nulls = _null_species()
    data = _payload(
        current=nulls,
        hourly_times=times,
        hourly={k: [None] for k in nulls},
    )
    with pytest.raises(OutOfCoverageError):
        parse_response(data, requested_lat=40.71, requested_lon=-74.01)


def test_parse_all_zero_is_in_coverage_none() -> None:
    times = ["2026-06-19T00:00"]
    zeros = _zero_species()
    data = _payload(
        current=zeros,
        hourly_times=times,
        hourly={k: [0.0] for k in zeros},
    )
    snap = parse_response(data, requested_lat=52.52, requested_lon=13.41)
    assert snap.in_coverage is True
    assert snap.overall_level == 0
    assert snap.overall_level_label == "none"
    assert snap.dominant_species is None


def test_parse_rejects_non_dict_current() -> None:
    data = {
        "latitude": 52.5,
        "longitude": 13.4,
        "current": ["not", "a", "dict"],
        "hourly": {"time": ["2026-06-19T00:00"]},
    }
    with pytest.raises(OpenMeteoError, match="shape"):
        parse_response(data, requested_lat=52.5, requested_lon=13.4)


def test_parse_rejects_non_dict_hourly() -> None:
    data = {
        "latitude": 52.5,
        "longitude": 13.4,
        "current": {},
        "hourly": "nope",
    }
    with pytest.raises(OpenMeteoError, match="shape"):
        parse_response(data, requested_lat=52.5, requested_lon=13.4)


def test_parse_rejects_bool_and_nan_as_missing() -> None:
    times = ["2026-06-19T00:00"]
    current = _null_species()
    current["grass_pollen"] = True  # type: ignore[assignment]
    current["birch_pollen"] = float("nan")  # type: ignore[assignment]
    hourly = {k: [None] for k in _null_species()}
    hourly["grass_pollen"] = [True]  # type: ignore[list-item]
    hourly["birch_pollen"] = [float("nan")]
    # All non-finite / bool → treated as null → out of coverage
    data = _payload(current=current, hourly_times=times, hourly=hourly)
    with pytest.raises(OutOfCoverageError):
        parse_response(data, requested_lat=52.5, requested_lon=13.4)


def test_parse_falls_back_to_requested_coords() -> None:
    times = ["2026-06-19T00:00"]
    zeros = _zero_species()
    data = _payload(
        current=zeros,
        hourly_times=times,
        hourly={k: [0.0] for k in zeros},
        latitude="bad",  # type: ignore[arg-type]
        longitude=float("nan"),
    )
    snap = parse_response(data, requested_lat=52.52, requested_lon=13.41)
    assert snap.latitude == 52.52
    assert snap.longitude == 13.41


def test_dominant_higher_grains_wins_same_level() -> None:
    """Equal severity: higher grains wins (both birch/alder in low band)."""
    times = ["2026-06-19T00:00"]
    # birch onset 20 peak 100 → 30 is low; alder onset 45 peak 80 → 50 is low
    current = _zero_species()
    current["birch_pollen"] = 30.0
    current["alder_pollen"] = 50.0
    data = _payload(
        current=current,
        hourly_times=times,
        hourly={k: [current[k]] for k in current},
    )
    snap = parse_response(data, requested_lat=52.5, requested_lon=13.4)
    assert snap.readings["birch"].level == snap.readings["alder"].level == 1
    assert snap.dominant_species == "alder"


def test_dominant_alphabetical_tie_break() -> None:
    """Equal level and equal grains → alphabetical species key."""
    times = ["2026-06-19T00:00"]
    # grass and mugwort share onset 3 / peak 50 → 10 is low for both
    current = _zero_species()
    current["grass_pollen"] = 10.0
    current["mugwort_pollen"] = 10.0
    data = _payload(
        current=current,
        hourly_times=times,
        hourly={k: [current[k]] for k in current},
    )
    snap = parse_response(data, requested_lat=52.5, requested_lon=13.4)
    assert snap.readings["grass"].level == snap.readings["mugwort"].level == 1
    assert snap.dominant_species == "grass"


def test_overall_forecast_is_max_grains_not_severity() -> None:
    """Birch 90 (medium) beats grass 20 (low) for state; forecast value is 90."""
    times = ["2026-06-19T00:00", "2026-06-19T01:00"]
    current = _zero_species()
    current["birch_pollen"] = 90.0  # medium (mid=60, peak=100)
    current["grass_pollen"] = 20.0  # low (mid=26.5, peak=50)
    data = _payload(
        current=current,
        hourly_times=times,
        hourly={
            **{k: [0.0, 0.0] for k in current},
            "birch_pollen": [90.0, 80.0],
            "grass_pollen": [20.0, 25.0],
        },
    )
    snap = parse_response(data, requested_lat=52.5, requested_lon=13.4)
    assert snap.overall_level_label == "medium"
    assert snap.dominant_species == "birch"
    assert snap.overall_hourly()[0].value == 90.0
    assert snap.overall_hourly()[1].value == 80.0
    assert snap.overall_daily()[0].value == 90.0


@pytest.mark.asyncio
async def test_fetch_pollen_success() -> None:
    times = ["2026-06-19T00:00"]
    zeros = _zero_species()
    body = _payload(
        current=zeros,
        hourly_times=times,
        hourly={k: [0.0] for k in zeros},
    )
    session = _FakeSession(_FakeResponse(json_data=body))
    snap = await fetch_pollen(session, 52.52, 13.41)  # type: ignore[arg-type]
    assert snap.overall_level_label == "none"
    assert session.last_get is not None
    assert "air-quality" in session.last_get["url"]
    timeout = session.last_get["timeout"]
    assert timeout is not None
    assert getattr(timeout, "total", None) == 30


@pytest.mark.asyncio
async def test_fetch_pollen_http_error() -> None:
    session = _FakeSession(
        _FakeResponse(status=503, text="service unavailable boom" * 20)
    )
    with pytest.raises(OpenMeteoError, match="HTTP 503"):
        await fetch_pollen(session, 52.52, 13.41)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_fetch_pollen_timeout() -> None:
    session = MagicMock()
    session.get.side_effect = TimeoutError()
    with pytest.raises(OpenMeteoError, match="timed out"):
        await fetch_pollen(session, 52.52, 13.41)


@pytest.mark.asyncio
async def test_fetch_pollen_api_error_flag() -> None:
    session = _FakeSession(
        _FakeResponse(json_data={"error": True, "reason": "Invalid latitude"})
    )
    with pytest.raises(OpenMeteoError, match="Invalid latitude"):
        await fetch_pollen(session, 52.52, 13.41)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_fetch_pollen_non_dict_json() -> None:
    session = _FakeSession(_FakeResponse(json_data=["not", "a", "dict"]))
    with pytest.raises(OpenMeteoError, match="Unexpected"):
        await fetch_pollen(session, 52.52, 13.41)  # type: ignore[arg-type]
