"""Diagnostics support for LuxCloud."""
from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.redact import async_redact_data

from .const import CONF_SERIAL
from .coordinator import LuxCloudCoordinator

_REDACT = {"username", "password"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator: LuxCloudCoordinator = entry.runtime_data

    return {
        "config": async_redact_data(dict(entry.data), _REDACT),
        "runtime_data": coordinator.data,
        "last_update_success": coordinator.last_update_success,
    }
