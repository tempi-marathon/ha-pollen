"""Open-Meteo Air Quality API client + parser for pollen."""

from __future__ import annotations

import math
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


def _as_finite_float(value: Any) -> float | None:
    """Return a finite float, or None for missing / non-numeric / non-finite values.

    Rejects bool (which is a subclass of int) and NaN/Inf so they never become
    sensor state.
    """
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        number = float(value)
        if math.isfinite(number):
            return number
    return None


def _as_coord(value: Any, fallback: float) -> float:
    """Coerce API lat/lon to float, falling back to the requested coordinate."""
    number = _as_finite_float(value)
    return number if number is not None else float(fallback)


def daily_peaks(times: list[str], values: list[float | None]) -> list[DailyPeak]:
    """Collapse an hourly series into per-calendar-day maxima."""
    by_date: dict[str, list[float]] = {}
    for t, value in zip(times, values, strict=False):
        if value is None:
            continue
        date = t[:10]
        by_date.setdefault(date, []).append(value)
    return [
        DailyPeak(date=date, value=max(vals)) for date, vals in sorted(by_date.items())
    ]


def parse_response(
    data: dict[str, Any],
    *,
    requested_lat: float,
    requested_lon: float,
) -> PollenSnapshot:
    """Parse an Open-Meteo air-quality JSON payload into a snapshot."""
    current_raw = data.get("current")
    hourly_raw = data.get("hourly")
    if current_raw is None:
        current_raw = {}
    if hourly_raw is None:
        hourly_raw = {}
    if not isinstance(current_raw, dict) or not isinstance(hourly_raw, dict):
        raise OpenMeteoError("Unexpected Open-Meteo response shape")

    current: dict[str, Any] = current_raw
    hourly: dict[str, Any] = hourly_raw
    times: list[str] = list(hourly.get("time") or [])

    any_value = False
    readings: dict[str, SpeciesReading] = {}

    for api_key in API_KEYS:
        species = API_TO_SPECIES[api_key]
        cur = _as_finite_float(current.get(api_key))
        if cur is not None:
            any_value = True
        series_raw = list(hourly.get(api_key) or [])
        # Pad / trim to times length
        if len(series_raw) < len(times):
            series_raw = series_raw + [None] * (len(times) - len(series_raw))
        elif len(series_raw) > len(times):
            series_raw = series_raw[: len(times)]

        series: list[float | None] = [_as_finite_float(v) for v in series_raw]
        if any(v is not None for v in series):
            any_value = True

        lvl = level_for_grains(species, cur)
        hourly_points = tuple(
            ForecastPoint(t=t, value=v) for t, v in zip(times, series, strict=False)
        )
        readings[species] = SpeciesReading(
            species=species,
            current=cur,
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
            and dominant is not None
        ):
            prev = readings[dominant]
            if prev.current is None or reading.current > prev.current:
                dominant = species
            elif reading.current == prev.current and species < dominant:
                # Same grains: alphabetical species key wins.
                dominant = species

    if overall_level == LEVEL_NONE:
        dominant = None

    generated = current.get("time")
    generated_at = generated if isinstance(generated, str) else None

    return PollenSnapshot(
        provider=PROVIDER_OPEN_METEO,
        latitude=_as_coord(data.get("latitude"), requested_lat),
        longitude=_as_coord(data.get("longitude"), requested_lon),
        generated_at=generated_at,
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
    from aiohttp import ClientError, ClientTimeout

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": ",".join(API_KEYS),
        "hourly": ",".join(API_KEYS),
        "forecast_days": FORECAST_DAYS,
        "timezone": "auto",
    }
    try:
        async with session.get(
            OPEN_METEO_URL,
            params=params,
            timeout=ClientTimeout(total=30),
        ) as resp:
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
