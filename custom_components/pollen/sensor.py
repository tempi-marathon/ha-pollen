"""Sensor platform for Pollen."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_DOMINANT_SPECIES,
    ATTR_FORECAST_DAILY,
    ATTR_FORECAST_HOURLY,
    ATTR_LEVEL,
    ATTR_LEVEL_LABEL,
    ATTR_PROVIDER,
    ATTR_SPECIES,
    ATTR_UNIT,
    ATTRIBUTION,
    CONF_NAME,
    DOMAIN,
    OVERALL_SPECIES,
    UNIT_OF_MEASUREMENT_GRAINS,
)
from .coordinator import PollenCoordinator
from .levels import LEVEL_LABELS
from .models import DailyPeak, ForecastPoint, SpeciesReading

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Pollen sensors from a config entry."""
    coordinator: PollenCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = [PollenOverallSensor(coordinator, entry)]
    for species in coordinator.data.readings:
        entities.append(PollenSpeciesSensor(coordinator, entry, species))
    async_add_entities(entities)


def _device_info(entry: ConfigEntry) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.data.get(CONF_NAME) or entry.title or "Pollen",
        manufacturer="Open-Meteo",
        model="Pollen",
        entry_type=DeviceEntryType.SERVICE,
        configuration_url="https://open-meteo.com/en/docs/air-quality-api",
    )


def _hourly_attr(points: tuple[ForecastPoint, ...]) -> list[dict[str, Any]]:
    return [{"t": p.t, "value": p.value} for p in points]


def _daily_attr(peaks: tuple[DailyPeak, ...]) -> list[dict[str, Any]]:
    return [{"date": p.date, "value": p.value} for p in peaks]


class PollenBaseSensor(CoordinatorEntity[PollenCoordinator], SensorEntity):
    """Shared base for pollen sensors."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION
    _attr_icon = "mdi:flower-pollen"

    def __init__(
        self,
        coordinator: PollenCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_device_info = _device_info(entry)


class PollenSpeciesSensor(PollenBaseSensor):
    """Current grains/m³ for one pollen species."""

    _attr_native_unit_of_measurement = UNIT_OF_MEASUREMENT_GRAINS
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: PollenCoordinator,
        entry: ConfigEntry,
        species: str,
    ) -> None:
        super().__init__(coordinator, entry)
        self._species = species
        self._attr_unique_id = f"{entry.entry_id}_{species}"
        self._attr_translation_key = species

    def _reading(self) -> SpeciesReading | None:
        return self.coordinator.data.readings.get(self._species)

    @property
    def available(self) -> bool:
        return super().available and self._species in self.coordinator.data.readings

    @property
    def native_value(self) -> float | None:
        reading = self._reading()
        return reading.current if reading else None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        reading = self._reading()
        if reading is None:
            return None
        return {
            ATTR_PROVIDER: self.coordinator.data.provider,
            ATTR_SPECIES: reading.species,
            ATTR_UNIT: reading.unit,
            ATTR_LEVEL: reading.level,
            ATTR_LEVEL_LABEL: reading.level_label,
            ATTR_FORECAST_HOURLY: _hourly_attr(reading.forecast_hourly),
            ATTR_FORECAST_DAILY: _daily_attr(reading.forecast_daily),
            "attribution": ATTRIBUTION,
        }


class PollenOverallSensor(PollenBaseSensor):
    """Overall pollen level (none / low / medium / high) for the location."""

    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = list(LEVEL_LABELS.values())
    _attr_entity_registry_enabled_default = True

    def __init__(
        self,
        coordinator: PollenCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_{OVERALL_SPECIES}"
        self._attr_translation_key = OVERALL_SPECIES

    @property
    def native_value(self) -> str | None:
        return self.coordinator.data.overall_level_label

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data
        return {
            ATTR_PROVIDER: data.provider,
            ATTR_SPECIES: OVERALL_SPECIES,
            ATTR_UNIT: "level",
            ATTR_LEVEL: data.overall_level,
            ATTR_LEVEL_LABEL: data.overall_level_label,
            ATTR_DOMINANT_SPECIES: data.dominant_species,
            ATTR_FORECAST_HOURLY: _hourly_attr(data.overall_hourly()),
            ATTR_FORECAST_DAILY: _daily_attr(data.overall_daily()),
            "attribution": ATTRIBUTION,
        }
