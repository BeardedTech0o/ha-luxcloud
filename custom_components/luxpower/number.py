"""LuxPower number entities for inverter control."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.number import (
    NumberEntityDescription,
    NumberEntity,
    NumberMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfElectricCurrent
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import LuxPowerCoordinator


@dataclass(frozen=True)
class LuxNumberDescription(NumberEntityDescription):
    state_key: str = ""
    set_fn: Any = None


NUMBER_DESCRIPTIONS: tuple[LuxNumberDescription, ...] = (
    LuxNumberDescription(
        key="ac_charge_current",
        name="AC Charge Current Limit",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        native_min_value=0,
        native_max_value=80,
        native_step=1,
        mode=NumberMode.SLIDER,
        icon="mdi:current-ac",
        state_key="ac_charge_current",
        set_fn=lambda api, v: api.async_set_ac_charge_current(int(v)),
    ),
    LuxNumberDescription(
        key="discharge_cutoff_soc",
        name="Discharge Cutoff SOC",
        native_unit_of_measurement=PERCENTAGE,
        native_min_value=5,
        native_max_value=100,
        native_step=1,
        mode=NumberMode.SLIDER,
        icon="mdi:battery-low",
        state_key="discharge_cutoff_soc",
        set_fn=lambda api, v: api.async_set_discharge_cutoff(int(v)),
    ),
    LuxNumberDescription(
        key="charge_cutoff_soc",
        name="Charge Cutoff SOC",
        native_unit_of_measurement=PERCENTAGE,
        native_min_value=5,
        native_max_value=100,
        native_step=1,
        mode=NumberMode.SLIDER,
        icon="mdi:battery-high",
        state_key="charge_cutoff_soc",
        set_fn=lambda api, v: api.async_set_charge_cutoff(int(v)),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: LuxPowerCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        LuxPowerNumber(coordinator, entry, desc) for desc in NUMBER_DESCRIPTIONS
    )


class LuxPowerNumber(CoordinatorEntity[LuxPowerCoordinator], NumberEntity):
    """LuxPower adjustable number control."""

    entity_description: LuxNumberDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: LuxPowerCoordinator,
        entry: ConfigEntry,
        description: LuxNumberDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        serial = entry.data["serial_number"]
        self._attr_unique_id = f"{serial}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, serial)},
            "name": f"LuxPower {serial}",
            "manufacturer": "LuxPower",
            "model": "Solar Inverter",
        }

    @property
    def native_value(self) -> float | None:
        if self.coordinator.data is None:
            return None
        val = self.coordinator.data.get(self.entity_description.state_key)
        return float(val) if val is not None else None

    async def async_set_native_value(self, value: float) -> None:
        await self.entity_description.set_fn(self.coordinator.api, value)
        await self.coordinator.async_request_refresh()
