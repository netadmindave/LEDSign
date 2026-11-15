"""CoolLEDX LED sign (CoolLED1248 app family) for Home Assistant."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

import voluptuous as vol

from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS, CONF_NAME, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv, device_registry as dr

from . import animations as A, protocol as P, render as R
from .client import CoolLedXClient, SignError
from .const import (
    ATTR_COLOR, ATTR_DEVICE_ID, ATTR_ENABLED, ATTR_FRAME_MS, ATTR_ICON, ATTR_LABEL, ATTR_LARGE,
    ATTR_MESSAGE, ATTR_MODE, ATTR_NAME, ATTR_SPEED, CONF_IDLE_MODE, CONF_LARGE_TEXT, CONF_MIRROR,
    CONF_PASSWORD, CONF_SCROLL_SPEED, DEFAULT_PASSWORD, DEFAULT_SCROLL_SPEED, DOMAIN,
)

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.LIGHT, Platform.SELECT, Platform.BUTTON]

COLORS = list(R.COLORS) + ["rainbow"]
ICONS = ["none", "warning", "error", "info", "ok"]


@dataclass
class SignController:
    hass: HomeAssistant
    entry: ConfigEntry
    address: str
    name: str
    client: CoolLedXClient
    library: list[dict] = field(default_factory=list)
    width: int = 64
    height: int = 16
    last_shown: str | None = None

    def _opt(self, key, default):
        return self.entry.options.get(key, self.entry.data.get(key, default))

    async def _run(self, **kw) -> None:
        dev = bluetooth.async_ble_device_from_address(self.hass, self.address, connectable=True)
        if dev is None:
            raise HomeAssistantError(
                f"{self.name} ({self.address}) is not in Bluetooth range. Check the sign is on, the phone app "
                "is disconnected, and a Bluetooth adapter or ESPHome proxy can hear it.")
        try:
            await self.client.run(dev, **kw)
        except SignError as err:
            raise HomeAssistantError(str(err)) from err
        except Exception as err:  # bleak / proxy errors
            raise HomeAssistantError(f"Bluetooth error talking to {self.name}: {err}") from err

    def _mirror(self, grid):
        return [row[::-1] for row in grid] if self._opt(CONF_MIRROR, False) else grid

    def _mode(self, mode: int) -> int:
        if self._opt(CONF_MIRROR, False):
            return {P.MODE_LEFT: P.MODE_RIGHT, P.MODE_RIGHT: P.MODE_LEFT}.get(mode, mode)
        return mode

    # ------------------------------------------------------------ actions
    async def show_text(self, message: str, *, color="white", icon=None, label=None, label_color="yellow",
                        mode: str = "scroll_left", speed: int | None = None, large: bool | None = None) -> None:
        large = self._opt(CONF_LARGE_TEXT, True) if large is None else large
        speed = self._opt(CONF_SCROLL_SPEED, DEFAULT_SCROLL_SPEED) if speed is None else speed
        mode_code = P.MODES.get(mode, P.MODE_LEFT)
        grid = await self.hass.async_add_executor_job(lambda: R.compose(
            message, color=color, icon=None if icon in (None, "none") else icon, label=label,
            label_color=label_color, large=large, width=self.width, height=self.height,
            center=mode_code == P.MODE_STATIC))
        packets = P.chunked(P.CMD_TEXT, P.text_payload(f"{label or ''} {message}".strip(), self._mirror(grid)))
        m = self._mode(mode_code)
        await self._run(commands_before=[P.simple(P.CMD_MODE, m), P.simple(P.CMD_SPEED, int(speed))],
                        upload=(P.CMD_TEXT, packets), commands_after=[P.simple(P.CMD_MODE, m)])
        self.last_shown = f"text: {message}"

    async def show_warning(self, message: str, *, color="yellow", label="WARNING", speed=None, large=None) -> None:
        await self.show_text(message, color=color, icon="warning", label=label, label_color="red",
                             mode="scroll_left", speed=speed, large=large)

    async def show_animation(self, anim: dict, frame_ms: int | None = None) -> None:
        frames = await self.hass.async_add_executor_job(A.frames, anim)
        frames = [self._mirror(f) for f in frames]
        payload = P.animation_payload(frames, frame_ms or anim["speedMs"])
        await self._run(upload=(P.CMD_ANIMATION, P.chunked(P.CMD_ANIMATION, payload)))
        self.last_shown = anim["name"]

    async def show_idle(self, mode: str | None = None) -> str:
        anim = A.pick(self.library, mode or self._opt(CONF_IDLE_MODE, "auto"))
        await self.show_animation(anim)
        return anim["name"]

    async def command(self, cmd: int, value: int) -> None:
        await self._run(commands_before=[P.simple(cmd, value)])


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    address = entry.data[CONF_ADDRESS]
    name = entry.data.get(CONF_NAME, "CoolLEDX")
    lib = await hass.async_add_executor_job(A.load)
    ctl = SignController(hass, entry, address, name,
                         CoolLedXClient(name, entry.options.get(CONF_PASSWORD, entry.data.get(CONF_PASSWORD, DEFAULT_PASSWORD))),
                         lib, entry.data.get("width", 64), entry.data.get("height", 16))
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = ctl
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_reload))
    _register_services(hass)
    return True


async def _reload(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return ok


# ---------------------------------------------------------------- services
def _targets(hass: HomeAssistant, call: ServiceCall) -> list[SignController]:
    ctls: dict[str, SignController] = hass.data.get(DOMAIN, {})
    if not ctls:
        raise HomeAssistantError("No CoolLEDX sign is configured")
    ids = call.data.get(ATTR_DEVICE_ID)
    if not ids:
        return list(ctls.values())
    if isinstance(ids, str):
        ids = [ids]
    reg = dr.async_get(hass)
    out = []
    for dev_id in ids:
        dev = reg.async_get(dev_id)
        for entry_id in (dev.config_entries if dev else []):
            if entry_id in ctls:
                out.append(ctls[entry_id])
    if not out:
        raise HomeAssistantError("That device is not a CoolLEDX sign")
    return out


BASE = {vol.Optional(ATTR_DEVICE_ID): vol.Any(cv.string, [cv.string])}
TEXT_SCHEMA = vol.Schema({
    **BASE,
    vol.Required(ATTR_MESSAGE): cv.string,
    vol.Optional(ATTR_COLOR, default="white"): vol.In(COLORS),
    vol.Optional(ATTR_ICON, default="none"): vol.In(ICONS),
    vol.Optional(ATTR_LABEL): cv.string,
    vol.Optional(ATTR_MODE, default="scroll_left"): vol.In(list(P.MODES)),
    vol.Optional(ATTR_SPEED): vol.All(vol.Coerce(int), vol.Range(min=0, max=255)),
    vol.Optional(ATTR_LARGE): cv.boolean,
})
WARNING_SCHEMA = vol.Schema({
    **BASE,
    vol.Required(ATTR_MESSAGE): cv.string,
    vol.Optional(ATTR_COLOR, default="yellow"): vol.In(COLORS),
    vol.Optional(ATTR_LABEL, default="WARNING"): cv.string,
    vol.Optional(ATTR_SPEED): vol.All(vol.Coerce(int), vol.Range(min=0, max=255)),
    vol.Optional(ATTR_LARGE): cv.boolean,
})
ANIM_SCHEMA = vol.Schema({
    **BASE,
    vol.Required(ATTR_NAME): cv.string,
    vol.Optional(ATTR_FRAME_MS): vol.All(vol.Coerce(int), vol.Range(min=20, max=2000)),
})
IDLE_SCHEMA = vol.Schema({**BASE, vol.Optional(ATTR_MODE): cv.string})
REVERSE_SCHEMA = vol.Schema({**BASE, vol.Required(ATTR_ENABLED): cv.boolean})


def _register_services(hass: HomeAssistant) -> None:
    if hass.services.has_service(DOMAIN, "show_text"):
        return

    async def show_text(call: ServiceCall) -> None:
        d = call.data
        for c in _targets(hass, call):
            await c.show_text(d[ATTR_MESSAGE], color=d[ATTR_COLOR], icon=d[ATTR_ICON], label=d.get(ATTR_LABEL),
                              mode=d[ATTR_MODE], speed=d.get(ATTR_SPEED), large=d.get(ATTR_LARGE))

    async def show_warning(call: ServiceCall) -> None:
        d = call.data
        for c in _targets(hass, call):
            await c.show_warning(d[ATTR_MESSAGE], color=d[ATTR_COLOR], label=d[ATTR_LABEL],
                                 speed=d.get(ATTR_SPEED), large=d.get(ATTR_LARGE))

    async def show_animation(call: ServiceCall) -> None:
        for c in _targets(hass, call):
            anim = A.find(c.library, call.data[ATTR_NAME])
            if anim is None:
                raise HomeAssistantError(f"No animation called '{call.data[ATTR_NAME]}'")
            await c.show_animation(anim, call.data.get(ATTR_FRAME_MS))

    async def show_idle(call: ServiceCall) -> None:
        for c in _targets(hass, call):
            await c.show_idle(call.data.get(ATTR_MODE))

    async def set_reverse(call: ServiceCall) -> None:
        for c in _targets(hass, call):
            await c.command(P.CMD_REVERSE, 1 if call.data[ATTR_ENABLED] else 0)

    hass.services.async_register(DOMAIN, "show_text", show_text, TEXT_SCHEMA)
    hass.services.async_register(DOMAIN, "show_warning", show_warning, WARNING_SCHEMA)
    hass.services.async_register(DOMAIN, "show_animation", show_animation, ANIM_SCHEMA)
    hass.services.async_register(DOMAIN, "show_idle", show_idle, IDLE_SCHEMA)
    hass.services.async_register(DOMAIN, "set_reverse", set_reverse, REVERSE_SCHEMA)
