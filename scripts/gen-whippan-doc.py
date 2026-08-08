#!/usr/bin/env python3
# whippan's own launch film, authored from one prompt: "show the format
# becoming a film". the json doc is the hero -- a stage snippet types
# itself, the screen it describes materializes, an anim line triggers a
# real crash-zoom, a whip-pan sweeps frames from our reproduced films,
# end card. same overlay contract as every other generator: scene-local
# `at`, unique ids per scene, one track per node per property, x/y keys
# are offsets.
import json
import os

W, H = 1920, 1080
MONO_W = 0.6
INK = "#e8e8e8"
ORANGE = "#ff5c1a"

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def text(id, s, x, y, size, color=INK, weight=400, family="inter"):
    return {"id": id, "type": "text", "text": s, "x": x, "y": y,
            "color": color, "font": {"size": size, "weight": weight,
                                     "family": family}}


def mono(id, s, left, y, size, color):
    cx = left + len(s) * size * MONO_W / 2
    return text(id, s, round(cx, 1), y, size, color, family="mono")


def rect(id, x, y, w, h, r, fill, **kw):
    n = {"id": id, "type": "rect", "x": x, "y": y, "w": w, "h": h,
         "radius": r, "fill": fill}
    n.update(kw)
    return n


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


tracks = []

# ------------------------------------------------- scene 1: the doc types
# dark editor, a real stage.json snippet typed line by line with the
# caret. the ticks this generates ARE the soundtrack's foreground.
J1 = [
    ('l1', '{ "id": "cta", "type": "rect",', 0.50),
    ('l2', '  "w": 320, "h": 96, "radius": 48,', 1.30),
    ('l3', '  "fill": "#ff5c1a",', 2.06),
    ('l4', '  "label": "Get started" }', 2.62),
]
CAD = 0.024
ADV = 44 * MONO_W
sc1_nodes = [text("kicker", "stage.json", 960, 300, 34, "#6b6b6b",
                  family="mono")]
sc1_nodes += [mono(lid, s, 560, 430 + i * 76, 44, INK)
              for i, (lid, s, _) in enumerate(J1)]
sc1_nodes.append(rect("caret", 560 + 1.5, 430, 3, 48, 1, "#f4f4f4"))
for lid, s, at in J1:
    tracks.append({"target": lid, "at": at, "reveal": {
        "unit": "type", "cadence": CAD, "dur": 0.04, "caret": "none"}})
# one caret that rides the typing: per-char x steps on the active line,
# jumps down a row between lines, blinks before the first keystroke
cx, cy = [], []
for i, (lid, s, at) in enumerate(J1):
    y = i * 76
    cy.append((at, y))
    for c in range(len(s) + 1):
        cx.append((at + c * CAD, round(c * ADV, 1)))
    if i + 1 < len(J1):
        nxt = J1[i + 1][2]
        cx.append((nxt - 0.001, round(len(s) * ADV, 1)))
        cy.append((nxt - 0.001, y))
end_t = J1[-1][2] + (len(J1[-1][1]) + 1) * CAD
tracks.append(keyed("caret", x=cx, y=cy,
                    opacity=[(0.0, 1), (0.25, 1), (0.27, 0), (0.48, 0),
                             (0.5, 1), (end_t, 1), (end_t + 0.3, 1),
                             (end_t + 0.32, 0), (end_t + 0.6, 0),
                             (end_t + 0.62, 1)]))
tracks.append(keyed("kicker", opacity=[(0.0, 0), (0.4, 0.9)]))

# ---------------------------------------- scene 2: the screen materializes
# hard cut to the light product screen the json described: navbar, a
# headline, and THE cta button (320x96 r48 #ff5c1a) landing with a pop.
sc2_nodes = [
    rect("nav", 960, 64, 1920, 128, 0, "#ffffff"),
    text("brand", "whippan", 220, 64, 40, "#111111", 700),
    rect("navpill", 1700, 64, 150, 56, 28, "#f0f0f0"),
    text("navdocs", "Docs", 1700, 64, 28, "#444444"),
    text("hl", "Ship the film with the feature", 960, 420, 84,
         "#111111", 700),
    text("sub", "Two JSON files. One render.", 960, 540, 40, "#777777"),
    rect("cta", 960, 720, 320, 96, 48, ORANGE),
    text("ctat", "Get started", 960, 720, 38, "#ffffff", 600),
]
RISE = [("nav", 0.10, -60), ("brand", 0.16, -40), ("navpill", 0.20, -40),
        ("navdocs", 0.20, -40), ("hl", 0.30, 50), ("sub", 0.44, 40)]
for nid, at, dy in RISE:
    tracks.append(keyed(nid,
                        opacity=[(at, 0), (at + 0.30, 1)],
                        y=[(at, dy), (at + 0.42, 0, "outCubic")]))
for nid in ("cta", "ctat"):
    tracks.append(keyed(nid,
                        opacity=[(0.62, 0), (0.72, 1)],
                        scale=[(0.62, 0.6), (0.86, 1.06, "outCubic"),
                               (1.02, 1.0, "outCubic")]))

# ------------------------------------- scene 3: anim.json moves the camera
# same screen, static; an anim.json one-liner types in a code strip at the
# bottom, and the moment it completes the camera crash-zooms onto the cta.
A3 = '{ "target": "cta", "cam": { "preset": "crash-zoom" } }'
sc3_nodes = [
    rect("nav3", 960, 64, 1920, 128, 0, "#ffffff"),
    text("brand3", "whippan", 220, 64, 40, "#111111", 700),
    rect("navpill3", 1700, 64, 150, 56, 28, "#f0f0f0"),
    text("navdocs3", "Docs", 1700, 64, 28, "#444444"),
    text("hl3", "Ship the film with the feature", 960, 420, 84,
         "#111111", 700),
    text("sub3", "Two JSON files. One render.", 960, 540, 40, "#777777"),
    rect("cta3", 960, 720, 320, 96, 48, ORANGE),
    text("ctat3", "Get started", 960, 720, 38, "#ffffff", 600),
    rect("strip", 960, 1002, 1920, 156, 0, "#0d0d0d"),
    text("stripk", "anim.json", 250, 964, 26, "#6b6b6b", family="mono"),
    mono("aline", A3, 250, 1022, 34, "#e8e8e8"),
]
tracks.append({"target": "aline", "at": 0.35, "reveal": {
    "unit": "type", "cadence": 0.018, "dur": 0.03, "caret": "none"}})
tracks.append(keyed("strip", y=[(0.0, 160), (0.28, 0, "outCubic")]))
for nid in ("stripk", "aline"):
    tracks.append(keyed(nid, opacity=[(0.0, 0), (0.3, 1)],
                        y=[(0.0, 160), (0.28, 0, "outCubic")]))
tracks.append({"target": "j3", "at": 1.75, "cam": {
    "preset": "crash-zoom", "z": 3.1, "anchor": [960, 720], "dur": 0.8}})

# ------------------------------ scene 4: whip-pan across films we've made
# three browser frames holding vignettes of our reproduced films: the
# atlas terminal, the chatgpt pill, the base-2 wordmark. real screens.
def browser(pre, cx, bg):
    return [
        rect(f"{pre}win", cx, 560, 1400, 820, 18, bg),
        rect(f"{pre}bar", cx, 190, 1400, 80, 18, "#ececec"),
        rect(f"{pre}d1", cx - 640, 190, 22, 22, 11, "#e0645c"),
        rect(f"{pre}d2", cx - 600, 190, 22, 22, 11, "#e0b55c"),
        rect(f"{pre}d3", cx - 560, 190, 22, 22, 11, "#79c979"),
    ]

sc4_nodes = [text("wall", "every frame here renders from the format",
                  960, 60, 30, "#8a8a8a")]
sc4_nodes += browser("v1", 960, "#101010") + [
    text("v1d", "$", 560, 480, 60, "#565656", family="mono"),
    mono("v1cmd", "git push", 620, 482, 60, "#ffffff"),
    rect("v1dot", 700, 640, 22, 22, 11, "#b55b01",
         glow={"sigma": 7, "opacity": 0.8, "color": "#b55b01"}),
    text("v1b", "Building", 840, 640, 42, "#f2f2f2", 500),
]
sc4_nodes += browser("v2", 2760, "#161616") + [
    text("v2a", "Imagine", 2360, 480, 62, "#ffffff"),
    text("v2b", "anything", 3170, 480, 62, "#ffffff"),
    rect("v2pill", 2762, 480, 500, 96, 48, "#2d2d2d"),
    rect("v2btn", 2950, 480, 64, 64, 10, "#fafafa"),
    text("v2t", "with a simple prompt...", 2700, 482, 26, "#9a9a9a"),
]
sc4_nodes += browser("v3", 4560, "#f2ede4") + [
    text("v3w", "base-2", 4560, 540, 110, "#1c1a17", 700),
    text("v3s", "industrial design, resolved in 8 scenes", 4560, 660,
         30, "#8a8177"),
]
# two whips in ONE cam track (a second track on j4 would replace the
# first); each hop copies the whip-pan preset's velocity profile
tracks.append(keyed("j4", cam_x=[
    (1.0, 0), (1.2, 1116, "inCubic"), (1.5, 1800, "outCubic"),
    (2.05, 1800), (2.25, 2916, "inCubic"), (2.55, 3600, "outCubic")]))

# ------------------------------------------------------ scene 5: end card
sc5_nodes = [
    text("wm", "whippan", 960, 500, 130, "#f4f4f4", 700),
    rect("wpill", 960, 610, 260, 26, 13, ORANGE),
    text("tag", "Launch films, written in JSON", 960, 700, 40, "#9a9a9a"),
]
tracks += [
    keyed("wm", opacity=[(0.15, 0), (0.5, 1)],
          y=[(0.15, 40), (0.55, 0, "outCubic")]),
    keyed("wpill", w=[(0.55, 0), (0.9, 260, "outCubic")],
          opacity=[(0.55, 0), (0.62, 1)]),
    keyed("tag", opacity=[(0.85, 0), (1.2, 1)],
          y=[(0.85, 24), (1.25, 0, "outCubic")]),
]

scenes = [
    {"id": "j1", "bg": "#0d0d0d", "dur": 3.2, "nodes": sc1_nodes},
    {"id": "j2", "bg": "#fafafa", "dur": 3.2, "nodes": sc2_nodes},
    {"id": "j3", "bg": "#fafafa", "dur": 3.4, "nodes": sc3_nodes},
    {"id": "j4", "bg": "#e9e6e0", "dur": 3.0, "nodes": sc4_nodes},
    {"id": "j5", "bg": "#0b0b0b", "dur": 2.8, "nodes": sc5_nodes},
]

stage = {"fps": 30, "size": [W, H], "scenes": scenes}
anim = {"tracks": tracks}
json.dump(stage, open("docs/whippan.stage.json", "w"), indent=1)
json.dump(anim, open("docs/whippan.anim.json", "w"), indent=1)
total = sum(s["dur"] for s in scenes)
print(f"wrote docs/whippan.{{stage,anim}}.json, "
      f"{sum(len(s['nodes']) for s in scenes)} nodes, "
      f"{len(tracks)} tracks, {total}s")
