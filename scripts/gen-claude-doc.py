#!/usr/bin/env python3
# reproduction of analysis/claude claude.mp4 (23.79s, 1920x1080, 24fps):
# the Claude Design promo staged inside a fake "Nexaa" storyboard template.
# every scene lives on a warm-grey mat with an inset 16:9 slide, a
# Hook / Demo / End result / CTA chapter bar whose playhead rides
# left-to-right for the whole film, a tick ruler and Nexaa wordmarks.
# terracotta serif-feel title cards alternate with drawn product ui.
# numbers measured from analysis/claude/frames (frame N = (N-1)/24 s).
import json
import math
import os

W, H = 1920, 1080

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

MAT = "#f1f0eb"
CLAY = "#cf6f57"
OFF = "#f9f9f9"
INK = "#241208"
UIINK = "#1f1f1f"
ACC = "#d26b58"
SEND = "#d9654a"
TOGBLUE = "#5e9ef1"
TABBLUE = "#bfe3fd"
CREAM = "#efe9dd"

# slide geometry (the inset 16:9 "frame" everything plays inside)
SLX, SLY, SLW, SLH = 960, 418.5, 1074, 607
SL_L, SL_R = SLX - SLW / 2, SLX + SLW / 2
SL_T, SL_B = SLY - SLH / 2, SLY + SLH / 2

# playhead travels the chapter bar linearly across the full 23.79s
TOTAL = 23.792
PX0, PX1 = 428.0, 1478.0
PXV = (PX1 - PX0) / TOTAL


def rect(id, x, y, w, h, r, fill, **kw):
    n = {"id": id, "type": "rect", "x": round(x, 1), "y": round(y, 1),
         "w": round(w, 1), "h": round(h, 1), "radius": r, "fill": fill}
    n.update(kw)
    return n


def text(id, s, x, y, size, color, weight=400, family="inter"):
    return {"id": id, "type": "text", "text": s, "x": round(x, 1),
            "y": round(y, 1), "color": color,
            "font": {"size": size, "weight": weight, "family": family}}


def ltext(id, s, left, y, size, color, weight=400):
    # left-anchored inter line, center estimated from avg advance
    cx = left + len(s) * size * 0.48 / 2
    return text(id, s, cx, y, size, color, weight)


def path(id, x, y, d, fill, **kw):
    n = {"id": id, "type": "path", "x": round(x, 1), "y": round(y, 1),
         "d": d, "fill": fill}
    n.update(kw)
    return n


def keyed(nid, at=0.0, **props):
    keys = {}
    for name, seq in props.items():
        out = []
        for k in seq:
            kk = {"t": round(k[0], 4), "v": round(k[1], 2)
                  if isinstance(k[1], float) else k[1]}
            if len(k) > 2:
                kk["ease"] = k[2]
            out.append(kk)
        keys[name] = out
    t = {"target": nid, "keys": keys}
    if at:
        t["at"] = at
    return t


def circle_d(r, cx=0, cy=0):
    k = r * 0.5523
    return (f"M{cx-r} {cy}C{cx-r} {cy-k} {cx-k} {cy-r} {cx} {cy-r}"
            f"C{cx+k} {cy-r} {cx+r} {cy-k} {cx+r} {cy}"
            f"C{cx+r} {cy+k} {cx+k} {cy+r} {cx} {cy+r}"
            f"C{cx-k} {cy+r} {cx-r} {cy+k} {cx-r} {cy}Z")


def sunburst_d(r0=9, r1=30, n=12, hw=3.0):
    d = ""
    for i in range(n):
        a = i * 2 * math.pi / n
        ca, sa = math.cos(a), math.sin(a)
        p1 = (r0 * ca - hw * sa, r0 * sa + hw * ca)
        p2 = (r0 * ca + hw * sa, r0 * sa - hw * ca)
        tip = (r1 * ca, r1 * sa)
        d += (f"M{p1[0]:.1f} {p1[1]:.1f}L{tip[0]:.1f} {tip[1]:.1f}"
              f"L{p2[0]:.1f} {p2[1]:.1f}Z")
    return d


def star4_d(r=30):
    c = r * 0.14
    return (f"M0 {-r}C{c} {-c*2} {c*2} {-c} {r} 0"
            f"C{c*2} {c} {c} {c*2} 0 {r}"
            f"C{-c} {c*2} {-c*2} {c} {-r} 0"
            f"C{-c*2} {-c} {-c} {-c*2} 0 {-r}Z")


NEXAA_GLYPH = "M0 22L0 0L7 8L7 0L18 22Z"

# ---------------------------------------------------------------- chrome
# per-scene template furniture. content overflowing the slide is hidden by
# four mat-colored bands, then the chapter bar + playhead sit on top.
CELLS = {
    "hook": (520.5, 201, "Hook", 514),
    "demo": (838.5, 419, "Demo: Use Case", 838),
    "end": (1188.5, 263, "End result", 1185),
    "cta": (1410.0, 166, "CTA", 1409),
}


def chrome(p, t0, dur, active):
    """active: list of (cell, on, off) scene-local windows for the blue
    highlight. returns (nodes, tracks); playhead x keys are linear."""
    nodes, tracks = [], []
    # mat bands mask slide overflow
    nodes += [
        rect(p + "bandl", SL_L / 2, 540, SL_L, 1080, 0, MAT),
        rect(p + "bandr", (SL_R + W) / 2, 540, W - SL_R, 1080, 0, MAT),
        rect(p + "bandt", 960, SL_T / 2, W, SL_T, 0, MAT),
        rect(p + "bandb", 960, (SL_B + H) / 2, W, H - SL_B, 0, MAT),
    ]
    act = {c for c, _, _ in active}
    for name, (cx, cw, label, lx) in CELLS.items():
        nodes.append(rect(p + "cell_" + name, cx, 825, cw, 144, 18,
                          "#ffffff"))
        if name in act:
            n = rect(p + "act_" + name, cx, 825, cw, 144, 18, TABBLUE)
            nodes.append(n)
            wins = [w for w in active if w[0] == name]
            ks = []
            for _, on, offt in wins:
                if on <= 0:
                    ks.append((0, 1))
                else:
                    ks += [(on - 0.001, 0), (on, 1)]
                if offt < dur:
                    ks += [(offt - 0.001, 1), (offt, 0)]
            if ks and ks[0][0] > 0:
                ks.insert(0, (0, 0))
            tracks.append(keyed(n["id"], opacity=ks))
    for name, (cx, cw, label, lx) in CELLS.items():
        nodes.append(text(p + "lbl_" + name, label, lx, 824, 30,
                          "#101010", weight=500))
    # tick ruler under the bar
    ticks = ""
    for i in range(36):
        x = 443 + i * (1478 - 443) / 35
        ticks += f"M{x:.1f} 916L{x:.1f} 930"
    nodes.append(path(p + "ruler", 0, 0, ticks, "#1c1c1c", stroke=2.0))
    # playhead: triangle + needle, riding the whole doc
    px = PX0 + PXV * t0
    dx = PXV * dur
    nodes.append(path(p + "tri", px, 758, "M-17 0L17 0L0 24Z", "#1c1c1c"))
    nodes.append(rect(p + "needle", px, 826, 3.5, 142, 1, "#1c1c1c"))
    tracks.append(keyed(p + "tri", x=[(0, 0.0), (dur, dx)]))
    tracks.append(keyed(p + "needle", x=[(0, 0.0), (dur, dx)]))
    # nexaa wordmarks: mat bottom-right + faint one inside the slide
    nodes.append(path(p + "nxg", 1652, 991, NEXAA_GLYPH, "#8f8d86"))
    nodes.append(text(p + "nxt", "Nexaa", 1745, 1003, 42, "#8f8d86",
                      weight=500))
    return nodes, tracks


def watermark(p):
    # faint wordmark inside the slide (drawn with content, under bands)
    n1 = path(p + "wmg", 1384, 681, NEXAA_GLYPH, "#a09b92")
    n1["keys"] = {"scale": [{"t": 0, "v": 0.62}]}
    n2 = text(p + "wmt", "Nexaa", 1440, 690, 26, "#a09b92", weight=500)
    ts = [keyed(p + "wmg", opacity=[(0, 0.55)]),
          keyed(p + "wmt", opacity=[(0, 0.55)])]
    return [n1, n2], ts


scenes = []
tracks = []


def scene(id, bg, dur, transition, nodes):
    scenes.append({"id": id, "bg": bg, "dur": round(dur, 3),
                   "transition": transition, "nodes": nodes})


# ============================================================ scene 1
# terracotta hook (f1-49): headline builds word by word, the moodboard
# collage flies in and clears, the Milanote card slides in and its toggle
# flips on under a white hand cursor. constant slow left drift.
D1 = 2.042
c = []
c.append(rect("s1_slide", SLX, SLY, SLW, SLH, 6, CLAY))
c.append(text("s1_head", "Claude Design now connects to", 955, 417, 50,
              INK, weight=600))
tracks.append({"target": "s1_head", "at": 0.02, "reveal": {
    "unit": "word", "stagger": 0.13, "dur": 0.04, "rise": 0}})
tracks.append(keyed("s1_head", x=[(0, 0.0), (D1, -22.0)]))

# collage: rounded cards flying in around the headline, then absorbing
COLL = [  # (x, y, w, h, fill, from_dx, from_dy)
    (1055, 297, 160, 92, "#ffffff", 0, -420),
    (1247, 350, 142, 96, "#ffffff", 620, 0),
    (1000, 380, 158, 96, "#d63b2f", -640, 0),
    (1263, 432, 140, 86, "#14301f", 620, 60),
    (1005, 478, 158, 90, "#ffffff", -300, 420),
    (1232, 510, 146, 72, "#e13fae", 300, 420),
    (1115, 546, 150, 80, "#ffffff", 0, 420),
    (1157, 380, 118, 70, "#f6f2ea", 200, -420),
]
for i, (x, y, w, h, fill, fdx, fdy) in enumerate(COLL):
    nid = f"s1_col{i}"
    kw = {}
    if fill == "#e13fae":
        kw["gradient"] = {"angle": 35, "stops": [
            {"at": 0, "color": "#a44bd6"}, {"at": 1, "color": "#ff8ac4"}]}
    c.append(rect(nid, x, y, w, h, 10, fill, **kw))
    st = 0.60 + (i % 4) * 0.05
    tracks.append(keyed(nid,
                        x=[(st, fdx), (st + 0.30, 0, "outCubic")],
                        y=[(st, fdy), (st + 0.30, 0, "outCubic")],
                        scale=[(1.0, 1.0), (1.22, 0.5, "inCubic")],
                        opacity=[(st, 0), (st + 0.08, 1), (1.02, 1),
                                 (1.2, 0)]))
    if fill in ("#ffffff", "#f6f2ea"):
        did = nid + "d"
        c.append(rect(did, x, y + 8, w - 28, h - 40, 4, "#dcd8d0"))
        tracks.append(keyed(did,
                            x=[(st, fdx), (st + 0.30, 0, "outCubic")],
                            y=[(st, fdy), (st + 0.30, 0, "outCubic")],
                            scale=[(1.0, 1.0), (1.22, 0.5, "inCubic")],
                            opacity=[(st, 0), (st + 0.08, 1), (1.02, 1),
                                     (1.18, 0)]))

# milanote connector card
CARD_IN = [(0, 520.0), (1.18, 520.0), (1.52, 0.0, "outCubic"),
           (1.83, 0.0), (2.0, -30.0, "outCubic")]
c += [
    rect("s1_card", 965, 410, 510, 132, 30, CREAM,
         glow={"sigma": 26, "opacity": 0.25, "color": "#7a5040", "dy": 12}),
    rect("s1_mic", 773, 410, 62, 62, 31, "#232120"),
    path("s1_mim", 773, 410, "M-9 9L-9 -9L0 1L9 -9L9 9", "#f5f2ec",
         stroke=2.4),
    text("s1_mlbl", "Milanote", 895, 409, 34, "#1c1c1c", weight=500),
    rect("s1_tpill", 1152, 410, 64, 38, 19, "#d8d2c4",
         states={"on": {"fill": TOGBLUE}}),
    rect("s1_tknob", 1139, 410, 30, 30, 15, "#ffffff"),
]
for nid in ["s1_card", "s1_mic", "s1_mim", "s1_mlbl", "s1_tpill"]:
    tracks.append(keyed(nid, x=CARD_IN))
tracks.append(keyed("s1_tknob",
                    x=[(0, 520.0), (1.18, 520.0), (1.52, 0.0, "outCubic"),
                       (1.79, 0.0), (1.91, 26.0, "outCubic"),
                       (2.0, -3.0, "outCubic")]))
tracks.append({"target": "s1_tpill", "at": 1.79, "state": "on"})
# white pointing cursor rises from below right, hits the toggle, drops out
c.append({"id": "s1_cur", "type": "cursor", "x": 1210, "y": 780, "w": 30,
          "fill": "#ffffff"})
tracks.append(keyed("s1_cur",
                    x=[(1.25, 0.0), (1.66, -48.0, "outCubic"),
                       (1.9, -40.0), (2.04, 30.0, "inCubic")],
                    y=[(1.25, 0.0), (1.66, -348.0, "outCubic"),
                       (1.9, -344.0), (2.04, 40.0, "inCubic")],
                    opacity=[(1.2, 0), (1.32, 1)]))

wn, wt = watermark("s1_")
cn, ct = chrome("s1c_", 0.0, D1, [("hook", 0, D1)])
tracks += wt + ct
scene("s1", MAT, D1, {"kind": "cut"}, c + wn + cn)

# ============================================================ scene 2
# hard cut to off-white: giant "Instantly" crash-scrub resolves into the
# small line that types word by word, clay accent on "into", sunburst caret.
D2 = 2.292
c = [rect("s2_slide", SLX, SLY, SLW, SLH, 6, OFF)]
c.append(text("s2_giant", "Instantly", 960, 430, 400, "#dc9c88",
              weight=600))
tracks.append(keyed("s2_giant",
                    x=[(0, 760.0), (0.92, -700.0, "outCubic")],
                    opacity=[(0, 1), (0.82, 1), (1.05, 0)]))
c.append(text("s2_line", "Instantly turn moodboards into storyboards",
              935, 415, 38, INK, weight=600))
tracks.append({"target": "s2_line", "at": 0.95, "reveal": {
    "unit": "word", "stagger": 0.09, "dur": 0.12, "rise": 0,
    "accent": ACC, "color_delay": 0.16, "color_dur": 0.3,
    "keep": ["into"]}})
tracks.append(keyed("s2_line", opacity=[(0, 0), (0.95, 0), (1.0, 1)]))
sb = path("s2_sun", 1372, 413, sunburst_d(), ACC)
sb["keys"] = {"scale": [{"t": 0, "v": 0.85}]}
c.append(sb)
tracks.append(keyed("s2_sun",
                    x=[(0, -278.0), (1.3, -278.0), (1.48, 0.0, "outCubic")],
                    opacity=[(0, 0), (1.0, 0), (1.1, 1)]))

wn, wt = watermark("s2_")
cn, ct = chrome("s2c_", D1, D2, [("hook", 0, D2)])
tracks += wt + ct
scene("s2", MAT, D2, {"kind": "cut"}, c + wn + cn)

# ============================================================ scene 3
# demo chapter: headline + chat composer dissolve up, the prompt types,
# the + menu and connectors submenu pop, Milanote/Figma toggle on, and a
# group push-in lands the frame on the Opus chip + orange send button.
# camera is faked per node (pivot zoom) so the template chrome stays put.
D3 = 6.375
FZX, FZY = 1280.0, 575.0  # zoom pivot: composer bottom-right


def ease_io(u):
    return 4 * u * u * u if u < 0.5 else 1 - ((-2 * u + 2) ** 3) / 2


def ease_out(u):
    return 1 - (1 - u) ** 3


def zf(t):
    if t <= 1.6:
        return 1.0
    if t <= 4.6:
        return 1.0 + 0.5 * ease_io((t - 1.6) / 3.0)
    if t <= 5.5:
        return 1.5 + 0.85 * ease_out((t - 4.6) / 0.9)
    return 2.35


GRID = sorted(set(
    [round(i * 0.25, 2) for i in range(int(D3 / 0.25) + 1)]
    + [round(4.4 + i * 0.05, 2) for i in range(27)] + [D3]))


def zoomed(nid, px, py, base=1.0, ox=None, oy=None):
    """bake the pivot zoom into x/y/scale keys; ox/oy are optional
    scene-local own-motion functions returning extra offsets."""
    xs, ys, ss = [], [], []
    for t in GRID:
        z = zf(t)
        exx = ox(t) if ox else 0.0
        eyy = oy(t) if oy else 0.0
        xs.append((t, (z - 1) * (px - FZX) + exx))
        ys.append((t, (z - 1) * (py - FZY) + eyy))
        ss.append((t, base * z))
    return [keyed(nid, x=xs, y=ys, scale=ss)]


def rise(t0, t1, amt):
    def f(t):
        if t <= t0:
            return amt
        if t >= t1:
            return 0.0
        return amt * (1 - ease_out((t - t0) / (t1 - t0)))
    return f


c = [rect("s3_slide", SLX, SLY, SLW, SLH, 6, OFF)]
Z = []  # (id, px, py, base, ox, oy)


def znode(n, base=1.0, ox=None, oy=None):
    c.append(n)
    Z.append((n["id"], n["x"], n["y"], base, ox, oy))
    return n


hb = path("s3_hsun", 750, 340, sunburst_d(), ACC)
znode(hb, base=1.15, oy=rise(0.0, 0.55, 34))
znode(text("s3_head", "Let's knock something off your list", 1105, 342,
           44, INK, weight=600), oy=rise(0.0, 0.55, 34))
znode(rect("s3_card", 1040, 512, 900, 238, 26, "#ffffff",
           glow={"sigma": 30, "opacity": 0.16, "color": "#8a8378",
                 "dy": 12}), oy=rise(0.15, 0.7, 46))
znode(ltext("s3_ph", "How can i help u today?", 625, 450, 30, "#b0aca4"),
      oy=rise(0.15, 0.7, 46))
P1 = "Hey Claude, Can you analyze my milanote board with the"
P2 = "product script, references, and moodboards and start"
P3 = "storyboarding in Figma?"
znode(ltext("s3_p1", P1, 625, 446, 28, UIINK))
znode(ltext("s3_p2", P2, 625, 482, 28, UIINK))
znode(ltext("s3_p3", P3, 625, 518, 28, UIINK))
znode(rect("s3_plus", 634, 592, 46, 46, 12, "#f1efeb"),
      oy=rise(0.15, 0.7, 46))
znode(path("s3_plusg", 634, 592, "M-9 0L9 0M0 -9L0 9", "#3f3f3f",
           stroke=2.6), oy=rise(0.15, 0.7, 46))
znode(text("s3_opus", "Opus 4.7", 1352, 592, 26, "#3f3f3f"),
      oy=rise(0.15, 0.7, 46))
znode(path("s3_chev", 1416, 594, "M-6 -3L0 3L6 -3", "#3f3f3f",
           stroke=2.2), oy=rise(0.15, 0.7, 46))
znode(rect("s3_send", 1458, 592, 54, 54, 14, SEND),
      oy=rise(0.15, 0.7, 46))
znode(path("s3_sendg", 1458, 592, "M0 9L0 -9M-7 -2L0 -9L7 -2", "#ffffff",
           stroke=3.0), oy=rise(0.15, 0.7, 46))
# + menu
znode(rect("s3_menu", 772, 585, 242, 180, 16, "#ffffff",
           glow={"sigma": 24, "opacity": 0.2, "color": "#8a8378",
                 "dy": 8}))
MENU = [("Add files or photos", 522), ("Skills", 566), ("Connectors", 604),
        ("Plugins", 642)]
for i, (s, y) in enumerate(MENU):
    znode(ltext(f"s3_mi{i}", s, 684, y, 21, "#2c2c2c"))
    if i > 0:
        znode(path(f"s3_mc{i}", 876, y, "M-3 -6L3 0L-3 6", "#9a9a9a",
                   stroke=2.0))
# connectors submenu
znode(rect("s3_sub", 1044, 585, 292, 272, 16, "#ffffff",
           glow={"sigma": 24, "opacity": 0.2, "color": "#8a8378",
                 "dy": 8}))
SUB = [("Milanote", 482), ("Figma", 523), ("Slack", 563),
       ("Claude in Chrome", 602), ("Add from Google Drive", 642)]
for i, (s, y) in enumerate(SUB):
    znode(ltext(f"s3_si{i}", s, 952, y, 21, "#2c2c2c"))
znode(rect("s3_sic0", 930, 482, 22, 22, 11, "#232120"))
znode(path("s3_sic0m", 930, 482, "M-4 4L-4 -4L0 0L4 -4L4 4", "#ffffff",
           stroke=1.6))
znode(rect("s3_sic1", 930, 523, 20, 20, 10, "#a259ff"))
znode(rect("s3_sic2", 930, 563, 20, 20, 10, "#e01e5a"))
znode(rect("s3_sic3", 930, 602, 20, 20, 10, "#4285f4"))
znode(path("s3_sic4", 930, 642, "M0 -9L9 7L-9 7Z", "#f4b400"))
znode(text("s3_foot", "Add connectors", 1010, 694, 20, "#8f8f8f"))
# submenu toggles: milanote + figma flip on, slack + chrome stay grey
for i, y in enumerate([482, 523, 563, 602]):
    znode(rect(f"s3_tp{i}", 1150, y, 40, 22, 11, "#d6d4ce",
               states={"on": {"fill": TOGBLUE}}))
FLIPS = {0: 4.27, 1: 4.62}
for i, y in enumerate([482, 523, 563, 602]):
    fl = FLIPS.get(i)

    def knb(t, fl=fl):
        if fl is None or t < fl:
            return 0.0
        return 18.0 if t > fl + 0.12 else 18.0 * (t - fl) / 0.12
    znode(rect(f"s3_tk{i}", 1141, y, 18, 18, 9, "#ffffff"), ox=knb)
if True:
    tracks.append({"target": "s3_tp0", "at": 4.27, "state": "on"})
    tracks.append({"target": "s3_tp1", "at": 4.62, "state": "on"})

for nid, px, py, base, ox, oy in Z:
    tracks += zoomed(nid, px, py, base, ox, oy)

# entrances / reveals / menu gating (opacity only, zoom handles geometry)
IN_HEAD = [(0.0, 0), (0.45, 1)]
IN_CARD = [(0.15, 0), (0.6, 1)]
for nid in ["s3_hsun", "s3_head"]:
    tracks.append(keyed(nid, opacity=IN_HEAD))
for nid in ["s3_card", "s3_plus", "s3_plusg", "s3_opus", "s3_chev",
            "s3_send", "s3_sendg"]:
    tracks.append(keyed(nid, opacity=IN_CARD))
tracks.append(keyed("s3_ph", opacity=[(0.15, 0), (0.6, 1), (1.75, 1),
                                      (1.88, 0)]))
tracks.append({"target": "s3_p1", "at": 1.92, "reveal": {
    "unit": "type", "cadence": 0.027, "dur": 0.05, "caret": "none"}})
tracks.append({"target": "s3_p2", "at": 3.45, "reveal": {
    "unit": "type", "cadence": 0.026, "dur": 0.05, "caret": "none"}})
tracks.append({"target": "s3_p3", "at": 4.85, "reveal": {
    "unit": "type", "cadence": 0.028, "dur": 0.05, "caret": "none"}})
tracks.append(keyed("s3_p1", opacity=[(0, 0), (1.9, 0), (1.92, 1)]))
tracks.append(keyed("s3_p2", opacity=[(0, 0), (3.43, 0), (3.45, 1)]))
tracks.append(keyed("s3_p3", opacity=[(0, 0), (4.83, 0), (4.85, 1)]))
MENU_IDS = ["s3_menu"] + [f"s3_mi{i}" for i in range(4)] + \
    [f"s3_mc{i}" for i in range(1, 4)]
for nid in MENU_IDS:
    tracks.append(keyed(nid, opacity=[(0, 0), (2.83, 0), (2.95, 1)]))
SUB_IDS = ["s3_sub", "s3_foot"] + [f"s3_si{i}" for i in range(5)] + \
    [f"s3_sic{i}" for i in range(5)] + ["s3_sic0m"] + \
    [f"s3_tp{i}" for i in range(4)] + [f"s3_tk{i}" for i in range(4)]
for nid in SUB_IDS:
    tracks.append(keyed(nid, opacity=[(0, 0), (3.7, 0), (3.82, 1)]))


def screen_pt(px, py, t):
    z = zf(t)
    return (FZX + z * (px - FZX), FZY + z * (py - FZY))


# cursor rides in screen space: + button, connectors, the two toggles,
# then down to the send button for the press
c.append({"id": "s3_cur", "type": "cursor", "x": 900, "y": 800, "w": 30,
          "fill": "#ffffff"})
WAY = [(1.45, 830, 700), (2.6, 648, 610), (3.3, 862, 616),
       (4.2, 1156, 494), (4.55, 1156, 534), (5.3, 1300, 620),
       (6.05, 1462, 618), (6.375, 1462, 618)]
cx0, cy0 = 900, 800
xs, ys = [], []
for t, px, py in WAY:
    sxx, syy = screen_pt(px, py, t)
    xs.append((t, sxx - cx0, "outCubic"))
    ys.append((t, syy - cy0, "outCubic"))
tracks.append(keyed("s3_cur", x=xs, y=ys,
                    opacity=[(1.3, 0), (1.45, 1)]))

wn, wt = watermark("s3_")
cn, ct = chrome("s3c_", D1 + D2, D3,
                [("hook", 0, 0.296), ("demo", 0.296, D3)])
tracks += wt + ct
scene("s3", MAT, D3, {"kind": "fade", "dur": 0.4}, c + wn + cn)

# ============================================================ scene 4
# blur+zoom-out handoff to the macOS transcript window; Claude's reply
# streams in and the Milanote source-board window slides in at right.
D4 = 3.583
c = [rect("s4_slide", SLX, SLY, SLW, SLH, 6, OFF)]
LWIN = ["s4_lwin", "s4_tl0", "s4_tl1", "s4_tl2", "s4_bub", "s4_bt0",
        "s4_bt1", "s4_bt2", "s4_r0", "s4_r1"]
c += [
    rect("s4_lwin", 765, 440, 410, 550, 12, "#ffffff",
         glow={"sigma": 28, "opacity": 0.18, "color": "#8a8378", "dy": 10}),
    rect("s4_tl0", 578, 178, 10, 10, 5, "#ff5f57"),
    rect("s4_tl1", 592, 178, 10, 10, 5, "#febc2e"),
    rect("s4_tl2", 606, 178, 10, 10, 5, "#28c840"),
    rect("s4_bub", 830, 214, 288, 52, 10, "#ececec"),
    text("s4_bt0", "Hey Claude, Can you analyze my milanote", 830, 200, 11,
         "#4a4a4a"),
    text("s4_bt1", "board with the product script, references, and", 830,
         214, 11, "#4a4a4a"),
    text("s4_bt2", "moodboards and start storyboarding in Figma?", 830,
         228, 11, "#4a4a4a"),
    ltext("s4_r0", "I'll review the script structure, visual references, "
          "pacing,", 590, 262, 11.5, "#3f3f3f"),
    ltext("s4_r1", "and creative direction from your Milanote board.", 590,
          278, 11.5, "#3f3f3f"),
]
for nid in LWIN:
    tracks.append(keyed(nid, opacity=[(0.05, 0), (0.5, 1)]
                        if nid not in ("s4_r0", "s4_r1") else
                        [(0.9 if nid == "s4_r0" else 1.15, 0),
                         (1.15 if nid == "s4_r0" else 1.4, 1)],
                        y=[(0.05, 26.0), (0.55, 0.0, "outCubic")]))
RWIN = []


def rw(n):
    c.append(n)
    RWIN.append(n["id"])
    return n


rw(rect("s4_rwin", 1210, 440, 415, 545, 12, "#ffffff",
        glow={"sigma": 28, "opacity": 0.18, "color": "#8a8378", "dy": 10}))
rw(rect("s4_rbar", 1210, 182, 415, 30, 10, "#f3f3f3"))
rw(ltext("s4_rbc", "Home  /  miro", 1020, 182, 12, "#6a6a6a"))
rw(rect("s4_bda", 1118, 320, 168, 148, 6, "#3b3b3d"))
for i, (x, y, w, h) in enumerate([(1078, 288, 40, 26), (1124, 286, 54, 30),
                                  (1090, 332, 62, 38), (1156, 328, 46, 32)]):
    rw(rect(f"s4_bda{i}", x, y, w, h, 3, "#fafafa"))
rw(rect("s4_bdb", 1272, 320, 118, 148, 6, "#2c2c2e"))
for i, (x, y, w, h, f) in enumerate([(1272, 282, 84, 26, "#baf7c4"),
                                     (1272, 316, 84, 26, "#fafafa"),
                                     (1272, 350, 84, 26, "#eaeaea")]):
    rw(rect(f"s4_bdb{i}", x, y, w, h, 3, f))
PHONES = [(1063, 478, "#e8622c"), (1130, 478, "#3178f2"),
          (1063, 582, "#f2c94c"), (1130, 582, "#29b6a8")]
for i, (x, y, f) in enumerate(PHONES):
    rw(rect(f"s4_ph{i}", x, y, 60, 92, 8, "#f6f1ea"))
    rw(rect(f"s4_phi{i}", x, y - 8, 44, 54, 4, f))
rw(rect("s4_yb", 1272, 458, 190, 58, 6, "#f5d532"))
rw(rect("s4_yb0", 1236, 458, 90, 34, 3, "#fdf7df"))
rw(rect("s4_sw", 1272, 590, 190, 125, 6, "#ffffff"))
rw(ltext("s4_swt", "Miro Colors", 1190, 545, 11, "#3f3f3f"))
for i, f in enumerate(["#5b8def", "#7ba3f5", "#3b5fd9"]):
    rw(rect(f"s4_swr{i}", 1266, 566 + i * 22, 164, 15, 3, f))
for nid in RWIN:
    tracks.append(keyed(nid, x=[(1.25, 520.0), (1.95, 0.0, "outCubic")],
                        opacity=[(1.2, 0), (1.4, 1)]))

wn, wt = watermark("s4_")
cn, ct = chrome("s4c_", D1 + D2 + D3, D4, [("demo", 0, D4)])
tracks += wt + ct
scene("s4", MAT, D4, {"kind": "fade", "dur": 0.7}, c + wn + cn)

# ============================================================ scene 5
# hard cut to terracotta: "From inspiration to production ready planning."
D5 = 1.333
c = [rect("s5_slide", SLX, SLY, SLW, SLH, 6, CLAY)]
c.append(text("s5_line", "From inspiration to production ready planning.",
              960, 415, 40, INK, weight=600))
tracks.append({"target": "s5_line", "at": 0.04, "reveal": {
    "unit": "word", "stagger": 0.11, "dur": 0.05, "rise": 0}})
tracks.append(keyed("s5_line", x=[(0, 0.0), (D5, -14.0)]))
wn, wt = watermark("s5_")
cn, ct = chrome("s5c_", D1 + D2 + D3 + D4, D5, [("end", 0, D5)])
tracks += wt + ct
scene("s5", MAT, D5, {"kind": "cut"}, c + wn + cn)

# ============================================================ scene 6
# hard cut to the split-window storyboard build: chat window at left keeps
# streaming, the Figma window's 3x2 grey frames fill in one by one.
D6 = 4.583
c = [rect("s6_slide", SLX, SLY, SLW, SLH, 6, OFF)]
c += [
    rect("s6_lwin", 765, 440, 410, 550, 12, "#ffffff",
         glow={"sigma": 28, "opacity": 0.18, "color": "#8a8378", "dy": 10}),
    rect("s6_tl0", 578, 178, 10, 10, 5, "#ff5f57"),
    rect("s6_tl1", 592, 178, 10, 10, 5, "#febc2e"),
    rect("s6_tl2", 606, 178, 10, 10, 5, "#28c840"),
    rect("s6_bub", 830, 214, 288, 52, 10, "#ececec"),
    text("s6_bt0", "Hey Claude, Can you analyze my milanote", 830, 200, 11,
         "#4a4a4a"),
    text("s6_bt1", "board with the product script, references, and", 830,
         214, 11, "#4a4a4a"),
    text("s6_bt2", "moodboards and start storyboarding in Figma?", 830,
         228, 11, "#4a4a4a"),
    ltext("s6_r0", "I'll review the script structure, visual references, "
          "pacing,", 590, 262, 11.5, "#3f3f3f"),
    ltext("s6_r1", "and creative direction from your Milanote board.", 590,
          278, 11.5, "#3f3f3f"),
    ltext("s6_gen", "Generating storyboard flow.....", 590, 312, 11.5,
          "#3f3f3f"),
    ltext("s6_r2", "I'll create editable storyboard frames with structured "
          "layouts,", 590, 344, 11.5, "#3f3f3f"),
    ltext("s6_r3", "visual hierarchy, and scene-by-scene composition.", 590,
          360, 11.5, "#3f3f3f"),
]
tracks.append({"target": "s6_gen", "at": 0.35, "reveal": {
    "unit": "type", "cadence": 0.04, "dur": 0.05, "caret": "none"}})
tracks.append(keyed("s6_gen", opacity=[(0, 0), (0.33, 0), (0.35, 1)]))
for nid, t0 in [("s6_r2", 1.9), ("s6_r3", 2.1)]:
    tracks.append(keyed(nid, opacity=[(t0, 0), (t0 + 0.25, 1)]))
c += [
    rect("s6_rwin", 1165, 428, 385, 512, 12, "#ffffff",
         glow={"sigma": 28, "opacity": 0.18, "color": "#8a8378", "dy": 10}),
    rect("s6_rbar", 1165, 187, 385, 30, 10, "#f3f3f3"),
    ltext("s6_rbc", "Home  /  Figma", 995, 187, 12, "#6a6a6a"),
]
GX = [1050, 1173, 1291]
GY = [295, 371]
for r in range(2):
    for col in range(3):
        c.append(rect(f"s6_g{r}{col}", GX[col], GY[r], 108, 64, 4,
                      "#ececec"))
FILL_T = [0.4, 0.95, 1.5, 2.1, 2.7, 3.3]


def fillfade(nid, t0):
    tracks.append(keyed(nid, opacity=[(t0, 0), (t0 + 0.35, 1)]))


c.append(rect("s6_f0", GX[0], GY[0], 108, 64, 4, "#17171a"))
c.append(text("s6_f0t", "MIRO x SIDEKICKS", GX[0], GY[0], 11, "#ffffff",
              weight=600))
fillfade("s6_f0", FILL_T[0])
fillfade("s6_f0t", FILL_T[0])
c.append(rect("s6_f1", GX[1], GY[1 - 1], 108, 64, 4, "#ffffff"))
c.append(rect("s6_f1c", GX[1] - 6, GY[0] - 8, 22, 22, 11, "#8b2fd6"))
c.append(rect("s6_f1r", GX[1], GY[0] + 18, 70, 8, 2, "#e0e0e0"))
fillfade("s6_f1", FILL_T[1])
fillfade("s6_f1c", FILL_T[1])
fillfade("s6_f1r", FILL_T[1])
c.append(rect("s6_f2", GX[2], GY[0], 108, 64, 4, "#e26bd3",
              gradient={"angle": 0, "stops": [
                  {"at": 0, "color": "#e26bd3"},
                  {"at": 1, "color": "#fef7fd"}]}))
fillfade("s6_f2", FILL_T[2])
c.append(rect("s6_f3", GX[0], GY[1], 108, 64, 4, "#ffffff"))
st = path("s6_f3s", GX[0], GY[1], star4_d(24), "#7b2fd6")
c.append(st)
fillfade("s6_f3", FILL_T[3])
fillfade("s6_f3s", FILL_T[3])
c.append(rect("s6_f4", GX[1], GY[1], 108, 64, 4, "#8b2fd6",
              gradient={"angle": 0, "stops": [
                  {"at": 0, "color": "#8b2fd6"},
                  {"at": 1, "color": "#e08cf0"}]}))
fillfade("s6_f4", FILL_T[4])
c.append(rect("s6_f5", GX[2], GY[1], 108, 64, 4, "#f4f4f6"))
c.append(rect("s6_f5d", GX[2], GY[1], 96, 52, 3, "#2a2a2e"))
fillfade("s6_f5", FILL_T[5])
fillfade("s6_f5d", FILL_T[5])

wn, wt = watermark("s6_")
cn, ct = chrome("s6c_", D1 + D2 + D3 + D4 + D5, D6, [("end", 0, D6)])
tracks += wt + ct
scene("s6", MAT, D6, {"kind": "cut"}, c + wn + cn)

# ============================================================ scene 7
# CTA terracotta: "Customize every frame." then an instant line swap to
# "Analyze & structure every frame."
D7 = 2.333
c = [rect("s7_slide", SLX, SLY, SLW, SLH, 6, CLAY)]
c.append(text("s7_l1", "Customize every frame.", 960, 415, 46, INK,
              weight=600))
c.append(text("s7_l2", "Analyze & structure every frame.", 960, 415, 46,
              INK, weight=600))
tracks.append({"target": "s7_l1", "at": 0.04, "reveal": {
    "unit": "word", "stagger": 0.1, "dur": 0.05, "rise": 0}})
tracks.append(keyed("s7_l1", opacity=[(0, 1), (1.2, 1), (1.21, 0)]))
tracks.append({"target": "s7_l2", "at": 1.22, "reveal": {
    "unit": "word", "stagger": 0.1, "dur": 0.05, "rise": 0}})
tracks.append(keyed("s7_l2", opacity=[(0, 0), (1.21, 0), (1.22, 1)]))
for nid in ["s7_l1", "s7_l2"]:
    tracks.append(keyed(nid, x=[(0, 0.0), (D7, -16.0)]))
wn, wt = watermark("s7_")
cn, ct = chrome("s7c_", D1 + D2 + D3 + D4 + D5 + D6, D7,
                [("end", 0, 0.196), ("cta", 0.196, D7)])
tracks += wt + ct
scene("s7", MAT, D7, {"kind": "cut"}, c + wn + cn)

# ============================================================ scene 8
# end card: "With Claude Design" + clay sunburst, dead-still hold.
D8 = TOTAL - (D1 + D2 + D3 + D4 + D5 + D6 + D7)
c = [rect("s8_slide", SLX, SLY, SLW, SLH, 6, OFF)]
c.append(text("s8_line", "With Claude Design", 935, 414, 52, INK,
              weight=600))
tracks.append({"target": "s8_line", "at": 0.05, "reveal": {
    "unit": "word", "stagger": 0.28, "dur": 0.1, "rise": 0,
    "accent": ACC, "color_delay": 0.28, "color_dur": 0.3}})
sb = path("s8_sun", 1210, 412, sunburst_d(), ACC)
c.append(sb)
tracks.append(keyed("s8_sun", opacity=[(0, 0), (0.75, 0), (0.9, 1)]))
wn, wt = watermark("s8_")
cn, ct = chrome("s8c_", TOTAL - D8, D8, [("cta", 0, D8)])
tracks += wt + ct
scene("s8", MAT, D8, {"kind": "cut"}, c + wn + cn)

# ---------------------------------------------------------------- write
stage = {"fps": 24, "size": [W, H], "scenes": scenes}
with open("docs/claude.stage.json", "w") as f:
    json.dump(stage, f, indent=1)
with open("docs/claude.anim.json", "w") as f:
    json.dump({"tracks": tracks}, f, indent=1)
print("wrote docs/claude.{stage,anim}.json,",
      sum(len(s["nodes"]) for s in scenes), "nodes,",
      len(tracks), "tracks,",
      round(sum(s["dur"] for s in scenes), 3), "s")
