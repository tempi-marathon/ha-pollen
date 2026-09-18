"""Config flow for Pollen."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME, DOMAIN
from .open_meteo import OpenMeteoError, OutOfCoverageError, fetch_pollen


class PollenConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Pollen."""

    VERSION = 2

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        hass_lat = self.hass.config.latitude
        hass_lon = self.hass.config.longitude

        if user_input is not None:
            lat = user_input[CONF_LATITUDE]
            lon = user_input[CONF_LONGITUDE]
            await self.async_set_unique_id(f"{lat:.4f}_{lon:.4f}")
            self._abort_if_unique_id_configured()

            session = async_get_clientsession(self.hass)
            try:
                await fetch_pollen(session, lat, lon)
            except OutOfCoverageError:
                errors["base"] = "out_of_coverage"
            except OpenMeteoError:
                errors["base"] = "cannot_connect"
            else:
                name = user_input.get(CONF_NAME) or "Pollen"
                return self.async_create_entry(
                    title=name,
                    data={
                        CONF_NAME: name,
                        CONF_LATITUDE: lat,
                        CONF_LONGITUDE: lon,
                    },
                )

        schema = vol.Schema(
            {
                vol.Optional(CONF_NAME, default="Pollen"): str,
                vol.Required(CONF_LATITUDE, default=hass_lat): cv.latitude,
                vol.Required(CONF_LONGITUDE, default=hass_lon): cv.longitude,
            }
        )
        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
        )
