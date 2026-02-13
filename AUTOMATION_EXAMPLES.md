# Automation Examples for Landfolk Rentals Integration

This document contains various automation examples showing how to use the Landfolk Rentals integration in your Home Assistant setup.

## What's New

The integration now includes:
- ✅ **Exclude Blocked Periods** - Configure to ignore "Blocked" calendar entries
- ✅ **Booking ID Extraction** - Automatically parses booking IDs from summaries
- ✅ **Time Calculations** - Days/hours until check-in and checkout
- ✅ **Dynamic Icons** - Icons change based on state
- ✅ **Device Grouping** - All entities grouped under one device

## Table of Contents

- [Guest Mode Automations](#guest-mode-automations)
- [Notification Automations](#notification-automations)
- [Climate Control](#climate-control)
- [Security & Access Control](#security--access-control)
- [Lighting Automations](#lighting-automations)
- [Using New Features](#using-new-features)

## Guest Mode Automations

### Using the Active Rental Sensor Directly

The simplest approach - use `binary_sensor.landfolk_active_rental` directly in conditions:

```yaml
automation:
  - alias: "Turn on lights when someone arrives (guests only)"
    trigger:
      - platform: state
        entity_id: binary_sensor.front_door
        to: "on"
    condition:
      - condition: state
        entity_id: binary_sensor.landfolk_active_rental
        state: "on"
    action:
      - action: light.turn_on
        target:
          entity_id: light.entrance
```

### Sync to input_boolean for Manual Override

Only needed if you want to manually control guest mode independently:

```yaml
automation:
  - alias: "Sync Guest Mode with Active Rental"
    trigger:
      - platform: state
        entity_id: binary_sensor.landfolk_active_rental
    action:
      - action: "input_boolean.turn_{{ 'on' if trigger.to_state.state == 'on' else 'off' }}"
        target:
          entity_id: input_boolean.guest_mode
```

## Notification Automations

### Notify Before Guest Arrival

Send a notification 2 hours before check-in time:

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
          message: "Guest checking in soon at {{ state_attr('calendar.landfolk_rentals', 'start_time') }}!"
```

### Notify When Rental Becomes Active

```yaml
automation:
  - alias: "Guest has arrived"
    trigger:
      - platform: state
        entity_id: binary_sensor.landfolk_active_rental
        to: "on"
    action:
      - service: notify.mobile_app
        data:
          title: "Rental Active"
          message: "{{ state_attr('binary_sensor.landfolk_active_rental', 'summary') }} - Guest has checked in"
```

### Daily Summary of Upcoming Rentals

```yaml
automation:
  - alias: "Daily rental summary"
    trigger:
      - platform: time
        at: "08:00:00"
    condition:
      - condition: numeric_state
        entity_id: sensor.landfolk_upcoming_rentals
        above: 0
    action:
      - service: notify.mobile_app
        data:
          title: "Upcoming Rentals"
          message: >
            You have {{ states('sensor.landfolk_upcoming_rentals') }} upcoming rental(s).
            {% set next = state_attr('sensor.landfolk_upcoming_rentals', 'next_rental') %}
            {% if next %}
            Next: {{ next.summary }} on {{ as_timestamp(next.start) | timestamp_custom('%B %d') }}
            {% endif %}
```

## Climate Control

### Prepare Heating Before Guest Arrival

Turn on heating 24 hours before check-in:

```yaml
automation:
  - alias: "Preheat for guests"
    trigger:
      - platform: calendar
        event: start
        entity_id: calendar.landfolk_rentals
        offset: "-24:0:0"  # 24 hours before
    action:
      - service: climate.set_temperature
        target:
          entity_id: climate.house
        data:
          temperature: 21
          hvac_mode: heat
```

### Adjust Temperature During Rental

```yaml
automation:
  - alias: "Guest climate control"
    trigger:
      - platform: state
        entity_id: binary_sensor.landfolk_active_rental
        to: "on"
    action:
      - service: climate.set_preset_mode
        target:
          entity_id: climate.house
        data:
          preset_mode: comfort

  - alias: "Energy saving after checkout"
    trigger:
      - platform: state
        entity_id: binary_sensor.landfolk_active_rental
        to: "off"
    action:
      - service: climate.set_preset_mode
        target:
          entity_id: climate.house
        data:
          preset_mode: away
```

### Turn on Heating Only When Rentals Are Imminent

```yaml
automation:
  - alias: "Smart heating preparation"
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

## Security & Access Control

### Disable Security System During Rentals

```yaml
automation:
  - alias: "Disable security during rentals"
    trigger:
      - platform: state
        entity_id: binary_sensor.landfolk_active_rental
        to: "on"
    action:
      - action: alarm_control_panel.disarm
        target:
          entity_id: alarm_control_panel.home

  - alias: "Enable security after checkout"
    trigger:
      - platform: state
        entity_id: binary_sensor.landfolk_active_rental
        to: "off"
    action:
      - action: alarm_control_panel.arm_away
        target:
          entity_id: alarm_control_panel.home
```

### Generate Door Code for Guests

```yaml
automation:
  - alias: "Set door code for rental"
    trigger:
      - platform: calendar
        event: start
        entity_id: calendar.landfolk_rentals
        offset: "-4:0:0"  # 4 hours before check-in
    action:
      - service: lock.set_usercode
        target:
          entity_id: lock.front_door
        data:
          code_slot: 5
          usercode: "{{ range(1000, 9999) | random }}"

  - alias: "Clear door code after checkout"
    trigger:
      - platform: calendar
        event: end
        entity_id: calendar.landfolk_rentals
        offset: "2:0:0"  # 2 hours after checkout
    action:
      - service: lock.clear_usercode
        target:
          entity_id: lock.front_door
        data:
          code_slot: 5
```

## Lighting Automations

### Welcome Lights on Check-in Day

```yaml
automation:
  - alias: "Turn on welcome lights"
    trigger:
      - platform: sun
        event: sunset
    condition:
      - condition: state
        entity_id: binary_sensor.landfolk_active_rental
        state: "on"
    action:
      - action: light.turn_on
        target:
          entity_id: light.entrance
        data:
          brightness_pct: 80
```

### Different Motion Sensor Behavior During Rentals

```yaml
automation:
  - alias: "Motion activated lights (rental mode)"
    trigger:
      - platform: state
        entity_id: binary_sensor.hallway_motion
        to: "on"
    condition:
      - condition: state
        entity_id: binary_sensor.landfolk_active_rental
        state: "on"
    action:
      - action: light.turn_on
        target:
          entity_id: light.hallway
        data:
          brightness_pct: 50  # Dimmer for guests at night
```

## Advanced Examples

### Multiple Property Support

If you have multiple Landfolk properties:

```yaml
automation:
  - alias: "Any rental active"
    trigger:
      - platform: state
        entity_id:
          - binary_sensor.landfolk_active_rental_property1
          - binary_sensor.landfolk_active_rental_property2
        to: "on"
    action:
      - service: notify.mobile_app
        data:
          message: "A rental is now active at {{ trigger.to_state.attributes.friendly_name }}"
```

### Integration with Cleaning Service

```yaml
automation:
  - alias: "Schedule cleaning after checkout"
    trigger:
      - platform: calendar
        event: end
        entity_id: calendar.landfolk_rentals
    action:
      - service: calendar.create_event
        target:
          entity_id: calendar.cleaning_schedule
        data:
          summary: "Clean rental property"
          start_date_time: "{{ (as_timestamp(trigger.calendar_event.end) + 3600) | timestamp_custom('%Y-%m-%d %H:%M:%S') }}"
          end_date_time: "{{ (as_timestamp(trigger.calendar_event.end) + 7200) | timestamp_custom('%Y-%m-%d %H:%M:%S') }}"
```

### Dashboard Conditional Cards

Show rental info only when active:

```yaml
type: conditional
conditions:
  - entity: binary_sensor.landfolk_active_rental
    state: "on"
card:
  type: entities
  title: Current Rental
  entities:
    - entity: binary_sensor.landfolk_active_rental
      name: Status
    - type: attribute
      entity: binary_sensor.landfolk_active_rental
      attribute: summary
      name: Booking
    - type: attribute
      entity: binary_sensor.landfolk_active_rental
      attribute: check_out
      name: Check-out
    - type: attribute
      entity: binary_sensor.landfolk_active_rental
      attribute: nights
      name: Nights
```

## Tips

- Use calendar event triggers for actions before/after rentals
- Use the binary sensor for real-time "is rental active now" checks
- Use the sensor for counting and displaying upcoming rentals
- Combine multiple conditions for complex scenarios
- Test automations carefully before deploying to production

---

## Using New Features

### Booking ID in Notifications

```yaml
automation:
  - alias: "Guest checked in with booking ID"
    trigger:
      - platform: state
        entity_id: binary_sensor.landfolk_active_rental
        to: "on"
    action:
      - service: notify.mobile_app
        data:
          title: "Guest Arrival"
          message: >
            Guest for booking {{ state_attr('binary_sensor.landfolk_active_rental', 'booking_id') }} 
            has checked in. They'll stay for {{ state_attr('binary_sensor.landfolk_active_rental', 'nights') }} nights.
```

### Countdown-Based Automations

**Turn on heating 3 days before arrival:**
```yaml
automation:
  - alias: "Start heating preparation"
    trigger:
      - platform: time_pattern
        hours: "/6"  # Check every 6 hours
    condition:
      - condition: template
        value_template: >
          {% set events = state_attr('sensor.landfolk_upcoming_rentals', 'events') | default([]) %}
          {{ events | length > 0 and events[0].days_until_checkin <= 3 }}
    action:
      - service: climate.turn_on
        target:
          entity_id: climate.house
```

**Send reminder 24 hours before checkout:**
```yaml
automation:
  - alias: "Checkout reminder"
    trigger:
      - platform: time_pattern
        hours: "/1"  # Check hourly
    condition:
      - condition: state
        entity_id: binary_sensor.landfolk_active_rental
        state: "on"
      - condition: template
        value_template: >
          {{ state_attr('binary_sensor.landfolk_active_rental', 'hours_until_checkout') <= 24 }}
    action:
      - service: notify.mobile_app
        data:
          message: "Checkout is in {{ state_attr('binary_sensor.landfolk_active_rental', 'hours_until_checkout') }} hours"
```

### Using Exclude Blocked Feature

The integration now excludes "Blocked" periods from rental counts by default. To change this behavior:

1. Go to **Settings** → **Devices & Services**
2. Find "Landfolk Rentals Calendar"
3. Click **Configure**
4. Toggle "Exclude 'Blocked' periods from rental counts"

This means:
- `sensor.landfolk_upcoming_rentals` only counts actual bookings
- `binary_sensor.landfolk_active_rental` won't trigger during blocked periods
- `calendar.landfolk_rentals` still shows all events for visibility

### Tracking Multiple Properties

If you have multiple Landfolk properties, add each as a separate integration instance:

```yaml
automation:
  - alias: "Any property occupied"
    trigger:
      - platform: state
        entity_id:
          - binary_sensor.landfolk_active_rental  # Property 1
          - binary_sensor.landfolk_active_rental_2  # Property 2
        to: "on"
    action:
      - service: notify.mobile_app
        data:
          message: >
            Property {{ trigger.to_state.attributes.friendly_name }} 
            is now occupied (Booking: {{ trigger.to_state.attributes.booking_id }})
```
