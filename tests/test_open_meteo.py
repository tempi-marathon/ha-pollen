"""Tests for Open-Meteo pollen parsing."""

from __future__ import annotations

import pytest

from custom_components.pollen.open_meteo import (
    OutOfCoverageError,
    daily_peaks,
    parse_response,
)


def _payload(
    *,
    current: dict,
    hourly_times: list[str],
    hourly: dict[str, list],
) -> dict:
    return {
        "latitude": 52.5,
        "longitude": 13.4,
        "current": {"time": "2026-06-19T12:00", **current},
        "hourly": {"time": hourly_times, **hourly},
    }


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
    nulls = {
        "alder_pollen": None,
        "birch_pollen": None,
        "grass_pollen": None,
        "mugwort_pollen": None,
        "olive_pollen": None,
        "ragweed_pollen": None,
    }
    data = _payload(
        current=nulls,
        hourly_times=times,
        hourly={k: [None] for k in nulls},
    )
    with pytest.raises(OutOfCoverageError):
        parse_response(data, requested_lat=40.71, requested_lon=-74.01)


def test_parse_all_zero_is_in_coverage_none() -> None:
    times = ["2026-06-19T00:00"]
    zeros = {
        "alder_pollen": 0.0,
        "birch_pollen": 0.0,
        "grass_pollen": 0.0,
        "mugwort_pollen": 0.0,
        "olive_pollen": 0.0,
        "ragweed_pollen": 0.0,
    }
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
