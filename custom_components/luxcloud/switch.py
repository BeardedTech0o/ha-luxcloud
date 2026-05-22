"""LuxCloud switch entities."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import LuxCloudCoordinator


@dataclass(frozen=True)
class LuxSwitchDescription(SwitchEntityDescription):
    state_key: str = ""
    turn_on_fn: Any = None
    turn_off_fn: Any = None


SWITCH_DESCRIPTIONS: tuple[LuxSwitchDescription, ...] = (
    LuxSwitchDescription(
        key="ac_charge",
        name="AC Charge",
        icon="mdi:battery-charging-100",
        state_key="ac_charge",
        turn_on_fn=lambda api: api.async_set_ac_charge(True),
        turn_off_fn=lambda api: api.async_set_ac_charge(False),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: LuxCloudCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        LuxCloudSwitch(coordinator, entry, desc) for desc in SWITCH_DESCRIPTIONS
    )


class LuxCloudSwitch(CoordinatorEntity[LuxCloudCoordinator], SwitchEntity):
    """LuxCloud controllable switch."""

    entity_description: LuxSwitchDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: LuxCloudCoordinator,
        entry: ConfigEntry,
        description: LuxSwitchDescription,
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
        }

    @property
    def is_on(self) -> bool | None:
        if self.coordinator.data is None:
            return None
        val = self.coordinator.data.get(self.entity_description.state_key)
        if val is None:
            return None
        return bool(val)

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.entity_description.turn_on_fn(self.coordinator.api)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.entity_description.turn_off_fn(self.coordinator.api)
        await self.coordinator.async_request_refresh()
