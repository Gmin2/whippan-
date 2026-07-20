#!/usr/bin/env python3
# reproduction of radio/crab (4.967s, 1080x1080): "coming soon" 3D landing
# page. act one is the page — blurred COMING SOON, glowing "?" badge with
# sparkles, email capture, click opens the info card, crab walks in at the
# right edge. one hard cut at f161, then act two: the crab is a draggable
# ragdoll on an elastic orange tether. the 3D low-poly crab becomes a drawn
# 2D cartoon (body polygon + capsule limbs); the drag physics are simulated
# here (slack-elastic body spring + under-damped limb springs) and baked as
# dense keys so the overshoot is real. silent source, timings from the
# 60fps frame ledger.
import json
import math
import os

W, H = 1080, 1080
F = 1 / 60
K = 0.5523

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

s1_nodes, s2_nodes, tracks = [], [], []
cur_nodes = s1_nodes


def rect(id, x, y, w, h, r, fill, **kw):
    n = {"id": id, "type": "rect", "x": round(x, 1), "y": round(y, 1),
         "w": round(w, 1), "h": round(h, 1), "radius": r, "fill": fill}
    n.update(kw)
    cur_nodes.append(n)
    return n


def text(id, s, x, y, size, color, weight=700, **kw):
    n = {"id": id, "type": "text", "text": s, "x": round(x, 1),
         "y": round(y, 1), "color": color,
         "font": {"size": round(size, 1), "weight": weight}}
    n.update(kw)
    cur_nodes.append(n)
    return n


def path(id, x, y, d, fill, **kw):
    n = {"id": id, "type": "path", "x": round(x, 1), "y": round(y, 1),
         "d": d, "fill": fill}
    n.update(kw)
    cur_nodes.append(n)
    return n


def set_static(n, **props):
    # static per-node values (opacity, scale) via stage keys
    ks = n.setdefault("keys", {})
    for name, v in props.items():
        ks[name] = [{"t": 0, "v": v}]
    return n


def track(nid, at=0.0, **props):
    keys = {}
    for name, seq in props.items():
        out = []
        for k in seq:
            kk = {"t": round(k[0], 4), "v": round(k[1], 2)}
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
    return (f"M{cx-r:.1f} {cy:.1f}C{cx-r:.1f} {cy-k:.1f} {cx-k:.1f} {cy-r:.1f} {cx:.1f} {cy-r:.1f}"
            f"C{cx+k:.1f} {cy-r:.1f} {cx+r:.1f} {cy-k:.1f} {cx+r:.1f} {cy:.1f}"
            f"C{cx+r:.1f} {cy+k:.1f} {cx+k:.1f} {cy+r:.1f} {cx:.1f} {cy+r:.1f}"
            f"C{cx-k:.1f} {cy+r:.1f} {cx-r:.1f} {cy+k:.1f} {cx-r:.1f} {cy:.1f}Z")


def grid_d(x0, x1, y0, y1, step):
    d = ""
    x = x0
    while x <= x1:
        d += f"M{x} {y0}L{x} {y1}"
        x += step
    y = y0
    while y <= y1:
        d += f"M{x0} {y}L{x1} {y}"
        y += step
    return d


def star_d(r):
    a = r * 0.16
    return (f"M0 {-r}C{a} {-a} {a} {-a} {r} 0C{a} {a} {a} {a} 0 {r}"
            f"C{-a} {a} {-a} {a} {-r} 0C{-a} {-a} {-a} {-a} 0 {-r}Z")


# pointing-hand cursor: index finger up + palm; drawn as fill union
HAND_D = ("M-5 -26C-5 -32 5 -32 5 -26L5 -2L-5 -2Z"
          "M-16 2C-16 -6 -5 -7 -5 0L-5 -2L14 -2C22 -2 26 3 26 10"
          "C26 19 19 26 9 26L-4 26C-12 26 -16 19 -16 12Z")
HAND_LINES = "M5 -1L5 9M13 0L13 9M20 3L20 9"
# closed grabbing fist
FIST_D = ("M-17 -2C-17 -16 17 -16 17 -2L17 7C17 18 -17 18 -17 7Z")
FIST_LINES = "M-8 -6L-8 3M0 -7L0 3M8 -6L8 3"


def cursor_group(prefix, x, y, kind, scale=1.0):
    d = HAND_D if kind == "hand" else FIST_D
    lines = HAND_LINES if kind == "hand" else FIST_LINES
    o = path(f"{prefix}_o", x, y, d, "#1c1c1e")
    o["keys"] = {"scale": [{"t": 0, "v": 1.17 * scale}]}
    f = path(f"{prefix}_f", x, y, d, "#ffffff")
    f["keys"] = {"scale": [{"t": 0, "v": scale}]}
    l = path(f"{prefix}_l", x, y, lines, "#1c1c1e", stroke=2.0)
    l["keys"] = {"scale": [{"t": 0, "v": scale}]}
    return [o["id"], f["id"], l["id"]]


# ------------------------------------------------------------------ scene 1
# the coming-soon page, laid out at full-page framing; the camera does the
# zoomed-in hook, the crash zoom-out, and the push-in to the info card.
S1 = 160 * F

rect("p_wash", 540, 470, 2400, 2200, 0, "#e9e9ec", gradient={
    "angle": 90, "stops": [{"at": 0, "color": "#e6e6ea"},
                           {"at": 0.5, "color": "#f8f8fa"},
                           {"at": 1, "color": "#fefefe"}]})
set_static(path("p_grid", 540, 540, grid_d(-940, 1480, -940, 1480, 74),
                "#ececef", stroke=1.0), opacity=0.6)

# blurred hero type: main + offset ghosts fake the permanent defocus
for gid, s, x, y in [("com", "COMING", 511, 372), ("soon", "SOON", 487, 564)]:
    for i, (dx, dy, op) in enumerate([(-6, 0, 0.22), (6, 3, 0.22),
                                      (0, 0, 0.85)]):
        n = text(f"h_{gid}{i}", s, x + dx, y + dy, 225, "#d8d7dc", weight=900)
        set_static(n, opacity=op)

# small inert "?" badge clipped at the far left of COMING
rect("b2_card", 35, 378, 84, 84, 24, "#ffffff",
     glow={"sigma": 14, "opacity": 0.25, "color": "#b9bcc9", "dy": 6})
text("b2_q", "?", 35, 380, 46, "#c5c5cc", weight=800)

# the interactive "?" badge at the right end of SOON
rect("b1_halo", 865, 565, 150, 150, 46, "#b9c4fb", blur=26)
track("b1_halo", opacity=[(0, 0), (4 * F, 0), (12 * F, 0.9, "outCubic"),
                          (40 * F, 0.75), (70 * F, 0.55), (88 * F, 0.5),
                          (96 * F, 0)])
rect("b1_card", 865, 565, 94, 94, 27, "#ffffff",
     glow={"sigma": 16, "opacity": 0.3, "color": "#aeb4cf", "dy": 7})
q_grey = text("b1_qg", "?", 865, 567, 52, "#b9b9c0", weight=800)
q_ind = text("b1_qi", "?", 865, 567, 52, "#6472f0", weight=800)
track("b1_qg", opacity=[(0, 1), (4 * F, 1), (11 * F, 0)])
track("b1_qi", opacity=[(0, 0), (4 * F, 0), (11 * F, 1), (90 * F, 1),
                        (96 * F, 0)])

# sparkle burst around the badge: teal + blue 4-point stars
SPARKS = [(-58, -48, 17, "#4fd6c4", 0.00), (-72, -18, 12, "#5b8def", 0.05),
          (-40, -66, 9, "#7fe3d4", 0.08), (62, -30, 13, "#4fd6c4", 0.03),
          (52, 28, 10, "#5b8def", 0.10), (74, 6, 8, "#4fd6c4", 0.13)]
for i, (dx, dy, r, col, dl) in enumerate(SPARKS):
    n = path(f"sp{i}", 865 + dx, 565 + dy, star_d(r), col)
    t0 = 4 * F + dl
    tw = []
    tt = t0 + 0.22
    v = 1.0
    while tt < 60 * F:
        v = 0.78 if v == 1.0 else 1.0
        tw.append((tt, v, "inOutCubic"))
        tt += 0.14
    track(n["id"],
          scale=[(t0, 0.0), (t0 + 0.18, 1.18, "outCubic"),
                 (t0 + 0.30, 1.0, "inOutCubic")] + tw,
          opacity=[(0, 0), (t0, 0), (t0 + 0.1, 1), (55 * F, 1), (72 * F, 0)])

text("cap", "Want to learn how to add 3D to your websites?", 511, 690,
     23, "#6d6d72", weight=500)

# email capture row
rect("em_card", 511, 765, 572, 78, 30, "#ffffff",
     glow={"sigma": 18, "opacity": 0.22, "color": "#b7bac6", "dy": 8})
rect("em_border", 421, 765, 358, 56, 15, "#d7d7dd")
rect("em_input", 421, 765, 355, 53, 14, "#ffffff")
text("em_ph", "Enter your email", 343, 766, 20, "#a3a3ab", weight=400)
rect("em_btn", 696, 765, 168, 56, 28, "#5876fc")
path("em_pl_c", 634, 765, circle_d(13), "#7e93fd")
path("em_pl", 634, 765, "M-6 3L7 -4L0 6L-2 2Z", "#ffffff")
text("em_btnt", "Get notified", 714, 766, 21, "#ffffff", weight=600)

# click flash on the badge at f88: a 2-frame diagonal streak
fl = rect("b1_flash", 865, 565, 120, 26, 13, "#ffffff", rot=-38)
track("b1_flash", opacity=[(0, 0), (87 * F, 0), (88 * F, 0.9),
                           (91 * F, 0)])

# info card materializes out of the push-in (page-space, small: the camera
# is at 1.9x when it is up)
CX, CY = 855, 555
card = rect("cd", CX, CY, 354, 140, 14, "#ffffff",
            glow={"sigma": 20, "opacity": 0.25, "color": "#b0b3c2", "dy": 8})
card_kids = []


def cd_text(id, s, x, y, size, color, weight=600):
    n = text(id, s, x, y, size, color, weight=weight)
    card_kids.append(n["id"])
    return n


LH = CX - 177 + 26        # card text left edge
fs = 18.2
l3_y = CY + 12


def line_w(s, size):
    return len(s) * size * 0.5


cd_text("cd_l1", "Learn how to add 3D to your", LH + line_w("Learn how to add 3D to your", fs) / 2, CY - 36, fs, "#1c1c1e")
cd_text("cd_l2", "websites and digital products,", LH + line_w("websites and digital products,", fs) / 2, CY - 12, fs, "#1c1c1e")
# line 3 mixes plain text with the black highlight chips
x = LH
w = line_w("with a focus on", fs)
cd_text("cd_l3a", "with a focus on", x + w / 2, l3_y, fs, "#1c1c1e")
x += w + 9
for cid, word in [("cd_ch1", "design"), ("cd_ch2", "feel.")]:
    cw = line_w(word, fs) + 14
    n = rect(cid, x + cw / 2, l3_y, cw, 24, 5, "#212123")
    card_kids.append(n["id"])
    cd_text(cid + "t", word, x + cw / 2, l3_y + 1, fs, "#ffffff")
    x += cw + 8
    if cid == "cd_ch1":
        w = line_w("and", fs)
        cd_text("cd_l3b", "and", x + w / 2, l3_y, fs, "#1c1c1e")
        x += w + 8

ck_y = CY + 42
x = LH
for i, item in enumerate(["Monthly breakdowns", "Source files",
                          "Exclusive tools"]):
    n = path(f"cd_tk{i}", x + 4, ck_y, "M-4 0L-1 3L5 -4", "#6472f0",
             stroke=2.2)
    card_kids.append(n["id"])
    w = line_w(item, 11)
    cd_text(f"cd_ck{i}", item, x + 15 + w / 2, ck_y, 11, "#6a6a70",
            weight=500)
    x += 15 + w + 14

close = rect("cd_close", 851, 830, 48, 19, 9.5, "#2c2c2e")
cd_text("cd_closet", "Close", 851, 831, 10, "#ffffff")

# card + kids materialize f92-112; close pops at f112
track("cd", opacity=[(0, 0), (92 * F, 0), (104 * F, 1, "outCubic")],
      scale=[(92 * F, 0.8), (110 * F, 1.0, "outCubic")],
      blur=[(92 * F, 9), (108 * F, 0, "outCubic")])
for i, kid in enumerate(card_kids):
    if kid in ("cd_closet",):
        track(kid, opacity=[(0, 0), (112 * F, 0), (118 * F, 1)])
        continue
    d = 96 * F + (i % 5) * 0.02
    track(kid, opacity=[(0, 0), (d, 0), (d + 0.18, 1, "outCubic")],
          y=[(d, 8), (d + 0.22, 0, "outCubic")])
track("cd_close", opacity=[(0, 0), (112 * F, 0), (118 * F, 1)],
      scale=[(112 * F, 0.7), (122 * F, 1.0, "outCubic")])

# the hero "?" glyphs + halo dip while the card swallows the badge
track("b1_card", opacity=[(0, 1), (90 * F, 1), (98 * F, 0)])
for nid in ("b1_qg", "b1_qi"):
    pass  # their opacity tracks already end them; add fade via card cover


# ---------------------------------------------------------- 2d cartoon crab
# body: low-poly pentagon + facet, white ring + orange socket dot.
# limbs: capsule polygons radiating out. builder returns node ids so both
# scenes can pose their own instance.
BODY_R = 38
LIMB_ANGLES = [-90, -38, 8, 55, 118, 165, 212]
LIMB_LEN = [58, 62, 55, 62, 58, 60, 55]
LIMB_COLS = ["#5c7afb", "#6b86f2", "#5c7afb", "#6377f0", "#6b86f2",
             "#5c7afb", "#6377f0"]


def pent_d(r):
    pts = []
    for i in range(5):
        a = math.radians(-90 + i * 72 + (6 if i % 2 else -4))
        rr = r * (1.0 if i % 2 else 0.92)
        pts.append((rr * math.cos(a), rr * math.sin(a)))
    d = f"M{pts[0][0]:.1f} {pts[0][1]:.1f}"
    for x, y in pts[1:]:
        d += f"L{x:.1f} {y:.1f}"
    return d + "Z"


def capsule_d(ln, wd):
    h = ln / 2
    w = wd / 2
    return (f"M{-w} {-h+3}C{-w} {-h-5} {w} {-h-5} {w} {-h+3}"
            f"L{w*0.86} {h-4}C{w*0.8} {h+5} {-w*0.8} {h+5} {-w*0.86} {h-4}Z")


def build_crab(prefix, cx, cy, sc, echoes=True):
    """static crab instance; returns dict of ids for posing."""
    ids = {"limbs": [], "echoes": []}
    sh = rect(f"{prefix}_sh", cx, cy + 62 * sc, 132 * sc, 28 * sc,
              14 * sc, "#c7c7cc", blur=9)
    set_static(sh, opacity=0.4)
    ids["shadow"] = sh["id"]
    for i, ang in enumerate(LIMB_ANGLES):
        a = math.radians(ang)
        lx = cx + math.cos(a) * (BODY_R + LIMB_LEN[i] / 2 - 8) * sc
        ly = cy + math.sin(a) * (BODY_R + LIMB_LEN[i] / 2 - 8) * sc
        if echoes:
            e = path(f"{prefix}_le{i}", lx, ly,
                     capsule_d(LIMB_LEN[i], 26), "#96a8f8", rot=ang + 90)
            set_static(e, scale=sc, opacity=0.0)
            ids["echoes"].append(e["id"])
        n = path(f"{prefix}_l{i}", lx, ly,
                 capsule_d(LIMB_LEN[i], 26), LIMB_COLS[i], rot=ang + 90)
        set_static(n, scale=sc)
        ids["limbs"].append(n["id"])
    b = path(f"{prefix}_body", cx, cy, pent_d(BODY_R), "#5c7afb")
    set_static(b, scale=sc)
    f = path(f"{prefix}_facet", cx, cy,
             "M-32 -13L2 -35L28 -7L-4 6Z", "#6b86f2")
    set_static(f, scale=sc, opacity=0.7)
    ring = path(f"{prefix}_ring", cx, cy, circle_d(15), "#ffffff")
    set_static(ring, scale=sc)
    dot = path(f"{prefix}_dot", cx, cy, circle_d(9), "#f79f28")
    set_static(dot, scale=sc)
    ids["body"] = [b["id"], f["id"], ring["id"], dot["id"]]
    return ids


# crab walks in at the right edge f128-160 (page space, seen at 1.9x)
pv = build_crab("pv", 1090, 552, 0.52, echoes=False)
for nid in pv["body"] + [pv["shadow"]]:
    track(nid, x=[(126 * F, 80), (160 * F, 0, "outCubic")],
          opacity=[(0, 0), (126 * F, 0), (132 * F, 1)])
for i, nid in enumerate(pv["limbs"]):
    sw = 14 if i % 2 else -14
    wig = []
    tt = 126 * F
    v = sw
    while tt <= 160 * F:
        wig.append((tt, LIMB_ANGLES[i] + 90 + v, "inOutCubic"))
        v = -v
        tt += 0.14
    track(nid, x=[(126 * F, 80), (160 * F, 0, "outCubic")],
          opacity=[(0, 0), (126 * F, 0), (132 * F, 1)],
          rot=wig)

# scene-1 pointing-hand cursor (stage pos: fingertip near badge lower edge)
c1 = cursor_group("cur1", 909, 668, "hand", 1.35)
for nid in c1:
    track(nid, x=[(0, 0), (4 * F, 0), (12 * F, -16, "outCubic"),
                  (30 * F, -16), (55 * F, -14, "inOutCubic"), (88 * F, -14),
                  (102 * F, 142, "inOutCubic"), (160 * F, 145)],
          y=[(0, 0), (4 * F, 0), (12 * F, -26, "outCubic"), (30 * F, -26),
             (55 * F, -32, "inOutCubic"), (88 * F, -32),
             (102 * F, -50, "inOutCubic"), (160 * F, -52)])

# camera: hook hold -> crash zoom-out -> hold -> push-in on the card
EZ = [0.16, 1, 0.3, 1]
track("s1",
      cam_zoom=[(0, 1.70), (26 * F, 1.715), (52 * F, 1.0, EZ), (88 * F, 1.0),
                (108 * F, 1.9, [0.3, 0.75, 0.3, 1]), (160 * F, 1.93)],
      cam_x=[(0, 325), (26 * F, 325), (52 * F, 0, EZ), (88 * F, 0),
             (108 * F, 325.5, [0.3, 0.75, 0.3, 1]), (160 * F, 327)],
      cam_y=[(0, 25), (26 * F, 27), (52 * F, 0, EZ), (88 * F, 0),
             (108 * F, 26.6, [0.3, 0.75, 0.3, 1]), (160 * F, 28)])

# ------------------------------------------------------------------ scene 2
# drag playground. world designed at the close framing (zoom 1.05 at cut);
# zoom-out to 0.62 reveals page furniture + the dark device bezel.
cur_nodes = s2_nodes
S2 = 138 * F

rect("g_wash", 540, 470, 3000, 2600, 0, "#e9e9ec", gradient={
    "angle": 90, "stops": [{"at": 0, "color": "#e6e6ea"},
                           {"at": 0.5, "color": "#f8f8fa"},
                           {"at": 1, "color": "#fefefe"}]})
set_static(path("g_grid", 540, 540, grid_d(-1200, 1700, -1200, 1700, 74),
                "#ececef", stroke=1.0), opacity=0.6)

# ghost hero type fragments (still defocused): big G bottom-left, NG top-left
for i, (dx, dy, op) in enumerate([(-6, 0, 0.22), (6, 3, 0.22), (0, 0, 0.8)]):
    set_static(text(f"g_g{i}", "G", 40 + dx, 790 + dy, 430, "#d5d4d9",
                    weight=900), opacity=op)
    set_static(text(f"g_ng{i}", "NG", 30 + dx, 60 + dy, 330, "#d5d4d9",
                    weight=900), opacity=op * 0.9)
    set_static(text(f"g_n{i}", "N", -95 + dx, 480 + dy, 330, "#d5d4d9",
                    weight=900), opacity=op * 0.9)

# page furniture seen when zoomed out: glowing badge + get-notified pill.
# the badge sits offscreen during the close framing; a parallax slide near
# the end brings it large into the top-left like the reference close.
BGX, BGY = -70, 411
set_static(rect("g_halo", BGX, BGY, 210, 210, 66, "#b9c4fb", blur=30),
           opacity=0.55)
rect("g_badge", BGX, BGY, 168, 168, 48, "#ffffff",
     glow={"sigma": 22, "opacity": 0.3, "color": "#aeb4cf", "dy": 10})
text("g_q", "?", BGX, BGY + 4, 92, "#6472f0", weight=800)
rect("g_pill", -240, 770, 280, 90, 45, "#5876fc")
text("g_pillt", "Get notified", -205, 772, 34, "#ffffff", weight=600)
text("g_caption", "s?", -280, 620, 34, "#6d6d72", weight=500)
set_static(path("g_mark", 1150, 1210, circle_d(64) + circle_d(38), "#d3d3d8",
                stroke=3.0), opacity=0.6)

# device bezel beyond the page's right/bottom edges
rect("bz_r", 1620, 540, 640, 3200, 64, "#3e3d42")
rect("bz_b", 540, 1640, 3400, 640, 64, "#3e3d42")
rect("bz_corner", 1452, 1452, 400, 400, 90, "#3e3d42", rot=0)

# --------------------------------------------------- ragdoll drag simulation
# handle waypoints authored in the SCREEN coords of the reference frames,
# mapped to world through the camera framing active at that moment.
# close framing: zoom 1.32 cam (-58, 12); mid: zoom 0.62 cam (0, 0);
# end framing zoom ~1.18 is solved after the sim from the crab's end pos.
def close_w(sx, sy):
    return ((sx - 540) / 1.32 + 482, (sy - 540) / 1.32 + 552)


def mid_w(sx, sy):
    return ((sx - 540) / 0.62 + 540, (sy - 540) / 0.62 + 540)


HANDLE_WP = [
    (0.00, *close_w(790, 475)),
    (0.14, *close_w(862, 566)),
    (0.28, *close_w(706, 700)),
    (0.42, *close_w(800, 528)),
    (0.58, *close_w(808, 522)),
    (0.68, *close_w(700, 810)),
    (0.80, *close_w(685, 840)),
    (0.95, *mid_w(690, 640)),
    (1.15, *mid_w(650, 600)),
    (1.35, *mid_w(700, 570)),
    (1.55, *mid_w(680, 560)),
    (1.75, 738, 491),
    (2.02, 752, 472),
    (2.12, 700, 545),
    (2.30, 430, 800),
]


def handle_pos(t):
    if t <= HANDLE_WP[0][0]:
        return HANDLE_WP[0][1], HANDLE_WP[0][2]
    for (t0, x0, y0), (t1, x1, y1) in zip(HANDLE_WP, HANDLE_WP[1:]):
        if t0 <= t <= t1:
            p = (t - t0) / (t1 - t0)
            p = p * p * (3 - 2 * p)  # smoothstep per segment
            return x0 + (x1 - x0) * p, y0 + (y1 - y0) * p
    return HANDLE_WP[-1][1], HANDLE_WP[-1][2]


DT = 1 / 240
STEPS = int(2.30 / DT) + 1
L_REST = 118
BODY_K = 42.0
BODY_DAMP = 3.0
LIMB_OM = 13.5
LIMB_Z = 0.22

bx, by = 300.0, 590.0
bvx, bvy = 0.0, 0.0
brot = 0.0
limb_off = [(0.0, 0.0)] * 7      # displacement from anchor
limb_vel = [(0.0, 0.0)] * 7

samples = []                     # per 1/30s: body, rot, limbs, handle
next_sample = 0.0
for step in range(STEPS):
    t = step * DT
    hx, hy = handle_pos(t)
    dx, dy = hx - bx, hy - by
    dist = math.hypot(dx, dy)
    ax = ay = 0.0
    if dist > L_REST:
        pull = (dist - L_REST) * BODY_K
        ax += dx / dist * pull
        ay += dy / dist * pull
    ax -= bvx * BODY_DAMP
    ay -= bvy * BODY_DAMP
    bvx += ax * DT
    bvy += ay * DT
    bx += bvx * DT
    by += bvy * DT
    rot_target = max(-26.0, min(26.0, bvx * 0.035))
    brot += (rot_target - brot) * min(1.0, 6.0 * DT)
    new_off, new_vel = [], []
    for i, ang in enumerate(LIMB_ANGLES):
        ox, oy = limb_off[i]
        vx, vy = limb_vel[i]
        # spring the limb displacement back to zero; body acceleration
        # excites it (limbs lag the body)
        lax = -LIMB_OM * LIMB_OM * ox - 2 * LIMB_Z * LIMB_OM * vx - ax * 0.62
        lay = -LIMB_OM * LIMB_OM * oy - 2 * LIMB_Z * LIMB_OM * vy - ay * 0.62
        vx += lax * DT
        vy += lay * DT
        ox += vx * DT
        oy += vy * DT
        m = math.hypot(ox, oy)
        if m > 40:
            ox, oy = ox / m * 40, oy / m * 40
        new_off.append((ox, oy))
        new_vel.append((vx, vy))
    limb_off, limb_vel = new_off, new_vel
    if t >= next_sample - 1e-9:
        samples.append((round(t, 4), bx, by, brot,
                        list(limb_off), hx, hy,
                        math.hypot(bvx, bvy)))
        next_sample += 1 / 30

# stage rest positions = first sample
b0x, b0y = samples[0][1], samples[0][2]
h0x, h0y = samples[0][5], samples[0][6]

crab = build_crab("cr", b0x, b0y, 1.0)

# limb anchors in body space (rotated by body rot at runtime)
ANCH = []
for i, ang in enumerate(LIMB_ANGLES):
    a = math.radians(ang)
    r = BODY_R + LIMB_LEN[i] / 2 + 6
    ANCH.append((math.cos(a) * r, math.sin(a) * r))


def rot2(x, y, deg):
    a = math.radians(deg)
    return (x * math.cos(a) - y * math.sin(a),
            x * math.sin(a) + y * math.cos(a))


body_keys_x, body_keys_y, body_keys_rot = [], [], []
limb_kx = [[] for _ in range(7)]
limb_ky = [[] for _ in range(7)]
limb_kr = [[] for _ in range(7)]
limb_echo_op = [[] for _ in range(7)]
sh_kx, sh_ky = [], []
handle_kx, handle_ky = [], []
dot_keys = [([], []) for _ in range(13)]
cur_kx, cur_ky = [], []

# limb stage positions (unrotated rest)
limb_stage = [(b0x + ax_, b0y + ay_) for ax_, ay_ in ANCH]

prev_limb_pos = list(limb_stage)
for si, (t, bx, by, brot, offs, hx, hy, spd) in enumerate(samples):
    body_keys_x.append((t, bx - b0x))
    body_keys_y.append((t, by - b0y))
    body_keys_rot.append((t, brot))
    sh_kx.append((t, bx - b0x))
    sh_ky.append((t, by - b0y))
    handle_kx.append((t, hx - h0x))
    handle_ky.append((t, hy - h0y))
    cur_kx.append((t, hx - h0x))
    cur_ky.append((t, hy - h0y))
    for i in range(7):
        axr, ayr = rot2(*ANCH[i], brot)
        ox, oy = offs[i]
        lx = bx + axr + ox
        ly = by + ayr + oy
        limb_kx[i].append((t, lx - limb_stage[i][0]))
        limb_ky[i].append((t, ly - limb_stage[i][1]))
        # swing: perpendicular displacement bends the limb
        pax, pay = -math.sin(math.radians(LIMB_ANGLES[i])), \
            math.cos(math.radians(LIMB_ANGLES[i]))
        perp = ox * pax + oy * pay
        limb_kr[i].append((t, LIMB_ANGLES[i] + 90 + brot
                           + max(-42, min(42, perp * 1.9))))
        pv_ = prev_limb_pos[i]
        lspd = math.hypot(lx - pv_[0], ly - pv_[1]) * 30
        limb_echo_op[i].append((t, max(0.0, min(0.32, (lspd - 550) / 2200))))
        prev_limb_pos[i] = (lx, ly)
    for di in range(13):
        f = (di + 1) / 14
        px = bx + (hx - bx) * f
        py = by + (hy - by) * f
        dot_keys[di][0].append((t, px))
        dot_keys[di][1].append((t, py))

track(crab["body"][0], x=body_keys_x, y=body_keys_y, rot=body_keys_rot)
for nid in crab["body"][1:]:
    track(nid, x=body_keys_x, y=body_keys_y)
track(crab["shadow"], x=sh_kx, y=sh_ky)
for i in range(7):
    track(crab["limbs"][i], x=limb_kx[i], y=limb_ky[i], rot=limb_kr[i])
    # echo: same motion delayed one sample, opacity by speed
    ex = [(t + 1 / 30, v) for t, v in limb_kx[i][:-1]]
    ey = [(t + 1 / 30, v) for t, v in limb_ky[i][:-1]]
    er = [(t + 1 / 30, v) for t, v in limb_kr[i][:-1]]
    track(crab["echoes"][i], x=[(0, limb_kx[i][0][1])] + ex,
          y=[(0, limb_ky[i][0][1])] + ey,
          rot=[(0, limb_kr[i][0][1])] + er,
          opacity=limb_echo_op[i])

# tether dots (absolute positions baked; stage pos = first sample)
for di in range(13):
    xs, ys = dot_keys[di]
    x0, y0 = xs[0][1], ys[0][1]
    rect(f"td{di}", x0, y0, 8.5, 8.5, 4.25, "#f09a2e")
    track(f"td{di}", x=[(t, v - x0) for t, v in xs],
          y=[(t, v - y0) for t, v in ys])

# handle dot + grabbing fist cursor riding it
rect("hd", h0x, h0y, 19, 19, 9.5, "#f79f28",
     streak={"samples": 4, "window": 0.04, "gain": 0.3})
track("hd", x=handle_kx, y=handle_ky)
c2 = cursor_group("cur2", h0x + 2, h0y + 46, "fist", 1.5)
for nid in c2:
    track(nid, x=cur_kx, y=cur_ky)

# camera: close on the toy -> pull back to the bezel -> drift back in.
# the end framing centers on wherever the simulated crab actually is at
# the final frame so the clip ends mid-drag on the crab.
cex, cey, cez = samples[-1][1], samples[-1][2], 1.18
end_cam_x = cex - 540 + (540 - 650) / cez
end_cam_y = cey - 540 + (540 - 470) / cez

# parallax-slide the badge so the end framing shows it big at top-left
# (the reference camera pans; our furniture drifts to the same effect)
bex = (150 - 540) / cez + end_cam_x + 540
bey = (210 - 540) / cez + end_cam_y + 540
for nid in ("g_halo", "g_badge", "g_q"):
    track(nid, x=[(0, 0), (1.72, 0), (2.1, bex - BGX, "inOutCubic")],
          y=[(0, 0), (1.72, 0), (2.1, bey - BGY, "inOutCubic")])
track("s2",
      cam_zoom=[(0, 1.32), (56 * F, 1.32), (88 * F, 0.62, EZ),
                (104 * F, 0.62), (130 * F, 1.08, [0.4, 0, 0.25, 1]),
                (138 * F, cez)],
      cam_x=[(0, -58), (56 * F, -58), (88 * F, 0, EZ), (104 * F, 0),
             (130 * F, end_cam_x * 0.9, [0.4, 0, 0.25, 1]),
             (138 * F, end_cam_x)],
      cam_y=[(0, 12), (56 * F, 12), (88 * F, 0, EZ), (104 * F, 0),
             (130 * F, end_cam_y * 0.9, [0.4, 0, 0.25, 1]),
             (138 * F, end_cam_y)])

stage = {
    "fps": 30,
    "size": [W, H],
    "scenes": [
        {"id": "s1", "bg": "#fefefe", "dur": round(S1, 4),
         "transition": {"kind": "cut"}, "nodes": s1_nodes},
        {"id": "s2", "bg": "#fefefe", "dur": round(S2, 4),
         "transition": {"kind": "cut"}, "nodes": s2_nodes},
    ],
}

with open("docs/crab.stage.json", "w") as f:
    json.dump(stage, f, indent=1)
with open("docs/crab.anim.json", "w") as f:
    json.dump({"tracks": tracks}, f, indent=1)
print("wrote docs/crab.{stage,anim}.json:",
      len(s1_nodes) + len(s2_nodes), "nodes,", len(tracks), "tracks,",
      f"dur {S1 + S2:.3f}s")
