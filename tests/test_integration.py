"""Run the integration in Home Assistant against a fake CoolLEDX sign."""
from unittest.mock import patch

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.coolledx_sign import protocol as P
from custom_components.coolledx_sign.const import DOMAIN

ADDR = "C0:00:00:00:07:2E"


class FakeSign:
    """Reassembles 20-byte writes into frames and answers like the real sign."""

    def __init__(self):
        self.nack_once = {}          # packet index -> status to return the first time
        self.drop_writes_after = None  # simulate a dropped link after N frames (first connection only)
        self.buf = bytearray()
        self.frames: list[bytes] = []
        self.piece_sizes: list[int] = []
        self.cb = None
        self.connected = True

    async def start_notify(self, uuid, cb):
        self.cb = cb

    async def write_gatt_char(self, uuid, data, response=False):
        assert response is False
        self.piece_sizes.append(len(data))
        self.buf += data
        while 0x03 in self.buf:
            end = self.buf.index(0x03)
            fr = bytes(self.buf[:end + 1]); del self.buf[:end + 1]
            self.frames.append(fr)
            if self.drop_writes_after is not None and len(self.frames) >= self.drop_writes_after:
                self.drop_writes_after = None
                self.buf.clear()
                from bleak.exc import BleakError
                raise BleakError("[org.bluez.Error.Failed] Not connected")
            p = P.unframe(fr)
            if p[0] == P.CMD_PASSWORD:
                self.cb(None, bytearray(P.frame(bytes([0x0D, 0x00]))))
            elif p[0] in (P.CMD_TEXT, P.CMD_IMAGE, P.CMD_ANIMATION):
                idx = (p[4] << 8) | p[5]
                status = self.nack_once.pop(idx, 0)
                self.cb(None, bytearray(P.frame(bytes([p[0], 0, p[4], p[5], status]))))

    async def disconnect(self):
        self.connected = False

    def cmds(self):
        return [P.unframe(f)[0] for f in self.frames]


@pytest.fixture
def sign():
    return FakeSign()


@pytest.fixture
async def entry(hass: HomeAssistant, sign):
    hass.config.components.update({"bluetooth", "bluetooth_adapters"})
    e = MockConfigEntry(domain=DOMAIN, unique_id=ADDR,
                        data={"address": ADDR, "name": "CoolLEDX", "password": "000000", "width": 64, "height": 16})
    e.add_to_hass(hass)
    with patch("custom_components.coolledx_sign.bluetooth.async_ble_device_from_address", return_value=object()), \
         patch("custom_components.coolledx_sign.client.establish_connection", return_value=sign), \
         patch("custom_components.coolledx_sign.client.asyncio.sleep", return_value=None):
        assert await hass.config_entries.async_setup(e.entry_id)
        await hass.async_block_till_done()
        yield e


async def test_warning(hass, entry, sign):
    await hass.services.async_call(DOMAIN, "show_warning", {"message": "Garage door open"}, blocking=True)
    assert sign.cmds()[0] == P.CMD_PASSWORD
    assert P.CMD_MODE in sign.cmds() and P.CMD_TEXT in sign.cmds()
    assert max(sign.piece_sizes) <= 20
    assert not sign.connected


async def test_status_animation_idle(hass, entry, sign):
    await hass.services.async_call(DOMAIN, "show_text",
                                   {"message": "All clear", "icon": "ok", "color": "green", "mode": "static"}, blocking=True)
    await hass.services.async_call(DOMAIN, "show_animation", {"name": "frequency comb"}, blocking=True)
    await hass.services.async_call(DOMAIN, "show_idle", {}, blocking=True)
    assert sign.cmds().count(P.CMD_ANIMATION) > 10


async def test_entities(hass, entry, sign):
    states = [s.entity_id for s in hass.states.async_all()]
    light = next(s for s in states if s.startswith("light."))
    select = next(s for s in states if s.startswith("select."))
    button = next(s for s in states if s.startswith("button."))
    await hass.services.async_call("light", "turn_on", {"entity_id": light, "brightness": 90}, blocking=True)
    await hass.services.async_call("light", "turn_off", {"entity_id": light}, blocking=True)
    opts = hass.states.get(select).attributes["options"]
    assert len(opts) == 100
    await hass.services.async_call("select", "select_option", {"entity_id": select, "option": opts[0]}, blocking=True)
    await hass.services.async_call("button", "press", {"entity_id": button}, blocking=True)
    assert P.CMD_BRIGHTNESS in sign.cmds() and P.CMD_SWITCH in sign.cmds()


async def test_reverse(hass, entry, sign):
    await hass.services.async_call(DOMAIN, "set_reverse", {"enabled": True}, blocking=True)
    assert P.unframe(sign.frames[-1]) == bytes([P.CMD_REVERSE, 1])


async def test_options_flow(hass, entry):
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == "form"
    with patch("custom_components.coolledx_sign.bluetooth.async_ble_device_from_address", return_value=object()):
        result = await hass.config_entries.options.async_configure(result["flow_id"], {
            "password": "123456", "scroll_speed": 180, "large_text": False, "idle_mode": "optics", "mirror": True})
        await hass.async_block_till_done()
    assert result["type"] == "create_entry"
    assert entry.options["idle_mode"] == "optics"


async def test_user_flow_no_devices(hass):
    hass.config.components.update({"bluetooth", "bluetooth_adapters"})
    with patch("custom_components.coolledx_sign.config_flow.async_discovered_service_info", return_value=[]):
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    assert result["type"] == "abort" and result["reason"] == "no_devices_found"


async def test_resends_corrupted_packet(hass, entry, sign):
    sign.nack_once = {1: 3}   # "data error" on packet 2, like the HA log
    await hass.services.async_call(DOMAIN, "show_animation", {"name": "Prism Dispersion"}, blocking=True)
    idx = [((P.unframe(f)[4] << 8) | P.unframe(f)[5]) for f in sign.frames if P.unframe(f)[0] == P.CMD_ANIMATION]
    assert idx.count(1) == 2 and idx[-1] == max(idx)


async def test_reconnects_after_drop(hass, entry, sign):
    sign.drop_writes_after = 5    # link drops mid-transfer on the first connection
    await hass.services.async_call(DOMAIN, "show_animation", {"name": "Fourier Pair"}, blocking=True)
    assert sign.cmds().count(P.CMD_PASSWORD) == 2     # reconnected and started over
