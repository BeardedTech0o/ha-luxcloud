"""LuxCloud switch entities."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import LuxCloudApiError
from .const import DOMAIN
from .coordinator import LuxCloudCoordinator
from .entity import luxcloud_device_info

PARALLEL_UPDATES = 1


@dataclass(frozen=True)
class LuxSwitchDescription(SwitchEntityDescription):
    state_key: str = ""
    turn_on_fn: Any = None
    turn_off_fn: Any = None


SWITCH_DESCRIPTIONS: tuple[LuxSwitchDescription, ...] = (
    LuxSwitchDescription(
        key="ac_charge",
        translation_key="ac_charge",
        entity_category=EntityCategory.CONFIG,
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
    coordinator: LuxCloudCoordinator = entry.runtime_data
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
        self._attr_device_info = luxcloud_device_info(serial)

    @property
    def is_on(self) -> bool | None:
        if self.coordinator.data is None:
            return None
        val = self.coordinator.data.get(self.entity_description.state_key)
        if val is None:
            return None
        return bool(val)

    async def async_turn_on(self, **kwargs: Any) -> None:
        try:
            await self.entity_description.turn_on_fn(self.coordinator.api)
        except LuxCloudApiError as exc:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="api_error",
                translation_placeholders={"message": str(exc)},
            ) from exc
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        try:
            await self.entity_description.turn_off_fn(self.coordinator.api)
        except LuxCloudApiError as exc:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="api_error",
                translation_placeholders={"message": str(exc)},
            ) from exc
        await self.coordinator.async_request_refresh()
