"""The Pollen integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .const import DOMAIN, OVERALL_SPECIES

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.const import Platform
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


def _platforms() -> list[Platform]:
    from homeassistant.const import Platform

    return [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Pollen from a config entry."""
    from homeassistant.helpers.aiohttp_client import async_get_clientsession

    from .coordinator import PollenCoordinator

    session = async_get_clientsession(hass)
    coordinator = PollenCoordinator(hass, entry, session)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, _platforms())
    return True


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate config entry to the latest version."""
    if entry.version < 2:
        from homeassistant.helpers import entity_registry as er

        registry = er.async_get(hass)
        unique_id = f"{entry.entry_id}_{OVERALL_SPECIES}"
        entity_id = registry.async_get_entity_id("sensor", DOMAIN, unique_id)
        if entity_id is not None:
            entity = registry.async_get(entity_id)
            if entity is not None and entity.disabled_by is not None:
                registry.async_update_entity(entity_id, disabled_by=None)
                _LOGGER.info(
                    "Re-enabled Overall pollen sensor %s during v2 migration",
                    entity_id,
                )

        hass.config_entries.async_update_entry(entry, version=2)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, _platforms())
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
