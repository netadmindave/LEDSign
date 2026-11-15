"""Display power + brightness as a light (state is assumed; the sign can't be read back)."""
from __future__ import annotations

from homeassistant.components.light import ATTR_BRIGHTNESS, ColorMode, LightEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.restore_state import RestoreEntity

from . import protocol as P
from .const import DOMAIN
from .entity import SignEntity


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities) -> None:
    async_add_entities([SignLight(hass.data[DOMAIN][entry.entry_id])])


class SignLight(SignEntity, LightEntity, RestoreEntity):
    _attr_name = "Display"
    _attr_assumed_state = True
    _attr_color_mode = ColorMode.BRIGHTNESS
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}

    def __init__(self, ctl) -> None:
        super().__init__(ctl, "display")
        self._attr_is_on = True
        self._attr_brightness = 160

    async def async_added_to_hass(self) -> None:
        if (last := await self.async_get_last_state()) is not None:
            self._attr_is_on = last.state == "on"
            self._attr_brightness = last.attributes.get(ATTR_BRIGHTNESS, 160)

    async def async_turn_on(self, **kwargs) -> None:
        cmds = []
        if ATTR_BRIGHTNESS in kwargs:
            self._attr_brightness = max(1, int(kwargs[ATTR_BRIGHTNESS]))
            cmds.append((P.CMD_BRIGHTNESS, self._attr_brightness))
        if not self._attr_is_on or ATTR_BRIGHTNESS not in kwargs:
            cmds.append((P.CMD_SWITCH, 1))
        await self.ctl.commands(cmds)   # one connection for both
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        await self.ctl.command(P.CMD_SWITCH, 0)
        self._attr_is_on = False
        self.async_write_ha_state()
