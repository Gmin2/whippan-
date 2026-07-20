#!/usr/bin/env python3
# reproduction of the blackbox.ai x nvidia launch video (29.0s, 1138x640,
# 30fps). the signature is the halftone dot engine: fixed-grid cell fields
# that precipitate imagery in and out (intro DAY 0, the hexagon logo, the
# outro). stock footage scenes are substituted with dot/gradient stand-ins.
# scene timing tracks the teardown's frame ledger 1:1 where possible.
import json
import math
import os

W, H = 1138, 640
F = 1 / 30
ORANGE = "#f5760f"
PALE = "#f6c9a0"
LIME = "#8bd200"
MINT = "#26f69c"
RED = "#e23a30"
WHITE = "#fcfcfc"

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
scenes, tracks = [], []


def rnd(seed):
    # tiny deterministic prng so cluster layouts are stable across runs
    s = seed & 0xffffffff
    while True:
        s = (s * 1103515245 + 12345) & 0x7fffffff
        yield (s >> 8) / (1 << 23)


def text(id, s, x, y, size, color=WHITE, family="mono", weight=500):
    f = {"size": size, "family": family}
    if family != "mono":
        f["weight"] = weight
    return {"id": id, "type": "text", "text": s, "x": x, "y": y,
            "color": color, "font": f}


def rect(id, x, y, w, h, r, fill, **kw):
    n = {"id": id, "type": "rect", "x": x, "y": y, "w": w, "h": h,
         "radius": r, "fill": fill}
    n.update(kw)
    return n


def path(id, x, y, d, fill, **kw):
    n = {"id": id, "type": "path", "x": x, "y": y, "d": d, "fill": fill}
    n.update(kw)
    return n


def track(nid, at=0.0, **props):
    keys = {}
    for name, seq in props.items():
        out = []
        for k in seq:
            kk = {"t": round(k[0], 4), "v": k[1]}
            if len(k) > 2:
                kk["ease"] = k[2]
            out.append(kk)
        keys[name] = out
    t = {"target": nid, "keys": keys}
    if at:
        t["at"] = at
    tracks.append(t)


def reveal(nid, at, **kw):
    tracks.append({"target": nid, "at": round(at, 3), "reveal": kw})


def stepk(pairs):
    # hard 1-frame steps: [(t, v), ...] -> step keys
    ks = []
    for t, v in pairs:
        if ks:
            ks.append((round(t - 0.001, 4), ks[-1][1]))
        ks.append((round(t, 4), v))
    return ks


def sq(x, y, s):
    return f"M{x - s/2:.1f} {y - s/2:.1f}h{s}v{s}h{-s}Z"


def box_path(w, h):
    return f"M{-w/2} {-h/2}L{w/2} {-h/2}L{w/2} {h/2}L{-w/2} {h/2}Z"


def hex_dist(x, y):
    # pointy-top hexagon "radius" (1.0 = boundary at circumradius 1)
    s3 = math.sqrt(3) / 2
    return max(abs(x), abs(x / 2 + y * s3), abs(x / 2 - y * s3)) / s3


def hex_ring_cells(R, pitch, cell, inner=0.60, seed=7):
    # halftone hexagon ring: grid cells whose hex distance falls in the band.
    # returns list of (d-fragment, angle) so callers can bucket into clusters.
    g = rnd(seed)
    out = []
    n = int(R / pitch) + 2
    for gy in range(-n, n + 1):
        for gx in range(-n, n + 1):
            x, y = gx * pitch, gy * pitch
            d = hex_dist(x / R, y / R)
            if inner < d < 1.0 and next(g) > 0.18:
                s = cell * (0.75 + 0.5 * next(g))
                out.append((sq(x, y, s), math.atan2(y, x)))
    return out


def clusters(cells, k=6):
    ds = [[] for _ in range(k)]
    for frag, a in cells:
        ds[int((a + math.pi) / (2 * math.pi) * k) % k].append(frag)
    return ["".join(c) for c in ds]


def noise_field(count, seed, cx=569, cy=320, spread=430, cell=6):
    g = rnd(seed)
    parts = []
    for _ in range(count):
        a = next(g) * 2 * math.pi
        r = next(g) ** 0.6 * spread
        x, y = cx + r * math.cos(a), cy + r * math.sin(a) * 0.62
        parts.append(sq(x, y, cell * (0.6 + next(g))))
    return "".join(parts)


def hex_mark(R, th=0.34):
    # the blackbox mark: hexagon ring built from 6 edge quads, alternating
    # edges trimmed to leave the broken-corner gaps of the real logo
    vo, vi = [], []
    for k in range(7):
        a = math.radians(90 + 60 * k)
        vo.append((R * math.cos(a), -R * math.sin(a)))
        ri = R * (1 - th)
        vi.append((ri * math.cos(a), -ri * math.sin(a)))
    parts = []
    for i in range(6):
        t0, t1 = (0.0, 0.70) if i % 2 else (0.0, 1.0)
        def lerp(p, q, t):
            return (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)
        a0, a1 = lerp(vo[i], vo[i + 1], t0), lerp(vo[i], vo[i + 1], t1)
        b0, b1 = lerp(vi[i], vi[i + 1], t0), lerp(vi[i], vi[i + 1], t1)
        parts.append(f"M{a0[0]:.1f} {a0[1]:.1f}L{a1[0]:.1f} {a1[1]:.1f}"
                     f"L{b1[0]:.1f} {b1[1]:.1f}L{b0[0]:.1f} {b0[1]:.1f}Z")
    return "".join(parts)


def ellipse_d(rx, ry):
    k = 0.5523
    return (f"M{-rx} 0C{-rx} {-ry*k} {-rx*k} {-ry} 0 {-ry}"
            f"C{rx*k} {-ry} {rx} {-ry*k} {rx} 0"
            f"C{rx} {ry*k} {rx*k} {ry} 0 {ry}"
            f"C{-rx*k} {ry} {-rx} {ry*k} {-rx} 0Z")


def scene(id, bg, dur, nodes, kind="cut", tdur=None):
    tr = {"kind": kind}
    if tdur:
        tr["dur"] = tdur
    scenes.append({"id": id, "bg": bg, "dur": round(dur, 3),
                   "transition": tr, "nodes": nodes})


# 1 ------------------------------------------- dot intro: 0 / Zer0 / DAY 0
# f1-65: halftone field ignites, glyph cycles inside a hexagon dot ring,
# corner ticks snap in. covers teardown scenes 1-2 (city footage omitted).
n1 = [path("bgdots1", 569, 320, noise_field(240, 11), "#3c3c3c")]
track("bgdots1", opacity=stepk([(0.15, 0), (0.2, 0.16), (0.5, 0.09),
                                (0.8, 0.15), (1.3, 0.07), (1.8, 0.11)]))
ring1 = clusters(hex_ring_cells(150, 13, 7.5, seed=3))
for i, d in enumerate(ring1):
    nid = f"ring1_{i}"
    n1.append(path(nid, 569, 320, d, "#b8b8b8"))
    a = 0.18 + i * 0.09
    track(nid, opacity=stepk([(a, 0), (a + 0.05, 0.55), (a + 0.3, 0.35),
                              (a + 0.55, 0.6), (1.4, 0.42), (1.9, 0.55)]),
          scale=[(0.15, 1.14), (1.3, 1.0, "outCubic")])
for gid, s, t0, t1 in [("g1_a", "0", 0.30, 0.63), ("g1_b", "Zer0", 0.63, 0.96),
                       ("g1_c", "DAY 0", 0.96, 2.2)]:
    n1.append(text(gid, s, 569, 322, 34))
    track(gid, opacity=stepk([(0, 0), (t0, 1), (t1, 0)] if t1 < 2.2
                             else [(0, 0), (t0, 1)]))
for i, (tx, ty) in enumerate([(-118, -84), (118, -84), (-118, 84), (118, 84)]):
    nid = f"tick1_{i}"
    n1.append(rect(nid, 569 + tx, 320 + ty, 9, 9, 0, WHITE))
    track(nid, opacity=stepk([(1.45, 0), (1.5, 1)]))
track("s1", cam_zoom=[(0, 1.07), (2.2, 1.0, "outCubic")])
scene("s1", "#000000", 2.2, n1)

# 2 -------------------------------------------------- big Zer0, typed away
# f66-102: "Zer0" typewriter-DELETES to a lone "0". apollo insert omitted.
n2 = [text("zer0", "Zer0", 569, 316, 96),
      text("zero_seed", "0", 569, 316, 96)]
reveal("zer0", 0.05, unit="type", cadence=0.045, dur=0.05, caret="block",
       untype_at=0.55)
track("zero_seed", opacity=stepk([(0, 0), (0.95, 1), (1.15, 0.75), (1.2, 1)]))
scene("s2", "#000000", 1.2, n2)

# 3 ------------------------------------------------ t/s counter HUD ramp
# f103-172: nested viewfinder frames reflow while the counter ramps 1 ->
# 420.2 t/s in accelerating steps. desk footage replaced by the HUD alone.
n3 = [
    rect("v3", 780, 320, 1.6, 640, 0, "#d0d0d0"),
    rect("h3", 569, 447, 1138, 1.6, 0, "#d0d0d0"),
    path("box3", 475, 340, box_path(610, 215), WHITE, stroke=1.6),
    text("unit3", "t/s", 150, 560, 16, "#c8c8c8"),
    path("cross3", 150, 528, "M-8 0L8 0M0 -8L0 8", "#c8c8c8", stroke=1.4),
]
track("v3", opacity=stepk([(0.05, 0), (0.1, 0.85)]),
      x=[(0.1, 0), (2.3, -26, "inOutCubic")])
track("h3", opacity=stepk([(0.1, 0), (0.15, 0.85)]),
      y=[(0.1, 0), (2.3, 14, "inOutCubic")])
track("box3", opacity=stepk([(0.12, 0), (0.17, 1)]),
      x=[(0.2, 0), (1.1, 10, "inOutCubic"), (2.3, -6, "inOutCubic")],
      y=[(0.2, 0), (2.3, -8, "inOutCubic")],
      scale=[(0.2, 0.96), (2.3, 1.02, "inOutCubic")])
track("unit3", opacity=stepk([(0.2, 0), (0.25, 1)]))
track("cross3", opacity=stepk([(0.2, 0), (0.25, 1)]))
VALS = ["1", "3.4", "86.8", "210.1", "233.4", "256.8", "303.5",
        "326.8", "350.2", "373.5", "396.9", "420.2"]
for i, v in enumerate(VALS):
    nid = f"ts_{i}"
    n3.append(text(nid, f"{v} t/s", 470, 348, 50))
    t0 = 0.30 + i * 2 * F
    if i < len(VALS) - 1:
        track(nid, opacity=stepk([(0, 0), (t0, 1), (t0 + 2 * F, 0)]))
    else:
        track(nid, opacity=stepk([(0, 0), (t0, 1)]))
track("s3", cam_zoom=[(0, 1.03), (2.3, 1.0, "outCubic")])
scene("s3", "#000000", 2.3, n3)

# 4 ------------------------------------------- 550 billion parameters
# f172-236: second HUD frame, both stats coexist, frames keep drifting.
n4 = [
    path("box4", 605, 302, box_path(810, 545), WHITE, stroke=1.6),
    rect("v4a", 200, 320, 1.4, 640, 0, "#c9c9c9"),
    rect("h4a", 569, 22, 1138, 1.4, 0, "#c9c9c9"),
    text("ts4", "420.2 t/s", 118, 62, 16),
    path("tsbox4", 118, 62, box_path(158, 36), "#bdbdbd", stroke=1.2),
    text("bil1", "550 billion", 407, 412, 44),
    text("bil2", "parameters", 396, 468, 44),
]
track("box4", x=[(0, 0), (2.2, -12, "inOutCubic")],
      y=[(0, 0), (2.2, 8, "inOutCubic")])
track("v4a", opacity=[(0, 0.7)], x=[(0, 0), (2.2, 18, "inOutCubic")])
track("h4a", opacity=[(0, 0.7)])
reveal("bil1", 0.15, unit="type", cadence=0.04, dur=0.06, caret="block",
       caret_typing="solid")
reveal("bil2", 0.75, unit="type", cadence=0.04, dur=0.06, caret="block")
track("s4", cam_zoom=[(0, 1.0), (2.2, 1.035, "inOutCubic")])
scene("s4", "#000000", 2.2, n4)

# 5 ------------------- benchmark squares -> leaderboard -> orange bar fill
# f236-346: seed squares on an axis, board resolves in (opacity settle
# stands in for the blur rack), only the Blackbox bar fills orange.
BOARD = [("01", "Claude Opus 4.5", 64, 0.45), ("02", "GPT-5.5", 66, 1.0),
         ("03", "Grok 4.1", 175, 1.0), ("04", "Blackbox", 420, 1.0),
         ("05", "gpt-oss-120", 344, 1.0), ("06", "Gemini 3.1 Pro", 136, 1.0),
         ("07", "DeepSeek V4 Pro", 53, 0.45)]
SEG_W, SEG_P, NSEG, BAR_X = 12, 16, 26, 540
n5 = [rect("axis5", 569, 320, 1030, 1.4, 0, "#bfbfbf")]
track("axis5", opacity=stepk([(0.08, 0), (0.13, 0.8), (0.75, 0.8), (0.95, 0)]))
gseed = rnd(21)
for i in range(5):
    nid = f"seed5_{i}"
    n5.append(rect(nid, 420 + i * 74 + next(gseed) * 18, 320, 13, 13, 0, WHITE))
    t0 = 0.15 + i * 0.07
    track(nid, opacity=stepk([(t0, 0), (t0 + 0.04, 1), (0.85, 1), (1.0, 0)]))
for i, (rank, name, val, dim) in enumerate(BOARD):
    y = 152 + i * 55
    lit = round(val / 420 * NSEG)
    dlit = "".join(sq(BAR_X + j * SEG_P, 0, SEG_W) for j in range(lit))
    ddim = "".join(sq(BAR_X + j * SEG_P, 0, SEG_W) for j in range(lit, NSEG))
    row = [rect(f"rbg5_{i}", 569, y, 990, 44, 4, "#0c0c0c"),
           text(f"rk5_{i}", rank, 132, y, 22, "#5c5c5c"),
           text(f"pl5_{i}", "+", 172, y, 22, MINT),
           path(f"bar5_{i}", 0, y, dlit, "#9a9a9a" if i != 3 else "#e8e8e8"),
           path(f"bdim5_{i}", 0, y, ddim, "#333333"),
           text(f"vl5_{i}", str(val), 512, y, 15, "#c9c9c9")]
    nm = text(f"nm5_{i}", name, 196 + len(name) * 6.6, y, 22,
              WHITE if dim == 1.0 else "#8b8b8b")
    row.append(nm)
    n5 += row
    t0 = 0.75 + i * 0.06
    for nd in row:
        track(nd["id"], opacity=[(t0, 0), (t0 + 0.55, dim, "outCubic")],
              y=[(t0, 8), (t0 + 0.55, 0, "outCubic")])
by = 152 + 3 * 55
n5.append(path("hl5", 569, by, box_path(990, 48), WHITE, stroke=1.4))
track("hl5", opacity=[(0.78, 0), (1.1, 1, "outCubic")],
      y=[(0.78, 8), (1.3, 0, "outCubic")])
n5.append(text("vlo5", "420", 512, by, 15, ORANGE))
track("vlo5", opacity=stepk([(0, 0), (2.1, 1)]))
for j in range(NSEG):
    nid = f"ofill5_{j}"
    n5.append(rect(nid, BAR_X + j * SEG_P, by, SEG_W, SEG_W, 1, ORANGE))
    t0 = 2.1 + j * 0.028
    track(nid, opacity=stepk([(t0, 0), (t0 + 0.03, 1)]))
track("s5", cam_zoom=[(0, 1.0), (3.6, 1.02, "inOutCubic")])
scene("s5", "#000000", 3.6, n5)

# 6 -------------------------------------------- orange progress loader
# f346-380: a full-width row of squares lengthens and saturates pale ->
# brand orange between two rails.
n6 = [rect("rail6a", 569, 160, 1138, 1.6, 0, "#e0e0e0"),
      rect("rail6b", 569, 478, 1138, 1.6, 0, "#e0e0e0")]
for i in range(11):
    x = 45 + i * 105
    pale = rect(f"lq6_{i}", x, 320, 86, 86, 6, PALE)
    hot = rect(f"lh6_{i}", x, 320, 86, 86, 6, ORANGE)
    n6 += [pale, hot]
    t0 = 0.06 + i * 0.05
    track(f"lq6_{i}", opacity=stepk([(t0, 0), (t0 + 0.04, 1)]),
          scale=[(t0, 0.9), (t0 + 0.2, 1.0, "outCubic")])
    track(f"lh6_{i}", opacity=[(0.42 + i * 0.05, 0),
                               (0.72 + i * 0.05, 1, "outCubic")])
scene("s6", "#000000", 1.2, n6, kind="fade", tdur=0.22)

# 7 ------------------------------------------------ terminal deploy line
# f381-460: faint grid, blackbox chip, three typed lines. lime is nvidia's,
# orange is LIVE. mono block caret.
CW = 15.6
grid = "".join(f"M{x} 0V640" for x in range(63, W, 127)) + \
       "".join(f"M0 {y}H1138" for y in range(66, H, 127))
n7 = [
    path("grid7", 0, 0, grid, "#242424", stroke=1.0),
    rect("chip7", 315, 197, 164, 44, 5, "#191919"),
    path("chiphex7", 265, 197, hex_mark(13, 0.4), WHITE),
    text("chipt7", "BlackBox", 333, 197, 16, "#8f8f8f"),
    text("t7a", ">", 238, 262, 26),
    text("t7b", "Nvidia", 292, 262, 26, LIME),
    text("t7c", "/nemotron-3-ultra-550b", 511, 262, 26),
    text("t7d", ">Status:", 292, 318, 26),
    text("t7e", "LIVE", 386, 318, 26, ORANGE),
    text("t7f", ">Day:0", 277, 374, 26),
]
track("grid7", opacity=[(0, 0), (0.3, 0.85)])
for nid in ["chip7", "chiphex7", "chipt7"]:
    track(nid, opacity=stepk([(0.1, 0), (0.15, 1)]))
track("t7a", opacity=stepk([(0.15, 0), (0.2, 1)]))
reveal("t7b", 0.25, unit="type", cadence=0.04, dur=0.04, caret="block",
       caret_typing="solid")
reveal("t7c", 0.52, unit="type", cadence=0.035, dur=0.04, caret="block",
       caret_typing="solid")
track("t7c", opacity=stepk([(0, 0), (0.52, 1)]))
reveal("t7d", 1.45, unit="type", cadence=0.045, dur=0.04, caret="block",
       caret_typing="solid")
track("t7d", opacity=stepk([(0, 0), (1.45, 1)]))
reveal("t7e", 1.85, unit="type", cadence=0.05, dur=0.04, caret="block",
       caret_typing="solid")
track("t7e", opacity=stepk([(0, 0), (1.85, 1)]))
reveal("t7f", 2.1, unit="type", cadence=0.045, dur=0.04, caret="block",
       caret_blink=1.0)
track("t7f", opacity=stepk([(0, 0), (2.1, 1)]))
scene("s7", "#000000", 2.6, n7)

# 8 --------------------------------------- ocean claim + pricing caption
# f461-571: grey gradient stand-in for the ocean shot, center measurement
# line, two captions trade places, vertical glitch bars exit.
n8 = [
    rect("sky8", 569, 320, 1140, 642, 0, "#a3a3a3",
         gradient={"angle": 90, "stops": [{"at": 0, "color": "#9b9b9b"},
                                          {"at": 1, "color": "#ababab"}]}),
    rect("sea8", 569, 588, 1140, 130, 0, "#7f7f7f",
         gradient={"angle": 90, "stops": [{"at": 0, "color": "#8e8e8e"},
                                          {"at": 1, "color": "#6e6e6e"}]}),
    rect("wave8a", 400, 545, 300, 2, 0, "#c4c4c4"),
    rect("wave8b", 760, 570, 380, 2, 0, "#bdbdbd"),
    rect("vln8", 552, 320, 2, 640, 0, WHITE),
    rect("cap8a", 552, 82, 70, 2, 0, WHITE),
    rect("cap8b", 552, 235, 70, 2, 0, WHITE),
    rect("rule8", 552, 120, 452, 2, 0, WHITE),
    text("fast8", "Faster than Smaller Models", 553, 175, 26, "#f2f2f2"),
    text("price8", "$0.37 In | $1.08 Out", 553, 300, 26, "#f8f8f8"),
]
track("sea8", y=[(0, 0), (3.7, -26)])
track("wave8a", opacity=[(0, 0.35)], y=[(0, 0), (3.7, -22)])
track("wave8b", opacity=[(0, 0.28)], y=[(0, 0), (3.7, -24)])
for nid in ["vln8", "cap8a", "cap8b", "rule8"]:
    track(nid, opacity=stepk([(0.06, 0), (0.1, 0.9)]))
reveal("fast8", 0.2, unit="type", cadence=0.028, dur=0.05, caret="block")
track("fast8", opacity=[(0.2, 1), (1.9, 1), (2.2, 0.3, "outCubic")])
track("price8", opacity=[(0, 0), (1.9, 0), (2.2, 1, "outCubic")],
      y=[(1.9, 8), (2.3, 0, "outCubic")])
for i, gx in enumerate([28, 96, 1046, 1112]):
    nid = f"gl8_{i}"
    n8.append(rect(nid, gx, 320, 16, 640, 0, WHITE))
    track(nid, opacity=stepk([(3.48, 0), (3.5, 0.9), (3.56, 0),
                              (3.6, 0.85), (3.66, 0)]))
n8.append(path("ret8", 552, 320, box_path(240, 420), WHITE, stroke=1.6))
track("ret8", opacity=stepk([(3.44, 0), (3.48, 1), (3.68, 1)]))
track("s8", cam_zoom=[(0, 1.0), (3.7, 1.03)])
scene("s8", "#9c9c9c", 3.7, n8)

# 9 ---------------------------------------------------- number matrix
# f572-598: a boxed grid of digits churns and flickers, scanline sweeps,
# ends on a white flash into the e2ee card.
g9 = rnd(41)
n9 = [path("mbox9", 600, 330, box_path(1010, 480), WHITE, stroke=1.6)]
track("mbox9", opacity=stepk([(0.03, 0), (0.06, 1)]))
for i in range(8):
    chars = []
    for c in range(17):
        v = next(g9)
        chars.append(str(int(v * 9)) if v > 0.33 else " ")
    s = " ".join(chars)
    nid = f"mrow9_{i}"
    n9.append(text(nid, s, 600, 140 + i * 54, 26))
    reveal(nid, 0.05 + (i % 4) * 0.04, unit="scramble", cadence=0.02, churn=6)
    ph = 0.1 + (i * 0.037) % 0.12
    track(nid, opacity=stepk([(0.05, 0), (0.08, 1), (ph + 0.2, 0.5),
                              (ph + 0.27, 1), (ph + 0.4, 0.6),
                              (ph + 0.47, 1), (ph + 0.6, 0.55),
                              (ph + 0.67, 1)]))
n9.append(rect("scan9", 600, 200, 1010, 56, 0, WHITE))
track("scan9", opacity=[(0.15, 0), (0.25, 0.14), (0.9, 0.1), (1.0, 0)],
      y=[(0.15, -80), (1.0, 260)])
n9.append(rect("flash9", 569, 320, 1138, 640, 0, WHITE))
track("flash9", opacity=stepk([(0.82, 0), (0.86, 0.95), (0.9, 0)]))
scene("s9", "#000000", 0.9, n9)

# 10 ----------------------------------------- END-TO-END ENCRYPTED card
# f599-696: the one grotesk moment. black card types the headline, flips
# white; red e2ee body; scrambling "Privacy Formation" ascii panel; a
# halftone stripe portrait sits behind at low opacity.
g10 = rnd(77)
stripes = []
for ry in range(0, H, 16):
    x0 = 300 + next(g10) * 500
    wl = 80 + next(g10) * 420
    stripes.append(f"M{x0:.0f} {ry}h{wl:.0f}v9h{-wl:.0f}Z")
n10 = [path("port10", 0, 0, "".join(stripes), "#8a8a8a")]
track("port10", opacity=stepk([(0.02, 0), (0.06, 0.22), (1.2, 0.16),
                               (2.0, 0.22), (3.1, 0.16), (3.2, 0)]))
n10 += [
    rect("cardb10", 400, 432, 580, 280, 0, "#0a0a0a"),
    rect("cardw10", 400, 432, 580, 280, 0, WHITE),
    text("hlw1", "END-TO-END", 297, 345, 54, WHITE, family="inter", weight=800),
    text("hlw2", "ENCRYPTED", 283, 425, 54, WHITE, family="inter", weight=800),
    text("hlb1", "END-TO-END", 297, 345, 54, "#0a0a0a", family="inter",
         weight=800),
    text("hlb2", "ENCRYPTED", 283, 425, 54, "#0a0a0a", family="inter",
         weight=800),
    text("sub10a", "End-to-end encryption (E2EE) is a security method where "
         "only the sender", 372, 512, 13, RED, family="inter", weight=500),
    text("sub10b", "and the intended recipient can read the contents of a "
         "message or data.", 369, 532, 13, RED, family="inter", weight=500),
    rect("abox10", 635, 200, 430, 186, 0, "#040404"),
    path("abord10", 635, 200, box_path(430, 186), "#4a4a4a", stroke=1.2),
    rect("plbl10", 933, 86, 158, 27, 0, "#ececec"),
    text("plblt10", "Privacy Formation", 933, 86, 13, "#111111",
         family="inter", weight=500),
]
FLIP = 0.85
track("cardb10", opacity=stepk([(0.04, 0), (0.08, 1), (FLIP, 0)]))
track("cardw10", opacity=stepk([(0, 0), (FLIP, 1), (3.15, 1), (3.25, 0)]))
reveal("hlw1", 0.12, unit="type", cadence=0.038, dur=0.04, caret="block",
       caret_typing="solid")
track("hlw1", opacity=stepk([(0.1, 0), (0.12, 1), (FLIP, 0)]))
reveal("hlw2", 0.5, unit="type", cadence=0.038, dur=0.04, caret="block",
       caret_typing="solid")
track("hlw2", opacity=stepk([(0, 0), (0.5, 1), (FLIP, 0)]))
track("hlb1", opacity=stepk([(0, 0), (FLIP, 1), (3.15, 1), (3.2, 0)]))
track("hlb2", opacity=stepk([(0, 0), (FLIP, 1), (3.05, 1), (3.1, 0)]))
for nid, a in [("sub10a", 1.0), ("sub10b", 1.05)]:
    track(nid, opacity=[(a, 0), (a + 0.25, 1), (3.1, 1), (3.2, 0)])
for nid in ["abox10", "abord10", "plbl10", "plblt10"]:
    track(nid, opacity=stepk([(0.15, 0), (0.2, 1), (3.2, 1), (3.25, 0)]))
ASCII = [":jYYj!~'  . .", "!JJ5i>>:'  .", ">tcY+>>!'", "=SXY=jc=~"]
for i, s in enumerate(ASCII):
    nid = f"asc10_{i}"
    n10.append(text(nid, s, 460 + len(s) * 9.6, 145 + i * 44, 30))
    reveal(nid, 0.25 + i * 0.12, unit="scramble", cadence=0.06, churn=5)
    track(nid, opacity=stepk([(0.22, 0), (0.25 + i * 0.12, 1),
                              (1.6 + i * 0.1, 0.7), (1.7 + i * 0.1, 1),
                              (2.4, 0.75), (2.5, 1), (3.2, 1), (3.25, 0)]))
scene("s10", "#000000", 3.3, n10)

# 11 ---------------------------------------- hexagon logo precipitates
# f697-739: the dot engine reforms as the hexagon ring, then the crisp
# white mark resolves out of it.
n11 = [path("bgdots11", 569, 320, noise_field(160, 55), "#3a3a3a")]
track("bgdots11", opacity=stepk([(0.05, 0), (0.1, 0.14), (0.5, 0.08),
                                 (0.9, 0.12), (1.2, 0.05)]))
ring11 = clusters(hex_ring_cells(120, 12, 7, seed=9))
for i, d in enumerate(ring11):
    nid = f"ring11_{i}"
    n11.append(path(nid, 569, 320, d, "#a8d8a8"))
    a = 0.08 + i * 0.06
    track(nid, opacity=stepk([(a, 0), (a + 0.05, 0.5), (a + 0.25, 0.35),
                              (a + 0.4, 0.55), (0.85, 0.45), (1.25, 0)]),
          scale=[(0.05, 1.18), (1.0, 1.0, "outCubic")])
n11.append(path("mark11", 569, 320, hex_mark(46), WHITE))
track("mark11", opacity=[(0.8, 0), (1.15, 1, "outCubic")],
      scale=[(0.8, 1.06), (1.2, 1.0, "outCubic")])
scene("s11", "#000000", 1.4, n11)

# 12 ---------------------------------------------- co-brand lockup
# f740-789: nvidia eye + X slide in beside the hexagon; caption scrambles
# to BLACKBOX.AI x NVIDIA.
n12 = [
    path("mark12", 475, 320, hex_mark(40), WHITE),
    text("x12", "X", 563, 322, 30),
    rect("nv12", 650, 325, 66, 66, 3, LIME),
    path("nveye12", 650, 322, ellipse_d(22, 13), WHITE, stroke=3.0),
    rect("nvbar12", 622, 322, 12, 4, 0, WHITE),
    text("cap12", "BLACKBOX.AI x NVIDIA", 569, 566, 15),
]
track("mark12", x=[(0, 0), (0.35, 0, "outCubic")])
for nid in ["x12", "nv12", "nveye12", "nvbar12"]:
    track(nid, opacity=[(0.08, 0), (0.35, 1, "outCubic")],
          x=[(0.08, 34), (0.45, 0, "outCubic")])
reveal("cap12", 0.55, unit="scramble", cadence=0.045, churn=4)
track("cap12", opacity=stepk([(0.5, 0), (0.55, 1)]))
scene("s12", "#000000", 2.0, n12)

# 13 ------------------------------------------- NEMOTORN 3 ULTRA title
# f801-835: the payoff title, lime + white, typed. (the video's own
# transposed spelling is kept.) lockup-disassembly beat is compressed to
# a reticle flash at entry.
n13 = [
    path("circ13", 569, 320, ellipse_d(120, 120), WHITE, stroke=1.4),
    text("ttl13a", "NEMOTORN 3 ULTRA", 578, 307, 34, LIME),
    text("ttl13b", "Now on BLACKBOX.AI", 578, 355, 30),
]
track("circ13", opacity=stepk([(0.0, 0.9), (0.14, 0.9), (0.18, 0)]),
      scale=[(0, 0.4), (0.16, 1.3, "outCubic")])
reveal("ttl13a", 0.1, unit="type", cadence=0.022, dur=0.04, caret="block",
       caret_typing="solid")
reveal("ttl13b", 0.42, unit="type", cadence=0.022, dur=0.04, caret="block")
track("ttl13b", opacity=stepk([(0, 0), (0.42, 1)]))
scene("s13", "#000000", 1.2, n13)

# 14 -------------------------------------------------- outro disperse
# f836-870: the dot hexagon reforms and disperses back to true black.
n14 = []
ring14 = clusters(hex_ring_cells(130, 12, 7, seed=13))
for i, d in enumerate(ring14):
    nid = f"ring14_{i}"
    n14.append(path(nid, 569, 320, d, "#9a9a9a"))
    a = 0.05 + i * 0.05
    off = 0.5 + i * 0.09
    track(nid, opacity=stepk([(a, 0), (a + 0.05, 0.5), (off, 0.4),
                              (off + 0.25, 0)]),
          scale=[(0.05, 1.0), (1.2, 1.14, "inCubic")])
n14.append(path("bgdots14", 569, 320, noise_field(120, 99), "#333333"))
track("bgdots14", opacity=stepk([(0.1, 0), (0.15, 0.12), (0.7, 0.07),
                                 (1.0, 0)]))
scene("s14", "#000000", 1.2, n14)

stage = {"fps": 30, "size": [W, H], "scenes": scenes,
         "audio": {"src": "/assets/audio/pad.m4a", "gain": 0.55,
                   "fade_out": 0.8}}
with open("docs/blackbox.stage.json", "w") as f:
    json.dump(stage, f, indent=1)
with open("docs/blackbox.anim.json", "w") as f:
    json.dump({"tracks": tracks}, f, indent=1)
total = sum(s["dur"] for s in scenes)
print("wrote docs/blackbox.{stage,anim}.json,",
      sum(len(s["nodes"]) for s in scenes), "nodes,", len(tracks),
      f"tracks, {total:.2f}s")
