"""Config flow for Landfolk Rentals Calendar integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
import aiohttp
from icalendar import Calendar

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import (
    DOMAIN,
    CONF_CALENDAR_URL,
    CONF_CHECKIN_TIME,
    CONF_CHECKOUT_TIME,
    DEFAULT_CHECKIN_TIME,
    DEFAULT_CHECKOUT_TIME,
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
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidCalendar(HomeAssistantError):
    """Error to indicate the calendar data is invalid."""
