"""Built-in 16x64 animation library and the date-aware 'idle' picker."""
from __future__ import annotations

import datetime as dt
import json
import random
from pathlib import Path

_LIB: list[dict] | None = None


def load() -> list[dict]:
    """Blocking (file I/O) - call from an executor."""
    global _LIB
    if _LIB is None:
        data = json.loads((Path(__file__).parent / "animations.json").read_text(encoding="utf-8"))
        _LIB = data["animations"]
    return _LIB


def names(lib: list[dict]) -> list[str]:
    return [a["name"] for a in lib]


def find(lib: list[dict], name: str) -> dict | None:
    key = name.strip().lower()
    for a in lib:
        if a["name"].lower() == key or a["id"] == key:
            return a
    for a in lib:
        if key in a["name"].lower():
            return a
    return None


def frames(anim: dict) -> list[list[list[int]]]:
    w, h = anim["width"], anim["height"]
    out = []
    for hx in anim["frames"]:
        b = bytes.fromhex(hx)
        px = []
        for v in b:
            px += [(v >> 4) & 7, v & 7]
        out.append([px[y * w:(y + 1) * w] for y in range(h)])
    return out


# ---------------------------------------------------------------- calendar
def _nth_weekday(year: int, month: int, weekday: int, n: int) -> dt.date:
    d = dt.date(year, month, 1)
    d += dt.timedelta(days=(weekday - d.weekday()) % 7)
    return d + dt.timedelta(weeks=n - 1)


def _last_weekday(year: int, month: int, weekday: int) -> dt.date:
    d = dt.date(year + (month == 12), month % 12 + 1, 1) - dt.timedelta(days=1)
    return d - dt.timedelta(days=(d.weekday() - weekday) % 7)


def _easter(year: int) -> dt.date:
    a = year % 19; b, c = divmod(year, 100); d, e = divmod(b, 4)
    f = (b + 8) // 25; g = (b - f + 1) // 3; h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4); l = (32 + 2 * e + 2 * i - h - k) % 7; m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = (h + l - 7 * m + 114) % 31 + 1
    return dt.date(year, month, day)


# lunisolar holidays: published dates
_LUNAR_NY = {2026: (2, 17), 2027: (2, 6), 2028: (1, 26), 2029: (2, 13), 2030: (2, 3), 2031: (1, 23), 2032: (2, 11)}
_HANUKKAH = {2026: (12, 4), 2027: (12, 24), 2028: (12, 12), 2029: (12, 1), 2030: (12, 20), 2031: (12, 9), 2032: (11, 27)}
_DIWALI = {2026: (11, 8), 2027: (10, 29), 2028: (10, 17), 2029: (11, 5), 2030: (10, 26), 2031: (11, 14), 2032: (11, 2)}

HOLIDAY_SETS: dict[str, list[str]] = {
    "new_year": ["New Year's Fireworks", "Ball Drop Countdown", "New Year, Same Me", "Resolutions 404"],
    "mlk": ["MLK Day - Dream"],
    "lunar_new_year": ["Lunar New Year Lanterns"],
    "groundhog": ["Groundhog Day"],
    "valentine": ["Valentine's Heartbeat", "Cupid's Arrow"],
    "pi_day": ["Pi Day"],
    "st_patrick": ["St. Patrick's Rainbow", "Wear Green or Get Pinched"],
    "easter": ["Easter Egg Hatch", "Hopping Bunny"],
    "earth_day": ["Earth Day"],
    "cinco": ["Cinco de Mayo Fiesta"],
    "mothers_day": ["Mother's Day Flowers"],
    "memorial": ["Memorial Day"],
    "fathers_day": ["Father's Day"],
    "juneteenth": ["Juneteenth"],
    "july4": ["4th of July", "Firework Fail"],
    "labor": ["Labor Day Gears"],
    "halloween": ["Jack-o'-Lanterns", "Bats Over the Moon", "Boo! Ghost", "Spiders", "Trick or Treat",
                  "Witch's Cauldron", "Glowing Skull", "Pumpkin Spice Level", "Sugar Rush",
                  "Peekaboo Ghost", "Zombie Hands"],
    "diwali": ["Diwali Diyas"],
    "veterans": ["Veterans Day"],
    "thanksgiving": ["Thanksgiving Turkey", "Turkey Says Eat Pizza", "Food Coma", "Leftovers Again"],
    "black_friday": ["Black Friday Sale"],
    "hanukkah": ["Hanukkah Menorah", "Spinning Dreidel"],
    "christmas": ["Christmas Tree & Snow", "Santa.exe Loading", "Catch Me Gingerbread", "Red Nose Reindeer",
                  "Florida Snowman", "Ugly Sweater", "Sleeps Till Christmas"],
    "kwanzaa": ["Kwanzaa Kinara"],
}


def holidays_on(day: dt.date) -> list[str]:
    """Holiday keys whose 'season' includes this date (several can overlap)."""
    y = day.year
    hits: list[str] = []

    def within(start: dt.date, before: int = 0, after: int = 0, key: str = "") -> None:
        if start - dt.timedelta(days=before) <= day <= start + dt.timedelta(days=after):
            hits.append(key)

    within(dt.date(y, 1, 1), 0, 2, "new_year"); within(dt.date(y, 12, 31), 0, 0, "new_year")
    within(_nth_weekday(y, 1, 0, 3), 1, 0, "mlk")
    if y in _LUNAR_NY:
        within(dt.date(y, *_LUNAR_NY[y]), 2, 5, "lunar_new_year")
    within(dt.date(y, 2, 2), 0, 0, "groundhog")
    within(dt.date(y, 2, 14), 7, 0, "valentine")
    within(dt.date(y, 3, 14), 0, 0, "pi_day")
    within(dt.date(y, 3, 17), 7, 0, "st_patrick")
    within(_easter(y), 7, 1, "easter")
    within(dt.date(y, 4, 22), 0, 0, "earth_day")
    within(dt.date(y, 5, 5), 1, 0, "cinco")
    within(_nth_weekday(y, 5, 6, 2), 6, 0, "mothers_day")
    within(_last_weekday(y, 5, 0), 2, 0, "memorial")
    within(_nth_weekday(y, 6, 6, 3), 6, 0, "fathers_day")
    within(dt.date(y, 6, 19), 0, 0, "juneteenth")
    within(dt.date(y, 7, 4), 6, 1, "july4")
    within(_nth_weekday(y, 9, 0, 1), 2, 0, "labor")
    if day.month == 10 or day == dt.date(y, 11, 1):
        hits.append("halloween")
    if y in _DIWALI:
        within(dt.date(y, *_DIWALI[y]), 2, 2, "diwali")
    within(dt.date(y, 11, 11), 0, 0, "veterans")
    tg = _nth_weekday(y, 11, 3, 4)
    within(tg, 6, 3, "thanksgiving")
    within(tg + dt.timedelta(days=1), 0, 0, "black_friday")
    if y in _HANUKKAH:
        within(dt.date(y, *_HANUKKAH[y]), 1, 8, "hanukkah")
    if y - 1 in _HANUKKAH:        # Hanukkah that started late last December
        within(dt.date(y - 1, *_HANUKKAH[y - 1]), 1, 8, "hanukkah")
    if dt.date(y, 12, 1) <= day <= dt.date(y, 12, 26) and not (tg <= day <= tg + dt.timedelta(days=3)):
        hits.append("christmas")
    if day >= dt.date(y, 12, 26) or day <= dt.date(y, 1, 1):
        hits.append("kwanzaa")
    return hits


CATEGORY_KEYS = {"halloween": "Halloween", "holidays": "Holidays", "reading": "Reading", "optics": "Optics"}


def pick(lib: list[dict], mode: str = "auto", today: dt.date | None = None,
         rng: random.Random | None = None) -> dict:
    """mode: auto | reading | optics | holidays | halloween | any | <animation name>."""
    rng = rng or random.Random()
    mode = (mode or "auto").lower()
    by_name = {a["name"]: a for a in lib}
    if mode in CATEGORY_KEYS:
        pool = [a for a in lib if a["category"] == CATEGORY_KEYS[mode]]
    elif mode == "any":
        pool = list(lib)
    elif mode == "auto":
        pool = []
        for key in holidays_on(today or dt.date.today()):
            pool += [by_name[n] for n in HOLIDAY_SETS.get(key, []) if n in by_name]
        if not pool:   # ordinary day: reading or optics
            pool = [a for a in lib if a["category"] in ("Reading", "Optics")]
    else:
        hit = find(lib, mode)
        pool = [hit] if hit else [a for a in lib if a["category"] in ("Reading", "Optics")]
    return rng.choice(pool)
