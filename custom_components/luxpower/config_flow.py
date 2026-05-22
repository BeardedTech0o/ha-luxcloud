"""Config flow for LuxPower integration."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import LuxPowerApi, LuxPowerApiError, LuxPowerAuthError
from .const import (
    CONF_REGION,
    CONF_SERIAL,
    DOMAIN,
    REGION_EU,
    REGION_GLOBAL,
)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Required(CONF_SERIAL): str,
        vol.Required(CONF_REGION, default=REGION_GLOBAL): vol.In(
            [REGION_GLOBAL, REGION_EU]
        ),
    }
)

STEP_REAUTH_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


class LuxPowerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the LuxPower configuration flow."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors: dict[str, str] = {}

        if user_input is not None:
            session = async_get_clientsession(self.hass)
            api = LuxPowerApi(
                session=session,
                username=user_input[CONF_USERNAME],
                password=user_input[CONF_PASSWORD],
                serial=user_input[CONF_SERIAL],
                region=user_input[CONF_REGION],
            )
            try:
                await api.async_validate_credentials()
            except LuxPowerAuthError:
                errors["base"] = "invalid_auth"
            except LuxPowerApiError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(user_input[CONF_SERIAL])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"LuxPower {user_input[CONF_SERIAL]}",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_SCHEMA,
            errors=errors,
        )

    async def async_step_reauth(self, entry_data):
        """Triggered by ConfigEntryAuthFailed — ask user to re-enter credentials."""
        self._reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None):
        errors: dict[str, str] = {}

        if user_input is not None:
            existing = self._reauth_entry
            merged = {**existing.data, **user_input}
            session = async_get_clientsession(self.hass)
            api = LuxPowerApi(
                session=session,
                username=merged[CONF_USERNAME],
                password=merged[CONF_PASSWORD],
                serial=merged[CONF_SERIAL],
                region=merged[CONF_REGION],
            )
            try:
                await api.async_validate_credentials()
            except LuxPowerAuthError:
                errors["base"] = "invalid_auth"
            except LuxPowerApiError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                errors["base"] = "unknown"
            else:
                self.hass.config_entries.async_update_entry(existing, data=merged)
                await self.hass.config_entries.async_reload(existing.entry_id)
                return self.async_abort(reason="reauth_successful")

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=STEP_REAUTH_SCHEMA,
            errors=errors,
        )
