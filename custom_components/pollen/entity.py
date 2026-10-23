"""Shared entity helpers for Pollen."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, CONF_NAME, DOMAIN
from .coordinator import PollenCoordinator


def pollen_device_info(entry: ConfigEntry) -> DeviceInfo:
    """Device info for the Pollen service device."""
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.data.get(CONF_NAME) or entry.title or "Pollen",
        manufacturer="Open-Meteo",
        model="Pollen",
        entry_type=DeviceEntryType.SERVICE,
        configuration_url="https://open-meteo.com/en/docs/air-quality-api",
    )


class PollenEntity(CoordinatorEntity[PollenCoordinator]):
    """Base entity tied to a Pollen config entry."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION

    def __init__(
        self,
        coordinator: PollenCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_device_info = pollen_device_info(entry)
