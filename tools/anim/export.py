"""Build animations.json (app asset) + GIF previews + a contact sheet."""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(__file__))
from pixkit import H, W
import set_halloween_reading, set_optics, set_holidays, set_memes
from set_halloween_reading import ANIMS

OUT = sys.argv[1]
os.makedirs(f"{OUT}/gif", exist_ok=True)
RGB = {i: ((255 if i & 1 else 0), (255 if i & 2 else 0), (255 if i & 4 else 0)) for i in range(8)}

def render(frame, scale=8):
    img = Image.new("RGB", (W * scale, H * scale), (10, 10, 14))
    d = ImageDraw.Draw(img)
    for y in range(H):
        for x in range(W):
            c = RGB[int(frame[y, x])] if frame[y, x] else (32, 32, 38)
            d.ellipse([x*scale+1, y*scale+1, x*scale+scale-2, y*scale+scale-2], fill=c)
    return img

def slug(s):
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in s).strip("_").replace("__", "_")

lib = []
for a in ANIMS:
    frames = a["fn"]()
    assert all(f.shape == (H, W) for f in frames)
    assert 1 <= len(frames) <= 32, (a["name"], len(frames))
    # 4 bits per pixel, row-major, two pixels per byte, hex encoded
    enc = []
    for f in frames:
        flat = f.flatten()
        enc.append(bytes((int(flat[i]) << 4) | int(flat[i+1]) for i in range(0, len(flat), 2)).hex())
    sid = slug(a["category"] + "_" + a["name"])
    lib.append(dict(id=sid, name=a["name"], category=a["category"], speedMs=a["speed"],
                    width=W, height=H, frames=enc))
    imgs = [render(f, 6) for f in frames]
    imgs[0].save(f"{OUT}/gif/{sid}.gif", save_all=True, append_images=imgs[1:], duration=a["speed"], loop=0)
    print(f'{a["category"]:10s} {a["name"]:28s} {len(frames):3d} frames')

json.dump(dict(version=1, animations=lib), open(f"{OUT}/animations.json", "w"), separators=(",", ":"))
print(len(lib), "animations")
