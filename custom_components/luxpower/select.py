"""LuxPower select entity for work mode."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, WORK_MODES
from .coordinator import LuxPowerCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: LuxPowerCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([LuxPowerWorkMode(coordinator, entry)])


class LuxPowerWorkMode(CoordinatorEntity[LuxPowerCoordinator], SelectEntity):
    """Select entity to change inverter work mode."""

    _attr_has_entity_name = True
    _attr_name = "Work Mode"
    _attr_icon = "mdi:cog-transfer"
    _attr_options = list(WORK_MODES.values())

    # reverse lookup: name → int
    _MODE_KEYS = {v: k for k, v in WORK_MODES.items()}

    def __init__(self, coordinator: LuxPowerCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        serial = entry.data["serial_number"]
        self._attr_unique_id = f"{serial}_work_mode_select"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, serial)},
            "name": f"LuxPower {serial}",
            "manufacturer": "LuxPower",
            "model": "Solar Inverter",
        }

    @property
    def current_option(self) -> str | None:
        if self.coordinator.data is None:
            return None
        val = self.coordinator.data.get("work_mode")
        if val is None:
            return None
        return WORK_MODES.get(int(val))

    async def async_select_option(self, option: str) -> None:
        mode_int = self._MODE_KEYS[option]
        await self.coordinator.api.async_set_work_mode(mode_int)
        await self.coordinator.async_request_refresh()
