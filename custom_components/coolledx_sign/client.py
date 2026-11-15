"""BLE transport for CoolLEDX signs, matching the stock CoolLED1248 app.

The stock app connects once and stays connected; cheap BLE modules like this sign's can lock up
after many rapid connect/disconnect cycles. So this client keeps ONE connection open while
commands keep coming and drops it after `idle_disconnect` seconds of quiet (so the phone app can
still connect between updates).
"""
from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable

from bleak.backends.device import BLEDevice
from bleak.exc import BleakError
from bleak_retry_connector import BleakClientWithServiceCache, establish_connection

from . import protocol as P
from .const import CHAR_UUID

_LOGGER = logging.getLogger(__name__)

RETRY_ERRORS = (BleakError, asyncio.TimeoutError, TimeoutError, EOFError, OSError)


class SignError(Exception):
    """Raised when the sign refuses or does not answer."""

    def __init__(self, msg: str, retryable: bool = True) -> None:
        super().__init__(msg)
        self.retryable = retryable


class CoolLedXClient:
    def __init__(self, name: str, password: str, idle_disconnect: float = 30.0) -> None:
        self.name = name
        self.password = password
        self.idle_disconnect = idle_disconnect
        self._lock = asyncio.Lock()
        self._client: BleakClientWithServiceCache | None = None
        self._queue: asyncio.Queue[bytes] = asyncio.Queue()
        self._idle: asyncio.TimerHandle | None = None
        self._expected_disconnect = False

    # ------------------------------------------------------------ connection
    def _on_disconnect(self, _client) -> None:
        if not self._expected_disconnect:
            _LOGGER.debug("%s: disconnected unexpectedly", self.name)
        self._client = None

    async def _connect(self, get_device: Callable[[], BLEDevice | None]):
        if self._client is not None and self._client.is_connected:
            return self._client
        device = get_device()
        if device is None:
            raise SignError("not in Bluetooth range")
        self._expected_disconnect = False
        client = await establish_connection(
            BleakClientWithServiceCache, device, self.name,
            disconnected_callback=self._on_disconnect,
            ble_device_callback=lambda: get_device() or device,   # best adapter/proxy on each try
            max_attempts=3,
        )
        try:
            self._queue = asyncio.Queue()
            q = self._queue
            await client.start_notify(CHAR_UUID, lambda _c, data: q.put_nowait(bytes(data)))
            await asyncio.sleep(0.6)
            self._client = client
            await self._check_password(client)
        except BaseException:
            await self._drop(client, clear_cache=True)
            raise
        _LOGGER.debug("%s: connected", self.name)
        return client

    async def _drop(self, client=None, clear_cache: bool = False) -> None:
        client = client or self._client
        self._client = None
        if client is None:
            return
        self._expected_disconnect = True
        if clear_cache:
            try:
                await client.clear_cache()
            except Exception:  # noqa: BLE001
                pass
        try:
            await client.disconnect()
        except Exception:  # noqa: BLE001
            pass

    def _schedule_idle_disconnect(self) -> None:
        if self._idle:
            self._idle.cancel()
        loop = asyncio.get_running_loop()
        self._idle = loop.call_later(self.idle_disconnect, lambda: loop.create_task(self._idle_drop()))

    async def _idle_drop(self) -> None:
        async with self._lock:
            if self._client is not None:
                _LOGGER.debug("%s: idle, disconnecting", self.name)
                await self._drop()

    async def close(self) -> None:
        if self._idle:
            self._idle.cancel()
            self._idle = None
        async with self._lock:
            await self._drop()

    # ------------------------------------------------------------ public
    async def run(self, get_device: Callable[[], BLEDevice | None], *,
                  commands_before: list[bytes] | None = None,
                  upload: tuple[int, list[bytes]] | None = None,
                  commands_after: list[bytes] | None = None, attempts: int = 3) -> None:
        async with self._lock:
            if self._idle:
                self._idle.cancel()
            last: Exception | None = None
            try:
                for attempt in range(1, attempts + 1):
                    try:
                        client = await self._connect(get_device)
                        await self._send(client, commands_before, upload, commands_after)
                        return
                    except SignError as err:
                        if not err.retryable:
                            raise
                        last = err
                    except RETRY_ERRORS as err:
                        last = err
                    _LOGGER.warning("%s: attempt %d/%d failed (%s)%s", self.name, attempt, attempts, last,
                                    ", reconnecting" if attempt < attempts else "")
                    await self._drop(clear_cache=True)
                    if attempt < attempts:
                        await asyncio.sleep(2.0 * attempt)
                assert last is not None
                raise last
            finally:
                if self._client is not None:
                    self._schedule_idle_disconnect()

    # ------------------------------------------------------------ protocol
    async def _write(self, client, data: bytes) -> None:
        # Stock app: default MTU, 20-byte pieces, write-without-response.
        for off in range(0, len(data), P.WRITE_PIECE):
            await client.write_gatt_char(CHAR_UUID, data[off:off + P.WRITE_PIECE], response=False)
            await asyncio.sleep(P.WRITE_GAP_S)

    async def _send(self, client, commands_before, upload, commands_after) -> None:
        for cmd in commands_before or []:
            await self._write(client, cmd)
            await asyncio.sleep(0.09)
        if upload:
            await self._upload(client, *upload)
        for cmd in commands_after or []:
            await asyncio.sleep(0.06)
            await self._write(client, cmd)
            await asyncio.sleep(0.09)

    async def _check_password(self, client) -> None:
        await self._write(client, P.password(self.password))
        try:
            reply = await asyncio.wait_for(self._queue.get(), 3)
        except asyncio.TimeoutError:
            _LOGGER.debug("%s: no reply to password check (no password set?)", self.name)
            return
        payload = P.unframe(reply)
        if payload and payload[0] == P.CMD_PASSWORD and payload[-1] != 0:
            raise SignError("The sign rejected the password; set the right one in the integration options",
                            retryable=False)

    async def _upload(self, client, cmd: int, packets: list[bytes]) -> None:
        while not self._queue.empty():
            self._queue.get_nowait()
        for idx, pkt in enumerate(packets):
            status = None
            for attempt in range(3):          # stock app: up to 3 tries per packet
                await self._write(client, pkt)
                status = await self._await_ack(cmd, idx)
                if status == 0:
                    break
                _LOGGER.debug("%s: packet %d attempt %d -> %s", self.name, idx, attempt + 1,
                              "no ack" if status is None else P.ACK_TEXT.get(status, status))
                if status is not None and status not in P.RETRYABLE_ACK:
                    break
                await asyncio.sleep(0.1)
            if status is None:
                raise SignError(f"The sign didn't acknowledge packet {idx + 1} of {len(packets)}")
            if status != 0:
                raise SignError(f"The sign rejected packet {idx + 1}: {P.ACK_TEXT.get(status, status)}",
                                retryable=status in P.RETRYABLE_ACK)
            await asyncio.sleep(0.02)
        _LOGGER.debug("%s: upload of %d packets OK", self.name, len(packets))

    async def _await_ack(self, cmd: int, idx: int) -> int | None:
        loop = asyncio.get_running_loop()
        deadline = loop.time() + 5
        while (left := deadline - loop.time()) > 0:
            try:
                data = await asyncio.wait_for(self._queue.get(), left)
            except asyncio.TimeoutError:
                return None
            ack = P.parse_ack(data)
            if ack and ack[0] == cmd and ack[1] == idx:
                return ack[2]
        return None
