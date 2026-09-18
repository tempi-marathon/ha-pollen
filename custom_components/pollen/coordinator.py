"""Data update coordinator for Pollen."""

from __future__ import annotations

import logging

from aiohttp import ClientSession

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_LATITUDE, CONF_LONGITUDE, DOMAIN, UPDATE_INTERVAL
from .models import PollenSnapshot
from .open_meteo import OpenMeteoError, OutOfCoverageError, fetch_pollen

_LOGGER = logging.getLogger(__name__)


class PollenCoordinator(DataUpdateCoordinator[PollenSnapshot]):
    """Fetch pollen data from the configured provider."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        session: ClientSession,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )
        self.config_entry = entry
        self._session = session

    @property
    def latitude(self) -> float:
        return float(self.config_entry.data[CONF_LATITUDE])

    @property
    def longitude(self) -> float:
        return float(self.config_entry.data[CONF_LONGITUDE])

    async def _async_update_data(self) -> PollenSnapshot:
        try:
            return await fetch_pollen(self._session, self.latitude, self.longitude)
        except OutOfCoverageError as err:
            raise UpdateFailed(str(err)) from err
        except OpenMeteoError as err:
            raise UpdateFailed(str(err)) from err
