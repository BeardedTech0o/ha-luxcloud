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
    EntityCategory,
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
from .entity import luxcloud_device_info

PARALLEL_UPDATES = 0


@dataclass(frozen=True)
class LuxSensorDescription(SensorEntityDescription):
    value_fn: Any = None


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


SENSOR_DESCRIPTIONS: tuple[LuxSensorDescription, ...] = (
    # ── Power (primary) ───────────────────────────────────────────────
    LuxSensorDescription(
        key="p_pv",
        translation_key="p_pv",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda raw: raw.get("p_pv"),
    ),
    LuxSensorDescription(
        key="p_battery",
        translation_key="p_battery",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda raw: raw.get("p_battery"),
    ),
    LuxSensorDescription(
        key="p_grid",
        translation_key="p_grid",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda raw: raw.get("p_grid"),
    ),
    LuxSensorDescription(
        key="p_load",
        translation_key="p_load",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda raw: raw.get("p_load"),
    ),
    LuxSensorDescription(
        key="soc",
        translation_key="soc",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda raw: raw.get("soc"),
    ),
    # ── Daily energy (primary) ────────────────────────────────────────
    LuxSensorDescription(
        key="e_pv_day",
        translation_key="e_pv_day",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda raw: raw.get("e_pv_day"),
    ),
    LuxSensorDescription(
        key="e_to_grid_day",
        translation_key="e_to_grid_day",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda raw: raw.get("e_to_grid_day"),
    ),
    LuxSensorDescription(
        key="e_to_user_day",
        translation_key="e_to_user_day",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda raw: raw.get("e_to_user_day"),
    ),
    LuxSensorDescription(
        key="e_discharge_day",
        translation_key="e_discharge_day",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda raw: raw.get("e_discharge_day"),
    ),
    LuxSensorDescription(
        key="e_charge_day",
        translation_key="e_charge_day",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda raw: raw.get("e_charge_day"),
    ),
    # ── PV string detail (diagnostic) ────────────────────────────────
    LuxSensorDescription(
        key="p_pv1",
        translation_key="p_pv1",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda raw: raw.get("p_pv1"),
    ),
    LuxSensorDescription(
        key="p_pv2",
        translation_key="p_pv2",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda raw: raw.get("p_pv2"),
    ),
    LuxSensorDescription(
        key="p_eps",
        translation_key="p_eps",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda raw: raw.get("p_eps"),
    ),
    # ── Voltage (diagnostic) ─────────────────────────────────────────
    LuxSensorDescription(
        key="v_pv1",
        translation_key="v_pv1",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda raw: raw.get("v_pv1"),
    ),
    LuxSensorDescription(
        key="v_pv2",
        translation_key="v_pv2",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda raw: raw.get("v_pv2"),
    ),
    LuxSensorDescription(
        key="v_bat",
        translation_key="v_bat",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda raw: raw.get("v_bat"),
    ),
    LuxSensorDescription(
        key="v_ac_r",
        translation_key="v_ac_r",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda raw: raw.get("v_ac_r"),
    ),
    # ── Current (diagnostic) ─────────────────────────────────────────
    LuxSensorDescription(
        key="i_pv1",
        translation_key="i_pv1",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda raw: raw.get("i_pv1"),
    ),
    LuxSensorDescription(
        key="i_pv2",
        translation_key="i_pv2",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda raw: raw.get("i_pv2"),
    ),
    LuxSensorDescription(
        key="i_bat",
        translation_key="i_bat",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda raw: raw.get("i_bat"),
    ),
    # ── Temperature (diagnostic) ─────────────────────────────────────
    LuxSensorDescription(
        key="t_inner",
        translation_key="t_inner",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda raw: raw.get("t_inner"),
    ),
    LuxSensorDescription(
        key="t_bat",
        translation_key="t_bat",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda raw: raw.get("t_bat"),
    ),
    LuxSensorDescription(
        key="t_rad1",
        translation_key="t_rad1",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda raw: raw.get("t_rad1"),
    ),
    # ── Lifetime energy (diagnostic) ─────────────────────────────────
    LuxSensorDescription(
        key="e_eps_day",
        translation_key="e_eps_day",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda raw: raw.get("e_eps_day"),
    ),
    LuxSensorDescription(
        key="e_pv_all",
        translation_key="e_pv_all",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda raw: raw.get("e_pv_all"),
    ),
    LuxSensorDescription(
        key="e_to_grid_all",
        translation_key="e_to_grid_all",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda raw: raw.get("e_to_grid_all"),
    ),
    LuxSensorDescription(
        key="e_to_user_all",
        translation_key="e_to_user_all",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda raw: raw.get("e_to_user_all"),
    ),
    LuxSensorDescription(
        key="e_discharge_all",
        translation_key="e_discharge_all",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda raw: raw.get("e_discharge_all"),
    ),
    LuxSensorDescription(
        key="e_charge_all",
        translation_key="e_charge_all",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda raw: raw.get("e_charge_all"),
    ),
    # ── Status (diagnostic) ───────────────────────────────────────────
    LuxSensorDescription(
        key="status",
        translation_key="status",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_status_name,
    ),
    LuxSensorDescription(
        key="work_mode",
        translation_key="work_mode",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_work_mode_name,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: LuxCloudCoordinator = entry.runtime_data
    async_add_entities(
        LuxCloudSensor(coordinator, entry, desc) for desc in SENSOR_DESCRIPTIONS
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
        self._attr_device_info = luxcloud_device_info(serial)

    @property
    def native_value(self) -> Any:
        if self.coordinator.data is None:
            return None
        fn = self.entity_description.value_fn
        if fn is None:
            return None
        return fn(self.coordinator.data)
