"""LuxCloud cloud API client."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

from .const import API_URLS, REGION_GLOBAL

_LOGGER = logging.getLogger(__name__)

_TOKEN_REFRESH_MARGIN = 300  # seconds before expiry to refresh


class LuxCloudAuthError(Exception):
    """Raised when authentication fails."""


class LuxCloudApiError(Exception):
    """Raised on API communication errors."""


class LuxCloudApi:
    """Async client for the LuxCloud cloud API."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        username: str,
        password: str,
        serial: str,
        region: str = REGION_GLOBAL,
    ) -> None:
        self._session = session
        self._username = username
        self._password = password
        self._serial = serial
        self._base_url = API_URLS[region]
        self._token: str | None = None
        self._token_expiry: float = 0.0

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------

    async def _ensure_token(self) -> str:
        loop = asyncio.get_event_loop()
        now = loop.time()
        if self._token and now < self._token_expiry - _TOKEN_REFRESH_MARGIN:
            return self._token
        await self._login()
        return self._token  # type: ignore[return-value]

    async def _login(self) -> None:
        """Authenticate and store the session token.

        The LuxCloud portal uses a SaToken-based login endpoint that expects
        the credentials as URL query parameters with isLogin=1 in the POST body.
        The response token is stored under data.token.
        """
        url = self._base_url + "/satoken/web/login"
        params = {
            "account": self._username,
            "password": self._password,
        }
        try:
            async with self._session.request(
                "POST",
                url,
                params=params,
                data={"isLogin": "1"},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=aiohttp.ClientTimeout(total=20),
            ) as resp:
                resp.raise_for_status()
                body = await resp.json(content_type=None)
        except aiohttp.ClientError as exc:
            raise LuxCloudApiError(f"HTTP error during login: {exc}") from exc

        code = body.get("code")
        if code == 401 or not body.get("success"):
            raise LuxCloudAuthError(
                body.get("message") or body.get("msg") or "Login failed"
            )

        token = (body.get("data") or {}).get("token")
        if not token:
            raise LuxCloudAuthError("No token returned from login")

        self._token = token
        loop = asyncio.get_event_loop()
        self._token_expiry = loop.time() + 3600

    # ------------------------------------------------------------------
    # HTTP helpers
    # ------------------------------------------------------------------

    async def _request(
        self,
        path: str,
        *,
        data: dict | None = None,
        auth: bool = True,
    ) -> dict[str, Any]:
        """POST form-encoded data to path; return parsed JSON body."""
        headers: dict[str, str] = {
            "Content-Type": "application/x-www-form-urlencoded",
        }
        if auth:
            token = await self._ensure_token()
            headers["token"] = token

        url = self._base_url + path
        try:
            async with self._session.request(
                "POST",
                url,
                headers=headers,
                data=data,
                timeout=aiohttp.ClientTimeout(total=20),
            ) as resp:
                resp.raise_for_status()
                body = await resp.json(content_type=None)
        except aiohttp.ClientError as exc:
            raise LuxCloudApiError(f"HTTP error talking to LuxCloud: {exc}") from exc

        code = body.get("code")
        if code == 401:
            self._token = None
            raise LuxCloudAuthError("Authentication token rejected (401)")

        if not body.get("success", True):
            msg = body.get("msg") or body.get("message") or "Unknown API error"
            raise LuxCloudApiError(f"API error: {msg}")

        return body

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def async_validate_credentials(self) -> bool:
        """Try logging in; return True on success."""
        await self._login()
        return True

    async def async_get_runtime(self) -> dict[str, Any]:
        """Return the latest data snapshot for the configured inverter.

        Fetches both the real-time runtime data and energy counters, then
        normalises the response into the field names expected by sensor.py.
        """
        rt = await self._request(
            "/v2/api/inverter/getInverterRuntime",
            data={"serialNum": self._serial},
        )
        try:
            en = await self._request(
                "/v2/api/inverter/getInverterEnergyInfo",
                data={"serialNum": self._serial},
            )
        except LuxCloudApiError:
            en = {}

        def _f(d: dict, *keys: str) -> Any:
            """Return the first matching key from dict d."""
            for k in keys:
                if d.get(k) is not None:
                    return d[k]
            return None

        return {
            # Power (W)
            "p_pv": _f(rt, "ppvAll", "ppv1"),
            "p_pv1": rt.get("ppv1"),
            "p_pv2": rt.get("ppv2"),
            "p_battery": rt.get("batPower"),
            "p_grid": _f(rt, "pToGrid"),
            "p_load": _f(rt, "consumptionPower", "pLoad"),
            "p_eps": _f(rt, "peps", "seps"),
            # SOC / voltage / current
            "soc": rt.get("soc"),
            "v_pv1": rt.get("vpv1"),
            "v_pv2": rt.get("vpv2"),
            "v_bat": (rt["vBat"] / 10) if rt.get("vBat") is not None else None,
            "v_ac_r": _f(rt, "vacr", "vac"),
            "i_pv1": rt.get("ipv1"),
            "i_pv2": rt.get("ipv2"),
            "i_bat": _f(rt, "iBat", "batCurrent"),
            # Temperature (°C)
            "t_inner": _f(rt, "tinner", "tInner"),
            "t_bat": _f(rt, "tBat", "tbat"),
            "t_rad1": _f(rt, "tradiator1", "trad1"),
            # Status / mode
            "status": _f(rt, "status", "statusCode"),
            "work_mode": _f(rt, "workMode", "workmode"),
            # Control state (read-back from inverter)
            "ac_charge": _f(rt, "acChargeEnable", "acCharge"),
            "ac_charge_current": _f(rt, "acChargeMaxCurr", "maxChgCurrValue"),
            "discharge_cutoff_soc": _f(rt, "dischgCutSoc", "minSoc", "disChgCutSoc"),
            "charge_cutoff_soc": _f(rt, "chgCutSoc", "maxSoc"),
            # Daily energy (kWh)
            "e_pv_day": _f(en, "ePvDay", "eYieldDay"),
            "e_to_grid_day": _f(en, "eToGridDay", "eExportDay"),
            "e_to_user_day": _f(en, "eToUserDay", "eImportDay"),
            "e_discharge_day": _f(en, "eDischargeDay", "eDisChgDay"),
            "e_charge_day": _f(en, "eChargeDay", "eChgDay"),
            "e_eps_day": _f(en, "eEpsDay", "eEPSDay"),
            # Total lifetime energy (kWh)
            "e_pv_all": _f(en, "ePvAll", "eYieldAll"),
            "e_to_grid_all": _f(en, "eToGridAll", "eExportAll"),
            "e_to_user_all": _f(en, "eToUserAll", "eImportAll"),
            "e_discharge_all": _f(en, "eDischargeAll", "eDisChgAll"),
            "e_charge_all": _f(en, "eChargeAll", "eChgAll"),
        }

    async def async_get_inverter_list(self) -> list[dict]:
        """Return all inverters associated with the account."""
        body = await self._request(
            "/v2/web/config/inverter/listForSearch",
            data={"page": "1", "rows": "50"},
        )
        rows = body.get("rows")
        if isinstance(rows, list):
            return rows
        return []

    # ------------------------------------------------------------------
    # Control – write to inverter via generic register write endpoint
    # ------------------------------------------------------------------

    async def _write(self, hold_param: str, value: int | str) -> None:
        """Generic inverter register write."""
        await self._request(
            "/v2/web/maintain/remoteSet/write",
            data={
                "inverterSn": self._serial,
                "holdParam": hold_param,
                "valueText": str(value),
                "clientType": "WEB",
                "remoteSetType": "NORMAL",
            },
        )

    async def async_set_ac_charge(self, enabled: bool) -> None:
        """Enable or disable AC charging."""
        await self._write("HOLD_AC_CHARGE_ENABLE", 1 if enabled else 0)

    async def async_set_ac_charge_current(self, current: int) -> None:
        """Set AC charge current limit (0-80 A)."""
        await self._write("HOLD_AC_CHARGE_MAX_CURR", current)

    async def async_set_discharge_cutoff(self, soc: int) -> None:
        """Set battery discharge cutoff SOC (%)."""
        await self._write("HOLD_DISCHG_CUT_SOC", soc)

    async def async_set_charge_cutoff(self, soc: int) -> None:
        """Set battery charge cutoff SOC (%)."""
        await self._write("HOLD_CHG_CUT_SOC", soc)

    async def async_set_work_mode(self, mode: int) -> None:
        """Set inverter work mode (0=Self-use, 1=Feed-in, 2=Backup, 3=Manual)."""
        await self._write("HOLD_WORK_MODE", mode)
