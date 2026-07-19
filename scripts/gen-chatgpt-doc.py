#!/usr/bin/env python3
# reproduction of animations/chatgpt.mp4 scenes 1-5 (0-7.6s), the typography
# half of the video. every number here is measured from the real frames
# (analysis/chatgpt/) -- word bboxes, pill geometry, card centers, timings
# mapped through pts.txt.
#
# overlay contract (learned the hard way): `at` is SCENE-LOCAL time; a track
# applies to every scene holding its target id, so ids are unique per scene;
# a later track keying the same prop replaces the earlier one, so each node
# gets ONE track with its whole timeline. x/y keys are offsets from the node
# base; w/h/rot/scale/opacity are absolute.
import json
import math
import os

W, H = 2994, 1618
INK = "#161616"

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def rot_about(cx, cy, x, y, deg, k=1.0):
    a = math.radians(deg)
    rx, ry = x - cx, y - cy
    return (
        round(cx + (rx * math.cos(a) - ry * math.sin(a)) * k, 1),
        round(cy + (rx * math.sin(a) + ry * math.cos(a)) * k, 1),
    )


def gauge_ticks():
    """the 24/100 card's tick ring: 28 radial ticks sweeping 250 degrees,
    one filled path, coordinates relative to the gauge center."""
    parts = []
    n, r0, r1, tw = 28, 68, 92, 3.4
    for i in range(n):
        a = math.radians(-215 + 250 * i / (n - 1))
        ca, sa = math.cos(a), math.sin(a)
        px, py = -sa * tw, ca * tw
        pts = [(r0 * ca + px, r0 * sa + py), (r1 * ca + px, r1 * sa + py),
               (r1 * ca - px, r1 * sa - py), (r0 * ca - px, r0 * sa - py)]
        parts.append("M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in pts) + "Z")
    return "".join(parts)


def blossom():
    """six-petal knot mark on the personality tile, petals 60 degrees apart."""
    petal = [(0, -40), (9, -40), (12, -32), (12, -14), (12, -6), (6, -2),
             (0, -2), (-6, -2), (-12, -6), (-12, -14), (-12, -32), (-9, -40)]
    parts = []
    for k in range(6):
        a = math.radians(60 * k)
        ca, sa = math.cos(a), math.sin(a)
        pts = [(x * ca - y * sa, x * sa + y * ca) for x, y in petal]
        d = f"M{pts[0][0]:.1f} {pts[0][1]:.1f}"
        for i in range(1, 12, 3):
            c1, c2, p = pts[i], pts[i + 1], pts[(i + 2) % 12]
            d += (f"C{c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} "
                  f"{p[0]:.1f} {p[1]:.1f}")
        parts.append(d + "Z")
    return "".join(parts)


def text(id, s, x, y, size, color=INK, weight=400, rot=None):
    n = {"id": id, "type": "text", "text": s, "x": x, "y": y,
         "color": color, "font": {"size": size, "weight": weight}}
    if rot:
        n["rot"] = rot
    return n


def rect(id, x, y, w, h, r, fill, **kw):
    n = {"id": id, "type": "rect", "x": x, "y": y, "w": w, "h": h,
         "radius": r, "fill": fill}
    n.update(kw)
    return n


def track(nid, base_x, base_y, x=None, y=None, **props):
    """one combined track. x/y given as [(t, absolute)] pairs, converted to
    engine offsets; other props passed as [(t, v)] or [(t, v, ease)]."""
    keys = {}

    def conv(seq, base):
        out = []
        for k in seq:
            t, v = k[0], k[1]
            e = k[2] if len(k) > 2 else None
            kk = {"t": t, "v": round(v - base, 1)}
            if e:
                kk["ease"] = e
            out.append(kk)
        return out

    if x:
        keys["x"] = conv(x, base_x)
    if y:
        keys["y"] = conv(y, base_y)
    for name, seq in props.items():
        out = []
        for k in seq:
            kk = {"t": k[0], "v": k[1]}
            if len(k) > 2:
                kk["ease"] = k[2]
            out.append(kk)
        keys[name] = out
    return {"target": nid, "keys": keys}


tracks = []

# ---------------------------------------------------------------- scene 1
# f1: three words on broken baselines, counter-rotated, blue swoosh under
# "anything". swoosh fades f77-80, iron-out f84-94, pre-clear widen f94-99.
sc1_nodes = [
    text("imagine", "Imagine", 1086, 752, 100, rot=-1.0),
    text("building", "building", 1481, 812, 100, rot=1.0),
    text("anything", "anything", 1883, 790, 100, rot=-1.0),
    {"id": "swoosh", "type": "path", "x": 1868, "y": 878, "fill": "#417fd9",
     "d": "M0 0C130 62 290 72 420 40C300 58 140 46 0 0Z"},
]
tracks += [
    {"target": "swoosh", "at": 2.56,
     "keys": {"opacity": [{"t": 0, "v": 1}, {"t": 0.17, "v": 0}]}},
    track("imagine", 1086, 752,
          x=[(2.83, 1086), (3.17, 1119, "outCubic"), (3.25, 1119),
             (3.375, 1040, "outCubic")],
          y=[(2.83, 752), (3.17, 782, "outCubic")],
          rot=[(2.83, -1.0), (3.17, 0, "outCubic")]),
    track("building", 1481, 812,
          x=[(2.83, 1481), (3.17, 1483, "outCubic")],
          y=[(2.83, 812), (3.17, 782, "outCubic")],
          rot=[(2.83, 1.0), (3.17, 0, "outCubic")]),
    track("anything", 1883, 790,
          x=[(2.83, 1883), (3.17, 1853, "outCubic"), (3.25, 1853),
             (3.375, 1932, "outCubic")],
          y=[(2.83, 790), (3.17, 782, "outCubic")],
          rot=[(2.83, -1.0), (3.17, 0, "outCubic")]),
]

# ---------------------------------------------------------------- scene 2
# polarity cut: same sentence white on black, "building" replaced by the
# live pill. pill grows leftward while typing (button pinned right), whole
# lockup winds up 8 degrees cw into the card crash (f138-146).
PILL_R = 1898
LCX, LCY = 1490, 785


def windup_xy(x, y):
    ex, ey = rot_about(LCX, LCY, x, y, 8, 0.92)
    return ex - 44, ey - 58


sc2_nodes = [
    text("imagine2", "Imagine", 815, 785, 100, color="#ffffff"),
    text("anything2", "anything", 2147, 785, 100, color="#ffffff"),
    rect("pill", PILL_R - 415, 785, 830, 158, 79, "#2d2d2d"),
    rect("btn", 1820, 785, 102, 102, 14, "#fafafa"),
    {"id": "btnup", "type": "path", "x": 1820, "y": 785, "fill": "#111111",
     "d": "M0 -26L20 0L8 0L8 26L-8 26L-8 0L-20 0Z"},
    text("typed", "with just a simple prompt...", 1345, 787, 42,
         color="#9a9a9a"),
]
wux, wuy = windup_xy(815, 785)
tracks.append(track("imagine2", 815, 785,
                    x=[(0.07, 963), (0.89, 815, "outCubic"), (1.28, 815),
                       (1.56, wux, "inCubic")],
                    y=[(1.28, 785), (1.56, wuy, "inCubic")],
                    rot=[(1.28, 0), (1.56, 8, "inCubic")],
                    scale=[(1.28, 1), (1.56, 0.92, "inCubic")]))
wux, wuy = windup_xy(2147, 785)
tracks.append(track("anything2", 2147, 785,
                    x=[(0.07, 2004), (0.89, 2147, "outCubic"), (1.28, 2147),
                       (1.56, wux, "inCubic")],
                    y=[(1.28, 785), (1.56, wuy, "inCubic")],
                    rot=[(1.28, 0), (1.56, 8, "inCubic")],
                    scale=[(1.28, 1), (1.56, 0.92, "inCubic")]))
wux, wuy = windup_xy(1483, 785)
tracks.append(track("pill", PILL_R - 415, 785,
                    x=[(0.07, PILL_R - 170), (0.89, PILL_R - 415, "outCubic"),
                       (1.28, PILL_R - 415), (1.56, wux, "inCubic")],
                    y=[(1.28, 785), (1.56, wuy, "inCubic")],
                    w=[(0.07, 340), (0.89, 830, "outCubic")],
                    rot=[(1.28, 0), (1.56, 8, "inCubic")],
                    scale=[(1.28, 1), (1.56, 0.92, "inCubic")]))
for nid, bx, by in [("btn", 1820, 785), ("btnup", 1820, 785),
                    ("typed", 1345, 787)]:
    wux, wuy = windup_xy(bx, by)
    tracks.append(track(nid, bx, by,
                        x=[(1.28, bx), (1.56, wux, "inCubic")],
                        y=[(1.28, by), (1.56, wuy, "inCubic")],
                        rot=[(1.28, 0), (1.56, 8, "inCubic")],
                        scale=[(1.28, 1), (1.56, 0.92, "inCubic")]))
tracks.append({"target": "typed", "at": 0.07, "reveal": {
    "unit": "type", "cadence": 0.014, "cadence_end": 0.046, "dur": 0.13,
    "caret": "bar", "caret_blink": 0.4}})

# ---------------------------------------------------------------- scene 3
# four spec cards crash in from the corners with echo trails (f147-152,
# settled f158), "Just" pops at -55deg, cards shrink to their centers on
# exit (f174-177) while "Just" starts crossfading toward "and".
# f160 positions are mid-settle; the crash decelerates through them and
# rests at the f168 layout, fully inside the frame
CARDS = {"lang": (1900, 234, 150, -900), "gauge": (974, 641, -1300, 0),
         "ctx": (1110, 1300, -500, 1000), "pers": (2122, 941, 1200, 300)}
REST = {"lang": (2011, 387), "gauge": (1085, 512),
        "ctx": (1025, 1155), "pers": (2010, 1088)}
STREAK = {"samples": 5, "window": 0.06, "gain": 0.5}
sc3_members = {
    "lang": [
        rect("lang", 1900, 234, 400, 480, 56, "#92373c",
             gradient={"angle": 90, "stops": [
                 {"at": 0, "color": "#92373c"}, {"at": 1, "color": "#e4b38a"}]},
             streak=STREAK),
        text("lang_t", "Language Output", 1900, 128, 30, color="#f5e5da"),
        text("lang_big", "10K/Day", 1900, 300, 58, color="#ffffff", weight=600),
        rect("lang_slider", 1900, 363, 270, 7, 4, "#f7ece2"),
        rect("lang_knob", 1860, 363, 18, 18, 9, "#ffffff"),
        text("lang_lim", "8K Day Limit", 1900, 392, 20, color="#e8cdb6"),
        rect("lang_up", 2040, 60, 56, 56, 28, "#fafafa"),
        {"id": "lang_up_a", "type": "path", "x": 2040, "y": 60,
         "fill": "#1c1c1c", "d": "M0 -14L11 0L4 0L4 14L-4 14L-4 0L-11 0Z"},
    ],
    "gauge": [
        rect("gauge", 974, 641, 398, 398, 56, "#0d0d0d",
             glow={"sigma": 10, "opacity": 0.55, "color": "#a32a32"},
             streak=STREAK),
        {"id": "gauge_ticks", "type": "path", "x": 974, "y": 600,
         "fill": "#a32a32", "d": gauge_ticks()},
        text("gauge_n", "24", 974, 596, 62, color="#ffffff", weight=600),
        text("gauge_frac", "24 /100", 974, 656, 26, color="#c8c8c8"),
        text("gauge_pct", "24% Complete", 990, 760, 24, color="#e6e6e6"),
    ],
    "ctx": [
        rect("ctx", 1110, 1300, 460, 560, 56, "#cee3e8",
             gradient={"angle": 90, "stops": [
                 {"at": 0, "color": "#cee3e8"}, {"at": 1, "color": "#7ec9a2"}]},
             streak=STREAK),
        text("ctx_t", "Context Window", 1110, 1128, 34, color="#2c4a44"),
        text("ctx_big", "3,200", 1110, 1200, 64, color="#1d3a34", weight=600),
        text("ctx_max", "Max 8k", 1110, 1256, 28, color="#3f6157"),
    ] + [
        rect(f"ctx_bar{i}", x, 1560 - h / 2, 40, h, 12, c)
        for i, (x, h, c) in enumerate([
            (920, 120, "#e9f2ee"), (984, 175, "#dcefe6"), (1048, 265, "#dc753e"),
            (1112, 150, "#d9ede4"), (1176, 205, "#e3f0e9"), (1240, 245, "#eef4f0")])
    ],
    "pers": [
        rect("pers", 2122, 941, 405, 352, 48, "#181818", streak=STREAK),
        rect("pers_chip", 2240, 830, 130, 36, 18, "#2a2a2a"),
        text("pers_chip_t", "Ai Assistant", 2240, 831, 17, color="#cfcfcf"),
        text("pers_t", "Personality Profile", 2122, 878, 30, color="#f2f2f2"),
        rect("pers_tile", 2200, 1010, 122, 122, 30, "#aae08a"),
        {"id": "pers_mark", "type": "path", "x": 2200, "y": 1010,
         "fill": "#ffffff", "d": blossom()},
        rect("pers_i1", 1990, 962, 34, 34, 17, "#262626"),
        rect("pers_i2", 1990, 1010, 34, 34, 17, "#262626"),
        rect("pers_i3", 1990, 1058, 34, 34, 17, "#262626"),
    ],
}
sc3_nodes = []
for cid, members in sc3_members.items():
    cx, cy, edx, edy = CARDS[cid]
    rx, ry = REST[cid]
    for n in members:
        off_x, off_y = n["x"] - cx, n["y"] - cy
        n["x"], n["y"] = rx + off_x, ry + off_y
        sc3_nodes.append(n)
        tracks.append(track(n["id"], n["x"], n["y"],
                            x=[(0, cx + off_x + edx), (0.40, cx + off_x, "outCubic"),
                               (0.70, rx + off_x, "outCubic"), (0.92, rx + off_x),
                               (1.06, rx, "inCubic")],
                            y=[(0, cy + off_y + edy), (0.40, cy + off_y, "outCubic"),
                               (0.70, ry + off_y, "outCubic"), (0.92, ry + off_y),
                               (1.06, ry, "inCubic")],
                            scale=[(0.92, 1), (1.06, 0.1, "inCubic")]))
sc3_nodes += [
    text("just", "Just", 1365, 843, 95, color="#ffffff", weight=500),
    text("type", "type", 1594, 794, 95, color="#ffffff", weight=500),
]
tracks += [
    track("just", 1365, 843,
          x=[(0.44, 1365), (0.80, 1372)],
          y=[(0.44, 843), (0.80, 818)],
          opacity=[(0.10, 0), (0.13, 1), (0.92, 1), (1.06, 0.35)],
          rot=[(0.10, -55), (0.44, -12, "outCubic"), (0.80, -4, "outCubic")]),
    track("type", 1594, 794,
          x=[(0.44, 1594), (0.80, 1600)],
          y=[(0.44, 794), (0.80, 772)],
          opacity=[(0.37, 0), (0.40, 1)],
          rot=[(0.37, -12), (0.80, -4, "outCubic")]),
]

# ---------------------------------------------------------------- scene 4
# bg swaps to light mid-flight: shrinking card ghosts and the morphing text
# ride across the cut, then "boom" resolves under a teal sweep and the pair
# pops out in one frame at f193.
sc4_nodes = [
    rect("ghost_g", 974, 641, 398, 398, 56, "#0d0d0d"),
    rect("ghost_p", 2122, 941, 405, 352, 48, "#181818"),
    text("just_ghost", "Just", 1365, 843, 95, color=INK, weight=500, rot=-8),
    text("and", "and", 1180, 770, 118, weight=500),
    text("boom", "boom", 1627, 770, 118, weight=500),
]
tracks += [
    {"target": "ghost_g", "keys": {
        "scale": [{"t": 0, "v": 0.1}, {"t": 0.1, "v": 0.01}],
        "opacity": [{"t": 0, "v": 0.8}, {"t": 0.1, "v": 0}]}},
    {"target": "ghost_p", "keys": {
        "scale": [{"t": 0, "v": 0.1}, {"t": 0.1, "v": 0.01}],
        "opacity": [{"t": 0, "v": 0.8}, {"t": 0.1, "v": 0}]}},
    {"target": "just_ghost", "keys": {
        "opacity": [{"t": 0, "v": 0.35}, {"t": 0.12, "v": 0}]}},
    {"target": "and", "keys": {
        "opacity": [{"t": 0, "v": 0}, {"t": 0.1, "v": 1},
                    {"t": 0.48, "v": 1}, {"t": 0.51, "v": 0}]}},
    {"target": "boom", "reveal": {
        "unit": "glyph", "stagger": 0.045, "dur": 0.1, "rise": 0,
        "accent": "#71b3bf", "color_delay": 0.03, "color_dur": 0.2}},
    {"target": "boom", "at": 0.48, "keys": {
        "opacity": [{"t": 0, "v": 1}, {"t": 0.03, "v": 0}]}},
]

# ---------------------------------------------------------------- scene 5
# "It's there": two blues resolving left-to-right, tempering to ink in
# reading order, trailing letters last. camera drifts up and grows 2%.
sc5_nodes = [
    text("its", "It's", 1320, 790, 112, weight=500),
    text("there", "there", 1632, 790, 112, weight=500),
]
tracks += [
    {"target": "its", "at": 0.10, "reveal": {
        "unit": "glyph", "stagger": 0.035, "dur": 0.12, "rise": 0,
        "accent": "#5c7fca", "color_delay": 0.31, "color_dur": 0.37}},
    {"target": "there", "at": 0.27, "reveal": {
        "unit": "glyph", "stagger": 0.035, "dur": 0.12, "rise": 0,
        "accent": "#7397e4", "color_delay": 0.24, "color_dur": 0.37}},
    {"target": "s5", "keys": {
        "cam_zoom": [{"t": 0.1, "v": 1.0}, {"t": 0.94, "v": 1.02}],
        "cam_y": [{"t": 0.1, "v": 0}, {"t": 0.94, "v": 14}]}},
]

stage = {
    "fps": 30,
    "size": [W, H],
    "scenes": [
        {"id": "s1", "bg": "#f2f2f2", "dur": 3.375,
         "transition": {"kind": "cut"}, "nodes": sc1_nodes},
        {"id": "s2", "bg": "#000000", "dur": 1.608,
         "transition": {"kind": "cut"}, "nodes": sc2_nodes},
        {"id": "s3", "bg": "#000000", "dur": 1.067,
         "transition": {"kind": "cut"}, "nodes": sc3_nodes},
        {"id": "s4", "bg": "#f2f2f2", "dur": 0.608,
         "transition": {"kind": "cut"}, "nodes": sc4_nodes},
        {"id": "s5", "bg": "#f2f2f2", "dur": 0.942,
         "transition": {"kind": "cut"}, "nodes": sc5_nodes},
    ],
}

anim = {"tracks": tracks}
with open("docs/chatgpt.stage.json", "w") as f:
    json.dump(stage, f, indent=1)
with open("docs/chatgpt.anim.json", "w") as f:
    json.dump(anim, f, indent=1)
print("wrote docs/chatgpt.{stage,anim}.json,",
      sum(len(s["nodes"]) for s in stage["scenes"]), "nodes,",
      len(tracks), "tracks")
