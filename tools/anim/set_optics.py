import math
import numpy as np
from pixkit import *
from set_halloween_reading import anim, ANIMS


def level(v):
    """map 0..1 intensity to a 2-step ramp (bright fringes only, easy to see)"""
    if v > 0.8: return Wh
    if v > 0.55: return B
    return K


@anim("Optics", "Prism Dispersion", 90)
def prism():
    out = []
    apex, base_l, base_r = (30, 1), (21, 15), (39, 15)
    for t in range(16):
        f = blank()
        line(f, *apex, *base_l, C); line(f, *apex, *base_r, C); line(f, *base_l, *base_r, C)
        # incoming white beam with travelling bright packet
        for x in range(0, 26):
            y = 13 - x * 0.2
            on = ((x - t * 2) % 8) < 5
            put(f, x, y, Wh if on else K)
        # refracted inside the glass
        line(f, 25, 8, 33, 7, Wh)
        # rainbow fan out of the far face
        for i, col in enumerate(RAINBOW):
            ang = -0.33 + i * 0.13
            for d in range(0, 32):
                x = 34 + d
                y = 7 + d * math.tan(ang)
                if ((d - t * 2) % 8) < 6:
                    put(f, x, y, col)
        out.append(f)
    return out


@anim("Optics", "Mode-Locked Laser", 70)
def laser_cavity():
    out = []
    L0, L1 = 3, 40
    n = 2 * (L1 - L0 - 2) // 3
    for t in range(n):
        f = blank()
        rect(f, L0, 3, 2, 11, Wh)      # HR mirror
        rect(f, L1, 3, 2, 11, C)       # output coupler
        rect(f, 16, 5, 10, 7, M, fill=False)  # gain crystal
        for xx in range(L0 + 2, L1):
            if xx % 2 == 0:
                put(f, xx, 8, R)
        # pulse bouncing back and forth (3 px per frame)
        span = L1 - L0 - 3
        p = (t * 3) % (2 * span)
        x = L0 + 2 + (p if p < span else 2 * span - p)
        for k in range(4):
            xx = x + (k if p >= span else -k)
            put(f, xx, 8, Wh if k < 2 else Y)
            if k < 2:
                put(f, xx, 7, Y); put(f, xx, 9, Y)
        # emitted pulse train to the right (one pulse per round trip)
        for k in range(4):
            ex = L1 + 2 + ((t * 3 - 0) % (2 * span)) // 2 + k * 12 - 12
            if L1 + 2 <= ex < W:
                for d in range(3):
                    put(f, ex + d, 8, Wh if d == 1 else R)
                put(f, ex + 1, 7, R); put(f, ex + 1, 9, R)
        out.append(f)
    return out


@anim("Optics", "Two-Source Interference", 100)
def interference():
    out = []
    yy, xx = np.mgrid[0:H, 0:W]
    s1, s2 = (-3, 1), (-3, 14)
    k = 2 * math.pi / 7.0
    for t in range(12):
        ph = 2 * math.pi * t / 12
        r1 = np.hypot(xx - s1[0], yy - s1[1]); r2 = np.hypot(xx - s2[0], yy - s2[1])
        field = np.cos(k * r1 - ph) + np.cos(k * r2 - ph)
        inten = (field / 2) ** 2
        f = blank()
        for y in range(H):
            for x in range(W):
                f[y, x] = level(inten[y, x])
        out.append(f)
    return out


@anim("Optics", "Lens Focus", 80)
def lens():
    out = []
    lx, fx = 22, 46
    for t in range(16):
        f = blank()
        # biconvex lens
        for y in range(1, 15):
            w = round(2 * math.sqrt(max(0, 1 - ((y - 8) / 7) ** 2)))
            for dx in range(-w, w + 1):
                put(f, lx + dx, y, C)
        for h in (3, 6, 10, 13):
            for x in range(0, W):
                if x < lx:
                    y = h
                else:
                    y = h + (8 - h) * (x - lx) / (fx - lx)
                if ((x - t * 2) % 8) < 5:
                    put(f, x, y, R if abs(h - 8) > 3 else Y)
        put(f, fx, 8, Wh); put(f, fx, 7, Wh if t % 2 else Y)
        out.append(f)
    return out


@anim("Optics", "Fiber TIR", 70)
def fiber():
    out = []
    for t in range(16):
        f = blank()
        for x in range(W):
            put(f, x, 3, B); put(f, x, 12, B)       # core/cladding boundary
            put(f, x, 1, C if x % 4 == 0 else K)
            put(f, x, 14, C if x % 4 == 0 else K)
        # zig-zag ray: slope 1, bouncing between y=4 and y=11
        for x in range(W):
            p = (x + 3) % 14
            y = 4 + (p if p < 7 else 14 - p)
            d = (x - t * 4) % 32
            if d < 10:
                put(f, x, y, Wh if d > 7 else G)
        out.append(f)
    return out


@anim("Optics", "Frequency Comb", 90)
def comb():
    out = []
    for t in range(16):
        f = blank()
        off = t % 4  # comb offset sliding (f_ceo)
        for i in range(0, W, 4):
            x = i + off
            env = math.exp(-((x - 32) / 16) ** 2)
            h = max(1, round(env * 13))
            col = RAINBOW[min(5, x * 6 // W)]
            for y in range(15 - h, 15):
                put(f, x, y, col)
        for x in range(W):
            put(f, x, 15, Wh)
        out.append(f)
    return out


@anim("Optics", "Heterodyne Beat Note", 70)
def beat():
    """cos(k1 u) + cos(k2 u) = 2 cos((k1-k2)u/2) cos((k1+k2)u/2): carrier inside its beat envelope."""
    k1, k2 = 2 * math.pi / 5.0, 2 * math.pi / 6.0      # beat period = 30 px
    A = 3.5                                             # 2A = 7 px half-height, centre row 7.5
    frames = 30                                         # one full beat period -> seamless loop
    out = []
    for t in range(frames):
        f = blank()
        prev = None
        for x in range(W):
            u = x + t
            env = 2 * abs(math.cos((k1 - k2) * u / 2))
            put(f, x, round(7.5 - A * env), M)
            put(f, x, round(7.5 + A * env), M)
        for x in range(W):
            u = x + t
            y = round(7.5 - A * (math.cos(k1 * u) + math.cos(k2 * u)))
            if prev is not None:
                line(f, x - 1, prev, x, y, Y)
            else:
                put(f, x, y, Y)
            prev = y
        out.append(f)
    return out


@anim("Optics", "Double-Slit", 100)
def double_slit():
    out = []
    yy, xx = np.mgrid[0:H, 0:W]
    bx, slits = 12, (4, 11)
    k = 2 * math.pi / 6.0
    for t in range(12):
        ph = 2 * math.pi * t / 12
        f = blank()
        # plane waves before the barrier
        for x in range(bx):
            if math.cos(k * x - ph) > 0.6:
                for y in range(H):
                    put(f, x, y, B)
        r1 = np.hypot(xx - bx, yy - slits[0]); r2 = np.hypot(xx - bx, yy - slits[1])
        field = np.cos(k * r1 - ph) + np.cos(k * r2 - ph)
        inten = (field / 2) ** 2
        for y in range(H):
            for x in range(bx + 1, W):
                f[y, x] = level(inten[y, x])
        for y in range(H):
            if y not in slits:
                put(f, bx, y, Y)
        out.append(f)
    return out


@anim("Optics", "Spectrum Sweep", 110)
def spectrum_text():
    out = []
    for t in range(12):
        f = blank()
        text_c(f, "LIGHT", 1, lambda i: RAINBOW[(i + t) % 6])
        for x in range(W):
            put(f, x, 11 + (x + t) % 2, RAINBOW[((x // 4) + t) % 6])
            put(f, x, 13 + (x + t + 1) % 2, RAINBOW[((x // 4) + t + 3) % 6])
        out.append(f)
    return out
