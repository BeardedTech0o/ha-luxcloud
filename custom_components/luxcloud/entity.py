"""Shared device info helper for LuxCloud entities."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN


def luxcloud_device_info(serial: str) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, serial)},
        name=f"LuxPower {serial}",
        manufacturer="LuxPower",
        model="Solar Inverter",
        configuration_url="https://openapi.luxpowertek.com",
    )
