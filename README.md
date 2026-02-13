# Landfolk Rentals Calendar Integration for Home Assistant

A custom Home Assistant integration that imports your Landfolk rental bookings as a calendar entity with configurable check-in and check-out times.

## Features

- 📅 Import Landfolk rental bookings from iCal feed
- ⏰ Configurable check-in time (default: 14:00)
- ⏰ Configurable check-out time (default: 11:00)
- 🔄 Automatic updates every hour
- 📱 Works with Home Assistant calendar dashboard
- 📊 Dedicated sensor showing count and list of all upcoming rentals
- 🌙 Automatically calculates rental nights and duration
- 🎯 Easy integration with dashboard cards and automations

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Go to "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/jjunker/ha-landfolk-rentals`
6. Category: Integration
7. Click "Add"
8. Search for "Landfolk Rentals Calendar"
9. Click "Download"
10. Restart Home Assistant

### Manual Installation

1. Copy the `landfolk_rentals` folder to your `custom_components` directory
2. Restart Home Assistant

## Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "Landfolk Rentals Calendar"
4. Enter your configuration:
   - **Calendar URL**: Your Landfolk iCal feed URL (from Landfolk platform)
   - **Check-in Time**: Time when guests can check in (format: HH:MM, e.g., 14:00)
   - **Check-out Time**: Time when guests must check out (format: HH:MM, e.g., 11:00)

## Getting Your Calendar URL

1. Log in to your Landfolk account
2. Go to your property settings
3. Find the calendar sync or iCal export section
4. Copy the iCal URL (it should look like: `https://landfolk.com/...`)

## Usage

Once configured, the integration creates two entities:

### Calendar Entity
- **Entity ID**: `calendar.landfolk_rentals`
- Shows the next upcoming booking
- Can be used in the calendar dashboard card
- Displays all bookings when viewing calendar

### Sensor Entity
- **Entity ID**: `sensor.landfolk_upcoming_rentals`
- State: Number of upcoming rentals
- Attributes include full list of upcoming events with details
- Perfect for dashboard lists and automations

### Display Upcoming Rentals List

Add this Markdown card to your dashboard to see all upcoming rentals:

```yaml
type: markdown
content: |
  ## 📅 Upcoming Rentals ({{ states('sensor.landfolk_upcoming_rentals') }})
  
  {% set events = state_attr('sensor.landfolk_upcoming_rentals', 'events') | default([]) %}
  {% if events | length > 0 %}
    {% for event in events[:10] %}
  **{{ loop.index }}. {{ event.summary }}**
  - 🏠 Check-in: {{ as_timestamp(event.start) | timestamp_custom('%A, %B %d at %H:%M', true) }}
  - 🚪 Check-out: {{ as_timestamp(event.end) | timestamp_custom('%A, %B %d at %H:%M', true) }}
  - 🌙 Duration: {{ event.nights }} night{{ 's' if event.nights != 1 else '' }}
  
    {% endfor %}
  {% else %}
  _No upcoming rentals scheduled_
  {% endif %}
  
  <sub>Last updated: {{ relative_time(strptime(state_attr('sensor.landfolk_upcoming_rentals', 'last_updated'), '%Y-%m-%dT%H:%M:%S.%f%z')) }}</sub>
```

### Example Automations

**Notify before guest arrival:**
```yaml
automation:
  - alias: "Notify before guest arrival"
    trigger:
      - platform: calendar
        event: start
        entity_id: calendar.landfolk_rentals
        offset: "-2:0:0"  # 2 hours before check-in
    action:
      - service: notify.mobile_app
        data:
          message: "Guest checking in soon!"
```

**Turn on heating when rentals are upcoming:**
```yaml
automation:
  - alias: "Prepare for guests"
    trigger:
      - platform: numeric_state
        entity_id: sensor.landfolk_upcoming_rentals
        above: 0
    condition:
      - condition: template
        value_template: >
          {% set next = state_attr('sensor.landfolk_upcoming_rentals', 'next_rental') %}
          {{ next and (as_timestamp(next.start) - as_timestamp(now())) < 86400 }}
    action:
      - service: climate.set_temperature
        target:
          entity_id: climate.house
        data:
          temperature: 21
```

## Troubleshooting

### Calendar not updating
- Check that the calendar URL is correct
- Ensure your Home Assistant has internet access
- Check the logs: **Settings** → **System** → **Logs**

### Times showing incorrectly
- Verify check-in/check-out times are in HH:MM format (24-hour)
- Check your Home Assistant timezone settings

## Support

For issues and feature requests, please use the [GitHub Issues](https://github.com/jjunker/ha-landfolk-rentals/issues) page.

## License

This project is licensed under the MIT License.
