"""Calendar platform for Landfolk Rentals."""
from __future__ import annotations

from datetime import datetime, timedelta
import logging

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
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
    """Set up the Landfolk Rentals calendar platform."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    async_add_entities([LandfolkCalendar(coordinator, config_entry)], True)


class LandfolkCalendar(CalendarEntity):
    """Representation of a Landfolk Rentals calendar."""

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        """Initialize the calendar."""
        self.coordinator = coordinator
        self._config_entry = config_entry
        self._attr_name = "Landfolk Rentals"
        self._attr_unique_id = f"{DOMAIN}_{config_entry.entry_id}"
        self._event: CalendarEvent | None = None
        
        # Get configurable check-in/out times
        self._checkin_time = config_entry.data.get(
            CONF_CHECKIN_TIME, DEFAULT_CHECKIN_TIME
        )
        self._checkout_time = config_entry.data.get(
            CONF_CHECKOUT_TIME, DEFAULT_CHECKOUT_TIME
        )

    @property
    def event(self) -> CalendarEvent | None:
        """Return the next upcoming event."""
        return self._event

    async def async_update(self) -> None:
        """Update the calendar entity."""
        await self.coordinator.async_request_refresh()
        
        calendar = self.coordinator.data
        if not calendar:
            return
        
        now = dt_util.now()
        events = []
        
        # Parse all events from the calendar
        for component in calendar.walk():
            if component.name == "VEVENT":
                event = self._parse_event(component)
                if event and event.start >= now:
                    events.append(event)
        
        # Sort events by start time and get the next one
        if events:
            events.sort(key=lambda e: e.start)
            self._event = events[0]
        else:
            self._event = None

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        """Return calendar events within a datetime range."""
        calendar = self.coordinator.data
        if not calendar:
            return []
        
        events = []
        
        for component in calendar.walk():
            if component.name == "VEVENT":
                event = self._parse_event(component)
                if event and event.start < end_date and event.end > start_date:
                    events.append(event)
        
        return sorted(events, key=lambda e: e.start)

    def _parse_event(self, component) -> CalendarEvent | None:
        """Parse an iCal event component into a CalendarEvent."""
        try:
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
                # Already a datetime (shouldn't happen with Landfolk, but handle it)
                start = dtstart
            else:
                # Date only - apply check-in time
                # Create datetime at midnight, then set to check-in time
                start = datetime.combine(dtstart, datetime.min.time())
                start = start.replace(hour=checkin_hour, minute=checkin_minute)
            
            if isinstance(dtend, datetime):
                # Already a datetime (shouldn't happen with Landfolk, but handle it)
                end = dtend
            else:
                # Date only - apply check-out time
                # Note: iCal DTEND is exclusive, so if booking is 20250829-20250831,
                # checkout is on 20250831 at the configured time
                end = datetime.combine(dtend, datetime.min.time())
                end = end.replace(hour=checkout_hour, minute=checkout_minute)
            
            # Make timezone-aware using Home Assistant's timezone
            if start.tzinfo is None:
                start = dt_util.as_local(start)
            if end.tzinfo is None:
                end = dt_util.as_local(end)
            
            return CalendarEvent(
                start=start,
                end=end,
                summary=summary,
                uid=uid,
            )
            
        except Exception as err:
            _LOGGER.error("Error parsing event: %s", err)
            return None
