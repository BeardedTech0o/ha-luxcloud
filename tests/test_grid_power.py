"""Tests for the live grid power sign convention."""
from unittest.mock import AsyncMock

import pytest

from custom_components.luxcloud.api import LuxCloudApi, _numeric_power


def _api(runtime):
    api = LuxCloudApi(session=None, username="u", password="p", serial="123")  # type: ignore[arg-type]
    api._request = AsyncMock(return_value=runtime)
    api._async_get_energy = AsyncMock(return_value={})
    return api


@pytest.mark.parametrize(
    ("to_user", "to_grid", "expected"),
    [
        (500, 0, 500),
        (0, 800, -800),
        (300, 100, 200),
        (0, 0, 0),
        ("250", "50", 200),
    ],
)
async def test_grid_power_is_import_minus_export(to_user, to_grid, expected):
    out = await _api({"pToUser": to_user, "pToGrid": to_grid}).async_get_runtime()
    assert out["p_grid"] == expected


@pytest.mark.parametrize(
    "runtime",
    [
        {"pToGrid": 100},
        {"pToUser": 100},
        {"pToUser": None, "pToGrid": 100},
        {"pToUser": "n/a", "pToGrid": 100},
        {"pToUser": 100, "pToGrid": float("nan")},
        {"pToUser": 100, "pToGrid": float("inf")},
        {"pToUser": True, "pToGrid": 100},
    ],
)
async def test_grid_power_unavailable_when_a_reading_is_invalid(runtime):
    out = await _api(runtime).async_get_runtime()
    assert out["p_grid"] is None


@pytest.mark.parametrize(
    ("value", "expected"),
    [(5, 5.0), ("-3.5", -3.5), (None, None), (False, None), ("x", None)],
)
def test_numeric_power(value, expected):
    assert _numeric_power(value) == expected
