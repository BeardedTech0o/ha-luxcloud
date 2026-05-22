"""LuxCloud number entities for inverter control."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.number import NumberEntity, NumberEntityDescription, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfElectricCurrent
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
class LuxNumberDescription(NumberEntityDescription):
    state_key: str = ""
    set_fn: Any = None


NUMBER_DESCRIPTIONS: tuple[LuxNumberDescription, ...] = (
    LuxNumberDescription(
        key="ac_charge_current",
        translation_key="ac_charge_current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        native_min_value=0,
        native_max_value=80,
        native_step=1,
        mode=NumberMode.SLIDER,
        entity_category=EntityCategory.CONFIG,
        state_key="ac_charge_current",
        set_fn=lambda api, v: api.async_set_ac_charge_current(int(v)),
    ),
    LuxNumberDescription(
        key="discharge_cutoff_soc",
        translation_key="discharge_cutoff_soc",
        native_unit_of_measurement=PERCENTAGE,
        native_min_value=5,
        native_max_value=100,
        native_step=1,
        mode=NumberMode.SLIDER,
        entity_category=EntityCategory.CONFIG,
        state_key="discharge_cutoff_soc",
        set_fn=lambda api, v: api.async_set_discharge_cutoff(int(v)),
    ),
    LuxNumberDescription(
        key="charge_cutoff_soc",
        translation_key="charge_cutoff_soc",
        native_unit_of_measurement=PERCENTAGE,
        native_min_value=5,
        native_max_value=100,
        native_step=1,
        mode=NumberMode.SLIDER,
        entity_category=EntityCategory.CONFIG,
        state_key="charge_cutoff_soc",
        set_fn=lambda api, v: api.async_set_charge_cutoff(int(v)),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: LuxCloudCoordinator = entry.runtime_data
    async_add_entities(
        LuxCloudNumber(coordinator, entry, desc) for desc in NUMBER_DESCRIPTIONS
    )


class LuxCloudNumber(CoordinatorEntity[LuxCloudCoordinator], NumberEntity):
    """LuxCloud adjustable number control."""

    entity_description: LuxNumberDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: LuxCloudCoordinator,
        entry: ConfigEntry,
        description: LuxNumberDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        serial = entry.data["serial_number"]
        self._attr_unique_id = f"{serial}_{description.key}"
        self._attr_device_info = luxcloud_device_info(serial)

    @property
    def native_value(self) -> float | None:
        if self.coordinator.data is None:
            return None
        val = self.coordinator.data.get(self.entity_description.state_key)
        return float(val) if val is not None else None

    async def async_set_native_value(self, value: float) -> None:
        try:
            await self.entity_description.set_fn(self.coordinator.api, value)
        except LuxCloudApiError as exc:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="api_error",
                translation_placeholders={"message": str(exc)},
            ) from exc
        await self.coordinator.async_request_refresh()
