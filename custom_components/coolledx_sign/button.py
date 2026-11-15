"""One-tap 'all clear' button: shows a date-appropriate animation."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .entity import SignEntity


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities) -> None:
    async_add_entities([IdleButton(hass.data[DOMAIN][entry.entry_id])])


class IdleButton(SignEntity, ButtonEntity):
    _attr_name = "Show idle animation"
    _attr_icon = "mdi:party-popper"

    def __init__(self, ctl) -> None:
        super().__init__(ctl, "idle")

    async def async_press(self) -> None:
        await self.ctl.show_idle()
