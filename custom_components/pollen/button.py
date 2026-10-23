"""Button platform for Pollen."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, REFRESH
from .coordinator import PollenCoordinator
from .entity import PollenEntity

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Pollen buttons from a config entry."""
    coordinator: PollenCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([PollenRefreshButton(coordinator, entry)])


class PollenRefreshButton(PollenEntity, ButtonEntity):
    """Manually request a pollen data refresh."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False
    _attr_icon = "mdi:refresh"

    def __init__(
        self,
        coordinator: PollenCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_{REFRESH}"
        self._attr_translation_key = REFRESH

    @property
    def available(self) -> bool:
        # Stay pressable when the last poll failed (that is when refresh helps).
        return True

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.coordinator.async_request_refresh()
