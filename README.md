<div align="center">

<img src="assets/banner.png" alt="LuxCloud for Home Assistant" width="100%">

### Monitor your LuxPower solar inverter and battery storage from Home Assistant

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5?style=for-the-badge&logo=homeassistantcommunitystore&logoColor=white)](https://hacs.xyz)
[![Release](https://img.shields.io/github/v/release/BeardedTech0o/ha-luxcloud?style=for-the-badge&color=2F81F7)](https://github.com/BeardedTech0o/ha-luxcloud/releases)
[![Validate](https://img.shields.io/github/actions/workflow/status/BeardedTech0o/ha-luxcloud/validate.yml?style=for-the-badge&label=Validate&color=3FB950)](https://github.com/BeardedTech0o/ha-luxcloud/actions/workflows/validate.yml)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2023.4%2B-41BDF5?style=for-the-badge&logo=home-assistant&logoColor=white)](https://www.home-assistant.io)
[![License](https://img.shields.io/github/license/BeardedTech0o/ha-luxcloud?style=for-the-badge&color=8957E5)](LICENSE)

</div>

***

## <img src="assets/icons/hub.svg" width="22" align="top"> Overview

LuxCloud links your **LuxPower** hybrid inverter to Home Assistant through the LuxPower cloud API. You get live visibility of solar production, battery charge and discharge, grid import and export, and household load, all as native Home Assistant entities with no local network access to the inverter required.

Every entity is grouped under a single **device** per inverter, named by serial number.

| | Platform | What it provides |
|:--:|:--|:--|
| <img src="assets/icons/sensors.svg" width="18"> | **Sensor** | Solar power, battery power and state of charge, grid import and export, home load, PV string voltages and currents, temperatures, daily and lifetime energy totals, inverter status |
| <img src="assets/icons/toggle_on.svg" width="18"> | **Switch** | AC charge on and off |
| <img src="assets/icons/speed.svg" width="18"> | **Number** | AC charge current limit, discharge cutoff SOC, charge cutoff SOC |
| <img src="assets/icons/format_list_bulleted.svg" width="18"> | **Select** | Work mode |

> [!IMPORTANT]
> **Control entities are experimental.** The Switch, Number and Select platforms ship with the integration but have not been fully verified. They need a LuxPower account with **installer or owner** permissions. Standard viewer accounts, which is what the LuxPower app creates by default, cannot send write commands and will raise a permissions error. The inverter register names used internally follow LuxPower API conventions and may need adjusting for your firmware.

***

## <img src="assets/icons/checklist.svg" width="22" align="top"> Requirements

| Requirement | Details |
|:--|:--|
| Home Assistant | 2023.4 or newer |
| LuxPower account | Free, register in the [LuxPower app](https://www.luxpowertek.com/app.html) |
| LuxPower inverter | Any LXP series with a WiFi or LAN dongle connected to the internet |

***

## <img src="assets/icons/download.svg" width="22" align="top"> Installation

<details open>
<summary><b>Option A &nbsp;&middot;&nbsp; HACS (recommended)</b></summary>

<br>

1. Open **HACS** in Home Assistant
2. Choose **⋮ → Custom repositories**
3. Add `https://github.com/BeardedTech0o/ha-luxcloud` with the category **Integration**
4. Search for **LuxCloud**, then click **Download**
5. Restart Home Assistant

</details>

<details>
<summary><b>Option B &nbsp;&middot;&nbsp; Manual install</b></summary>

<br>

1. Download the [latest release](https://github.com/BeardedTech0o/ha-luxcloud/releases/latest) archive
2. Copy the `luxcloud/` folder into your Home Assistant configuration:

```text
config/
└── custom_components/
    └── luxcloud/          ← copy here
        ├── __init__.py
        ├── manifest.json
        └── ...
```

3. Restart Home Assistant

</details>

***

## <img src="assets/icons/tune.svg" width="22" align="top"> Configuration

Go to **Settings → Devices & Services → Add Integration**, search for **LuxCloud**, then fill in the form.

| Field | Where to find it |
|:--|:--|
| **Email address** | The email you use to sign in to the LuxPower app |
| **Password** | Your LuxPower account password |
| **Inverter serial number** | On the label on the side of the inverter, or in the LuxPower app under Device → Info |
| **Server region** | `EU` for the European server (`eu.luxpowertek.com`), otherwise `Global` |

Credentials are checked before the entry is saved, so a successful submit means the connection already works.

> [!TIP]
> Running more than one inverter? Add the integration once per serial number. To change credentials or region later, use **Settings → Devices & Services → LuxCloud → ⋮ → Reconfigure**. There is no need to delete and re add the integration.

***

## <img src="assets/icons/sensors.svg" width="22" align="top"> Entities

### <img src="assets/icons/bolt.svg" width="18" align="top"> Live power

Updated every 30 seconds.

| | Entity | Unit | Meaning |
|:--:|:--|:--:|:--|
| <img src="assets/icons/solar_power.svg" width="18"> | Solar Power | W | Total PV generation |
| <img src="assets/icons/battery_charging_full.svg" width="18"> | Battery Power | W | Positive when charging, negative when discharging |
| <img src="assets/icons/electric_meter.svg" width="18"> | Grid Power | W | Positive when importing, negative when exporting |
| <img src="assets/icons/house.svg" width="18"> | Load Power | W | Household consumption |
| <img src="assets/icons/percent.svg" width="18"> | Battery State of Charge | % | Current battery level |

### <img src="assets/icons/donut_small.svg" width="18" align="top"> Daily energy

Reset at midnight.

| Entity | Unit | Meaning |
|:--|:--:|:--|
| Solar Energy Today | kWh | PV generation since midnight |
| Export Energy Today | kWh | Sent to the grid today |
| Import Energy Today | kWh | Drawn from the grid today |
| Battery Charge Today | kWh | Charged into the battery today |
| Battery Discharge Today | kWh | Discharged from the battery today |

All energy sensors use `state_class: total_increasing`, so they work with the Energy Dashboard straight away.

### <img src="assets/icons/admin_panel_settings.svg" width="18" align="top"> Controls

Experimental, and only available to installer or owner accounts.

| Entity | Platform | Range | Effect |
|:--|:--:|:--:|:--|
| AC Charge | Switch | on, off | Enable or disable grid to battery charging |
| AC Charge Current Limit | Number | 0 to 80 A | Maximum charge current drawn from the grid |
| Discharge Cutoff SOC | Number | 5 to 100 % | Battery stops discharging below this level |
| Charge Cutoff SOC | Number | 5 to 100 % | Battery stops charging above this level |
| Work Mode | Select | 4 options | `Self Use`, `Feed-in Priority`, `Backup`, `Manual` |

If a control does nothing or reports an error, check your account role in the LuxPower portal first. Viewer accounts have no write access.

### <img src="assets/icons/info.svg" width="18" align="top"> Diagnostics

Disabled by default and enabled individually in the entity settings: PV string power, voltages, currents, EPS power, inverter, battery and radiator temperatures, inverter status, work mode readout, and lifetime energy totals.

***

## <img src="assets/icons/donut_small.svg" width="22" align="top"> Energy Dashboard

Map these sensors in **Settings → Dashboards → Energy**.

| Energy Dashboard slot | LuxCloud sensor |
|:--|:--|
| Solar production | Solar Energy Today |
| Grid consumption | Import Energy Today |
| Return to grid | Export Energy Today |
| Battery charged | Battery Charge Today |
| Battery discharged | Battery Discharge Today |

***

## <img src="assets/icons/smart_toy.svg" width="22" align="top"> Services and automations

### <img src="assets/icons/sync_alt.svg" width="18" align="top"> Force a refresh

Skips the wait for the next scheduled poll.

```yaml
service: luxcloud.refresh
```

### <img src="assets/icons/schedule.svg" width="18" align="top"> Alert on a low battery

```yaml
automation:
  - alias: "LuxCloud: low battery alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.SERIAL_soc
        below: 20
    action:
      - service: notify.mobile_app
        data:
          message: "Battery is at {{ states('sensor.SERIAL_soc') }}%"
```

Replace `SERIAL` with your own inverter serial number. Examples that drive the inverter controls are deliberately left out, since those entities need an installer or owner account and are not yet verified.

***

## <img src="assets/icons/memory.svg" width="22" align="top"> Supported hardware

| Series | Typical models |
|:--|:--|
| LXP Hybrid | 3.6 kW, 5 kW, 6 kW, 7.5 kW, 10 kW, 12 kW |
| LXP AC Couple | All variants |

A LuxPower WiFi or LAN monitoring dongle and an active internet connection are required. Local network access to the inverter is not.

***

## <img src="assets/icons/report.svg" width="22" align="top"> Known limitations

| Limitation | Details |
|:--|:--|
| Cloud dependency | The LuxPower cloud API has to be reachable, so an internet outage stops updates |
| Polling only | The API offers no push or webhook support, and 30 seconds is the shortest sensible interval |
| Controls need an installer account | Viewer accounts cannot send write commands and will fail with a permissions error |
| Controls unverified | Write register names follow LuxPower API conventions and have not been tested against every firmware version |
| Delayed confirmation | A control change is reflected in Home Assistant on the next poll, roughly 30 seconds later |
| No local mode | Local RS485 and Modbus access is not supported |

***

## <img src="assets/icons/handyman.svg" width="22" align="top"> Troubleshooting

<details>
<summary><b>Cannot connect during setup</b></summary>

<br>

* Confirm the inverter shows as online in the LuxPower app
* Try the other server region, **Global** or **EU**
* Confirm Home Assistant has outbound internet access

</details>

<details>
<summary><b>Invalid auth during setup</b></summary>

<br>

* Recheck the email and password, both are case sensitive
* If you registered with Google or Apple, set a password first using **Forgot Password** in the app

</details>

<details>
<summary><b>Entities show as unavailable</b></summary>

<br>

* The inverter is almost certainly offline: power cut, no internet, or an unplugged dongle
* Check the LuxPower app. Entities recover on their own once the inverter reports in again

</details>

<details>
<summary><b>Values look stale</b></summary>

<br>

* The poll interval is 30 seconds by default
* Call `luxcloud.refresh` to pull fresh data immediately
* If it persists, look for API errors in **Settings → System → Logs**

</details>

<details>
<summary><b>Controls do nothing</b></summary>

<br>

* Check your account role in the LuxPower portal. Viewer accounts have no write access
* Confirm the change on the next poll rather than instantly
* Report the firmware version in an issue if the register appears to be wrong

</details>

***

## <img src="assets/icons/delete_forever.svg" width="22" align="top"> Removing the integration

Go to **Settings → Devices & Services → LuxCloud → ⋮ → Delete**, then confirm.

Every entity and the device are removed from Home Assistant. Your LuxPower account and the inverter settings are untouched.

***

## <img src="assets/icons/code.svg" width="22" align="top"> Contributing

Contributions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request.

```bash
# Install test dependencies
pip install -r requirements_test.txt

# Run the test suite
pytest tests/

# Validate with hassfest
docker run --rm -v "$(pwd)":/github/workspace homeassistant/hassfest

# Validate with HACS
docker run --rm -v "$(pwd)":/github/workspace ghcr.io/hacs/action
```

***

## <img src="assets/icons/history.svg" width="22" align="top"> Changelog

Release history lives in [CHANGELOG.md](CHANGELOG.md).

***

## <img src="assets/icons/balance.svg" width="22" align="top"> License

[MIT](LICENSE) © BeardedTech0o

Icons are Google Material Symbols, licensed under Apache 2.0.

<div align="center">

### <img src="assets/icons/favorite.svg" width="20" align="top"> Support the project

If LuxCloud is useful to you, a coffee is always appreciated.

[![Buy Me a Coffee](https://img.buymeacoffee.com/button-api/?text=Buy%20me%20a%20coffee&emoji=&slug=nullobj&button_colour=FFDD00&font_colour=000000&font_family=Cookie&outline_colour=000000&coffee_colour=ffffff)](https://www.buymeacoffee.com/nullobj)

</div>
