"""BLE transport for CoolLEDX signs, matching the stock CoolLED1248 app.

Each operation connects, verifies the password, sends, waits for the per-chunk acks and
disconnects again, so the phone app can still reach the sign between updates.
"""
from __future__ import annotations

import asyncio
import logging

from bleak.backends.device import BLEDevice
from bleak_retry_connector import BleakClientWithServiceCache, establish_connection

from . import protocol as P
from .const import CHAR_UUID

_LOGGER = logging.getLogger(__name__)


class SignError(Exception):
    """Raised when the sign refuses or does not answer."""


class CoolLedXClient:
    def __init__(self, name: str, password: str) -> None:
        self.name = name
        self.password = password
        self._lock = asyncio.Lock()

    async def _write(self, client, data: bytes) -> None:
        # Stock app: default MTU, 20-byte pieces, 15 ms apart, write-without-response.
        for off in range(0, len(data), P.WRITE_PIECE):
            await client.write_gatt_char(CHAR_UUID, data[off:off + P.WRITE_PIECE], response=False)
            await asyncio.sleep(P.WRITE_GAP_S)

    async def run(self, device: BLEDevice, *, commands_before: list[bytes] | None = None,
                  upload: tuple[int, list[bytes]] | None = None,
                  commands_after: list[bytes] | None = None) -> None:
        async with self._lock:
            client = await establish_connection(BleakClientWithServiceCache, device, self.name, max_attempts=3)
            queue: asyncio.Queue[bytes] = asyncio.Queue()
            try:
                await client.start_notify(CHAR_UUID, lambda _c, data: queue.put_nowait(bytes(data)))
                await asyncio.sleep(0.6)
                await self._check_password(client, queue)
                for cmd in commands_before or []:
                    await self._write(client, cmd)
                    await asyncio.sleep(0.09)
                if upload:
                    await self._upload(client, queue, *upload)
                for cmd in commands_after or []:
                    await asyncio.sleep(0.06)
                    await self._write(client, cmd)
                    await asyncio.sleep(0.09)
            finally:
                try:
                    await client.disconnect()
                except Exception:  # noqa: BLE001
                    pass

    async def _check_password(self, client, queue: asyncio.Queue) -> None:
        await self._write(client, P.password(self.password))
        try:
            reply = await asyncio.wait_for(queue.get(), 3)
        except asyncio.TimeoutError:
            _LOGGER.debug("%s: no reply to password check (no password set?)", self.name)
            return
        payload = P.unframe(reply)
        if payload and payload[0] == P.CMD_PASSWORD and payload[-1] != 0:
            raise SignError("The sign rejected the password; set the right one in the integration options")

    async def _upload(self, client, queue: asyncio.Queue, cmd: int, packets: list[bytes]) -> None:
        while not queue.empty():
            queue.get_nowait()
        for idx, pkt in enumerate(packets):
            for attempt in range(3):
                await self._write(client, pkt)
                status = await self._await_ack(queue, cmd, idx)
                if status == 6 and attempt < 2:
                    continue
                break
            if status is None:
                raise SignError(f"The sign didn't acknowledge packet {idx + 1} of {len(packets)}")
            if status != 0:
                raise SignError(f"The sign rejected packet {idx + 1}: {P.ACK_TEXT.get(status, status)}")
            await asyncio.sleep(0.02)
        _LOGGER.debug("%s: upload of %d packets OK", self.name, len(packets))

    @staticmethod
    async def _await_ack(queue: asyncio.Queue, cmd: int, idx: int) -> int | None:
        loop = asyncio.get_running_loop()
        deadline = loop.time() + 5
        while (left := deadline - loop.time()) > 0:
            try:
                data = await asyncio.wait_for(queue.get(), left)
            except asyncio.TimeoutError:
                return None
            ack = P.parse_ack(data)
            if ack and ack[0] == cmd and ack[1] == idx:
                return ack[2]
        return None
