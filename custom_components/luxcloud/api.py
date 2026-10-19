"""LuxCloud cloud API client."""
from __future__ import annotations

import asyncio
import json
import logging
import math
from typing import Any

import aiohttp

from .const import API_URLS, REGION_GLOBAL

_LOGGER = logging.getLogger(__name__)

_TOKEN_REFRESH_MARGIN = 300  # seconds before expiry to refresh


# Energy counters: normalised key -> (legacy keys already in kWh, portal field stem).
# The portal returns e.g. todayYielding=115 (0.1 kWh) alongside todayYieldingText="11.5" (kWh).
_ENERGY_FIELDS: dict[str, tuple[tuple[str, ...], str | None]] = {
    "e_pv_day": (("ePvDay", "eYieldDay"), "todayYielding"),
    "e_to_grid_day": (("eToGridDay", "eExportDay"), "todayExport"),
    "e_to_user_day": (("eToUserDay", "eImportDay"), "todayImport"),
    "e_discharge_day": (("eDischargeDay", "eDisChgDay"), "todayDischarging"),
    "e_charge_day": (("eChargeDay", "eChgDay"), "todayCharging"),
    "e_eps_day": (("eEpsDay", "eEPSDay"), None),
    "e_pv_all": (("ePvAll", "eYieldAll"), "totalYielding"),
    "e_to_grid_all": (("eToGridAll", "eExportAll"), "totalExport"),
    "e_to_user_all": (("eToUserAll", "eImportAll"), "totalImport"),
    "e_discharge_all": (("eDischargeAll", "eDisChgAll"), "totalDischarging"),
    "e_charge_all": (("eChargeAll", "eChgAll"), "totalCharging"),
}


def _counter(value: Any) -> float | None:
    """Parse a counter; None for missing, boolean, non-finite or negative values."""
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number) or number < 0:
        return None
    return number


def parse_energy(en: dict[str, Any]) -> dict[str, float | None]:
    """Normalise a getInverterEnergyInfo response into kWh counters.

    Legacy key names (already kWh) win; otherwise the portal's ``<stem>Text``
    value (kWh) is used, falling back to ``<stem>`` in units of 0.1 kWh.
    """
    if isinstance(en.get("data"), dict):
        en = {**en["data"], **{k: v for k, v in en.items() if k != "data"}}

    result: dict[str, float | None] = {}
    for key, (legacy, stem) in _ENERGY_FIELDS.items():
        value = next((v for v in (_counter(en.get(k)) for k in legacy) if v is not None), None)
        if value is None and stem:
            value = _counter(en.get(f"{stem}Text"))
            if value is None:
                raw = _counter(en.get(stem))
                value = raw / 10 if raw is not None else None
        result[key] = value
    return result


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
                raw = await resp.text()
                if not resp.ok:
                    _LOGGER.error(
                        "LuxCloud HTTP %s at %s — response body: %s",
                        resp.status,
                        path,
                        raw,
                    )
                resp.raise_for_status()
                body = json.loads(raw) if raw else {}
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
        energy = await self._async_get_energy()

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
            # Daily and lifetime energy (kWh)
            **energy,
        }

    async def _async_get_energy(self) -> dict[str, float | None]:
        """Fetch energy counters, falling back to the non-v2 path if none are usable."""
        for path in (
            "/v2/api/inverter/getInverterEnergyInfo",
            "/api/inverter/getInverterEnergyInfo",
        ):
            try:
                en = await self._request(path, data={"serialNum": self._serial})
            except LuxCloudAuthError:
                raise
            except LuxCloudApiError as exc:
                _LOGGER.warning("LuxCloud energy request to %s failed: %s", path, exc)
                continue
            parsed = parse_energy(en)
            if parsed["e_pv_day"] is not None:
                return parsed
            _LOGGER.debug("No usable daily solar counter from %s", path)
        return parse_energy({})

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
                "serialNum": self._serial,
                "holdParam": hold_param,
                "valueText": str(value),
                "clientType": "WEB",
                "remoteSetType": "NORMAL",
            },
        )

    async def async_set_ac_charge(self, enabled: bool) -> None:
        """Enable or disable AC charging."""
        await self._write("HOLD_AC_CHARGE_ENABLE", "true" if enabled else "false")

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
