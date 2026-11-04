"""Renders every preset through the real OF_Flare.blink source (C++ shim) and compares with the numpy reference."""
import json, os, subprocess, struct, sys
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "reference"))
import of_core, flare

W, H = 1280, 720
LIGHT = (0.72, 0.30)
out_dir = os.path.join(ROOT, "previews", "kernel")
os.makedirs(out_dir, exist_ok=True)

def cpp_value(v):
    if isinstance(v, (list, tuple)) and len(v) == 2:
        return "float2(%.6ff,%.6ff)" % tuple(v)
    if isinstance(v, (list, tuple)):
        return "float3(%.6ff,%.6ff,%.6ff)" % tuple(v)
    if isinstance(v, bool): return "true" if v else "false"
    if isinstance(v, int): return str(v)
    return "%.6ff" % v

def run(preset, tag, frame=0.0):
    params = of_core.preset_to_params(preset)
    names = set(of_core.all_param_names())
    assert set(params) == names, set(params) ^ names
    lines = ["k.animTime = %.3ff;" % frame, "k.lightPos = float2(%.3ff, %.3ff);" % (LIGHT[0] * W, (1 - LIGHT[1]) * H)]
    lines += ["k.%s = %s;" % (n, cpp_value(v)) for n, v in params.items()]
    open(os.path.join(HERE, "assign.inc"), "w").write("\n".join(lines))
    exe = "/tmp/of_h_" + tag
    r = subprocess.run(["g++", "-std=c++17", "-O2", "-o", exe, os.path.join(HERE, "harness.cpp")], capture_output=True, text=True, cwd=HERE)
    if r.returncode: print(r.stderr[:2000]); raise SystemExit("compile failed " + tag)
    subprocess.run([exe, exe + ".bin"], check=True)
    raw = open(exe + ".bin", "rb").read()
    w, h = struct.unpack("ii", raw[:8])
    img = np.frombuffer(raw[8:], np.float32).reshape(h, w, 3)
    return img

worst = 0
tiles = []
for fn in sorted(os.listdir(os.path.join(ROOT, "Presets"))):
    if not fn.endswith(".json"): continue
    p = json.load(open(os.path.join(ROOT, "Presets", fn), encoding="utf-8"))
    frames = [0.0] if "animation" not in p else [0.0, 7.0, 23.0]
    err = 0.0
    for fr in frames:
        k = run(p, fn[:2], fr)
        n = flare.render(p, W, H, LIGHT, frame=fr)
        err = max(err, float(np.abs(k - n).max()))
    if len(frames) > 1:
        a = run(p, fn[:2], 0.0); b = run(p, fn[:2], 23.0)
        assert np.abs(a - b).max() > 0.01, "animation has no visible effect: " + p["name"]
    note = ""
    print("%-26s max|kernel-numpy| = %.5f%s" % (p["name"], err, note))
    worst = max(worst, err)
    im = Image.fromarray(flare.tonemap(k)); im.save(os.path.join(out_dir, fn[:-5] + ".png"))
    tiles.append(im.resize((480, 270)))
sheet = Image.new("RGB", (1440, 270 * ((len(tiles) + 2) // 3)))
for i, t in enumerate(tiles): sheet.paste(t, ((i % 3) * 480, (i // 3) * 270))
sheet.save(os.path.join(out_dir, "_contact_sheet.png"))
print("worst error (all presets): %.6f" % worst)
