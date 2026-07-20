#!/usr/bin/env python3
# reproduction of radio/base-2.mp4 (8.77s, 1280x720): the base44 rebrand
# happening on an artboard. old lockup deletes to its mark, the mark gets
# selected on a design canvas and liquid-morphs through the labeled design
# process (gear -> team arrows -> bulb -> crown -> eye) into the new
# sunrise mark, then the new wordmark hammers in. all icon shapes are
# authored loops the engine's dseq morphing flows between; timings mapped
# from the frame ledger (30fps constant, 1:1).
import json
import math
import os

W, H = 1280, 720
K = 0.5523  # circle-from-bezier constant

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


def poly(pts, ccw=False):
    seq = list(reversed(pts)) if ccw else pts
    return "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in seq) + "Z"


def gear():
    """8 square teeth around r 72-98, CCW square hole."""
    pts = []
    n = 8
    for i in range(n):
        a0 = (i / n) * 2 * math.pi
        for (da, r) in [(0.02, 72), (0.18, 72), (0.24, 98), (0.62, 98),
                        (0.68, 72), (0.98, 72)]:
            a = a0 + da * 2 * math.pi / n
            pts.append((r * math.cos(a), r * math.sin(a)))
    return poly(pts) + poly([(-24, -24), (24, -24), (24, 24), (-24, 24)], ccw=True)


def arrow(sign):
    """chunky rounded block with a corner arrowhead; sign=1 points up-right
    (the blue one), sign=-1 down-left (the orange one)."""
    s = sign
    pts = [(-55, -10), (10, -10), (10, -55), (55, -55), (55, 10), (10, 10),
           (10, 55), (-10, 55), (-10, 30), (-55, 30)]
    out = [(x * s, y * -s) for x, y in pts]
    return poly(out if s > 0 else list(reversed(out)))


def bulb():
    """conceptualizing: a bulb blob with a squat neck."""
    return ("M-62 -20"
            "C-62 -78 -34 -96 0 -96"
            "C34 -96 62 -78 62 -20"
            "C62 14 40 30 30 48"
            "L30 72L-30 72L-30 48"
            "C-40 30 -62 14 -62 -20Z")


def crown():
    """perfecting: flared top with a center stub over a slab base."""
    return ("M-16 -92L16 -92L16 -62"
            "C40 -70 70 -66 92 -52"
            "L92 -30C92 -6 60 8 30 12"
            "L30 26L92 26L92 88L-92 88L-92 26L-30 26L-30 12"
            "C-60 8 -92 -6 -92 -30"
            "L-92 -52C-70 -66 -40 -70 -16 -62Z")


def eye():
    return ("M-96 0C-60 -58 60 -58 96 0"
            "C60 58 -60 58 -96 0Z"
            + circle(0, 0, 30, ccw=True))


def disc(r=98):
    return circle(0, 0, r)


def slats(r=98):
    """the old mark's horizon stripes, one node over the disc in bg color."""
    bars = []
    for y0, h in [(8, 12), (34, 11), (58, 9)]:
        halfw = math.sqrt(max(r * r - y0 * y0, 100)) + 4
        bars.append(poly([(-halfw, y0), (halfw, y0), (halfw, y0 + h), (-halfw, y0 + h)]))
    return "".join(bars)


def newmark(r=94):
    """sunrise: dome over one horizon gap, small arc slab below."""
    k = r * K
    dome = (f"M{-r} -8"
            f"C{-r} {-8 - k} {-k} {-r - 8} 0 {-r - 8}"
            f"C{k} {-r - 8} {r} {-8 - k} {r} -8Z")
    a = 0.78 * r
    slab = (f"M{-a} 14"
            f"C{-a * 0.6} {14 + 26} {a * 0.6} {14 + 26} {a} 14"
            f"L{a * 0.86} 30"
            f"C{a * 0.5} {30 + 18} {-a * 0.5} {30 + 18} {-a * 0.86} 30Z")
    return dome + slab


def text(id, s, x, y, size, color, weight=400):
    return {"id": id, "type": "text", "text": s, "x": x, "y": y,
            "color": color, "font": {"size": size, "weight": weight}}


def steps(pairs):
    ks = []
    for tt, v in pairs:
        if ks:
            ks.append({"t": round(tt - 0.001, 3), "v": ks[-1]["v"]})
        ks.append({"t": round(tt, 3), "v": v})
    return ks


tracks = []

# ---------------------------------------------------------------- scene 1
# old lockup on the flat bg: wordmark deletes right-to-left (f31-38), the
# mark drifts to center and grows into the canvas world.
OLD_INK = "#35342f"
glyphs1 = [("b1", "B", 575), ("b2", "a", 634), ("b3", "s", 684),
           ("b4", "e", 731), ("b5", "4", 800), ("b6", "4", 848)]
sc1_nodes = [
    {"id": "mark1", "type": "path", "x": 467, "y": 360, "fill": "#f16204",
     "d": disc(52)},
    {"id": "slats1", "type": "path", "x": 467, "y": 360, "fill": "#edece7",
     "d": slats(52)},
] + [text(g, ch, x, 360, 92, OLD_INK, weight=700) for g, ch, x in glyphs1]
# scale the slat geometry down with the small mark
for n in sc1_nodes[:2]:
    if n["id"] == "slats1":
        n["d"] = slats(52)
# delete right-to-left, then the mark takes the stage
for i, (g, _, _) in enumerate(reversed(glyphs1)):
    at = 1.0 + i * 0.045
    tracks.append({"target": g, "keys": {"opacity": steps([(at, 1), (at + 0.05, 0)])}})
for nid in ("mark1", "slats1"):
    tracks.append({"target": nid, "keys": {
        "x": [{"t": 1.3, "v": 0}, {"t": 1.66, "v": 173, "ease": "inOutCubic"}],
        "scale": [{"t": 1.3, "v": 1}, {"t": 1.66, "v": 1.88, "ease": "inOutCubic"}],
    }})

# ---------------------------------------------------------------- scene 2
# the artboard: grain, selection chrome, the labeled morph chain, the new
# lockup assembling. times are scene-local (global minus 1.667).
STAGES = [
    ("01_old_logo", 0.00),
    ("02_Planning", 1.13),
    ("03_Team_work", 2.03),
    ("04_Conceptualizing", 2.46),
    ("05_Perfecting", 3.06),
    ("06_Finalizing", 3.73),
    ("07_New_Logo", 3.96),
]
DSEQ = [
    {"at": 0.00, "d": disc()},
    {"at": 0.83, "d": disc()},
    {"at": 1.13, "d": gear()},
    {"at": 1.73, "d": gear()},
    {"at": 2.03, "d": arrow(-1)},
    {"at": 2.16, "d": arrow(-1)},
    {"at": 2.46, "d": bulb()},
    {"at": 2.76, "d": bulb()},
    {"at": 3.06, "d": crown()},
    {"at": 3.43, "d": crown()},
    {"at": 3.73, "d": eye()},
    {"at": 3.76, "d": eye()},
    {"at": 3.96, "d": newmark()},
]


def grain():
    parts = []
    step = 9
    for gy in range(0, H, step):
        for gx in range(0, W, step):
            # deterministic scatter
            jx = (gx * 7 + gy * 13) % 5 - 2
            jy = (gx * 11 + gy * 3) % 5 - 2
            if (gx + gy) % 27 < 9:
                parts.append(f"M{gx + jx} {gy + jy}L{gx + jx + 1.2} {gy + jy}"
                             f"L{gx + jx + 1.2} {gy + jy + 1.2}L{gx + jx} {gy + jy + 1.2}Z")
    return "".join(parts)


NEW_INK = "#2d2a31"
glyphs2 = [("n1", "B", 556), ("n2", "a", 622), ("n3", "s", 678),
           ("n4", "e", 731), ("n5", "4", 793), ("n6", "4", 851)]
sc2_nodes = [
    {"id": "grain", "type": "path", "x": 0, "y": 0, "fill": "#d9d6cd",
     "d": grain()},
    {"id": "mark2", "type": "path", "x": 640, "y": 358, "fill": "#f19107",
     "dseq": DSEQ},
    {"id": "slats2", "type": "path", "x": 640, "y": 358, "fill": "#f3f2ee",
     "d": slats(98)},
    {"id": "blue", "type": "path", "x": 640, "y": 358, "fill": "#566be8",
     "dseq": [
         {"at": 1.93, "d": circle(60, -60, 3)},
         {"at": 2.10, "d": arrow(1)},
         {"at": 2.86, "d": arrow(1)},
         {"at": 3.06, "d": crown()},
     ]},
] + [
    {"id": f"h{i}", "type": "rect", "x": hx, "y": hy, "w": 13, "h": 13,
     "radius": 1, "fill": "#2d2c28"}
    for i, (hx, hy) in enumerate([(507, 230), (774, 230), (507, 481), (774, 481)])
] + [
    text(f"lbl{i}", name, 500 + len(name) * 3.8, 200, 15, "#8a8a86")
    for i, (name, _) in enumerate(STAGES)
] + [text(g, ch, x, 360, 100, NEW_INK, weight=700) for g, ch, x in glyphs2]

# labels swap with the stages
for i, (name, at) in enumerate(STAGES):
    end = STAGES[i + 1][1] if i + 1 < len(STAGES) else 4.9
    ks = []
    if at > 0:
        ks += [(0, 0), (at, 1)]
    else:
        ks += [(0, 1)]
    ks += [(end, 0)]
    tracks.append({"target": f"lbl{i}", "keys": {"opacity": steps(ks)}})

# blue accent lives only through team_work -> perfecting merge
tracks.append({"target": "blue", "keys": {
    "opacity": steps([(0, 0), (1.93, 1), (3.0, 1), (3.12, 0)])}})
# old-mark slats dissolve as the first morph begins
tracks.append({"target": "slats2", "keys": {
    "opacity": steps([(0, 1), (0.83, 1), (1.05, 0)])}})
# selection chrome deselects after the new mark lands
for i in range(4):
    tracks.append({"target": f"h{i}", "keys": {
        "opacity": steps([(4.7, 1), (4.95, 0)])}})
# the rebrand lockup: mark shrinks left, wordmark hammers in on the onsets
tracks.append({"target": "mark2", "keys": {
    "x": [{"t": 4.53, "v": 0}, {"t": 4.86, "v": -205, "ease": "inOutCubic"}],
    "scale": [{"t": 4.53, "v": 1}, {"t": 4.86, "v": 0.585, "ease": "inOutCubic"}],
}})
for i, (g, _, _) in enumerate(glyphs2):
    at = 4.53 + i * 0.09
    tracks.append({"target": g, "keys": {
        "opacity": steps([(0, 0), (at, 0), (at + 0.03, 1)]),
        "scale": [{"t": at, "v": 0.85}, {"t": at + 0.14, "v": 1.0,
                                          "ease": [0.22, 1, 0.36, 1]}],
    }})

stage = {
    "fps": 30,
    "size": [W, H],
    "scenes": [
        {"id": "s1", "bg": "#edece7", "dur": 1.667,
         "transition": {"kind": "cut"}, "nodes": sc1_nodes},
        {"id": "s2", "bg": "#f3f2ee", "dur": 7.1,
         "transition": {"kind": "cut"}, "nodes": sc2_nodes},
    ],
}

with open("docs/base-2.stage.json", "w") as f:
    json.dump(stage, f, indent=1)
with open("docs/base-2.anim.json", "w") as f:
    json.dump({"tracks": tracks}, f, indent=1)
print("wrote docs/base-2.{stage,anim}.json,",
      sum(len(s["nodes"]) for s in stage["scenes"]), "nodes,",
      len(tracks), "tracks")
