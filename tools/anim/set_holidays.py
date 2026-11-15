import math
from pixkit import *
from set_halloween_reading import anim, ANIMS

HEART = sprite([".##.##.", "#######", "#######", ".#####.", "..###..", "...#..."])
HEART_BIG = sprite([".###...###.", "#####.#####", "###########", "###########",
                    ".#########.", "..#######..", "...#####...", "....###....", ".....#....."])


@anim("Holidays", "New Year's Fireworks", 90)
def new_year():
    out = []
    shows = [(8, 5, 0, R), (22, 4, 5, G), (40, 6, 2, B), (56, 4, 8, M), (30, 3, 11, Y), (14, 6, 14, C)]
    for t in range(24):
        f = blank()
        for (x, y, st, col) in shows:
            tt = (t - st) % 24
            rocket(f, x, 15, y, tt, 4)
            firework(f, x, y, tt - 4, col)
        text_c(f, "2027", 9, lambda i: [Y, Wh][(i + t // 2) % 2])
        out.append(f)
    return out


@anim("Holidays", "MLK Day - Dream", 160)
def mlk():
    out = []
    for t in range(12):
        f = blank()
        text_c(f, "I HAVE A", 0, Wh)
        text_c(f, "DREAM", 9, lambda i: Y if (i <= t % 6) else B)
        out.append(f)
    return out


@anim("Holidays", "Lunar New Year Lanterns", 120)
def lunar():
    LANT = sprite(["..Y..", ".RRR.", "RRYRR", "RRYRR", "RRYRR", ".RRR.", "..Y..", ".Y.Y."])
    out = []
    for t in range(16):
        f = blank()
        for x in range(W):
            put(f, x, 0, Y)
        for i, x in enumerate((3, 15, 46, 58)):
            sw = round(math.sin(t * 0.4 + i) * 1.2)
            line(f, x + 2, 0, x + 2 + sw, 2, Y)
            draw(f, LANT, x + sw, 3)
        firework(f, 32, 7, t % 8, [R, Y][(t // 8) % 2], rays=10, life=7)
        out.append(f)
    return out


@anim("Holidays", "Valentine's Heartbeat", 100)
def valentine():
    out = []
    beat = [0, 1, 0, 1, 0, 0, 0, 0]
    for t in range(16):
        f = blank()
        big = beat[t % 8]
        if big:
            draw(f, HEART_BIG, 2, 3, color=R)
        else:
            draw(f, HEART, 4, 5, color=R)
        text(f, "LOVE", 19, 4, lambda i: [R, M][(i + t) % 2])
        for k in range(3):  # floating hearts on the right
            y = 12 - ((t + k * 5) % 16)
            if 0 <= y + 6:
                draw(f, HEART, 46 + k * 6 - 3, y, color=[M, R, M][k])
        out.append(f)
    return out


SHAMROCK = sprite(["..##.##..", ".#######.", ".#######.", "..#####..", "###.#.###",
                   "####.####", ".##.#.##.", "....#....", "...#.....", "..#......"])


@anim("Holidays", "St. Patrick's Rainbow", 120)
def st_patrick():
    out = []
    for t in range(12):
        f = blank()
        draw(f, SHAMROCK, 1, 3, color=G)
        for i, col in enumerate(RAINBOW):
            r = 12 - i * 1.2
            for k in range(25):
                a = math.pi * k / 24
                put(f, 47 + r * math.cos(a), 15 - r * math.sin(a), col)
        # pot of gold with twinkling coins at the rainbow's right foot
        rect(f, 56, 12, 7, 4, B)
        for k in range(5):
            put(f, 57 + k, 11, Y if (k + t) % 3 else Wh)
        text(f, "LUCK", 11, 4, lambda i: G if (i + t) % 4 else Y)
        out.append(f)
    return out


@anim("Holidays", "Easter Egg Hatch", 150)
def easter():
    EGG = sprite(["...####...", "..#M#M##..", ".########.", ".#C#C#C##.", "##########",
                  "#Y##Y##Y##", "##########", ".########.", "..######.."])
    CHICK = sprite(["..YYY..", ".YYWYY.", "YYYYYYR", ".YYYYY.", "..Y.Y.."])
    out = []
    for t in range(16):
        f = blank()
        for x in range(W):
            put(f, x, 15, G)
            if x % 5 == 0:
                put(f, x, 14, G)
        if t < 8:
            rock = [0, 1, 0, -1][t % 4]
            draw(f, EGG, 27 + rock, 6, color=Wh)
            if t >= 5:
                line(f, 28 + rock, 10, 36 + rock, 10, K)
        else:
            # cracked bottom half + chick popping out
            draw(f, EGG[5:], 27, 11, color=Wh)
            lift = min(4, t - 8)
            draw(f, CHICK, 29, 10 - lift)
            draw(f, sprite([".#.#..#.#.", "##########"]), 27, 7 - lift, color=Wh)
        text(f, "HOP", 2, 3, M); text(f, "HOP", 44, 3, C if t % 2 else M)
        out.append(f)
    return out


@anim("Holidays", "Mother's Day Flowers", 150)
def mothers_day():
    out = []
    flowers = [(4, M), (12, R), (52, Y), (60, M)]
    for t in range(14):
        f = blank()
        for i, (x, col) in enumerate(flowers):
            h = min(9, t + 2 - i)
            if h > 0:
                line(f, x, 15, x, 15 - h, G)
                if h >= 9:
                    disc(f, x, 5, 1.6, col); put(f, x, 5, Y)
            if h > 4:
                put(f, x + 1, 12, G)
        text_c(f, "MOM", 1, lambda i: [M, R, M][i], x0=16, x1=48)
        if t > 6:
            draw(f, HEART, 29, 9, color=R if t % 2 else M)
        out.append(f)
    return out


def flag(f, x0, y0, t, w=26, h=14, wave=True):
    for x in range(w):
        dy = round(math.sin((x - t * 2) * 0.35) * 1.0) if wave and x > 1 else 0
        for y in range(h):
            if x < 11 and y < 7:
                c = Wh if (x % 2 == 1 and y % 2 == 1) else B
            else:
                c = R if (y // 2) % 2 == 0 else Wh
            put(f, x0 + x, y0 + y + dy, c)


@anim("Holidays", "Memorial Day", 140)
def memorial():
    out = []
    for t in range(12):
        f = blank()
        line(f, 1, 0, 1, 15, Wh)
        flag(f, 2, 1, t, w=19, h=13)
        text_c(f, "HONOR", 0, Wh, x0=23)
        text_c(f, "VALOR", 9, R if t % 4 < 2 else B, x0=23)
        out.append(f)
    return out


@anim("Holidays", "Father's Day", 150)
def fathers_day():
    TIE = sprite(["..###..", "..###..", "...#...", "..###..", "..###..", ".#####.", ".#####.",
                  ".#####.", "#######", "#######", ".#####.", "..###..", "...#..."])
    out = []
    for t in range(12):
        f = blank()
        line(f, 0, 0, 3, 3, Wh); line(f, 10, 0, 7, 3, Wh)   # collar
        draw(f, TIE, 2, 2, color=[B, R, G, M][(t // 3) % 4])
        for yy in range(5, 15, 3):  # stripes
            put(f, 4 + ((yy + t) % 3) - 1, yy, Y)
        text_c(f, "#1 DAD", 4, lambda i: Y if (i + t) % 6 < 3 else Wh, x0=14)
        out.append(f)
    return out


@anim("Holidays", "Juneteenth", 150)
def juneteenth():
    STAR = sprite(["...#...", "..###..", "#######", ".#####.", ".##.##.", "#.....#"])
    out = []
    for t in range(12):
        f = blank()
        for x in range(W):
            put(f, x, 15, R)
            put(f, x, 14, B)
        draw(f, STAR, 2, 3, color=Wh if t % 2 else Y)
        draw(f, STAR, 55, 3, color=Y if t % 2 else Wh)
        text_c(f, "FREEDOM", 4, lambda i: Wh if i != t % 7 else R)
        out.append(f)
    return out


@anim("Holidays", "4th of July", 90)
def july4():
    out = []
    shows = [(34, 4, 0, R), (48, 6, 3, Wh), (60, 3, 6, B), (42, 3, 9, R), (55, 7, 12, B)]
    for t in range(16):
        f = blank()
        line(f, 0, 0, 0, 15, Wh)
        flag(f, 1, 1, t, w=25, h=13)
        for (x, y, st, col) in shows:
            tt = (t - st) % 16
            rocket(f, x, 15, y, tt, 4)
            firework(f, x, y, tt - 4, col)
        out.append(f)
    return out


def gear(f, cx, cy, r, teeth, rot, c):
    disc(f, cx, cy, r - 1, c)
    disc(f, cx, cy, 1, K)
    for k in range(teeth):
        a = rot + 2 * math.pi * k / teeth
        for d in (r, r + 0.8):
            put(f, cx + d * math.cos(a), cy + d * math.sin(a), c)


@anim("Holidays", "Labor Day Gears", 100)
def labor():
    out = []
    for t in range(12):
        f = blank()
        gear(f, 6, 7, 5, 8, t * math.pi / 24, Y)
        gear(f, 15, 11, 3.5, 6, -t * math.pi / 16 + 0.3, C)
        text_c(f, "LABOR", 0, Wh, x0=20)
        text_c(f, "DAY", 9, B, x0=20)
        out.append(f)
    return out


@anim("Holidays", "Veterans Day", 160)
def veterans():
    out = []
    for t in range(12):
        f = blank()
        line(f, 1, 0, 1, 15, Wh)
        flag(f, 2, 1, t, w=22, h=13)
        if (t // 6) == 0:
            text_c(f, "THANK", 0, Wh, x0=24); text_c(f, "YOU", 9, R, x0=24)
        else:
            text_c(f, "VETS", 4, lambda i: [R, Wh, B, Wh][i], x0=24)
        out.append(f)
    return out


@anim("Holidays", "Thanksgiving Turkey", 140)
def thanksgiving():
    out = []
    bands = [R, Y, G, R, Y]
    for t in range(12):
        f = blank()
        cx, cy = 8, 11
        for y in range(H):
            for x in range(0, 18):
                r = math.hypot(x - cx, (y - cy) * 1.1)
                if 3.5 < r <= 8.5 and y <= cy:
                    a = math.atan2(cy - y, x - cx)
                    feather = int(a / math.pi * 7)
                    if (feather + int(r)) % 2 == 0 or r > 7:
                        put(f, x, y, bands[(int(r) + t) % 5])
        disc(f, cx, cy, 3, M)              # body
        disc(f, cx, cy - 4, 1.4, Wh)       # head
        put(f, cx + 2, cy - 4, Y)          # beak
        put(f, cx + 1, cy - 3, R); put(f, cx + 1, cy - 2, R)  # wattle
        put(f, cx, cy - 4, K)              # eye
        put(f, cx - 1, 15, Y); put(f, cx + 1, 15, Y)
        text_c(f, "GOBBLE", 0, Y if t % 2 else R, x0=18)
        text_c(f, "GOBBLE", 9, R if t % 2 else Y, x0=18)
        out.append(f)
    return out


RAINBOW_LETTERS = ['R', 'Y', 'G']


@anim("Holidays", "Hanukkah Menorah", 200)
def hanukkah():
    out = []
    xs = [10, 15, 20, 25, 39, 44, 49, 54]
    for t in range(20):
        f = blank()
        lit = min(8, t // 2)
        rect(f, 29, 14, 7, 2, Y); line(f, 32, 4, 32, 14, Y)
        line(f, 10, 12, 54, 12, Y)
        for x in xs:
            line(f, x, 7, x, 11, B)
            put(f, x, 12, Y)
        line(f, 32, 2, 32, 4, Wh)  # shamash (raised)
        flame(f, 32, 1, t, 9)
        for i in range(lit):
            flame(f, xs[7 - i], 6, t, i)
        out.append(f)
    return out


TREE = sprite([
    ".......Y.......",
    "......YYY......",
    ".......G.......",
    "......GGG......",
    ".....GGGGG.....",
    "......GGG......",
    ".....GGGGG.....",
    "....GGGGGGG....",
    ".....GGGGG.....",
    "...GGGGGGGGG...",
    "..GGGGGGGGGGG..",
    ".GGGGGGGGGGGGG.",
    "......RRR......",
])


@anim("Holidays", "Christmas Tree & Snow", 130)
def christmas():
    out = []
    rg = Rng(25)
    bulbs = [(rg.i(4, 12), rg.i(3, 12)) for _ in range(12)]
    for t in range(16):
        f = blank()
        snow(f, t, count=26, seed=8)
        draw(f, TREE, 1, 2)
        for i, (bx, by) in enumerate(bulbs):
            dx = bx - 7
            if abs(dx) <= (by - 1) // 2 + 1:
                put(f, 8 + dx, by + 2, [R, B, Y, M, C, Wh][(i + t) % 6])
        put(f, 8, 2, Wh if t % 2 else Y)
        text_c(f, "MERRY", 0, R, x0=18)
        text_c(f, "XMAS", 9, G if t % 4 < 2 else R, x0=18)
        out.append(f)
    return out


@anim("Holidays", "Kwanzaa Kinara", 200)
def kwanzaa():
    out = []
    xs = [11, 18, 25, 32, 39, 46, 53]
    cols = [R, R, R, Wh, G, G, G]   # black candle shown white so it is visible
    order = [3, 2, 4, 1, 5, 0, 6]
    for t in range(18):
        f = blank()
        line(f, 10, 13, 54, 13, Y); rect(f, 14, 14, 37, 2, Y)
        for x, c in zip(xs, cols):
            line(f, x, 6, x, 12, c)
            put(f, x + 1, 12, c)
            line(f, x + 1, 6, x + 1, 11, c)
        lit = min(7, t // 2 + 1)
        for k in range(lit):
            flame(f, xs[order[k]], 5, t, k)
            flame(f, xs[order[k]] + 1, 5, t, k + 3)
        out.append(f)
    return out


@anim("Holidays", "Diwali Diyas", 120)
def diwali():
    DIYA = sprite(["#.....#", ".#####.", "..###.."])
    out = []
    for t in range(16):
        f = blank()
        for i, x in enumerate((2, 16, 41, 55)):
            draw(f, DIYA, x, 12, color=[R, M, Y, R][i])
            flame(f, x + 3, 11, t, i)
        rg = Rng(100 + t)
        for _ in range(6):  # sparkles
            put(f, rg.i(0, W), rg.i(0, 9), rg.pick([Y, Wh, M]))
        text_c(f, "DIWALI", 2, lambda i: [Y, R, M][(i + t) % 3], x0=10, x1=54)
        out.append(f)
    return out
