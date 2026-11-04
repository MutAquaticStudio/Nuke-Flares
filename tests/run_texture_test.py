"""Checks the `dirt` and `aperture` inputs of OF_Flare using synthetic textures (C++ shim)."""
import os, struct, subprocess, sys
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "reference"))
import of_core, flare

W, H = 1280, 720
preset = {"name": "texture test",
  "glow": [{"radius": 0.012, "intensity": 5.0, "color": [1, 1, 1], "halo": 0.0},
           {"radius": 0.06, "intensity": 1.0, "color": [1.0, 0.8, 0.5], "halo": 0.0}],
  "ghosts": [{"pos": 0.6, "size": 0.09, "intensity": 1.2, "color": [0.6, 0.85, 1.0], "shape": "custom"},
             {"pos": 1.2, "size": 0.12, "intensity": 1.0, "color": [1.0, 0.7, 0.5], "shape": "custom"}],
  "animation": {"spin_speed": 3.0, "spin_ghosts": True},
  "dirt": {"amount": 0.9, "spread": 3.0, "scale": 1.0, "offset": [0.0, 0.0], "tint": [1.0, 0.95, 0.9]}}

FILL = r'''
  k.dirt.alloc(512, 288);                       // dust: speckles + a scratch, different size than the frame
  for (int y = 0; y < 288; y++) for (int x = 0; x < 512; x++) {
    unsigned h = (unsigned)(x * 73856093u) ^ (unsigned)(y * 19349663u);
    float n = ((h >> 8) & 255) / 255.0f;
    float v = n > 0.985f ? 1.0f : 0.0f;
    if (x == 100 + y / 3) v = 0.8f;             // scratch
    k.dirt.buf[y * 512 + x] = float4(v, v, v, 1.0f);
  }
  k.aperture.alloc(64, 64);                     // aperture: a 5-pointed star
  for (int y = 0; y < 64; y++) for (int x = 0; x < 64; x++) {
    float dx = (x + 0.5f) / 32.0f - 1.0f, dy = (y + 0.5f) / 32.0f - 1.0f;
    float r = sqrtf(dx * dx + dy * dy), a = atan2f(dy, dx);
    float edge = 0.45f + 0.5f * (0.5f + 0.5f * cosf(5.0f * a));
    float v = r < edge * 0.9f ? 1.0f : 0.0f;
    k.aperture.buf[y * 64 + x] = float4(v, v, v, 1.0f);
  }
'''
def cv(v):
    if isinstance(v, (list, tuple)) and len(v) == 2: return "float2(%.6ff,%.6ff)" % tuple(v)
    if isinstance(v, (list, tuple)): return "float3(%.6ff,%.6ff,%.6ff)" % tuple(v)
    if isinstance(v, bool): return "true" if v else "false"
    if isinstance(v, int): return str(v)
    return "%.6ff" % v

def render(preset, frame, fill=True):
    p = of_core.preset_to_params(preset)
    lines = ["k.animTime = %.2ff;" % frame, "k.lightPos = float2(%.2ff,%.2ff);" % (0.72 * W, 0.7 * H)]
    lines += ["k.%s = %s;" % (n, cv(v)) for n, v in p.items()]
    if fill: lines.append(FILL)
    open(os.path.join(HERE, "assign.inc"), "w").write("\n".join(lines))
    exe = "/tmp/of_tex"
    r = subprocess.run(["g++", "-std=c++17", "-O2", "-o", exe, os.path.join(HERE, "harness.cpp")], capture_output=True, text=True, cwd=HERE)
    if r.returncode: print(r.stderr[:3000]); raise SystemExit(1)
    subprocess.run([exe, exe + ".bin"], check=True)
    raw = open(exe + ".bin", "rb").read(); w, h = struct.unpack("ii", raw[:8])
    return np.frombuffer(raw[8:], np.float32).reshape(h, w, 3)

a = render(preset, 0)
b = render(preset, 10)
none = render(preset, 0, fill=False)           # textures NOT connected: must not crash, ghosts/dirt vanish
base = flare.render({k: v for k, v in preset.items() if k not in ("ghosts", "dirt")}, W, H, (0.72, 0.30))
print("dirt+aperture connected : mean %.4f" % a.mean())
print("inputs not connected    : mean %.4f, equals glow-only reference: %s"
      % (none.mean(), bool(np.abs(none - base).max() < 1e-3)))
print("custom ghost rotates with spin: frame0 vs frame10 differ by %.3f" % np.abs(a - b).max())
os.makedirs(os.path.join(ROOT, "previews", "kernel"), exist_ok=True)
Image.fromarray(np.hstack([flare.tonemap(a), flare.tonemap(none)])[:, :]).resize((1280, 360)).save(
    os.path.join(ROOT, "previews", "kernel", "_texture_test.png"))
