"""Data update coordinator for Pollen."""

from __future__ import annotations

import logging

from aiohttp import ClientSession
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import (
    TimestampDataUpdateCoordinator,
    UpdateFailed,
)

from .const import CONF_LATITUDE, CONF_LONGITUDE, DOMAIN, UPDATE_INTERVAL
from .models import PollenSnapshot
from .open_meteo import OpenMeteoError, OutOfCoverageError, fetch_pollen

_LOGGER = logging.getLogger(__name__)


class PollenCoordinator(TimestampDataUpdateCoordinator[PollenSnapshot]):
    """Fetch pollen data from the configured provider."""

    config_entry: ConfigEntry
    last_error: str | None = None

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

    @callback
    def _async_refresh_finished(self) -> None:
        """Update listeners on failure so last_error refreshes on consecutive fails."""
        super()._async_refresh_finished()
        # Parent skips async_update_listeners when already failed; diagnostic
        # entities still need the new last_error written to state.
        if not self.last_update_success:
            self.async_update_listeners()

    async def _async_update_data(self) -> PollenSnapshot:
        try:
            return await fetch_pollen(self._session, self.latitude, self.longitude)
        except OutOfCoverageError as err:
            self.last_error = str(err)
            raise UpdateFailed(str(err)) from err
        except OpenMeteoError as err:
            self.last_error = str(err)
            raise UpdateFailed(str(err)) from err
