"""Constants for the Pollen integration."""

from __future__ import annotations

from datetime import timedelta
from typing import Final

DOMAIN: Final = "pollen"
PROVIDER_OPEN_METEO: Final = "open_meteo"

ATTRIBUTION: Final = (
    "Data provided by Open-Meteo.com (CC BY 4.0). "
    "Generated using Copernicus Atmosphere Monitoring Service information."
)

CONF_LATITUDE: Final = "latitude"
CONF_LONGITUDE: Final = "longitude"
CONF_NAME: Final = "name"

UPDATE_INTERVAL: Final = timedelta(minutes=60)
FORECAST_DAYS: Final = 4

# Open-Meteo API keys → canonical species keys.
SPECIES: Final[tuple[tuple[str, str, str], ...]] = (
    ("alder_pollen", "alder", "Alder"),
    ("birch_pollen", "birch", "Birch"),
    ("grass_pollen", "grass", "Grass"),
    ("mugwort_pollen", "mugwort", "Mugwort"),
    ("olive_pollen", "olive", "Olive"),
    ("ragweed_pollen", "ragweed", "Ragweed"),
)

API_KEYS: Final[tuple[str, ...]] = tuple(api for api, _, _ in SPECIES)
SPECIES_KEYS: Final[tuple[str, ...]] = tuple(key for _, key, _ in SPECIES)
SPECIES_NAMES: Final[dict[str, str]] = {key: name for _, key, name in SPECIES}
API_TO_SPECIES: Final[dict[str, str]] = {api: key for api, key, _ in SPECIES}

UNIT_GRAINS: Final = "grains_m3"
UNIT_OF_MEASUREMENT_GRAINS: Final = "grains/m³"

ATTR_PROVIDER: Final = "provider"
ATTR_SPECIES: Final = "species"
ATTR_UNIT: Final = "unit"
ATTR_LEVEL: Final = "level"
ATTR_LEVEL_LABEL: Final = "level_label"
ATTR_FORECAST_HOURLY: Final = "forecast_hourly"
ATTR_FORECAST_DAILY: Final = "forecast_daily"
ATTR_DOMINANT_SPECIES: Final = "dominant_species"

OVERALL_SPECIES: Final = "overall"

OPEN_METEO_URL: Final = "https://air-quality-api.open-meteo.com/v1/air-quality"
