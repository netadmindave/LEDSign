"""Config flow: discover CoolLEDX signs over Bluetooth (local adapter or ESPHome proxy)."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components.bluetooth import BluetoothServiceInfoBleak, async_discovered_service_info
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.const import CONF_ADDRESS, CONF_NAME
from homeassistant.core import callback

from .const import (
    CONF_IDLE_MODE, CONF_LARGE_TEXT, CONF_MIRROR, CONF_PASSWORD, CONF_SCROLL_SPEED,
    DEFAULT_PASSWORD, DEFAULT_SCROLL_SPEED, DOMAIN, IDLE_MODES,
)

PASSWORD_RE = vol.Match(r"^\d{6}$")


def _is_sign(info: BluetoothServiceInfoBleak) -> bool:
    return (info.name or "").startswith("CoolLEDX") or (info.name or "") in ("CoolLED", "CoolLEDA", "CoolLEDS")


def _size(info: BluetoothServiceInfoBleak) -> tuple[int, int]:
    """Manufacturer data (company ID stripped): MAC(6) | rows | cols(2) | colour type | fw."""
    for data in info.manufacturer_data.values():
        if len(data) >= 10:
            rows, cols = data[6], (data[7] << 8) | data[8]
            if rows in (8, 12, 16, 24, 32) and 16 <= cols <= 512:
                return rows, cols
    return 16, 64


class CoolLedXConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._info: BluetoothServiceInfoBleak | None = None
        self._found: dict[str, BluetoothServiceInfoBleak] = {}

    async def async_step_bluetooth(self, discovery_info: BluetoothServiceInfoBleak):
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()
        if not _is_sign(discovery_info):
            return self.async_abort(reason="not_supported")
        self._info = discovery_info
        self.context["title_placeholders"] = {"name": f"{discovery_info.name} {discovery_info.address[-5:]}"}
        return await self.async_step_confirm()

    async def async_step_confirm(self, user_input: dict[str, Any] | None = None):
        assert self._info
        if user_input is not None:
            return self._create(self._info, user_input[CONF_PASSWORD])
        return self.async_show_form(
            step_id="confirm",
            data_schema=vol.Schema({vol.Required(CONF_PASSWORD, default=DEFAULT_PASSWORD): PASSWORD_RE}),
            description_placeholders={"name": self._info.name, "address": self._info.address},
        )

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            info = self._found[user_input[CONF_ADDRESS]]
            await self.async_set_unique_id(info.address)
            self._abort_if_unique_id_configured()
            return self._create(info, user_input[CONF_PASSWORD])
        configured = self._async_current_ids()
        for info in async_discovered_service_info(self.hass, connectable=True):
            if _is_sign(info) and info.address not in configured:
                self._found[info.address] = info
        if not self._found:
            return self.async_abort(reason="no_devices_found")
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_ADDRESS): vol.In({a: f"{i.name} ({a})" for a, i in self._found.items()}),
                vol.Required(CONF_PASSWORD, default=DEFAULT_PASSWORD): PASSWORD_RE,
            }),
        )

    def _create(self, info: BluetoothServiceInfoBleak, password: str):
        rows, cols = _size(info)
        return self.async_create_entry(
            title=f"{info.name} {rows}x{cols}",
            data={CONF_ADDRESS: info.address, CONF_NAME: info.name, CONF_PASSWORD: password,
                  "width": cols, "height": rows},
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return CoolLedXOptionsFlow()


class CoolLedXOptionsFlow(OptionsFlow):
    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        o = {**self.config_entry.data, **self.config_entry.options}
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required(CONF_PASSWORD, default=o.get(CONF_PASSWORD, DEFAULT_PASSWORD)): PASSWORD_RE,
                vol.Required(CONF_SCROLL_SPEED, default=o.get(CONF_SCROLL_SPEED, DEFAULT_SCROLL_SPEED)):
                    vol.All(vol.Coerce(int), vol.Range(min=0, max=255)),
                vol.Required(CONF_LARGE_TEXT, default=o.get(CONF_LARGE_TEXT, True)): bool,
                vol.Required(CONF_IDLE_MODE, default=o.get(CONF_IDLE_MODE, "auto")): vol.In(IDLE_MODES),
                vol.Required(CONF_MIRROR, default=o.get(CONF_MIRROR, False)): bool,
            }),
        )
