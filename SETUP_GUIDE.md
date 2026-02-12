# Setup Guide

## Directory Structure

Your final structure should look like this:

```
config/
└── custom_components/
    └── landfolk_rentals/
        ├── __init__.py
        ├── calendar.py
        ├── config_flow.py
        ├── const.py
        ├── manifest.json
        ├── strings.json
        └── hacs.json
```

## Step-by-Step Installation

### 1. Copy Files to Home Assistant

Copy the entire `landfolk_rentals` folder to your Home Assistant `custom_components` directory.

**Location depends on your installation type:**
- **Home Assistant OS**: `/config/custom_components/`
- **Docker**: Your mapped config volume, typically `/config/custom_components/`
- **Core**: `~/.homeassistant/custom_components/`

### 2. Restart Home Assistant

After copying the files, restart Home Assistant completely.

### 3. Add Integration

1. Go to **Settings** → **Devices & Services**
2. Click the **+ Add Integration** button (bottom right)
3. Search for "Landfolk Rentals Calendar"
4. Click on it to start configuration

### 4. Configure

Enter the following information:

- **Calendar URL**: Your Landfolk iCal feed URL
  - Example: `https://landfolk.com/api/calendar/your-property-id.ics`
  
- **Check-in Time**: When guests can arrive (24-hour format)
  - Example: `14:00` (2:00 PM)
  - Default: 14:00
  
- **Check-out Time**: When guests must leave (24-hour format)
  - Example: `11:00` (11:00 AM)
  - Default: 11:00

### 5. Verify Installation

1. Go to **Settings** → **Devices & Services**
2. Find "Landfolk Rentals Calendar" in your integrations
3. Click on it to see the calendar entity
4. Go to **Overview** dashboard and add a calendar card
5. Select `calendar.landfolk_rentals` as the calendar source

## Using the Calendar

### In Dashboards

Add a calendar card to your dashboard:

```yaml
type: calendar
entities:
  - calendar.landfolk_rentals
```

### In Automations

#### Example 1: Prepare for Guest Arrival

```yaml
automation:
  - alias: "Prepare house before guest arrival"
    trigger:
      platform: calendar
      event: start
      entity_id: calendar.landfolk_rentals
      offset: "-4:0:0"  # 4 hours before check-in
    action:
      - service: climate.set_temperature
        data:
          entity_id: climate.summerhouse
          temperature: 21
      - service: notify.mobile_app
        data:
          title: "Guest Arrival Soon"
          message: "Guest checking in at {{ trigger.calendar_event.start }}"
```

#### Example 2: Notify When Booking Created

```yaml
automation:
  - alias: "New booking notification"
    trigger:
      platform: state
      entity_id: calendar.landfolk_rentals
    condition:
      - condition: template
        value_template: "{{ trigger.to_state.state == 'on' }}"
    action:
      - service: notify.family
        data:
          message: "New Landfolk booking: {{ state_attr('calendar.landfolk_rentals', 'message') }}"
```

#### Example 3: Post-Checkout Tasks

```yaml
automation:
  - alias: "After guest checkout"
    trigger:
      platform: calendar
      event: end
      entity_id: calendar.landfolk_rentals
    action:
      - service: script.cleanup_routine
      - service: notify.cleaner
        data:
          message: "Guest has checked out, property ready for cleaning"
```

### Template Sensors

Create sensors based on calendar state:

```yaml
template:
  - sensor:
      - name: "Days Until Next Guest"
        state: >
          {% set next_event = state_attr('calendar.landfolk_rentals', 'start_time') %}
          {% if next_event %}
            {{ ((as_timestamp(next_event) - as_timestamp(now())) / 86400) | round(0) }}
          {% else %}
            None
          {% endif %}
        unit_of_measurement: "days"
        
  - binary_sensor:
      - name: "House Occupied"
        state: "{{ is_state('calendar.landfolk_rentals', 'on') }}"
```

## Troubleshooting

### Integration Not Showing Up

1. Verify all files are in the correct location
2. Check file permissions (should be readable)
3. Restart Home Assistant completely (not just reload)
4. Check logs: **Settings** → **System** → **Logs**

### Calendar Shows No Events

1. Verify the calendar URL is correct and accessible
2. Test the URL in a web browser - it should download an .ics file
3. Check that the calendar contains events
4. Wait up to 60 minutes for the first sync (or restart)

### Times Are Wrong

1. Check your Home Assistant timezone: **Settings** → **System** → **General**
2. Verify check-in/check-out times are in 24-hour format (HH:MM)
3. The Landfolk feed shows dates in the format `YYYYMMDD`, and this integration applies your configured times

### Common Log Errors

**"Error fetching calendar"**
- Check internet connectivity
- Verify the calendar URL is still valid
- Check if Landfolk's API is accessible

**"Invalid calendar format"**
- The URL might not be pointing to a valid iCal file
- Verify you're using the correct Landfolk calendar export URL

## Advanced Configuration

### Changing Update Interval

By default, the calendar updates every 60 minutes. To change this, edit `const.py`:

```python
# Update interval in minutes
UPDATE_INTERVAL = 30  # Update every 30 minutes
```

### Multiple Properties

To track multiple Landfolk properties, add the integration multiple times with different calendar URLs. Each will create a separate calendar entity.

## Support

If you encounter issues:

1. Check the logs first
2. Search existing GitHub issues
3. Create a new issue with:
   - Home Assistant version
   - Integration version
   - Relevant log entries
   - Steps to reproduce the problem
