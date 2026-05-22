"""DataUpdateCoordinator for LuxPower."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import LuxPowerApi, LuxPowerApiError, LuxPowerAuthError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class LuxPowerCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Polls LuxPower cloud API and distributes data to all entities."""

    def __init__(self, hass: HomeAssistant, api: LuxPowerApi) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.api = api

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await self.api.async_get_runtime()
        except LuxPowerAuthError as exc:
            raise ConfigEntryAuthFailed from exc
        except LuxPowerApiError as exc:
            raise UpdateFailed(str(exc)) from exc
