"""LuxCloud sensor entities."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, INVERTER_STATUS, WORK_MODES
from .coordinator import LuxCloudCoordinator


@dataclass(frozen=True)
class LuxSensorDescription(SensorEntityDescription):
    """Extends SensorEntityDescription with a value transformer."""

    value_fn: Any = None  # callable(raw_data) -> value


def _work_mode_name(raw: dict) -> str | None:
    val = raw.get("work_mode")
    if val is None:
        return None
    return WORK_MODES.get(int(val), str(val))


def _status_name(raw: dict) -> str | None:
    val = raw.get("status")
    if val is None:
        return None
    return INVERTER_STATUS.get(int(val), str(val))


def _kwh(key: str):
    return lambda raw: raw.get(key)


def _w(key: str):
    return lambda raw: raw.get(key)


def _v(key: str):
    return lambda raw: raw.get(key)


def _a(key: str):
    return lambda raw: raw.get(key)


def _pct(key: str):
    return lambda raw: raw.get(key)


def _temp(key: str):
    return lambda raw: raw.get(key)


SENSOR_DESCRIPTIONS: tuple[LuxSensorDescription, ...] = (
    # ── Power (instantaneous) ──────────────────────────────────────────
    LuxSensorDescription(
        key="p_pv",
        name="Solar Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_w("p_pv"),
        icon="mdi:solar-power",
    ),
    LuxSensorDescription(
        key="p_pv1",
        name="Solar Power String 1",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_w("p_pv1"),
        icon="mdi:solar-panel",
        entity_registry_enabled_default=False,
    ),
    LuxSensorDescription(
        key="p_pv2",
        name="Solar Power String 2",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_w("p_pv2"),
        icon="mdi:solar-panel",
        entity_registry_enabled_default=False,
    ),
    LuxSensorDescription(
        key="p_battery",
        name="Battery Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_w("p_battery"),
        icon="mdi:battery-charging",
    ),
    LuxSensorDescription(
        key="p_grid",
        name="Grid Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_w("p_grid"),
        icon="mdi:transmission-tower",
    ),
    LuxSensorDescription(
        key="p_load",
        name="Load Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_w("p_load"),
        icon="mdi:home-lightning-bolt",
    ),
    LuxSensorDescription(
        key="p_eps",
        name="EPS Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_w("p_eps"),
        icon="mdi:power-socket",
        entity_registry_enabled_default=False,
    ),
    # ── Battery ───────────────────────────────────────────────────────
    LuxSensorDescription(
        key="soc",
        name="Battery State of Charge",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_pct("soc"),
    ),
    # ── Voltage ───────────────────────────────────────────────────────
    LuxSensorDescription(
        key="v_pv1",
        name="PV Voltage String 1",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_v("v_pv1"),
        entity_registry_enabled_default=False,
    ),
    LuxSensorDescription(
        key="v_pv2",
        name="PV Voltage String 2",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_v("v_pv2"),
        entity_registry_enabled_default=False,
    ),
    LuxSensorDescription(
        key="v_bat",
        name="Battery Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_v("v_bat"),
        entity_registry_enabled_default=False,
    ),
    LuxSensorDescription(
        key="v_ac_r",
        name="AC Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_v("v_ac_r"),
        entity_registry_enabled_default=False,
    ),
    # ── Current ───────────────────────────────────────────────────────
    LuxSensorDescription(
        key="i_pv1",
        name="PV Current String 1",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_a("i_pv1"),
        entity_registry_enabled_default=False,
    ),
    LuxSensorDescription(
        key="i_pv2",
        name="PV Current String 2",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_a("i_pv2"),
        entity_registry_enabled_default=False,
    ),
    LuxSensorDescription(
        key="i_bat",
        name="Battery Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_a("i_bat"),
        entity_registry_enabled_default=False,
    ),
    # ── Temperature ───────────────────────────────────────────────────
    LuxSensorDescription(
        key="t_inner",
        name="Inverter Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_temp("t_inner"),
    ),
    LuxSensorDescription(
        key="t_bat",
        name="Battery Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_temp("t_bat"),
    ),
    LuxSensorDescription(
        key="t_rad1",
        name="Radiator Temperature 1",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_temp("t_rad1"),
        entity_registry_enabled_default=False,
    ),
    # ── Daily energy ──────────────────────────────────────────────────
    LuxSensorDescription(
        key="e_pv_day",
        name="Solar Energy Today",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=_kwh("e_pv_day"),
        icon="mdi:solar-power",
    ),
    LuxSensorDescription(
        key="e_to_grid_day",
        name="Export Energy Today",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=_kwh("e_to_grid_day"),
        icon="mdi:transmission-tower-export",
    ),
    LuxSensorDescription(
        key="e_to_user_day",
        name="Import Energy Today",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=_kwh("e_to_user_day"),
        icon="mdi:transmission-tower-import",
    ),
    LuxSensorDescription(
        key="e_discharge_day",
        name="Battery Discharge Today",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=_kwh("e_discharge_day"),
        icon="mdi:battery-minus",
    ),
    LuxSensorDescription(
        key="e_charge_day",
        name="Battery Charge Today",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=_kwh("e_charge_day"),
        icon="mdi:battery-plus",
    ),
    LuxSensorDescription(
        key="e_eps_day",
        name="EPS Energy Today",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=_kwh("e_eps_day"),
        entity_registry_enabled_default=False,
    ),
    # ── Lifetime energy ───────────────────────────────────────────────
    LuxSensorDescription(
        key="e_pv_all",
        name="Solar Energy Total",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=_kwh("e_pv_all"),
        icon="mdi:solar-power",
        entity_registry_enabled_default=False,
    ),
    LuxSensorDescription(
        key="e_to_grid_all",
        name="Export Energy Total",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=_kwh("e_to_grid_all"),
        entity_registry_enabled_default=False,
    ),
    LuxSensorDescription(
        key="e_to_user_all",
        name="Import Energy Total",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=_kwh("e_to_user_all"),
        entity_registry_enabled_default=False,
    ),
    LuxSensorDescription(
        key="e_discharge_all",
        name="Battery Discharge Total",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=_kwh("e_discharge_all"),
        entity_registry_enabled_default=False,
    ),
    LuxSensorDescription(
        key="e_charge_all",
        name="Battery Charge Total",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=_kwh("e_charge_all"),
        entity_registry_enabled_default=False,
    ),
    # ── Status / mode ─────────────────────────────────────────────────
    LuxSensorDescription(
        key="status",
        name="Inverter Status",
        value_fn=_status_name,
        icon="mdi:information-outline",
    ),
    LuxSensorDescription(
        key="work_mode",
        name="Work Mode",
        value_fn=_work_mode_name,
        icon="mdi:cog",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: LuxCloudCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        LuxCloudSensor(coordinator, entry, desc)
        for desc in SENSOR_DESCRIPTIONS
    )


class LuxCloudSensor(CoordinatorEntity[LuxCloudCoordinator], SensorEntity):
    """A single LuxCloud sensor."""

    entity_description: LuxSensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: LuxCloudCoordinator,
        entry: ConfigEntry,
        description: LuxSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        serial = entry.data["serial_number"]
        self._attr_unique_id = f"{serial}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, serial)},
            "name": f"LuxCloud {serial}",
            "manufacturer": "LuxCloud",
            "model": "Solar Inverter",
            "configuration_url": "https://openapi.luxpowertek.com",
        }

    @property
    def native_value(self):
        if self.coordinator.data is None:
            return None
        fn = self.entity_description.value_fn
        if fn is None:
            return None
        return fn(self.coordinator.data)
