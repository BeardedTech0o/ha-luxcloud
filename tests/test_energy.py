"""Tests for LuxCloud energy counter parsing."""
from unittest.mock import AsyncMock

import pytest

from custom_components.luxcloud.api import (
    LuxCloudApi,
    LuxCloudApiError,
    LuxCloudAuthError,
    parse_energy,
)

# Representative getInverterEnergyInfo response from the EU portal (issue #2).
PORTAL = {
    "success": True,
    "todayYielding": 115,
    "todayYieldingText": "11.5",
    "todayCharging": 130,
    "todayChargingText": "13",
    "todayDischarging": 113,
    "todayDischargingText": "11.3",
    "todayImport": 159,
    "todayImportText": "15.9",
    "todayExport": 6,
    "todayExportText": "0.6",
    "totalYielding": 58895,
    "totalYieldingText": "5889.5",
}


def test_portal_text_fields_are_kwh():
    out = parse_energy(PORTAL)
    assert out["e_pv_day"] == 11.5
    assert out["e_charge_day"] == 13.0
    assert out["e_discharge_day"] == 11.3
    assert out["e_to_user_day"] == 15.9
    assert out["e_to_grid_day"] == 0.6
    assert out["e_pv_all"] == 5889.5


def test_numeric_fallback_is_tenths_of_kwh():
    out = parse_energy({"todayYielding": 115, "todayExport": 6})
    assert out["e_pv_day"] == 11.5
    assert out["e_to_grid_day"] == 0.6


def test_zero_is_kept_and_missing_stays_none():
    out = parse_energy({"todayYielding": 0, "todayYieldingText": "0"})
    assert out["e_pv_day"] == 0.0
    assert out["e_charge_day"] is None


@pytest.mark.parametrize("bad", [None, True, False, "", "n/a", -1, float("nan"), float("inf")])
def test_invalid_values_are_rejected(bad):
    out = parse_energy({"todayYielding": bad, "todayYieldingText": bad})
    assert out["e_pv_day"] is None


def test_legacy_keys_win_and_are_not_rescaled():
    out = parse_energy({"ePvDay": 7.25, "todayYielding": 115})
    assert out["e_pv_day"] == 7.25


def test_nested_data_dict():
    out = parse_energy({"success": True, "data": PORTAL})
    assert out["e_pv_day"] == 11.5


def _api():
    return LuxCloudApi(session=None, username="u", password="p", serial="123")  # type: ignore[arg-type]


async def test_falls_back_to_non_v2_path():
    api = _api()
    api._request = AsyncMock(side_effect=[{"success": True}, PORTAL])
    out = await api._async_get_energy()
    assert out["e_pv_day"] == 11.5
    assert [c.args[0] for c in api._request.call_args_list] == [
        "/v2/api/inverter/getInverterEnergyInfo",
        "/api/inverter/getInverterEnergyInfo",
    ]


async def test_failed_energy_requests_return_empty_counters():
    api = _api()
    api._request = AsyncMock(side_effect=LuxCloudApiError("boom"))
    out = await api._async_get_energy()
    assert out["e_pv_day"] is None


async def test_auth_errors_propagate():
    api = _api()
    api._request = AsyncMock(side_effect=LuxCloudAuthError("nope"))
    with pytest.raises(LuxCloudAuthError):
        await api._async_get_energy()
