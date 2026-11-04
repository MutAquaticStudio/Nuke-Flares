"""OpenFlares core - preset <-> kernel parameter mapping. No Nuke dependency."""
import json
import os

N_GLOW = 3
N_GHOST = 8
SHAPES = {"disc": 0, "ring": 1, "hex": 2, "poly": 2, "custom": 3}
SHAPE_NAMES = {0: "disc", 1: "ring", 2: "hex", 3: "custom"}

# per-ghost defaults used for every entry that does not state a value
GHOST_DEFAULTS = {"pos": 0.5, "size": 0.05, "intensity": 0.0, "color": [1.0, 1.0, 1.0],
                  "shape": "disc", "sides": 6, "softness": 0.2, "width": 0.12, "rim": 0.0}
GLOW_DEFAULTS = {"radius": 0.02, "intensity": 0.0, "color": [1.0, 1.0, 1.0], "halo": 0.0}
STREAK_DEFAULTS = {"length": 0.5, "thickness": 0.005, "intensity": 0.0, "color": [1.0, 1.0, 1.0], "angle": 0.0}
STAR_DEFAULTS = {"rays": 8, "length": 0.3, "intensity": 0.0, "color": [1.0, 1.0, 1.0],
                 "sharp": 60.0, "rotation": 0.0, "seed": 1.0}
GLOBAL_KEYS = {"master": "master", "scale": "flareScale", "ghost_spread": "ghostSpread",
               "follow_source": "srcLink", "tint": "globalTint"}
ANIM_KEYS = {"flicker": "flicker_amount", "flicker_speed": "flicker_speed", "flicker_seed": "flicker_seed",
             "ghost_flicker": "ghost_flicker", "pulse": "pulse_amount", "pulse_speed": "pulse_speed",
             "spin_speed": "spin_speed", "spin_streak": "spin_streak", "spin_ghosts": "spin_ghosts",
             "poly_rotation": "poly_rotation"}
ANIM_DEFAULTS = {"flicker": 0.0, "flicker_speed": 0.15, "flicker_seed": 0.0, "ghost_flicker": 0.0, "pulse": 0.0,
                 "pulse_speed": 0.05, "spin_speed": 0.0, "spin_streak": False, "spin_ghosts": False, "poly_rotation": 0.0}
DIRT_KEYS = {"amount": "dirt_amount", "spread": "dirt_spread", "scale": "dirt_scale",
             "offset": "dirt_offset", "tint": "dirt_tint"}
DIRT_DEFAULTS = {"amount": 0.0, "spread": 2.5, "scale": 1.0, "offset": [0.0, 0.0], "tint": [1.0, 1.0, 1.0]}
GLOBAL_DEFAULTS = {"master": 1.0, "scale": 1.0, "ghost_spread": 1.0, "follow_source": 0.0, "tint": [1.0, 1.0, 1.0]}

PRESET_DIR_NAME = "Presets"


def _merge(defaults, given):
    d = dict(defaults)
    d.update(given or {})
    return d


def preset_to_params(preset):
    """Full set of kernel parameters (name -> number or [r,g,b]) for a preset.
    Everything the preset does not mention is reset, so presets never leak into each other."""
    out = {}
    for key, name in GLOBAL_KEYS.items():
        out[name] = preset.get(key, GLOBAL_DEFAULTS[key])

    glows = preset.get("glow", [])
    for i in range(1, N_GLOW + 1):
        g = _merge(GLOW_DEFAULTS, glows[i - 1] if i <= len(glows) else {})
        for k in GLOW_DEFAULTS:
            out["glow%d_%s" % (i, k)] = g[k]

    s = _merge(STREAK_DEFAULTS, preset.get("streak"))
    for k in STREAK_DEFAULTS:
        out["streak_" + k] = s[k]

    st = _merge(STAR_DEFAULTS, preset.get("starburst"))
    out["star_rays"] = st["rays"]
    for k in ("length", "intensity", "color", "sharp", "rotation", "seed"):
        out["star_" + k] = st[k]

    ghosts = preset.get("ghosts", [])
    for i in range(1, N_GHOST + 1):
        g = _merge(GHOST_DEFAULTS, ghosts[i - 1] if i <= len(ghosts) else {})
        for k in GHOST_DEFAULTS:
            v = g[k]
            if k == "shape":
                v = SHAPES.get(v, 0) if isinstance(v, str) else int(v)
            out["ghost%d_%s" % (i, k)] = v

    anim = _merge(ANIM_DEFAULTS, preset.get("animation"))
    for key, name in ANIM_KEYS.items():
        out[name] = anim[key]
    dirt = _merge(DIRT_DEFAULTS, preset.get("dirt"))
    for key, name in DIRT_KEYS.items():
        out[name] = dirt[key]
    return out


def params_to_preset(values, name="My Flare"):
    """Inverse of preset_to_params. values: kernel parameter name -> number or [r,g,b]."""
    p = {"name": name}
    for key, kname in GLOBAL_KEYS.items():
        if kname in values:
            p[key] = values[kname]

    p["glow"] = []
    for i in range(1, N_GLOW + 1):
        if values.get("glow%d_intensity" % i, 0) > 0:
            p["glow"].append({k: values["glow%d_%s" % (i, k)] for k in GLOW_DEFAULTS})

    if values.get("streak_intensity", 0) > 0:
        p["streak"] = {k: values["streak_" + k] for k in STREAK_DEFAULTS}

    if values.get("star_intensity", 0) > 0:
        p["starburst"] = {"rays": int(values["star_rays"]),
                          **{k: values["star_" + k] for k in ("length", "intensity", "color", "sharp", "rotation", "seed")}}

    p["ghosts"] = []
    for i in range(1, N_GHOST + 1):
        if values.get("ghost%d_intensity" % i, 0) > 0:
            g = {k: values["ghost%d_%s" % (i, k)] for k in GHOST_DEFAULTS}
            g["shape"] = SHAPE_NAMES.get(int(g["shape"]), "disc")
            p["ghosts"].append(g)

    anim = {key: values[name] for key, name in ANIM_KEYS.items() if name in values}
    for k in ("spin_streak", "spin_ghosts"):
        if k in anim:
            anim[k] = bool(anim[k])
    if any(anim.get(k, 0) for k in ("flicker", "ghost_flicker", "pulse", "spin_speed")):
        p["animation"] = anim
    if values.get("dirt_amount", 0) > 0:
        p["dirt"] = {key: values[name] for key, name in DIRT_KEYS.items() if name in values}
    return p


def all_param_names():
    return list(preset_to_params({}).keys())


def list_presets(*dirs):
    """[(display name, path)] from the given directories, sorted by file name."""
    found = []
    for d in dirs:
        if not d or not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if fn.lower().endswith(".json"):
                path = os.path.join(d, fn)
                try:
                    with open(path, encoding="utf-8") as fh:
                        name = json.load(fh).get("name") or os.path.splitext(fn)[0]
                except (OSError, ValueError):
                    continue
                found.append((name, path))
    return found


def load_preset(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def save_preset(preset, directory, filename):
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, filename)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(preset, fh, indent=2)
    return path


# --------------------------------------------------------------------------- UI layout (used by the gizmo)
LABELS = {
    "master": "Master Intensity", "flareScale": "Flare Scale", "ghostSpread": "Ghost Spread",
    "srcLink": "Follow Source Brightness", "globalTint": "Global Tint", "flareOnly": "Flare Only",
    "radius": "Radius", "intensity": "Intensity", "color": "Color", "halo": "Halo",
    "length": "Length", "thickness": "Thickness", "angle": "Angle",
    "rays": "Rays", "sharp": "Sharpness", "rotation": "Rotation", "seed": "Seed",
    "pos": "Position", "size": "Size", "shape": "Shape (0 disc, 1 ring, 2 polygon, 3 custom)",
    "sides": "Polygon Sides", "softness": "Softness", "width": "Ring Width", "rim": "Rim",
    "flicker_amount": "Flicker Amount", "flicker_speed": "Flicker Speed", "flicker_seed": "Flicker Seed",
    "ghost_flicker": "Ghost Flicker", "pulse_amount": "Pulse Amount", "pulse_speed": "Pulse Speed",
    "spin_speed": "Spin Speed (deg/frame)", "spin_streak": "Spin Streak", "spin_ghosts": "Spin Polygon/Custom Ghosts",
    "poly_rotation": "Polygon Rotation",
    "dirt_amount": "Dirt Amount", "dirt_spread": "Dirt Spread", "dirt_scale": "Dirt Scale",
    "dirt_offset": "Dirt Offset", "dirt_tint": "Dirt Tint",
}


def label(name):
    if name in LABELS:
        return LABELS[name]
    return LABELS.get(name.split("_", 1)[-1], name)


def _block(prefix, keys):
    return [prefix + k for k in keys]


def ui_tabs():
    """[(tab title, [(group title or None, [param names])])] for the gizmo. lightPos / animTime are handled separately."""
    tabs = [("Flare", [(None, ["master", "flareScale", "ghostSpread", "srcLink", "globalTint", "flareOnly"])]),
            ("Glow", [("Glow %d" % i, _block("glow%d_" % i, GLOW_DEFAULTS)) for i in range(1, N_GLOW + 1)]),
            ("Streak & Star", [("Anamorphic Streak", _block("streak_", STREAK_DEFAULTS)),
                               ("Starburst", _block("star_", STAR_DEFAULTS))])]
    for lo in (1, 5):
        tabs.append(("Ghosts %d-%d" % (lo, lo + 3),
                     [("Ghost %d" % i, _block("ghost%d_" % i, GHOST_DEFAULTS)) for i in range(lo, lo + 4)]))
    tabs.append(("Animation", [
        ("Flicker", ["flicker_amount", "flicker_speed", "flicker_seed", "ghost_flicker"]),
        ("Pulse", ["pulse_amount", "pulse_speed"]),
        ("Spin", ["spin_speed", "spin_streak", "spin_ghosts", "poly_rotation"])]))
    tabs.append(("Textures", [("Dirt / Dust / Scratches (input: dirt)", list(DIRT_KEYS.values()))]))
    return tabs
