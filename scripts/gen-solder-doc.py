#!/usr/bin/env python3
# launch film for solder, aceternity-style: near-black stage, dot grid,
# violet/cyan orbs, real product screenshots floating in gradient-glow
# frames. screens are actual captures -- the homepage from localhost:5260
# and the settled quadcopter diagram from the vector-hardware harness.
# overlay contract as usual: scene-local `at`, unique ids per scene, one
# track per node per property, x/y keys are offsets.
import json
import os

W, H = 1920, 1080
BG = "#050509"
WHITE = "#f5f5f7"
GREY = "#8b8b96"
INDIGO = "#818cf8"
GRAD = [{"at": 0.0, "color": "#6366f1"}, {"at": 0.5, "color": "#a855f7"},
        {"at": 1.0, "color": "#22d3ee"}]

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def text(id, s, x, y, size, color=WHITE, weight=400, family="inter"):
    return {"id": id, "type": "text", "text": s, "x": x, "y": y,
            "color": color, "font": {"size": size, "weight": weight,
                                     "family": family}}


def rect(id, x, y, w, h, r, fill=None, **kw):
    n = {"id": id, "type": "rect", "x": x, "y": y, "w": w, "h": h,
         "radius": r}
    if fill:
        n["fill"] = fill
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


def dots(step=72, r=1.6):
    parts = []
    for y in range(step // 2, H, step):
        for x in range(step // 2, W, step):
            parts.append(f"M{x - r} {y}a{r} {r} 0 1 0 {2*r} 0"
                         f"a{r} {r} 0 1 0 {-2*r} 0")
    return "".join(parts)


def rise(nid, at, dy=44, dur=0.5):
    return keyed(nid, opacity=[(at, 0), (at + dur * 0.7, 1)],
                 y=[(at, dy), (at + dur, 0, "outCubic")])


DOTS = dots()


def stagebase(p):
    """dot grid + two color orbs, shared by every scene."""
    return [
        {"id": f"{p}dots", "type": "path", "x": 0, "y": 0,
         "fill": "#181824", "d": DOTS},
        rect(f"{p}orb1", 320, 940, 900, 900, 450, "#3b2a8f", blur=170,
             opacity=0.5),
        rect(f"{p}orb2", 1680, 140, 760, 760, 380, "#0e4a5e", blur=160,
             opacity=0.45),
    ]


def framed(p, src, w, h, at=0.1):
    """a screenshot floating in a gradient border with a glow halo."""
    pad = 14
    ns = [
        rect(f"{p}halo", 960, 540, w + pad * 2, h + pad * 2, 26,
             glow={"sigma": 46, "opacity": 0.55, "color": "#6d5cf0"},
             gradient={"angle": 30, "stops": GRAD}),
        rect(f"{p}mat", 960, 540, w + 8, h + 8, 20, "#0a0a12"),
        {"id": f"{p}shot", "type": "image", "src": src,
         "x": 960, "y": 540, "w": w, "h": h, "radius": 14},
    ]
    trs = [rise(f"{p}halo", at, 70, 0.7), rise(f"{p}mat", at, 70, 0.7),
           rise(f"{p}shot", at, 70, 0.7)]
    return ns, trs


tracks = []

# ---------------------------------------------------- scene 1: the problem
sc1_nodes = stagebase("p") + [
    rect("pspot", 960, 60, 1300, 700, 350, blur=210, opacity=0.32,
         gradient={"angle": 90, "stops": [
             {"at": 0.0, "color": "#8b7cf8"},
             {"at": 1.0, "color": "#050509"}]}),
    text("p1", "You know what you want to build.", 960, 450, 76, WHITE, 700),
    text("p2", "The wiring is where it dies.", 960, 560, 76, INDIGO, 700),
    text("p3", "Datasheets. Pinouts. A 5V pin on a 3.3V net.",
         960, 680, 28, GREY),
]
tracks += [keyed("pspot", opacity=[(0.0, 0), (0.8, 0.32)]),
           rise("p1", 0.25, 44), rise("p2", 0.6, 44), rise("p3", 1.1, 30)]

# --------------------------------------------------- scene 2: the homepage
HW, HH = 1460, 821
sc2_nodes = stagebase("h")
fr, ft = framed("h", "/assets/solder/home.png", HW, HH, 0.35)
sc2_nodes += fr
tracks += ft
sc2_nodes.append(text("hkick", "this is Solder", 960, 96, 30, GREY, 500))
tracks.append(rise("hkick", 0.12, 26))

# ---------------------------------- scene 3: zoom into the bar, type, send
# the frame carries over; camera dives to the real input bar inside the
# screenshot. geometry maps homepage css -> film through the fit scale.
K = HW / 1920


def m(px, py):
    return (round(960 + (px - 960) * K, 1), round(540 + (py - 540) * K, 1))


PROMPT = "a palm sized quadcopter drone"
bx, by = m(960, 655)
tx, _ = m(723, 655)
sx, sy = m(1191, 654)
sc3_nodes = stagebase("z")
fr, _ = framed("z", "/assets/solder/home.png", HW, HH)
sc3_nodes += fr
sc3_nodes += [
    rect("zcover", bx - 18, by, round(452 * K, 1), 34, 8, "#ffffff",
         opacity=0),
    text("ztyped", PROMPT, round(tx + len(PROMPT) * 12.2 * 0.5 * 0.5, 1),
         by, 12.2, "#1d1d1d"),
    {"id": "zsend2", "type": "image", "src": "/assets/solder/send.png",
     "x": sx, "y": sy, "w": 29, "h": 29},
]
tracks.append(keyed("zcover", opacity=[(0.62, 0), (0.78, 1)]))
tracks.append({"target": "ztyped", "at": 0.85, "reveal": {
    "unit": "type", "cadence": 0.052, "dur": 0.04,
    "caret": "bar", "caret_typing": "solid"}})
tracks.append({"target": "j3", "at": 0.12, "cam": {
    "preset": "crash-zoom", "z": 3.1, "anchor": [bx, by], "dur": 0.7}})
end_type = 0.85 + len(PROMPT) * 0.052
tracks.append(keyed("zsend2",
                    scale=[(end_type + 0.25, 1), (end_type + 0.33, 0.85,
                            "outCubic"), (end_type + 0.45, 1, "outCubic")]))
tracks.append({"target": "zsend2", "at": end_type + 0.28, "state": "sent"})

# --------------------------------------- scene 4: compose, check, repair
LOG = [
    ("g1", "composing plan", "#c8c8d4", 0.30),
    ("g2", "picked 9 parts from the catalog", GREY, 0.75),
    ("g3", "wired 14 nets", GREY, 1.05),
    ("g4", "checking against physics", GREY, 1.35),
    ("g5", "!  IMU 3V3 pin found on a 5V net", "#fb923c", 1.75),
    ("g6", "repaired -- second pass clean", "#34d399", 2.35),
]
MONO_W = 0.6
sc4_nodes = stagebase("g") + [
    rect("gedge", 960, 540, 916, 496, 24,
         glow={"sigma": 38, "opacity": 0.4, "color": "#6d5cf0"},
         gradient={"angle": 30, "stops": GRAD}),
    rect("gcard", 960, 540, 900, 480, 20, "#0c0c15"),
    rect("gdot", 555, 350, 14, 14, 7, INDIGO,
         glow={"sigma": 9, "opacity": 0.9, "color": INDIGO}),
    text("ghead", "build 4212 · quadcopter", 745, 350, 26, WHITE, 600),
]
for i, (gid, s, col, _) in enumerate(LOG):
    x = 540 + len(s) * 26 * MONO_W / 2
    sc4_nodes.append(text(gid, s, round(x, 1), 430 + i * 58, 26, col,
                          family="mono"))
sc4_nodes.append(text("gfoot", "only plans that pass the checks become builds",
                      960, 792, 22, GREY))
tracks += [rise("gedge", 0.05, 44), rise("gcard", 0.05, 44),
           rise("gdot", 0.18, 24), rise("ghead", 0.18, 24)]
for gid, s, col, at in LOG:
    tracks.append(keyed(gid, opacity=[(at, 0), (at + 0.1, 1)]))
tracks.append(keyed("gfoot", opacity=[(2.7, 0), (2.95, 1)]))

# ------------------------------------------- scene 5: the blueprint draws
QW, QH = 1420, 968
sc5_nodes = stagebase("q")
fr, ft = framed("q", "/assets/solder/quad.png", QW, QH, 0.15)
sc5_nodes += fr
tracks += ft
sc5_nodes.append(text("qkick",
                      "wiring checked against physics, drawn as a build",
                      960, 66, 26, GREY, 500))
tracks.append(rise("qkick", 0.3, 22))
tracks.append({"target": "j5", "at": 2.4, "cam": {
    "preset": "zoom-promote", "z": 1.34, "anchor": [960, 560], "dur": 1.5}})

# ----------------------------------------------------- scene 6: end card
sc6_nodes = stagebase("e") + [
    rect("espot", 960, 100, 1200, 760, 380, blur=200, opacity=0.3,
         gradient={"angle": 90, "stops": [
             {"at": 0.0, "color": "#8b7cf8"},
             {"at": 1.0, "color": "#050509"}]}),
    text("ewm", "Solder", 960, 470, 190, WHITE, 600, "playfair"),
    rect("ebeam", 960, 596, 340, 5, 2.5,
         gradient={"angle": 0, "stops": GRAD},
         glow={"sigma": 14, "opacity": 0.8, "color": "#7c6cf5"}),
    text("etag", "Type it. Build it.", 960, 672, 38, WHITE, 500),
    text("esub", "The AI that turns a prompt into buildable hardware.",
         960, 730, 25, GREY),
]
tracks += [keyed("espot", opacity=[(0.0, 0), (0.7, 0.3)]),
           rise("ewm", 0.15, 40),
           keyed("ebeam", w=[(0.55, 0), (0.95, 340, "outCubic")],
                 opacity=[(0.55, 0), (0.65, 1)]),
           rise("etag", 0.75, 26), rise("esub", 0.95, 22)]

scenes = [
    {"id": "j1", "bg": BG, "dur": 3.0, "nodes": sc1_nodes,
     "note": "Problem on the dark stage: you know what you want to build; "
             "the wiring is where it dies."},
    {"id": "j2", "bg": BG, "dur": 3.2, "nodes": sc2_nodes,
     "note": "The real homepage floats up in a gradient-glow frame over "
             "the dot grid."},
    {"id": "j3", "bg": BG, "dur": 3.6, "nodes": sc3_nodes,
     "note": "Crash-zoom into the real input bar. The prompt types -- a "
             "palm sized quadcopter drone -- and the send button clicks."},
    {"id": "j4", "bg": BG, "dur": 3.2, "nodes": sc4_nodes,
     "note": "The job log in a dark glass card: physics check finds a "
             "3V3-on-5V fault, Solder repairs itself."},
    {"id": "j5", "bg": BG, "dur": 4.2, "nodes": sc5_nodes,
     "note": "The real quadcopter blueprint in its glowing frame, camera "
             "pushing in."},
    {"id": "j6", "bg": BG, "dur": 2.8, "nodes": sc6_nodes,
     "note": "End card: wordmark over the spotlight, gradient beam, "
             "silence."},
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
