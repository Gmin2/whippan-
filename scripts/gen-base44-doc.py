#!/usr/bin/env python3
# reproduction of the base44 launch video (analysis/base44), compressed from
# 50s to a ~38s arc: code-confetti intro, dot -> sun mark -> wordmark, prompt
# typewriter, the iridescent generate wash, and the apps condensing out of it
# (bike shop, route planner, rental gantt, phone tracker, terminal, damage
# report, publish), then the confetti collapses back into the sun and the
# "Build it your way" pill lands. tokens from the teardown: cream #eeebe4,
# orange #ef5d24, near-black ui #1c1c1d, lime #93c049, wash = orange/pink/
# lavender/cyan that never settles. same overlay contract as the other gens:
# scene-local at, unique ids per scene, one track per node per prop, x/y
# keys are offsets.
import json
import os

W, H = 1920, 1080
K = 0.5523
INTER_W = 0.5
MONO_W = 0.6

CREAM = "#eeebe4"
ORANGE = "#ef5d24"
INK = "#010202"
DARK = "#1c1c1d"
LIME = "#93c049"
ROUTE = "#d57f1c"

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def circle(cx, cy, r, ccw=False):
    k = r * K
    if not ccw:
        return (f"M{cx - r} {cy}"
                f"C{cx - r} {cy - k} {cx - k} {cy - r} {cx} {cy - r}"
                f"C{cx + k} {cy - r} {cx + r} {cy - k} {cx + r} {cy}"
                f"C{cx + r} {cy + k} {cx + k} {cy + r} {cx} {cy + r}"
                f"C{cx - k} {cy + r} {cx - r} {cy + k} {cx - r} {cy}Z")
    return (f"M{cx - r} {cy}"
            f"C{cx - r} {cy + k} {cx - k} {cy + r} {cx} {cy + r}"
            f"C{cx + k} {cy + r} {cx + r} {cy + k} {cx + r} {cy}"
            f"C{cx + r} {cy - k} {cx + k} {cy - r} {cx} {cy - r}"
            f"C{cx - k} {cy - r} {cx - r} {cy - k} {cx - r} {cy}Z")


def disc(r):
    return circle(0, 0, r)


def slats(r):
    """setting-sun horizon stripes over the disc, drawn in bg color.
    proportions lifted from the base-2 mark (y/r ratios)."""
    import math
    bars = []
    for fy, fh in [(0.08, 0.125), (0.35, 0.115), (0.60, 0.09)]:
        y0, h = fy * r, fh * r
        halfw = math.sqrt(max(r * r - y0 * y0, r * 0.04)) + r * 0.04
        bars.append(f"M{-halfw:.1f} {y0:.1f}L{halfw:.1f} {y0:.1f}"
                    f"L{halfw:.1f} {y0 + h:.1f}L{-halfw:.1f} {y0 + h:.1f}Z")
    return "".join(bars)


def flower(r=10):
    """four overlapping petals, the trailride glyph."""
    return (circle(0, -r, r * 0.92) + circle(r, 0, r * 0.92)
            + circle(0, r, r * 0.92) + circle(-r, 0, r * 0.92))


def text(id, s, x, y, size, color, weight=400, family="inter"):
    return {"id": id, "type": "text", "text": s, "x": round(x, 1),
            "y": round(y, 1), "color": color,
            "font": {"size": size, "weight": weight, "family": family}}


def left_text(id, s, left, y, size, color, weight=400, family="inter"):
    adv = MONO_W if family == "mono" else INTER_W
    return text(id, s, left + len(s) * size * adv / 2, y, size, color,
                weight, family)


def rect(id, x, y, w, h, r, fill, **kw):
    n = {"id": id, "type": "rect", "x": x, "y": y, "w": w, "h": h,
         "radius": r, "fill": fill}
    n.update(kw)
    return n


def grad(angle, *stops):
    n = len(stops) - 1
    return {"angle": angle,
            "stops": [{"at": round(i / n, 3), "color": c}
                      for i, c in enumerate(stops)]}


def keyed(nid, at=None, **props):
    keys = {}
    for name, seq in props.items():
        out = []
        for k in seq:
            kk = {"t": k[0], "v": k[1]}
            if len(k) > 2:
                kk["ease"] = k[2]
            out.append(kk)
        keys[name] = out
    tr = {"target": nid, "keys": keys}
    if at is not None:
        tr["at"] = at
    return tr


def watermark(prefix, color="#c9c4b8"):
    """tiny Base44 lockup top-left, present on the app scenes."""
    return [
        {"id": prefix + "wmk", "type": "path", "x": 52, "y": 40,
         "fill": color, "d": disc(14) + slats(14)},
        left_text(prefix + "wmt", "Base 44", 76, 40, 24, color, weight=600),
    ]


scenes = []
tracks = []

# --------------------------------------------------- s1: code-confetti intro
# "< Build apps >" swaps to "< that scale >" inside a field of tumbling
# slashes and brackets; real js fragments ghost in late (f1-46).
conf1 = [("/", 680, 445, 64, INK), ("/", 822, 415, 64, ROUTE),
         ("/", 1105, 415, 64, INK), ("/", 1265, 445, 64, INK),
         ("/", 675, 605, 64, INK), ("/", 818, 672, 64, INK),
         (">", 1088, 672, 56, INK), ("*", 1266, 608, 60, INK)]
frag1 = [("const express();", 410, 295, 30), ("(req,res)=>{", 1490, 320, 30),
         ("userResponse = await axios", 470, 795, 28),
         ("app.get('/connect/github')", 1420, 800, 28)]
s1_nodes = [
    text("i_lt", "<", 655, 545, 88, INK),
    text("i_gt", ">", 1265, 545, 88, INK),
    text("i_w1", "Build apps", 960, 540, 88, INK, weight=500),
    text("i_w2", "that scale", 960, 540, 88, INK, weight=500),
] + [text(f"i_c{n}", g, x, y, sz, c, family="mono")
     for n, (g, x, y, sz, c) in enumerate(conf1)] + [
    text(f"i_f{n}", s, x, y, sz, "#8a8a86", family="mono")
    for n, (s, x, y, sz) in enumerate(frag1)]
scenes.append({"id": "s1", "bg": CREAM, "dur": 2.4,
               "transition": {"kind": "cut"}, "nodes": s1_nodes})
tracks += [
    keyed("i_w1", opacity=[(0, 0), (0.12, 1), (1.149, 1), (1.15, 0)]),
    keyed("i_w2", opacity=[(1.149, 0), (1.15, 1)]),
    keyed("i_lt", opacity=[(0, 0), (0.1, 1)],
          x=[(0, -14), (0.35, 0, "outCubic")]),
    keyed("i_gt", opacity=[(0, 0), (0.1, 1)],
          x=[(0, 14), (0.35, 0, "outCubic")]),
]
for n in range(len(conf1)):
    at = 0.18 + (n * 5 % 8) * 0.06
    tracks.append(keyed(f"i_c{n}",
                        opacity=[(at, 0), (at + 0.08, 1)],
                        y=[(at, 14), (at + 0.4, 0, "outCubic")]))
for n in range(len(frag1)):
    at = 1.55 + n * 0.09
    tracks.append(keyed(f"i_f{n}", opacity=[(at, 0), (at + 0.12, 0.9)]))

# ------------------------------------------------------- s2: dot -> sun mark
# a gradient dot forms center and cycles cool to warm (blue, pink, orange),
# then grows into the sun disc and gains its horizon slats (f91-105).
s2_nodes = [
    {"id": "d_blue", "type": "path", "x": 960, "y": 540, "fill": "#6b8bf0",
     "d": disc(20)},
    {"id": "d_pink", "type": "path", "x": 960, "y": 540, "fill": "#f08ac2",
     "d": disc(20)},
    {"id": "d_org", "type": "path", "x": 960, "y": 540, "fill": ORANGE,
     "d": disc(20)},
    {"id": "d_slats", "type": "path", "x": 960, "y": 540, "fill": CREAM,
     "d": slats(68)},
]
scenes.append({"id": "s2", "bg": CREAM, "dur": 1.5,
               "transition": {"kind": "fade", "dur": 0.3}, "nodes": s2_nodes})
tracks += [
    keyed("d_blue", opacity=[(0, 0), (0.1, 1), (0.3, 1), (0.42, 0)]),
    keyed("d_pink", opacity=[(0.28, 0), (0.4, 1), (0.52, 1), (0.64, 0)]),
    keyed("d_org", opacity=[(0.5, 0), (0.62, 1)],
          scale=[(0.62, 1), (1.0, 3.4, "outCubic")]),
    keyed("d_slats", opacity=[(0.95, 0), (1.12, 1)]),
]

# -------------------------------------------------------- s3: Base44 wordmark
# the mark slides left and the wordmark sweeps in glyph by glyph, born warm
# and tempering to near-black (f106-144).
s3_nodes = [
    {"id": "m3", "type": "path", "x": 790, "y": 540, "fill": ORANGE,
     "d": disc(46) + slats(46).replace("M", "M")},
    {"id": "m3s", "type": "path", "x": 790, "y": 540, "fill": CREAM,
     "d": slats(46)},
    text("wm3", "Base 44", 1042, 540, 96, INK, weight=700),
]
scenes.append({"id": "s3", "bg": CREAM, "dur": 1.7,
               "transition": {"kind": "fade", "dur": 0.25}, "nodes": s3_nodes})
tracks += [
    keyed("m3", x=[(0, 170), (0.4, 0, "outCubic")],
          scale=[(0, 1.48), (0.4, 1.0, "outCubic")]),
    keyed("m3s", x=[(0, 170), (0.4, 0, "outCubic")],
          scale=[(0, 1.48), (0.4, 1.0, "outCubic")]),
    {"target": "wm3", "at": 0.3, "reveal": {
        "unit": "glyph", "stagger": 0.045, "dur": 0.2, "rise": 0,
        "accent": ORANGE, "color_delay": 0.12, "color_dur": 0.3}},
]

# ------------------------------------------------------- s4: prompt typewriter
# white rounded prompt box, two typed lines, macos cursor resting on the dark
# submit arrow, press at the end (f145-170).
P_L = 475
s4_nodes = watermark("p_") + [
    rect("p_box", 940, 540, 1010, 300, 28, "#ffffff"),
    rect("p_btn", 1385, 452, 76, 76, 18, "#191919",
         states={"pressed": {"scale": 0.92}}),
    {"id": "p_arr", "type": "path", "x": 1385, "y": 452, "fill": "#ffffff",
     "stroke": 3.5, "d": "M-13 0L13 0M3 -10L13 0L3 10"},
    text("p_plus", "+", 492, 632, 44, "#b5b0a6"),
    left_text("p_l1", "I want to build a bike renting app that features",
              P_L, 482, 38, "#1b1b1b"),
    left_text("p_l2", "terrain tracking, a social hub and events",
              P_L, 538, 38, "#1b1b1b"),
    {"id": "p_cur", "type": "cursor", "x": 1600, "y": 800, "w": 26,
     "fill": "#111111"},
]
scenes.append({"id": "s4", "bg": CREAM, "dur": 3.5,
               "transition": {"kind": "fade", "dur": 0.3}, "nodes": s4_nodes})
for nid in ("p_box", "p_btn", "p_arr", "p_plus"):
    tracks.append(keyed(nid, opacity=[(0.05, 0), (0.3, 1)],
                        y=[(0.05, 16), (0.4, 0, "outCubic")]))
tracks += [
    {"target": "p_l1", "at": 0.5, "reveal": {
        "unit": "type", "cadence": 0.026, "dur": 0.05, "caret": "none"}},
    {"target": "p_l2", "at": 1.85, "reveal": {
        "unit": "type", "cadence": 0.026, "dur": 0.05, "caret": "bar",
        "caret_blink": 1.0, "caret_typing": "solid"}},
    keyed("p_l1", opacity=[(0.49, 0), (0.5, 1)]),
    keyed("p_l2", opacity=[(1.84, 0), (1.85, 1)]),
    keyed("p_cur",
          x=[(1.9, 0), (2.7, -207, "outCubic")],
          y=[(1.9, 0), (2.7, -330, "outCubic")]),
    {"target": "p_btn", "at": 3.15, "state": "pressed"},
]

# ----------------------------------------------------- s5: the generate wash
# the whole frame becomes the iridescent orange/pink/lavender/cyan bloom;
# the prompt ghosts out, code fragments float (f171-185).
s5_nodes = [
    rect("w_a", 960, 300, 2200, 900, 0, "#ffb37a", blur=90, rot=-8,
         gradient=grad(15, "#ffb37a", "#ff8ac2", "#ffd9a0")),
    rect("w_b", 700, 800, 2000, 800, 0, "#b8a6ff", blur=110, rot=6,
         gradient=grad(160, "#b8a6ff", "#ff9ecb", "#ffb37a")),
    rect("w_c", 1400, 640, 1600, 700, 0, "#8fd8ff", blur=100, rot=-4,
         gradient=grad(60, "#8fd8ff", "#fff3d8", "#ffa4c8")),
    rect("w_core", 1050, 420, 900, 500, 250, "#fff6e2", blur=120),
    rect("w_ghost", 940, 540, 1010, 300, 28, "#ffffff"),
    text("w_f1", "const orgs", 400, 110, 40, "#8fd8ff", family="mono"),
    text("w_f2", "req.que", 1500, 105, 40, "#ffffff", family="mono"),
    text("w_f3", "=> {", 120, 560, 44, "#ffffff", family="mono"),
    text("w_f4", "express", 540, 285, 40, "#8fd8ff", family="mono"),
]
scenes.append({"id": "s5", "bg": "#f6ddc8", "dur": 1.8,
               "transition": {"kind": "dissolve", "dur": 0.35},
               "nodes": s5_nodes})
for nid, o, dx in [("w_a", 0.95, 70), ("w_b", 0.9, -60), ("w_c", 0.85, 50)]:
    tracks.append(keyed(nid, opacity=[(0, 0), (0.3, o)],
                        x=[(0, 0), (1.8, dx)]))
tracks += [
    keyed("w_core", opacity=[(0, 0), (0.4, 0.9)]),
    keyed("w_ghost", opacity=[(0, 0.4), (0.55, 0)]),
]
for n in range(1, 5):
    at = 0.15 + n * 0.12
    tracks.append(keyed(f"w_f{n}", opacity=[(at, 0), (at + 0.1, 0.9),
                                            (1.5, 0.9), (1.75, 0)]))

# --------------------------------------------------- s6: bike-shop site lands
# "your next adventure awaits" hero + dark category cards condense out of
# the bloom, tint draining to neutral (f186-223).
CARD_LBL = [("Gravel Bikes", "Great for rough trails"),
            ("BMX Bikes", "Great for rough trails"),
            ("Dirt Bikes", "Built for speed"),
            ("Mountain Bikes", "Conquers any terrain"),
            ("Road Bikes", "Maximum performance")]
s6_nodes = watermark("b_") + [
    rect("b_card", 960, 540, 1330, 790, 16, "#21251f"),
    rect("b_hero", 960, 372, 1310, 448, 12, "#5a6b52",
         gradient=grad(180, "#8e9c7e", "#5f7355", "#3f4a38")),
    rect("b_chrome", 410, 190, 190, 54, 12, "#161613"),
    left_text("b_chromet", "trailride", 340, 190, 24, "#ffffff", weight=600),
    rect("b_rent", 1408, 190, 150, 42, 8, "#f0a232"),
    text("b_rentt", "Rent Bikes", 1408, 190, 19, "#3a2a10", family="mono"),
    rect("b_search", 1580, 190, 170, 42, 8, "#2c2c2a"),
    text("b_searcht", "Search Routes", 1580, 190, 19, "#e8e8e4",
         family="mono"),
    left_text("b_h1", "your next adventure", 400, 585, 84, "#ffffff",
              weight=600),
    {"id": "b_fl", "type": "path", "x": 1240, "y": 578, "fill": "#ffffff",
     "d": flower(16)},
    left_text("b_h2", "awaits", 1290, 585, 84, "#ffffff", weight=600),
]
for i, (lbl, sub) in enumerate(CARD_LBL):
    cx = 436 + i * 262
    s6_nodes += [
        rect(f"b_k{i}", cx, 795, 250, 276, 10, "#3d3d3f"),
        left_text(f"b_kl{i}", lbl, cx - 110, 705, 24, "#f2f2f2", weight=600),
        left_text(f"b_ks{i}", sub, cx - 110, 736, 14, "#a9a9a6"),
    ]
scenes.append({"id": "s6", "bg": CREAM, "dur": 3.2,
               "transition": {"kind": "dissolve", "dur": 0.4},
               "nodes": s6_nodes})
tracks += [
    keyed("b_card", opacity=[(0, 0), (0.35, 1)], blur=[(0, 40), (0.6, 0)]),
    keyed("b_hero", opacity=[(0.05, 0), (0.45, 1)],
          blur=[(0.05, 50), (0.7, 0)]),
    keyed("s6", cam_zoom=[(0.4, 1.0), (3.2, 1.035)]),
    {"target": "b_h1", "at": 0.55, "reveal": {
        "unit": "word", "stagger": 0.07, "dur": 0.24, "rise": 0,
        "accent": "#ffb0d0", "color_delay": 0.12, "color_dur": 0.28}},
    keyed("b_fl", opacity=[(0.9, 0), (1.05, 1)]),
    {"target": "b_h2", "at": 0.95, "reveal": {
        "unit": "word", "stagger": 0.07, "dur": 0.24, "rise": 0,
        "accent": "#ffb0d0", "color_delay": 0.12, "color_dur": 0.28}},
]
for nid, at in [("b_chrome", 0.5), ("b_chromet", 0.55), ("b_rent", 0.6),
                ("b_rentt", 0.65), ("b_search", 0.66), ("b_searcht", 0.7),
                ("b_wmk", 0.4), ("b_wmt", 0.4)]:
    tracks.append(keyed(nid, opacity=[(at, 0), (at + 0.15, 1)]))
for i in range(5):
    at = 0.7 + i * 0.09
    tracks.append(keyed(f"b_k{i}", opacity=[(at, 0), (at + 0.2, 1)],
                        y=[(at, 26), (at + 0.4, 0, "outCubic")]))
    tracks.append(keyed(f"b_kl{i}", opacity=[(at + 0.12, 0),
                                             (at + 0.3, 1)]))
    tracks.append(keyed(f"b_ks{i}", opacity=[(at + 0.16, 0),
                                             (at + 0.34, 0.85)]))

# ------------------------------------------------------ s7: route planner
# dark control panel slides in over a topo map with the orange route line
# and blue waypoints (f279-306).
CONTOURS = [-210, -90, 50, 200]
s7_nodes = watermark("r_", "#b9b4a8") + [
    rect("r_map", 1155, 540, 1230, 820, 16, "#e7dfd0"),
] + [
    {"id": f"r_c{i}", "type": "path", "x": 1155, "y": 540,
     "fill": "#d5c9b0", "stroke": 2.0,
     "d": (f"M-560 {y0}C-320 {y0 - 62} -120 {y0 + 44} 140 {y0 - 28}"
           f"S470 {y0 + 26} 560 {y0 - 44}")}
    for i, y0 in enumerate(CONTOURS)
] + [
    {"id": "r_route", "type": "path", "x": 1155, "y": 540, "fill": ROUTE,
     "stroke": 6.0,
     "d": ("M-480 260C-300 180 -260 60 -120 20"
           "S120 -60 220 -140S420 -180 500 -260")},
    {"id": "r_wp1", "type": "path", "x": 675, "y": 800, "fill": "#4a8de8",
     "d": disc(11)},
    {"id": "r_wp2", "type": "path", "x": 1655, "y": 280, "fill": "#4a8de8",
     "d": disc(11)},
    rect("r_panel", 330, 540, 360, 820, 16, DARK),
    left_text("r_title", "Build your Route", 185, 250, 32, "#f2f2f2",
              weight=600),
]
ROWS7 = [("Trail difficulty", "Hard"), ("Distance", "24 km"),
         ("Elevation", "620 m")]
for i, (lbl, val) in enumerate(ROWS7):
    y = 350 + i * 82
    s7_nodes += [
        rect(f"r_row{i}", 330, y, 316, 62, 10, "#27272a"),
        left_text(f"r_rl{i}", lbl, 190, y, 21, "#b9b9b6"),
        left_text(f"r_rv{i}", val, 405, y, 21, "#f0f0ee", weight=500),
    ]
s7_nodes += [
    rect("r_sl_track", 330, 640, 280, 6, 3, "#3a3a3e"),
    rect("r_sl_fill", 278, 640, 176, 6, 3, ORANGE),
    {"id": "r_sl_knob", "type": "path", "x": 366, "y": 640, "fill": ORANGE,
     "d": disc(10)},
    rect("r_go", 330, 880, 300, 62, 13, ORANGE),
    text("r_got", "Build Route", 330, 880, 24, "#ffffff", weight=600),
]
scenes.append({"id": "s7", "bg": CREAM, "dur": 2.4,
               "transition": {"kind": "fade", "dur": 0.35},
               "nodes": s7_nodes})
tracks += [
    keyed("r_map", opacity=[(0, 0), (0.3, 1)]),
    keyed("r_panel", opacity=[(0.1, 0), (0.35, 1)],
          x=[(0.1, -90), (0.55, 0, "outCubic")]),
    keyed("r_title", opacity=[(0.35, 0), (0.55, 1)]),
    keyed("r_route", opacity=[(0.55, 0), (0.95, 1)]),
    keyed("r_wp1", opacity=[(0.85, 0), (1.0, 1)],
          scale=[(0.85, 0.4), (1.1, 1, "outCubic")]),
    keyed("r_wp2", opacity=[(1.0, 0), (1.15, 1)],
          scale=[(1.0, 0.4), (1.25, 1, "outCubic")]),
]
for i in range(4):
    tracks.append(keyed(f"r_c{i}", opacity=[(0.2 + i * 0.07, 0),
                                            (0.45 + i * 0.07, 1)]))
for i in range(3):
    at = 0.45 + i * 0.12
    tracks.append(keyed(f"r_row{i}", opacity=[(at, 0), (at + 0.18, 1)]))
    tracks.append(keyed(f"r_rl{i}", opacity=[(at + 0.08, 0),
                                             (at + 0.26, 1)]))
    tracks.append(keyed(f"r_rv{i}", opacity=[(at + 0.08, 0),
                                             (at + 0.26, 1)]))
for nid, at in [("r_sl_track", 0.85), ("r_sl_fill", 0.9),
                ("r_sl_knob", 0.9), ("r_go", 1.0), ("r_got", 1.05)]:
    tracks.append(keyed(nid, opacity=[(at, 0), (at + 0.18, 1)]))

# ---------------------------------------- s8: wash again, gantt bars pre-viz
# heavily blurred colored bars drift on cream, the calendar about to be
# born; the orange heading fades up (f376-400).
BLOBS = [(510, 340, 560, 105, grad(10, "#f2a0c8", "#f0964a")),
         (1195, 235, 420, 105, grad(15, "#e4f0ff", "#d9b8f0")),
         (915, 535, 780, 110, grad(12, "#f2b8e0", "#f2a038")),
         (1435, 700, 340, 100, grad(8, "#f0a8d8", "#f286b8")),
         (455, 825, 330, 95, grad(12, "#dcd4f4", "#c8ccf2"))]
s8_nodes = watermark("g0_") + [
    rect(f"g0_b{i}", x, y, w, h, h / 2, "#f0a0c0", blur=34, gradient=g)
    for i, (x, y, w, h, g) in enumerate(BLOBS)
] + [left_text("g0_head", "Track and plan bike rentals", 322, 175, 26,
               ORANGE, family="mono")]
scenes.append({"id": "s8", "bg": CREAM, "dur": 1.5,
               "transition": {"kind": "dissolve", "dur": 0.35},
               "nodes": s8_nodes})
for i in range(5):
    at = 0.05 + i * 0.07
    tracks.append(keyed(f"g0_b{i}", opacity=[(at, 0), (at + 0.25, 0.9)],
                        x=[(at, -30), (1.5, 20)]))
tracks.append(keyed("g0_head", opacity=[(0.85, 0), (1.1, 1)]))

# ------------------------------------------------- s9: Bike Rental Status
# the bars sharpen into the booking gantt: dark store nav left, dated
# columns, named bookings, quick actions right (f401-455), with the zoom
# and pan from scene 14 folded into the tail.
NAV = ["Downtown Hub", "Waterfront Station", "Gate Depot", "Bridge Outlet",
       "Sunset Park"]
NAV2 = ["Bike Rentals", "Pages", "Performance", "Team Management",
        "Customize"]
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
BARS = [
    # id, cx, cy, w, fill, name, sub, ink
    ("mj", 855, 595, 420, "#ec8a3c", "Marcus Johnson", "Tue 23 - Thu 25",
     "#ffffff"),
    ("dp", 470, 700, 280, "#cbdb6a", "David Park", "Sat 27 - Sun 28",
     "#3a4018"),
    ("al", 700, 845, 360, "#ecd9ab", "Amanda Lee", "Thu 25 - Sat 27",
     "#5a4a22"),
    ("jw", 1370, 790, 280, "#cbdb6a", "James Wilson", "Tue 23 - Wed 24",
     "#3a4018"),
    ("lt", 1300, 435, 150, "#a9d3f2", "Lisa T.", "Mon 22", "#1e3a52"),
    ("er", 1000, 840, 150, "#a9d3f2", "Emily R.", "Sun 28", "#1e3a52"),
]
s9_nodes = [
    rect("g_nav", 142, 540, 285, 1080, 0, "#171717"),
    {"id": "g_wmk", "type": "path", "x": 60, "y": 56, "fill": "#8a8a86",
     "d": disc(13) + ""},
    left_text("g_wmt", "Base 44", 84, 56, 22, "#d5d5d2", weight=600),
    rect("g_navhl", 142, 194, 253, 46, 10, "#2c2c2e"),
]
for i, lbl in enumerate(NAV):
    s9_nodes.append(left_text(f"g_n{i}", lbl, 46, 148 + i * 46, 21,
                              "#e8e8e4" if i == 1 else "#8f8f8c"))
for i, lbl in enumerate(NAV2):
    s9_nodes.append(left_text(f"g_m{i}", lbl, 46, 430 + i * 46, 21,
                              "#8f8f8c"))
s9_nodes += [
    left_text("g_title", "Bike Rental Status", 322, 112, 60, INK,
              weight=600),
    left_text("g_sub", "Track and plan bike rentals", 322, 175, 26,
              "#c98a4a", family="mono"),
    left_text("g_month", "January 2026", 360, 240, 26, "#e87ab8",
              weight=500),
    left_text("g_range", "Jan 22, 2026 - Jan 28, 2026", 360, 272, 18,
              "#c9895a"),
    rect("g_today", 1445, 248, 108, 42, 21, "#161613"),
    text("g_todayt", "Today", 1445, 248, 20, "#ffffff"),
]
for i in range(7):
    x = 400 + i * 190
    s9_nodes += [
        text(f"g_d{i}", str(22 + i), x, 330, 58, INK, weight=600),
        text(f"g_dl{i}", DAYS[i], x + 58, 342, 16, "#9a958a"),
    ]
    if i:
        s9_nodes.append(rect(f"g_sep{i}", x - 95, 660, 2, 620, 1,
                             "#ddd6c8"))
for bid, cx, cy, w, fill, name, sub, ink in BARS:
    s9_nodes += [
        rect(f"g_{bid}", cx, cy, w, 74, 12, fill),
        left_text(f"g_{bid}n", name, cx - w / 2 + 18, cy - 13, 21, ink,
                  weight=600),
        left_text(f"g_{bid}s", sub, cx - w / 2 + 18, cy + 15, 15, ink),
    ]
s9_nodes += [
    rect("g_sc", 1580, 695, 260, 90, 14, "#f2a0c8", blur=22,
         gradient=grad(10, "#f0a8d8", "#f0964a")),
    rect("g_qa", 1770, 258, 250, 120, 14, "#f6f1e6"),
    left_text("g_qat", "Quick Actions", 1668, 222, 22, INK, weight=600),
    left_text("g_qas", "Manage Rentals", 1668, 275, 19, "#6a675f"),
    rect("g_av", 1770, 520, 250, 240, 14, "#f6f1e6"),
    left_text("g_avt", "Available Bikes", 1668, 432, 21, "#8a8578",
              weight=600),
]
for i, (bike, until) in enumerate([("Summit Rider", "Available until 03.12.26"),
                                   ("PeakSeeker Pro", "Available until 02.15.26"),
                                   ("Velocity Racer", "Available until 04.01.26")]):
    y = 478 + i * 74
    s9_nodes += [
        left_text(f"g_bk{i}", bike, 1668, y, 19, "#8f8b80", weight=500),
        left_text(f"g_bu{i}", until, 1668, y + 26, 14, "#a9a498"),
    ]
scenes.append({"id": "s9", "bg": CREAM, "dur": 3.4,
               "transition": {"kind": "dissolve", "dur": 0.4},
               "nodes": s9_nodes})
tracks += [
    keyed("g_nav", opacity=[(0, 0), (0.25, 1)]),
    keyed("g_navhl", opacity=[(0.2, 0), (0.4, 1)]),
    keyed("g_title", opacity=[(0.1, 0), (0.32, 1)]),
    keyed("g_sub", opacity=[(0, 1)]),
    keyed("g_month", opacity=[(0.25, 0), (0.45, 1)]),
    keyed("g_range", opacity=[(0.3, 0), (0.5, 1)]),
    keyed("g_today", opacity=[(0.35, 0), (0.55, 1)]),
    keyed("g_todayt", opacity=[(0.35, 0), (0.55, 1)]),
    keyed("g_wmk", opacity=[(0, 0), (0.25, 1)]),
    keyed("g_wmt", opacity=[(0, 0), (0.25, 1)]),
    keyed("g_sc", opacity=[(0.6, 0), (0.9, 0.85)]),
    keyed("s9",
          cam_zoom=[(2.3, 1.0), (3.4, 1.12, "inOutCubic")],
          cam_x=[(2.3, 0), (3.4, 70, "inOutCubic")]),
]
for i in range(len(NAV)):
    tracks.append(keyed(f"g_n{i}", opacity=[(0.2 + i * 0.04, 0),
                                            (0.38 + i * 0.04, 1)]))
for i in range(len(NAV2)):
    tracks.append(keyed(f"g_m{i}", opacity=[(0.4 + i * 0.04, 0),
                                            (0.58 + i * 0.04, 1)]))
for i in range(7):
    at = 0.3 + i * 0.05
    tracks.append(keyed(f"g_d{i}", opacity=[(at, 0), (at + 0.16, 1)]))
    tracks.append(keyed(f"g_dl{i}", opacity=[(at + 0.05, 0),
                                             (at + 0.2, 0.9)]))
    if i:
        tracks.append(keyed(f"g_sep{i}", opacity=[(at, 0),
                                                  (at + 0.2, 1)]))
for k, (bid, *_rest) in enumerate(BARS):
    at = 0.35 + k * 0.11
    tracks.append(keyed(f"g_{bid}",
                        blur=[(at, 26), (at + 0.5, 0, "outCubic")],
                        opacity=[(at, 0), (at + 0.2, 1)]))
    tracks.append(keyed(f"g_{bid}n", opacity=[(at + 0.3, 0),
                                              (at + 0.5, 1)]))
    tracks.append(keyed(f"g_{bid}s", opacity=[(at + 0.36, 0),
                                              (at + 0.55, 0.9)]))
for nid, at in [("g_qa", 0.7), ("g_qat", 0.8), ("g_qas", 0.86),
                ("g_av", 0.85), ("g_avt", 0.95)]:
    tracks.append(keyed(nid, opacity=[(at, 0), (at + 0.2, 1)]))
for i in range(3):
    at = 1.0 + i * 0.08
    tracks.append(keyed(f"g_bk{i}", opacity=[(at, 0), (at + 0.18, 1)]))
    tracks.append(keyed(f"g_bu{i}", opacity=[(at + 0.05, 0),
                                             (at + 0.22, 0.85)]))

# --------------------------------------------------- s10: phone ride tracker
# hard cut to the Waterfront tracker: phone on cream, rainbow streak
# sweeping behind, distance ticking 5.7 -> 5.8 (f456-493).
s10_nodes = watermark("t_") + [
    rect("t_streak", 960, 940, 2100, 240, 0, "#ffd0e8", blur=70, rot=-5,
         gradient=grad(0, "#ffb0d8", "#ffd9a0", "#c8f0d8", "#b0d8ff")),
    rect("t_phone", 960, 540, 390, 800, 38, "#93a084",
         gradient=grad(180, "#e8c99a", "#98a888", "#54654a")),
    rect("t_chrome", 872, 178, 140, 44, 12, "#161613"),
    text("t_chromet", "trailride", 872, 178, 20, "#ffffff", weight=600),
    rect("t_menu", 1116, 178, 44, 44, 12, "#161613"),
    text("t_menut", "=", 1116, 177, 26, "#ffffff", weight=700),
    left_text("t_name", "Waterfront", 800, 258, 52, "#ffffff", weight=500),
    rect("t_dchip", 862, 618, 140, 34, 8, "#101010"),
    rect("t_dsq", 812, 618, 14, 14, 3, "#4a9de8"),
    left_text("t_dlbl", "Distance", 830, 618, 18, "#ffffff", family="mono"),
    left_text("t_d57", "5.7", 800, 690, 84, "#ffffff", weight=600),
    left_text("t_d58", "5.8", 800, 690, 84, "#ffffff", weight=600),
    left_text("t_dk", "K", 950, 712, 26, "#e8e8e4"),
    rect("t_tchip", 848, 788, 110, 34, 8, "#101010"),
    rect("t_tsq", 812, 788, 14, 14, 3, "#4a9de8"),
    left_text("t_tlbl", "Time", 830, 788, 18, "#ffffff", family="mono"),
    left_text("t_time", "0:07:24", 800, 856, 62, "#ffffff", weight=500),
    rect("t_stop", 942, 950, 306, 62, 12, "#f0982e"),
    left_text("t_stopt", "Stop Trip", 812, 950, 26, "#ffffff", weight=500),
    {"id": "t_pause", "type": "path", "x": 1112, "y": 950, "fill": "#141414",
     "d": disc(26)},
    {"id": "t_pauseg", "type": "path", "x": 1112, "y": 950,
     "fill": "#ffffff", "stroke": 4.0, "d": "M-5 -8L-5 8M5 -8L5 8"},
]
scenes.append({"id": "s10", "bg": "#f2efe8", "dur": 2.8,
               "transition": {"kind": "cut"}, "nodes": s10_nodes})
tracks += [
    keyed("t_streak", opacity=[(0, 0), (0.4, 0.55)],
          x=[(0, -120), (2.8, 120)]),
    keyed("t_phone", opacity=[(0, 0), (0.25, 1)],
          y=[(0, 44), (0.55, 0, "outCubic")]),
    keyed("t_d57", opacity=[(0, 1), (1.6, 1), (1.7, 0)],
          y=[(1.6, 0), (1.7, -18, "outCubic")]),
    keyed("t_d58", opacity=[(1.6, 0), (1.7, 1)],
          y=[(1.6, 18), (1.7, 0, "outCubic")]),
]
for nid, at in [("t_chrome", 0.3), ("t_chromet", 0.35), ("t_menu", 0.35),
                ("t_menut", 0.4), ("t_name", 0.4), ("t_dchip", 0.5),
                ("t_dsq", 0.52), ("t_dlbl", 0.55), ("t_dk", 0.6),
                ("t_tchip", 0.6), ("t_tsq", 0.62), ("t_tlbl", 0.65),
                ("t_time", 0.7), ("t_stop", 0.75), ("t_stopt", 0.8),
                ("t_pause", 0.78), ("t_pauseg", 0.82)]:
    tracks.append(keyed(nid, opacity=[(at, 0), (at + 0.15, 1)]))

# ------------------------------------------------------- s11: terminal push
# hard cut to the near-black terminal, lime arrow, "git push origin main"
# typed with the origin/main selection boxes (f569-620).
CMD = "git push origin main"
CMD_SIZE = 72
CMD_LEFT = 780
ADV = CMD_SIZE * MONO_W


def cmd_span(a, b):
    cx = CMD_LEFT + (a + b + 1) / 2 * ADV
    w = (b - a + 1) * ADV + 18
    return cx, w


ox, ow = cmd_span(9, 14)
mx, mw = cmd_span(16, 19)
s11_nodes = [
    {"id": "c_wmk", "type": "path", "x": 52, "y": 40, "fill": "#6a6a66",
     "d": disc(14) + slats(14)},
    left_text("c_wmt", "Base 44", 76, 40, 24, "#8f8f8b", weight=600),
    rect("c_ohl", ox, 540, ow, 84, 8, ROUTE),
    rect("c_mhl", mx, 540, mw, 84, 8, "#4a7dd8"),
    {"id": "c_arr", "type": "path", "x": 700, "y": 542, "fill": LIME,
     "stroke": 5.0, "d": "M-22 0L18 0M4 -13L18 0L4 13"},
    left_text("c_cmd", CMD, CMD_LEFT, 540, CMD_SIZE, "#ffffff",
              family="mono"),
]
scenes.append({"id": "s11", "bg": DARK, "dur": 2.6,
               "transition": {"kind": "cut"}, "nodes": s11_nodes})
tracks += [
    keyed("c_arr", opacity=[(0, 0), (0.12, 1)]),
    {"target": "c_cmd", "at": 0.45, "reveal": {
        "unit": "type", "cadence": 0.072, "dur": 0.06, "caret": "block",
        "caret_blink": 1.0, "caret_typing": "solid"}},
    keyed("c_cmd", opacity=[(0.44, 0), (0.45, 1)]),
    keyed("c_ohl", opacity=[(1.62, 0), (1.75, 0.4)]),
    keyed("c_mhl", opacity=[(2.0, 0), (2.12, 0.45)]),
]

# --------------------------------------------------- s12: DamageReport card
# a white card sharpens on a soft iridescent wash, cursor rolls to Apply
# Fixes and presses it (f932-968).
s12_nodes = [
    rect("dm_wa", 500, 250, 900, 600, 300, "#ffca9e", blur=100,
         gradient=grad(20, "#ffca9e", "#ffa4c8")),
    rect("dm_wb", 1500, 780, 900, 600, 300, "#a8d8f0", blur=110,
         gradient=grad(200, "#b8e0f0", "#e8c0f0")),
    rect("dm_wc", 1450, 220, 700, 460, 230, "#ffd9b0", blur=95),
    rect("dm_card", 960, 540, 810, 280, 22, "#fdfbf6"),
    left_text("dm_t", "DamageReport", 615, 465, 40, INK, weight=600),
    rect("dm_pub", 962, 463, 118, 42, 21, "#efece4"),
    text("dm_pubt", "Public", 970, 463, 21, "#5a5a56"),
    {"id": "dm_alert", "type": "path", "x": 628, "y": 522, "fill": "#e0453a",
     "stroke": 2.2, "d": circle(0, 0, 10) + "M0 -4L0 2M0 5L0 6"},
    left_text("dm_alertt", "All users have access", 650, 522, 26,
              "#a09a92"),
    rect("dm_input", 905, 610, 630, 64, 12, "#f4f0e6"),
    left_text("dm_int", "All users have access", 640, 610, 24, "#3a3a36"),
    rect("dm_fix", 1245, 610, 190, 56, 10, "#121212"),
    rect("dm_fixhl", 1245, 610, 190, 56, 10, ORANGE),
    text("dm_fixt", "Apply Fixes", 1245, 610, 22, "#ffffff", weight=500),
    {"id": "dm_cur", "type": "cursor", "x": 1520, "y": 810, "w": 26,
     "fill": "#111111"},
]
scenes.append({"id": "s12", "bg": "#f2ede2", "dur": 2.2,
               "transition": {"kind": "dissolve", "dur": 0.4},
               "nodes": s12_nodes})
tracks += [
    keyed("dm_wa", opacity=[(0, 0), (0.3, 0.75)], x=[(0, 0), (2.2, 40)]),
    keyed("dm_wb", opacity=[(0, 0), (0.3, 0.7)], x=[(0, 0), (2.2, -40)]),
    keyed("dm_wc", opacity=[(0, 0), (0.35, 0.6)]),
    keyed("dm_card", opacity=[(0.05, 0), (0.3, 1)],
          blur=[(0.05, 30), (0.5, 0, "outCubic")]),
    keyed("dm_fixhl", opacity=[(0, 0), (1.55, 0), (1.66, 0.55),
                               (1.85, 0)]),
    keyed("dm_cur", x=[(0.5, 0), (1.15, -252, "outCubic")],
          y=[(0.5, 0), (1.15, -180, "outCubic")]),
]
for nid, at in [("dm_t", 0.3), ("dm_pub", 0.38), ("dm_pubt", 0.42),
                ("dm_alert", 0.45), ("dm_alertt", 0.48), ("dm_input", 0.5),
                ("dm_int", 0.55), ("dm_fix", 0.55), ("dm_fixt", 0.6)]:
    tracks.append(keyed(nid, opacity=[(at, 0), (at + 0.15, 1)]))

# ----------------------------------------------------------- s13: publish
# the dawn sky gradient and the single black Publish button; cursor drifts
# up and presses (f1032-1080).
s13_nodes = [
    rect("pb_sky", 960, 540, 1920, 1080, 0, "#f5e4d2",
         gradient=grad(180, "#f5e4d2", "#eee6db", "#c2d3cd")),
    rect("pb_btn", 960, 540, 260, 100, 18, "#101010",
         states={"pressed": {"scale": 0.95, "fill": "#5a4a6a"}}),
    text("pb_t", "Publish", 960, 540, 34, "#ffffff", weight=500),
    {"id": "pb_cur", "type": "cursor", "x": 1090, "y": 670, "w": 26,
     "fill": "#333333"},
]
scenes.append({"id": "s13", "bg": "#eee6db", "dur": 2.4,
               "transition": {"kind": "cut"}, "nodes": s13_nodes})
tracks += [
    keyed("pb_btn", opacity=[(0.08, 0), (0.3, 1)],
          scale=[(0.08, 0.94), (0.45, 1, "outCubic")]),
    keyed("pb_t", opacity=[(0.12, 0), (0.35, 1)]),
    keyed("pb_cur", x=[(0.5, 0), (1.3, -96, "outCubic")],
          y=[(0.5, 0), (1.3, -76, "outCubic")]),
    {"target": "pb_btn", "at": 1.75, "state": "pressed"},
]

# --------------------------------------- s14: confetti collapses to the sun
# mirror of the open: the fragments scatter, thin, and condense into the
# dot that warms into the sun mark (f1161-1185).
conf14 = [("/", 640, 400, 56, INK), ("/", 1300, 380, 56, INK),
          ("<", 760, 660, 52, INK), (">", 1180, 665, 52, INK),
          ("*", 990, 330, 52, ROUTE), ("/", 880, 730, 56, INK)]
frag14 = [("const express", 380, 260, 28), ("client_id", 1520, 300, 28),
          ("app.get('/connect/github')", 1380, 810, 26),
          ("434b", 480, 800, 28)]
s14_nodes = [
    text(f"e_c{n}", g, x, y, sz, c, family="mono")
    for n, (g, x, y, sz, c) in enumerate(conf14)
] + [
    text(f"e_f{n}", s, x, y, sz, "#8a8a86", family="mono")
    for n, (s, x, y, sz) in enumerate(frag14)
] + [
    {"id": "e_pink", "type": "path", "x": 960, "y": 540, "fill": "#f08ac2",
     "d": disc(20)},
    {"id": "e_org", "type": "path", "x": 960, "y": 540, "fill": ORANGE,
     "d": disc(20)},
    {"id": "e_slats", "type": "path", "x": 960, "y": 540, "fill": CREAM,
     "d": slats(68)},
]
scenes.append({"id": "s14", "bg": CREAM, "dur": 2.2,
               "transition": {"kind": "dissolve", "dur": 0.4},
               "nodes": s14_nodes})
for n, (g, x, y, sz, c) in enumerate(conf14):
    at = 0.05 + (n * 3 % 5) * 0.05
    tracks.append(keyed(
        f"e_c{n}",
        opacity=[(at, 0), (at + 0.1, 1), (0.9, 1), (1.15, 0)],
        x=[(0.55, 0), (1.15, (960 - x) * 0.35, "inCubic")],
        y=[(0.55, 0), (1.15, (540 - y) * 0.35, "inCubic")]))
for n, (s, x, y, sz) in enumerate(frag14):
    tracks.append(keyed(f"e_f{n}",
                        opacity=[(0.05 + n * 0.06, 0),
                                 (0.2 + n * 0.06, 0.85), (0.75, 0.85),
                                 (1.0, 0)]))
tracks += [
    keyed("e_pink", opacity=[(1.0, 0), (1.12, 1), (1.22, 1), (1.32, 0)]),
    keyed("e_org", opacity=[(1.2, 0), (1.32, 1)],
          scale=[(1.32, 1), (1.68, 3.4, "outCubic")]),
    keyed("e_slats", opacity=[(1.62, 0), (1.8, 1)]),
]

# ----------------------------------------------------- s15: wordmark payoff
s15_nodes = [
    {"id": "m15", "type": "path", "x": 790, "y": 540, "fill": ORANGE,
     "d": disc(46)},
    {"id": "m15s", "type": "path", "x": 790, "y": 540, "fill": CREAM,
     "d": slats(46)},
    text("wm15", "Base 44", 1042, 540, 96, INK, weight=700),
]
scenes.append({"id": "s15", "bg": CREAM, "dur": 1.6,
               "transition": {"kind": "fade", "dur": 0.25},
               "nodes": s15_nodes})
tracks += [
    keyed("m15", x=[(0, 170), (0.35, 0, "outCubic")],
          scale=[(0, 1.48), (0.35, 1.0, "outCubic")]),
    keyed("m15s", x=[(0, 170), (0.35, 0, "outCubic")],
          scale=[(0, 1.48), (0.35, 1.0, "outCubic")]),
    {"target": "wm15", "at": 0.25, "reveal": {
        "unit": "glyph", "stagger": 0.04, "dur": 0.18, "rise": 0,
        "accent": ORANGE, "color_delay": 0.1, "color_dur": 0.25}},
]

# ------------------------------------------------ s16: Build it your way
# the tagline types word by word inside a growing outline pill, then the
# border fades and the plain text holds to the end (f1197-1252).
s16_nodes = [
    rect("q_out", 960, 540, 250, 96, 48, "#16130f"),
    rect("q_in", 960, 540, 244, 90, 45, CREAM),
    text("q_t", "Build it your way", 960, 540, 44, INK, weight=500),
]
scenes.append({"id": "s16", "bg": CREAM, "dur": 3.0,
               "transition": {"kind": "fade", "dur": 0.3},
               "nodes": s16_nodes})
tracks += [
    keyed("q_out",
          w=[(0.2, 250), (0.55, 300, "outCubic"), (0.85, 300),
             (1.1, 390, "outCubic"), (1.25, 390),
             (1.55, 470, "outCubic")],
          opacity=[(0, 0), (0.2, 1), (2.2, 1), (2.55, 0)]),
    keyed("q_in",
          w=[(0.2, 244), (0.55, 294, "outCubic"), (0.85, 294),
             (1.1, 384, "outCubic"), (1.25, 384),
             (1.55, 464, "outCubic")],
          opacity=[(0, 0), (0.2, 1), (2.2, 1), (2.55, 0)]),
    {"target": "q_t", "at": 0.35, "reveal": {
        "unit": "word", "stagger": 0.38, "dur": 0.2, "rise": 0,
        "accent": ORANGE, "color_delay": 0.14, "color_dur": 0.3}},
]

stage = {"fps": 25, "size": [W, H], "scenes": scenes}

with open("docs/base44.stage.json", "w") as f:
    json.dump(stage, f, indent=1)
with open("docs/base44.anim.json", "w") as f:
    json.dump({"tracks": tracks}, f, indent=1)
total = sum(s["dur"] for s in scenes)
print("wrote docs/base44.{stage,anim}.json,",
      sum(len(s["nodes"]) for s in scenes), "nodes,",
      len(tracks), "tracks,", round(total, 2), "s")
