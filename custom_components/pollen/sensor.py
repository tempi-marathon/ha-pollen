"""Sensor platform for Pollen."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    ATTR_DOMINANT_SPECIES,
    ATTR_FORECAST_DAILY,
    ATTR_FORECAST_HOURLY,
    ATTR_IN_COVERAGE,
    ATTR_LATITUDE,
    ATTR_LEVEL,
    ATTR_LEVEL_LABEL,
    ATTR_LONGITUDE,
    ATTR_PROVIDER,
    ATTR_SPECIES,
    ATTR_UNIT,
    ATTRIBUTION,
    DATA_TIME,
    DOMAIN,
    LAST_ERROR,
    LAST_FETCH,
    OVERALL_SPECIES,
    UNIT_OF_MEASUREMENT_GRAINS,
)
from .coordinator import PollenCoordinator
from .entity import PollenEntity
from .levels import LEVEL_LABELS
from .models import DailyPeak, ForecastPoint, SpeciesReading
from .times import parse_generated_at

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Pollen sensors from a config entry."""
    coordinator: PollenCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = [
        PollenOverallSensor(coordinator, entry),
        PollenLastFetchSensor(coordinator, entry),
        PollenDataTimeSensor(coordinator, entry),
        PollenLastErrorSensor(coordinator, entry),
    ]
    for species in coordinator.data.readings:
        entities.append(PollenSpeciesSensor(coordinator, entry, species))
    async_add_entities(entities)


def _hourly_attr(points: tuple[ForecastPoint, ...]) -> list[dict[str, Any]]:
    return [{"t": p.t, "value": p.value} for p in points]


def _daily_attr(peaks: tuple[DailyPeak, ...]) -> list[dict[str, Any]]:
    return [{"date": p.date, "value": p.value} for p in peaks]


class PollenBaseSensor(PollenEntity, SensorEntity):
    """Shared base for pollen sensors."""

    _attr_icon = "mdi:flower-pollen"


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


class PollenLastFetchSensor(PollenBaseSensor):
    """When the integration last successfully fetched from the provider."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False
    _attr_icon = "mdi:clock-check"

    def __init__(
        self,
        coordinator: PollenCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_{LAST_FETCH}"
        self._attr_translation_key = LAST_FETCH

    @property
    def available(self) -> bool:
        # Keep last success time visible during a failed poll.
        return True

    @property
    def native_value(self) -> datetime | None:
        return self.coordinator.last_update_success_time

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        data = self.coordinator.data
        if data is None:
            return None
        return {
            ATTR_PROVIDER: data.provider,
            ATTR_LATITUDE: data.latitude,
            ATTR_LONGITUDE: data.longitude,
            ATTR_IN_COVERAGE: data.in_coverage,
        }


class PollenDataTimeSensor(PollenBaseSensor):
    """Provider timestamp for the current pollen hour."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False
    _attr_icon = "mdi:clock-outline"

    def __init__(
        self,
        coordinator: PollenCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_{DATA_TIME}"
        self._attr_translation_key = DATA_TIME

    @property
    def available(self) -> bool:
        # Keep provider data time visible during a failed poll.
        return True

    @property
    def native_value(self) -> datetime | None:
        data = self.coordinator.data
        if data is None:
            return None
        return parse_generated_at(data.generated_at)


class PollenLastErrorSensor(PollenBaseSensor):
    """Last failed update error message (persists after recovery)."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False
    _attr_icon = "mdi:alert-circle-outline"

    def __init__(
        self,
        coordinator: PollenCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_{LAST_ERROR}"
        self._attr_translation_key = LAST_ERROR

    @property
    def available(self) -> bool:
        # Stay available even when the coordinator's last update failed.
        return True

    @property
    def native_value(self) -> str | None:
        return self.coordinator.last_error
