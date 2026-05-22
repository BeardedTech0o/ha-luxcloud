"""LuxCloud select entity for work mode."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import LuxCloudApiError
from .const import DOMAIN, WORK_MODES
from .coordinator import LuxCloudCoordinator
from .entity import luxcloud_device_info

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: LuxCloudCoordinator = entry.runtime_data
    async_add_entities([LuxCloudWorkMode(coordinator, entry)])


class LuxCloudWorkMode(CoordinatorEntity[LuxCloudCoordinator], SelectEntity):
    """Select entity to change inverter work mode."""

    _attr_has_entity_name = True
    _attr_translation_key = "work_mode_control"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_options = list(WORK_MODES.values())

    _MODE_KEYS = {v: k for k, v in WORK_MODES.items()}

    def __init__(self, coordinator: LuxCloudCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        serial = entry.data["serial_number"]
        self._attr_unique_id = f"{serial}_work_mode_select"
        self._attr_device_info = luxcloud_device_info(serial)

    @property
    def current_option(self) -> str | None:
        if self.coordinator.data is None:
            return None
        val = self.coordinator.data.get("work_mode")
        if val is None:
            return None
        return WORK_MODES.get(int(val))

    async def async_select_option(self, option: str) -> None:
        try:
            await self.coordinator.api.async_set_work_mode(self._MODE_KEYS[option])
        except LuxCloudApiError as exc:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="api_error",
                translation_placeholders={"message": str(exc)},
            ) from exc
        await self.coordinator.async_request_refresh()
