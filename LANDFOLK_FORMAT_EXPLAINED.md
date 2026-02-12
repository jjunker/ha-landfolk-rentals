# Landfolk iCal Format - How It's Parsed

## Your Landfolk iCal Format

```
BEGIN:VEVENT
DTSTAMP:20250828T080833Z
UID:d83e1919-aede-42dd-8183-28cdc082e713
DTSTART;VALUE=DATE:20250829
DTEND;VALUE=DATE:20250831
SUMMARY:Booking #d263b4d4
END:VEVENT
```

## Key Differences from Initial Format

1. **VALUE=DATE**: This is crucial - it means the dates are DATE objects, not DATETIME
2. **Date Format**: `YYYYMMDD` (e.g., 20250829 = August 29, 2025)
3. **No Time Component**: The raw iCal has no time information

## How the Integration Handles It

### Example 1: Booking #d263b4d4
- **Raw Data**: 
  - DTSTART: 20250829 (August 29, 2025)
  - DTEND: 20250831 (August 31, 2025)

- **With Default Times** (check-in: 14:00, check-out: 11:00):
  - Check-in: **August 29, 2025 at 14:00** (2:00 PM)
  - Check-out: **August 31, 2025 at 11:00** (11:00 AM)

- **With Custom Times** (check-in: 16:00, check-out: 10:00):
  - Check-in: **August 29, 2025 at 16:00** (4:00 PM)
  - Check-out: **August 31, 2025 at 10:00** (10:00 AM)

### Example 2: Booking #d6dde96a
- **Raw Data**:
  - DTSTART: 20250912 (September 12, 2025)
  - DTEND: 20250914 (September 14, 2025)

- **With Default Times**:
  - Check-in: **September 12, 2025 at 14:00**
  - Check-out: **September 14, 2025 at 11:00**

## Important iCal Convention

⚠️ **DTEND is EXCLUSIVE** in iCal format:
- A booking from 20250829 to 20250831 means:
  - Guest arrives on August 29
  - Guest leaves on August 31
  - The property is occupied on Aug 29 and Aug 30
  - The property is available again on Aug 31 after checkout

This is correctly handled by the integration!

## How the Code Works

```python
# 1. Parse the date from iCal (e.g., 20250829)
dtstart = component.get("dtstart").dt  # Returns: date(2025, 8, 29)

# 2. Check if it's a date object (not datetime)
if isinstance(dtstart, datetime):
    # Already has time - use as-is (won't happen with Landfolk)
    start = dtstart
else:
    # It's a date - convert to datetime at midnight
    start = datetime.combine(dtstart, datetime.min.time())
    # Result: 2025-08-29 00:00:00
    
    # 3. Apply your configured check-in time (e.g., 14:00)
    start = start.replace(hour=14, minute=0)
    # Result: 2025-08-29 14:00:00

# 4. Make it timezone-aware using Home Assistant's timezone
start = dt_util.as_local(start)
# Result: 2025-08-29 14:00:00+02:00 (for Denmark in summer)
```

## Configuration Examples

When you set up the integration, you'll see:

```
Calendar URL: https://landfolk.com/api/calendar/your-property.ics
Check-in Time: 14:00  ← Users can change this
Check-out Time: 11:00 ← Users can change this
```

### Scenario 1: Standard Danish Summer House Rules
- Check-in: 16:00 (4 PM on Saturday)
- Check-out: 10:00 (10 AM on Saturday)

### Scenario 2: Flexible Times
- Check-in: 15:00 (3 PM)
- Check-out: 12:00 (noon)

### Scenario 3: Full-Day Rental
- Check-in: 12:00 (noon)
- Check-out: 12:00 (noon)

## Calendar Display in Home Assistant

Once configured, your calendar will show:

```
📅 Landfolk Rentals

August 2025
29 Fri  14:00 - 31 Sun 11:00  Booking #d263b4d4
                               (2 nights, 3 days)

September 2025
12 Fri  14:00 - 14 Sun 11:00  Booking #d6dde96a
                               (2 nights, 3 days)
```

## Automation Examples

### Turn on heating 4 hours before guest arrival
```yaml
automation:
  - alias: "Preheat summerhouse"
    trigger:
      platform: calendar
      event: start
      entity_id: calendar.landfolk_rentals
      offset: "-4:0:0"  # 4 hours before 14:00 = triggers at 10:00
    action:
      - service: climate.set_temperature
        data:
          entity_id: climate.summerhouse
          temperature: 21
```

### Get notified day before checkout
```yaml
automation:
  - alias: "Remind about checkout tomorrow"
    trigger:
      platform: calendar
      event: end
      entity_id: calendar.landfolk_rentals
      offset: "-24:0:0"  # 24 hours before 11:00 checkout
    action:
      - service: notify.mobile_app
        data:
          message: "Guest checking out tomorrow at 11:00"
```

## Testing the Integration

1. Copy integration to `custom_components/landfolk_rentals/`
2. Restart Home Assistant
3. Add integration with your Landfolk calendar URL
4. Set your preferred check-in/out times
5. Go to Developer Tools → States
6. Find `calendar.landfolk_rentals`
7. Check the attributes - you'll see the next event with proper times!

The integration correctly handles the VALUE=DATE format from Landfolk and applies your configured times! 🎉
