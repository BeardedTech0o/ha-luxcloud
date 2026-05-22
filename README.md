<div align="center">

# LuxCloud for Home Assistant

**Monitor and control your LuxPower solar inverter and battery storage directly from Home Assistant.**

[![HACS Badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://hacs.xyz)
[![GitHub Release](https://img.shields.io/github/v/release/BeardedTech0o/ha-luxcloud?style=for-the-badge&color=brightgreen)](https://github.com/BeardedTech0o/ha-luxcloud/releases)
[![Validate](https://img.shields.io/github/actions/workflow/status/BeardedTech0o/ha-luxcloud/validate.yml?style=for-the-badge&label=Validate)](https://github.com/BeardedTech0o/ha-luxcloud/actions/workflows/validate.yml)
[![License](https://img.shields.io/github/license/BeardedTech0o/ha-luxcloud?style=for-the-badge)](LICENSE)
[![HA Min Version](https://img.shields.io/badge/Home%20Assistant-2023.4%2B-blue?style=for-the-badge&logo=home-assistant)](https://www.home-assistant.io)

</div>

---

## Overview

LuxCloud connects your **LuxPower** hybrid inverter to Home Assistant via the LuxPower cloud API, giving you real-time monitoring of your solar, battery, and grid power flows — plus full control over charge/discharge behaviour from automations and dashboards.

### What you get

| Platform | Entities |
|:---------|:---------|
| 🌡️ **Sensor** | Solar power, battery power & SOC, grid import/export, home load, PV string voltages & currents, temperatures, daily & lifetime energy totals, inverter status |
| 🔀 **Switch** | AC charge on/off |
| 🔢 **Number** | AC charge current limit, discharge cutoff SOC, charge cutoff SOC |
| 🔘 **Select** | Work mode — Self-use / Feed-in Priority / Backup / Manual |

> All entities are grouped under a single **device** per inverter, named by serial number.

---

## Requirements

| Requirement | Details |
|:------------|:--------|
| Home Assistant | 2023.4 or newer |
| LuxPower account | Free — register in the [LuxPower app](https://www.luxpowertek.com/app.html) |
| LuxPower inverter | Any LXP series with WiFi/LAN dongle connected to the internet |

---

## Installation

### Option A — HACS *(recommended)*

1. Open **HACS** in Home Assistant
2. Click **⋮ → Custom repositories**
3. Add `https://github.com/BeardedTech0o/ha-luxcloud` with category **Integration**
4. Search **LuxCloud** → **Download**
5. Restart Home Assistant

### Option B — Manual

1. Download the [latest release](https://github.com/BeardedTech0o/ha-luxcloud/releases/latest) `.zip`
2. Extract and copy the `luxcloud/` folder to your HA config:

```
config/
└── custom_components/
    └── luxcloud/       ← copy here
        ├── __init__.py
        ├── manifest.json
        └── ...
```

3. Restart Home Assistant

---

## Configuration

1. Go to **Settings → Devices & Services → + Add Integration**
2. Search for **LuxCloud**
3. Complete the form:

| Field | Where to find it |
|:------|:----------------|
| **Email address** | Your LuxPower app login email |
| **Password** | Your LuxPower app password |
| **Inverter serial number** | Label on the side of your inverter, or LuxPower app → Device → Info |
| **Server region** | `EU` for Europe (`eu.luxpowertek.com`), otherwise `Global` |

4. Click **Submit** — credentials are verified before the entry is saved

> **Multiple inverters?** Add the integration once per serial number.

---

## Entities

### ⚡ Live power sensors *(updated every 30 s)*

| Entity | Unit | Description |
|:-------|:----:|:------------|
| Solar Power | W | Total PV generation. Positive = producing |
| Battery Power | W | Positive = charging, negative = discharging |
| Grid Power | W | Positive = importing, negative = exporting |
| Load Power | W | Home consumption |
| Battery State of Charge | % | Current battery level |

### 📊 Daily energy totals *(reset at midnight)*

| Entity | Unit | Description |
|:-------|:----:|:------------|
| Solar Energy Today | kWh | PV generation since midnight |
| Export Energy Today | kWh | Sent to the grid today |
| Import Energy Today | kWh | Drawn from the grid today |
| Battery Charge Today | kWh | Charged into battery today |
| Battery Discharge Today | kWh | Discharged from battery today |

> All energy sensors use `state_class: total_increasing` — compatible with the **Energy Dashboard** out of the box.

### 🎛️ Controls

| Entity | Type | Range | Description |
|:-------|:----:|:-----:|:------------|
| AC Charge | Switch | on/off | Enable/disable grid-to-battery charging |
| AC Charge Current Limit | Number | 0–80 A | Maximum charge current from grid |
| Discharge Cutoff SOC | Number | 5–100 % | Battery stops discharging below this level |
| Charge Cutoff SOC | Number | 5–100 % | Battery stops charging above this level |
| Work Mode | Select | — | Self-use / Feed-in Priority / Backup / Manual |

### 🔧 Diagnostic sensors *(disabled by default)*

Voltages, currents, temperatures, PV string detail, inverter status, and lifetime energy totals. Enable individually in the entity settings if needed.

---

## Energy Dashboard

Add these sensors in **Settings → Dashboards → Energy**:

```
Solar production    →  Solar Energy Today
Grid consumption    →  Import Energy Today
Return to grid      →  Export Energy Today
Battery charged     →  Battery Charge Today
Battery discharged  →  Battery Discharge Today
```

---

## Automation examples

### Forecast-based overnight charging

Charge from the grid when tomorrow's solar forecast is low:

```yaml
automation:
  - alias: "LuxCloud: charge overnight if solar forecast is low"
    trigger:
      - platform: time
        at: "22:00:00"
    condition:
      - condition: numeric_state
        entity_id: sensor.solcast_forecast_tomorrow
        below: 5  # kWh — adjust to your needs
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.luxcloud_SERIAL_ac_charge
      - service: number.set_value
        target:
          entity_id: number.luxcloud_SERIAL_ac_charge_current_limit
        data:
          value: 50
      - service: select.select_option
        target:
          entity_id: select.luxcloud_SERIAL_work_mode
        data:
          option: "Self Use"
```

### Time-of-use tariff switching

Switch to Feed-in Priority during peak export rates:

```yaml
automation:
  - alias: "LuxCloud: export during peak rate"
    trigger:
      - platform: time
        at: "16:00:00"
    action:
      - service: select.select_option
        target:
          entity_id: select.luxcloud_SERIAL_work_mode
        data:
          option: "Feed-in Priority"
  - alias: "LuxCloud: return to self-use after peak"
    trigger:
      - platform: time
        at: "19:00:00"
    action:
      - service: select.select_option
        target:
          entity_id: select.luxcloud_SERIAL_work_mode
        data:
          option: "Self Use"
```

### Force a data refresh

```yaml
service: luxcloud.refresh
```

---

## Supported devices

| Series | Typical models |
|:-------|:--------------|
| LXP Hybrid | 3.6 kW, 5 kW, 6 kW, 7.5 kW, 10 kW, 12 kW |
| LXP AC Couple | All variants |

Requires the LuxPower WiFi/LAN monitoring dongle and an active internet connection. Does **not** require local network access to the inverter.

---

## Known limitations

| Limitation | Details |
|:-----------|:--------|
| Cloud dependency | Requires internet and the LuxPower cloud API to be reachable |
| Poll-only | API has no push/webhook support; minimum update interval is 30 s |
| Control read-back | Write commands are confirmed on the next poll cycle (~30 s) |
| No local mode | Local RS485/Modbus is not currently supported |

---

## Troubleshooting

<details>
<summary><strong>"Cannot connect" during setup</strong></summary>

- Check your inverter is online in the LuxPower app
- Try switching the region between **Global** and **EU**
- Check your Home Assistant has outbound internet access

</details>

<details>
<summary><strong>"Invalid auth" during setup</strong></summary>

- Double-check your email and password (case-sensitive)
- If you signed up with Google or Apple, set a password via **Forgot Password** in the app first

</details>

<details>
<summary><strong>Entities show "Unavailable"</strong></summary>

- The inverter is likely offline (power cut, no internet, dongle unplugged)
- Check the LuxPower app — entities recover automatically when the inverter comes back online

</details>

<details>
<summary><strong>Data not updating / stale values</strong></summary>

- Default poll interval is 30 seconds
- Call `luxcloud.refresh` to force an immediate update
- If persistent, check HA logs for API errors: **Settings → System → Logs**

</details>

<details>
<summary><strong>Need to change credentials or region?</strong></summary>

Go to **Settings → Devices & Services → LuxCloud → ⋮ → Reconfigure** — no need to delete and re-add.

</details>

---

## Removing the integration

**Settings → Devices & Services → LuxCloud → ⋮ → Delete → Confirm**

This removes all entities and the device from Home Assistant. It does not affect your LuxPower account or inverter settings.

---

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting a PR.

```bash
# Install test dependencies
pip install -r requirements_test.txt

# Run tests
pytest tests/

# Validate with hassfest
docker run --rm -v "$(pwd)":/github/workspace homeassistant/hassfest

# Validate with HACS
docker run --rm -v "$(pwd)":/github/workspace ghcr.io/hacs/action
```

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for release history.

---

## License

[MIT](LICENSE) © BeardedTech0o
