#!/usr/bin/env python3
# reproduction of radio/sunflower (6.85s, 1080x1080): the message-effect
# tool. phase 1 is the split editor — grey wireframe canvas + live color
# preview scrubbing off one pinned-playhead timeline — building three
# imessage effects (hey / bang / bb); the one hard cut promotes the comp
# to fullscreen and the three effects replay full-bleed. silent source.
# emoji are drawn cartoon paths (the real clip uses apple glyphs).
import json
import math
import os

W, H = 1080, 1080
F = 1 / 60  # ledger frames are 60fps

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
K = 0.5523

nodes, tracks = [], []


def rect(id, x, y, w, h, r, fill, **kw):
    n = {"id": id, "type": "rect", "x": x, "y": y, "w": w, "h": h,
         "radius": r, "fill": fill}
    n.update(kw)
    nodes.append(n)
    return n


def text(id, s, x, y, size, color, weight=700):
    n = {"id": id, "type": "text", "text": s, "x": x, "y": y, "color": color,
         "font": {"size": size, "weight": weight}}
    nodes.append(n)
    return n


def path(id, x, y, d, fill, **kw):
    n = {"id": id, "type": "path", "x": x, "y": y, "d": d, "fill": fill}
    n.update(kw)
    nodes.append(n)
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


def circle_d(r, cx=0, cy=0):
    k = r * K
    return (f"M{cx-r} {cy}C{cx-r} {cy-k} {cx-k} {cy-r} {cx} {cy-r}"
            f"C{cx+k} {cy-r} {cx+r} {cy-k} {cx+r} {cy}"
            f"C{cx+r} {cy+k} {cx+k} {cy+r} {cx} {cy+r}"
            f"C{cx-k} {cy+r} {cx-r} {cy+k} {cx-r} {cy}Z")


# cartoon emoji, ~1.0 unit radius, scaled per instance via node scale keys
def sun_d():
    d = circle_d(30)
    for i in range(8):
        a = i * math.pi / 4
        x0, y0 = 36 * math.cos(a), 36 * math.sin(a)
        x1, y1 = 48 * math.cos(a), 48 * math.sin(a)
        px, py = -math.sin(a) * 4, math.cos(a) * 4
        d += (f"M{x0+px:.1f} {y0+py:.1f}L{x1:.1f} {y1:.1f}"
              f"L{x0-px:.1f} {y0-py:.1f}Z")
    return d


def face_holes_d():
    return (circle_d(4, -10, -6) + circle_d(4, 10, -6)
            + "M-12 10C-6 18 6 18 12 10C6 14 -6 14 -12 10Z")


def hand_d():
    return ("M-16 24L-16 -2C-16 -8 -8 -8 -8 -2L-8 -14C-8 -20 0 -20 0 -14"
            "L0 -18C0 -24 8 -24 8 -18L8 -8C8 -12 16 -12 16 -6L16 24"
            "C16 30 -16 30 -16 24Z")


def frog_d():
    return circle_d(30) + circle_d(9, -14, -26) + circle_d(9, 14, -26)


def alien_d():
    return ("M-24 -8C-24 -30 24 -30 24 -8C24 12 10 28 0 28C-10 28 -24 12 -24 -8Z")


def dog_d():
    return (circle_d(28) + "M-34 -18C-40 2 -34 10 -26 8L-22 -16Z"
            "M34 -18C40 2 34 10 26 8L22 -16Z")


def bouquet_d():
    d = "M-26 20L0 70L26 20Z"
    for cx, cy, r in [(-20, -6, 13), (0, -18, 14), (20, -6, 13),
                      (-10, 8, 11), (10, 8, 11)]:
        d += circle_d(r, cx, cy)
    return d


EMOJI = {
    "sun": (sun_d, "#f5a623"), "face": (face_holes_d, "#7a5410"),
    "hand": (hand_d, "#f0b98d"), "frog": (frog_d, "#5cb85c"),
    "alien": (alien_d, "#b9dcae"), "dog": (dog_d, "#c98a4b"),
    "bouquet": (bouquet_d, "#e46fa0"),
}

# effect definitions: bg gradient, bubble, emoji layout
FX = {
    "hey": {
        "bg": ("#f7c735", "#e5e5e5"),
        "bubble": ("#2d2d2f", "hey", "#f9f7fc"),
        "bubble_at": (0.0, 0.30),      # x,y fractions of region (from center)
        "emoji": [("sun", -0.30, 0.02, 1.3), ("face", -0.30, 0.02, 1.3),
                  ("sun", 0.26, -0.22, 1.0), ("face", 0.26, -0.22, 1.0),
                  ("sun", 0.05, 0.34, 0.8), ("face", 0.05, 0.34, 0.8),
                  ("hand", -0.36, 0.36, 0.9), ("hand", 0.38, 0.30, 0.9),
                  ("sun", 0.36, 0.10, 0.6), ("face", 0.36, 0.10, 0.6)],
        "rise": (0.0, 0.55), "hold_to": 0.82, "exit": (0.82, 1.07),
    },
    "bang": {
        "bg": ("#4ca646", "#e9f2e6"),
        "bubble": ("#fafafa", "bang", "#1a1a1a"),
        "bubble_at": (-0.10, -0.05),
        "emoji": [(kind, 0.34 * math.cos(a), 0.34 * math.sin(a), 0.75)
                  for i, (kind, a) in enumerate(
                      [(k, math.pi / 2 + i * 2 * math.pi / 8)
                       for i, k in enumerate(
                           ["frog", "alien", "dog", "frog", "alien",
                            "dog", "frog", "alien"])])],
        "rise": (0.12, 0.75), "hold_to": 1.0, "exit": (1.0, 1.25),
    },
    "bb": {
        "bg": ("#e65888", "#f6eef1"),
        "bubble": ("#e02e5e", "bb", "#fffdfa"),
        "bubble_at": (0.0, 0.30),
        "emoji": [("bouquet", 0.0, -0.05, 2.4)],
        "rise": (0.02, 0.55), "hold_to": 0.90, "exit": (0.90, 1.20),
    },
}


def build_effect(prefix, fx_name, cx, cy, rw, rh, t0, wire=False):
    """one effect instance inside region (cx,cy,rw,rh), starting at t0
    scene-local. wire renders everything grey (the authoring canvas)."""
    fx = FX[fx_name]
    top, bot = fx["bg"]
    r0, r1 = fx["rise"]
    e0, e1 = fx["exit"]
    if not wire:
        bg = rect(f"{prefix}_bg", cx, cy, rw, rh, 34, top,
                  gradient={"angle": 90, "stops": [
                      {"at": 0, "color": top}, {"at": 1, "color": bot}]})
        track(bg["id"], at=t0, opacity=[(-0.02, 0), (0.02, 1),
                                        (e1 + 0.02, 1), (e1 + 0.06, 0)])
    rise_px = rh * 0.55
    for i, (kind, fx_, fy_, sc) in enumerate(fx["emoji"]):
        dfn, col = EMOJI[kind]
        col = "#b5b5b5" if wire and kind != "face" else \
              ("#8f8f8f" if wire else col)
        n = path(f"{prefix}_e{i}", round(cx + fx_ * rw, 1),
                 round(cy + fy_ * rh, 1), dfn(), col)
        n["keys"] = {"scale": [{"t": 0, "v": sc * rw / 420}]}
        stag = (i % 5) * 0.06
        track(n["id"], at=t0,
              y=[(r0 + stag, rise_px), (r1 + stag, 0, "outCubic"),
                 (e0, -14), (e1, -rise_px * 1.7, "inCubic")],
              opacity=[(-0.02, 0), (r0 + stag, 0), (r0 + stag + 0.12, 1),
                       (e1 - 0.04, 1), (e1, 0)])
    bfill, blabel, bink = fx["bubble"]
    bx = cx + fx["bubble_at"][0] * rw
    by = cy + fx["bubble_at"][1] * rh
    bw, bh = rw * 0.42, rh * 0.155
    bub = rect(f"{prefix}_bub", round(bx, 1), round(by, 1), round(bw, 1),
               round(bh, 1), round(bh / 2, 1),
               "#a8a8a8" if wire else bfill)
    lbl = text(f"{prefix}_lbl", blabel, round(bx, 1), round(by + 1, 1),
               round(bh * 0.52, 1), "#7a7a7a" if wire else bink)
    for n in (bub, lbl):
        track(n["id"], at=t0,
              y=[(r0 + 0.10, rise_px), (r1 + 0.05, 0, "outCubic"),
                 (e0, -20), (e1, -rise_px * 1.9, "inCubic")],
              scale=[(r0 + 0.10, 0.7), (r1 + 0.05, 1.0, "outCubic")],
              opacity=[(-0.02, 0), (r0 + 0.10, 0), (r0 + 0.20, 1),
                       (e1 - 0.03, 1), (e1, 0)])


# ---------------------------------------------------------------- phase 1
# split editor on flat grey. left wireframe card, right live preview,
# pinned-playhead timeline below. effect starts at f-ledger times.
S1 = 212 * F   # 3.533
PREV = (770, 470, 380, 620)    # right preview card center + size
WIRE = (300, 470, 380, 620)
sc1_pre = [
    rect("ed_wire_card", *WIRE[:2], WIRE[2] + 28, WIRE[3] + 28, 40, "#ebebeb"),
    rect("ed_prev_card", *PREV[:2], PREV[2] + 28, PREV[3] + 28, 40, "#ebebeb"),
]
starts = {"hey": 0.0, "bang": 65 * F, "bb": 141 * F}
for name, at in starts.items():
    build_effect(f"w_{name}", name, WIRE[0], WIRE[1], WIRE[2], WIRE[3],
                 at, wire=True)
    build_effect(f"p_{name}", name, PREV[0], PREV[1], PREV[2], PREV[3], at)

# selection bounds + lock on the wireframe card
sel = path("ed_sel", WIRE[0], WIRE[1] + 90,
           "M-100 -55L100 -55L100 55L-100 55Z", "#e16622", stroke=1.6)
track("ed_sel",
      y=[(0, 0), (65 * F, 0), (75 * F, -95, "outCubic"),
         (141 * F, -95), (150 * F, 60, "outCubic"), (165 * F, -60, "outCubic")],
      h=[(0, 110)],
      opacity=[(0, 1)])
path("ed_lock", WIRE[0] + 150, WIRE[1] + 270,
     "M-9 0L9 0L9 14L-9 14ZM-5 0L-5 -6C-5 -13 5 -13 5 -6L5 0",
     "#8a8a8a", stroke=2.0)

# timeline strip: play pill, pinned playhead + glow, scrolling ruler,
# keyframe chips, hatch gaps
rect("tl_pill", 108, 950, 110, 56, 28, "#ffffff")
path("tl_play", 88, 950, "M-8 -10L8 0L-8 10Z", "#1d1d1d")
path("tl_bars", 122, 950, "M-4 -9L-4 9M4 -9L4 9", "#1d1d1d", stroke=3.0)
ruler_ids = []
for i in range(8):
    n = text(f"tl_n{i}", str(i), 260 + i * 150, 918, 20, "#9a9a9a", weight=400)
    ruler_ids.append(n["id"])
chips = ["#1d1d1d"] * 12
chip_ids = []
for i in range(12):
    n = rect(f"tl_c{i}", 300 + i * 92, 972, 56, 40, 10, "#1d1d1d")
    chip_ids.append(n["id"])
for i in range(3):
    n = rect(f"tl_h{i}", 560 + i * 380, 972, 60, 40, 8, "#c9c9c9")
    chip_ids.append(n["id"])
# everything in the strip scrolls left under the pinned playhead:
# ruler runs 0..7 over ~7.4 tool-seconds mapped onto our 3.53s phase
SCROLL = -150 * 4 / (212 * F)
for nid in ruler_ids + chip_ids:
    track(nid, x=[(0, 0), (S1, SCROLL * S1)])
    track(nid, at=0, opacity=[(0, 1), (S1 - 0.02, 1), (S1, 0)])
rect("tl_head", 240, 950, 4, 110, 2, "#e16622",
     glow={"sigma": 9, "opacity": 0.8, "color": "#cadb52", "dy": 46})
for i, at in enumerate([8 * F, 66 * F, 142 * F]):
    n = rect(f"tl_k{i}", 240, 1002, 14, 14, 7, "#cadb52")
    track(n["id"], at=at, opacity=[(-0.02, 0), (0.02, 1), (0.30, 0)])

# phase-1 chrome dies at the cut
for nid in ["ed_wire_card", "ed_prev_card", "ed_sel", "ed_lock", "tl_pill",
            "tl_play", "tl_bars", "tl_head"]:
    track(nid, at=0, opacity=[(0, 1), (S1 - 0.001, 1), (S1, 0)])

# ---------------------------------------------------------------- phase 2
# fullscreen replay of the three effects
starts2 = {"hey": 213 * F, "bang": 274 * F, "bb": 350 * F}
for name, at in starts2.items():
    build_effect(f"f_{name}", name, 540, 540, 1080, 1080, at)

stage = {
    "fps": 30,
    "size": [W, H],
    "scenes": [
        {"id": "s", "bg": "#d2d2d2", "dur": 6.85,
         "transition": {"kind": "cut"}, "nodes": nodes},
    ],
}

with open("docs/sunflower.stage.json", "w") as f:
    json.dump(stage, f, indent=1)
with open("docs/sunflower.anim.json", "w") as f:
    json.dump({"tracks": tracks}, f, indent=1)
print("wrote docs/sunflower.{stage,anim}.json,", len(nodes), "nodes,",
      len(tracks), "tracks")
