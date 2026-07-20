#!/usr/bin/env python3
# reproduction of animations/replit (76.24s, 998x720, 25fps) compressed to a
# ~40s arc. one continuous morphing board: giant "Run" + metaball pill
# sentence, task cards on connector lines, the 10x digit roll, the red blob
# that morphs into the replit mark (and back at the end), the prompt-card use
# cases with four named cursors, agent nodes, copies forking + merging, the
# human->agent tree, the red flood. persistent chapter scrubber + playhead on
# every scene. timings mapped from the frame ledger, durations compressed
# scene-by-scene.
import json
import math
import os

W, H = 998, 720
FPS = 25
K = 0.5523

RED = "#ed2c03"
RED_DEEP = "#dd3005"
INK = "#1a1a1a"
BLUE = "#3775e4"
BLUE_LT = "#a9c4f2"
TEAL = "#51ada2"
GREEN = "#4a9d4a"
GREY = "#8a8a86"
BORDER = "#e2dfd7"
STAGE_BG = "#f8f7f2"

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

tracks = []
scenes = []


def text(id, s, x, y, size, color, weight=500):
    return {"id": id, "type": "text", "text": s, "x": x, "y": y,
            "color": color, "font": {"size": size, "weight": weight}}


def rect(id, x, y, w, h, r, fill, **kw):
    n = {"id": id, "type": "rect", "x": x, "y": y, "w": w, "h": h,
         "radius": r, "fill": fill}
    n.update(kw)
    return n


def path(id, x, y, d, fill, stroke=None, **kw):
    n = {"id": id, "type": "path", "x": x, "y": y, "d": d, "fill": fill}
    if stroke:
        n["stroke"] = stroke
    n.update(kw)
    return n


def circle_d(cx, cy, r):
    k = r * K
    return (f"M{cx - r} {cy}"
            f"C{cx - r} {cy - k} {cx - k} {cy - r} {cx} {cy - r}"
            f"C{cx + k} {cy - r} {cx + r} {cy - k} {cx + r} {cy}"
            f"C{cx + r} {cy + k} {cx + k} {cy + r} {cx} {cy + r}"
            f"C{cx - k} {cy + r} {cx - r} {cy + k} {cx - r} {cy}Z")


def rrect_d(x0, y0, w, h, r):
    x1, y1 = x0 + w, y0 + h
    k = r * K
    return (f"M{x0 + r} {y0}L{x1 - r} {y0}"
            f"C{x1 - r + k} {y0} {x1} {y0 + r - k} {x1} {y0 + r}"
            f"L{x1} {y1 - r}"
            f"C{x1} {y1 - r + k} {x1 - r + k} {y1} {x1 - r} {y1}"
            f"L{x0 + r} {y1}"
            f"C{x0 + r - k} {y1} {x0} {y1 - r + k} {x0} {y1 - r}"
            f"L{x0} {y0 + r}"
            f"C{x0} {y0 + r - k} {x0 + r - k} {y0} {x0 + r} {y0}Z")


def hook_d(q):
    """the mark's bar+block lobe: top bar running left, block descending
    right. local units ~130 wide, scaled by q."""
    pts = ("M-45 -65 L45 -65 C58 -65 65 -58 65 -45 L65 26 C65 39 58 46 45 46 "
           "L28 46 C15 46 8 39 8 26 L8 10 C8 3 3 -2 -4 -2 L-45 -2 "
           "C-58 -2 -65 -9 -65 -22 L-65 -45 C-65 -58 -58 -65 -45 -65 Z")
    out = []
    for tok in pts.split():
        if tok == "Z":
            out.append("Z")
        elif tok[0] in "MLC":
            out.append(tok[0] + f"{float(tok[1:]) * q:.1f}")
        else:
            out.append(f"{float(tok) * q:.1f}")
    return " ".join(out)


# disc lobe offset from hook center, in hook units
DISC_DX, DISC_DY, DISC_R = -13.0, 74.0, 30.0


def mark_d(q):
    """the full mark as one static path: hook + disc lobes."""
    return hook_d(q) + circle_d(DISC_DX * q, DISC_DY * q, DISC_R * q)


def molecule(idp, x, y, s=1.0):
    """the blue agent icon: dark + light dot cluster."""
    dark = [(-6, -6), (6, -6), (0, 1), (6, 7)]
    light = [(0, -6), (-6, 1), (-6, 7), (6, 1)]
    d1 = "".join(circle_d(dx * s, dy * s, 2.7 * s) for dx, dy in dark)
    d2 = "".join(circle_d(dx * s, dy * s, 2.2 * s) for dx, dy in light)
    return [path(idp + "d", x, y, d1, BLUE), path(idp + "l", x, y, d2, BLUE_LT)]


def person_d(s=1.0):
    return (circle_d(0, -5 * s, 4.2 * s) +
            f"M{-8 * s} {9 * s}C{-8 * s} {0.5 * s} {8 * s} {0.5 * s} "
            f"{8 * s} {9 * s}Z")


def track(nid, at=None, **props):
    keys = {}
    for name, seq in props.items():
        out = []
        for k in seq:
            kk = {"t": k[0], "v": k[1]}
            if len(k) > 2:
                kk["ease"] = k[2]
            out.append(kk)
        keys[name] = out
    t = {"target": nid, "keys": keys}
    if at is not None:
        t["at"] = at
    tracks.append(t)


def steps(pairs):
    ks = []
    for tt, v in pairs:
        if ks:
            ks.append({"t": round(tt - 0.001, 3), "v": ks[-1]["v"]})
        ks.append({"t": round(tt, 3), "v": v})
    return ks


def ostep(nid, pairs):
    tracks.append({"target": nid, "keys": {"opacity": steps(pairs)}})


def exit_fade(nids, t0, t1):
    """append a fade-out into each node's existing opacity track (one track
    per node per prop), or make one if the node has none."""
    for nid in nids:
        host = None
        for t in tracks:
            if t["target"] == nid and "opacity" in t.get("keys", {}) \
                    and "at" not in t:
                host = t
        if host:
            ks = host["keys"]["opacity"]
            last = ks[-1]["v"]
            ks += [{"t": round(t0, 3), "v": last}, {"t": round(t1, 3), "v": 0}]
        else:
            ostep(nid, [(0, 1), (t0, 1), (t1, 0)])


# ------------------------------------------------------------ chrome
# scrubber boxes, playhead, waveform, halftone dots. present every scene.
BOXES = [(71, 110, None), (184, 167, "Use case 1"), (354, 105, "Use case 2"),
         (462, 329, "Use case 3"), (795, 126, "Outro")]
PH_X0, PH_X1 = 72, 918


def waveform_d():
    parts = []
    for x in range(72, 921, 9):
        h = 5 + (x * 13) % 15
        parts.append(f"M{x} {693 - h}L{x + 3.2} {693 - h}"
                     f"L{x + 3.2} 693L{x} 693Z")
    return "".join(parts)


WAVE_D = waveform_d()
SCRUB_D = "".join(rrect_d(x0, 596, w, 55, 8) for x0, w, _ in BOXES)
TOTAL = 39.8


def chrome(si, g0, dur):
    s = f"_c{si}"
    ns = [
        path("scrub" + s, 0, 0, SCRUB_D, "#c9c7c0", stroke=1.3),
        text("lbl_do1" + s, "Dream", 126, 617, 13, "#26241f"),
        text("lbl_do2" + s, "outcome", 126, 633, 13, "#26241f"),
        path("wave" + s, 0, 0, WAVE_D, "#dfdcd4"),
    ]
    for i, (x0, w, lab) in enumerate(BOXES):
        if lab:
            ns.append(text(f"lbl{i}" + s, lab, x0 + w / 2, 624, 14, "#26241f"))
    px0 = PH_X0 + (PH_X1 - PH_X0) * g0 / TOTAL
    px1 = PH_X0 + (PH_X1 - PH_X0) * (g0 + dur) / TOTAL
    ns.append(path("ph" + s, round(px0, 1), 583, "M-7 -4L7 -4L0 8Z", "#111111"))
    ns.append(rect("phline" + s, round(px0, 1), 623, 1.5, 57, 1, "#555550"))
    for nid in ("ph" + s, "phline" + s):
        track(nid, x=[(0, 0), (dur, round(px1 - px0, 1))])
    return ns


def stage_rect(si):
    return rect(f"stage_{si}", 499, 307, 906, 510, 0, STAGE_BG)


def scene(si, dur, transition, nodes, g0):
    scenes.append({"id": f"s{si}", "bg": "#ffffff", "dur": dur,
                   "transition": transition,
                   "nodes": [stage_rect(si)] + nodes + chrome(si, g0, dur)})


def border(id, x, y, w, h, r, color=BORDER, stroke=1.2):
    return path(id, x, y, rrect_d(-w / 2, -h / 2, w, h, r), color,
                stroke=stroke)


def postinify(prefix, cx, cy, s):
    """drawn stand-in for the Postinify hero card. w 400*s, h 260*s."""
    p = prefix
    ns = [
        rect(p + "card", cx, cy, 400 * s, 260 * s, 14 * s, "#ffffff"),
        border(p + "cardb", cx, cy, 400 * s, 260 * s, 14 * s),
        path(p + "logo", cx - 172 * s, cy - 105 * s, circle_d(0, 0, 6 * s), TEAL),
        text(p + "brand", "Postinify", cx - 128 * s, cy - 105 * s, 13 * s, INK, 650),
        rect(p + "cta2", cx + 148 * s, cy - 105 * s, 78 * s, 24 * s, 12 * s, "#1f1f1c"),
        text(p + "cta2t", "Get Started", cx + 148 * s, cy - 105 * s, 9 * s,
             "#ffffff", 600),
        text(p + "h1", "Schedule once.", cx - 108 * s, cy - 58 * s, 21 * s, INK, 700),
        text(p + "h2", "Post everywhere", cx - 102 * s, cy - 32 * s, 21 * s, TEAL, 700),
        text(p + "h3", "automatically.", cx - 112 * s, cy - 6 * s, 21 * s, INK, 700),
        rect(p + "l1", cx - 105 * s, cy + 22 * s, 155 * s, 5 * s, 2, "#d8d5cc"),
        rect(p + "l2", cx - 112 * s, cy + 34 * s, 140 * s, 5 * s, 2, "#d8d5cc"),
        rect(p + "btn", cx - 130 * s, cy + 66 * s, 112 * s, 30 * s, 15 * s, TEAL),
        text(p + "btnt", "Start free trial", cx - 130 * s, cy + 66 * s, 10.5 * s,
             "#ffffff", 600),
        rect(p + "im1", cx + 92 * s, cy - 42 * s, 80 * s, 66 * s, 8 * s, "#cfe6e1"),
        rect(p + "im2", cx + 166 * s, cy - 42 * s, 52 * s, 66 * s, 8 * s, TEAL),
        text(p + "im2t", "+248%", cx + 166 * s, cy - 42 * s, 10 * s, "#ffffff", 700),
        rect(p + "im3", cx + 92 * s, cy + 36 * s, 80 * s, 70 * s, 8 * s, "#e7f0ee"),
        rect(p + "im4", cx + 166 * s, cy + 36 * s, 52 * s, 70 * s, 8 * s, "#9fcdc5"),
    ]
    av = ["#c9a29a", "#9ab4c9", "#b9a9c9", "#a9c99a"]
    for i, col in enumerate(av):
        ns.append(path(f"{p}av{i}", cx - 160 * s + i * 20 * s, cy + 104 * s,
                       circle_d(0, 0, 8 * s), col))
    return ns


def cursor_chip(idp, x, y, color, name, chip_dx, chip_dy, big=False):
    cw = len(name) * (10 if big else 7.5) + (50 if big else 30)
    ch = 40 if big else 30
    fs = 18 if big else 14
    return [
        {"id": idp + "cur", "type": "cursor", "x": x, "y": y, "w": 20,
         "fill": color},
        rect(idp + "chipf", x + chip_dx, y + chip_dy, cw, ch, ch / 2, "#ffffff"),
        border(idp + "chipb", x + chip_dx, y + chip_dy, cw, ch, ch / 2),
        text(idp + "chipt", name, x + chip_dx, y + chip_dy, fs, color, 600),
    ]


g0 = 0.0

# ---------------------------------------------------------------- s1 title
d1 = 1.0
ns = [
    path("t_mark", 229, 305, mark_d(0.36), RED),
    text("t_word", "Replit Parallel Agents", 526, 305, 50, INK, 650),
]
track("t_mark", y=[(0, 0), (d1, -2)])
track("t_word", y=[(0, 0), (d1, -2)])
scene(1, d1, {"kind": "cut"}, ns, g0)
g0 += d1

# ---------------------------------------------------------------- s2 run
d2 = 3.0
ns = [
    text("run2", "Run", 235, 307, 84, INK, 700),
    rect("pill1", 415, 307, 195, 72, 36, RED, goo="pillgoo"),
    text("pill1t", "multiple", 415, 307, 40, "#ffffff", 600),
    rect("pill2", 600, 307, 158, 72, 36, RED, goo="pillgoo"),
    text("pill2t", "agents", 600, 307, 40, "#ffffff", 600),
    text("inpar", "in parallel", 800, 307, 40, INK, 600),
]
tracks.append({"target": "run2", "reveal": {
    "unit": "word", "stagger": 0, "dur": 0.15, "rise": 0, "accent": RED,
    "color_delay": 0.3, "color_dur": 0.5}})
track("run2", x=[(0, 0), (d2, -39)])
for nid in ("pill1", "pill1t"):
    track(nid, x=[(0.5, 420), (0.85, 0, "outCubic"), (d2, -28)])
    ostep(nid, [(0, 0), (0.5, 1)])
for nid in ("pill2", "pill2t"):
    track(nid, scale=[(1.2, 0.15), (1.6, 1.0, "outCubic")],
          x=[(1.6, 0), (d2, -18)])
    ostep(nid, [(0, 0), (1.2, 1)])
tracks.append({"target": "inpar", "at": 1.9, "reveal": {
    "unit": "word", "stagger": 0.09, "dur": 0.2, "rise": 22, "accent": INK}})
ostep("inpar", [(0, 0), (1.9, 1)])
track("inpar", x=[(1.9, 0), (d2, -14)])
scene(2, d2, {"kind": "cut"}, ns, g0)
g0 += d2

# ---------------------------------------------------------------- s3 tasks
d3 = 2.8
CARDS3 = [("Adding checkout", 310, 140), ("Building a new blog section", 590, 205),
          ("Creating finance dashboard", 700, 395), ("Adding user profile", 300, 470)]
ns = [text("h3", "on different tasks", 499, 307, 52, INK, 650)]
tracks.append({"target": "h3", "at": 0.3, "reveal": {
    "unit": "word", "stagger": 0.12, "dur": 0.24, "rise": 26, "accent": RED,
    "color_delay": 0.2, "color_dur": 0.4}})
ostep("h3", [(0, 0), (0.3, 1)])
for i, (label, cx, cy) in enumerate(CARDS3):
    cw = len(label) * 8.5 + 62
    t0 = 0.5 + i * 0.25
    lf = cx - cw / 2 - 46 + 6
    ns.append(rect(f"c3line{i}", round(46 + lf / 2, 1), cy, lf, 2.5, 1, BLUE))
    track(f"c3line{i}",
          w=[(t0, 8), (t0 + 0.5, lf, "outCubic")],
          x=[(t0, -(lf - 8) / 2), (t0 + 0.5, 0, "outCubic")])
    ostep(f"c3line{i}", [(0, 0), (t0, 1)])
    ns.append(rect(f"c3card{i}", cx, cy, cw, 44, 10, "#ffffff"))
    ns += molecule(f"c3mol{i}", cx - cw / 2 + 24, cy, 0.9)
    ns.append(text(f"c3t{i}", label, cx + 12, cy, 17, INK, 550))
    for nid in (f"c3card{i}", f"c3mol{i}d", f"c3mol{i}l", f"c3t{i}"):
        track(nid, x=[(t0 + 0.2, -60), (t0 + 0.65, 0, "outCubic")])
        ostep(nid, [(0, 0), (t0 + 0.2, 0), (t0 + 0.4, 1)])
scene(3, d3, {"kind": "fade", "dur": 0.3}, ns, g0)
g0 += d3

# ---------------------------------------------------------------- s4 10x
d4 = 2.2
ns = [
    text("t4and", "and build", 330, 307, 54, INK, 650),
    rect("t4glow", 502, 307, 88, 78, 12, "#ffc394", blur=16),
    text("t4x", "x faster", 655, 307, 54, RED, 650),
    text("t4ten", "10", 502, 307, 54, RED, 650),
]
for i, digits in enumerate(["47", "83", "26"]):
    ns.append(text(f"t4f{i}", digits, 502, 307, 54, RED, 650))
    t0 = 0.3 + i * 0.22
    track(f"t4f{i}", y=[(t0, 36), (t0 + 0.2, -36)])
    ostep(f"t4f{i}", [(0, 0), (t0, 0.75), (t0 + 0.2, 0.75), (t0 + 0.21, 0)])
tracks.append({"target": "t4and", "at": 0.1, "reveal": {
    "unit": "word", "stagger": 0.07, "dur": 0.2, "rise": 20, "accent": RED,
    "color_delay": 0.15, "color_dur": 0.3}})
ostep("t4and", [(0, 0), (0.1, 1), (1.9, 1), (2.15, 0)])
ostep("t4x", [(0, 0), (0.25, 0), (0.45, 1), (1.9, 1), (2.15, 0)])
track("t4x", y=[(0.25, 18), (0.55, 0, "outCubic")])
ostep("t4glow", [(0, 0), (0.3, 0.55), (1.0, 0.55), (1.25, 0)])
ostep("t4ten", [(0, 0), (0.96, 0), (1.02, 1), (1.9, 1), (2.15, 0)])
track("t4ten", y=[(0.96, 30), (1.25, 0, "outCubic")])
scene(4, d4, {"kind": "fade", "dur": 0.3}, ns, g0)
g0 += d4

# ---------------------------------------------------------------- s5 blob -> mark
d5 = 3.2
# giant goo pair: hook lobe grows out of the dropped blob, both shrink into
# the lockup, crossfade to the static mark while the wordmark reveals.
ns = [
    path("blobg", 515, 378, circle_d(0, 0, 78), RED, goo="brand"),
    path("hookg", 540, 240, hook_d(1.9), RED, goo="brand"),
    path("mark5", 253, 300, mark_d(0.36), RED),
    text("word5", "Replit Parallel Agents", 530, 303, 46, INK, 650),
]
track("blobg",
      x=[(0, -45), (1.0, -45), (1.55, 0, "inOutCubic"),
         (2.1, 0), (2.6, 248 - 515, "inOutCubic")],
      y=[(0, -660), (0.42, -78, "inCubic"), (0.56, -95, "outCubic"),
         (0.72, -88, "inOutCubic"), (1.0, -88), (1.55, 0, "inOutCubic"),
         (2.1, 0), (2.6, 327 - 378, "inOutCubic")],
      scale=[(1.0, 1.0), (1.55, 0.73, "inOutCubic"),
             (2.1, 0.73), (2.6, 0.138, "inOutCubic")])
ostep("blobg", [(0, 1), (2.6, 1), (2.72, 0)])
track("hookg",
      x=[(1.0, -70), (1.55, 0, "outCubic"), (2.1, 0), (2.6, 253 - 540, "inOutCubic")],
      y=[(1.0, 50), (1.55, 0, "outCubic"), (2.1, 0), (2.6, 300 - 240, "inOutCubic")],
      scale=[(1.0, 0.12), (1.55, 1.0, "outCubic"),
             (2.1, 1.0), (2.6, 0.19, "inOutCubic")])
ostep("hookg", [(0, 0), (1.0, 1), (2.6, 1), (2.72, 0)])
ostep("mark5", [(0, 0), (2.62, 0), (2.72, 1)])
tracks.append({"target": "word5", "at": 2.55, "reveal": {
    "unit": "word", "stagger": 0.09, "dur": 0.2, "rise": 18, "accent": RED,
    "color_delay": 0.18, "color_dur": 0.35, "keep": ["Agents"]}})
ostep("word5", [(0, 0), (2.55, 1)])
scene(5, d5, {"kind": "fade", "dur": 0.3}, ns, g0)
g0 += d5

# ---------------------------------------------------------------- s6 prompt UC1
d6 = 4.0
ns = [
    rect("rail", 120, 300, 96, 380, 18, "#ffffff"),
    border("railb", 120, 300, 96, 380, 18),
    text("railp", "+", 120, 190, 28, GREY),
]
ns += molecule("railm", 120, 252, 1.1)
ns += [
    rect("pcard", 470, 300, 520, 170, 16, "#ffffff"),
    border("pcardb", 470, 300, 520, 170, 16),
    text("ptyped", "Create about us page", 364, 258, 26, INK, 550),
    text("pplus", "+", 250, 352, 22, "#9a968e"),
    rect("wash", 620, 330, 300, 140, 18, RED, blur=26),
    rect("send", 700, 352, 42, 42, 12, BLUE),
    path("sendar", 700, 352, "M0 8L0 -8M-6 -2L0 -8L6 -2", "#ffffff", stroke=2.4),
    rect("appcard", 900, 300, 240, 400, 18, "#ffffff"),
    border("appcardb", 900, 300, 240, 400, 18),
    text("app_h1", "Post", 850, 138, 30, INK, 700),
    text("app_h2", "everywhere", 880, 172, 26, TEAL, 700),
    rect("app_l1", 862, 208, 130, 5, 2, "#dcd9d1"),
    rect("app_l2", 858, 222, 122, 5, 2, "#dcd9d1"),
    rect("app_l3", 866, 236, 118, 5, 2, "#dcd9d1"),
    rect("app_btn", 872, 282, 124, 36, 18, TEAL),
    text("app_btnt", "Start free trial", 872, 282, 12, "#ffffff", 600),
]
for i, col in enumerate(["#c9a29a", "#9ab4c9", "#b9a9c9", "#a9c99a", "#c9c29a"]):
    ns.append(path(f"app_av{i}", 828 + i * 22, 342, circle_d(0, 0, 10), col))
ns += cursor_chip("m6", 770, 505, BLUE, "Max", 52, 40)
tracks.append({"target": "ptyped", "at": 0.7, "reveal": {
    "unit": "type", "cadence": 0.055, "dur": 0.08, "caret": "bar",
    "caret_blink": 0.9}})
ostep("ptyped", [(0, 0), (0.7, 1)])
ostep("wash", [(0, 0), (2.8, 0), (3.1, 0.3), (3.6, 0)])
for nid in ("m6cur", "m6chipf", "m6chipb", "m6chipt"):
    track(nid, x=[(1.9, 0), (2.5, -56, "outCubic")],
          y=[(1.9, 0), (2.5, -121, "outCubic")])
    ostep(nid, [(0, 0), (0.4, 0), (0.6, 1)])
track("send", scale=[(2.85, 1), (2.95, 0.86, "inCubic"), (3.1, 1, "outCubic")])
appn = ["appcard", "appcardb", "app_h1", "app_h2", "app_l1", "app_l2",
        "app_l3", "app_btn", "app_btnt"] + [f"app_av{i}" for i in range(5)]
for j, nid in enumerate(appn):
    t0 = 1.7 + (j % 5) * 0.08
    ostep(nid, [(0, 0), (t0, 0), (t0 + 0.3, 1)])
scene(6, d6, {"kind": "fade", "dur": 0.35}, ns, g0)
g0 += d6

# ---------------------------------------------------------------- s7 teammate canvas
d7 = 4.0
QUAD = [
    ("Restyle landing page hero", "Paul", RED, 262, 175),
    ("Add login flow & auth", "Lisa", "#7e9d99", 737, 175),
    ("Add payments page", "Max", BLUE, 262, 440),
    ("Add ability to collaborate with colleagues", "Emma", GREEN, 737, 440),
]
ns = [
    rect("crossv", 499, 307, 1.5, 510, 1, "#ddd9d0"),
    rect("crossh", 499, 307, 906, 1.5, 1, "#ddd9d0"),
    rect("stack", 499, 307, 64, 170, 30, "#ffffff"),
    border("stackb", 499, 307, 64, 170, 30),
    text("stackp", "+", 499, 250, 22, "#7a766e"),
]
ns += molecule("stkm1", 499, 300, 1.0)
ns += molecule("stkm2", 499, 350, 1.0)
for nid in ("stack", "stackb", "stackp", "stkm1d", "stkm1l", "stkm2d", "stkm2l"):
    track(nid, scale=[(0.5, 0.6), (0.85, 1.0, "outCubic")])
    ostep(nid, [(0, 0), (0.5, 1)])
for i, (prompt, name, col, bx, by) in enumerate(QUAD):
    p = f"q{i}"
    tw = len(prompt) * 14 * 0.5
    right = bx > 499
    ns += [
        rect(p + "box", bx, by, 350, 110, 12, "#ffffff"),
        border(p + "boxb", bx, by, 350, 110, 12),
        text(p + "t", prompt, round(bx - 175 + 16 + tw / 2, 1), by - 32, 14, INK),
        text(p + "plus", "+", bx - 155, by + 35, 18, "#9a968e"),
        rect(p + "send", bx + 148, by + 35, 30, 30, 9, BLUE),
        path(p + "sendar", bx + 148, by + 35, "M0 6L0 -6M-4.5 -1.5L0 -6L4.5 -1.5",
             "#ffffff", stroke=1.8),
    ]
    cdx = -58 if right else 48
    ns += cursor_chip(p, bx + 168, by + 60, col, name, cdx, 22)
    t0 = 0.25 + i * 0.14
    grp = [p + s for s in ("box", "boxb", "plus", "send", "sendar",
                           "cur", "chipf", "chipb", "chipt")]
    for nid in grp:
        track(nid, y=[(t0, 14), (t0 + 0.35, 0, "outCubic")])
        ostep(nid, [(0, 0), (t0, 0), (t0 + 0.25, 1)])
    tracks.append({"target": p + "t", "at": 0.7 + i * 0.25, "reveal": {
        "unit": "type", "cadence": 0.045, "dur": 0.07, "caret": "bar",
        "caret_blink": 0.8}})
    ostep(p + "t", [(0, 0), (0.7 + i * 0.25, 1)])
    track(p + "cur", x=[(1.5 + i * 0.2, 0), (2.4 + i * 0.2, -12, "inOutCubic")],
          y=[(1.5 + i * 0.2, 0), (2.4 + i * 0.2, -16, "inOutCubic")])
scene(7, d7, {"kind": "fade", "dur": 0.35}, ns, g0)
g0 += d7

# ---------------------------------------------------------------- s8 agent A-D
d8 = 2.4
ns = [
    rect("col8", 499, 300, 92, 420, 20, "#ffffff"),
    border("col8b", 499, 300, 92, 420, 20),
]
CELLY = [145, 240, 335, 430]
LABELS8 = [("Agent A", 720, 145), ("Agent B", 300, 240),
           ("Agent C", 712, 335), ("Agent D", 298, 430)]
for i, cy in enumerate(CELLY):
    ns.append(border(f"cell{i}", 499, cy, 62, 62, 12, "#e8e5dd", 1.2))
    ns += molecule(f"cm8{i}", 499, cy, 1.5)


def dash_d(x0, x1, step=10, ln=5):
    parts = []
    x = min(x0, x1)
    end = max(x0, x1)
    while x < end:
        parts.append(f"M{x} 0L{min(x + ln, end)} 0")
        x += step
    return "".join(parts)


for i, (lab, lx, ly) in enumerate(LABELS8):
    right = lx > 499
    x_cell = 499 + (34 if right else -34)
    x_lab = lx - 76 if right else lx + 76
    ns.append(path(f"dash8{i}", min(x_cell, x_lab), ly,
                   dash_d(0, abs(x_lab - x_cell)), BLUE, stroke=1.6))
    ns.append(path(f"dot8{i}", 0, ly,
                   circle_d(x_cell, 0, 2.8) + circle_d(x_lab, 0, 2.8), BLUE))
    ns += [
        rect(f"lab8{i}", lx, ly, 150, 54, 12, "#ffffff"),
        border(f"lab8{i}b", lx, ly, 150, 54, 12),
        text(f"lab8{i}t", lab, lx, ly, 21, INK, 600),
    ]
    t0 = 0.5 + i * 0.22
    dx0 = -18 if right else 18
    for nid in (f"lab8{i}", f"lab8{i}b", f"lab8{i}t"):
        track(nid, x=[(t0, dx0), (t0 + 0.3, 0, "outCubic")])
        ostep(nid, [(0, 0), (t0, 0), (t0 + 0.22, 1)])
    for nid in (f"dash8{i}", f"dot8{i}"):
        ostep(nid, [(0, 0), (t0 + 0.1, 0), (t0 + 0.35, 1)])
scene(8, d8, {"kind": "fade", "dur": 0.3}, ns, g0)
g0 += d8

# ---------------------------------------------------------------- s9 main app + copies
d9 = 3.0
ns = postinify("m9", 300, 300, 1.0)
ns += [
    rect("chip9", 170, 148, 108, 34, 8, "#eceae3"),
    text("chip9t", "Main App", 170, 148, 16, INK, 600),
]
for j, n in enumerate(postinify("", 0, 0, 1.0)):
    pass
m9ids = [n["id"] for n in ns if n["id"].startswith("m9")]
track("m9card", blur=[(0, 14), (0.7, 0, "outCubic")])
for j, nid in enumerate(m9ids):
    ostep(nid, [(0, 0), (0.1 + (j % 6) * 0.05, 0), (0.45 + (j % 6) * 0.05, 1)])
ostep("chip9", [(0, 0), (0.5, 0), (0.7, 1)])
ostep("chip9t", [(0, 0), (0.5, 0), (0.7, 1)])
for i in range(4):
    cy = 150 + i * 100
    t0 = 0.9 + i * 0.18
    lf = 212
    ns.append(rect(f"c9line{i}", 510 + lf / 2, cy, lf, 2, 1, "#9db7e8"))
    track(f"c9line{i}", w=[(t0, 6), (t0 + 0.4, lf, "outCubic")],
          x=[(t0, -(lf - 6) / 2), (t0 + 0.4, 0, "outCubic")])
    ostep(f"c9line{i}", [(0, 0), (t0, 1)])
    ns += [
        rect(f"copy{i}", 790, cy, 130, 50, 12, "#ffffff"),
        border(f"copy{i}b", 790, cy, 130, 50, 12),
        text(f"copy{i}t", f"Copy {i + 1}", 790, cy, 18, INK, 600),
    ]
    for nid in (f"copy{i}", f"copy{i}b", f"copy{i}t"):
        track(nid, scale=[(t0 + 0.3, 0.85), (t0 + 0.55, 1.0, "outCubic")])
        ostep(nid, [(0, 0), (t0 + 0.3, 0), (t0 + 0.45, 1)])
scene(9, d9, {"kind": "fade", "dur": 0.35}, ns, g0)
g0 += d9

# ---------------------------------------------------------------- s10 independent
d10 = 2.4
ns = [
    text("h10a", "then agents work", 610, 290, 42, INK, 650),
    text("h10b", "independently", 610, 338, 42, RED, 650),
]
tracks.append({"target": "h10a", "at": 0.5, "reveal": {
    "unit": "word", "stagger": 0.09, "dur": 0.2, "rise": 20, "accent": RED,
    "color_delay": 0.15, "color_dur": 0.3}})
ostep("h10a", [(0, 0), (0.5, 1)])
ostep("h10b", [(0, 0), (0.75, 0), (0.95, 1)])
track("h10b", y=[(0.75, 16), (1.05, 0, "outCubic")])
LINES10 = [(150, 560), (255, 470), (360, 440), (465, 410)]
for i, (ly, xend) in enumerate(LINES10):
    lf = xend - 46
    t0 = 0.2 + i * 0.12
    ns.append(rect(f"l10_{i}", 46 + lf / 2, ly, lf, 2, 1, "#3a3833"))
    track(f"l10_{i}", w=[(t0, 10), (t0 + 0.7, lf, "outCubic")],
          x=[(t0, -(lf - 10) / 2), (t0 + 0.7, 0, "outCubic")])
    ostep(f"l10_{i}", [(0, 0), (t0, 1)])
    ns.append(path(f"d10_{i}", xend, ly, circle_d(0, 0, 5.5), BLUE))
    track(f"d10_{i}", x=[(t0, -(lf - 30)), (t0 + 1.5, 0, "outCubic")])
    ostep(f"d10_{i}", [(0, 0), (t0 + 0.15, 0), (t0 + 0.3, 1)])
scene(10, d10, {"kind": "fade", "dur": 0.3}, ns, g0)
g0 += d10

# ---------------------------------------------------------------- s11 merged
d11 = 2.2
ns = [
    text("h11a", "and their work gets", 499, 140, 38, INK, 650),
    text("h11b", "merged together", 499, 188, 38, RED, 650),
]
tracks.append({"target": "h11a", "at": 0.15, "reveal": {
    "unit": "word", "stagger": 0.08, "dur": 0.2, "rise": 18, "accent": RED,
    "color_delay": 0.15, "color_dur": 0.3}})
ostep("h11a", [(0, 0), (0.15, 1)])
ostep("h11b", [(0, 0), (0.4, 0), (0.6, 1)])
track("h11b", y=[(0.4, 14), (0.7, 0, "outCubic")])
ns += postinify("m11", 499, 395, 0.85)
m11ids = [n["id"] for n in ns if n["id"].startswith("m11")]
track("m11card", blur=[(0, 16), (0.6, 16), (1.2, 0, "outCubic")])
for j, nid in enumerate(m11ids):
    ostep(nid, [(0, 0), (0.55 + (j % 6) * 0.05, 0), (0.95 + (j % 6) * 0.05, 1)])
ns += [
    rect("chip11", 300, 285, 90, 30, 15, BLUE),
    text("chip11t", "Merged", 300, 285, 14, "#ffffff", 600),
]
for nid in ("chip11", "chip11t"):
    track(nid, scale=[(1.35, 0.7), (1.6, 1.0, "outCubic")])
    ostep(nid, [(0, 0), (1.35, 0), (1.5, 1)])
scene(11, d11, {"kind": "dissolve", "dur": 0.4}, ns, g0)
g0 += d11

# ---------------------------------------------------------------- s12 outro tree
d12 = 3.6
NODEX = [340, 447, 552, 658]
rings = "".join(circle_d(0, 0, r) for r in (105, 160, 215))
branches = "".join(
    f"M0 0C{(x - 499) * 0.2:.0f} 40 {(x - 499) * 0.75:.0f} 60 {x - 499} 112"
    for x in NODEX)
ns = [
    path("rings12", 499, 225, rings, "#d8d4ca", stroke=1.0),
    path("branch12", 499, 283, branches, "#8a867e", stroke=1.4),
    rect("circ12", 499, 225, 110, 110, 55, "#ffffff"),
    path("circ12b", 499, 225, circle_d(0, 0, 55), INK, stroke=1.6),
    path("chev12", 499, 225, "M-8 -9L-17 0L-8 9M8 -9L17 0L8 9", INK, stroke=3.0),
    path("mark12", 499, 222, mark_d(0.5), RED),
    text("h12a", "Human Developers work.", 499, 505, 40, INK, 650),
    text("h12b", "Now agents do the same.", 499, 505, 40, INK, 650),
]
ostep("rings12", [(0, 0), (0.3, 0), (0.7, 0.5)])
track("rings12", scale=[(0, 1), (d12, 1.08)])
ostep("branch12", [(0, 0), (0.6, 0), (0.95, 1)])
for nid in ("circ12", "circ12b", "chev12"):
    ostep(nid, [(0, 0), (0.15, 0), (0.4, 1), (2.1, 1), (2.35, 0)])
ostep("mark12", [(0, 0), (2.2, 0), (2.45, 1)])
for i, x in enumerate(NODEX):
    ns += [
        rect(f"dev{i}", x, 400, 52, 52, 26, "#ffffff"),
        path(f"dev{i}b", x, 400, circle_d(0, 0, 26), "#55504a", stroke=1.3),
        path(f"dev{i}p", x, 400, person_d(1.6), INK),
    ]
    ns += molecule(f"am12{i}", x, 400, 1.3)
    for nid in (f"dev{i}", f"dev{i}b"):
        ostep(nid, [(0, 0), (0.8 + i * 0.12, 0), (1.05 + i * 0.12, 1)])
    ostep(f"dev{i}p", [(0, 0), (0.8 + i * 0.12, 0), (1.05 + i * 0.12, 1),
                       (2.1, 1), (2.35, 0)])
    for nid in (f"am12{i}d", f"am12{i}l"):
        ostep(nid, [(0, 0), (2.2, 0), (2.45, 1)])
tracks.append({"target": "h12a", "at": 1.0, "reveal": {
    "unit": "word", "stagger": 0.1, "dur": 0.22, "rise": 20, "accent": RED,
    "color_delay": 0.2, "color_dur": 0.35, "keep": ["Human", "Developers"]}})
ostep("h12a", [(0, 0), (1.0, 1), (2.05, 1), (2.25, 0)])
tracks.append({"target": "h12b", "at": 2.35, "reveal": {
    "unit": "word", "stagger": 0.08, "dur": 0.2, "rise": 16, "accent": RED,
    "color_delay": 0.2, "color_dur": 0.35, "keep": ["Now"]}})
ostep("h12b", [(0, 0), (2.35, 1)])
scene(12, d12, {"kind": "fade", "dur": 0.4}, ns, g0)
g0 += d12

# ---------------------------------------------------------------- s13 red flood
d13 = 2.8
rt = "".join(rrect_d(-w / 2, -h / 2, w, h, r)
             for w, h, r in ((660, 300, 150), (820, 430, 215)))
ns = [
    rect("flood", 499, 307, 906, 510, 30, RED),
    path("rt13", 499, 300, rt, "#ffffff", stroke=1.5),
    rect("pill13", 499, 300, 520, 180, 92, STAGE_BG),
    text("t13a", "Build More", 499, 300, 52, INK, 700),
    text("t13b", "Move Faster", 499, 300, 52, INK, 700),
]
track("flood",
      w=[(0, 70), (0.32, 906, "outCubic"), (2.5, 906), (2.8, 104, "inCubic")],
      h=[(0, 70), (0.32, 510, "outCubic"), (2.5, 510), (2.8, 104, "inCubic")])
ostep("rt13", [(0, 0), (0.6, 0), (0.9, 0.22), (2.4, 0.22), (2.55, 0)])
track("pill13",
      w=[(0.45, 50), (0.85, 520, "outCubic"), (2.3, 520), (2.62, 36, "inCubic")],
      h=[(0.45, 50), (0.85, 180, "outCubic"), (2.3, 180), (2.62, 36, "inCubic")])
ostep("pill13", [(0, 0), (0.45, 1), (2.6, 1), (2.66, 0)])
tracks.append({"target": "t13a", "at": 1.0, "reveal": {
    "unit": "word", "stagger": 0.08, "dur": 0.2, "rise": 14, "accent": "#8a8a86",
    "color_delay": 0.12, "color_dur": 0.25}})
ostep("t13a", [(0, 0), (1.0, 1), (1.6, 1), (1.75, 0)])
ostep("t13b", [(0, 0), (1.8, 0), (1.95, 1), (2.3, 1), (2.45, 0)])
track("t13b", y=[(1.8, 12), (2.05, 0, "outCubic")])
scene(13, d13, {"kind": "fade", "dur": 0.3}, ns, g0)
g0 += d13

# ---------------------------------------------------------------- s14 end lockup
d14 = 3.2
ns = [
    path("blob14", 505, 334, circle_d(0, 0, 52), RED, goo="end"),
    path("hook14", 515, 275, hook_d(0.8), RED, goo="end"),
    path("mark14", 515, 278, mark_d(0.8), RED),
    text("t14a", "With parallel agents on", 410, 295, 36, INK, 600),
    text("t14b", "Replit", 741, 293, 36, INK, 650),
]
# dot -> mark: blob wobbles then splits into the goo pair, static mark takes
# over, shrinks right into the wordline slot, wordline builds, qualifier
# fades and the lockup re-centers.
track("blob14",
      x=[(0, -6), (0.5, -6), (1.0, 0, "inOutCubic")],
      y=[(0, -34), (0.5, -34), (1.0, 0, "inOutCubic")],
      scale=[(0, 1.0), (0.25, 1.06, "inOutCubic"), (0.5, 1.0, "inOutCubic"),
             (1.0, 0.46, "inOutCubic")])
ostep("blob14", [(0, 1), (1.05, 1), (1.15, 0)])
track("hook14",
      scale=[(0.5, 0.1), (1.0, 1.0, "outCubic")],
      x=[(0.5, -16), (1.0, 0, "outCubic")],
      y=[(0.5, 40), (1.0, 0, "outCubic")])
ostep("hook14", [(0, 0), (0.5, 1), (1.05, 1), (1.15, 0)])
track("mark14",
      scale=[(1.5, 1.0), (1.9, 0.45, "inOutCubic")],
      x=[(1.5, 0), (1.9, 140, "inOutCubic"), (2.8, 140), (3.1, -76, "inOutCubic")],
      y=[(1.5, 0), (1.9, 14, "inOutCubic")])
ostep("mark14", [(0, 0), (1.06, 0), (1.12, 1)])
tracks.append({"target": "t14a", "at": 1.9, "reveal": {
    "unit": "word", "stagger": 0.08, "dur": 0.2, "rise": 16, "accent": RED,
    "color_delay": 0.2, "color_dur": 0.35, "keep": ["parallel", "agents"]}})
ostep("t14a", [(0, 0), (1.9, 1), (2.75, 1), (2.95, 0)])
tracks.append({"target": "t14b", "at": 2.15, "reveal": {
    "unit": "word", "stagger": 0.08, "dur": 0.2, "rise": 16, "accent": RED,
    "color_delay": 0.18, "color_dur": 0.3}})
ostep("t14b", [(0, 0), (2.15, 1)])
track("t14b", x=[(2.8, 0), (3.1, -216, "inOutCubic")])
scene(14, d14, {"kind": "cut"}, ns, g0)
g0 += d14

stage = {"fps": FPS, "size": [W, H], "scenes": scenes}

with open("docs/replit.stage.json", "w") as f:
    json.dump(stage, f, indent=1)
with open("docs/replit.anim.json", "w") as f:
    json.dump({"tracks": tracks}, f, indent=1)
print("wrote docs/replit.{stage,anim}.json,",
      sum(len(s["nodes"]) for s in scenes), "nodes,", len(tracks), "tracks,",
      f"{g0:.1f}s")
