#!/usr/bin/env python3
# reproduction of animations/launch-quick4.mp4 scenes 1-2 (f1-50, 0-1.67s):
# the invert-strobe cold open and the accelerating LED logo carousel with
# the decoder headline. 30fps constant, so our frame N maps 1:1 to theirs.
# scenes 3-6 are real footage (eye macro, rocket) and out of scope.
# every logo is a dot-matrix stencil rendered as one filled path, the way
# the real video redraws every brand in the same LED grammar.
import json
import math
import os

W, H = 1920, 1080
F = 1 / 30

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def dots_path(stencil, pitch=30, r=9.5):
    """ascii stencil -> one path of filled circles, centered on the grid."""
    rows = [row for row in stencil.strip("\n").split("\n")]
    hgt, wid = len(rows), max(len(rw) for rw in rows)
    parts = []
    for gy, row in enumerate(rows):
        for gx, ch in enumerate(row):
            if ch != '#':
                continue
            x = (gx - wid / 2 + 0.5) * pitch
            y = (gy - hgt / 2 + 0.5) * pitch
            parts.append(f"M{x - r:.1f} {y:.1f}a{r} {r} 0 1 0 {2*r:.1f} 0"
                         f"a{r} {r} 0 1 0 {-2*r:.1f} 0")
    return "".join(parts)


LOGOS = {
    # knot: interlocked hexagonal ring (openai-ish)
    "knot": ("#8ed3b6", """
....####....
..##....##..
.#..####..#.
.#.#....#.#.
#..#....#..#
#.#..##..#.#
#.#..##..#.#
#..#....#..#
.#.#....#.#.
.#..####..#.
..##....##..
....####...."""),
    # 8-arm asterisk over two squares
    "asterisk": ("#67e5d7", """
.....##.....
.#...##...#.
..#..##..#..
...#.##.#...
....####....
############
############
....####....
...#.##.#...
..#..##..#..
.#...##...#.
.....##....."""),
    "cube": ("#ffffff", """
.....##.....
...##..##...
..#......#..
.##........#
#....##....#
#..##..##..#
#.#......#.#
#.#......#.#
#..##..##..#
#....##....#
.##......##.
...######..."""),
    "heart": ("#e491e0", """
............
..##....##..
.####..####.
############
############
############
.##########.
..########..
...######...
....####....
.....##.....
............"""),
    "snake": ("#deea59", """
............
.#########..
.........#..
.........#..
..#######...
..#.........
..#.........
...######...
.........#..
.........#..
.#########..
............"""),
    "chevron": ("#eb9044", """
#....#......
##....#.....
.##....#....
..##....#...
...##....#..
....##....#.
....##....#.
...##....#..
..##....#...
.##....#....
##....#.....
#....#......"""),
    "bars": ("#ffffff", """
....#..#....
...#....#...
..#......#..
..#......#..
.#........#.
.#........#.
.#........#.
.#........#.
..#......#..
..#......#..
...#....#...
....#..#...."""),
    "claw": ("#ffffff", """
............
..#..#..#...
..#..#..#...
.#..#..#....
.#..#..#....
#..#..#..##.
#..#..#.#...
#..#..#.#...
#..#..##....
.#..#.......
..##........
............"""),
    "spiral": ("#dfea94", """
....######..
..##......#.
.#.........#
.#..####...#
#..#....#..#
#..#.##.#..#
#..#.##..#.#
#..#....#..#
.#..####..#.
.#.......#..
..##....##..
....####...."""),
    "equalizer": ("#ffffff", """
.....#......
..#..#..#...
..#..#..#...
..#..#..#..#
#.#..#..#..#
#.#..#..#..#
#.#..#..#..#
#.#..#..#..#
#.#..#..#..#
..#..#..#..#
..#..#..#...
.....#......"""),
    "blobs": ("#1f00f8", """
............
...####.....
..######....
..######....
...####.....
............
......####..
.....######.
.....######.
......####..
.##.........
............"""),
    "sunburst": ("#e4ae9b", """
.....##.....
.#...##...#.
..#.####.#..
...######...
.##########.
############
############
.##########.
...######...
..#.####.#..
.#...##...#.
.....##....."""),
}

# first-visible frame per logo, from the swap timeline; deck loops at the end
WINDOWS = {
    "knot": [(8, 13), (43, 45)],
    "asterisk": [(13, 17), (45, 47)],
    "cube": [(17, 21), (47, 49)],
    "heart": [(21, 24), (49, 51)],
    "snake": [(24, 27)],
    "chevron": [(27, 30)],
    "bars": [(30, 32)],
    "claw": [(32, 35)],
    "spiral": [(35, 37)],
    "equalizer": [(37, 39)],
    "blobs": [(39, 41)],
    "sunburst": [(41, 43)],
}


def steps(windows):
    """opacity keys for hard 1-frame swaps: on at window start, off at end."""
    ks = [{"t": 0, "v": 0}] if windows[0][0] > 8 else []
    for a, b in windows:
        ta, tb = (a - 8) * F, (b - 8) * F
        ks += [{"t": round(ta - 0.001, 4), "v": 0}, {"t": round(ta, 4), "v": 1},
               {"t": round(tb - 0.001, 4), "v": 1}, {"t": round(tb, 4), "v": 0}]
    if ks and ks[0]["t"] < 0:
        ks[0]["t"] = 0
    return ks


def halftone(pitch=16, r=1.1, w=W, h=H):
    parts = []
    for gy in range(0, h, pitch):
        for gx in range(0, w, pitch):
            x, y = gx + (gy // pitch % 2) * pitch / 2, gy
            parts.append(f"M{x - r} {y}a{r} {r} 0 1 0 {2*r} 0"
                         f"a{r} {r} 0 1 0 {-2*r} 0")
    return "".join(parts)


def box_path(w, h):
    return f"M{-w/2} {-h/2}L{w/2} {-h/2}L{w/2} {h/2}L{-w/2} {h/2}Z"


def dashed_arc(x0, y0, cx, cy, x1, y1, n=26):
    """dash segments along a quadratic bezier."""
    parts = []
    for i in range(n):
        if i % 2:
            continue
        t0, t1 = i / n, (i + 0.6) / n
        def q(u):
            a = (1 - u) ** 2
            b = 2 * u * (1 - u)
            c = u ** 2
            return a * x0 + b * cx + c * x1, a * y0 + b * cy + c * y1
        ax, ay = q(t0)
        bx, by = q(t1)
        parts.append(f"M{ax:.1f} {ay:.1f}L{bx:.1f} {by:.1f}")
    return "".join(parts)


tracks = []

# ------------------------------------------------- scene 1: invert strobe
# strict one-flip-per-frame alternation f1-6, the glitch square teleporting
# every black frame, then f7 stays black and the scene hands off.
def stepk(pairs, f0=1):
    ks = []
    for f, v in pairs:
        t = (f - f0) * F
        if ks:
            ks.append({"t": round(t - 0.001, 4), "v": ks[-1]["v"]})
        ks.append({"t": round(t, 4), "v": v})
    return ks


sc1_nodes = [
    {"id": "paper", "type": "path", "x": 0, "y": 0, "fill": "#111111",
     "d": halftone()},
    {"id": "blackout", "type": "rect", "x": 960, "y": 540, "w": 1920,
     "h": 1080, "radius": 0, "fill": "#0a0c09"},
    {"id": "tiles", "type": "path", "x": 4, "y": 6, "fill": "#3a423c",
     "d": halftone(pitch=22, r=2.2)},
    {"id": "glitch", "type": "rect", "x": 1585, "y": 292, "w": 330, "h": 330,
     "radius": 0, "fill": "#f4f2ec"},
]
tracks += [
    keyed_ := {"target": "paper", "keys": {"opacity": stepk(
        [(1, 0.14), (2, 0), (3, 0.14), (4, 0), (5, 0.14), (6, 0)])}},
    {"target": "blackout", "keys": {"opacity": stepk(
        [(1, 0), (2, 1), (3, 0), (4, 1), (5, 0), (6, 1)])}},
    {"target": "tiles", "keys": {"opacity": stepk(
        [(1, 0), (2, 0.5), (3, 0), (4, 0.5), (5, 0), (6, 0.5)])}},
    {"target": "glitch", "keys": {
        "opacity": stepk([(1, 0), (2, 1), (3, 0), (4, 1), (5, 0), (6, 1)]),
        "x": stepk([(2, 0), (4, -420), (6, -190), (7, -530)]),
        "y": stepk([(2, 0), (4, 105), (6, 288), (7, 420)])}},
]

# ------------------------------------------------ scene 2: LED carousel
sc2_nodes = [
    {"id": "tiles2", "type": "path", "x": 4, "y": 6, "fill": "#141a16",
     "d": halftone(pitch=22, r=2.2)},
    {"id": "line", "type": "text", "text": "Every AI product", "x": 480,
     "y": 512, "color": "#ffffff",
     "font": {"size": 44, "weight": 500}},
    {"id": "lbl1", "type": "text", "text": "x: 310  y: 507", "x": 380,
     "y": 455, "color": "#ffffff", "font": {"size": 15, "family": "mono"}},
    {"id": "lbl2", "type": "text", "text": "x: 1110  y: 219", "x": 1190,
     "y": 219, "color": "#ffffff", "font": {"size": 15, "family": "mono"}},
    {"id": "selbox", "type": "path", "x": 1400, "y": 550, "fill": "#513d92",
     "stroke": 2.0, "d": box_path(400, 400)},
    {"id": "arc", "type": "path", "x": 0, "y": 0, "fill": "#cfcfcf",
     "stroke": 1.6, "d": dashed_arc(700, 540, 1050, 700, 1230, 570)},
]
for name, (color, stencil) in LOGOS.items():
    sc2_nodes.append({"id": name, "type": "path", "x": 1400, "y": 550,
                      "fill": color, "d": dots_path(stencil)})
    tracks.append({"target": name, "keys": {"opacity": steps(WINDOWS[name])}})
tracks += [
    {"target": "line", "reveal": {
        "unit": "scramble", "cadence": 0.052, "churn": 4}},
    {"target": "lbl1", "keys": {"opacity": stepk(
        [(8, 1), (20, 0), (23, 1), (40, 1)], f0=8)}},
    {"target": "lbl2", "keys": {"opacity": stepk(
        [(8, 0), (13, 1), (30, 0), (39, 1)], f0=8)}},
    # selection boxes live exactly with their logos (cube, claw, equalizer)
    {"target": "selbox", "keys": {"opacity": stepk(
        [(8, 0), (17, 1), (21, 0), (32, 1), (39, 0), (47, 1), (49, 0)], f0=8)}},
    {"target": "arc", "keys": {"opacity": stepk(
        [(8, 0), (20, 0.9), (31, 0.9), (39, 0), (49, 0.9)], f0=8)}},
]

stage = {
    "fps": 30,
    "size": [W, H],
    "scenes": [
        {"id": "s1", "bg": "#f4f2ec", "dur": round(7 * F, 4),
         "transition": {"kind": "cut"}, "nodes": sc1_nodes},
        {"id": "s2", "bg": "#030605", "dur": round(44 * F, 4),
         "transition": {"kind": "cut"}, "nodes": sc2_nodes},
    ],
}

with open("docs/launch-quick4.stage.json", "w") as f:
    json.dump(stage, f, indent=1)
with open("docs/launch-quick4.anim.json", "w") as f:
    json.dump({"tracks": tracks}, f, indent=1)
print("wrote docs/launch-quick4.{stage,anim}.json,",
      sum(len(s["nodes"]) for s in stage["scenes"]), "nodes,",
      len(tracks), "tracks")
