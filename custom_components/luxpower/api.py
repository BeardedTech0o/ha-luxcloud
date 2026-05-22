"""LuxPower cloud API client."""
from __future__ import annotations

import asyncio
import hashlib
import logging
from typing import Any

import aiohttp

from .const import API_URLS, REGION_GLOBAL

_LOGGER = logging.getLogger(__name__)

_TOKEN_REFRESH_MARGIN = 300  # seconds before expiry to refresh


class LuxPowerAuthError(Exception):
    """Raised when authentication fails."""


class LuxPowerApiError(Exception):
    """Raised on API communication errors."""


class LuxPowerApi:
    """Async client for the LuxPower cloud API."""

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

    @staticmethod
    def _hash_password(password: str) -> str:
        return hashlib.md5(password.encode()).hexdigest()  # noqa: S324

    async def _ensure_token(self) -> str:
        loop = asyncio.get_event_loop()
        now = loop.time()
        if self._token and now < self._token_expiry - _TOKEN_REFRESH_MARGIN:
            return self._token
        await self._login()
        return self._token  # type: ignore[return-value]

    async def _login(self) -> None:
        payload = {
            "account": self._username,
            "password": self._hash_password(self._password),
        }
        data = await self._post("/web/api/login", payload, auth=False)
        token = data.get("token")
        if not token:
            raise LuxPowerAuthError("No token returned from login")
        self._token = token
        loop = asyncio.get_event_loop()
        # expiration field is in seconds from epoch; fall back to 1 hour
        expiry = data.get("expiration", loop.time() + 3600)
        self._token_expiry = float(expiry)

    # ------------------------------------------------------------------
    # HTTP helpers
    # ------------------------------------------------------------------

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict | None = None,
        params: dict | None = None,
        auth: bool = True,
    ) -> dict[str, Any]:
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if auth:
            token = await self._ensure_token()
            headers["Authorization"] = f"Bearer {token}"
        url = self._base_url + path
        try:
            async with self._session.request(
                method,
                url,
                headers=headers,
                json=json,
                params=params,
                timeout=aiohttp.ClientTimeout(total=20),
            ) as resp:
                if resp.status == 401:
                    self._token = None
                    raise LuxPowerAuthError("Authentication token rejected (401)")
                resp.raise_for_status()
                body = await resp.json()
        except aiohttp.ClientError as exc:
            raise LuxPowerApiError(f"HTTP error talking to LuxPower: {exc}") from exc

        if not body.get("success", True):
            msg = body.get("msg") or body.get("message") or "Unknown API error"
            raise LuxPowerApiError(f"API error: {msg}")
        return body

    async def _post(self, path: str, payload: dict, *, auth: bool = True) -> dict:
        body = await self._request("POST", path, json=payload, auth=auth)
        return body.get("data", body)

    async def _get(self, path: str, params: dict | None = None) -> dict:
        body = await self._request("GET", path, params=params)
        return body.get("data", body)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def async_validate_credentials(self) -> bool:
        """Try logging in; return True on success."""
        await self._login()
        return True

    async def async_get_runtime(self) -> dict[str, Any]:
        """Return the latest runtime snapshot for the configured inverter."""
        params = {"serialNum": self._serial, "lang": "en"}
        data = await self._get("/web/api/inverter/commonMsg/read", params)
        runtime = data.get("runtime", data)
        return runtime

    async def async_get_inverter_list(self) -> list[dict]:
        """Return all inverters associated with the account."""
        data = await self._get("/web/api/inverter/list", {"page": 1, "rows": 50})
        if isinstance(data, list):
            return data
        return data.get("rows", [])

    # ------------------------------------------------------------------
    # Control
    # ------------------------------------------------------------------

    async def async_set_ac_charge(self, enabled: bool) -> None:
        """Enable or disable AC charging."""
        await self._post(
            "/web/api/inverter/acCharge",
            {"serialNum": self._serial, "enabled": enabled},
        )

    async def async_set_ac_charge_current(self, current: int) -> None:
        """Set AC charge current limit (0-80 A)."""
        await self._post(
            "/web/api/inverter/acChargePara",
            {"serialNum": self._serial, "chargeCurrent": current},
        )

    async def async_set_discharge_cutoff(self, soc: int) -> None:
        """Set battery discharge cutoff SOC (%)."""
        await self._post(
            "/web/api/inverter/dischgCutoffSoc",
            {"serialNum": self._serial, "soc": soc},
        )

    async def async_set_charge_cutoff(self, soc: int) -> None:
        """Set battery charge cutoff SOC (%)."""
        await self._post(
            "/web/api/inverter/chgCutoffSoc",
            {"serialNum": self._serial, "soc": soc},
        )

    async def async_set_work_mode(self, mode: int) -> None:
        """Set inverter work mode (0=Self-use, 1=Feed-in, 2=Backup, 3=Manual)."""
        await self._post(
            "/web/api/inverter/workMode",
            {"serialNum": self._serial, "workMode": mode},
        )
