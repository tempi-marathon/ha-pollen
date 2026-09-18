"""Open-Meteo Air Quality API client + parser for pollen."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .const import (
    API_KEYS,
    API_TO_SPECIES,
    ATTRIBUTION,
    FORECAST_DAYS,
    OPEN_METEO_URL,
    PROVIDER_OPEN_METEO,
    UNIT_GRAINS,
)
from .levels import LEVEL_NONE, level_for_grains, level_label
from .models import DailyPeak, ForecastPoint, PollenSnapshot, SpeciesReading

if TYPE_CHECKING:
    from aiohttp import ClientSession


class OpenMeteoError(Exception):
    """Raised when the Open-Meteo request fails."""


class OutOfCoverageError(Exception):
    """Raised when the location has no CAMS pollen data."""


def daily_peaks(
    times: list[str], values: list[float | None]
) -> list[DailyPeak]:
    """Collapse an hourly series into per-calendar-day maxima."""
    by_date: dict[str, list[float]] = {}
    for t, value in zip(times, values, strict=False):
        if value is None:
            continue
        date = t[:10]
        by_date.setdefault(date, []).append(value)
    return [
        DailyPeak(date=date, value=max(vals))
        for date, vals in sorted(by_date.items())
    ]


def parse_response(
    data: dict[str, Any],
    *,
    requested_lat: float,
    requested_lon: float,
) -> PollenSnapshot:
    """Parse an Open-Meteo air-quality JSON payload into a snapshot."""
    current = data.get("current") or {}
    hourly = data.get("hourly") or {}
    times: list[str] = list(hourly.get("time") or [])

    any_value = False
    readings: dict[str, SpeciesReading] = {}

    for api_key in API_KEYS:
        species = API_TO_SPECIES[api_key]
        cur = current.get(api_key)
        if cur is not None:
            any_value = True
        series = list(hourly.get(api_key) or [])
        # Pad / trim to times length
        if len(series) < len(times):
            series = series + [None] * (len(times) - len(series))
        elif len(series) > len(times):
            series = series[: len(times)]

        if any(v is not None for v in series):
            any_value = True

        lvl = level_for_grains(species, cur if isinstance(cur, (int, float)) else None)
        hourly_points = tuple(
            ForecastPoint(
                t=t,
                value=float(v) if isinstance(v, (int, float)) else None,
            )
            for t, v in zip(times, series, strict=False)
        )
        readings[species] = SpeciesReading(
            species=species,
            current=float(cur) if isinstance(cur, (int, float)) else None,
            unit=UNIT_GRAINS,
            level=lvl,
            level_label=level_label(lvl),
            forecast_hourly=hourly_points,
            forecast_daily=tuple(daily_peaks(times, series)),
        )

    if not any_value:
        raise OutOfCoverageError(
            "Open-Meteo returned no pollen data for this location "
            "(CAMS European coverage only)."
        )

    overall_level = LEVEL_NONE
    dominant: str | None = None
    for species, reading in readings.items():
        if reading.level is None:
            continue
        if reading.level > overall_level:
            overall_level = reading.level
            dominant = species
        elif (
            reading.level == overall_level
            and reading.level > LEVEL_NONE
            and reading.current is not None
        ):
            assert dominant is not None
            prev = readings[dominant]
            if prev.current is None or reading.current > prev.current:
                dominant = species
            elif reading.current == prev.current and species < dominant:
                dominant = species

    if overall_level == LEVEL_NONE:
        dominant = None

    return PollenSnapshot(
        provider=PROVIDER_OPEN_METEO,
        latitude=float(data.get("latitude", requested_lat)),
        longitude=float(data.get("longitude", requested_lon)),
        generated_at=current.get("time"),
        readings=readings,
        overall_level=overall_level,
        overall_level_label=level_label(overall_level),
        dominant_species=dominant,
        in_coverage=True,
        attribution=ATTRIBUTION,
    )


async def fetch_pollen(
    session: ClientSession,
    latitude: float,
    longitude: float,
) -> PollenSnapshot:
    """Fetch and parse pollen from Open-Meteo."""
    from aiohttp import ClientError

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": ",".join(API_KEYS),
        "hourly": ",".join(API_KEYS),
        "forecast_days": FORECAST_DAYS,
        "timezone": "auto",
    }
    try:
        async with session.get(OPEN_METEO_URL, params=params, timeout=30) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise OpenMeteoError(f"HTTP {resp.status}: {text[:200]}")
            data = await resp.json(content_type=None)
    except TimeoutError as err:
        raise OpenMeteoError("Open-Meteo request timed out") from err
    except ClientError as err:
        raise OpenMeteoError(f"Open-Meteo request failed: {err}") from err

    if not isinstance(data, dict):
        raise OpenMeteoError("Unexpected Open-Meteo response")
    if data.get("error"):
        raise OpenMeteoError(str(data.get("reason") or "Open-Meteo error"))

    return parse_response(data, requested_lat=latitude, requested_lon=longitude)
