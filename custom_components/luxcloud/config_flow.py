"""Config flow for LuxCloud integration."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import LuxCloudApi, LuxCloudApiError, LuxCloudAuthError
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


def _build_api(hass, data: dict) -> LuxCloudApi:
    return LuxCloudApi(
        session=async_get_clientsession(hass),
        username=data[CONF_USERNAME],
        password=data[CONF_PASSWORD],
        serial=data[CONF_SERIAL],
        region=data[CONF_REGION],
    )


async def _validate(hass, data: dict) -> str | None:
    """Return error key or None on success."""
    try:
        await _build_api(hass, data).async_validate_credentials()
    except LuxCloudAuthError:
        return "invalid_auth"
    except LuxCloudApiError:
        return "cannot_connect"
    except Exception:  # noqa: BLE001
        return "unknown"
    return None


class LuxCloudConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the LuxCloud configuration flow."""

    VERSION = 1

    # ------------------------------------------------------------------
    # Initial setup
    # ------------------------------------------------------------------

    async def async_step_user(self, user_input=None):
        errors: dict[str, str] = {}

        if user_input is not None:
            if error := await _validate(self.hass, user_input):
                errors["base"] = error
            else:
                await self.async_set_unique_id(user_input[CONF_SERIAL])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"LuxCloud {user_input[CONF_SERIAL]}",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_SCHEMA,
            errors=errors,
        )

    # ------------------------------------------------------------------
    # Reauthentication
    # ------------------------------------------------------------------

    async def async_step_reauth(self, entry_data):
        self._reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None):
        errors: dict[str, str] = {}

        if user_input is not None:
            merged = {**self._reauth_entry.data, **user_input}
            if error := await _validate(self.hass, merged):
                errors["base"] = error
            else:
                self.hass.config_entries.async_update_entry(
                    self._reauth_entry, data=merged
                )
                await self.hass.config_entries.async_reload(
                    self._reauth_entry.entry_id
                )
                return self.async_abort(reason="reauth_successful")

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=STEP_REAUTH_SCHEMA,
            errors=errors,
        )

    # ------------------------------------------------------------------
    # Reconfiguration (change region or credentials without re-adding)
    # ------------------------------------------------------------------

    async def async_step_reconfigure(self, user_input=None):
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        errors: dict[str, str] = {}

        if user_input is not None:
            merged = {**entry.data, **user_input}
            if error := await _validate(self.hass, merged):
                errors["base"] = error
            else:
                self.hass.config_entries.async_update_entry(entry, data=merged)
                await self.hass.config_entries.async_reload(entry.entry_id)
                return self.async_abort(reason="reconfigure_successful")

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME, default=entry.data[CONF_USERNAME]): str,
                    vol.Required(CONF_PASSWORD): str,
                    vol.Required(CONF_SERIAL, default=entry.data[CONF_SERIAL]): str,
                    vol.Required(
                        CONF_REGION, default=entry.data[CONF_REGION]
                    ): vol.In([REGION_GLOBAL, REGION_EU]),
                }
            ),
            errors=errors,
        )
