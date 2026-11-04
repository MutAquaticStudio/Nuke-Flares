"""OpenFlares reference renderer (numpy). Written from scratch.

Used to design and preview presets, and as the numeric reference for the Blink kernel.
All sizes are relative to image height so presets are resolution independent.
Coordinates follow Nuke: y points up (rows are flipped only when saving PNGs).

Usage:
    python3 -I flare.py ../Presets ../previews [frame]
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image

TWO_PI = 2.0 * math.pi


def _grid(w, h, cx, cy):
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    return (x + 0.5 - cx) / h, (y + 0.5 - cy) / h      # pixel centres, units of image height


def _col(c):
    return np.array(c, np.float32).reshape(1, 1, 3)


def flicker(t, seed, amount, speed):
    a = t * speed * TWO_PI + seed * 17.0
    n = 0.5 * math.sin(a) + 0.3 * math.sin(a * 2.31 + 1.7) + 0.2 * math.sin(a * 5.17 + 4.1)
    return 1.0 - amount * 0.5 * (1.0 + n)


def glow(dx, dy, layers, sc):
    r2 = dx * dx + dy * dy
    out = np.zeros(dx.shape + (3,), np.float32)
    for L in layers:
        s = max(L["radius"] * sc, 1e-4)
        q = r2 / (s * s)
        prof = np.exp(-q * 0.5) + L.get("halo", 0.0) / (1.0 + q) ** 1.5
        out += prof[..., None] * L["intensity"] * _col(L["color"])
    return out


def streak(dx, dy, p, sc, angle_deg):
    a = math.radians(angle_deg)
    u = dx * math.cos(a) + dy * math.sin(a)
    v = -dx * math.sin(a) + dy * math.cos(a)
    t = max(p["thickness"] * sc, 1e-5)
    prof = np.exp(-np.abs(u) / max(p["length"] * sc, 1e-5)) * np.exp(-(v * v) / (2 * t * t))
    return prof[..., None] * p["intensity"] * _col(p["color"])


def starburst(dx, dy, p, sc, rot_deg):
    r = np.sqrt(dx * dx + dy * dy) + 1e-6
    th = np.arctan2(dy, dx) + math.radians(rot_deg)
    n = p["rays"]
    ang = np.abs(np.cos(n * th / 2.0)) ** max(p.get("sharp", 40), 1.0)
    seed = np.float32(p.get("seed", 1))
    h1 = np.sin(seed * np.float32(12.9898)) * np.float32(43758.5453)
    h2 = np.sin(seed * np.float32(78.233)) * np.float32(43758.5453)
    f1 = 0.3 + 0.4 * (h1 - np.floor(h1))                # same hash as the kernel, no RNG
    f2 = TWO_PI * (h2 - np.floor(h2))
    jit = 0.65 + 0.35 * np.cos(th * n * 0.5 * f1 + f2)
    prof = np.exp(-r / max(p["length"] * sc, 1e-5)) * ang * jit
    return prof[..., None] * p["intensity"] * _col(p["color"])


def ghost(dx, dy, g, sc, poly_rot):
    size = max(g["size"] * sc, 1e-5)
    shape = g.get("shape", "disc")
    r = np.sqrt(dx * dx + dy * dy) + 1e-9
    if shape in ("hex", "poly"):
        n = max(int(g.get("sides", 6)), 3)
        th = np.arctan2(dy, dx) - poly_rot
        seg = TWO_PI / n
        edge = size * math.cos(math.pi / n) / np.cos((th - seg * np.floor(th / seg)) - math.pi / n)
        d = (r - edge) / size
    else:
        d = (r - size) / size
    if shape == "ring":
        w = max(g.get("width", 0.12), 1e-3)
        prof = np.exp(-((d / w) ** 2))
    else:
        soft = max(g.get("softness", 0.2), 1e-3)
        prof = 1.0 / (1.0 + np.exp(np.clip(d / soft * 6.0, -40, 40)))
        prof = prof * (0.6 + 0.4 * np.clip(1.0 + d, 0, 1))
        if g.get("rim", 0) > 0:
            prof = prof + g["rim"] * np.exp(-((d / 0.08) ** 2))
    return prof[..., None] * g["intensity"] * _col(g["color"])


def render(preset, w=1280, h=720, light=(0.72, 0.30), frame=0.0):
    """light is given in image fractions with y measured from the TOP (as in a picture)."""
    lx, ly = light[0] * w, (1.0 - light[1]) * h          # -> y-up pixel coordinates
    cx, cy = w / 2.0, h / 2.0
    A = dict(flicker=0.0, flicker_speed=0.15, flicker_seed=0.0, ghost_flicker=0.0, pulse=0.0,
             pulse_speed=0.05, spin_speed=0.0, spin_streak=False, spin_ghosts=False, poly_rotation=0.0)
    A.update(preset.get("animation", {}))
    t = frame
    flick = flicker(t, A["flicker_seed"], A["flicker"], A["flicker_speed"])
    sc = preset.get("scale", 1.0) * (1.0 + A["pulse"] * math.sin(t * A["pulse_speed"] * TWO_PI))
    spin = A["spin_speed"] * t
    star_rot = (preset.get("starburst", {}).get("rotation", 0.0)) + spin
    streak_ang = preset.get("streak", {}).get("angle", 0.0) + (spin if A["spin_streak"] else 0.0)
    poly_rot = math.radians(A["poly_rotation"] + (spin if A["spin_ghosts"] else 0.0))

    out = np.zeros((h, w, 3), np.float32)
    dx, dy = _grid(w, h, lx, ly)
    if "glow" in preset:
        out += glow(dx, dy, preset["glow"], sc)
    if "streak" in preset and preset["streak"]["intensity"] > 0:
        out += streak(dx, dy, preset["streak"], sc, streak_ang)
    if "starburst" in preset and preset["starburst"]["intensity"] > 0:
        out += starburst(dx, dy, preset["starburst"], sc, star_rot)
    for i, g in enumerate(preset.get("ghosts", []), start=1):
        gx = lx + (cx - lx) * g["pos"] * preset.get("ghost_spread", 1.0)
        gy = ly + (cy - ly) * g["pos"] * preset.get("ghost_spread", 1.0)
        gdx, gdy = _grid(w, h, gx, gy)
        gf = flicker(t, A["flicker_seed"] + 1.37 * i, A["ghost_flicker"], A["flicker_speed"])
        out += ghost(gdx, gdy, g, sc, poly_rot) * gf
    out *= _col(preset.get("tint", [1, 1, 1])) * (preset.get("master", 1.0) * flick)
    return out


def tonemap(img):
    img = 1.0 - np.exp(-img * 1.15)
    img = np.clip(img, 0, 1) ** (1 / 2.2)
    return (img[::-1] * 255 + 0.5).astype(np.uint8)     # flip y-up -> picture rows


def main(preset_dir, out_dir, frame=0.0):
    os.makedirs(out_dir, exist_ok=True)
    tiles = []
    for fn in sorted(os.listdir(preset_dir)):
        if not fn.endswith(".json"):
            continue
        with open(os.path.join(preset_dir, fn), encoding="utf-8") as f:
            p = json.load(f)
        im = tonemap(render(p, frame=frame))
        Image.fromarray(im).save(os.path.join(out_dir, fn[:-5] + ".png"))
        tiles.append(Image.fromarray(im).resize((480, 270)))
        print("rendered", p.get("name", fn))
    if tiles:
        cols = 3
        rows = (len(tiles) + cols - 1) // cols
        sheet = Image.new("RGB", (480 * cols, 270 * rows))
        for i, t in enumerate(tiles):
            sheet.paste(t, ((i % cols) * 480, (i // cols) * 270))
        sheet.save(os.path.join(out_dir, "_contact_sheet.png"))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], float(sys.argv[3]) if len(sys.argv) > 3 else 0.0)
