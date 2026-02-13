# Landfolk Rentals Calendar Integration for Home Assistant

A custom Home Assistant integration that imports your Landfolk rental bookings as a calendar entity with configurable check-in and check-out times.

## Features

- 📅 Import Landfolk rental bookings from iCal feed
- ⏰ Configurable check-in time (default: 14:00)
- ⏰ Configurable check-out time (default: 11:00)
- 🔄 Automatic updates every hour
- 📱 Works with Home Assistant calendar dashboard
- 📊 Dedicated sensor showing count and list of all upcoming rentals
- � Binary sensor for active rental detection (perfect for "guest mode")
- �🌙 Automatically calculates rental nights and duration
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

1. Download the latest release from GitHub
2. Create a `landfolk_rentals` folder in your `custom_components` directory
3. Copy all Python files (`__init__.py`, `calendar.py`, `sensor.py`, `config_flow.py`, `const.py`) and JSON files (`manifest.json`, `strings.json`) into the `landfolk_rentals` folder
4. Restart Home Assistant

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

Once configured, the integration creates three entities:

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

### Binary Sensor Entity
- **Entity ID**: `binary_sensor.landfolk_active_rental`
- State: ON when a rental is currently active, OFF otherwise
- Attributes: Current rental details (summary, check-in, check-out, nights)
- Perfect for triggering "guest mode" automations

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
  {% if event.booking_id %}
  - 🔖 Booking ID: `{{ event.booking_id }}`
  {% endif %}
  - 🏠 Check-in: {{ as_timestamp(event.start) | timestamp_custom('%A, %B %d at %H:%M', true) }}
  - 🚪 Check-out: {{ as_timestamp(event.end) | timestamp_custom('%A, %B %d at %H:%M', true) }}
  - 🌙 Duration: {{ event.nights }} night{{ 's' if event.nights != 1 else '' }}
  - ⏰ In {{ event.days_until_checkin }} day{{ 's' if event.days_until_checkin != 1 else '' }}
  
    {% endfor %}
  {% else %}
  _No upcoming rentals scheduled_
  {% endif %}
  
  <sub>Last updated: {{ relative_time(strptime(state_attr('sensor.landfolk_upcoming_rentals', 'last_updated'), '%Y-%m-%dT%H:%M:%S.%f%z')) }}</sub>
```

For more dashboard examples, see [dashboard-example.yaml](dashboard-example.yaml).

## Advanced: Guest Mode with Manual Override

If you want to combine automatic rental detection with manual control for personal guests, create a template binary sensor:

### Step 1: Create Helper for Manual Override

Go to **Settings** → **Devices & Services** → **Helpers** → **Create Helper** → **Toggle**
- Name: "Guest Mode Override"
- Entity ID will be: `input_boolean.guest_mode_override`

### Step 2: Create Template Binary Sensor

Add to your `configuration.yaml`:

```yaml
template:
  - binary_sensor:
      - name: "Guest Mode"
        unique_id: guest_mode_combined
        device_class: occupancy
        state: >
          {{ is_state('binary_sensor.landfolk_active_rental', 'on') 
             or is_state('input_boolean.guest_mode_override', 'on') }}
        icon: >
          {% if is_state('input_boolean.guest_mode_override', 'on') %}
            mdi:account-cog
          {% elif is_state('binary_sensor.landfolk_active_rental', 'on') %}
            mdi:home-account
          {% else %}
            mdi:home-outline
          {% endif %}
        attributes:
          source: >
            {% if is_state('input_boolean.guest_mode_override', 'on') %}
              Manual Override
            {% elif is_state('binary_sensor.landfolk_active_rental', 'on') %}
              Active Rental
            {% else %}
              Inactive
            {% endif %}
```

### Step 3: Use in Automations

Now use `binary_sensor.guest_mode` in all your automations:

```yaml
alias: Turn on lights at sunset during guest mode
triggers:
  - platform: sun
    event: sunset
conditions:
  - condition: state
    entity_id: binary_sensor.guest_mode
    state: "on"
actions:
  - service: light.turn_on
    target:
      entity_id: light.outdoor_lights
```

**Benefits:**
- ✅ Automatically detects Landfolk rentals
- ✅ Manual control via toggle for personal guests
- ✅ Single sensor to use in all automations
- ✅ Follows Home Assistant conventions

## Automation Examples

For comprehensive automation examples including guest mode, climate control, security, notifications, and more, see [AUTOMATION_EXAMPLES.md](AUTOMATION_EXAMPLES.md).

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
