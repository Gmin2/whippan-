#!/usr/bin/env python3
# launch film for solder (the prompt-to-hardware product). screens mirror
# the real app at localhost:5260 -- playfair wordmark on rgb(45,82,240),
# blueprint background, the one input bar -- and the diagram scene is the
# actual quadcopter svg pulled from the vector-hardware harness
# (tmp/claude/solder/quad-svg.json), every path verbatim.
# overlay contract as usual: scene-local `at`, unique ids per scene, one
# track per node per property, x/y keys are offsets.
import json
import os
import re

W, H = 1920, 1080
BLUE = "#2d52f0"
BG = "#f7f8fd"
INK = "#1d1d1d"
GREY = "#6b7280"
MONO_W = 0.6

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SVG = json.load(open("../tmp/claude/solder/quad-svg.json"))


def text(id, s, x, y, size, color=INK, weight=400, family="inter"):
    return {"id": id, "type": "text", "text": s, "x": x, "y": y,
            "color": color, "font": {"size": size, "weight": weight,
                                     "family": family}}


def rect(id, x, y, w, h, r, fill, **kw):
    n = {"id": id, "type": "rect", "x": x, "y": y, "w": w, "h": h,
         "radius": r, "fill": fill}
    n.update(kw)
    return n


def keyed(nid, **props):
    keys = {}
    for name, seq in props.items():
        out = []
        for k in seq:
            kk = {"t": k[0], "v": k[1]}
            if len(k) > 2:
                kk["ease"] = k[2]
            out.append(kk)
        keys[name] = out
    return {"target": nid, "keys": keys}


def rgb_hex(s):
    m = re.match(r"rgb\((\d+), (\d+), (\d+)\)", s)
    return "#{:02x}{:02x}{:02x}".format(*map(int, m.groups())) if m else s


def hatch(x0, y0, w, h, step=46):
    parts = []
    d = int(w + h)
    for i in range(0, d, step):
        ax = x0 + i
        parts.append(f"M{min(ax, x0 + w)} {y0 + max(0, i - w)}"
                     f"L{x0 + max(0, i - h)} {min(y0 + i, y0 + h)}")
    return "".join(parts)


def rise(nid, at, dy=36, dur=0.34):
    return keyed(nid, opacity=[(at, 0), (at + dur * 0.8, 1)],
                 y=[(at, dy), (at + dur, 0, "outCubic")])


tracks = []


def homepage(sfx, tile_rows=True):
    """the real landing screen: hatched panel, tile wall, serif wordmark,
    three chips, tagline, the input bar with its blue send button."""
    ns = [rect(f"{sfx}panel", 960, 470, 1660, 760, 6, "#fbfcff"),
          {"id": f"{sfx}hatch", "type": "path", "x": 130, "y": 90,
           "stroke": 1.2, "fill": "#dfe6fb", "d": hatch(0, 0, 1660, 760)}]
    if tile_rows:
        i = 0
        for row, (y, count, xpad) in enumerate([(180, 15, 0), (248, 15, 0),
                                                (316, 5, 0), (316, 5, 1130)]):
            for c in range(count):
                ns.append(rect(f"{sfx}t{i}", 235 + xpad + c * 68, y, 56, 56,
                               10, "#ffffff"))
                i += 1
    ns += [
        text(f"{sfx}wm", "Solder", 960, 400, 210, BLUE, 600, "playfair"),
        rect(f"{sfx}c1", 700, 545, 200, 40, 20, "#ffffff"),
        text(f"{sfx}c1t", "real vetted parts", 700, 545, 21, INK, 500),
        rect(f"{sfx}c2", 950, 545, 230, 40, 20, "#ffffff"),
        text(f"{sfx}c2t", "wiring that checks out", 950, 545, 21, INK, 500),
        rect(f"{sfx}c3", 1210, 545, 220, 40, 20, "#ffffff"),
        text(f"{sfx}c3t", "animated diagrams", 1210, 545, 21, INK, 500),
        text(f"{sfx}tag1", "The AI that turns a prompt into buildable hardware.",
             960, 625, 26, "#3c4250"),
        text(f"{sfx}tag2", "Real parts, wiring checked against physics, a diagram that draws itself.",
             960, 660, 26, "#3c4250"),
        rect(f"{sfx}bar", 940, 745, 800, 82, 18, "#ffffff"),
        text(f"{sfx}ph", "what hardware you want to prototype",
             770, 746, 24, "#9aa1af"),
        rect(f"{sfx}send", 1296, 745, 60, 60, 14, "#4255e8"),
        {"id": f"{sfx}sendic", "type": "path", "x": 1284, "y": 733,
         "fill": "#ffffff",
         "d": "M2 12L22 3L15 22L11 14Z M11 14L22 3"},
        text(f"{sfx}nav1", "Community", 1600, 60, 24, GREY),
        rect(f"{sfx}nav2", 1750, 60, 110, 44, 22, "#111111"),
        text(f"{sfx}nav2t", "Sign in", 1750, 60, 22, "#ffffff", 500),
    ]
    return ns


# ---------------------------------------------------- scene 1: the problem
sc1_nodes = [
    {"id": "p_hatch", "type": "path", "x": 0, "y": 0, "stroke": 1.2,
     "fill": "#e6ebfb", "d": hatch(0, 0, 1920, 1080, 64)},
    text("p1", "You know what you want to build.", 960, 450, 88, INK, 600,
         "playfair"),
    text("p2", "The wiring is where it dies.", 960, 570, 88, BLUE, 600,
         "playfair"),
    text("p3", "Datasheets. Pinouts. A 5V pin on a 3.3V net.",
         960, 690, 30, GREY),
]
tracks += [rise("p1", 0.25, 40), rise("p2", 0.65, 40), rise("p3", 1.15, 26)]

# --------------------------------------------------- scene 2: the homepage
# the actual page, screenshotted from localhost:5260 at 2x. it arrives
# like real footage: fade up with a slow settle from 103%.
sc2_nodes = [
    {"id": "hshot", "type": "image", "src": "/assets/solder/home.png",
     "x": 960, "y": 540, "w": 1920, "h": 1080},
]
tracks.append(keyed("hshot",
                    opacity=[(0.08, 0), (0.5, 1)],
                    scale=[(0.08, 1.035), (1.1, 1.0, "outCubic")]))

# ---------------------------------- scene 3: zoom into the bar, type, send
# same bitmap; the camera dives to the real input bar. a white cover hides
# the baked-in placeholder, the prompt types over it, and a crop of the
# real send button does the press.
PROMPT = "a palm sized quadcopter drone"
sc3_nodes = [
    {"id": "zshot", "type": "image", "src": "/assets/solder/home.png",
     "x": 960, "y": 540, "w": 1920, "h": 1080},
    rect("zcover", 936, 655, 452, 40, 8, "#ffffff", opacity=0),
    text("ztyped", PROMPT, 723 + len(PROMPT) * 16 * 0.5 * 0.5, 655, 16, INK),
    {"id": "zsend2", "type": "image", "src": "/assets/solder/send.png",
     "x": 1191, "y": 654, "w": 38, "h": 38},
]
tracks.append(keyed("zcover", opacity=[(0.62, 0), (0.78, 1)]))
tracks.append({"target": "ztyped", "at": 0.85, "reveal": {
    "unit": "type", "cadence": 0.052, "dur": 0.04,
    "caret": "bar", "caret_typing": "solid"}})
tracks.append({"target": "j3", "at": 0.12, "cam": {
    "preset": "crash-zoom", "z": 2.55, "anchor": [960, 655], "dur": 0.7}})
end_type = 0.85 + len(PROMPT) * 0.052
tracks.append(keyed("zsend2",
                    scale=[(end_type + 0.25, 1), (end_type + 0.33, 0.85,
                            "outCubic"), (end_type + 0.45, 1, "outCubic")]))
tracks.append({"target": "zsend2", "at": end_type + 0.28, "state": "sent"})

# --------------------------------------- scene 4: compose, check, repair
LOG = [
    ("g1", "composing plan", "#3c4250", 0.30),
    ("g2", "picked 9 parts from the catalog", GREY, 0.75),
    ("g3", "wired 14 nets", GREY, 1.05),
    ("g4", "checking against physics", GREY, 1.35),
    ("g5", "!  IMU 3V3 pin found on a 5V net", "#c2410c", 1.75),
    ("g6", "repaired -- second pass clean", "#15803d", 2.35),
]
sc4_nodes = [
    rect("gcard", 960, 540, 900, 480, 20, "#ffffff"),
    rect("gdot", 555, 350, 14, 14, 7, BLUE,
         glow={"sigma": 8, "opacity": 0.7, "color": BLUE}),
    text("ghead", "build 4212 · quadcopter", 745, 350, 26, INK, 600),
]
for i, (gid, s, col, _) in enumerate(LOG):
    x = 540 + len(s) * 26 * MONO_W / 2
    sc4_nodes.append(text(gid, s, round(x, 1), 430 + i * 58, 26, col,
                          family="mono"))
sc4_nodes.append(text("gfoot", "only plans that pass the checks become builds",
                      960, 792, 22, GREY))
tracks.append(rise("gcard", 0.05, 40))
tracks.append(rise("gdot", 0.15, 20))
tracks.append(rise("ghead", 0.15, 20))
for gid, s, col, at in LOG:
    tracks.append(keyed(gid, opacity=[(at, 0), (at + 0.1, 1)]))
tracks.append(keyed("gfoot", opacity=[(2.7, 0), (2.95, 1)]))

# ------------------------------------------- scene 5: the blueprint draws
K5 = 1.05
OX = (W - 1320 * K5) / 2
OY = 120
sc5_nodes = [
    rect("btabs", 960, 56, 1920, 112, 0, "#ffffff"),
    text("btab1", "Diagram", 760, 56, 26, BLUE, 600),
    rect("btabu", 760, 88, 96, 4, 2, BLUE),
    text("btab2", "Wiring", 900, 56, 26, GREY),
    text("btab3", "Parts", 1020, 56, 26, GREY),
    text("btab4", "Steps", 1130, 56, 26, GREY),
]
# every path from the real svg, fill and stroke as separate nodes where
# both exist; leader lines (stroke, no fill) come in with the labels
part_ids, leader_ids = [], []
for i, p in enumerate(SVG["paths"]):
    fill = rgb_hex(p["fill"]) if p["fill"] != "none" else None
    stroke = rgb_hex(p["stroke"]) if p["stroke"] != "none" else None
    sw = float(p["sw"].replace("px", ""))
    is_leader = fill is None and stroke
    base = {"x": OX, "y": OY, "d": p["d"],
            "keys": {"scale": [{"t": 0, "v": K5}]}}
    if fill:
        n = {"id": f"q{i}f", "type": "path", "fill": fill, **base}
        if float(p["op"]) < 1:
            n["opacity"] = float(p["op"])
        sc5_nodes.append(n)
        (leader_ids if is_leader else part_ids).append(f"q{i}f")
    if stroke:
        n = {"id": f"q{i}s", "type": "path", "fill": stroke,
             "stroke": sw * K5, **base}
        sc5_nodes.append(n)
        (leader_ids if is_leader else part_ids).append(f"q{i}s")
for j, t in enumerate(SVG["texts"]):
    lx, ly = float(t["x"]), float(t["y"])
    s = t["s"]
    half = len(s) * 15 * MONO_W / 2
    x = OX + lx * K5 + (-half if t["anchor"] == "end" else half)
    sc5_nodes.append(text(f"qt{j}", s, round(x, 1), round(OY + ly * K5 - 5, 1),
                          15, BLUE, 500, "mono"))
    leader_ids.append(f"qt{j}")

for nid, at in [("btabs", 0.05), ("btab1", 0.15), ("btabu", 0.15),
                ("btab2", 0.2), ("btab3", 0.25), ("btab4", 0.3)]:
    tracks.append(rise(nid, at, -24))
for k, nid in enumerate(part_ids):
    at = 0.35 + (k / max(1, len(part_ids) - 1)) * 1.3
    tracks.append(keyed(nid, opacity=[(at, 0), (at + 0.18, 1)],
                        y=[(at, 14), (at + 0.3, 0, "outCubic")]))
for k, nid in enumerate(leader_ids):
    at = 1.9 + (k % 6) * 0.12
    tracks.append(keyed(nid, opacity=[(at, 0), (at + 0.22, 1)]))
tracks.append({"target": "j5", "at": 2.6, "cam": {
    "preset": "zoom-promote", "z": 1.28, "anchor": [960, 560], "dur": 1.4}})

# ----------------------------------------------------- scene 6: end card
sc6_nodes = [
    {"id": "e_hatch", "type": "path", "x": 0, "y": 0, "stroke": 1.2,
     "fill": "#e6ebfb", "d": hatch(0, 0, 1920, 1080, 64)},
    text("ewm", "Solder", 960, 480, 190, BLUE, 600, "playfair"),
    text("etag", "Type it. Build it.", 960, 640, 40, INK, 500),
    text("esub", "The AI that turns a prompt into buildable hardware.",
         960, 700, 26, GREY),
]
tracks += [rise("ewm", 0.15, 36), rise("etag", 0.5, 26), rise("esub", 0.7, 22)]

scenes = [
    {"id": "j1", "bg": BG, "dur": 3.0, "nodes": sc1_nodes,
     "note": "Problem, in Solder's own serif: you know what you want to "
             "build; the wiring is where it dies."},
    {"id": "j2", "bg": BG, "dur": 3.2, "nodes": sc2_nodes,
     "note": "The real homepage, real pixels: fades up and settles "
             "like footage."},
    {"id": "j3", "bg": BG, "dur": 3.6, "nodes": sc3_nodes,
     "note": "Crash-zoom into the bar. The prompt types itself -- a palm "
             "sized quadcopter drone -- and the send button clicks."},
    {"id": "j4", "bg": BG, "dur": 3.2, "nodes": sc4_nodes,
     "note": "The job log: parts picked, nets wired, physics checked. A "
             "3V3-on-5V fault appears and Solder repairs itself."},
    {"id": "j5", "bg": BG, "dur": 4.2, "nodes": sc5_nodes,
     "note": "The blueprint draws: the real quadcopter vector assembles "
             "part by part, callouts land, camera pushes in."},
    {"id": "j6", "bg": BG, "dur": 2.8, "nodes": sc6_nodes,
     "note": "End card: wordmark, 'Type it. Build it.', silence."},
]

stage = {"fps": 30, "size": [W, H], "scenes": scenes,
         "audio": {"src": "/assets/audio/gen/solder.mp3", "gain": 0.85,
                   "fade_out": 0.5, "bpm": 123.0, "offset": 0.604,
                   "start": 3.97}}
anim = {"tracks": tracks}
json.dump(stage, open("docs/solder.stage.json", "w"), indent=1)
json.dump(anim, open("docs/solder.anim.json", "w"), indent=1)
total = sum(s["dur"] for s in scenes)
print(f"wrote docs/solder.{{stage,anim}}.json, "
      f"{sum(len(s['nodes']) for s in scenes)} nodes, {len(tracks)} tracks, "
      f"{total:.1f}s")
