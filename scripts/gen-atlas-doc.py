#!/usr/bin/env python3
# reproduction of animations/atlas-video.mp4 segments A-C (0-7.5s): terminal
# git push -> output -> console dissolves into the building chip -> the
# deployments dashboard materializes around the chip at ~2.1x zoom and row 1
# flips to Running. all numbers measured from analysis/atlas-video frames
# (f100 terminal, f250 chip, f305 zoom framing, f390 dashboard rest).
# same overlay contract as gen-chatgpt-doc: scene-local `at`, unique ids per
# scene, one track per node, x/y keys are offsets.
import json
import os

W, H = 1920, 1080
MONO_W = 0.6  # jetbrains mono advance per char, em fraction

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))



NUCLEO = "/Users/mintu/coding/portfolio/ui/tools/icons"


def icon(id, svg_file, cx, cy, size, color, stroke=2.0, filled=False):
    """inline a nucleo svg as one path node. paths keep their viewBox
    coords; the node anchors at the icon's top-left so (cx,cy) is the
    optical center after scaling."""
    import re as _re
    src = open(f"{NUCLEO}/{svg_file}").read()
    vb = float(_re.search(r'viewBox="0 0 (\d+)', src).group(1))
    parts = []
    for m in _re.finditer(r'<path[^>]*? d="([^"]+)"', src):
        parts.append(m.group(1))
    for m in _re.finditer(r'<line[^>]*?x1="([\d.]+)"[^>]*?y1="([\d.]+)"[^>]*?x2="([\d.]+)"[^>]*?y2="([\d.]+)"', src):
        x1, y1, x2, y2 = m.groups()
        parts.append(f"M{x1} {y1}L{x2} {y2}")
    for m in _re.finditer(r'<circle[^>]*?cx="([\d.]+)"[^>]*?cy="([\d.]+)"[^>]*?r="([\d.]+)"', src):
        x, y, r = (float(v) for v in m.groups())
        parts.append(f"M{x - r} {y}a{r} {r} 0 1 0 {2 * r} 0"
                     f"a{r} {r} 0 1 0 {-2 * r} 0")
    for m in _re.finditer(r'<polyline[^>]*?points="([^"]+)"', src):
        pts = m.group(1).split()
        parts.append("M" + "L".join(pts))
    k = size / vb
    n = {"id": id, "type": "path", "x": round(cx - size / 2, 1),
         "y": round(cy - size / 2, 1), "fill": color,
         "d": "".join(parts), "keys": {"scale": [{"t": 0, "v": k}]}}
    if not filled:
        n["stroke"] = stroke
    return n


def text(id, s, x, y, size, color, weight=400, family="inter"):
    return {"id": id, "type": "text", "text": s, "x": x, "y": y,
            "color": color, "font": {"size": size, "weight": weight,
                                     "family": family}}


def mono(id, s, left, y, size, color):
    """left-anchored mono line: center computed from the fixed advance."""
    cx = left + len(s) * size * MONO_W / 2
    return text(id, s, round(cx, 1), y, size, color, family="mono")


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


tracks = []

# ------------------------------------------------------- scene 1: terminal
# "$" from f1, block caret blinks, "git push" typed f35-61 (~67ms/char,
# cursor hidden), caret solid through the loaded hold, enter jolt at 2.0
# scrolls the console up as output prints, everything dissolves 2.33-2.9
# while the building chip fades in underneath.
CON = [  # console column: (id, text, size, color, print time)
    ("out1", "[feat/login-redesign 3f8a2c1] update auth flow for chrome.",
     26, "#c2c2c2", 2.03),
    ("out2", "11 files changed, 142 insertions(+), 38 deletions(-)",
     26, "#9a9a9a", 2.10),
    ("out3", "create mode 100644 src/auth/session.ts", 26, "#8a8a8a", 2.18),
    ("out4", "create mode 100644 src/auth/tokens.ts", 26, "#8a8a8a", 2.27),
    ("out5", "delete mode 100644 src/auth/legacy.ts", 26, "#8a8a8a", 2.38),
    ("out6", "To github.com:dokedu/dokedu.git", 26, "#6b6b6b", 2.55),
]
# column scroll: the jolt then one step up per print
SHIFTS = [(2.017, -50), (2.10, -42), (2.18, -42), (2.27, -42),
          (2.38, -42), (2.55, -42)]


def scrolled(extra=0.0):
    """shared y-offset timeline for every console node."""
    ks, acc = [(0.0, 0.0)], 0.0
    for t0, dv in SHIFTS:
        ks.append((t0, acc))
        acc += dv
        ks.append((t0 + 0.07, acc, "outCubic"))
    return [(t, v + extra) for t, v in [(k[0], k[1]) for k in ks]]


def con_y(seq):
    return [(t, v, "outCubic") for t, v in seq]


sc1_nodes = [
    text("dollar", "$", 692, 542, 96, "#565656", family="mono"),
    mono("cmd", "git push", 800, 545, 96, "#ffffff"),
    rect("caret", 1410, 540, 48, 92, 2, "#ffffff"),
] + [mono(cid, s, 620, 620 + i * 42, sz, col) for i, (cid, s, sz, col, _) in
     enumerate(CON)] + [
    rect("chipdot1", 765, 540, 30, 30, 15, "#b55b01",
         glow={"sigma": 9, "opacity": 0.8, "color": "#b55b01"}),
    text("chipb1", "Building", 985, 540, 62, "#f2f2f2", weight=500),
    text("chipd0", "0", 1168, 540, 54, "#8a8a8a"),
    text("chipd1_1", "1", 1168, 540, 54, "#8a8a8a"),
    text("chips1", "s", 1202, 541, 54, "#8a8a8a"),
]
tracks += [
    keyed("cmd", opacity=[(0, 1)], y=con_y(scrolled())),
    keyed("dollar", y=con_y(scrolled()),
          opacity=[(2.33, 1), (2.9, 0)]),
    # caret: blink until typing (0.567), hidden while typing, solid through
    # the hold, gone with the jolt
    keyed("caret",
          y=con_y(scrolled()),
          opacity=[(0.03, 1), (0.5, 1), (0.53, 0), (1.0, 0), (1.02, 1),
                   (2.0, 1), (2.05, 0)]),
]
tracks.append({"target": "cmd", "at": 0.567, "reveal": {
    "unit": "type", "cadence": 0.062, "dur": 0.05, "caret": "none"}})
# cmd fade with the console
tracks.append({"target": "cmd", "at": 2.33, "keys": {
    "opacity": [{"t": 0, "v": 1}, {"t": 0.57, "v": 0}]}})
for i, (cid, s, sz, col, pt) in enumerate(CON):
    tracks.append(keyed(cid,
                        y=con_y(scrolled()),
                        opacity=[(pt, 0), (pt + 0.06, 1),
                                 (2.35, 0.8), (2.9, 0)]))
# chip fades in under the dissolving console; counter 0 -> 1 at 2.83
for nid, ka in [("chipdot1", 0.85), ("chipb1", 1.0), ("chips1", 1.0)]:
    tracks.append(keyed(nid, opacity=[(2.3, 0), (3.0, ka)]))
tracks.append(keyed("chipd0",
                    opacity=[(2.3, 0), (2.78, 0.9), (2.83, 0.9), (2.93, 0)],
                    y=[(2.83, 0), (2.93, -16, "outCubic")]))
tracks.append(keyed("chipd1_1",
                    opacity=[(2.83, 0), (2.93, 1)],
                    y=[(2.83, 16), (2.93, 0, "outCubic")]))

# ------------------------------------------------------------ scene 2: chip
# 2.7s of loaded stillness: the chip alone on the plum-washed black,
# odometer rolls 1->2 at 0.85 and 2->3 at 1.83 (real seconds).
sc2_nodes = [
    rect("plum", 960, 60, 1200, 460, 230, "#120b10", blur=150),
    rect("chipdot2", 765, 540, 30, 30, 15, "#b55b01",
         glow={"sigma": 9, "opacity": 0.8, "color": "#b55b01"}),
    text("chipb2", "Building", 985, 540, 62, "#f2f2f2", weight=500),
    text("chipd1", "1", 1168, 540, 54, "#8a8a8a"),
    text("chipd2", "2", 1168, 540, 54, "#8a8a8a"),
    text("chipd3", "3", 1168, 540, 54, "#8a8a8a"),
    text("chips2", "s", 1202, 541, 54, "#8a8a8a"),
]
tracks += [
    keyed("chipd1", opacity=[(0, 1), (0.85, 1), (0.95, 0)],
          y=[(0.85, 0), (0.95, -16, "outCubic")]),
    keyed("chipd2", opacity=[(0.85, 0), (0.95, 1), (1.83, 1), (1.93, 0)],
          y=[(0.85, 16), (0.95, 0, "outCubic"), (1.83, 0),
             (1.93, -16, "outCubic")]),
    keyed("chipd3", opacity=[(1.83, 0), (1.93, 1)],
          y=[(1.83, 16), (1.93, 0, "outCubic")]),
]

# ------------------------------------------------- scene 3: the dashboard
# the page is already laid out and fades in around the chip in ~4 frames at
# 2.13x zoom, anchored so row 1's Building cell sits exactly where the chip
# was; the camera pulls back with a long decel, the counter reaches 4s,
# and the row flips to Running.
ROWS = [
    ("a4d9c3f", "Fix issue with user login timeout caus...", None, None,
     "Production", "feat/login-red...", ""),
    ("b7e2a1d", "Add new feature to export reports in P...", "Ready",
     "#1fc133", "Production", "main", "13 seconds ago"),
    ("c8f4b2e", "Improve loading speed on the dashbo...", "Stopped",
     "#525252", "Development", "feat/primary-f...", "2 min ago"),
    ("d1a3c5b", "Update user profile page layout to en...", "Failed",
     "#e3133d", "Development", "chore/default...", "1 day ago"),
    ("e6b7d8f", "Refactor notification system to suppo...", "Stopped",
     "#525252", "Development", "feat/central-h...", "1 day ago"),
    ("f3c9e4a", "Fix typo in settings menu and update...", "Stopped",
     "#525252", "Production", "main", "1 day ago"),
    ("a7d5f2c", "Implement dark mode option for bett...", "Failed",
     "#e3133d", "Production", "main", "1 day ago"),
    ("b2e8c6d", "Add unit tests for payment processi...", "Stopped",
     "#525252", "Production", "main", "1 day ago"),
]
sc3_nodes = [
    rect("plum3", 960, 60, 1200, 460, 230, "#120b10", blur=150),
    # breadcrumb
    rect("bc_tile", 190, 300, 36, 36, 9, "#f2f2f2"),
    text("bc_glyph", "a", 190, 300, 24, "#141014", weight=600),
    text("bc_org", "Dokedu", 269, 300, 28, "#e6e6e6", weight=500),
    text("bc_sep", "/", 367, 300, 26, "#5a5a5a"),
    text("bc_proj", "Dokedu Backend", 492, 298, 28, "#e6e6e6", weight=500),
    # tabs
    rect("tab_pill", 259, 375, 216, 52, 11, "#211f23"),
    icon("tab_dep_i", "core/grid-2.svg", 189, 375, 22, "#f0f0f0"),
    text("tab_dep", "Deployments", 290, 374, 26, "#f0f0f0", weight=500),
    icon("tab_logs_i", "micro-bold/bars-filter.svg", 402, 373, 20, "#8f8f8f"),
    text("tab_logs", "Logs", 460, 373, 26, "#8f8f8f"),
    icon("tab_set_i", "core/gear-3.svg", 530, 373, 22, "#8f8f8f"),
    text("tab_set", "Settings", 606, 373, 26, "#8f8f8f"),
    # header
    text("hd_t", "Deployments", 241, 449, 26, "#d0d0d0", weight=500),
    text("hd_sub", "Automatically created for pushes to", 549, 449, 24,
         "#8f8f8f"),
    icon("hd_gh", "social/logo-github.svg", 795, 448, 28, "#c9c9c9", filled=True),
    text("hd_repo", "dokedu/dokedu", 915, 447, 26, "#e6e6e6", weight=500),
    rect("btn_create", 1775, 444, 240, 58, 13, "#fafafa"),
    text("btn_create_t", "Create Deployment", 1775, 444, 24, "#161616",
         weight=500),
]
for i, (h, msg, st, stc, env, br, age) in enumerate(ROWS):
    y = 523 + i * 76
    p = f"r{i}_"
    sc3_nodes += [
        {"id": p + "ci", "type": "path", "x": 187, "y": y, "fill": "#6f6f6f",
         "stroke": 2.0,
         "d": "M-9 0L-5 0M5 0L9 0M-5 0a5 5 0 1 0 10 0a5 5 0 1 0 -10 0"},
        text(p + "hash", h, 249, y, 24, "#8f8f8f"),
        text(p + "msg", msg, 305 + len(msg) * 5.6, y, 24, "#e6e6e6"),
        text(p + "env", env, 1126, y, 26, "#c9c9c9"),
        {"id": p + "bi", "type": "path", "x": 1310, "y": y, "fill": "#6f6f6f",
         "stroke": 2.0,
         "d": "M-4 -3L-4 6M-4 -6a2.8 2.8 0 1 0 0.02 0M-4 6a2.8 2.8 0 1 0 0.02 "
              "0M6 -6a2.8 2.8 0 1 0 0.02 0M6 -3C6 2 -1 0 -4 3"},
        text(p + "br", br, 1420, y, 26, "#c9c9c9"),
        rect(p + "av", 1556, y, 28, 28, 14, "#2c2c2e"),
        {"id": p + "avp", "type": "path", "x": 1556, "y": y, "fill": "#8f8f8f",
         "stroke": 1.8, "d": "M-4 0L4 0M0 -4L0 4"},
        text(p + "auth", "aaronmahlke", 1658, y, 26, "#c9c9c9"),
    ]
    if age:
        sc3_nodes.append(text(p + "age", age, 1868, y, 24, "#8f8f8f"))
    if i > 0:
        sc3_nodes.append(rect(p + "sep", 1000, y - 38, 1700, 2, 1, "#232226"))
    if st:
        sc3_nodes += [
            rect(p + "dot", 770, y, 16, 16, 8, stc),
            text(p + "st", st, 800 + len(st) * 7, y, 26,
                 "#e0e0e0" if stc != "#525252" else "#8f8f8f"),
            text(p + "dur", "34s" + (" (5m ago)" if i == 1 else ""),
                 958 + (40 if i == 1 else 0), y, 24, "#8f8f8f"),
        ]
# row 1 live cells: building cluster (continues the chip) and its flip
sc3_nodes += [
    rect("r0_dot_b", 770, 523, 12, 12, 6, "#b55b01",
         glow={"sigma": 5, "opacity": 0.8, "color": "#b55b01"}),
    text("r0_st_b", "Building", 852, 523, 26, "#e0e0e0", weight=500),
    text("r0_d3", "3", 927, 523, 24, "#8f8f8f"),
    text("r0_d4", "4", 927, 523, 24, "#8f8f8f"),
    text("r0_s", "s", 944, 524, 24, "#8f8f8f"),
    rect("r0_dot_r", 770, 523, 12, 12, 6, "#1fc133",
         glow={"sigma": 5, "opacity": 0.7, "color": "#1fc133"}),
    text("r0_st_r", "Running", 850, 523, 26, "#e0e0e0", weight=500),
    text("r0_age", "now", 1868, 523, 24, "#8f8f8f"),
]

FADE = [(0.03, 0), (0.10, 1)]
live = {"r0_dot_b", "r0_st_b", "r0_d3", "r0_s"}
for n in sc3_nodes:
    nid = n["id"]
    if nid in live or nid in ("r0_d4", "r0_dot_r", "r0_st_r", "r0_age"):
        continue
    if nid == "btn_create":
        tracks.append(keyed(nid, opacity=[(1.05, 0), (1.15, 1)],
                            x=[(1.05, 250), (1.35, 0, "outCubic")]))
    elif nid == "btn_create_t":
        tracks.append(keyed(nid, opacity=[(1.05, 0), (1.18, 1)],
                            x=[(1.05, 250), (1.35, 0, "outCubic")]))
    else:
        tracks.append(keyed(nid, opacity=FADE))
tracks += [
    # odometer 3 -> 4 at 0.85, then the whole cluster flips to Running
    keyed("r0_d3", opacity=[(0, 1), (0.85, 1), (0.95, 0)],
          y=[(0.85, 0), (0.95, -9, "outCubic")]),
    keyed("r0_d4", opacity=[(0.85, 0), (0.95, 1), (1.03, 1), (1.13, 0)],
          y=[(0.85, 9), (0.95, 0, "outCubic")]),
    keyed("r0_s", opacity=[(0, 1), (1.03, 1), (1.13, 0)]),
    keyed("r0_dot_b", opacity=[(0, 1), (1.03, 1), (1.13, 0)]),
    keyed("r0_st_b", opacity=[(0, 1), (1.03, 1), (1.13, 0)]),
    keyed("r0_dot_r", opacity=[(1.03, 0), (1.13, 1)]),
    keyed("r0_st_r", opacity=[(1.03, 0), (1.13, 1)]),
    keyed("r0_age", opacity=[(1.08, 0), (1.2, 1)]),
    # the pull-back: anchored zoom, long decel, micro-settle
    # zoom curve fitted to the real dot-area measurements (f305-f410);
    # the row-1 status dot is the anchor and never moves
    keyed("s3",
          cam_zoom=[(0, 2.5), (0.05, 2.42), (0.283, 1.79), (0.783, 1.27),
                    (1.283, 1.07), (1.62, 1.02), (1.8, 1.0)],
          cam_x=[(0, -112.4), (0.05, -109.8), (0.283, -81.6), (0.783, -37.2),
                 (1.283, -8.7), (1.62, -0.2), (1.8, 0.0)],
          cam_y=[(0, -14.9), (0.05, -14.5), (0.283, -10.3), (0.783, -4.4),
                 (1.283, -1.1), (1.62, -0.3), (1.8, 0.0)]),
]

stage = {
    "fps": 30,
    "size": [W, H],
    "audio": {"src": "/assets/audio/pad.m4a", "gain": 0.5, "fade_out": 0.8},
    "scenes": [
        {"id": "s1", "bg": "#000000", "dur": 3.0,
         "transition": {"kind": "cut"}, "nodes": sc1_nodes},
        {"id": "s2", "bg": "#0a0a0c", "dur": 2.0,
         "transition": {"kind": "cut"}, "nodes": sc2_nodes},
        {"id": "s3", "bg": "#0a0a0c", "dur": 1.8,
         "transition": {"kind": "cut"}, "nodes": sc3_nodes},
    ],
}

with open("docs/atlas.stage.json", "w") as f:
    json.dump(stage, f, indent=1)
with open("docs/atlas.anim.json", "w") as f:
    json.dump({"tracks": tracks}, f, indent=1)
print("wrote docs/atlas.{stage,anim}.json,",
      sum(len(s["nodes"]) for s in stage["scenes"]), "nodes,",
      len(tracks), "tracks")
