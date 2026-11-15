import math
import numpy as np
from pixkit import *
from set_halloween_reading import anim, ANIMS

HEART = sprite([".##.##.", "#######", "#######", ".#####.", "..###..", "...#..."])


def caption(f, lines, color, x0=0, x1=W):
    """1 line -> vertically centred; 2 lines -> top/bottom."""
    if isinstance(lines, str):
        lines = [lines]
    if len(lines) == 1:
        text_c(f, lines[0], 4, color, x0=x0, x1=x1)
    else:
        text_c(f, lines[0], 0, color if not isinstance(color, tuple) else color[0], x0=x0, x1=x1)
        text_c(f, lines[1], 9, color if not isinstance(color, tuple) else color[1], x0=x0, x1=x1)


def page(t, pages, period):
    return pages[(t // period) % len(pages)]


def bar(f, x, y, w, h, frac, col, frame_col=Wh):
    rect(f, x, y, w, h, frame_col, fill=False)
    fill = int(round((w - 2) * max(0, min(1, frac))))
    if fill > 0:
        rect(f, x + 1, y + 1, fill, h - 2, col)


def typewriter(f, s, y, t, color, x=0, cps=1):
    n = min(len(s), t * cps)
    end = text(f, s[:n], x, y, color)
    if t % 2 == 0 and n < len(s) + 1:
        line(f, end, y, end, y + 6, Wh)


BOOK_OPEN = sprite([
    "WWWWWWW.WWWWWWW",
    "W.....WRW.....W",
    "W.BBB.WRW.BBB.W",
    "W.....WRW.....W",
    "W.BBB.WRW.BBB.W",
    "W.....WRW.....W",
    "WWWWWWWRWWWWWWW",
])

# =================================================================== READING MEMES


@anim("Reading", "One More Chapter... 3 AM", 220)
def three_am():
    out = []
    for t in range(16):
        f = blank()
        if t < 8:
            draw(f, BOOK_OPEN, 1, 4)
            caption(f, ["ONE MORE", "CHAPTER"], (Wh, Y), x0=17)
        else:
            disc(f, 7, 8, 6.5, Wh); disc(f, 7, 8, 5.5, K)
            line(f, 7, 8, 7, 4, Y); line(f, 7, 8, 10, 8, Y)  # 3 o'clock hands
            put(f, 7, 8, R)
            caption(f, ["IT IS", "3:00 AM"], (Wh, R if t % 2 else M), x0=15)
        out.append(f)
    return out


@anim("Reading", "TBR Pile", 160)
def tbr():
    cols = [R, B, G, M, C, Y, Wh]
    out = []
    for t in range(24):
        f = blank()
        n = min(13, t // 1 + 1) if t < 16 else 13
        lean = 0 if t < 16 else (t - 15)
        for i in range(n):
            x = 3 + (i % 2) + (round(lean * i / 6) if t >= 16 else 0)
            y = 15 - i
            line(f, x, y, x + 9, y, cols[i % 7])
        caption(f, ["TBR PILE", "GROWING"], (Wh, Y if t % 4 < 2 else R), x0=16)
        out.append(f)
    return out


@anim("Reading", "Plot Twist!", 110)
def plot_twist():
    out = []
    for t in range(16):
        f = blank()
        jx = [0, 1, -1, 1, 0, -1][t % 6] if t >= 6 else 0
        if t < 6:
            text_c(f, "PLOT", 4, Wh)
        else:
            text_c(f, "TWIST!", 4, [R, Y, M][t % 3], x0=jx, x1=W + jx)
            for k in range(8):
                a = 2 * math.pi * k / 8 + t * 0.3
                r = 3 + (t - 6) * 2
                put(f, 32 + r * math.cos(a) * 1.8, 8 + r * math.sin(a) * 0.5, Y)
        out.append(f)
    return out


@anim("Reading", "No Spoilers", 180)
def no_spoilers():
    out = []
    for t in range(12):
        f = blank()
        disc(f, 7, 8, 6.5, R); disc(f, 7, 8, 5, K)
        line(f, 3, 4, 11, 12, R); line(f, 3, 5, 10, 12, R)
        caption(f, ["NO", "SPOILERS"] if t < 8 else ["LA LA", "LA LA!"], (Wh, R if t % 2 else Y), x0=15)
        out.append(f)
    return out


MAG = sprite([".###..", "#...#.", "#...#.", "#...#.", ".###..", "....#.", ".....#"])


@anim("Reading", "Where's My Bookmark?", 120)
def bookmark():
    out = []
    for t in range(24):
        f = blank()
        x = 2 + round((math.sin(t * 0.35) + 1) * 26)
        draw(f, MAG, x, 7 + round(math.sin(t * 0.7)), color=C)
        text_c(f, "BOOKMARK?", 0, Y)
        if t > 18:
            line(f, 58, 9, 58, 15, R); put(f, 57, 15, R); put(f, 59, 15, R)  # found it
        out.append(f)
    return out


CAT = sprite([
    "#.....#.......",
    "##...##.......",
    "#######.......",
    "#G###G#.......",
    "###R###########",
    ".#############.",
    "..###########..",
    "..#.#.....#.#..",
])


@anim("Reading", "Cat on My Book", 200)
def cat_book():
    out = []
    for t in range(16):
        f = blank()
        draw(f, BOOK_OPEN, 1, 9)
        draw(f, CAT, 1, 2 + (1 if t % 8 == 4 else 0), color=Y)
        if t % 8 in (6, 7):  # slow blink
            put(f, 2, 5, Y); put(f, 6, 5, Y)
        if (t // 4) % 2:   # tail flick
            put(f, 15, 4, Y); put(f, 16, 3, Y)
        caption(f, ["MOVE?", "NOPE."] if t >= 8 else ["I WAS", "READING"], (Wh, M), x0=18)
        out.append(f)
    return out


@anim("Reading", "Reading 99%", 140)
def reading_99():
    out = []
    for t in range(24):
        f = blank()
        frac = min(0.99, t / 12)
        bar(f, 2, 10, 60, 5, frac, G if frac < 0.99 else Y)
        if t < 18:
            text(f, "READING", 2, 0, Wh)
            pct = f"{int(frac * 100)}"
            mini(f, pct.rjust(2), 50, 1, Y)
        else:
            text_c(f, "NEW BOOK!", 0, M if t % 2 else C)
        out.append(f)
    return out


@anim("Reading", "Shhh! Library", 200)
def shhh():
    out = []
    for t in range(12):
        f = blank()
        n = 1 + t % 6
        text(f, "S" + "H" * n, 2, 4, [Wh, C, B][min(2, n // 3)])
        if t % 6 == 5:
            text(f, "!", 2 + 6 * (n + 1), 4, R)
        out.append(f)
    return out


MUG = sprite(["#######.", "#######.", "#######.", "#######WW", "#######.W", "#######WW", ".#####..."])


@anim("Reading", "Books & Coffee", 160)
def coffee():
    out = []
    for t in range(16):
        f = blank()
        draw(f, MUG, 2, 8, color=R)
        for k, x in enumerate((3, 5, 7)):
            for j in range(3):
                y = 6 - ((t + k * 2 + j * 2) % 6)
                if y >= 0:
                    put(f, x + round(math.sin((y + t) * 0.9)), y, Wh if j else C)
        caption(f, ["BOOKS &", "COFFEE"], (Y, R), x0=13)
        out.append(f)
    return out


@anim("Reading", "Five More Pages", 260)
def five_pages():
    out = []
    seq = [5, 4, 3, 2, 1, 0, 5, 5]
    for t in range(16):
        f = blank()
        n = seq[t % 8] if t < 8 else seq[(t + 3) % 8]
        text(f, "PAGES", 2, 0, Wh)
        text(f, "LEFT:", 2, 9, Wh)
        text(f, str(n), 38, 4, R if n == 0 else Y)
        text(f, "OK" if n == 0 else "", 48, 4, G)
        if n == 5 and t >= 5:
            text(f, "?!", 47, 4, M)
        out.append(f)
    return out


@anim("Reading", "Book Hangover", 150)
def hangover():
    out = []
    for t in range(16):
        f = blank()
        draw(f, BOOK_OPEN, 1, 8)
        for k in range(3):
            a = t * 0.5 + k * 2.1
            put(f, 8 + 6 * math.cos(a), 4 + 2 * math.sin(a), Y)
        caption(f, ["BOOK", "HANGOVER"], (Wh, B if t % 2 else M), x0=16)
        out.append(f)
    return out


@anim("Reading", "Shelf Full?", 150)
def shelf():
    cols = [R, G, B, Y, M, C, Wh]
    out = []
    for t in range(20):
        f = blank()
        line(f, 0, 15, 63, 15, Y); line(f, 0, 0, 0, 15, Y); line(f, 63, 0, 63, 15, Y)
        n = min(30, t * 2)
        x = 2
        for i in range(n):
            h = 7 + (i % 2)
            w = 2 if t < 15 else 1      # squeeze one more in
            rect(f, x, 15 - h, w, h, cols[i % 7])
            x += w
        if t >= 15:
            text_c(f, "ONE MORE", 1, Wh)
        out.append(f)
    return out


@anim("Reading", "I Love Books", 130)
def love_books():
    beat = [1, 0, 1, 0, 0, 0]
    out = []
    for t in range(12):
        f = blank()
        text(f, "I", 4, 4, Wh)
        draw(f, HEART, 12, 5, color=R if beat[t % 6] else M)
        if beat[t % 6]:
            put(f, 11, 6, R); put(f, 19, 6, R)
        text(f, "BOOKS", 24, 4, lambda i: [Y, C, G, M, B][(i + t) % 5])
        out.append(f)
    return out


@anim("Reading", "E-Reader Battery 1%", 180)
def battery():
    out = []
    for t in range(16):
        f = blank()
        lvl = max(0.02, 1 - t / 10)
        rect(f, 1, 4, 15, 8, Wh, fill=False); rect(f, 16, 6, 2, 4, Wh)
        col = G if lvl > 0.5 else (Y if lvl > 0.2 else R)
        if t < 10 or t % 2:
            rect(f, 2, 5, max(1, round(13 * lvl)), 6, col)
        caption(f, ["1 MORE", "PAGE..."] if t >= 10 else ["BATTERY", "LOW"], (Wh, R), x0=19)
        out.append(f)
    return out


@anim("Reading", "Nom Nom Bookworm", 110)
def nom():
    out = []
    word = "LITERATURE"
    for t in range(24):
        f = blank()
        eaten = t // 2
        visible = "".join(ch if i >= eaten else " " for i, ch in enumerate(word))
        text(f, visible, 2, 2, B, spacing=0)
        hx = 2 + eaten * 5
        for k in range(5):
            put(f, hx - k, 12 + round(math.sin(k + t) * 0.8), G)
        put(f, hx + 1, 11, Wh); put(f, hx + 1, 12, K)
        if t % 2:
            text(f, "NOM", 40, 9, Y) if hx < 34 else text(f, "NOM", 4, 9, Y)
        out.append(f)
    return out


@anim("Reading", "Reading Is Lit", 120)
def lit():
    out = []
    for t in range(16):
        f = blank()
        draw(f, BOOK_OPEN, 1, 8)
        for k, x in enumerate((4, 8, 12)):
            flame(f, x, 7, t, k)
            put(f, x, 4 - (t + k) % 3, R if (t + k) % 2 else Y)
        caption(f, ["READING", "IS LIT"], (Wh, lambda i: [R, Y][(i + t) % 2]), x0=17)
        out.append(f)
    return out


# =================================================================== OPTICS MEMES


@anim("Optics", "Wave or Particle?", 200)
def wave_particle():
    out = []
    for t in range(18):
        f = blank()
        ph = (t // 6) % 3
        if ph == 0:
            for x in range(36):
                put(f, x, 8 + round(3 * math.sin(x * 0.5 - t)), C)
            caption(f, "WAVE?", Wh, x0=36)
        elif ph == 1:
            disc(f, (t % 6) * 11 + 3, 13, 1.5, Y)
            text_c(f, "PARTICLE?", 1, Wh)
        else:
            for x in range(0, 30):
                put(f, x, 8 + round(3 * math.sin(x * 0.5 - t)), C)
            disc(f, 32, 8, 1.5, Y)
            caption(f, "YES.", G, x0=38)
        out.append(f)
    return out


EYE = sprite([".#####.", "#.....#", "#.BBB.#", "#.BWB.#", "#.BBB.#", "#.....#", ".#####."])


@anim("Optics", "Do Not Look Into Laser", 200)
def laser_eye():
    out = []
    pages = [["DO NOT", "LOOK INTO"], ["LASER", "WITH YOUR"], ["REMAINING", "EYE"]]
    for t in range(18):
        f = blank()
        draw(f, EYE, 0, 4, color=Wh)
        for x in range(8, 16):
            if (x + t) % 3:
                put(f, x, 7, R)
        caption(f, page(t, pages, 6), (Y, R), x0=16)
        out.append(f)
    return out


@anim("Optics", "Alignment Hell", 140)
def alignment():
    out = []
    offs = [5, 4, -3, 3, -2, 1, -1, 0, 0, 0, 0, 4]
    for t in range(24):
        f = blank()
        o = offs[t // 2]
        # iris
        for y in range(16):
            if abs(y - 8) > 1:
                put(f, 22, y, Wh)
        for x in range(0, 22):
            put(f, x, 8 + o * x / 22, R)
        if abs(o) <= 1:
            for x in range(23, 30):
                put(f, x, 8 + o * x / 22, R)
        if t // 2 in (7, 8, 9, 10):
            caption(f, ["ALIGNED!", ""], (G, G), x0=30)
        elif t // 2 == 11:
            caption(f, ["WHO", "BUMPED IT"], (R, R), x0=26)
        else:
            caption(f, ["ALMOST", "THERE"], (Y, Wh), x0=30)
        out.append(f)
    return out


@anim("Optics", "Snell's Law", 120)
def snell():
    out = []
    for t in range(16):
        f = blank()
        for x in range(32, 64):
            for y in range(16):
                if (x + y) % 6 == 0:
                    put(f, x, y, B)
        for x in range(64):
            y = x * 0.25 if x < 32 else 8 + (x - 32) * 0.12
            if (x - t * 3) % 10 < 7:
                put(f, x, y, Y)
        text(f, "N1", 2, 9, Wh); text(f, "N2", 50, 0, C)
        out.append(f)
    return out


@anim("Optics", "Speed of Light", 80)
def speed_light():
    out = []
    for t in range(16):
        f = blank()
        x = (t * 8) % 80 - 8
        for k in range(12):
            put(f, x - k, 4, Wh if k < 3 else Y)
            put(f, x - k - 2, 3 + (k % 2), Y if k % 3 == 0 else K)
        mini(f, "299792458", 0, 10, C)
        text(f, "M/S", 40, 9, Wh)
        out.append(f)
    return out


@anim("Optics", "Doppler Shift", 110)
def doppler():
    out = []
    for t in range(16):
        f = blank()
        sx = 16 + t
        disc(f, sx, 8, 1.5, Wh)
        for k in range(1, 7):
            age = (k * 4 + t) % 24
            r = age * 1.2
            ex = sx - age * 0.7   # emitted when source was further left
            for a in range(0, 360, 12):
                rad = math.radians(a)
                x = ex + r * math.cos(rad); y = 8 + r * math.sin(rad)
                put(f, x, y, B if x > sx else R)
        out.append(f)
    return out


@anim("Optics", "Crossed Polarizers", 160)
def polarizers():
    out = []
    for t in range(16):
        f = blank()
        th = math.pi * t / 16
        # first polariser fixed vertical, second rotates
        line(f, 8, 2, 8, 13, C)
        cx, cy = 26, 8
        line(f, cx - 5 * math.sin(th), cy - 5 * math.cos(th), cx + 5 * math.sin(th), cy + 5 * math.cos(th), M)
        I = math.cos(th) ** 2
        for x in range(0, 8):
            put(f, x, 8, Wh)
        for x in range(9, 22):
            put(f, x, 8, Y)
        if I > 0.15:
            for x in range(31, 64):
                put(f, x, 8, Y if I > 0.5 else R)
        bar(f, 40, 11, 22, 4, I, Y)
        text(f, "MALUS", 34, 0, Wh) if I < 0.15 else None
        out.append(f)
    return out


@anim("Optics", "Michelson Fringes", 100)
def michelson():
    out = []
    for t in range(10):
        f = blank()
        for y in range(H):
            for x in range(W):
                r = math.hypot((x - 32) * 0.5, y - 7.5)
                v = math.cos(r * r * 0.07 - t * 2 * math.pi / 10)
                if v > 0.7:
                    f[y, x] = Wh if v > 0.92 else R
        out.append(f)
    return out


@anim("Optics", "TEM00 Gaussian", 160)
def gaussian():
    out = []
    for t in range(16):
        f = blank()
        w = 6 + 2 * math.sin(t * 2 * math.pi / 16)
        for x in range(0, 40):
            h = 13 * math.exp(-2 * ((x - 20) / w) ** 2)
            for y in range(15 - round(h), 15):
                put(f, x, y, R if y > 10 else (Y if y > 5 else Wh))
        line(f, 0, 15, 39, 15, B)
        text(f, "TEM", 42, 0, Wh); mini(f, "00", 45, 9, Y)
        out.append(f)
    return out


@anim("Optics", "Mode Hop!", 150)
def mode_hop():
    out = []
    pos = [10, 10, 10, 10, 26, 26, 26, 42, 42, 18, 18, 34, 34, 34, 10, 50]
    for t in range(16):
        f = blank()
        for x in range(2, 62, 4):
            put(f, x, 15, B)
        x = pos[t]
        line(f, x, 15, x, 5, R)
        put(f, x, 4, Wh)
        text_c(f, "MODE HOP!" if pos[t] != pos[t - 1] else "STABLE", 0, Y if pos[t] != pos[t - 1] else G)
        out.append(f)
    return out


@anim("Optics", "Q-Switch Pew", 110)
def qswitch():
    out = []
    for t in range(20):
        f = blank()
        if t < 12:
            bar(f, 2, 2, 24, 6, t / 11, G if t < 11 else Y)
            text(f, "CHARGING", 2, 9, Wh, spacing=0)
        else:
            for x in range(0, 64):
                h = 6 * math.exp(-((x - (t - 12) * 9) / 3) ** 2)
                for y in range(round(8 - h), round(8 + h) + 1):
                    if h > 0.6:
                        put(f, x, y, Wh if abs(y - 8) < h / 2 else R)
            text(f, "PEW!", 40, 0, M) if t % 2 else None
        out.append(f)
    return out


@anim("Optics", "Fourier Pair", 400)
def fourier():
    out = []
    for t in range(8):
        f = blank()
        short = (t // 4) % 2 == 0
        for x in range(32):
            wt = 1.2 if short else 6
            ws = 8 if short else 2
            ht = 12 * math.exp(-((x - 16) / wt) ** 2)
            hs = 12 * math.exp(-((x - 16) / ws) ** 2)
            for y in range(15 - round(ht), 15):
                put(f, x, y, Y)
            for y in range(15 - round(hs), 15):
                put(f, x + 32, y, RAINBOW[min(5, x // 6)])
        line(f, 31, 0, 31, 15, B)
        text(f, "T", 1, 0, Wh); text(f, "F", 58, 0, Wh)
        out.append(f)
    return out


@anim("Optics", "LIDAR Sweep", 90)
def lidar():
    out = []
    rng = Rng(3)
    objs = [(rng.i(20, 62), rng.i(1, 15)) for _ in range(14)]
    for t in range(24):
        f = blank()
        a = -0.6 + 1.2 * ((t % 12) / 11 if (t // 12) % 2 == 0 else 1 - (t % 12) / 11)
        for d in range(1, 64):
            x, y = 2 + d * math.cos(a), 8 + d * math.sin(a)
            hit = any(abs(x - ox) < 1 and abs(y - oy) < 1 for ox, oy in objs)
            put(f, x, y, G)
            if hit:
                break
        for ox, oy in objs:
            ang = math.atan2(oy - 8, ox - 2)
            if abs(ang - a) < 0.25:
                put(f, ox, oy, Wh)
        rect(f, 0, 7, 3, 3, C)
        out.append(f)
    return out


@anim("Optics", "Einstein Ring", 140)
def einstein_ring():
    out = []
    rng = Rng(9)
    stars = [(rng.i(0, 64), rng.i(0, 16)) for _ in range(16)]
    for t in range(16):
        f = blank()
        for sx, sy in stars:
            x = (sx + t) % 64
            dx, dy = x - 32, sy - 8
            r = math.hypot(dx, dy) + 0.01
            push = 14 / r
            put(f, 32 + dx * (1 + push / r), 8 + dy * (1 + push / r), Wh)
        ring(f, 32, 8, 5 + (t % 4 == 0) * 0.3, Y)
        disc(f, 32, 8, 3, K)
        out.append(f)
    return out


@anim("Optics", "Fabry-Perot Scan", 110)
def fabry_perot():
    out = []
    for t in range(16):
        f = blank()
        for x in range(64):
            ph = (x / 64 * 4 + t / 16) * 2 * math.pi
            T = 1 / (1 + 30 * math.sin(ph / 2) ** 2)
            for y in range(15 - round(T * 14), 16):
                put(f, x, y, C if T > 0.4 else B)
        rect(f, 0, 0, 19, 8, K)
        text(f, "FSR", 1, 0, Wh)
        out.append(f)
    return out


@anim("Optics", "Rainbow in the Rain", 110)
def rain_rainbow():
    out = []
    for t in range(16):
        f = blank()
        for i, col in enumerate(RAINBOW):
            r = 28 - i * 1.5
            for k in range(60):
                a = math.pi * k / 59
                put(f, 32 + r * math.cos(a), 17 - r * math.sin(a) * 0.55, col)
        snow(f, t, seed=4, count=14, color=C, speed=2)
        disc(f, 4, 3, 2.5, Y)
        out.append(f)
    return out


@anim("Optics", "Help, I'm in a Fiber", 120)
def trapped():
    out = []
    for t in range(24):
        f = blank()
        line(f, 0, 0, 63, 0, B); line(f, 0, 15, 63, 15, B)
        for x in range(64):
            p = (x + t * 2) % 10
            y = 2 + (p if p < 5 else 10 - p) * 2.4
            if (x - t * 3) % 30 < 8:
                put(f, x, y, G)
        caption(f, ["HELP I'M", "TIR'D"] if (t // 8) % 3 != 2 else ["TOTAL", "INTERNAL"], (Wh, Y), x0=8, x1=56)
        out.append(f)
    return out


GOGGLES = sprite(["################", "#GGGGG####GGGGG#", "#GGGGG#..#GGGGG#", "#GGGGG#..#GGGGG#", "################"])


@anim("Optics", "Goggles On!", 200)
def goggles():
    out = []
    for t in range(12):
        f = blank()
        draw(f, GOGGLES, 1, 5, color=Wh if t % 2 else Y)
        caption(f, ["GOGGLES", "ON!"], (Wh, R if t % 2 else Y), x0=18)
        out.append(f)
    return out


@anim("Optics", "Constructive vs Destructive", 300)
def con_des():
    out = []
    for t in range(12):
        f = blank()
        des = (t // 6) % 2 == 1
        for x in range(36):
            a = math.sin(x * 0.55 + t)
            b = math.sin(x * 0.55 + t + (math.pi if des else 0))
            put(f, x, 3 - round(a * 2), C)
            put(f, x, 3 - round(b * 2) + 5, M)
            put(f, x, 13 - round((a + b) * 1.4), Wh)
        text(f, "ZERO" if des else "BIG!", 38, 4, R if des else G)
        out.append(f)
    return out


# =================================================================== HOLIDAY MEMES

GROUNDHOG = sprite(["..YY..", ".YYYY.", "YRYYRY", "YYWWYY", ".YYYY.", ".YYYY.", "YYYYYY"])


@anim("Holidays", "Groundhog Day", 180)
def groundhog():
    out = []
    for t in range(16):
        f = blank()
        line(f, 0, 15, 63, 15, G)
        disc(f, 60, 2, 2, Y)  # sun
        up = min(7, t) if t < 12 else max(0, 7 - (t - 12) * 3)
        draw(f, GROUNDHOG, 4, 15 - up)
        if 6 < t < 12:
            for k in range(6):
                put(f, 11 + k, 14, B)   # shadow!
            caption(f, ["6 MORE", "WEEKS"], (Wh, C), x0=14, x1=57)
        else:
            caption(f, "SHADOW?", Wh, x0=12, x1=57)
        out.append(f)
    return out


@anim("Holidays", "Pi Day", 120)
def pi_day():
    digits = "3.14159265358979323846"
    out = []
    for t in range(24):
        f = blank()
        s = digits[: min(len(digits), t + 1)]
        start = max(0, len(s) - 10)
        text(f, s[start:], 0, 0, Y, spacing=1)
        # pie
        for x in range(4, 26):
            put(f, x, 13 + ((x + t) % 3 == 0), Y)
        line(f, 6, 12, 23, 12, R); line(f, 4, 14, 25, 14, Y)
        rect(f, 6, 15, 18, 1, Y)
        text(f, "3/14", 34, 9, M)
        out.append(f)
    return out


@anim("Holidays", "Earth Day", 140)
def earth_day():
    land = [(0, 3, 4), (5, 7, 3), (11, 5, 5), (17, 9, 3), (21, 3, 4), (26, 10, 4)]
    out = []
    for t in range(16):
        f = blank()
        disc(f, 8, 8, 7, B)
        for (lx, ly, ln) in land:
            for k in range(ln):
                x = (lx + k - t) % 32
                if x < 15:
                    xx = 1 + x
                    if (xx - 8) ** 2 + (ly - 8) ** 2 <= 46:
                        put(f, xx, ly, G); put(f, xx, ly + 1, G)
        caption(f, ["EARTH", "DAY"], (G, B), x0=17)
        out.append(f)
    return out


MARACA = sprite(["..###", ".####", ".####", "..##.", ".#...", "#...."])


@anim("Holidays", "Cinco de Mayo Fiesta", 110)
def fiesta():
    out = []
    rng = Rng(5)
    conf = [(rng.i(0, 64), rng.i(0, 16), rng.pick([R, G, Wh, Y, M])) for _ in range(20)]
    for t in range(16):
        f = blank()
        for x, y, c in conf:
            put(f, x, (y + t) % 16, c)
        s = [0, 1][t % 2]
        draw(f, MARACA, 2, 4 + s, color=R)
        draw(f, MARACA, 56, 5 - s, color=G)
        text_c(f, "FIESTA!", 4, lambda i: [G, Wh, R][(i + t) % 3])
        out.append(f)
    return out


@anim("Holidays", "Turkey Says Eat Pizza", 200)
def eat_pizza():
    TURK = sprite(["R.Y.G.R.", ".RYGRY..", "..MMM...", ".MWMMM..", ".MMMMM..", "..Y.Y..."])
    out = []
    for t in range(16):
        f = blank()
        x = 2 + (t % 4 == 1) - (t % 4 == 3)
        draw(f, TURK, x, 5)
        rect(f, 11, 1, 2, 14, Y)            # sign post
        rect(f, 13, 1, 1, 1, Y)
        caption(f, ["EAT", "PIZZA"] if t < 8 else ["NOT", "ME!"], (Wh, R), x0=15)
        out.append(f)
    return out


@anim("Holidays", "Food Coma", 160)
def food_coma():
    out = []
    for t in range(20):
        f = blank()
        frac = min(1, t / 12)
        bar(f, 2, 10, 60, 5, frac, G if frac < 0.7 else (Y if frac < 1 else R))
        text(f, "FOOD COMA" if frac >= 1 and t % 2 else "LOADING", 2, 1, Wh if frac < 1 else M)
        if frac >= 1:
            text(f, "Z", 56, 0 + t % 3, C)
        out.append(f)
    return out


@anim("Holidays", "Black Friday Sale", 100)
def black_friday():
    out = []
    for t in range(12):
        f = blank()
        rect(f, 0, 0, 64, 16, R if t % 2 else K, fill=False)
        text_c(f, "SALE!", 0, Y if t % 2 else Wh)
        text_c(f, "-99%", 9, R if t % 2 else Wh)
        out.append(f)
    return out


@anim("Holidays", "Santa.exe Loading", 160)
def santa_exe():
    out = []
    for t in range(24):
        f = blank()
        frac = min(0.99, t / 14)
        text(f, "SANTA", 2, 0, R)
        bar(f, 2, 9, 44, 6, frac, G)
        mini(f, str(int(frac * 100)).rjust(2), 50, 10, Y)
        if t > 16 and t % 2:
            text(f, "!", 56, 0, Y)
        out.append(f)
    return out


GINGER = [sprite(["..###..", "..W#W..", "#######", "..#R#..", "..###..", ".#...#.", "#.....#"]),
          sprite(["..###..", "..W#W..", ".#####.", "#.#R#.#", "..###..", "..#.#..", "..#.#.."])]


@anim("Holidays", "Catch Me Gingerbread", 90)
def gingerbread():
    out = []
    for t in range(24):
        f = blank()
        x = 70 - t * 3
        draw(f, GINGER[t % 2], x, 8, color=Y)
        text(f, "CATCH ME!", 1, 0, Wh) if (t // 4) % 2 == 0 else text(f, "RUN RUN", 6, 0, R)
        out.append(f)
    return out


DEER = sprite(["#.#........", ".#.#.......", "..##.......", "WW#######..", "R.#######..", "..##...##..", "..#.#.#.#.."])


@anim("Holidays", "Red Nose Reindeer", 100)
def reindeer():
    out = []
    for t in range(24):
        f = blank()
        snow(f, t, seed=12, count=12)
        x = t * 3 - 10
        y = 4 + round(math.sin(t * 0.5) * 2)
        draw(f, DEER, x, y, color=Y)
        put(f, x, y + 4, R if t % 2 else Wh)
        out.append(f)
    return out


SNOWMAN = sprite(["...KKK...", "..KKKKK..", "...WWW...", "..WKWKW..", "..WWYWW..", "...WWW...",
                  "..WWWWW..", ".WWRWWWW.", ".WWWWWWW.", ".WWRWWWW.", "..WWWWW.."])


@anim("Holidays", "Florida Snowman", 220)
def florida_snowman():
    out = []
    for t in range(16):
        f = blank()
        disc(f, 2, 2, 3, Y)
        melt = min(10, max(0, t - 3))
        spr = SNOWMAN[melt:] if melt < len(SNOWMAN) else []
        spr = [[('B' if ch == 'K' else ch) for ch in row] for row in spr]
        draw(f, spr, 4, 5 + melt)
        if melt > 0:
            for k in range(min(16, melt * 2)):
                put(f, 8 - melt + k, 15, C)
        caption(f, ["FLORIDA", "XMAS"], (Y, R if t % 2 else G), x0=18)
        out.append(f)
    return out


@anim("Holidays", "Ugly Sweater", 140)
def ugly_sweater():
    out = []
    for t in range(16):
        f = blank()
        for y in range(16):
            for x in range(64):
                xx = x + t
                if y in (0, 15):
                    put(f, x, y, Wh if xx % 2 else R)
                elif y in (2, 13):
                    put(f, x, y, G if (xx // 2) % 2 else K)
                elif 4 <= y <= 11:
                    d = abs((xx % 8) - 4) + abs(y - 8)
                    if d == 3:
                        put(f, x, y, Wh)
                    elif d <= 1:
                        put(f, x, y, R)
        out.append(f)
    return out


@anim("Holidays", "Sleeps Till Christmas", 250)
def sleeps():
    out = []
    for t in range(20):
        f = blank()
        n = max(0, 9 - t)
        if n > 0:
            text(f, str(n), 2, 4, Y if t % 2 else R)
            caption(f, ["SLEEPS", "TO XMAS"], (Wh, G), x0=9)
        else:
            text_c(f, "XMAS!!", 4, [R, G, Wh][t % 3])
            snow(f, t, count=10)
        out.append(f)
    return out


@anim("Holidays", "New Year, Same Me", 250)
def same_me():
    out = []
    for t in range(16):
        f = blank()
        if t < 8:
            caption(f, ["NEW YEAR", "NEW ME"], (Y, Wh))
        else:
            caption(f, ["NEW YEAR", "SAME ME"], (Y, Wh))
            if t % 2:
                line(f, 8, 12, 25, 12, R)
        out.append(f)
    return out


@anim("Holidays", "Resolutions 404", 200)
def resolutions():
    out = []
    items = ["GYM", "DIET", "READ"]
    for t in range(16):
        f = blank()
        i = (t // 4) % 3
        if t < 12:
            rect(f, 2, 4, 7, 7, Wh, fill=False)
            if t % 4 >= 2:
                line(f, 3, 5, 7, 9, R); line(f, 7, 5, 3, 9, R)
            text(f, items[i], 13, 4, Wh if t % 4 < 2 else R)
            if items[i] == "READ" and t % 4 >= 2:
                rect(f, 3, 5, 5, 5, K); line(f, 3, 7, 5, 9, G); line(f, 5, 9, 8, 4, G)
        else:
            text_c(f, "ERR 404", 4, R)
        out.append(f)
    return out


@anim("Holidays", "Ball Drop Countdown", 300)
def ball_drop():
    out = []
    for t in range(14):
        f = blank()
        n = 10 - t
        line(f, 6, 0, 6, 15, Wh)
        y = min(13, t)
        disc(f, 6, y, 2, [C, M, Y, Wh][t % 4])
        if n > 0:
            text(f, str(n), 14, 4, Y)
            text(f, "TO GO", 32, 4, Wh)
        else:
            text(f, "2027!", 18, 4, lambda i: [R, Y, G, C, M][(i + t) % 5])
            firework(f, 56, 5, t - 10, M)
        out.append(f)
    return out


@anim("Holidays", "Cupid's Arrow", 100)
def cupid():
    out = []
    for t in range(20):
        f = blank()
        hit = t >= 12
        draw(f, HEART, 52, 5, color=R if not hit or t % 2 else M)
        ax = min(48, t * 4)
        line(f, ax - 8, 8, ax, 8, Y)
        put(f, ax + 1, 8, Wh); put(f, ax, 7, Wh); put(f, ax, 9, Wh)
        put(f, ax - 8, 7, M); put(f, ax - 8, 9, M)
        if hit:
            text(f, "BAE", 2, 0, M)
        out.append(f)
    return out


@anim("Holidays", "Wear Green or Get Pinched", 200)
def wear_green():
    out = []
    for t in range(12):
        f = blank()
        caption(f, ["WEAR GREEN", "OR ELSE"] if t < 8 else ["PINCH", "PROOF"], (G, Wh if t < 8 else Y))
        out.append(f)
    return out


BUNNY = [sprite([".#.#...", ".#.#...", ".###...", "#R#R#..", "#####.W", ".#####W", "#.#.#.."]),
         sprite(["..#.#..", ".#.#...", ".###...", "#R#R#..", "#####.W", ".#####W", ".#...#."])]


@anim("Holidays", "Hopping Bunny", 90)
def bunny():
    out = []
    for t in range(24):
        f = blank()
        x = t * 3 - 6
        hop = abs(math.sin(t * math.pi / 4)) * 5
        draw(f, BUNNY[t % 2], x, 8 - round(hop), color=Wh)
        line(f, 0, 15, 63, 15, G)
        for k in range(0, 64, 13):
            disc(f, k + 4, 13, 1.3, [M, C, Y, B, R][(k // 13) % 5])
        out.append(f)
    return out


@anim("Holidays", "Firework Fail", 140)
def firework_fail():
    out = []
    for t in range(16):
        f = blank()
        if t < 5:
            rocket(f, 20, 15, 4, t, 5)
            text(f, "WAIT FOR", 30, 0, Wh, spacing=0)
            text(f, "IT...", 30, 9, Wh)
        elif t < 9:
            put(f, 20 + (t % 2), 4, R)
            text(f, "...", 30, 4, Wh)
        else:
            put(f, 20, 4 + (t - 9) * 2, Wh if t % 2 else K)
            text(f, "OOPS", 30, 4, R)
        out.append(f)
    return out


@anim("Holidays", "Pumpkin Spice Level", 170)
def pumpkin_spice():
    out = []
    for t in range(20):
        f = blank()
        frac = min(1, t / 12)
        for k in range(12):
            if k < frac * 12:
                rect(f, 2, 14 - k, 8, 1, R if k > 8 else (Y if k > 4 else G))
        rect(f, 1, 2, 10, 14, Wh, fill=False)
        caption(f, ["PUMPKIN", "SPICE" if frac < 1 else "MAX!!"], (Y, R if frac >= 1 and t % 2 else Wh), x0=13)
        out.append(f)
    return out


@anim("Holidays", "Sugar Rush", 90)
def sugar_rush():
    out = []
    for t in range(16):
        f = blank()
        jx, jy = [(0, 0), (1, -1), (-1, 1), (1, 1), (-1, -1)][t % 5]
        text_c(f, "SUGAR", 0 + jy, [R, Y, M][t % 3], x0=jx, x1=W + jx)
        text_c(f, "RUSH!", 9 - jy, [C, G, Wh][t % 3], x0=-jx, x1=W - jx)
        out.append(f)
    return out


@anim("Holidays", "Peekaboo Ghost", 160)
def peekaboo():
    G2 = sprite(["..####..", ".######.", "##B##B##", "########", "##.BB.##", "########", "#.#..#.#"])
    out = []
    for t in range(16):
        f = blank()
        rect(f, 28, 0, 8, 16, B)           # wall
        p = [0, 2, 4, 7, 7, 7, 4, 2][t % 8]
        draw(f, G2, 28 - p, 4, color=Wh)
        rect(f, 28, 0, 8, 16, B)
        if p == 7:
            text(f, "BOO", 40, 4, M)
        out.append(f)
    return out


@anim("Holidays", "Zombie Hands", 160)
def zombie():
    HAND = sprite(["#.#.#", "#.#.#", "#####", ".###.", ".###.", ".###.", ".###.", ".###."])
    out = []
    for t in range(16):
        f = blank()
        for i, x in enumerate((4, 24, 44)):
            up = max(0, min(8, (t - i * 3)))
            sh = round(math.sin(t + i))
            draw(f, HAND[:up], x + sh, 16 - up, color=G)
        for x in range(64):
            put(f, x, 15, Y if x % 3 else R)
        if t > 10:
            text(f, "BRAINS", 22, 0, R if t % 2 else M)
        out.append(f)
    return out


@anim("Holidays", "Spinning Dreidel", 110)
def dreidel():
    out = []
    for t in range(16):
        f = blank()
        w = abs(math.cos(t * math.pi / 4))
        hw = max(1, round(5 * w))
        line(f, 10, 1, 10, 3, Y)
        rect(f, 10 - hw, 3, hw * 2 + 1, 7, B if (t // 2) % 2 else C)
        for k in range(4):
            line(f, 10 - hw + k, 10 + k, 10 + hw - k, 10 + k, B if (t // 2) % 2 else C)
        if hw > 2:
            put(f, 10, 6, Wh)
        text(f, "SPIN!", 24, 4, Y if t % 2 else Wh)
        out.append(f)
    return out


@anim("Holidays", "Leftovers Again", 220)
def leftovers():
    out = []
    for t in range(12):
        f = blank()
        rect(f, 2, 3, 14, 12, Wh, fill=False)  # fridge
        line(f, 2, 7, 15, 7, Wh); put(f, 14, 5, Wh); put(f, 14, 10, Wh)
        text_c(f, "LEFTOVER", 0, Y, x0=17)
        text_c(f, "DAY " + str(min(9, t + 1)), 9, Wh, x0=17)
        out.append(f)
    return out
