"""Sensor platform for Landfolk Rentals."""
from __future__ import annotations

from datetime import datetime
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Landfolk Rentals sensor platform."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    async_add_entities([LandfolkUpcomingRentalsSensor(coordinator, config_entry)], True)


class LandfolkUpcomingRentalsSensor(SensorEntity):
    """Sensor that shows count and details of upcoming rentals."""

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        self.coordinator = coordinator
        self._config_entry = config_entry
        self._attr_name = "Landfolk Upcoming Rentals"
        self._attr_unique_id = f"{DOMAIN}_{config_entry.entry_id}_upcoming"
        self._attr_icon = "mdi:calendar-multiple"
        self._attr_native_unit_of_measurement = "rentals"
        
        # Get configurable check-in/out times
        from .const import (
            CONF_CHECKIN_TIME,
            CONF_CHECKOUT_TIME,
            CONF_EXCLUDE_BLOCKED,
            DEFAULT_CHECKIN_TIME,
            DEFAULT_CHECKOUT_TIME,
            DEFAULT_EXCLUDE_BLOCKED,
        )
        self._checkin_time = config_entry.data.get(
            CONF_CHECKIN_TIME, DEFAULT_CHECKIN_TIME
        )
        self._checkout_time = config_entry.data.get(
            CONF_CHECKOUT_TIME, DEFAULT_CHECKOUT_TIME
        )
        self._exclude_blocked = config_entry.data.get(
            CONF_EXCLUDE_BLOCKED, DEFAULT_EXCLUDE_BLOCKED
        )

    @property
    def native_value(self) -> int:
        """Return the number of upcoming rentals."""
        events = self._get_upcoming_events()
        return len(events)

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional attributes."""
        events = self._get_upcoming_events()
        
        # Format events for easy consumption in templates
        formatted_events = []
        for event in events[:50]:  # Limit to 50 events to avoid attribute size issues
            # Calculate nights (date difference, not time difference)
            checkin_date = event["start"].date()
            checkout_date = event["end"].date()
            nights = (checkout_date - checkin_date).days
            
            formatted_events.append({
                "summary": event["summary"],
                "start": event["start"].isoformat(),
                "end": event["end"].isoformat(),
                "nights": nights,
                "duration_days": (event["end"] - event["start"]).days,
                "duration_hours": (event["end"] - event["start"]).seconds // 3600,
            })
        
        next_event = formatted_events[0] if formatted_events else None
        
        return {
            "events": formatted_events,
            "next_rental": next_event,
            "last_updated": dt_util.now().isoformat(),
        }

    async def async_update(self) -> None:
        """Update the sensor."""
        await self.coordinator.async_request_refresh()

    def _get_upcoming_events(self) -> list[dict]:
        """Get all upcoming events from the calendar."""
        calendar = self.coordinator.data
        if not calendar:
            return []
        
        now = dt_util.now()
        events = []
        
        # Parse all events from the calendar
        for component in calendar.walk():
            if component.name == "VEVENT":
                event = self._parse_event(component)
                if event and event["start"] >= now:
                    # Filter blocked events if configured
                    if self._exclude_blocked and "blocked" in event["summary"].lower():
                        continue
                    events.append(event)
        
        # Sort events by start time
        events.sort(key=lambda e: e["start"])
        return events

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
