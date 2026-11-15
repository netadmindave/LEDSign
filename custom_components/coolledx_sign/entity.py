"""Shared entity base."""
from __future__ import annotations

from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo
from homeassistant.helpers.entity import Entity

from .const import DOMAIN


class SignEntity(Entity):
    _attr_has_entity_name = True

    def __init__(self, ctl, key: str) -> None:
        self.ctl = ctl
        self._attr_unique_id = f"{ctl.address}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, ctl.address)},
            connections={(CONNECTION_BLUETOOTH, ctl.address)},
            name=f"{ctl.name} LED sign",
            manufacturer="CoolLED (JTKJ)",
            model=f"{ctl.name} {ctl.height}x{ctl.width}",
        )
