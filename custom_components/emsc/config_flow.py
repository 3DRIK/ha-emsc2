"""Config flow for Earthquake Monitoring integration."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.helpers import config_validation as cv

from .const import (
    DOMAIN,
    CONF_MIN_MAGNITUDE,
    CONF_RADIUS,
    DEFAULT_MIN_MAGNITUDE,
    DEFAULT_RADIUS,
)

class ZemetraseniaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Earthquake Monitoring."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            return self.async_create_entry(
                title="Earthquake Monitor",
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_LATITUDE, default=48.1486): float,
                    vol.Required(CONF_LONGITUDE, default=17.1077): float,
                    vol.Required(CONF_RADIUS, default=DEFAULT_RADIUS): float,
                    vol.Required(CONF_MIN_MAGNITUDE, default=DEFAULT_MIN_MAGNITUDE): float,
                }
            ),
            errors=errors,
        )
