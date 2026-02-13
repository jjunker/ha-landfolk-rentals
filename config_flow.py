"""Config flow for Landfolk Rentals Calendar integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
import aiohttp
from icalendar import Calendar

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import (
    DOMAIN,
    CONF_CALENDAR_URL,
    CONF_CHECKIN_TIME,
    CONF_CHECKOUT_TIME,
    CONF_EXCLUDE_BLOCKED,
    DEFAULT_CHECKIN_TIME,
    DEFAULT_CHECKOUT_TIME,
    DEFAULT_EXCLUDE_BLOCKED,
)

_LOGGER = logging.getLogger(__name__)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    
    calendar_url = data[CONF_CALENDAR_URL]
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(calendar_url, timeout=10) as response:
                if response.status != 200:
                    raise CannotConnect(f"HTTP {response.status}")
                
                ical_data = await response.text()
                
                # Try to parse the iCal data
                try:
                    calendar = Calendar.from_ical(ical_data)
                except Exception as err:
                    raise InvalidCalendar from err
                
    except aiohttp.ClientError as err:
        raise CannotConnect from err
    
    return {"title": "Landfolk Rentals"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Landfolk Rentals Calendar."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
                
                return self.async_create_entry(title=info["title"], data=user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidCalendar:
                errors["base"] = "invalid_calendar"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        data_schema = vol.Schema(
            {
                vol.Required(CONF_CALENDAR_URL): str,
                vol.Optional(
                    CONF_CHECKIN_TIME, 
                    default=DEFAULT_CHECKIN_TIME
                ): str,
                vol.Optional(
                    CONF_CHECKOUT_TIME, 
                    default=DEFAULT_CHECKOUT_TIME
                ): str,
                vol.Optional(
                    CONF_EXCLUDE_BLOCKED,
                    default=DEFAULT_EXCLUDE_BLOCKED
                ): bool,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidCalendar(HomeAssistantError):
    """Error to indicate the calendar data is invalid."""


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Landfolk Rentals Calendar."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            # Update the config entry with new data
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data={**self.config_entry.data, **user_input}
            )
            # Reload the integration to apply changes
            await self.hass.config_entries.async_reload(self.config_entry.entry_id)
            return self.async_create_entry(title="", data={})

        # Show form with current values
        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_CALENDAR_URL,
                    default=self.config_entry.data.get(CONF_CALENDAR_URL)
                ): str,
                vol.Optional(
                    CONF_CHECKIN_TIME,
                    default=self.config_entry.data.get(CONF_CHECKIN_TIME, DEFAULT_CHECKIN_TIME)
                ): str,
                vol.Optional(
                    CONF_CHECKOUT_TIME,
                    default=self.config_entry.data.get(CONF_CHECKOUT_TIME, DEFAULT_CHECKOUT_TIME)
                ): str,
                vol.Optional(
                    CONF_EXCLUDE_BLOCKED,
                    default=self.config_entry.data.get(CONF_EXCLUDE_BLOCKED, DEFAULT_EXCLUDE_BLOCKED)
                ): bool,
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema
        )

