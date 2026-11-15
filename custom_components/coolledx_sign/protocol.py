"""CoolLEDX (CoolLED1248 app family) wire protocol.

Matches the stock CoolLED1248 app's Light1664Utils / DeviceManager for 16x64 seven-colour signs:
  frame      = 0x01 | escape(len16 + payload) | 0x03   (bytes 0x01..0x03 -> 0x02, b ^ 0x04)
  upload     = 128-byte chunks: cmd | 00 | total16 | index16 | size8 | data | xor(00..data)
  ack        = 01 | 00 05 | cmd 00 index16 status | 03    (status 0 OK, 6 checksum -> resend)
  transport  = default MTU, every frame written in 20-byte pieces 15 ms apart (write-without-response)
"""
from __future__ import annotations

CMD_TEXT = 0x02
CMD_IMAGE = 0x03
CMD_ANIMATION = 0x04
CMD_MODE = 0x06
CMD_SPEED = 0x07
CMD_BRIGHTNESS = 0x08
CMD_SWITCH = 0x09
CMD_REVERSE = 0x0C
CMD_PASSWORD = 0x0D

MODE_STATIC, MODE_LEFT, MODE_RIGHT, MODE_UP, MODE_DOWN, MODE_SNOW, MODE_PICTURE, MODE_LASER = range(1, 9)
MODES = {"static": 1, "scroll_left": 2, "scroll_right": 3, "scroll_up": 4, "scroll_down": 5,
         "snowflake": 6, "picture": 7, "laser": 8}

CHUNK = 128
MAX_PAYLOAD = 30 * 1024          # the 16x64 sign rejects uploads much past ~30 KiB
MAX_ANIMATION_FRAMES = 79
WRITE_PIECE = 20
WRITE_GAP_S = 0.025          # stock app uses 15 ms; a little slack for BlueZ / proxies

RETRYABLE_ACK = {1, 3, 6}     # transmission failed / data error / checksum -> resend the packet
ACK_TEXT = {0: "OK", 1: "transmission failed", 2: "device abnormality", 3: "data error",
            4: "data too long", 5: "data ID error", 6: "checksum error"}


def frame(payload: bytes) -> bytes:
    inner = bytes([(len(payload) >> 8) & 0xFF, len(payload) & 0xFF]) + bytes(payload)
    out = bytearray([0x01])
    for b in inner:
        if 0x01 <= b <= 0x03:
            out += bytes([0x02, b ^ 0x04])
        else:
            out.append(b)
    out.append(0x03)
    return bytes(out)


def unframe(data: bytes) -> bytes | None:
    if len(data) < 4 or data[0] != 0x01 or data[-1] != 0x03:
        return None
    out = bytearray()
    i = 1
    while i < len(data) - 1:
        if data[i] == 0x02 and i + 1 < len(data) - 1:
            out.append(data[i + 1] ^ 0x04)
            i += 2
        else:
            out.append(data[i])
            i += 1
    return bytes(out[2:]) if len(out) >= 2 else None


def parse_ack(data: bytes) -> tuple[int, int, int] | None:
    """-> (cmd, index, status) for a data-chunk ack, else None."""
    p = unframe(data)
    if not p or len(p) < 5:
        return None
    return p[0], (p[2] << 8) | p[3], p[-1]


def chunked(cmd: int, data: bytes) -> list[bytes]:
    if len(data) > 0xFFFF:
        raise ValueError(f"payload too large ({len(data)} bytes)")
    frames = []
    for idx, off in enumerate(range(0, len(data), CHUNK)):
        part = data[off:off + CHUNK]
        body = bytes([0x00, (len(data) >> 8) & 0xFF, len(data) & 0xFF, (idx >> 8) & 0xFF, idx & 0xFF, len(part)]) + part
        x = 0
        for b in body:
            x ^= b
        frames.append(frame(bytes([cmd]) + body + bytes([x])))
    return frames


def simple(cmd: int, value: int | None = None) -> bytes:
    return frame(bytes([cmd]) if value is None else bytes([cmd, value & 0xFF]))


def password(pwd: str) -> bytes:
    pwd = "".join(c for c in (pwd or "000000") if c.isdigit())[:6].ljust(6, "0")
    return frame(bytes([CMD_PASSWORD]) + pwd.encode("ascii"))


# ---------------------------------------------------------------- pixels
# A grid is a list of rows; each pixel 0..7 = bit0 red, bit1 green, bit2 blue.

def planes(grid: list[list[int]]) -> bytes:
    """Column-major R, G, B bit planes, 8 rows per byte, MSB = top."""
    h = len(grid)
    w = len(grid[0]) if h else 0
    if h % 8:
        raise ValueError("height must be a multiple of 8")
    out = [bytearray(), bytearray(), bytearray()]
    for x in range(w):
        for yb in range(0, h, 8):
            v = [0, 0, 0]
            for k in range(8):
                c = grid[yb + k][x]
                for ch in range(3):
                    v[ch] = (v[ch] << 1) | ((c >> ch) & 1)
            for ch in range(3):
                out[ch].append(v[ch])
    return bytes(out[0] + out[1] + out[2])


def text_payload(text: str, grid: list[list[int]]) -> bytes:
    bits = planes(grid)
    n = min(len(text), 80)
    meta = bytes([0x30] * n + [0] * (80 - n))
    return bytes(24) + bytes([n]) + meta + bytes([(len(bits) >> 8) & 0xFF, len(bits) & 0xFF]) + bits


def image_payload(grid: list[list[int]]) -> bytes:
    bits = planes(grid)
    return bytes(24) + bytes([(len(bits) >> 8) & 0xFF, len(bits) & 0xFF]) + bits


def animation_payload(frames: list[list[list[int]]], speed_ms: int) -> bytes:
    frames = frames[:MAX_ANIMATION_FRAMES]
    r = bytearray(); g = bytearray(); b = bytearray()
    for f in frames:
        p = planes(f)
        third = len(p) // 3
        r += p[:third]; g += p[third:2 * third]; b += p[2 * third:]
    s = max(1, min(0xFFFF, int(speed_ms)))
    return bytes(24) + bytes([len(frames), s >> 8, s & 0xFF]) + bytes(r + g + b)
