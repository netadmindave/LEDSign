"""Pick any built-in animation from a dashboard."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant

from . import animations as A
from .const import DOMAIN
from .entity import SignEntity


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities) -> None:
    async_add_entities([AnimationSelect(hass.data[DOMAIN][entry.entry_id])])


class AnimationSelect(SignEntity, SelectEntity):
    _attr_name = "Animation"
    _attr_icon = "mdi:animation-play"

    def __init__(self, ctl) -> None:
        super().__init__(ctl, "animation")
        self._attr_options = [f"{a['category']}: {a['name']}" for a in ctl.library]
        self._attr_current_option = None

    async def async_select_option(self, option: str) -> None:
        name = option.split(": ", 1)[-1]
        anim = A.find(self.ctl.library, name)
        if anim:
            await self.ctl.show_animation(anim)
            self._attr_current_option = option
            self.async_write_ha_state()
