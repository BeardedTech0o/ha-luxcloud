"""Global test fixtures for LuxCloud integration tests."""
from unittest.mock import AsyncMock, patch

import pytest

from custom_components.luxcloud.const import (
    CONF_REGION,
    CONF_SERIAL,
    DOMAIN,
    REGION_GLOBAL,
)
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME

MOCK_CONFIG = {
    CONF_USERNAME: "test@example.com",
    CONF_PASSWORD: "testpassword",
    CONF_SERIAL: "1234567890",
    CONF_REGION: REGION_GLOBAL,
}

MOCK_RUNTIME = {
    "soc": 80,
    "p_pv": 2500,
    "p_battery": 500,
    "p_grid": -200,
    "p_load": 2800,
    "v_pv1": 380.0,
    "v_bat": 52.0,
    "t_inner": 35,
    "t_bat": 25,
    "e_pv_day": 12.5,
    "e_to_grid_day": 3.2,
    "e_to_user_day": 0.8,
    "e_discharge_day": 5.0,
    "e_charge_day": 6.1,
    "status": 1,
    "work_mode": 0,
}


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations in all tests."""
    yield


@pytest.fixture
def mock_api():
    """Return a mocked LuxCloudApi."""
    with patch("custom_components.luxcloud.config_flow.LuxCloudApi") as mock_cls:
        instance = mock_cls.return_value
        instance.async_validate_credentials = AsyncMock(return_value=True)
        yield instance


@pytest.fixture
def mock_coordinator_api():
    """Patch coordinator API calls for entry setup."""
    with patch(
        "custom_components.luxcloud.coordinator.LuxCloudCoordinator._async_update_data",
        return_value=MOCK_RUNTIME,
    ):
        yield
