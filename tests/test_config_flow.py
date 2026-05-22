"""Tests for the LuxCloud config flow."""
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType

from custom_components.luxcloud.api import LuxCloudApiError, LuxCloudAuthError
from custom_components.luxcloud.const import (
    CONF_REGION,
    CONF_SERIAL,
    DOMAIN,
    REGION_GLOBAL,
)
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME

VALID_INPUT = {
    CONF_USERNAME: "test@example.com",
    CONF_PASSWORD: "testpassword",
    CONF_SERIAL: "1234567890",
    CONF_REGION: REGION_GLOBAL,
}


async def _start_flow(hass):
    return await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )


async def test_form_shows_correctly(hass):
    """Config flow shows a form on first load."""
    result = await _start_flow(hass)
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}


async def test_successful_setup(hass):
    """Config entry is created on valid credentials."""
    result = await _start_flow(hass)

    with patch(
        "custom_components.luxcloud.config_flow.LuxCloudApi.async_validate_credentials",
        new_callable=AsyncMock,
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], VALID_INPUT
        )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == f"LuxCloud {VALID_INPUT[CONF_SERIAL]}"
    assert result["data"] == VALID_INPUT


async def test_invalid_auth(hass):
    """Auth error surfaces as invalid_auth form error."""
    result = await _start_flow(hass)

    with patch(
        "custom_components.luxcloud.config_flow.LuxCloudApi.async_validate_credentials",
        side_effect=LuxCloudAuthError,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], VALID_INPUT
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}


async def test_cannot_connect(hass):
    """API error surfaces as cannot_connect form error."""
    result = await _start_flow(hass)

    with patch(
        "custom_components.luxcloud.config_flow.LuxCloudApi.async_validate_credentials",
        side_effect=LuxCloudApiError,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], VALID_INPUT
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_unknown_error(hass):
    """Unexpected exception surfaces as unknown form error."""
    result = await _start_flow(hass)

    with patch(
        "custom_components.luxcloud.config_flow.LuxCloudApi.async_validate_credentials",
        side_effect=Exception("boom"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], VALID_INPUT
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "unknown"}


async def test_duplicate_entry_aborts(hass):
    """Second config entry with same serial is aborted."""
    with patch(
        "custom_components.luxcloud.config_flow.LuxCloudApi.async_validate_credentials",
        new_callable=AsyncMock,
        return_value=True,
    ):
        result = await _start_flow(hass)
        await hass.config_entries.flow.async_configure(result["flow_id"], VALID_INPUT)

        result = await _start_flow(hass)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], VALID_INPUT
        )

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "already_configured"
