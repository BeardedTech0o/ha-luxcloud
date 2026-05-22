# ha-solar-integration — LuxPower

A Home Assistant custom integration for **LuxPower** solar inverters (LXP series) using the LuxPower cloud API.

## Features

| Platform | Entities |
|----------|----------|
| **Sensor** | Solar power, battery power/SOC, grid power, load power, PV string voltages & currents, temperatures, daily & lifetime energy totals, inverter status |
| **Switch** | AC Charge enable/disable |
| **Number** | AC charge current limit, discharge cutoff SOC, charge cutoff SOC |
| **Select** | Work mode (Self-use / Feed-in Priority / Backup / Manual) |

## Installation

### HACS (recommended)
1. Add this repo as a custom HACS repository (category: Integration).
2. Search for **LuxPower** and install.
3. Restart Home Assistant.

### Manual
Copy `custom_components/luxpower/` into your HA `config/custom_components/` directory and restart.

## Configuration

Go to **Settings → Devices & Services → Add Integration → LuxPower**.

You will need:
- LuxPower cloud account **email** and **password**
- Your inverter **serial number** (found on the inverter label or in the LuxPower app)
- **Server region** — `global` (`openapi.luxpowertek.com`) or `eu` (`eu.luxpowertek.com`)

## Automation example — solar-forecast charge control

```yaml
automation:
  - alias: "Charge battery from grid when tomorrow looks cloudy"
    trigger:
      - platform: time
        at: "22:00:00"
    condition:
      - condition: numeric_state
        entity_id: sensor.solcast_forecast_tomorrow
        below: 5  # kWh
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.luxpower_SERIAL_ac_charge
      - service: number.set_value
        target:
          entity_id: number.luxpower_SERIAL_ac_charge_current_limit
        data:
          value: 50
```

## Data refresh

Entities update every **30 seconds** by default (configurable via `const.py`).

## Supported models

Any LuxPower inverter that supports the LuxPower cloud API, including the LXP series hybrid inverters (3kW – 12kW) with battery storage.
