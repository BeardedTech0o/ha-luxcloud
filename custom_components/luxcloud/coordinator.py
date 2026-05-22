"""DataUpdateCoordinator for LuxCloud."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import LuxCloudApi, LuxCloudApiError, LuxCloudAuthError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class LuxCloudCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Polls LuxCloud cloud API and distributes data to all entities."""

    def __init__(self, hass: HomeAssistant, api: LuxCloudApi) -> None:
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
        except LuxCloudAuthError as exc:
            raise ConfigEntryAuthFailed from exc
        except LuxCloudApiError as exc:
            raise UpdateFailed(str(exc)) from exc
