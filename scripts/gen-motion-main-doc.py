#!/usr/bin/env python3
# reproduction of radio/motion-main (12.1s): a screen capture of the "mo"
# motion editor playing back the "iPod, but it's 2026" concept. frame is
# split: left = editor canvas (grid + yellow selection chrome), right =
# clean preview, bottom = timeline (layer bars, amber keyframe rail, green
# waveform, blue playhead in real time). the preview runs one continuous
# morph chain: glyph -> click wheel -> album cover -> phone card -> iPod
# device -> coverflow -> itunes bubbles -> green-screen dancer -> "iPod"
# wordmark -> ", but it's 2026" -> mo1 logo. all geometry measured from
# analysis/motion-main frames (2484x2160), authored at half scale.
import json
import math
import os

S = 0.5
W, H = int(2484 * S), int(2160 * S)
K = 0.5523

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

GREEN = "#93e928"
PERI = "#6c6cf4"
TLBG = "#141416"

# preview panel: x 1077..2484, canvas area y 0..1410
PX, PY = 1780, 705
# timeline ruler: t=0 at x 244, 173 px/s
TLX0, PPS = 244, 173
ROWY0, PITCH, BARH = 1556, 47, 30
DUR = 12.1


def pt(x, y):
    return f"{x * S:.1f} {y * S:.1f}"


def poly(pts, ccw=False):
    seq = list(reversed(pts)) if ccw else pts
    return "M" + "L".join(pt(x, y) for x, y in seq) + "Z"


def circle(cx, cy, r, ccw=False):
    k = r * K
    if not ccw:
        return (f"M{pt(cx - r, cy)}"
                f"C{pt(cx - r, cy - k)} {pt(cx - k, cy - r)} {pt(cx, cy - r)}"
                f"C{pt(cx + k, cy - r)} {pt(cx + r, cy - k)} {pt(cx + r, cy)}"
                f"C{pt(cx + r, cy + k)} {pt(cx + k, cy + r)} {pt(cx, cy + r)}"
                f"C{pt(cx - k, cy + r)} {pt(cx - r, cy + k)} {pt(cx - r, cy)}Z")
    return (f"M{pt(cx - r, cy)}"
            f"C{pt(cx - r, cy + k)} {pt(cx - k, cy + r)} {pt(cx, cy + r)}"
            f"C{pt(cx + k, cy + r)} {pt(cx + r, cy + k)} {pt(cx + r, cy)}"
            f"C{pt(cx + r, cy - k)} {pt(cx + k, cy - r)} {pt(cx, cy - r)}"
            f"C{pt(cx - k, cy - r)} {pt(cx - r, cy - k)} {pt(cx - r, cy)}Z")


def lines(segs):
    """open polyline segments for stroked chrome."""
    out = []
    for seg in segs:
        out.append("M" + "L".join(pt(x, y) for x, y in seg))
    return "".join(out)


def text(id, s, x, y, size, color, weight=400, family="inter"):
    return {"id": id, "type": "text", "text": s, "x": round(x * S, 1),
            "y": round(y * S, 1), "color": color,
            "font": {"size": round(size * S, 1), "weight": weight,
                     "family": family}}


def ltext(id, s, left, y, size, color, weight=400):
    cx = left + len(s) * size * 0.5 / 2
    return text(id, s, cx, y, size, color, weight)


def rect(id, x, y, w, h, r, fill, **kw):
    n = {"id": id, "type": "rect", "x": round(x * S, 1), "y": round(y * S, 1),
         "w": round(w * S, 1), "h": round(h * S, 1),
         "radius": round(r * S, 1), "fill": fill}
    n.update(kw)
    return n


def path(id, x, y, d, fill, **kw):
    n = {"id": id, "type": "path", "x": round(x * S, 1),
         "y": round(y * S, 1), "d": d, "fill": fill}
    n.update(kw)
    return n


def grad(angle, c0, c1):
    return {"angle": angle, "stops": [{"at": 0, "color": c0},
                                      {"at": 1, "color": c1}]}


SCALED = {"x", "y", "w", "h", "blur", "glow_sigma"}


def keyed(nid, **props):
    keys = {}
    for name, seq in props.items():
        out = []
        for k in seq:
            v = k[1] * S if name in SCALED else k[1]
            kk = {"t": round(k[0], 3), "v": round(v, 3)}
            if len(k) > 2:
                kk["ease"] = k[2]
            out.append(kk)
        keys[name] = out
    return {"target": nid, "keys": keys}


def steps(pairs):
    ks = []
    for tt, v in pairs:
        if ks:
            ks.append({"t": round(tt - 0.001, 3), "v": ks[-1]["v"]})
        ks.append({"t": round(tt, 3), "v": v})
    return ks


def vis(nid, in0, in1, out0=None, out1=None, hi=1.0):
    ks = []
    if in0 > 0:
        ks.append((0, 0))
    ks += [(in0, 0), (in1, hi)]
    if out0 is not None:
        ks += [(out0, hi), (out1, 0)]
    return keyed(nid, opacity=ks)


nodes = []
tracks = []

# ===================================================== canvas backdrops
nodes.append(rect("cvl", 538.5, 705, 1077, 1410, 0, "#a4a4a4"))
gridsegs = [[(x, 0), (x, 1410)] for x in range(16, 1078, 160)]
gridsegs += [[(0, y), (1077, y)] for y in range(63, 1410, 160)]
nodes.append(path("cvgrid", 0, 0, lines(gridsegs), "#949494", stroke=1.0))
# toolbar chips top-left
nodes.append(rect("tbchip", 100, 42, 156, 46, 12, "#232326"))
for i in range(3):
    nodes.append(rect(f"tbg{i}", 62 + i * 40, 42, 20, 20, 5, "#b9b9bc"))
nodes.append(rect("pvbase", PX + 1.5, 705, 1407, 1410, 0, "#bfbfbf"))
nodes.append(rect("pvblack", PX + 1.5, 705, 1407, 1410, 0, "#0a0a0a"))
tracks.append(vis("pvblack", 1.78, 2.12))
nodes.append(rect("pvgreen", PX + 1.5, 705, 1407, 1410, 0, GREEN))
tracks.append(vis("pvgreen", 5.75, 5.98))

# ===================================================== s1: glyph drop-in
# small white lozenge with the black player glyph, grows on a long ease
glyph_d = ("M" + f"{pt(-58, -60)}"
           f"C{pt(-58, -86)} {pt(-40, -92)} {pt(0, -92)}"
           f"C{pt(40, -92)} {pt(58, -86)} {pt(58, -60)}"
           f"L{pt(58, 60)}"
           f"C{pt(58, 86)} {pt(40, 92)} {pt(0, 92)}"
           f"C{pt(-40, 92)} {pt(-58, 86)} {pt(-58, 60)}Z"
           + poly([(-38, -70), (38, -70), (38, -22), (-38, -22)], ccw=True)
           + circle(0, 38, 26, ccw=True))
GLY_SC = [(0, 0.5), (0.45, 1.0, "outCubic")]
GLY_OP = [(0, 1), (0.5, 1), (0.78, 0)]
nodes.append(rect("glyshadow", PX, 745, 260, 90, 45, "#8f8f8f", blur=10))
tracks.append(keyed("glyshadow", scale=GLY_SC,
                    opacity=[(0, 0.4), (0.5, 0.4), (0.72, 0)]))
nodes.append(rect("glylo", PX, 710, 250, 130, 65, "#f4f4f4"))
tracks.append(keyed("glylo", scale=GLY_SC, opacity=GLY_OP))
nodes.append(path("glymark", PX, 710, glyph_d, "#101010"))
tracks.append(keyed("glymark", scale=[(0, 0.35), (0.45, 0.62, "outCubic")],
                    opacity=GLY_OP))
# canvas mirror
nodes.append(path("m_glylo", 655, 795, circle(0, 0, 115), "#747474"))
tracks.append(keyed("m_glylo", scale=GLY_SC, opacity=GLY_OP))
nodes.append(path("m_glymark", 655, 793, glyph_d, "#1e1e1e"))
tracks.append(keyed("m_glymark", scale=[(0, 0.3), (0.45, 0.55, "outCubic")],
                    opacity=GLY_OP))

# ===================================================== s2: MO1 click wheel
WHL_SC = [(0.45, 0.55), (0.95, 1.0, "outCubic")]
WHL_OP = [(0, 0), (0.45, 0), (0.6, 1), (1.08, 1), (1.32, 0)]
rew_d = (poly([(0, -30), (0, 30), (-36, 0)])
         + poly([(30, -30), (30, 30), (-6, 0)]))
ff_d = (poly([(0, -30), (36, 0), (0, 30)])
        + poly([(-30, -30), (6, 0), (-30, 30)]))
pp_d = (poly([(-34, -24), (-6, 0), (-34, 24)])
        + poly([(4, -24), (16, -24), (16, 24), (4, 24)])
        + poly([(24, -24), (36, -24), (36, 24), (24, 24)]))
wheel_parts = [
    rect("whlbody", PX, 710, 660, 660, 330, "#c9c9c9"),
    rect("whlglow", PX, 710, 612, 612, 306, GREEN, blur=22,
         glow={"sigma": 60, "opacity": 0.9, "color": GREEN}),
    rect("whlmid", PX, 710, 470, 470, 235, "#efefef"),
    rect("whlhole", PX, 710, 200, 200, 100, "#c3c3c3"),
    text("whlmo1", "MO1", PX, 478, 64, "#9d9d9d", weight=700),
    path("whlrew", PX - 235, 710, rew_d, "#a6a6a6"),
    path("whlff", PX + 235, 710, ff_d, "#a6a6a6"),
    path("whlpp", PX, 945, pp_d, "#a6a6a6"),
]
for n in wheel_parts:
    nodes.append(n)
    if n["id"] == "whlglow":
        tracks.append(keyed("whlglow", scale=WHL_SC, opacity=[
            (0, 0), (0.5, 0), (0.66, 0.92, "outCubic"),
            (1.02, 0.15, "inOutCubic"), (1.2, 0)]))
    else:
        tracks.append(keyed(n["id"], scale=WHL_SC, opacity=WHL_OP))
# canvas mirror wheel
m_wheel = [
    rect("mwhlbody", 645, 785, 520, 520, 260, "#7c7c7c"),
    rect("mwhlhole", 645, 785, 160, 160, 80, "#0c0c0c"),
    text("mwhlmo1", "MO1", 645, 600, 52, "#9e9e9e", weight=700),
    path("mwhlrew", 645 - 185, 785, rew_d, "#9a9a9a"),
    path("mwhlff", 645 + 185, 785, ff_d, "#9a9a9a"),
    path("mwhlpp", 645, 970, pp_d, "#9a9a9a"),
]
for n in m_wheel:
    nodes.append(n)
    tracks.append(keyed(n["id"], scale=WHL_SC, opacity=WHL_OP))

# ============================== s3+s4: album cover -> phone card (one rect)
# grows out of the wheel to full bleed, collapses into the now-playing
# card on black, later lifts above the device and fans away
nodes.append(rect("cover", PX, 705, 100, 100, 44,
                  "#8a6a4e", gradient=grad(30, "#c09468", "#5e4736")))
tracks.append(keyed(
    "cover",
    w=[(1.05, 240), (1.38, 1410, "outCubic"), (1.95, 1410),
       (2.3, 760, "inOutCubic"), (4.0, 760), (4.35, 470, "inOutCubic")],
    h=[(1.05, 240), (1.38, 1414, "outCubic"), (1.95, 1414),
       (2.3, 760, "inOutCubic"), (4.0, 760), (4.35, 470, "inOutCubic")],
    y=[(1.95, 0), (2.3, -15, "inOutCubic"), (4.0, -15),
       (4.35, -385, "inOutCubic"), (4.9, -385), (5.3, -455, "inOutCubic")],
    scale=[(2.9, 1), (3.4, 0.95, "inOutCubic"), (3.95, 1.0, "inOutCubic")],
    rot=[(4.9, 0), (5.25, -5, "inOutCubic")],
    opacity=[(0, 0), (1.05, 0), (1.22, 1), (5.3, 1), (5.6, 0)]))
# full-bleed labels, lower left
nodes.append(ltext("cvt1", "Seigfried", 1210, 1160, 66, "#f5f5f5",
                   weight=700))
nodes.append(ltext("cvt2", "Frank Ocean", 1214, 1230, 44, "#d9d9d9"))
tracks.append(vis("cvt1", 1.38, 1.58, 1.95, 2.15))
tracks.append(vis("cvt2", 1.42, 1.62, 1.95, 2.15))
# now-playing card chrome (card spans x 1400..2160, y 310..1070)
card_chrome = [
    ltext("np941", "9:41", 1455, 395, 42, "#f2f2f2", weight=600),
    rect("npsig", 2035, 393, 30, 20, 4, "#e8e8e8"),
    rect("npbat", 2085, 393, 44, 22, 8, "#e8e8e8"),
    ltext("nptitle", "Seigfried", 1455, 862, 60, "#ffffff", weight=700),
    ltext("npartist", "Frank Ocean", 1457, 925, 40, "#d4d4d4"),
    rect("npsc1", 1600, 985, 300, 7, 3, "#f4f4f4"),
    rect("npsc2", 1955, 985, 310, 7, 3, "#8a8377"),
    ltext("npt1", "5:34", 2050, 1030, 32, "#efefef"),
]
NP_OP = (2.18, 2.4, 3.8, 4.0)
for n in card_chrome:
    nodes.append(n)
    tracks.append(vis(n["id"], *NP_OP))
# live scrubber time: 1:36 steps to 1:52 mid-hold
nodes.append(ltext("npt0a", "1:36", 1455, 1030, 32, "#efefef"))
tracks.append({"target": "npt0a", "keys": {"opacity": [
    {"t": 0, "v": 0}, {"t": 2.18, "v": 0}, {"t": 2.4, "v": 1},
    {"t": 3.349, "v": 1}, {"t": 3.35, "v": 0}]}})
nodes.append(ltext("npt0b", "1:52", 1455, 1030, 32, "#efefef"))
tracks.append({"target": "npt0b", "keys": {"opacity": [
    {"t": 0, "v": 0}, {"t": 3.349, "v": 0}, {"t": 3.35, "v": 1},
    {"t": 3.8, "v": 1}, {"t": 4.0, "v": 0}]}})
# canvas mirror: the cover reads as a light grey slab that fills the
# canvas with the expand, then collapses into the card
nodes.append(rect("mcard", 560, 760, 240, 240, 30, "#9b9b9b"))
tracks.append(keyed(
    "mcard",
    w=[(1.05, 240), (1.38, 1000, "outCubic"), (1.95, 1000),
       (2.3, 600, "inOutCubic")],
    h=[(1.05, 240), (1.38, 1030, "outCubic"), (1.95, 1030),
       (2.3, 600, "inOutCubic")],
    opacity=[(0, 0), (1.05, 0), (1.25, 1), (3.8, 1), (4.0, 0)]))
m_card = [
    ltext("mct1", "Seigfried", 340, 900, 52, "#f2f2f2", weight=700),
    ltext("mct2", "Frank Ocean", 342, 955, 36, "#dedede"),
    rect("mcsc", 620, 1010, 520, 6, 3, "#cccccc"),
]
for n in m_card:
    nodes.append(n)
    tracks.append(vis(n["id"], *NP_OP))

# ===================================================== s5: tab bar + card2
tab_icons = (
    lines([[(-170, 8), (-170, -8), (-156, -20), (-142, -8), (-142, 8),
            (-170, 8)]])
    + circle(0, 0, 16) + circle(0, 0, 6, ccw=True)
    + lines([[(146, -12), (178, -12)], [(146, 0), (178, 0)],
             [(146, 12), (178, 12)]]))
nodes.append(rect("tabbar", PX, 1180, 560, 96, 48, "#1d1d1f"))
nodes.append(path("tabicons", PX, 1180, tab_icons, "#d8d8d8", stroke=1.6))
for nid in ("tabbar", "tabicons"):
    tracks.append(keyed(
        nid,
        y=[(3.0, 160), (3.4, 0, "outCubic"), (4.4, 0),
           (4.75, -75, "inOutCubic")],
        opacity=[(0, 0), (2.98, 0), (3.2, 1), (5.35, 1), (5.6, 0)]))

CARD2_Y = [(3.45, -420), (3.9, 0, "outCubic"), (4.8, 0),
           (5.2, 60, "inOutCubic")]
CARD2_OP = [(0, 0), (3.4, 0), (3.6, 1), (5.3, 1), (5.6, 0)]
nodes.append(rect("card2", PX, 150, 560, 330, 40, "#a03326",
                  gradient=grad(40, "#c8402e", "#6f1c14")))
nodes.append(text("c2t1", "Illegal", PX, 130, 40, "#ffffff", weight=700))
nodes.append(text("c2t2", "PinkPantheress", PX, 185, 27, "#f0d9d6"))
for nid in ("card2", "c2t1", "c2t2"):
    tracks.append(keyed(nid, y=CARD2_Y, opacity=CARD2_OP,
                        rot=[(4.8, 0), (5.15, 5, "inOutCubic")]))

# ===================================================== s6: iPod device
DEV_OP = [(0, 0), (3.9, 0), (4.2, 1), (5.3, 1), (5.58, 0)]
DEV_SC = [(3.9, 0.92), (4.25, 1.0, "outCubic")]
dev_parts = [
    rect("devbody", PX, 800, 700, 880, 90, "#f3f3f4"),
    rect("devwheel", PX, 950, 420, 420, 210, "#e2e2e4"),
    rect("devhole", PX, 950, 140, 140, 70, "#f3f3f4"),
    path("devrew", PX - 150, 950, rew_d, "#bcbcc0"),
    path("devff", PX + 150, 950, ff_d, "#bcbcc0"),
    path("devpp", PX, 1100, pp_d, "#bcbcc0"),
]
for n in dev_parts:
    nodes.append(n)
    tracks.append(keyed(n["id"], scale=DEV_SC, opacity=DEV_OP))
# canvas mirror: grey card stack rising
for i in range(4):
    g = ["#6e6e6e", "#8b8b8b", "#a5a5a5", "#bcbcbc"][i]
    nodes.append(rect(f"mstack{i}", 640, 620 - i * 78, 360 - i * 26,
                      i and 60 or 340, 18, g))
    tracks.append(keyed(
        f"mstack{i}",
        y=[(4.1 + i * 0.12, 90), (4.5 + i * 0.12, 0, "outCubic")],
        opacity=[(0, 0), (4.1 + i * 0.12, 0), (4.3 + i * 0.12, 1),
                 (5.35, 1), (5.62, 0)]))

# ===================================================== s6/7: card3 + fan
nodes.append(rect("card3", PX, 335, 500, 310, 38, "#1e3a52",
                  gradient=grad(35, "#2c4f6e", "#0e1c2a")))
nodes.append(text("c3t1", "Paper Trails", PX - 60, 310, 38, "#ffffff",
                  weight=700))
nodes.append(text("c3t2", "Darkside", PX - 90, 362, 27, "#c2ccd4"))
for nid in ("card3", "c3t1", "c3t2"):
    tracks.append(keyed(
        nid,
        y=[(4.15, 80), (4.5, 0, "outCubic"), (4.9, 0),
           (5.3, -55, "inOutCubic")],
        rot=[(4.9, 0), (5.25, 4, "inOutCubic")],
        opacity=[(0, 0), (4.15, 0), (4.4, 1), (5.35, 1), (5.62, 0)]))
nodes.append(rect("card4", PX, 240, 560, 350, 40, "#4a86c2",
                  gradient=grad(30, "#62a0dc", "#2d69a8")))
nodes.append(text("c4t1", "The Rockafeller Skank", PX - 60, 190, 40,
                  "#ffffff", weight=700))
nodes.append(text("c4t2", "Fatboy Slim", PX - 160, 245, 28, "#dce9f4"))
for nid in ("card4", "c4t1", "c4t2"):
    tracks.append(keyed(
        nid,
        y=[(4.85, 300), (5.25, 0, "outCubic")],
        opacity=[(0, 0), (4.85, 0), (5.05, 1), (5.45, 1), (5.72, 0)]))

# ===================================================== s8: itunes bubbles
BUBS = [(1265, 200, 150, "#575759"), (2300, 250, 170, "#7a6f63"),
        (1430, 730, 95, "#8a7460"), (2190, 770, 120, "#5f6c7a"),
        (1310, 1210, 105, "#7d6f7d"), (2340, 1180, 80, "#585f6b"),
        (2060, 1050, 70, "#6d7a88"), (1650, 1290, 88, "#665c50")]
for i, (bx, by, br, bc) in enumerate(BUBS):
    nodes.append(rect(f"bub{i}", bx, by, br * 2, br * 2, br, bc))
    tracks.append(vis(f"bub{i}", 4.9 + (i % 3) * 0.1, 5.2 + (i % 3) * 0.1,
                      5.72, 5.95, hi=0.92))
    tracks.append({"target": f"bub{i}", "at": 4.9, "loop": True,
                   "keys": {"y": [
                       {"t": 0, "v": 0},
                       {"t": 1.2 + (i % 4) * 0.2, "v": round(-16 * S, 1),
                        "ease": "inOutCubic"},
                       {"t": 2.4 + (i % 4) * 0.4, "v": 0,
                        "ease": "inOutCubic"}]}})
MBUBS = [(160, 240, 165), (515, 130, 120), (870, 320, 175), (130, 620, 95),
         (460, 590, 130), (940, 700, 110), (250, 1000, 150), (640, 950, 90),
         (900, 1180, 130), (420, 1290, 105)]
for i, (bx, by, br) in enumerate(MBUBS):
    g = ["#7a7a7a", "#8f8f8f", "#6b6b6b", "#9b9b9b", "#818181",
         "#747474", "#989898", "#888888", "#6f6f6f", "#929292"][i]
    nodes.append(rect(f"mbub{i}", bx, by, br * 2, br * 2, br, g))
    tracks.append(vis(f"mbub{i}", 4.95, 5.25, 5.85, 6.1, hi=0.9))
IT_OP = [(0, 0), (5.3, 0), (5.55, 1), (5.82, 1), (6.02, 0)]
IT_SC = [(5.4, 0.8), (5.72, 1.0, "outCubic")]
note_d = (circle(-52, 52, 30) + circle(40, 64, 30)
          + poly([(-30, 52), (-22, 52), (-22, -58), (-30, -58)])
          + poly([(62, 64), (70, 64), (70, -46), (62, -46)])
          + poly([(-30, -58), (70, -46), (70, -14), (-30, -26)]))
it_parts = [
    rect("itcd", PX, 1050, 340, 340, 170, "#c9ccd4",
         gradient=grad(130, "#f0f0f4", "#9aa0ac")),
    rect("itring", PX, 1050, 130, 130, 65, "#b9bdc6"),
    rect("ithole", PX, 1050, 56, 56, 28, "#f6f6f8"),
    path("itnote", PX + 14, 1042, note_d, "#3b57e8"),
]
for n in it_parts:
    nodes.append(n)
    tracks.append(keyed(n["id"], scale=IT_SC, opacity=IT_OP))

# ===================================================== s9: the dancer
def limb(joints, w0, w1):
    """thick tapered polygon strip through the joint chain."""
    left, right = [], []
    n = len(joints)
    for i, (x, y) in enumerate(joints):
        if i == 0:
            dx, dy = joints[1][0] - x, joints[1][1] - y
        elif i == n - 1:
            dx, dy = x - joints[i - 1][0], y - joints[i - 1][1]
        else:
            dx, dy = joints[i + 1][0] - joints[i - 1][0], \
                joints[i + 1][1] - joints[i - 1][1]
        ln = math.hypot(dx, dy) or 1.0
        wx, wy = -dy / ln, dx / ln
        w = (w0 + (w1 - w0) * i / (n - 1)) / 2
        left.append((x + wx * w, y + wy * w))
        right.append((x - wx * w, y - wy * w))
    return poly(left + list(reversed(right)))


def head_d(hx, hy):
    pts = []
    for i in range(22):
        a = i / 22 * 2 * math.pi - math.pi / 2
        spike = (i % 2 == 0)
        if math.sin(a) < 0.15:
            r = 200 if spike else 120
        else:
            r = 128 if spike else 118
        pts.append((hx + r * math.cos(a), hy + r * math.sin(a)))
    return poly(pts)


def torso_d(lean):
    return poly([(-160, 90), (-185, -110), (-255 + lean * 0.6, -295),
                 (-95 + lean, -335), (95 + lean, -335),
                 (255 + lean * 0.6, -295), (185, -110), (160, 90)])


def band_d(hx, hy):
    """headphone band: filled crescent hugging the head."""
    out, inn = [], []
    for i in range(13):
        a = math.pi + i / 12 * math.pi
        out.append((hx + 152 * math.cos(a), hy + 5 + 145 * math.sin(a)))
        inn.append((hx + 112 * math.cos(a), hy + 5 + 106 * math.sin(a)))
    return poly(out + list(reversed(inn)))


def pads_d(hx, hy):
    return circle(hx - 128, hy + 22, 44) + circle(hx + 128, hy + 22, 44)


# poses: head center, torso lean, arm/leg joint chains
POSES = [
    # P0 wide stance, arms out
    {"head": (0, -430), "lean": 0,
     "al": [(-235, -265), (-360, -140), (-470, -40)],
     "ar": [(235, -265), (360, -140), (470, -40)],
     "ll": [(-95, 40), (-160, 300), (-215, 560)],
     "lr": [(95, 40), (160, 300), (215, 560)]},
    # P1 arms thrown up
    {"head": (0, -455), "lean": 0,
     "al": [(-235, -270), (-340, -420), (-420, -580)],
     "ar": [(235, -270), (340, -420), (420, -580)],
     "ll": [(-90, 40), (-115, 310), (-135, 570)],
     "lr": [(90, 40), (120, 310), (150, 570)]},
    # P2 lean left, right arm up, right leg kick
    {"head": (-65, -440), "lean": -60,
     "al": [(-240, -260), (-310, -90), (-335, 80)],
     "ar": [(230, -280), (330, -440), (395, -600)],
     "ll": [(-95, 40), (-130, 300), (-155, 560)],
     "lr": [(95, 40), (250, 250), (430, 420)]},
    # P3 crouch, arms bent in
    {"head": (0, -375), "lean": 0,
     "al": [(-235, -240), (-305, -100), (-165, -15)],
     "ar": [(235, -240), (305, -100), (165, -15)],
     "ll": [(-100, 60), (-235, 300), (-190, 560)],
     "lr": [(100, 60), (235, 300), (190, 560)]},
    # P4 phone raised in right hand
    {"head": (20, -430), "lean": 20,
     "al": [(-235, -260), (-330, -120), (-380, 30)],
     "ar": [(230, -270), (315, -450), (330, -640)],
     "ll": [(-95, 40), (-140, 300), (-180, 560)],
     "lr": [(95, 40), (150, 300), (200, 560)]},
]


def pose_parts(p):
    hx, hy = p["head"]
    return {
        "torso": torso_d(p["lean"]),
        "head": head_d(hx, hy),
        "al": limb(p["al"], 66, 46),
        "ar": limb(p["ar"], 66, 46),
        "ll": limb(p["ll"], 100, 78),
        "lr": limb(p["lr"], 100, 78),
        "band": band_d(hx, hy),
        "pads": pads_d(hx, hy),
    }


POSE_D = [pose_parts(p) for p in POSES]
ORDER = [0, 0, 1, 2, 0, 3, 1, 2, 0, 3, 4, 4]
DBASE, DSTEP = 5.55, 0.4


def dseq_for(part):
    seq = []
    for i, pi in enumerate(ORDER):
        t = DBASE + i * DSTEP
        seq.append({"at": round(t, 2), "d": POSE_D[pi][part]})
        seq.append({"at": round(t + 0.24, 2), "d": POSE_D[pi][part]})
    seq.append({"at": 10.6, "d": POSE_D[4][part]})
    return seq


DANCER_PARTS = [("ll", "#050505"), ("lr", "#050505"), ("al", "#050505"),
                ("ar", "#050505"), ("torso", "#050505"), ("head", "#050505"),
                ("band", "#f0f2f2"), ("pads", "#f0f2f2")]
DX = [(5.55, -560), (6.35, 0, "outCubic"), (10.15, 0),
      (10.5, -430, "inOutCubic")]
DY = [(10.15, 0), (10.5, 430, "inOutCubic")]
DOP = [(0, 0), (5.55, 0), (5.75, 1), (10.9, 1), (11.15, 0)]
for part, col in DANCER_PARTS:
    nodes.append({"id": f"dn_{part}", "type": "path",
                  "x": round(PX * S, 1), "y": round(720 * S, 1),
                  "fill": col, "dseq": dseq_for(part)})
    tracks.append(keyed(f"dn_{part}", x=DX, y=DY, opacity=DOP,
                        scale=[(10.15, 1), (10.5, 0.42, "inOutCubic")]))
    # canvas mirror dancer (left panel, smaller)
    nodes.append({"id": f"md_{part}", "type": "path",
                  "x": round(585 * S, 1), "y": round(905 * S, 1),
                  "fill": col, "dseq": dseq_for(part)})
    tracks.append(keyed(f"md_{part}",
                        x=[(t[0], t[1] * 0.62) + t[2:] for t in DX],
                        y=[(t[0], t[1] * 0.62) + t[2:] for t in DY],
                        opacity=DOP,
                        scale=[(0, 0.62), (10.15, 0.62),
                               (10.5, 0.26, "inOutCubic")]))
# the phone in the raised hand; during the shrink it follows the hand
# (dancer scales about its own center, the phone compensates)
nodes.append(rect("dphone", PX + 330, 60, 84, 140, 18, "#f4f4f4",
                  rot=14))
tracks.append(keyed("dphone",
                    x=[(5.55, -560), (6.35, 0, "outCubic"), (10.15, 0),
                       (10.5, -621, "inOutCubic")],
                    y=[(10.15, 0), (10.5, 821, "inOutCubic")],
                    scale=[(10.15, 1), (10.5, 0.42, "inOutCubic")],
                    opacity=[(0, 0), (9.4, 0), (9.6, 1), (10.9, 1),
                             (11.1, 0)]))

# ===================================================== s10-12: type + logo
nodes.append(text("wm_ipod", "iPod", PX, 660, 350, "#0a0a0a", weight=700))
tracks.append(keyed("wm_ipod",
                    scale=[(10.25, 0.6), (10.58, 1.0, "outCubic")],
                    opacity=[(0, 0), (10.25, 0), (10.38, 1),
                             (10.98, 1), (11.16, 0)]))
nodes.append(text("m_ipod", "iPod", 612, 720, 175, "#4a4a4a", weight=700))
tracks.append(keyed("m_ipod",
                    scale=[(10.25, 0.6), (10.58, 1.0, "outCubic")],
                    opacity=[(0, 0), (10.25, 0), (10.38, 1),
                             (10.98, 1), (11.16, 0)]))
nodes.append(text("wm_full", "iPod, but it's 2026", PX, 690, 118,
                  "#0a0a0a", weight=700))
tracks.append(keyed("wm_full",
                    x=[(10.95, 40), (11.25, 0, "outCubic")],
                    opacity=[(0, 0), (10.95, 0), (11.15, 1),
                             (11.52, 1), (11.68, 0)]))
nodes.append(text("m_full", "iPod, but it's 2026", 612, 720, 62,
                  "#4a4a4a", weight=700))
tracks.append(keyed("m_full",
                    x=[(10.95, 25), (11.25, 0, "outCubic")],
                    opacity=[(0, 0), (10.95, 0), (11.15, 1),
                             (11.52, 1), (11.68, 0)]))
MO1_OP = [(0, 0), (11.55, 0), (11.78, 1)]
MO1_SC = [(11.55, 0.85), (11.85, 1.0, "outCubic")]
mo1_parts = [
    text("mo1_m", "m", PX, 618, 230, "#0a0a0a", weight=800),
    rect("mo1_o", PX, 775, 250, 100, 50, "#0a0a0a"),
    text("mo1_1", "1", PX, 777, 82, GREEN, weight=800),
]
for n in mo1_parts:
    nodes.append(n)
    tracks.append(keyed(n["id"], scale=MO1_SC, opacity=MO1_OP))
m_mo1 = [
    text("mmo1_m", "m", 600, 700, 160, "#8a8a8a", weight=800),
    rect("mmo1_o", 600, 795, 175, 74, 37, "#8a8a8a"),
    text("mmo1_1", "1", 600, 796, 60, "#a4a4a4", weight=800),
]
for n in m_mo1:
    nodes.append(n)
    tracks.append(keyed(n["id"], scale=MO1_SC, opacity=MO1_OP))

# ===================================================== selection chrome
selbox = (lines([[(229, 554), (691, 554), (691, 1020), (229, 1020),
                  (229, 554)],
                 [(229, 554), (320, 784)], [(691, 554), (320, 784)],
                 [(229, 1020), (320, 784)], [(691, 1020), (320, 784)]]))
nodes.append(path("selbox", 0, 0, selbox, "#e8e400", stroke=1.2))
nodes.append(path("seltri", 0, 0,
                  poly([(428, 539), (508, 539), (468, 496)]), "#f2e400"))

# ===================================================== timeline chrome
nodes.append(rect("tlbg", W, 1785, 2484, 750, 0, TLBG))
# faint column + row grid under the bars
colsegs = [[(TLX0 + PPS * s, 1546), (TLX0 + PPS * s, 2050)]
           for s in range(13)]
nodes.append(path("tlcols", 0, 0, lines(colsegs), "#1d1d1f", stroke=1.0))
rowsegs = [[(244, y), (2470, y)] for y in range(1580, 2050, PITCH)]
nodes.append(path("tlrows", 0, 0, lines(rowsegs), "#191a1c", stroke=1.0))

ROWS = [
    ("Instance 18", 0.05, 1.35), ("Dial 1", 0.05, 1.35),
    ("Cover BG", 1.12, 4.83), ("Cover Expandable", 0.88, 2.85),
    ("Screen", 1.93, 4.03), ("Tabbar", 2.10, 4.03), ("Dial", 2.42, 4.03),
    ("Cards Cloner", 3.30, 4.75), ("Screen BG", 4.15, 6.05),
    ("itunes", 3.98, 5.72), ("Bubbles", 4.15, 5.90),
    ("Green BG", 4.78, 12.84), ("Character", 5.70, 7.50),
    ("Character", 7.45, 9.15), ("Character", 8.90, 10.90),
    ("iPod", 10.20, 11.30), ("2026", 10.85, 11.45), ("mo1", 11.45, 12.84),
]
SCROLL = [(5.8, 0), (6.4, -188, "inOutCubic"), (9.15, -188),
          (9.75, -329, "inOutCubic")]
for i, (name, t0, t1) in enumerate(ROWS):
    y = ROWY0 + i * PITCH
    x0 = TLX0 + PPS * t0
    bw = PPS * (t1 - t0)
    cx = x0 + bw / 2
    p = f"row{i}_"
    nodes.append(rect(p + "b", cx, y, bw, BARH, 10, "#232327"))
    nodes.append(rect(p + "a", cx, y, bw, BARH, 10, PERI))
    nodes.append(path(p + "t", x0 + 28, y,
                      poly([(0, -6), (7, 0), (0, 6)]), "#a8a8c0"))
    nodes.append(ltext(p + "l", name, x0 + 46, y + 1, 23, "#d2d2d8",
                       weight=500))
    end = min(t1, DUR + 0.5)
    on = steps([(0, 0), (t0, 1)] + ([(end, 0)] if t1 < DUR else []))
    tracks.append({"target": p + "a", "keys": {"opacity": on,
                   "y": [dict(t=k[0], v=round(k[1] * S, 1),
                              **({"ease": k[2]} if len(k) > 2 else {}))
                         for k in SCROLL]}})
    # rows scrolled past the ruler leave the visible band
    hide = None
    if i <= 3:
        hide = [(5.88, 1), (6.28, 0)]
    elif i <= 6:
        hide = [(9.2, 1), (9.65, 0)]
    for suf in ("b", "t", "l"):
        if hide:
            tracks.append(keyed(p + suf, y=SCROLL, opacity=hide))
        else:
            tracks.append(keyed(p + suf, y=SCROLL))

# ruler strip drawn over scrolled bars
nodes.append(rect("rulbg", W, 1477, 2484, 138, 0, TLBG))
for s in range(13):
    nodes.append(text(f"rul{s}", f"{s}.00", TLX0 + PPS * s, 1513, 27,
                      "#87878b"))
# transport row
nodes.append(rect("pausebg", 52, 1457, 44, 44, 11, "#232327"))
nodes.append(rect("pau1", 45, 1457, 6, 18, 2, "#f0f0f0"))
nodes.append(rect("pau2", 59, 1457, 6, 18, 2, "#f0f0f0"))
nodes.append(path("mutei", 1752, 1457,
                  poly([(-10, -6), (-2, -6), (8, -15), (8, 15), (-2, 6),
                        (-10, 6)]), "#e6e6e6"))
nodes.append(rect("sparkle", 1822, 1457, 38, 38, 10, "#2c2c54"))
nodes.append(path("sparkg", 1822, 1457,
                  poly([(0, -11), (3, -3), (11, 0), (3, 3), (0, 11),
                        (-3, 3), (-11, 0), (-3, -3)]), "#8a8af8"))
nodes.append(rect("sldtrack", 1985, 1457, 210, 6, 3, "#e4e4e6"))
nodes.append(rect("sldknob", 1893, 1457, 26, 26, 13, PERI))
nodes.append(ltext("startl", "Start", 2124, 1457, 27, "#8a8a8e"))
nodes.append(ltext("startv", "0,00", 2196, 1457, 27, "#e2e2e4"))
nodes.append(ltext("endl", "End", 2298, 1457, 27, "#8a8a8e"))
nodes.append(ltext("endv", "12,84", 2360, 1457, 27, "#e2e2e4"))

# bottom strip: amber keyframe rail + green waveform
nodes.append(rect("botbg", W, 2105, 2484, 112, 0, TLBG))
nodes.append(rect("amber", 1352, 2077, 2216, 6, 3, "#a85a12"))
for i, (a, b) in enumerate([(0.55, 1.45), (2.3, 3.6), (4.6, 5.2),
                            (6.2, 6.6), (8.3, 8.7), (10.6, 11.0)]):
    nodes.append(rect(f"amberhot{i}", TLX0 + PPS * (a + b) / 2, 2077,
                      PPS * (b - a), 9, 4, "#e07f1e"))
DIA = [0, 0.92, 1.38, 2.64, 3.42, 3.98, 4.95, 5.57, 6.39, 7.12, 7.93,
       8.75, 9.32, 9.78, 10.81, 11.45, 12.46]
for i, s in enumerate(DIA):
    nodes.append(rect(f"dia{i}", TLX0 + PPS * s, 2077, 15, 15, 3,
                      "#f0e6d8", rot=45))
nodes.append(rect("wave", 1352, 2131, 2216, 36, 18, "#17a04a"))
ticks = []
x = 262
i = 0
while x < 2440:
    h = 8 + ((i * 7919) % 19)
    ticks.append([(x, 2131 - h / 2), (x, 2131 + h / 2)])
    x += 10
    i += 1
nodes.append(path("waveticks", 0, 0, lines(ticks), "#0d7a35", stroke=1.2))

# playhead on top of everything
nodes.append(rect("phline", TLX0, 1830, 4, 660, 1, "#5757e8"))
nodes.append(rect("phhandle", TLX0, 1505, 13, 30, 3, "#5757e8"))
PH = [(0, 0), (DUR, PPS * DUR)]
tracks.append(keyed("phline", x=PH))
tracks.append(keyed("phhandle", x=PH))

stage = {
    "fps": 30,
    "size": [W, H],
    "scenes": [
        {"id": "s1", "bg": "#0a0a0b", "dur": DUR,
         "transition": {"kind": "cut"}, "nodes": nodes},
    ],
}

with open("docs/motion-main.stage.json", "w") as f:
    json.dump(stage, f, indent=1)
with open("docs/motion-main.anim.json", "w") as f:
    json.dump({"tracks": tracks}, f, indent=1)
print("wrote docs/motion-main.{stage,anim}.json,", len(nodes), "nodes,",
      len(tracks), "tracks")
