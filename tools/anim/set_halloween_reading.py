import math
from pixkit import *

ANIMS = []


def anim(cat, name, speed=120):
    def deco(fn):
        ANIMS.append(dict(category=cat, name=name, speed=speed, fn=fn))
        return fn
    return deco


# ============================================================ HALLOWEEN
PUMPKIN = sprite([
    ".....GG.....",
    "....GG......",
    "..RRRRRRRR..",
    ".RRRRRRRRRR.",
    "RRR##RR##RRR",
    "RRR##RR##RRR",
    "RRRRRR#RRRRR",
    "RRRRRRRRRRRR",
    "RR########RR",
    "RRR#R##R#RRR",
    ".RRRRRRRRRR.",
    "..RRRRRRRR..",
])


@anim("Halloween", "Jack-o'-Lanterns", 110)
def pumpkins():
    out = []
    rg = Rng(7)
    for t in range(16):
        f = blank()
        for i, x in enumerate((2, 26, 50)):
            glow = rg.pick([Y, Y, Y, Wh, K])  # flickering candle inside
            bob = 1 if (t // 4 + i) % 2 else 0
            draw(f, PUMPKIN, x, 2 + bob, color=glow)
        out.append(f)
    return out


BAT = [sprite(["#.......#", "##.#.#.##", "#########", ".###.###.", "..#...#.."]),
       sprite([".........", "...#.#...", ".#######.", "#########", "#.......#"])]


@anim("Halloween", "Bats Over the Moon", 90)
def bats():
    out = []
    for t in range(32):
        f = blank()
        disc(f, 32, 8, 7, Y)
        disc(f, 35, 6, 6.5, K)  # crescent
        for i, (x0, y0, sp) in enumerate([(0, 2, 2), (20, 8, 3), (40, 4, 2), (55, 10, 3)]):
            x = (x0 + t * sp) % (W + 12) - 10
            y = y0 + round(math.sin((t + i * 3) * 0.7) * 1.5)
            draw(f, BAT[(t + i) % 2], x, y, color=M if i % 2 else B)
        out.append(f)
    return out


GHOST = sprite([
    "...####...",
    "..######..",
    ".########.",
    ".#B##B###.",
    ".#B##B###.",
    "##########",
    "####BB####",
    "##########",
    "##########",
    "##########",
    "#.##..##.#",
])


@anim("Halloween", "Boo! Ghost", 110)
def ghost():
    out = []
    for t in range(24):
        f = blank()
        x = 4 + t * 2 if t < 12 else 4 + (24 - t) * 2
        y = 2 + round(math.sin(t * 0.8) * 2)
        draw(f, GHOST, x, y, color=Wh)
        if (t // 3) % 2 == 0:
            text(f, "BOO!", 40 - (x // 6), 4, C if t % 6 < 3 else M)
        out.append(f)
    return out


SPIDER = sprite(["#.#..#.#", ".##RR##.", "##RRRR##", ".######.", "#.#..#.#"])


@anim("Halloween", "Spiders", 100)
def spiders():
    out = []
    for t in range(24):
        f = blank()
        # web in the top-left corner
        for r in (3, 6, 9):
            for k in range(7):
                a = math.pi / 2 * k / 6
                put(f, r * math.cos(a), r * math.sin(a), Wh if r != 6 else C)
        for k in range(4):
            a = math.pi / 2 * k / 3
            line(f, 0, 0, 10 * math.cos(a), 10 * math.sin(a), Wh)
        for i, x in enumerate((20, 34, 48, 59)):
            ph = (t + i * 6) % 24
            d = ph if ph < 12 else 24 - ph
            y = round(d * 0.9)
            line(f, x + 3, 0, x + 3, y, Wh)
            draw(f, SPIDER, x, y, color=M if i % 2 else G)
        out.append(f)
    return out


@anim("Halloween", "Trick or Treat", 150)
def trick_or_treat():
    out = []
    corn = [Y, R, Wh]
    for t in range(12):
        f = blank()
        text_c(f, "TRICK OR", 0, lambda i: corn[(i + t) % 3])
        text_c(f, "TREAT!", 9, lambda i: corn[(i + t + 1) % 3])
        out.append(f)
    return out


CAULDRON = sprite([
    "W..............W",
    ".WWWWWWWWWWWWWW.",
    "..BBBBBBBBBBBB..",
    ".BBBBBBBBBBBBBB.",
    ".BBBBBBBBBBBBBB.",
    "..BBBBBBBBBBBB..",
    "...BB......BB...",
])


@anim("Halloween", "Witch's Cauldron", 100)
def cauldron():
    out = []
    rg = Rng(11)
    bubbles = [(rg.i(22, 40), rg.i(0, 24)) for _ in range(9)]
    for t in range(24):
        f = blank()
        draw(f, CAULDRON, 24, 9)
        for x in range(26, 38):
            put(f, x, 9, G if (x + t) % 3 else Y)
        for (x, ph) in bubbles:
            age = (t + ph) % 24
            if age < 9:
                y = 8 - age
                wob = round(math.sin(age + x) * 0.8)
                put(f, x + wob, y, G if age < 6 else C)
        text(f, "BREW", 0, 4, M)
        text(f, "HAHA", 41, 4, G if t % 4 < 2 else M)
        out.append(f)
    return out


SKULL = sprite([
    "..########..",
    ".##########.",
    "############",
    "##..####..##",
    "##..####..##",
    "############",
    ".#####.####.",
    "..########..",
    "..#.#.#.#...",
    "...#.#.#.#..",
])


@anim("Halloween", "Glowing Skull", 140)
def skull():
    out = []
    eyes = [R, M, G, C]
    for t in range(16):
        f = blank()
        draw(f, SKULL, 2, 3, color=Wh)
        e = eyes[(t // 4) % 4]
        dx = [0, 1, 1, 0][t % 4]
        put(f, 4 + dx, 7, e); put(f, 10 + dx, 7, e)
        if t % 8 < 6:
            put(f, 4 + dx, 6, e); put(f, 10 + dx, 6, e)
        text_c(f, "STAY", 0, Y, x0=16)
        text_c(f, "SPOOKY", 9, lambda i: [Y, R][(i + t) % 2], x0=14)
        out.append(f)
    return out


# ============================================================ READING
@anim("Reading", "Page Flip", 90)
def page_flip():
    out = []
    n = 16
    for t in range(n):
        f = blank()
        # open book: two pages with spine at x=32
        for x in range(10, 54):
            put(f, x, 14, Y)  # cover edge
        for side in (-1, 1):
            for k in range(3, 13, 3):
                line(f, 32 + side * 4, k, 32 + side * 20, k, B)
        rect(f, 31, 2, 2, 13, R)
        # page sweeping right -> left following an arc
        a = math.pi * t / (n - 1)
        tipx = 32 + 21 * math.cos(a)
        lift = 6 * math.sin(a)
        top = 2 - lift * 0.5
        line(f, 32, 2, tipx, top, Wh)
        line(f, 32, 13, tipx, 13 - lift * 0.3, Wh)
        line(f, tipx, top, tipx, 13 - lift * 0.3, Wh)
        for k in (5, 8, 11):
            line(f, 32 + (tipx - 32) * 0.15, k, 32 + (tipx - 32) * 0.85, k - lift * 0.4, Y)
        out.append(f)
    return out


@anim("Reading", "Bookworm", 110)
def bookworm():
    out = []
    for t in range(32):
        f = blank()
        text_c(f, "READ", 4, lambda i: [B, M, C, Y][i])
        # green worm wiggling along the bottom then over the letters
        head = (t * 2) % (W + 16) - 8
        for k in range(8):
            x = head - k
            y = 13 + round(math.sin((x + t) * 0.9) * 1.2)
            put(f, x, y, G)
        put(f, head + 1, 12 + round(math.sin((head + 1 + t) * 0.9) * 1.2), Wh)
        out.append(f)
    return out


BOOK = sprite([
    "RRRRRRRRRR",
    "RWWWWWWWWW",
    "RRRRRRRRRR",
])


@anim("Reading", "One More Chapter", 160)
def one_more_chapter():
    out = []
    cols = [R, B, G, M, C]
    for t in range(16):
        f = blank()
        n = min(5, t // 2 + 1)
        for i in range(n):
            spr = [[(('#' if ch == 'R' else ch)) for ch in row] for row in BOOK]
            draw(f, spr, 2 + (i % 2), 13 - i * 3, color=cols[i])
        text_c(f, "ONE MORE", 0, Wh, x0=14)
        if t % 4 < 3:
            text_c(f, "CHAPTER", 9, Y, x0=14)
        out.append(f)
    return out


GLASSES = sprite([
    "#####......#####",
    "#...#......#...#",
    "#...########...#",
    "#...#......#...#",
    "#####......#####",
])


@anim("Reading", "Reading Glasses", 120)
def glasses():
    out = []
    for t in range(24):
        f = blank()
        draw(f, GLASSES, 2, 5, color=C)
        # pupils scan left -> right then snap back (reading lines)
        p = (t % 8) / 7
        for yy in (7, 8):
            put(f, 3 + round(p), yy, Wh)
            put(f, 14 + round(p), yy, Wh)
        # lines of 'text' being read appear across the right side
        line_i = (t // 8)
        for li in range(3):
            y = 3 + li * 4
            length = 40 if li < line_i else (round(p * 40) if li == line_i else 0)
            for x in range(22, 22 + length):
                if (x * 7 + li * 3) % 9 not in (0, 5):
                    put(f, x, y, Y if li == line_i else B)
        out.append(f)
    return out


@anim("Reading", "Letters Take Flight", 100)
def letters_fly():
    out = []
    rg = Rng(5)
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    parts = [(rg.i(18, 44), rg.i(0, 24), rg.pick(letters), rg.pick([Y, C, M, G, Wh]), rg.f() * 2 - 1)
             for _ in range(7)]
    for t in range(24):
        f = blank()
        # open book at the bottom
        for x in range(14, 50):
            put(f, x, 15, R)
        for dx in range(0, 17):
            yl = 12 + dx // 6
            for y in range(yl, 15):
                put(f, 31 - dx, y, Wh if (y + dx) % 7 else B)
                put(f, 32 + dx, y, Wh if (y + dx) % 7 else B)
        for (x, ph, ch, col, drift) in parts:
            age = (t + ph) % 24
            if age < 14:
                y = 12 - age
                text(f, ch, x + round(drift * age), y - 6, col)
        out.append(f)
    return out
