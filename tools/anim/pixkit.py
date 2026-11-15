"""Tiny pixel toolkit for a 16x64, 7-color (1 bit per R/G/B) LED matrix."""
import math
import numpy as np

H, W = 16, 64
K, R, G, Y, B, M, C, Wh = 0, 1, 2, 3, 4, 5, 6, 7  # bit0=R bit1=G bit2=B
CODE = {'.': K, ' ': K, 'R': R, 'G': G, 'Y': Y, 'B': B, 'M': M, 'C': C, 'W': Wh, 'O': Y}
RAINBOW = [R, Y, G, C, B, M]


def blank():
    return np.zeros((H, W), dtype=np.uint8)


def put(f, x, y, c):
    x, y = int(round(x)), int(round(y))
    if 0 <= x < W and 0 <= y < H:
        f[y, x] = c


def sprite(rows):
    """rows: list of strings using CODE letters; '#' means 'use color passed at draw'."""
    return [list(r) for r in rows]


def draw(f, spr, x0, y0, color=None, transparent='.'):
    for dy, row in enumerate(spr):
        for dx, ch in enumerate(row):
            if ch == transparent or ch == ' ':
                continue
            c = color if ch == '#' else CODE.get(ch, Wh)
            if c is None:
                c = Wh
            put(f, x0 + dx, y0 + dy, c)


def line(f, x0, y0, x1, y1, c):
    x0, y0, x1, y1 = map(lambda v: int(round(v)), (x0, y0, x1, y1))
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    while True:
        put(f, x0, y0, c)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def rect(f, x, y, w, h, c, fill=True):
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            if fill or yy in (y, y + h - 1) or xx in (x, x + w - 1):
                put(f, xx, yy, c)


def disc(f, cx, cy, r, c):
    for yy in range(int(cy - r - 1), int(cy + r + 2)):
        for xx in range(int(cx - r - 1), int(cx + r + 2)):
            if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r + 0.3:
                put(f, xx, yy, c)


def ring(f, cx, cy, r, c, step=None):
    n = max(8, int(2 * math.pi * r * 1.5))
    for i in range(n):
        a = 2 * math.pi * i / n
        put(f, cx + r * math.cos(a), cy + r * math.sin(a), c)


# ---------------------------------------------------------------- 5x7 font
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
# narrow glyphs drawn 3 wide to save space
NARROW = {'I': 3, '!': 3, '.': 3, ',': 3, "'": 3, ':': 3, '1': 4, ' ': 3}


def glyph_w(ch):
    return NARROW.get(ch, 5)


def text_width(s, spacing=1):
    return sum(glyph_w(ch) + spacing for ch in s) - spacing if s else 0


def text(f, s, x, y, color, spacing=1):
    """color may be an int, or a function(index)->int for per-letter colors."""
    cx = x
    for i, ch in enumerate(s.upper()):
        g = FONT.get(ch, FONT['?'])
        w = glyph_w(ch)
        off = {3: 1, 4: 0}.get(w, 0)  # centre narrow glyphs
        col = color(i) if callable(color) else color
        for dy, row in enumerate(g):
            for dx in range(w):
                sx = dx + off
                if sx < 5 and row[sx] == '#':
                    put(f, cx + dx, y + dy, col)
        cx += w + spacing
    return cx


def text_c(f, s, y, color, x0=0, x1=W, spacing=1):
    if text_width(s.upper(), spacing) > x1 - x0 and spacing > 0:
        spacing = 0          # auto-tighten long lines so they never clip
    w = text_width(s.upper(), spacing)
    return text(f, s, x0 + (x1 - x0 - w) // 2, y, color, spacing)


# ---------------------------------------------------------------- 3x5 mini font (digits + few letters)
MINI = {
    '0': ["###", "#.#", "#.#", "#.#", "###"], '1': [".#.", "##.", ".#.", ".#.", "###"],
    '2': ["###", "..#", "###", "#..", "###"], '3': ["###", "..#", ".##", "..#", "###"],
    '4': ["#.#", "#.#", "###", "..#", "..#"], '5': ["###", "#..", "###", "..#", "###"],
    '6': ["###", "#..", "###", "#.#", "###"], '7': ["###", "..#", ".#.", ".#.", ".#."],
    '8': ["###", "#.#", "###", "#.#", "###"], '9': ["###", "#.#", "###", "..#", "###"],
}


def mini(f, s, x, y, color):
    for i, ch in enumerate(s):
        if ch not in MINI:
            continue
        g = MINI[ch]
        for dy, row in enumerate(g):
            for dx, p in enumerate(row):
                if p == '#':
                    put(f, x + i * 4 + dx, y + dy, color)


# ---------------------------------------------------------------- shared effects
class Rng:
    def __init__(self, seed):
        self.r = np.random.default_rng(seed)

    def i(self, a, b):
        return int(self.r.integers(a, b))

    def f(self):
        return float(self.r.random())

    def pick(self, seq):
        return seq[self.i(0, len(seq))]


def firework(f, cx, cy, t, color, rays=8, life=6):
    """t: 0..life. Expanding burst that fades to sparkles."""
    if t < 0 or t > life:
        return
    if t == 0:
        put(f, cx, cy, Wh)
        return
    r = t * 1.6
    for k in range(rays):
        a = 2 * math.pi * k / rays + 0.3
        x, y = cx + r * math.cos(a), cy + r * math.sin(a) * 0.85
        if t < life - 1 or k % 2 == 0:
            put(f, x, y, color)
        if t >= 2 and t < life - 1:
            put(f, cx + (r - 1.4) * math.cos(a), cy + (r - 1.4) * math.sin(a) * 0.85,
                Wh if t < 3 else color)


def rocket(f, x, y0, y1, t, n, color=Wh):
    """rocket trail rising from y0 to y1 over n frames"""
    if 0 <= t < n:
        y = y0 + (y1 - y0) * t / max(1, n - 1)
        put(f, x, y, color)
        put(f, x, y + 1, Y)


def snow(f, t, seed=3, count=18, color=Wh, speed=1.0):
    rg = np.random.default_rng(seed)
    xs = rg.integers(0, W, count)
    ys = rg.integers(0, H, count)
    for x, y in zip(xs, ys):
        yy = (y + t * speed) % H
        xx = x + round(math.sin((t + y) * 0.6))
        put(f, xx % W, yy, color)


def flame(f, x, y, t, seed=0):
    """2px wide-ish candle flame whose top flickers; base at (x,y)."""
    flick = (t * 7 + seed * 3) % 5
    put(f, x, y, Y)
    put(f, x, y - 1, Y if flick != 2 else R)
    if flick in (0, 1, 3):
        put(f, x, y - 2, R if flick == 3 else Y)
    if flick == 4:
        put(f, x + (1 if seed % 2 else -1), y - 1, R)
