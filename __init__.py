"""The Landfolk Rentals Calendar integration."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
import aiohttp
from icalendar import Calendar

from .const import DOMAIN, CONF_CALENDAR_URL, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = ["calendar"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Landfolk Rentals Calendar from a config entry."""
    
    coordinator = LandfolkDataUpdateCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok


class LandfolkDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Landfolk calendar data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize."""
        self.calendar_url = entry.data[CONF_CALENDAR_URL]
        
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=UPDATE_INTERVAL),
        )

    async def _async_update_data(self) -> Calendar:
        """Fetch data from iCal feed."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.calendar_url, timeout=30) as response:
                    if response.status != 200:
                        raise UpdateFailed(f"Error fetching calendar: {response.status}")
                    
                    ical_data = await response.text()
                    calendar = Calendar.from_ical(ical_data)
                    return calendar
                    
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Unexpected error: {err}") from err
