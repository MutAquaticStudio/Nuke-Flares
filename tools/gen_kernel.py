"""Generates Kernels/OF_Flare.blink (repeated glow/ghost blocks are generated, not hand-typed).

    python3 -I tools/gen_kernel.py
"""
import os

N_GLOW = 3
N_GHOST = 8

# (name, label, default) per block ----------------------------------------
GLOW_DEFAULTS = [
    (0.012, 6.0, (1.0, 1.0, 1.0), 0.0),
    (0.05, 0.9, (0.35, 0.6, 1.0), 0.05),
    (0.30, 0.0, (1.0, 0.7, 0.4), 0.0),
]


def f(x):
    return "%.4ff" % x


def f3(c):
    return "float3(%s, %s, %s)" % (f(c[0]), f(c[1]), f(c[2]))


def build():
    params = []     # (decl, define line)
    P = params.append

    P(("float2 lightPos", 'defineParam(lightPos, "Light Position", float2(960.0f, 540.0f));'))
    P(("float master", 'defineParam(master, "Master Intensity", 1.0f);'))
    P(("float flareScale", 'defineParam(flareScale, "Flare Scale", 1.0f);'))
    P(("float ghostSpread", 'defineParam(ghostSpread, "Ghost Spread", 1.0f);'))
    P(("float srcLink", 'defineParam(srcLink, "Follow Source Brightness", 0.0f);'))
    P(("float3 globalTint", 'defineParam(globalTint, "Global Tint", float3(1.0f, 1.0f, 1.0f));'))
    P(("bool flareOnly", 'defineParam(flareOnly, "Flare Only", false);'))
    P(("float animTime", 'defineParam(animTime, "Anim Time (expression: frame)", 0.0f);'))
    P(("float flicker_amount", 'defineParam(flicker_amount, "Flicker Amount", 0.0f);'))
    P(("float flicker_speed", 'defineParam(flicker_speed, "Flicker Speed", 0.15f);'))
    P(("float flicker_seed", 'defineParam(flicker_seed, "Flicker Seed", 0.0f);'))
    P(("float ghost_flicker", 'defineParam(ghost_flicker, "Ghost Flicker", 0.0f);'))
    P(("float pulse_amount", 'defineParam(pulse_amount, "Pulse Amount", 0.0f);'))
    P(("float pulse_speed", 'defineParam(pulse_speed, "Pulse Speed", 0.05f);'))
    P(("float spin_speed", 'defineParam(spin_speed, "Spin Speed (deg per frame)", 0.0f);'))
    P(("bool spin_streak", 'defineParam(spin_streak, "Spin Streak", false);'))
    P(("bool spin_ghosts", 'defineParam(spin_ghosts, "Spin Polygon Ghosts", false);'))
    P(("float poly_rotation", 'defineParam(poly_rotation, "Polygon Rotation", 0.0f);'))
    P(("float dirt_amount", 'defineParam(dirt_amount, "Dirt Amount", 0.0f);'))
    P(("float dirt_spread", 'defineParam(dirt_spread, "Dirt Spread", 2.5f);'))
    P(("float dirt_scale", 'defineParam(dirt_scale, "Dirt Scale", 1.0f);'))
    P(("float2 dirt_offset", 'defineParam(dirt_offset, "Dirt Offset", float2(0.0f, 0.0f));'))
    P(("float3 dirt_tint", 'defineParam(dirt_tint, "Dirt Tint", float3(1.0f, 1.0f, 1.0f));'))

    for i in range(1, N_GLOW + 1):
        r, inten, col, halo = GLOW_DEFAULTS[i - 1]
        P(("float glow%d_radius" % i, 'defineParam(glow%d_radius, "Glow %d Radius", %s);' % (i, i, f(r))))
        P(("float glow%d_intensity" % i, 'defineParam(glow%d_intensity, "Glow %d Intensity", %s);' % (i, i, f(inten))))
        P(("float3 glow%d_color" % i, 'defineParam(glow%d_color, "Glow %d Color", %s);' % (i, i, f3(col))))
        P(("float glow%d_halo" % i, 'defineParam(glow%d_halo, "Glow %d Halo", %s);' % (i, i, f(halo))))

    P(("float streak_length", 'defineParam(streak_length, "Streak Length", 0.55f);'))
    P(("float streak_thickness", 'defineParam(streak_thickness, "Streak Thickness", 0.004f);'))
    P(("float streak_intensity", 'defineParam(streak_intensity, "Streak Intensity", 0.0f);'))
    P(("float3 streak_color", 'defineParam(streak_color, "Streak Color", float3(0.35f, 0.62f, 1.0f));'))
    P(("float streak_angle", 'defineParam(streak_angle, "Streak Angle", 0.0f);'))

    P(("int star_rays", 'defineParam(star_rays, "Star Rays", 8);'))
    P(("float star_length", 'defineParam(star_length, "Star Length", 0.3f);'))
    P(("float star_intensity", 'defineParam(star_intensity, "Star Intensity", 0.0f);'))
    P(("float3 star_color", 'defineParam(star_color, "Star Color", float3(1.0f, 0.9f, 0.7f));'))
    P(("float star_sharp", 'defineParam(star_sharp, "Star Sharpness", 60.0f);'))
    P(("float star_rotation", 'defineParam(star_rotation, "Star Rotation", 0.0f);'))
    P(("float star_seed", 'defineParam(star_seed, "Star Seed", 1.0f);'))

    for i in range(1, N_GHOST + 1):
        P(("float ghost%d_pos" % i, 'defineParam(ghost%d_pos, "Ghost %d Position", %s);' % (i, i, f(0.3 + 0.2 * i))))
        P(("float ghost%d_size" % i, 'defineParam(ghost%d_size, "Ghost %d Size", 0.05f);' % (i, i)))
        P(("float ghost%d_intensity" % i, 'defineParam(ghost%d_intensity, "Ghost %d Intensity", 0.0f);' % (i, i)))
        P(("float3 ghost%d_color" % i, 'defineParam(ghost%d_color, "Ghost %d Color", float3(0.6f, 0.8f, 1.0f));' % (i, i)))
        P(("int ghost%d_shape" % i, 'defineParam(ghost%d_shape, "Ghost %d Shape (0 disc, 1 ring, 2 polygon, 3 custom)", 0);' % (i, i)))
        P(("int ghost%d_sides" % i, 'defineParam(ghost%d_sides, "Ghost %d Polygon Sides", 6);' % (i, i)))
        P(("float ghost%d_softness" % i, 'defineParam(ghost%d_softness, "Ghost %d Softness", 0.25f);' % (i, i)))
        P(("float ghost%d_width" % i, 'defineParam(ghost%d_width, "Ghost %d Ring Width", 0.1f);' % (i, i)))
        P(("float ghost%d_rim" % i, 'defineParam(ghost%d_rim, "Ghost %d Rim", 0.0f);' % (i, i)))

    decl = "\n".join("    %s;" % d for d, _ in params)
    define = "\n".join("    %s" % l for _, l in params)

    body = []
    for i in range(1, N_GLOW + 1):
        body.append("    if (glow%d_intensity > 0.0f) acc += glowLayer(r2, glow%d_radius * sc, glow%d_intensity, glow%d_color, glow%d_halo);" % ((i,) * 5))
    body.append("    if (streak_intensity > 0.0f) acc += streakFn(d, streak_length * sc, streak_thickness * sc, streak_intensity, streak_color, streakAng);")
    body.append("    if (star_intensity > 0.0f) acc += starburstFn(d, star_rays, star_length * sc, star_intensity, star_color, star_sharp, starRot, star_seed);")
    for i in range(1, N_GHOST + 1):
        body.append("""    if (ghost%(i)d_intensity > 0.0f) {
      float2 gc = lightPx + (centre - lightPx) * (ghost%(i)d_pos * ghostSpread);
      float2 gd = float2((float(pos.x) + 0.5f - gc.x) / H, (float(pos.y) + 0.5f - gc.y) / H);
      float gf = flickerAt(t, flicker_seed + %(seed)s, ghost_flicker);
      acc += ghostFn(gd, ghost%(i)d_size * sc, ghost%(i)d_shape, ghost%(i)d_sides, ghost%(i)d_softness, ghost%(i)d_width, ghost%(i)d_rim, polyRot, ghost%(i)d_color, ghost%(i)d_intensity) * gf;
    }""" % {"i": i, "seed": f(1.37 * i)})
    ghosts = "\n".join(body)

    dirt = []
    for i in range(1, N_GLOW + 1):
        dirt.append("      if (glow%d_intensity > 0.0f) dl += glowLayer(r2, glow%d_radius * sc * dirt_spread, glow%d_intensity, glow%d_color, 0.0f);" % ((i,) * 4))
    dirt = "\n".join(dirt)

    return TEMPLATE.replace("@DECL@", decl).replace("@DEFINE@", define).replace("@BODY@", ghosts).replace("@DIRT@", dirt)


TEMPLATE = r"""// OpenFlares - OF_Flare (Blink Script, Nuke 14+)
// GENERATED by tools/gen_kernel.py - edit the generator, not this file.
// Procedural lens flare: glow layers, anamorphic streak, starburst, ghosts/iris.
// Output = source + flare. All sizes are relative to image height.

kernel OF_Flare : ImageComputationKernel<ePixelWise>
{
  Image<eRead, eAccessRandom, eEdgeClamped> src;       // background
  Image<eRead, eAccessRandom, eEdgeClamped> dirt;      // optional: dust / scratch / grain texture
  Image<eRead, eAccessRandom, eEdgeClamped> aperture;  // optional: custom ghost shape (white on black)
  Image<eWrite, eAccessPoint> dst;

  param:
@DECL@

  void define()
  {
@DEFINE@
  }

  float3 mul3(float3 a, float3 b)
  {
    return float3(a.x * b.x, a.y * b.y, a.z * b.z);
  }

  float3 glowLayer(float r2, float radius, float inten, float3 col, float halo)
  {
    float s = max(radius, 0.0001f);
    float q = r2 / (s * s);
    float prof = exp(-q * 0.5f) + halo / pow(1.0f + q, 1.5f);
    return col * (prof * inten);
  }

  float3 streakFn(float2 d, float len, float thick, float inten, float3 col, float angleDeg)
  {
    float a = angleDeg * 3.14159265f / 180.0f;
    float u = d.x * cos(a) + d.y * sin(a);
    float v = -d.x * sin(a) + d.y * cos(a);
    float t = max(thick, 0.00001f);
    float prof = exp(-fabs(u) / max(len, 0.00001f)) * exp(-(v * v) / (2.0f * t * t));
    return col * (prof * inten);
  }

  float3 starburstFn(float2 d, int rays, float len, float inten, float3 col, float sharp, float rotDeg, float seed)
  {
    float r = sqrt(d.x * d.x + d.y * d.y) + 0.000001f;
    float th = atan2(d.y, d.x) + rotDeg * 3.14159265f / 180.0f;
    float n = float(max(rays, 1));
    float ang = pow(fabs(cos(n * th * 0.5f)), max(sharp, 1.0f));
    float h1 = sin(seed * 12.9898f) * 43758.5453f;
    float h2 = sin(seed * 78.233f) * 43758.5453f;
    float f1 = 0.3f + 0.4f * (h1 - floor(h1));
    float f2 = 6.2831853f * (h2 - floor(h2));
    float jit = 0.65f + 0.35f * cos(th * n * 0.5f * f1 + f2);
    float prof = exp(-r / max(len, 0.00001f)) * ang * jit;
    return col * (prof * inten);
  }

  float flickerAt(float t, float seed, float amount)
  {
    float a = t * flicker_speed * 6.2831853f + seed * 17.0f;
    float n = 0.5f * sin(a) + 0.3f * sin(a * 2.31f + 1.7f) + 0.2f * sin(a * 5.17f + 4.1f);   // -1 .. 1
    return 1.0f - amount * 0.5f * (1.0f + n);
  }

  float4 lerp4(float4 a, float4 b, float t)
  {
    return a * (1.0f - t) + b * t;
  }

  // bilinear lookups, uv in 0..1 over the texture's own bounds; black when the input is not connected
  float4 texDirt(float u, float v)
  {
    float w = float(dirt.bounds.x2 - dirt.bounds.x1);
    float h = float(dirt.bounds.y2 - dirt.bounds.y1);
    if (w < 1.0f || h < 1.0f || u < 0.0f || u > 1.0f || v < 0.0f || v > 1.0f) return float4(0.0f, 0.0f, 0.0f, 0.0f);
    float x = u * w - 0.5f;
    float y = v * h - 0.5f;
    int x0 = int(floor(x));
    int y0 = int(floor(y));
    float fx = x - float(x0);
    float fy = y - float(y0);
    x0 += dirt.bounds.x1;
    y0 += dirt.bounds.y1;
    return lerp4(lerp4(dirt(x0, y0), dirt(x0 + 1, y0), fx), lerp4(dirt(x0, y0 + 1), dirt(x0 + 1, y0 + 1), fx), fy);
  }

  float4 texAperture(float u, float v)
  {
    float w = float(aperture.bounds.x2 - aperture.bounds.x1);
    float h = float(aperture.bounds.y2 - aperture.bounds.y1);
    if (w < 1.0f || h < 1.0f || u < 0.0f || u > 1.0f || v < 0.0f || v > 1.0f) return float4(0.0f, 0.0f, 0.0f, 0.0f);
    float x = u * w - 0.5f;
    float y = v * h - 0.5f;
    int x0 = int(floor(x));
    int y0 = int(floor(y));
    float fx = x - float(x0);
    float fy = y - float(y0);
    x0 += aperture.bounds.x1;
    y0 += aperture.bounds.y1;
    return lerp4(lerp4(aperture(x0, y0), aperture(x0 + 1, y0), fx), lerp4(aperture(x0, y0 + 1), aperture(x0 + 1, y0 + 1), fx), fy);
  }

  float3 ghostFn(float2 d, float size, int shape, int sides, float soft, float width, float rim, float polyRot, float3 col, float inten)
  {
    float sz = max(size, 0.00001f);
    if (shape == 3) {
      // custom aperture: the texture's luminance is the shape, rotated by polyRot
      float cr = cos(polyRot);
      float sr = sin(polyRot);
      float dxr = d.x * cr + d.y * sr;
      float dyr = -d.x * sr + d.y * cr;
      float4 tx = texAperture(dxr / (2.0f * sz) + 0.5f, dyr / (2.0f * sz) + 0.5f);
      float lum = tx.x * 0.2126f + tx.y * 0.7152f + tx.z * 0.0722f;
      return col * (lum * inten);
    }
    float r = sqrt(d.x * d.x + d.y * d.y) + 0.000000001f;
    float dist;
    if (shape == 2) {
      float n = float(max(sides, 3));
      float th = atan2(d.y, d.x) - polyRot;
      float seg = 6.2831853f / n;
      float m = th - seg * floor(th / seg);
      float edge = sz * cos(3.14159265f / n) / cos(m - 3.14159265f / n);
      dist = (r - edge) / sz;
    } else {
      dist = (r - sz) / sz;
    }
    float prof;
    if (shape == 1) {
      float w = max(width, 0.001f);
      prof = exp(-(dist / w) * (dist / w));
    } else {
      float sf = max(soft, 0.001f);
      float e = min(max(dist / sf * 6.0f, -40.0f), 40.0f);
      prof = 1.0f / (1.0f + exp(e));
      prof = prof * (0.6f + 0.4f * min(max(1.0f + dist, 0.0f), 1.0f));
      if (rim > 0.0f) {
        float k = dist / 0.08f;
        prof += rim * exp(-k * k);
      }
    }
    return col * (prof * inten);
  }

  void process(int2 pos)
  {
    float H = float(src.bounds.y2 - src.bounds.y1);
    float2 centre = float2(0.5f * float(src.bounds.x1 + src.bounds.x2), 0.5f * float(src.bounds.y1 + src.bounds.y2));
    float2 lightPx = lightPos;

    // ---- animation (animTime is normally the expression "frame")
    float t = animTime;
    float flick = flickerAt(t, flicker_seed, flicker_amount);
    float sc = flareScale * (1.0f + pulse_amount * sin(t * pulse_speed * 6.2831853f));
    float spinDeg = spin_speed * t;
    float starRot = star_rotation + spinDeg;
    float streakAng = streak_angle + (spin_streak ? spinDeg : 0.0f);
    float polyRot = (poly_rotation + (spin_ghosts ? spinDeg : 0.0f)) * 3.14159265f / 180.0f;

    float2 d = float2((float(pos.x) + 0.5f - lightPx.x) / H, (float(pos.y) + 0.5f - lightPx.y) / H);
    float r2 = d.x * d.x + d.y * d.y;

    float3 acc = float3(0.0f, 0.0f, 0.0f);
@BODY@

    // ---- dirt: user texture lit by a widened copy of the glow layers
    if (dirt_amount > 0.0f) {
      float3 dl = float3(0.0f, 0.0f, 0.0f);
@DIRT@
      float sw = float(src.bounds.x2 - src.bounds.x1);
      float u = (float(pos.x) + 0.5f - float(src.bounds.x1)) / max(sw, 1.0f);
      float v = (float(pos.y) + 0.5f - float(src.bounds.y1)) / max(H, 1.0f);
      float ds = max(dirt_scale, 0.0001f);
      u = (u - 0.5f - dirt_offset.x) / ds + 0.5f;
      v = (v - 0.5f - dirt_offset.y) / ds + 0.5f;
      float4 dt = texDirt(u, v);
      acc += mul3(mul3(float3(dt.x, dt.y, dt.z), dirt_tint), dl) * dirt_amount;
    }

    float fac = 1.0f;
    if (srcLink > 0.0f) {
      float4 ls = src(int(lightPx.x), int(lightPx.y));
      float luma = ls.x * 0.2126f + ls.y * 0.7152f + ls.z * 0.0722f;
      fac = 1.0f + srcLink * (min(max(luma, 0.0f), 1.0f) - 1.0f);
    }
    acc = mul3(acc, globalTint) * (master * fac * flick);

    float4 orig = src(pos.x, pos.y);
    float4 result;
    if (flareOnly) {
      result = float4(acc.x, acc.y, acc.z, min(max(max(acc.x, max(acc.y, acc.z)), 0.0f), 1.0f));
    } else {
      result = float4(orig.x + acc.x, orig.y + acc.y, orig.z + acc.z, orig.w);
    }
    dst() = result;
  }
};
"""

if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join(here, "..", "Kernels", "OF_Flare.blink")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(build())
    print("wrote", os.path.normpath(out))
