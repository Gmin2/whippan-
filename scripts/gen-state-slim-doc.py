#!/usr/bin/env python3
# reproduction of state-slim (earnin brand film, 55.5s, 1138x640, 30fps).
# the whole edit grammar is the 1-frame background flip between the three
# brand tokens (yellow/off-white/black), so chapters are split into cut
# sub-scenes at the ledger's flip frames, 1:1 with the real timeline.
# spec sheets are type + rule lines + dimension marks, photos are gradient
# stand-ins, and the earn-in logo is literally a toggle: pill + knob with
# a keyed x, bookending the film.
import json
import os

W, H = 1138, 640
CX, CY = W / 2, H / 2
YEL = "#ffe91e"
OW = "#f4f5f0"
BLACK = "#000000"
DRAFT = "#1c1c1c"
GREY = "#9a9a9a"
PINK = "#f7ecf2"

K = 0.5523

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
scenes, tracks = [], []


def text(id, s, x, y, size, color=BLACK, weight=500, family=None, rot=None):
    n = {"id": id, "type": "text", "text": s, "x": round(x, 1),
         "y": round(y, 1), "color": color,
         "font": {"size": size, "weight": weight}}
    if family:
        n["font"]["family"] = family
    if rot:
        n["rot"] = rot
    return n


def rect(id, x, y, w, h, r, fill, **kw):
    n = {"id": id, "type": "rect", "x": round(x, 1), "y": round(y, 1),
         "w": round(w, 1), "h": round(h, 1), "radius": r, "fill": fill}
    n.update(kw)
    return n


def circle(id, x, y, r, fill, **kw):
    return rect(id, x, y, 2 * r, 2 * r, r, fill, **kw)


def path(id, x, y, d, fill, **kw):
    n = {"id": id, "type": "path", "x": round(x, 1), "y": round(y, 1),
         "d": d, "fill": fill}
    n.update(kw)
    return n


def rrect_d(w, h, r):
    # rounded rect outline centered on 0,0
    hw, hh = w / 2, h / 2
    k = r * K
    return (f"M{-hw + r} {-hh}L{hw - r} {-hh}"
            f"C{hw - r + k} {-hh} {hw} {-hh + r - k} {hw} {-hh + r}"
            f"L{hw} {hh - r}"
            f"C{hw} {hh - r + k} {hw - r + k} {hh} {hw - r} {hh}"
            f"L{-hw + r} {hh}"
            f"C{-hw + r - k} {hh} {-hw} {hh - r + k} {-hw} {hh - r}"
            f"L{-hw} {-hh + r}"
            f"C{-hw} {-hh + r - k} {-hw + r - k} {-hh} {-hw + r} {-hh}Z")


def circle_d(r, cx=0, cy=0):
    k = r * K
    return (f"M{cx - r} {cy}C{cx - r} {cy - k} {cx - k} {cy - r} {cx} {cy - r}"
            f"C{cx + k} {cy - r} {cx + r} {cy - k} {cx + r} {cy}"
            f"C{cx + r} {cy + k} {cx + k} {cy + r} {cx} {cy + r}"
            f"C{cx - k} {cy + r} {cx - r} {cy + k} {cx - r} {cy}Z")


def dash_d(length, on=9, off=8):
    segs, x = [], -length / 2
    while x < length / 2:
        segs.append(f"M{round(x, 1)} 0L{round(min(x + on, length / 2), 1)} 0")
        x += on + off
    return "".join(segs)


def dashline(id, x, y, length, color, vertical=False, stroke=1.5):
    n = path(id, x, y, dash_d(length), color, stroke=stroke)
    if vertical:
        n["rot"] = 90
    return n


def solidline(id, x, y, length, color, vertical=False, stroke=1.5):
    d = f"M{-length / 2} 0L{length / 2} 0"
    n = path(id, x, y, d, color, stroke=stroke)
    if vertical:
        n["rot"] = 90
    return n


def track(nid, at=0.0, **props):
    keys = {}
    for name, seq in props.items():
        out = []
        for k in seq:
            kk = {"t": round(k[0], 3), "v": k[1]}
            if len(k) > 2:
                kk["ease"] = k[2]
            out.append(kk)
        keys[name] = out
    t = {"target": nid, "keys": keys}
    if at:
        t["at"] = at
    tracks.append(t)


def reveal(nid, at, **kw):
    tracks.append({"target": nid, "at": at, "reveal": kw})


def scene(id, bg, frames, nodes, kind="cut", tdur=0.0):
    tr = {"kind": kind}
    if tdur:
        tr["dur"] = tdur
    scenes.append({"id": id, "bg": bg, "dur": round(frames / 30, 3),
                   "transition": tr, "nodes": nodes})


def steps_vis(nid, spans, total):
    # hard-step opacity: visible during [a,b) spans
    keys = [(0, 1 if spans and spans[0][0] <= 0 else 0)]
    for a, b in spans:
        if a > 0:
            keys.append((a - 0.001, 0))
            keys.append((a, 1))
        keys.append((min(b, total) - 0.001, 1))
        if b < total:
            keys.append((b, 0))
    track(nid, opacity=keys)


def blueprint(pfx, color="#4a4a4a", vxs=(276, 836), hys=(262, 352)):
    ns = []
    for i, vx in enumerate(vxs):
        ns.append(dashline(f"{pfx}v{i}", vx, CY, H, color, vertical=True))
    for i, hy in enumerate(hys):
        ns.append(dashline(f"{pfx}h{i}", CX, hy, W, color))
    return ns


# ---------------------------------------------------------------- chapter 1
# "We" -> "We love" -> "We love chaos", three flips
scene("s1a", OW, 11, [text("we1", "We", CX, 330, 560, BLACK, 500)])
track("we1", scale=[(0, 1.0), (0.36, 1.05, "outCubic")])

scene("s1b", YEL, 10, [
    text("wl1", "We", 350, 320, 170, BLACK, 500),
    text("wl2", "love", 620, 320, 170, BLACK, 800),
])

scene("s1c", BLACK, 23, [
    text("wc1", "We love", 400, 320, 110, YEL, 500),
    text("wc2", "chaos", 800, 320, 110, YEL, 800),
])

# ---------------------------------------------------------------- chapter 2
# draft typewriter on blueprint grid, then flip to yellow hero
n2 = blueprint("g2")
n2.append(text("org1", "organized chaos.", CX, 318, 96, GREY, 500))
scene("s2a", DRAFT, 40, n2)
reveal("org1", 0.02, unit="type", cadence=0.045, cadence_end=0.1, dur=0.08)

scene("s2b", YEL, 15, [text("org2", "organized chaos.", CX, 318, 96,
                            BLACK, 700)])

# ---------------------------------------------------------------- chapter 3
# toggle drawn on the grid, then yellow toggle, knob slides right
n3 = blueprint("g3", vxs=(400, 517, 740), hys=(255, 385))
n3.append(rect("tg1", CX, 320, 342, 132, 66, "#8f8f8f"))
n3.append(circle("tk1", 462, 320, 52, "#c2c2c2"))
scene("s3a", DRAFT, 25, n3)
track("tg1", opacity=[(0, 0), (0.12, 1)])
track("tk1", opacity=[(0, 0), (0.2, 1)],
      scale=[(0.1, 0.3), (0.45, 1.0, "outCubic")])

scene("s3b", BLACK, 9, [
    rect("tg2", CX, 320, 350, 135, 67, YEL),
    circle("tk2", 462, 320, 52, BLACK),
])
track("tk2", x=[(0.03, 0), (0.28, 214, "outCubic")])

# ---------------------------------------------------------------- chapter 4
# the toggle becomes the earn in logo, letters fill in
scene("s4", YEL, 17, [
    rect("lg1", CX, 318, 372, 142, 71, BLACK),
    circle("lk1", 688, 318, 62, "#ffffff"),
    text("lgt1", "earn", 512, 320, 86, "#ffffff", 600),
    text("lgi1", "in", 688, 320, 58, BLACK, 700),
])
reveal("lgt1", 0.03, unit="glyph", stagger=0.09, dur=0.15, rise=0,
       accent="#ffffff")

# ---------------------------------------------------------------- chapter 5
# fast use-case card montage on pale pink
scene("s5a", PINK, 8, [
    rect("m1p", CX, 320, 200, 78, 39, BLACK),
    circle("m1k", 634, 320, 34, "#ffffff"),
    text("m1t", "earn", 540, 321, 46, "#ffffff", 600),
    text("m1i", "in", 634, 321, 32, BLACK, 700),
])

scene("s5b", PINK, 8, [
    rect("m2c", CX, 320, 660, 410, 28, YEL),
    text("m2a", "In real time.", CX, 275, 46, BLACK, 700),
    text("m2b", "Like real time,", CX, 355, 46, BLACK, 700),
])

n5c = [rect("m3c", CX, 320, 660, 410, 28, OW)]
for i in range(5):
    n5c.append(text(f"m3r{i}", "Ramen", 460, 175 + i * 72, 44, BLACK, 600))
n5c += [circle("m3f0", 700, 210, 44, "#c97a3a"),
        circle("m3f1", 760, 330, 40, "#a8522e"),
        circle("m3f2", 690, 440, 44, "#d9a441")]
scene("s5c", PINK, 8, n5c)

n5d = [rect("m4c", CX, 320, 660, 410, 28, BLACK)]
for i in range(3):
    n5d.append(text(f"m4r{i}", "Right Now", CX, 220 + i * 100, 52, YEL, 700))
scene("s5d", PINK, 6, n5d)

# ---------------------------------------------------------------- chapter 6
# "This is not just a card", is-not on a yellow highlight
scene("s6", PINK, 15, [
    rect("c6", CX, 320, 530, 330, 26, "#eff0e9"),
    text("c6a", "This", 452, 282, 56, "#2a2a2a", 500),
    rect("c6h", 652, 282, 240, 82, 6, YEL),
    text("c6b", "is", 570, 283, 56, "#2a2a2a", 500),
    text("c6c", "not", 685, 283, 56, BLACK, 800),
    text("c6d", "just a card", CX, 372, 56, "#2a2a2a", 500),
])

# ---------------------------------------------------------------- chapter 7
# typeface spec sheet, giant EarnIn Mori with a slow pan
n7 = [
    solidline("t7l1", CX, 258, W, "#1a1a1a", stroke=1.5),
    solidline("t7l2", CX, 415, W, "#1a1a1a", stroke=1.5),
    solidline("t7l3", 118, CY, H, "#1a1a1a", vertical=True, stroke=1.5),
    text("t7lab", "Typeface", 186, 248, 26, BLACK, 600),
    text("t7big", "EarnIn Mori", 545, 345, 150, BLACK, 500),
]
weights = [("ExtraLight", 200), ("Light", 300), ("Regular", 400),
           ("Medium", 500)]
for i, (nm, wt) in enumerate(weights):
    s = f"EarnIn Mori   {nm}"
    n7.append(text(f"t7w{i}", s, 130 + len(s) * 17 * 0.25, 522 + i * 24,
                   17, "#1a1a1a", wt))
for i, (nm, wt) in enumerate([("SemiBold", 600), ("Bold", 700),
                              ("ExtraBold", 800)]):
    s = f"EarnIn Mori   {nm}"
    n7.append(text(f"t7b{i}", s, 330 + len(s) * 17 * 0.25, 526 + i * 26,
                   17, "#1a1a1a", wt))
scene("s7", YEL, 73, n7)
track("s7", cam_x=[(0, 70), (2.3, -70, "outCubic")])
for i in range(4):
    track(f"t7w{i}", at=0.3 + i * 0.08, opacity=[(0, 0), (0.15, 1)])
for i in range(3):
    track(f"t7b{i}", at=0.6 + i * 0.08, opacity=[(0, 0), (0.15, 1)])

# ---------------------------------------------------------------- chapter 8
# H1-H4 + Body heading scale, white on black, yellow tails
n8 = [
    solidline("t8v0", 168, CY, H, "#2e2e2e", vertical=True, stroke=1),
    solidline("t8v1", 455, CY, H, "#2e2e2e", vertical=True, stroke=1),
    solidline("t8v2", 1012, CY, H, "#2e2e2e", vertical=True, stroke=1),
]
rows = [("H1", 84, "Headi", "ng", 140), ("H2", 74, "Head", "ing", 248),
        ("H3", 62, "Hea", "ding", 350), ("H4", 52, "He", "ading", 445)]
for j, hy in enumerate((95, 192, 295, 395, 490, 585)):
    n8.append(solidline(f"t8h{j}", CX, hy, W, "#242424", stroke=1))
for i, (lab, sz, wpart, ypart, y) in enumerate(rows):
    n8.append(text(f"t8l{i}", lab, 237, y, int(sz * 0.75), "#ffffff", 700))
    ww = len(wpart) * sz * 0.5
    yw = len(ypart) * sz * 0.5
    n8.append(text(f"t8w{i}", wpart, 470 + ww / 2, y, sz, "#ffffff", 500))
    n8.append(text(f"t8y{i}", ypart, 470 + ww + yw / 2, y, sz, YEL, 500))
n8.append(text("t8l4", "Body", 237, 538, 30, "#ffffff", 700))
n8.append(text("t8y4", "Paragraph Body", 640, 538, 34, YEL, 500))
scene("s8", BLACK, 32, n8)
for i in range(5):
    for pfx in ("t8l", "t8w", "t8y"):
        nid = f"{pfx}{i}"
        if any(n["id"] == nid for n in n8):
            track(nid, at=0.05 + i * 0.06, opacity=[(0, 0), (0.12, 1)])

# ---------------------------------------------------------------- chapter 9
# "Three colors" draft build on near-black
n9 = blueprint("g9")
n9.append(text("tc1", "Three colors,", CX, 268, 96, GREY, 500))
n9.append(text("tc2", "infinite possibilities.", CX, 385, 64, "#7a7a7a", 500))
scene("s9", DRAFT, 59, n9)
reveal("tc1", 0.1, unit="type", cadence=0.06, dur=0.08)
reveal("tc2", 1.0, unit="type", cadence=0.035, dur=0.08)

# --------------------------------------------------------------- chapter 10
# yellow hero lines, then the literal swatch cards
def left_text(id, s, left, y, size, color=BLACK, weight=700):
    return text(id, s, left + len(s) * size * 0.25, y, size, color, weight)


scene("s10a", YEL, 40, [
    left_text("h10a", "Three colors,", 50, 150, 120),
    left_text("h10b", "infinite", 50, 300, 120),
    left_text("h10c", "possibilities.", 50, 450, 120),
])
for i, nid in enumerate(("h10a", "h10b", "h10c")):
    track(nid, at=i * 0.07, opacity=[(0, 0), (0.05, 1)])

scene("s10b", OW, 30, [
    rect("sw1", 189.7, CY, 379.3, H, 0, OW),
    text("sw1a", "Off White", 189, 300, 34, BLACK, 600),
    text("sw1b", "f4f5f0", 189, 350, 24, "#3a3a3a", 500),
    rect("sw2", 569, CY, 379.3, H, 0, BLACK),
    text("sw2a", "Black", 569, 300, 34, "#ffffff", 600),
    text("sw2b", "000000", 569, 350, 24, "#cfcfcf", 500),
    rect("sw3", 948.3, CY, 379.3, H, 0, YEL),
    text("sw3a", "Yellow", 948, 300, 34, BLACK, 600),
    text("sw3b", "ffe91e", 948, 350, 24, "#3a3a00", 500),
])
for i, pfx in enumerate(("sw1", "sw2", "sw3")):
    for sfx in ("", "a", "b"):
        track(pfx + sfx, at=i * 0.06, opacity=[(0, 0), (0.08, 1)])

# --------------------------------------------------------------- chapter 11
# giant Get, then the block collage
scene("s11a", OW, 15, [text("get1", "Get", CX, 330, 620, BLACK, 700)])
track("get1", scale=[(0, 1.0), (0.5, 1.04, "outCubic")])

cells = []
colw, rowh = W / 3, H / 3


def cell(cx, cy):
    return colw / 2 + cx * colw, rowh / 2 + cy * rowh


n11 = []
c = cell(0, 0)
n11 += [rect("bc0", c[0], c[1], colw, rowh, 0, YEL),
        text("bc0t", "paycheck", c[0] - 60, c[1] - 40, 22, BLACK, 500)]
c = cell(1, 0)
n11 += [rect("bc1", c[0], c[1], colw, rowh, 0, OW),
        text("bc1a", "paych", c[0] - 40, c[1] - 60, 46, BLACK, 500),
        text("bc1b", "payc", c[0] - 52, c[1], 46, BLACK, 500),
        text("bc1c", "pay", c[0] - 64, c[1] + 60, 46, BLACK, 500)]
c = cell(2, 0)
n11 += [rect("bc2", c[0], c[1], colw, rowh, 0, OW),
        text("bc2a", "This is not just a ca", c[0] + 30, c[1] - 50, 26,
             BLACK, 500, rot=-8),
        text("bc2b", "not just a card", c[0], c[1], 30, BLACK, 600, rot=-8),
        text("bc2c", "This is not just a car", c[0] + 20, c[1] + 55, 26,
             BLACK, 500, rot=-8)]
c = cell(0, 1)
n11 += [rect("bc3", c[0], c[1], colw, rowh, 0, YEL)]
for i in range(4):
    n11.append(text(f"bc3r{i}", "card  card  card", c[0], c[1] - 54 + i * 36,
                    26, BLACK, 500))
c = cell(1, 1)
n11 += [rect("bc4", c[0], c[1], colw, rowh, 0, OW),
        text("bc4t", "Get started", c[0], c[1], 40, BLACK, 700)]
c = cell(2, 1)
n11 += [rect("bc5", c[0], c[1], colw, rowh, 0, YEL),
        text("bc5t", "card", c[0], c[1], 70, BLACK, 500)]
c = cell(0, 2)
n11 += [rect("bc6", c[0], c[1], colw, rowh, 0, OW),
        text("bc6t", "card", c[0] - 60, c[1], 62, BLACK, 500)]
c = cell(1, 2)
n11 += [rect("bc7", c[0], c[1], colw, rowh, 0, YEL),
        text("bc7t", "befor", c[0] - 50, c[1] - 40, 62, BLACK, 500)]
c = cell(2, 2)
n11 += [rect("bc8", c[0], c[1], colw, rowh, 0, OW),
        text("bc8t", "paycheck", c[0], c[1], 46, "#3a3a3a", 500)]
scene("s11b", OW, 30, n11)
order = ["bc0", "bc1", "bc2", "bc3", "bc4", "bc5", "bc6", "bc7", "bc8"]
kids = {n["id"] for n in n11}
for i, b in enumerate(order):
    at = 0.02 + (i % 5) * 0.05
    for nid in sorted(kids):
        if nid.startswith(b) and (nid == b or not nid[len(b):].isdigit()):
            track(nid, at=at, opacity=[(0, 0), (0.06, 1)])

# --------------------------------------------------------------- chapter 12
# studio monitor types the sentence one word per screen
T12 = 69 / 30
n12 = [
    rect("mn_st", 569, 530, 150, 130, 8, "#9aa0a3"),
    rect("mn_bs", 569, 601, 170, 14, 6, "#8e9497"),
    rect("mn_bz", 569, 295, 662, 388, 14, "#0a0a0a"),
    rect("mn_ow", 569, 295, 632, 358, 6, OW),
    rect("mn_yl", 569, 295, 632, 358, 6, YEL),
    rect("mn_bk", 569, 295, 632, 358, 6, "#050505"),
    rect("mn_bloom", 569, 415, 260, 110, 55, YEL, blur=26),
]
bounds = [0, 0.30, 0.55, 0.80, 1.05, 1.75, T12]
slots = [(bounds[i], bounds[i + 1]) for i in range(6)]
words = ["This", "is", "not", "just", "a", "card"]
for i, wd in enumerate(words):
    col = YEL if i == 5 else BLACK
    n12.append(text(f"mn_w{i}", wd, 569, 300, 64, col, 600))
scene("s12", "#b9bdbf", 69, n12)
steps_vis("mn_yl", [(slots[4][0], slots[5][0])], T12)
steps_vis("mn_bk", [(slots[5][0], T12)], T12)
for i in range(6):
    steps_vis(f"mn_w{i}", [slots[i]], T12)
track("mn_bloom", opacity=[(0, 0.5), (slots[4][0] - 0.001, 0.7),
                           (slots[4][0], 0)],
      y=[(0, 10), (slots[4][0], -40)])

# --------------------------------------------------------------- chapter 13
# motion as textures: typed, then glitch bars, then a bloom
n13 = [
    dashline("g13v", 200, CY, H, "#c9b900", vertical=True),
    solidline("g13h", CX, 348, W, "#8a7e00", stroke=1),
    text("mt1", "Motion as textures.", CX, 315, 80, BLACK, 700),
]
scene("s13a", YEL, 40, n13)
reveal("mt1", 0.08, unit="type", cadence=0.045, dur=0.06)

import random
rng = random.Random(7)
n13b = []
for i in range(12):
    bw = rng.randint(160, 720)
    bh = rng.randint(7, 22)
    bx = rng.randint(200, 940)
    by = rng.randint(40, 600)
    fill = OW if i % 4 else YEL
    n13b.append(rect(f"gl{i}", bx, by, bw, bh, 2, fill))
    on1 = rng.uniform(0, 0.3)
    off1 = on1 + rng.uniform(0.08, 0.25)
    on2 = off1 + rng.uniform(0.05, 0.2)
    steps_vis(f"gl{i}", [(on1, off1), (on2, 0.8)], 0.8)
scene("s13b", BLACK, 24, n13b)

scene("s13c", OW, 17, [
    circle("bl13", CX, CY, 150, YEL, blur=55),
])
track("bl13", scale=[(0, 0.7), (0.55, 1.15, "outCubic")],
      opacity=[(0, 0.5), (0.3, 0.95)])

# --------------------------------------------------------------- chapter 14
# the number-grid texture: real amounts as a moving pattern
amts = ["$1,330.46      $368.06      $1,396.48      $1,266.87",
        "$136.09      $1,401.71      $853.00      $1,207.06",
        "$1,266.87      $160.09      $1,330.46      $652.00",
        "$368.06      $1,396.48      $1,401.71      $136.09",
        "$853.00      $1,207.06      $1,330.46      $1,266.87",
        "$1,401.71      $136.09      $368.06      $1,396.48",
        "$160.09      $652.00      $1,207.06      $853.00",
        "$1,330.46      $368.06      $1,396.48      $1,266.87"]
n14 = []
for i, row in enumerate(amts):
    n14.append(text(f"nr{i}", row, CX, 55 + i * 78, 28, BLACK, 500,
                    family="mono"))
    track(f"nr{i}", y=[(0, 10), (0.7, -14)])
scene("s14", YEL, 21, n14)

# --------------------------------------------------------------- chapter 15
# card-scatter shape-language field
GRAIN = "#23211a"
n15 = [
    circle("sc_bloom", 560, 210, 110, YEL, blur=40),
    rect("sc_a", 440, 90, 105, 85, 8, GRAIN),
    circle("sc_ad", 442, 55, 8, "#ffffff"),
    path("sc_ol", 594, 92, rrect_d(200, 112, 4), YEL, stroke=1.5),
    rect("sc_b", 622, 185, 115, 55, 4, GRAIN),
    rect("sc_c", 777, 212, 195, 110, 8, GRAIN),
    rect("sc_yl", 371, 187, 155, 88, 2, YEL, blur=6),
    rect("sc_yg", 583, 318, 132, 70, 3, "#d9cb1c"),
    rect("sc_pill", 289, 345, 118, 62, 6, YEL),
    circle("sc_p1", 275, 328, 9, "#ffffff"),
    circle("sc_p2", 240, 328, 7, BLACK),
    circle("sc_p3", 282, 360, 8, BLACK),
    rect("sc_d", 465, 428, 160, 100, 8, GRAIN),
    rect("sc_e", 710, 402, 200, 112, 8, GRAIN),
    circle("sc_e1", 675, 355, 9, "#ffffff"),
    circle("sc_e2", 782, 417, 10, "#ffffff"),
    rect("sc_f", 672, 540, 152, 86, 8, GRAIN),
    rect("sc_g", 425, 547, 118, 62, 3, "#171717"),
]
scene("s15", OW, 69, n15)
drift = [("sc_a", 8, 5), ("sc_b", -6, 7), ("sc_c", 9, -6), ("sc_yl", -7, 4),
         ("sc_yg", 6, -5), ("sc_pill", -5, -6), ("sc_d", 7, 6),
         ("sc_e", -8, 5), ("sc_f", 6, -7), ("sc_g", -6, 4), ("sc_ol", 5, 6)]
for i, (nid, dx, dy) in enumerate(drift):
    track(nid, at=0.015 * i, opacity=[(0, 0), (0.09, 1)],
          x=[(0, 0), (2.2, dx)], y=[(0, 0), (2.2, dy)])
track("sc_bloom", opacity=[(0, 0), (0.15, 0.5)])

# --------------------------------------------------------------- chapter 16
# toggle anatomy spec on yellow: track outline + knob state row
n16 = [
    path("an_tr", 500, 265, rrect_d(360, 130, 65), BLACK, stroke=2.5),
    circle("an_kn", 408, 265, 50, GRAIN),
    dashline("an_g1", CX, 200, W, "#b0a400"),
    dashline("an_g2", CX, 330, W, "#b0a400"),
    circle("an_s1", 420, 470, 44, "#ffffff"),
    path("an_s2", 569, 470, circle_d(44), BLACK, stroke=2),
    circle("an_s3", 718, 470, 44, BLACK, blur=9),
]
scene("s16", YEL, 14, n16)
for i, nid in enumerate(("an_s1", "an_s2", "an_s3")):
    track(nid, at=0.05 + i * 0.06, opacity=[(0, 0), (0.1, 1)],
          scale=[(0, 0.6), (0.2, 1.0, "outCubic")])
track("an_kn", x=[(0.15, 0), (0.42, 184, "outCubic")])

# --------------------------------------------------------------- chapter 17
# corner-radius connectors, then outline rects drawn on black
n17 = [
    solidline("cr_gv1", 487, CY, H, "#2c2c2c", vertical=True, stroke=1),
    solidline("cr_gv2", 651, CY, H, "#2c2c2c", vertical=True, stroke=1),
    solidline("cr_gh1", CX, 245, W, "#2c2c2c", stroke=1),
    solidline("cr_gh2", CX, 408, W, "#2c2c2c", stroke=1),
    path("cr_l1", 284, 333, "M-284 0L203 0", YEL, stroke=3),
    path("cr_l2", 568, 289, "M-81 44C-35 44 0 9 0 -44L0 -289", YEL,
         stroke=3),
    path("cr_l3", 894, 333, "M-243 0L244 0", YEL, stroke=3),
    path("cr_l4", 568, 525, "M83 -192C37 -192 0 -155 0 -115L0 115", YEL,
         stroke=3),
    circle("cr_d1", 487, 333, 8, YEL),
    circle("cr_d2", 568, 245, 8, YEL),
    circle("cr_d3", 651, 333, 8, YEL),
    circle("cr_d4", 568, 410, 8, YEL),
    text("cr_t1", "42 px", 397, 180, 24, YEL, 500),
    text("cr_t2", "42 px", 695, 388, 24, YEL, 500),
]
scene("s17a", BLACK, 60, n17)
for i, nid in enumerate(("cr_l1", "cr_l2", "cr_l3", "cr_l4")):
    track(nid, at=i * 0.03, opacity=[(0, 0), (0.07, 1)])
for i, nid in enumerate(("cr_d1", "cr_d2", "cr_d3", "cr_d4")):
    track(nid, at=0.04 + i * 0.04, scale=[(0, 0), (0.15, 1.0, "outCubic")])
for nid in ("cr_t1", "cr_t2"):
    track(nid, at=0.25, opacity=[(0, 0), (0.1, 1)])

n17b = [
    solidline("rr_gv1", 180, CY, H, "#242424", vertical=True, stroke=1),
    solidline("rr_gv2", 842, CY, H, "#242424", vertical=True, stroke=1),
    solidline("rr_gh1", CX, 170, W, "#242424", stroke=1),
    solidline("rr_gh2", CX, 470, W, "#242424", stroke=1),
    path("rr_r1", 511, 320, rrect_d(660, 292, 24), "#dfe32e", stroke=2),
    path("rr_r2", 1135, 320, rrect_d(240, 230, 20), "#dfe32e", stroke=2),
    text("rr_t1", "66 px", 250, 130, 22, "#dfe32e", 500),
]
scene("s17b", BLACK, 37, n17b)
track("rr_r1", opacity=[(0, 0), (0.15, 1)],
      scale=[(0, 0.92), (0.5, 1.0, "outCubic")])
track("rr_r2", at=0.25, opacity=[(0, 0), (0.15, 1)])
track("rr_t1", at=0.45, opacity=[(0, 0), (0.15, 1)])

# --------------------------------------------------------------- chapter 18
# tickets and takeout use-case boards, photos as gradient stand-ins
def photo(id, x, y, w, h, c1, c2, r=8):
    return rect(id, x, y, w, h, r, c1,
                gradient={"angle": 115, "stops": [{"at": 0, "color": c1},
                                                  {"at": 1, "color": c2}]})


n18 = [
    text("tk_lab", "tickets", 190, 110, 44, BLACK, 600),
    rect("tk_y", 300, 360, 300, 200, 4, YEL),
    photo("tk_p1", 660, 270, 360, 240, "#3a2c3e", "#7a4a52"),
    photo("tk_p2", 900, 440, 280, 200, "#a9c4e0", "#e8eef5"),
]
scene("s18a", OW, 40, n18)
for i, (nid, dx) in enumerate([("tk_y", -60), ("tk_p1", 70), ("tk_p2", 80)]):
    track(nid, at=0.06 + i * 0.08, opacity=[(0, 0), (0.2, 1)],
          x=[(0, dx), (0.45, 0, "outCubic")])
track("tk_lab", opacity=[(0, 0), (0.15, 1)])

n18b = [
    photo("to_p1", 145, 415, 290, 450, "#b8672f", "#e0a05c"),
    photo("to_p2", 830, 210, 500, 290, "#8a6a4e", "#c9a17a", r=10),
    rect("to_y", 415, 520, 250, 250, 2, YEL),
    text("to_t", "takeout", 905, 540, 64, BLACK, 500),
]
scene("s18b", OW, 35, n18b)
track("to_p1", opacity=[(0, 0), (0.15, 1)], x=[(0, -70), (0.4, 0, "outCubic")])
track("to_p2", at=0.08, opacity=[(0, 0), (0.15, 1)],
      x=[(0, 70), (0.4, 0, "outCubic")])
track("to_y", at=0.12, opacity=[(0, 0), (0.15, 1)])
reveal("to_t", 0.1, unit="type", cadence=0.05, dur=0.06, caret="bar")

# --------------------------------------------------------------- chapter 19
# sneakers typewriter over a blueprint, then the giant Sys
n19 = [
    dashline("g19v1", 360, CY, H, "#bdbdb5", vertical=True),
    dashline("g19v2", 787, CY, H, "#bdbdb5", vertical=True),
    dashline("g19h1", CX, 258, W, "#bdbdb5"),
    dashline("g19h2", CX, 392, W, "#bdbdb5"),
    text("snk", "sneakers", 500, 322, 72, BLACK, 500),
    photo("snk_p", 872, 470, 300, 200, "#5a5e66", "#9aa0a8"),
]
scene("s19a", OW, 50, n19)
reveal("snk", 0.15, unit="type", cadence=0.07, dur=0.06, caret="bar")
track("snk_p", at=1.0, opacity=[(0, 0), (0.2, 1)],
      y=[(0, 40), (0.35, 0, "outCubic")])

scene("s19b", YEL, 25, [text("sys", "Sys", 480, 330, 380, BLACK, 700)])
track("sys", scale=[(0, 1.0), (0.8, 1.03, "outCubic")])

# --------------------------------------------------------------- chapter 20
# systems never stand still, then the easing-curve spec
scene("s20a", YEL, 39, [
    left_text("sy1", "Systems", 55, 120, 100),
    left_text("sy2", "never stand", 55, 258, 100),
    left_text("sy3", "still.", 55, 396, 100),
])
for i, nid in enumerate(("sy1", "sy2", "sy3")):
    track(nid, at=i * 0.06, opacity=[(0, 0), (0.05, 1)])

n20b = [
    dashline("ez_gv1", 330, CY, H, "#3a3a3a", vertical=True),
    dashline("ez_gv2", 808, CY, H, "#3a3a3a", vertical=True),
    dashline("ez_gh", CX, 320, W, "#3a3a3a"),
    path("ez_card", 569, 300, rrect_d(560, 400, 18), "#e8e8e8", stroke=1.5),
    path("ez_base", 569, 420, "M-239 0L239 0", YEL, stroke=4),
    path("ez_crv", 569, 420, "M-239 0C-60 0 -20 -230 239 -252", YEL,
         stroke=3),
]
for i, lab in enumerate(("0.0", "0.23", "0.45", "1.13")):
    n20b.append(text(f"ez_n{i}", lab, 362 + i * 136, 448, 22, YEL, 500))
scene("s20b", BLACK, 36, n20b)
track("ez_base", opacity=[(0, 0), (0.12, 1)])
track("ez_crv", at=0.35, opacity=[(0, 0), (0.3, 1)])
track("ez_card", at=0.15, opacity=[(0, 0), (0.2, 1)])
for i in range(4):
    track(f"ez_n{i}", at=0.12 + i * 0.06, opacity=[(0, 0), (0.1, 1)])

# --------------------------------------------------------------- chapter 21
# stacked-bar layout demo inside an outlined card
n21 = [
    dashline("br_gv1", 112, CY, H, "#3a3a3a", vertical=True),
    dashline("br_gv2", 1026, CY, H, "#3a3a3a", vertical=True),
    dashline("br_gh1", CX, 156, W, "#3a3a3a"),
    dashline("br_gh2", CX, 480, W, "#3a3a3a"),
    path("br_card", 569, 318, rrect_d(912, 324, 14), "#dddddd", stroke=1.5),
    rect("br_1", 782, 211, 485, 102, 6, OW),
    rect("br_2", 368, 318, 508, 104, 6, YEL),
    rect("br_3", 233, 426, 240, 102, 6, OW),
]
scene("s21", BLACK, 74, n21)
track("br_1", w=[(0.8, 485), (1.1, 300, "inOutCubic"), (1.7, 420,
                                                        "inOutCubic")],
      x=[(0.8, 0), (1.1, -92, "inOutCubic"), (1.7, -30, "inOutCubic")])
track("br_2", w=[(0.9, 508), (1.2, 640, "inOutCubic"), (1.8, 380,
                                                        "inOutCubic")],
      x=[(0.9, 0), (1.2, 66, "inOutCubic"), (1.8, -60, "inOutCubic")])
track("br_3", w=[(1.0, 240), (1.3, 400, "inOutCubic"), (1.9, 300,
                                                        "inOutCubic")],
      x=[(1.0, 0), (1.3, 80, "inOutCubic"), (1.9, 30, "inOutCubic")])

# --------------------------------------------------------------- chapter 22
# it's a card tag with a trail, then the weight ladder
n22 = [
    path("ia_bd", 569, 300, rrect_d(620, 320, 18), YEL, stroke=3),
    text("ia_t", "It's a", 520, 300, 90, BLACK, 600),
    rect("ia_tag", 700, 392, 150, 64, 32, YEL,
         streak={"samples": 5, "window": 0.06, "gain": 0.5}),
    text("ia_tt", "card", 700, 393, 30, BLACK, 600),
]
scene("s22a", OW, 38, n22)
track("ia_bd", opacity=[(0, 1), (0.3, 1), (0.45, 0)])
for nid in ("ia_tag", "ia_tt"):
    track(nid, at=0.45, opacity=[(0, 0), (0.05, 1)],
          x=[(0, 430), (0.5, 0, "outCubic")],
          y=[(0, -300), (0.5, 0, "outCubic")])

lads = [(300, 65), (600, 180), (800, 300), (500, 420), (300, 540)]
n22b = []
for i, (wt, y) in enumerate(lads):
    n22b.append(text(f"lad{i}", "It's also a", 569, y, 78, "#161616", wt))
    track(f"lad{i}", at=0.05 + i * 0.07, opacity=[(0, 0), (0.12, 1)],
          y=[(0, 34), (0.3, 0, "outCubic")])
scene("s22b", OW, 38, n22b)

# --------------------------------------------------------------- chapter 23
# hours later? wall, then the say hello ladder
n23 = [path("hr_bd", 569, 320, rrect_d(600, 100, 10), YEL, stroke=3)]
for i in range(5):
    wt = 800 if i == 2 else 500
    n23.append(text(f"hr{i}", "hours later?", 569, 90 + i * 115, 72,
                    "#161616", wt))
    track(f"hr{i}", at=0.05 + i * 0.06, opacity=[(0, 0), (0.1, 1)])
scene("s23a", OW, 40, n23)
track("hr_bd", opacity=[(0.35, 0), (0.5, 1)])

n23b = []
for i, (wt, y, sz) in enumerate([(700, 185, 96), (400, 320, 96),
                                 (200, 452, 96)]):
    n23b.append(text(f"sh{i}", "Say hello", 490, y, sz, "#161616", wt))
    track(f"sh{i}", at=0.05 + i * 0.08, opacity=[(0, 0), (0.15, 1)],
          y=[(0, 44), (0.4, 0, "outCubic")])
scene("s23b", OW, 34, n23b)

# --------------------------------------------------------------- chapter 24
# giant Built glyph build, then built to scale on the blueprint
scene("s24a", OW, 27, [text("blt", "Built", 569, 330, 300, BLACK, 700)])
reveal("blt", 0.02, unit="type", cadence=0.16, dur=0.04, caret="bar")

n24 = [
    dashline("g24v1", 360, CY, H, "#bdbdb5", vertical=True),
    dashline("g24v2", 787, CY, H, "#bdbdb5", vertical=True),
    dashline("g24h1", CX, 258, W, "#bdbdb5"),
    dashline("g24h2", CX, 392, W, "#bdbdb5"),
    circle("dot1", 112, 102, 105, YEL),
    circle("dot2", 895, 525, 105, YEL),
    circle("dot3", 1090, 525, 105, YEL),
    text("bts1", "Built", 428, 290, 84, BLACK, 600),
    text("bts2", "to scale.", 470, 372, 84, BLACK, 600),
]
scene("s24b", OW, 48, n24)
reveal("bts2", 0.15, unit="type", cadence=0.06, dur=0.05, caret="bar")
for i, nid in enumerate(("dot1", "dot2", "dot3")):
    track(nid, at=0.2 + i * 0.14, scale=[(0, 0.2), (0.35, 1.0, "outCubic")],
          opacity=[(0, 0), (0.08, 1)])

# --------------------------------------------------------------- chapter 25
# instagram-style post cards slide across a black canvas
n25 = [
    solidline("ph_gv1", 218, CY, H, "#2e2e2e", vertical=True, stroke=1),
    solidline("ph_gv2", 536, CY, H, "#2e2e2e", vertical=True, stroke=1),
    solidline("ph_gv3", 855, CY, H, "#2e2e2e", vertical=True, stroke=1),
]
cards25 = []


def post(pfx, x, body):
    ns = [rect(f"{pfx}_c", x, 318, 285, 364, 4, OW),
          circle(f"{pfx}_av", x - 118, 155, 11, BLACK),
          text(f"{pfx}_nm", "Earnin", x - 72, 155, 16, BLACK, 600),
          circle(f"{pfx}_h", x - 110, 478, 6, "#2a2a2a"),
          circle(f"{pfx}_cm", x - 86, 478, 6, "#2a2a2a"),
          circle(f"{pfx}_sv", x + 114, 478, 6, "#2a2a2a")]
    ns += body(x)
    cards25.append([n["id"] for n in ns])
    return ns


n25 += post("p1", 150, lambda x: [
    rect("p1_y", x - 60, 260, 120, 130, 2, YEL),
    text("p1_t", "payro", x + 40, 322, 26, BLACK, 500)])
n25 += post("p2", 460, lambda x: [
    rect("p2_bk", x, 315, 265, 285, 2, "#0c0c0c"),
    text("p2_t1", "just", x - 55, 315, 26, "#ffffff", 500),
    rect("p2_tag", x + 62, 315, 92, 44, 4, YEL),
    text("p2_t2", "ca", x + 62, 316, 24, BLACK, 600)])
n25 += post("p3", 770, lambda x: [
    path("p3_ck1", x - 92, 318, circle_d(34), BLACK, stroke=2.5),
    path("p3_ck2", x + 92, 318, circle_d(34), BLACK, stroke=2.5),
    text("p3_t1", "clock in", x, 305, 24, BLACK, 500),
    text("p3_t2", "when you", x, 338, 24, BLACK, 600)])
n25 += post("p4", 1080, lambda x: [
    photo("p4_ph", x - 50, 290, 130, 120, "#b8672f", "#e0a05c", r=4),
    rect("p4_y", x + 40, 360, 110, 90, 2, YEL),
    text("p4_t", "takeo", x + 60, 300, 24, BLACK, 500)])
scene("s25", BLACK, 76, n25)
for ids in cards25:
    for nid in ids:
        track(nid, x=[(0, 170), (2.45, -150, "outCubic")])

# --------------------------------------------------------------- chapter 26
# gallery-wall monitor render with the eclipse disc
n26 = []
for i in range(13):
    n26.append(solidline(f"wd{i}", 45 + i * 95, 280, 560, "#6a4a35",
                         vertical=True, stroke=2))
n26 += [
    rect("wd_fl", CX, 600, W, 80, 0, "#cfc4b6"),
    rect("wd_sh1", 260, 180, 300, 200, 60, "#4a3020", blur=60),
    rect("wd_sh2", 900, 480, 320, 180, 60, "#4a3020", blur=70),
    rect("gal_fr", 600, 248, 646, 370, 4, "#111111"),
    rect("gal_sc", 600, 248, 622, 346, 2, "#f6f5ee"),
    circle("gal_ec", 884, 240, 152, "#0b0b0b",
           glow={"sigma": 26, "opacity": 1.0, "color": YEL}),
    text("gal_cd1", "$1,207.06  $853.0", 884, 200, 11, "#5daa5d", 400,
         family="mono"),
    text("gal_cd2", "$1,330.46  $160.0", 878, 260, 11, "#5daa5d", 400,
         family="mono"),
    left_text("gal_t1", "to the", 385, 182, 46, "#111111", 500),
    left_text("gal_t2", "get your", 385, 244, 46, "#111111", 500),
    left_text("gal_t3", "earnings", 385, 308, 46, "#111111", 500),
    rect("st1", 165, 572, 70, 85, 4, "#b98d63"),
    rect("st2", 258, 578, 75, 78, 4, "#a87c52"),
]
scene("s26", "#7d5a42", 75, n26)
reveal("gal_t3", 0.5, unit="scramble", cadence=0.07, churn=4)
track("gal_ec", scale=[(0, 0.96), (2.4, 1.0, "outCubic")])

# --------------------------------------------------------------- chapter 27
# every spec sheet flies together, with a cursor
n27 = [
    rect("cl_1", 700, 92, 330, 180, 12, YEL),
    text("cl_1t", "sha", 610, 60, 30, BLACK, 600),
    path("cl_1g", 740, 105, rrect_d(140, 62, 31), BLACK, stroke=2),
    rect("cl_2", 360, 196, 300, 190, 14, "#0d0d0d"),
    path("cl_2c", 360, 205, "M-110 60C-30 60 -10 -48 110 -55", YEL,
         stroke=2),
    rect("cl_3", 822, 260, 345, 215, 16, "#0d0d0d"),
    path("cl_3c", 822, 265, circle_d(85), "#dfe32e", stroke=1.5),
    text("cl_3a", "92.3", 878, 185, 16, "#dfe32e", 500),
    text("cl_3b", "101.25", 725, 272, 16, "#dfe32e", 500),
    rect("cl_4", 330, 322, 260, 120, 10, "#0d0d0d"),
    text("cl_4t", "$1500", 330, 322, 44, YEL, 700),
    rect("cl_5", 448, 555, 230, 190, 10, "#0d0d0d"),
    text("cl_5a", "H1  Heading", 448, 515, 26, "#ffffff", 700),
    text("cl_5b", "H2  Heading", 448, 558, 24, "#ffffff", 600),
    text("cl_5c", "H3  Heading", 448, 598, 22, "#ffffff", 500),
    rect("cl_6", 690, 590, 330, 130, 8, YEL),
    text("cl_6a", "Typeface", 600, 558, 14, BLACK, 500),
    text("cl_6b", "EarnIn Mori", 690, 600, 42, BLACK, 700),
    path("cl_7", 872, 462, rrect_d(330, 200, 8), "#c9c9c0", stroke=1.5),
    text("cl_7a", "Designing a", 862, 438, 28, "#111111", 600),
    text("cl_7b", "Visual System", 870, 474, 28, "#111111", 600),
    {"id": "cl_cur", "type": "cursor", "x": 772, "y": 500, "w": 26,
     "fill": "#111111"},
]
scene("s27", OW, 54, n27)
flights = [("cl_1", 0, -260), ("cl_1t", 0, -260), ("cl_1g", 0, -260),
           ("cl_2", -320, 0), ("cl_2c", -320, 0),
           ("cl_3", 320, -80), ("cl_3a", 320, -80), ("cl_3b", 320, -80),
           ("cl_4", -300, 60), ("cl_4t", -300, 60),
           ("cl_5", -120, 280), ("cl_5a", -120, 280), ("cl_5b", -120, 280),
           ("cl_5c", -120, 280),
           ("cl_6", 80, 300), ("cl_6a", 80, 300), ("cl_6b", 80, 300),
           ("cl_7", 340, 120), ("cl_7a", 340, 120), ("cl_7b", 340, 120)]
for i, (nid, dx, dy) in enumerate(flights):
    track(nid, at=0.03 * (i % 7), opacity=[(0, 0), (0.12, 1)],
          x=[(0, dx), (0.55, 0, "outCubic")],
          y=[(0, dy), (0.55, 0, "outCubic")])
track("cl_cur", at=0.7, opacity=[(0, 0), (0.1, 1)],
      x=[(0, 60), (0.7, 0, "outCubic")], y=[(0, 40), (0.7, 0, "outCubic")])

# --------------------------------------------------------------- chapter 28
# the bookend: toggle slides once more, logo settles on yellow
scene("s28a", BLACK, 16, [
    rect("tg3", CX, 320, 350, 135, 67, YEL),
    circle("tk3", 462, 320, 52, BLACK),
])
track("tk3", x=[(0.05, 0), (0.4, 214, "outCubic")])

scene("s28b", YEL, 96, [
    rect("lg2", CX, 318, 372, 142, 71, BLACK),
    circle("lk2", 688, 318, 62, "#ffffff"),
    text("lgt2", "earn", 512, 320, 86, "#ffffff", 600),
    text("lgi2", "in", 688, 320, 58, BLACK, 700),
])
for nid in ("lg2", "lk2", "lgt2", "lgi2"):
    track(nid, scale=[(0, 1.07), (0.5, 1.0, "outCubic")])

stage = {"fps": 30, "size": [W, H], "scenes": scenes,
         "audio": {"src": "/assets/audio/pad.m4a", "gain": 0.6,
                   "fade_out": 0.8}}
with open("docs/state-slim.stage.json", "w") as f:
    json.dump(stage, f, indent=1)
with open("docs/state-slim.anim.json", "w") as f:
    json.dump({"tracks": tracks}, f, indent=1)
total = sum(s["dur"] for s in scenes)
frames = sum(round(s["dur"] * 30) for s in scenes)
print("wrote docs/state-slim.{stage,anim}.json,",
      sum(len(s["nodes"]) for s in scenes), "nodes,", len(tracks),
      f"tracks, {total:.2f}s, {frames} frames")
