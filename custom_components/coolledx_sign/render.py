"""Bitmap text and icons for the 16-row sign (pure Python, no Pillow needed)."""
from __future__ import annotations

COLORS = {"off": 0, "red": 1, "green": 2, "yellow": 3, "blue": 4, "magenta": 5, "cyan": 6, "white": 7}
RAINBOW = [1, 3, 2, 6, 4, 5]

# fmt: off
FONT = {
    'A': [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    'B': ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    'C': [".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."],
    'D': ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
    'E': ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    'F': ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
    'G': [".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".####"],
    'H': ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    'I': [".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."],
    'J': ["..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."],
    'K': ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    'L': ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    'M': ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
    'N': ["#...#", "#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#"],
    'O': [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    'P': ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    'Q': [".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"],
    'R': ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    'S': [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    'T': ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    'U': ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    'V': ["#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
    'W': ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "#.#.#", ".#.#."],
    'X': ["#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"],
    'Y': ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."],
    'Z': ["#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"],
    '0': [".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."],
    '1': ["..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."],
    '2': [".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"],
    '3': ["#####", "...#.", "..#..", "...#.", "....#", "#...#", ".###."],
    '4': ["...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."],
    '5': ["#####", "#....", "####.", "....#", "....#", "#...#", ".###."],
    '6': ["..##.", ".#...", "#....", "####.", "#...#", "#...#", ".###."],
    '7': ["#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."],
    '8': [".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."],
    '9': [".###.", "#...#", "#...#", ".####", "....#", "...#.", ".##.."],
    '!': ["..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."],
    '?': [".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."],
    '.': [".....", ".....", ".....", ".....", ".....", ".....", "..#.."],
    ',': [".....", ".....", ".....", ".....", "..#..", "..#..", ".#..."],
    "'": ["..#..", "..#..", ".#...", ".....", ".....", ".....", "....."],
    '-': [".....", ".....", ".....", "#####", ".....", ".....", "....."],
    '#': [".#.#.", ".#.#.", "#####", ".#.#.", "#####", ".#.#.", ".#.#."],
    '&': [".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"],
    ':': [".....", "..#..", "..#..", ".....", "..#..", "..#..", "....."],
    '/': [".....", "....#", "...#.", "..#..", ".#...", "#....", "....."],
    '%': ["##...", "##..#", "...#.", "..#..", ".#...", "#..##", "...##"],
    '+': [".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."],
    '=': [".....", ".....", "#####", ".....", "#####", ".....", "....."],
    ' ': [".....", ".....", ".....", ".....", ".....", ".....", "....."],
}
FONT.update({
    '(': ["...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."],
    ')': [".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."],
    '@': [".###.", "#...#", "#.###", "#.#.#", "#.###", "#....", ".###."],
    '"': [".#.#.", ".#.#.", ".....", ".....", ".....", ".....", "....."],
    ';': [".....", "..#..", "..#..", ".....", "..#..", "..#..", ".#..."],
    '_': [".....", ".....", ".....", ".....", ".....", ".....", "#####"],
    '<': ["...#.", "..#..", ".#...", "#....", ".#...", "..#..", "...#."],
    '>': [".#...", "..#..", "...#.", "....#", "...#.", "..#..", ".#..."],
    '*': [".....", "#.#.#", ".###.", "#####", ".###.", "#.#.#", "....."],
    '$': ["..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."],
    '°': [".##..", "#..#.", ".##..", ".....", ".....", ".....", "....."],
})
# fmt: on
NARROW = {"I": 3, "!": 3, ".": 3, ",": 3, "'": 3, ":": 3, ";": 3, "1": 4, " ": 3, "(": 4, ")": 4, '"': 4}

ICONS = {
    # 16x16; '#' = icon colour, 'K' = punched-out (off), letters = fixed colours
    "warning": [
        ".......YY.......", "......YYYY......", "......YYYY......", ".....YYYYYY.....",
        ".....YYKKYY.....", "....YYYKKYYY....", "....YYYKKYYY....", "...YYYYKKYYYY...",
        "...YYYYKKYYYY...", "..YYYYYKKYYYYY..", "..YYYYYYYYYYYY..", ".YYYYYYKKYYYYYY.",
        ".YYYYYYKKYYYYYY.", "YYYYYYYYYYYYYYYY", "YYYYYYYYYYYYYYYY", "................",
    ],
    "error": [
        ".....RRRRRR.....", "...RRRRRRRRRR...", "..RRRRRRRRRRRR..", ".RRRKRRRRRRKRRR.",
        ".RRKKKRRRRKKKRR.", "RRRRKKKRRKKKRRRR", "RRRRRKKKKKKRRRRR", "RRRRRRKKKKRRRRRR",
        "RRRRRRKKKKRRRRRR", "RRRRRKKKKKKRRRRR", "RRRRKKKRRKKKRRRR", ".RRKKKRRRRKKKRR.",
        ".RRRKRRRRRRKRRR.", "..RRRRRRRRRRRR..", "...RRRRRRRRRR...", ".....RRRRRR.....",
    ],
    "info": [
        ".....BBBBBB.....", "...BBBBBBBBBB...", "..BBBBBWWBBBBB..", ".BBBBBBWWBBBBBB.",
        ".BBBBBBBBBBBBBB.", "BBBBBBWWWBBBBBBB", "BBBBBBBWWBBBBBBB", "BBBBBBBWWBBBBBBB",
        "BBBBBBBWWBBBBBBB", "BBBBBBBWWBBBBBBB", "BBBBBBBWWBBBBBBB", ".BBBBBWWWWBBBBB.",
        ".BBBBBBBBBBBBBB.", "..BBBBBBBBBBBB..", "...BBBBBBBBBB...", ".....BBBBBB.....",
    ],
    "ok": [
        ".....GGGGGG.....", "...GGGGGGGGGG...", "..GGGGGGGGGGGG..", ".GGGGGGGGGGGWGG.",
        ".GGGGGGGGGGWWGG.", "GGGGGGGGGGWWGGGG", "GGGGGGGGGWWGGGGG", "GGWGGGGGWWGGGGGG",
        "GGWWGGGWWGGGGGGG", "GGGWWGWWGGGGGGGG", "GGGGWWWGGGGGGGGG", ".GGGGWGGGGGGGGG.",
        ".GGGGGGGGGGGGGG.", "..GGGGGGGGGGGG..", "...GGGGGGGGGG...", ".....GGGGGG.....",
    ],
}
CODE = {"R": 1, "G": 2, "Y": 3, "B": 4, "M": 5, "C": 6, "W": 7, "K": 0}
ICON_DEFAULT_TEXT_COLOR = {"warning": "yellow", "error": "red", "info": "cyan", "ok": "green"}


def blank(w: int, h: int = 16) -> list[list[int]]:
    return [[0] * w for _ in range(h)]


def _glyph(ch: str):
    ch = ch.upper()
    return FONT.get(ch, FONT["?"]), NARROW.get(ch, 5)


def text_width(s: str, scale: int = 1, spacing: int = 1) -> int:
    if not s:
        return 0
    return sum((_glyph(c)[1] + spacing) * scale for c in s) - spacing * scale


def draw_text(grid, s: str, x: int, y: int, color, scale: int = 1, spacing: int = 1) -> int:
    """color: int, or callable(char_index) -> int. Returns x after the text."""
    h, w = len(grid), len(grid[0])
    cx = x
    for i, ch in enumerate(s):
        g, gw = _glyph(ch)
        off = {3: 1, 4: 0}.get(gw, 0)
        col = color(i) if callable(color) else color
        for gy, row in enumerate(g):
            for gx in range(gw):
                sx = gx + off
                if sx < 5 and row[sx] == "#":
                    for dy in range(scale):
                        for dx in range(scale):
                            px, py = cx + gx * scale + dx, y + gy * scale + dy
                            if 0 <= px < w and 0 <= py < h:
                                grid[py][px] = col
        cx += (gw + spacing) * scale
    return cx


def draw_icon(grid, name: str, x: int, y: int = 0, color: int | None = None) -> int:
    rows = ICONS[name]
    for dy, row in enumerate(rows):
        for dx, ch in enumerate(row):
            if ch == ".":
                continue
            c = color if (ch == "#" and color is not None) else CODE.get(ch, 7)
            if 0 <= y + dy < len(grid) and 0 <= x + dx < len(grid[0]):
                grid[y + dy][x + dx] = c
    return x + len(rows[0])


def color_value(color) -> int | str:
    if isinstance(color, int):
        return color & 7
    c = str(color or "white").lower()
    return "rainbow" if c == "rainbow" else COLORS.get(c, 7)


def compose(message: str, *, color="white", icon: str | None = None, label: str | None = None,
            label_color="yellow", large: bool = True, width: int = 64, height: int = 16,
            center: bool = False, max_columns: int = 4800) -> list[list[int]]:
    """Icon + optional label + message, rendered for the sign's own text scrolling."""
    scale = 2 if large and height >= 16 else 1
    y = (height - 7 * scale) // 2
    col = color_value(color)
    lcol = color_value(label_color)
    parts_w = 0
    if icon:
        parts_w += 16 + 3
    if label:
        parts_w += text_width(label, scale) + 4 * scale
    msg = message or ""
    # keep within the sign's ~30 KiB upload budget
    while msg and parts_w + text_width(msg, scale) > max_columns:
        msg = msg[:-1]
    total = parts_w + text_width(msg, scale)
    w = max(width, total + 2)
    grid = blank(w, height)
    x = (w - total) // 2 if center and total < width else 1
    if icon:
        x = draw_icon(grid, icon, x, (height - 16) // 2) + 3
    if label:
        x = draw_text(grid, label, x, y, (lambda i: RAINBOW[i % 6]) if lcol == "rainbow" else lcol, scale) + 4 * scale
    draw_text(grid, msg, x, y, (lambda i: RAINBOW[i % 6]) if col == "rainbow" else col, scale)
    return grid
