"""Binary sensor platform for Landfolk Rentals."""
from __future__ import annotations

from datetime import datetime
import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    CONF_CHECKIN_TIME,
    CONF_CHECKOUT_TIME,
    DEFAULT_CHECKIN_TIME,
    DEFAULT_CHECKOUT_TIME,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Landfolk Rentals binary sensor platform."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    async_add_entities([LandfolkActiveRentalSensor(coordinator, config_entry)], True)


class LandfolkActiveRentalSensor(BinarySensorEntity):
    """Binary sensor that indicates if there's an active rental right now."""

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        """Initialize the binary sensor."""
        self.coordinator = coordinator
        self._config_entry = config_entry
        self._attr_name = "Landfolk Active Rental"
        self._attr_unique_id = f"{DOMAIN}_{config_entry.entry_id}_active"
        self._attr_device_class = BinarySensorDeviceClass.OCCUPANCY
        self._attr_icon = "mdi:home-account"
        
        # Get configurable check-in/out times
        self._checkin_time = config_entry.data.get(
            CONF_CHECKIN_TIME, DEFAULT_CHECKIN_TIME
        )
        self._checkout_time = config_entry.data.get(
            CONF_CHECKOUT_TIME, DEFAULT_CHECKOUT_TIME
        )
        
        self._current_event = None

    @property
    def is_on(self) -> bool:
        """Return true if there's an active rental."""
        return self._current_event is not None

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional attributes."""
        if self._current_event:
            return {
                "summary": self._current_event["summary"],
                "check_in": self._current_event["start"].isoformat(),
                "check_out": self._current_event["end"].isoformat(),
                "nights": (self._current_event["end"].date() - self._current_event["start"].date()).days,
            }
        return {}

    async def async_update(self) -> None:
        """Update the binary sensor."""
        await self.coordinator.async_request_refresh()
        
        calendar = self.coordinator.data
        if not calendar:
            self._current_event = None
            return
        
        now = dt_util.now()
        
        # Check if we're currently within any event
        for component in calendar.walk():
            if component.name == "VEVENT":
                event = self._parse_event(component)
                if event and event["start"] <= now < event["end"]:
                    self._current_event = event
                    return
        
        # No active rental found
        self._current_event = None

    def _parse_event(self, component) -> dict | None:
        """Parse an iCal event component into a dict."""
        try:
            from datetime import datetime, timedelta
            
            summary = str(component.get("summary", "Booking"))
            uid = str(component.get("uid", ""))
            
            # Get start and end datetime
            dtstart = component.get("dtstart").dt
            dtend = component.get("dtend").dt
            
            # Parse the configured check-in/out times
            checkin_hour, checkin_minute = map(int, self._checkin_time.split(":"))
            checkout_hour, checkout_minute = map(int, self._checkout_time.split(":"))
            
            # Landfolk uses VALUE=DATE format, so dtstart/dtend are date objects, not datetime
            if isinstance(dtstart, datetime):
                start = dtstart
            else:
                # Date only - apply check-in time
                start = datetime.combine(dtstart, datetime.min.time())
                start = start.replace(hour=checkin_hour, minute=checkin_minute)
            
            if isinstance(dtend, datetime):
                end = dtend
            else:
                # Date only - apply check-out time
                # Landfolk's DTEND represents the actual checkout date (not exclusive)
                end = datetime.combine(dtend, datetime.min.time())
                end = end.replace(hour=checkout_hour, minute=checkout_minute)
            
            # Make timezone-aware using Home Assistant's timezone
            if start.tzinfo is None:
                start = dt_util.as_local(start)
            if end.tzinfo is None:
                end = dt_util.as_local(end)
            
            return {
                "summary": summary,
                "uid": uid,
                "start": start,
                "end": end,
            }
            
        except Exception as err:
            _LOGGER.error("Error parsing event: %s", err)
            return None
