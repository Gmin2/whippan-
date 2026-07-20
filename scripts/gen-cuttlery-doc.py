#!/usr/bin/env python3
# reproduction of cuttlery.mp4 (44.77s, 1280x720): quicksight ep.01, the
# brutalist editorial data-story. scene clock matches the real cut frames
# (f560/675/796/1035/1100/1150/1255 at 30fps) so timing lines up with the
# reference. photography is replaced by flat editorial stand-in shapes:
# drawn cutlery, top-view planes, side-view cars, people capsules, panels.
# the viewfinder corner-bracket motif seeds in the car scene and the thesis
# square before resolving into the quicksight logo lockup.
import json
import os

W, H = 1280, 720
GREY = "#f1f2f2"
KELLY = "#35a85c"
LIME = "#bdf24f"
OLIVE = "#a8d84e"
SKY = "#5b96d1"
PANELBLUE = "#7aa8dd"
INK = "#111111"
CHROME = "#d3d7d7"
K = 0.5523

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
scenes, tracks = [], []


def text(id, s, x, y, size, color=INK, weight=500, family="inter"):
    return {"id": id, "type": "text", "text": s, "x": x, "y": y,
            "color": color, "font": {"size": size, "weight": weight,
                                     "family": family}}


def rect(id, x, y, w, h, r, fill, **kw):
    n = {"id": id, "type": "rect", "x": x, "y": y, "w": w, "h": h,
         "radius": r, "fill": fill}
    n.update(kw)
    return n


def path(id, x, y, d, fill, **kw):
    n = {"id": id, "type": "path", "x": x, "y": y, "d": d, "fill": fill}
    n.update(kw)
    return n


def circle_d(r, cx=0, cy=0):
    k = r * K
    return (f"M{cx-r:.1f} {cy:.1f}C{cx-r:.1f} {cy-k:.1f} {cx-k:.1f} "
            f"{cy-r:.1f} {cx:.1f} {cy-r:.1f}C{cx+k:.1f} {cy-r:.1f} "
            f"{cx+r:.1f} {cy-k:.1f} {cx+r:.1f} {cy:.1f}C{cx+r:.1f} "
            f"{cy+k:.1f} {cx+k:.1f} {cy+r:.1f} {cx:.1f} {cy+r:.1f}"
            f"C{cx-k:.1f} {cy+r:.1f} {cx-r:.1f} {cy+k:.1f} {cx-r:.1f} "
            f"{cy:.1f}Z")


def ellipse_d(rx, ry, cx=0, cy=0):
    kx, ky = rx * K, ry * K
    return (f"M{cx-rx:.1f} {cy:.1f}C{cx-rx:.1f} {cy-ky:.1f} {cx-kx:.1f} "
            f"{cy-ry:.1f} {cx:.1f} {cy-ry:.1f}C{cx+kx:.1f} {cy-ry:.1f} "
            f"{cx+rx:.1f} {cy-ky:.1f} {cx+rx:.1f} {cy:.1f}C{cx+rx:.1f} "
            f"{cy+ky:.1f} {cx+kx:.1f} {cy+ry:.1f} {cx:.1f} {cy+ry:.1f}"
            f"C{cx-kx:.1f} {cy+ry:.1f} {cx-rx:.1f} {cy+ky:.1f} "
            f"{cx-rx:.1f} {cy:.1f}Z")


def track(nid, at=0.0, **props):
    keys = {}
    for name, seq in props.items():
        out = []
        for k in seq:
            kk = {"t": round(k[0], 4), "v": k[1]}
            if len(k) > 2:
                kk["ease"] = k[2]
            out.append(kk)
        keys[name] = out
    t = {"target": nid, "keys": keys}
    if at:
        t["at"] = round(at, 4)
    tracks.append(t)


def fade_in(nid, at, dur=0.22, rise=0):
    if rise:
        track(nid, at=at, opacity=[(0, 0), (dur, 1)],
              y=[(0, rise), (dur + 0.05, 0, "outCubic")])
    else:
        track(nid, at=at, opacity=[(0, 0), (dur, 1)])


def word_reveal(nid, at, accent=None, keep=None, stagger=0.09, rise=14):
    r = {"unit": "word", "stagger": stagger, "dur": 0.24, "rise": rise}
    if accent:
        r["accent"] = accent
        r["color_delay"] = 0.14
        r["color_dur"] = 0.28
    if keep:
        r["keep"] = keep
    tracks.append({"target": nid, "at": round(at, 3), "reveal": r})


def hardstep(nid, spans, at=0.0):
    # spans: list of (t_on, t_off or None). builds 1ms-step opacity keys.
    ks = []
    if spans[0][0] > 0:
        ks.append((0, 0))
    for a, b in spans:
        if ks and ks[-1][1] == 0:
            ks.append((a - 0.001, 0))
        ks.append((a, 1))
        if b is not None:
            ks.append((b - 0.001, 1))
            ks.append((b, 0))
    track(nid, at=at, opacity=[(t, v) for t, v in ks])


def drift(nid, dx, dy, period, rot0=None, drot=0.0):
    # perpetual slow drift loop; rot is absolute so restate the base.
    keys = {"x": [{"t": 0, "v": 0},
                  {"t": period / 2, "v": dx, "ease": "inOutCubic"},
                  {"t": period, "v": 0, "ease": "inOutCubic"}],
            "y": [{"t": 0, "v": 0},
                  {"t": period / 2, "v": dy, "ease": "inOutCubic"},
                  {"t": period, "v": 0, "ease": "inOutCubic"}]}
    if rot0 is not None:
        keys["rot"] = [{"t": 0, "v": rot0},
                       {"t": period / 2, "v": rot0 + drot,
                        "ease": "inOutCubic"},
                       {"t": period, "v": rot0, "ease": "inOutCubic"}]
    tracks.append({"target": nid, "loop": True, "keys": keys})


def scene(id, bg, dur, nodes, kind="cut", tdur=None, dir=None):
    tr = {"kind": kind}
    if tdur:
        tr["dur"] = tdur
    if dir:
        tr["dir"] = dir
    scenes.append({"id": id, "bg": bg, "dur": round(dur, 4),
                   "transition": tr, "nodes": nodes})


# ---------------------------------------------------------------- shapes

FORK_D = ("M-24 -100L-18 -100L-18 -55L-24 -55Z"
          "M-10 -100L-4 -100L-4 -55L-10 -55Z"
          "M4 -100L10 -100L10 -55L4 -55Z"
          "M18 -100L24 -100L24 -55L18 -55Z"
          "M-26 -58L26 -58L14 -28L-14 -28Z"
          "M-7 -30L7 -30L9 100C9 107 -9 107 -9 100Z")

KNIFE_D = ("M-9 -115L3 -115C13 -92 15 -52 12 -12L-9 -12Z"
           "M-9 -12L11 -12L11 100C11 107 -9 107 -9 100Z")

SPOON_D = (ellipse_d(26, 35, 0, -72) +
           "M-7 -42L7 -42L9 100C9 107 -9 107 -9 100Z")

PLANE_D = ("M0 -170C9 -170 14 -150 15 -120L15 100C15 122 10 136 0 152"
           "C-10 136 -15 122 -15 100L-15 -120C-14 -150 -9 -170 0 -170Z"
           "M14 -28L150 64L150 82L14 44Z"
           "M-14 -28L-150 64L-150 82L-14 44Z"
           "M10 106L58 142L58 154L10 132Z"
           "M-10 106L-58 142L-58 154L-10 132Z"
           "M18 6L34 6L34 40L18 40Z"
           "M-18 6L-34 6L-34 40L-18 40Z")

CAR_D = ("M-70 14L-70 -6C-52 -10 -44 -24 -22 -26L18 -26C40 -24 52 -12 "
         "70 -8L70 14Z" + circle_d(11, -41, 14) + circle_d(11, 42, 14))

PERSON_D = circle_d(9, 0, -8) + ellipse_d(21, 13, 0, 10)

BOTTLE_D = ("M-5 -36L5 -36L5 -22L14 -15L14 30C14 37 -14 37 -14 30"
            "L-14 -15L-5 -22Z")

ARROW_UP_D = "M0 16L0 -14M-8 -5L0 -14L8 -5"

CLOUD_D = (circle_d(42, -48, 12) + circle_d(56, 4, -6) +
           circle_d(40, 56, 14))


def brackets_d(s, arm, corners="tlbr,tr,bl,br"):
    parts = []
    if "tl" in corners:
        parts.append(f"M{-s} {-s+arm}L{-s} {-s}L{-s+arm} {-s}")
    if "tr" in corners:
        parts.append(f"M{s-arm} {-s}L{s} {-s}L{s} {-s+arm}")
    if "bl" in corners:
        parts.append(f"M{-s} {s-arm}L{-s} {s}L{-s+arm} {s}")
    if "br" in corners:
        parts.append(f"M{s-arm} {s}L{s} {s}L{s} {s-arm}")
    return "".join(parts)


# ============================================ scene 1+2: title -> chart
# the green card is one rect: seed square -> portrait card -> chart field.
n1 = []
CUTLERY1 = [
    ("t_sp1", SPOON_D, 66, 120, 15, 1.05, 10, 5),
    ("t_kn1", KNIFE_D, 600, 150, -35, 1.35, -14, -6),
    ("t_fk1", FORK_D, 1090, 90, 160, 1.25, 12, 7),
    ("t_fk2", FORK_D, 420, 430, -52, 1.45, -10, 5),
    ("t_sp2", SPOON_D, 866, 380, 6, 1.5, 8, -6),
    ("t_kn2", KNIFE_D, 250, 655, -80, 1.2, 12, 4),
    ("t_kn3", KNIFE_D, 1200, 650, -28, 1.15, -8, -5),
]
for nid, d, x, y, r0, sc, dx, dr in CUTLERY1:
    n1.append(path(nid, x, y, d, CHROME, rot=r0,
                   keys={"scale": [{"t": 0, "v": sc}]}))
    drift(nid, dx, dx * 0.7, 6.0, rot0=r0, drot=dr)
    fade_in(nid, 0.25 + (x % 5) * 0.07, 0.4)

n1 += [
    text("t_h1", "Can cutlery save", 170, 356, 34, INK),
    text("t_tag1", "Quicksight", 71, 400, 14, INK, weight=400),
    text("t_tag2", "EP.", 45, 419, 14, INK, weight=400),
    text("t_tag3", "01", 168, 419, 14, INK, weight=400),
    rect("t_acc", 90, 211, 26, 26, 0, KELLY),
]
word_reveal("t_h1", 1.5, stagger=0.2, rise=0)
# the growing green card (drawn above cutlery)
n1.append(rect("t_card", 820, 360, 920, 720, 0, KELLY))
track("t_card",
      opacity=[(1.5, 0), (1.55, 1)],
      x=[(1.5, 295), (3.5, 295), (5.2, 0, "inOutCubic")],
      y=[(1.5, 240), (3.5, 15, "outCubic"), (5.2, 0, "inOutCubic")],
      w=[(1.5, 40), (3.5, 270, "outCubic"), (5.2, 920, "inOutCubic")],
      h=[(1.5, 40), (3.5, 470, "outCubic"), (5.2, 720, "inOutCubic")])
n1 += [
    text("t_c1", "a carbon-intensive", 1115, 360, 26, "#ffffff"),
    text("t_c2", "industry?", 1185, 392, 26, "#ffffff"),
]
track("t_c1", opacity=[(3.7, 0), (3.9, 1), (4.85, 1), (5.0, 0)])
track("t_c2", opacity=[(3.85, 0), (4.05, 1), (4.85, 1), (5.0, 0)])
# title headline swaps to the chart headline on the left strip
track("t_h1", at=5.0, opacity=[(0, 1), (0.2, 0)])
track("t_tag1", opacity=[(2.4, 0), (2.55, 1), (5.0, 1), (5.2, 0)])
track("t_tag2", opacity=[(2.5, 0), (2.65, 1), (5.0, 1), (5.2, 0)])
track("t_tag3", opacity=[(2.5, 0), (2.65, 1), (5.0, 1), (5.2, 0)])
track("t_acc", opacity=[(1.5, 0), (1.6, 1), (5.0, 1), (5.2, 0)])

# chart furniture on the green field
n1 += [
    text("t_j1", "Jet fuel burned", 140, 50, 22, INK),
    text("t_j2", "per day in millions", 156, 80, 22, INK),
    text("t_j3", "of tonnes", 112, 110, 22, INK),
    path("t_upar", 54, 658, ARROW_UP_D, "#111111", stroke=2.5,
         keys={"scale": [{"t": 0, "v": 1.3}]}),
]
for nid, at in [("t_j1", 5.3), ("t_j2", 5.5), ("t_j3", 5.7)]:
    word_reveal(nid, at, stagger=0.12, rise=0)
    track(nid, opacity=[(5.25, 0), (5.3, 1)])
fade_in("t_upar", 5.6, 0.2)
for lbl, y in [("0.5", 8), ("0", 161), ("2", 316), ("1.5", 465),
               ("1", 616)]:
    nid = f"t_ax{lbl.replace('.', '_')}"
    n1.append(text(nid, lbl, 414, y, 15, "#ffffff", weight=400))
    fade_in(nid, 5.4, 0.2)
PLANES = [
    ("1", 655, 528, 0.52, "0.938", 566, 449, "2019", 5.8),
    ("2", 837, 388, 0.66, "1.27", 760, 307, "2030", 6.4),
    ("3", 1019, 262, 0.82, "1.56", 936, 190, "2040", 7.0),
    ("4", 1200, 128, 1.0, "1.92", 1126, 46, "2050", 7.6),
]
for i, px, py, sc, val, vx, vy, yr, at in PLANES:
    stem_h = 660 - py
    n1.append(rect(f"t_st{i}", px, py + stem_h / 2, 3, stem_h, 0,
                   "#ffffff"))
    n1.append(path(f"t_pl{i}", px, py, PLANE_D, "#dde1e1",
                   keys={"scale": [{"t": 0, "v": sc}]}))
    n1.append(rect(f"t_vb{i}", vx, vy, len(val) * 13 + 22, 34, 2,
                   "#ffffff"))
    n1.append(text(f"t_vt{i}", val, vx, vy + 1, 21, INK, weight=500))
    n1.append(text(f"t_yr{i}", yr, px + 12, 681, 15, "#ffffff",
                   weight=400))
    fade_in(f"t_st{i}", at + 0.1, 0.2)
    track(f"t_pl{i}", at=at, opacity=[(0, 0), (0.25, 1)],
          y=[(0, 30), (0.35, 0, "outCubic")])
    fade_in(f"t_vb{i}", at + 0.3, 0.12)
    fade_in(f"t_vt{i}", at + 0.3, 0.12)
    fade_in(f"t_yr{i}", at + 0.15, 0.15)
n1.append(path("t_fork_l", 250, 430, FORK_D, CHROME, rot=115,
               keys={"scale": [{"t": 0, "v": 1.6}]}))
track("t_fork_l", opacity=[(5.3, 0), (5.6, 1)])
drift("t_fork_l", -8, 6, 5.0, rot0=115, drot=4)
scene("s1", GREY, 10.8333, n1)

# ==================================================== scene 3+4: the sky
n2 = []
for i, (cx, cy, sc) in enumerate([(140, 640, 1.3), (430, 690, 1.6),
                                  (760, 660, 1.2), (1060, 700, 1.7)]):
    n2.append(path(f"sk_cl{i}", cx, cy, CLOUD_D, "#ffffff",
                   keys={"scale": [{"t": 0, "v": sc}]}))
    drift(f"sk_cl{i}", 14 if i % 2 else -14, 0, 9.0)
n2.append(path("sk_plane", 645, 380, PLANE_D, "#e4e7e7",
               keys={"scale": [{"t": 0, "v": 1.15}]}))
track("sk_plane", opacity=[(0, 1), (1.4, 1), (1.9, 0)],
      y=[(0, 0), (1.9, -120, "inCubic")])
PEOPLE = [
    ("sk_p0", 215, 430, LIME, 0), ("sk_p1", 130, 500, "#2a2a2a", 15),
    ("sk_p2", 300, 560, "#3a3a3a", -20), ("sk_p3", 210, 630, "#242424", 30),
    ("sk_p4", 385, 615, "#ffffff", 10), ("sk_p5", 900, 120, "#2a2a2a", -12),
    ("sk_p6", 1010, 200, "#333333", 24), ("sk_p7", 1120, 130, LIME, -30),
    ("sk_p8", 950, 300, "#262626", 8), ("sk_p9", 1090, 330, "#ffffff", -18),
]
for nid, x, y, fill, r0 in PEOPLE:
    n2.append(path(nid, x, y, PERSON_D, fill, rot=r0,
                   keys={"scale": [{"t": 0, "v": 2.1}]}))
    drift(nid, 10 if x < 640 else -10, 6, 7.0, rot0=r0, drot=6)
    fade_in(nid, 1.0 + (x % 7) * 0.09, 0.3)
n2 += [
    text("sk_h1", "Aviation", 228, 85, 72, "#ffffff", weight=400),
    text("sk_h2", "has to", 365, 172, 60, "#ffffff", weight=400),
    text("sk_h3", "get creative", 868, 470, 72, "#ffffff", weight=400),
    path("sk_arr", 632, 307, "M-50 0L50 0M20 -22L50 0L20 22", "#ffffff",
         stroke=3),
]
word_reveal("sk_h1", 1.3, rise=0)
word_reveal("sk_h2", 1.8, stagger=0.14, rise=0)
word_reveal("sk_h3", 2.5, accent=LIME, keep=["creative"], stagger=0.16,
            rise=0)
track("sk_h3", opacity=[(2.45, 0), (2.5, 1)])
fade_in("sk_arr", 2.2, 0.25)
scene("s2", SKY, 4.9667, n2, kind="wipe", tdur=1.2, dir="up")

# ======================================================= scene 5: bamboo
n3 = []
STALKS = [(90, 40, "#a9b1ab"), (235, 30, "#b4bbb5"), (30, 22, "#c0c6c1"),
          (1155, 34, "#a9b1ab"), (1245, 26, "#b4bbb5")]
for i, (x, w_, fill) in enumerate(STALKS):
    n3.append(rect(f"bb_s{i}", x, 360, w_, 760, w_ / 2, fill))
    for j in range(4):
        n3.append(rect(f"bb_s{i}j{j}", x, 90 + j * 180, w_ + 4, 7, 3,
                       "#7e857f"))
    ids = [f"bb_s{i}"] + [f"bb_s{i}j{j}" for j in range(4)]
    for nid in ids:
        track(nid, y=[(0, 320), (0.45, 0, "outCubic")])
n3.append(text("bb_word", "Bamboo", 560, 365, 240, KELLY, weight=500))
tracks.append({"target": "bb_word", "at": 0.15, "reveal": {
    "unit": "glyph", "stagger": 0.05, "dur": 0.18, "rise": 0}})
n3 += [text("bb_q", "Qu", 607, 510, 13, INK, weight=400),
       text("bb_ep", "EP.", 617, 529, 13, INK, weight=400)]
fade_in("bb_q", 0.5, 0.15)
fade_in("bb_ep", 0.6, 0.15)
scene("s3", "#fbfbfb", 1.5, n3, kind="wipe", tdur=0.45, dir="up")

# ==================================================== scene 6: Utensils
n4 = [
    path("ut_kn", 105, 355, KNIFE_D, "#4a4d4a",
         keys={"scale": [{"t": 0, "v": 2.2}]}),
    path("ut_fk", 200, 350, FORK_D, "#565956", rot=3,
         keys={"scale": [{"t": 0, "v": 2.3}]}),
    path("ut_sp", 1195, 350, SPOON_D, "#4a4d4a", rot=-4,
         keys={"scale": [{"t": 0, "v": 2.3}]}),
    text("ut_word", "Utensils", 640, 360, 230, INK, weight=500),
    text("ut_t1", "Quicksight", 632, 511, 13, INK, weight=400),
    text("ut_t2", "EP.", 605, 530, 13, INK, weight=400),
    text("ut_t3", "01", 725, 530, 13, INK, weight=400),
]
track("ut_word", scale=[(0, 1.03), (1.3, 1.0, "outCubic")])
for nid, r0, dr in [("ut_kn", 0, -2), ("ut_fk", 3, 2), ("ut_sp", -4, 2)]:
    drift(nid, 4, 3, 2.8, rot0=r0, drot=dr)
for nid in ["ut_t1", "ut_t2", "ut_t3"]:
    track(nid, opacity=[(0.9, 0), (1.0, 1), (1.25, 1), (1.33, 0)])
scene("s4", GREY, 1.3333, n4)

# ============================================= scene 7: plastic counter
n5 = []
PLASTICS = [
    (60, 120, "#5a5d5a", BOTTLE_D, 1.6, 20), (150, 90, "#8fd0a0",
                                              BOTTLE_D, 1.3, -15),
    (320, 130, "#666966", FORK_D, 0.7, 60), (420, 40, "#57b598",
                                             BOTTLE_D, 1.5, 130),
    (740, 95, "#3a3d3a", circle_d(28), 1.0, 0),
    (1035, 80, "#454845", circle_d(24) + circle_d(12, 0, -34), 1.0, 25),
    (1140, 140, "#c8cdc8", BOTTLE_D, 1.7, 160),
    (135, 250, "#535653", "M-40 -8L40 -8L40 8L-40 8Z"
     "M-34 8L-30 26L-26 8ZM-18 8L-14 26L-10 8ZM-2 8L2 26L6 8Z"
     "M14 8L18 26L22 8Z", 1.4, 15),
    (95, 500, "#2e312e", circle_d(26) + "M18 -18L64 -64L72 -56L26 -10Z",
     1.2, 0),
    (575, 615, "#8a8f8a", "M-6 -60L6 -60L8 20C8 26 -8 26 -8 20Z"
     + circle_d(16, 0, -66), 1.2, -30),
    (800, 590, "#b9bfb9", BOTTLE_D, 1.9, 8),
    (950, 545, "#454845", circle_d(20), 1.0, 0),
    (1175, 470, "#57b598", "M-24 -50L24 -50L30 40C30 48 -30 48 -30 40Z"
     "M-8 -50L-8 -70L8 -70L8 -50Z", 1.6, -5),
    (1035, 615, "#3a3d3a", circle_d(24) + circle_d(10, 0, 0), 1.1, 0),
    (330, 660, "#9ba09b", BOTTLE_D, 1.5, -12),
    (1220, 260, "#c8cdc8", ellipse_d(16, 40), 1.1, 40),
]
for i, (x, y, fill, d, sc, r0) in enumerate(PLASTICS):
    nid = f"pl_o{i}"
    n5.append(path(nid, x, y, d, fill, rot=r0,
                   keys={"scale": [{"t": 0, "v": sc}]}))
    drift(nid, 9 if i % 2 else -9, 6, 6.5, rot0=r0, drot=5)
VALUES = ["2.5", "2.8", "3.2", "3.4M", "3.6M", "3.9M", "4.1M", "4.3M"]
for i, v in enumerate(VALUES):
    nid = f"pl_v{i}"
    n5.append(text(nid, v, 575, 378, 200, INK, weight=500))
    t_on = 0.35 + i * 0.27
    t_off = 0.35 + (i + 1) * 0.27 if i < len(VALUES) - 1 else None
    hardstep(nid, [(t_on, t_off)])
n5.append(text("pl_lbs", "lbs", 880, 420, 64, INK, weight=500))
fade_in("pl_lbs", 2.25, 0.12)
n5 += [
    text("pl_cap1", "Cut on plastic use annualy", 917, 479, 15, INK,
         weight=400),
    text("pl_cap2", "from Airlinetk", 875, 498, 15, INK, weight=400),
]
tracks.append({"target": "pl_cap1", "at": 2.4, "reveal": {
    "unit": "type", "cadence": 0.02, "dur": 0.05, "caret": "bar",
    "caret_typing": "hidden"}})
fade_in("pl_cap2", 3.0, 0.15)
scene("s5", OLIVE, 3.8333, n5)

# ============================================== scene 8: 1,300 cars
n6 = []
for i, y in enumerate([188, 383, 690]):
    n6.append(rect(f"cr_gl{i}", 640, y, 1280, 1, 0, "#2c2c2c"))
    fade_in(f"cr_gl{i}", 0.5 + i * 0.1, 0.3)
# the lime capture square + reticle, pulling back to a dot
n6.append(rect("cr_sq", 640, 360, 330, 330, 0, LIME))
n6.append(path("cr_ret", 640, 360, brackets_d(200, 46), LIME, stroke=4))
for nid in ["cr_sq", "cr_ret"]:
    track(nid, scale=[(0, 2.4), (1.25, 0.13, "inOutCubic")],
          opacity=[(0, 1), (1.5, 1), (1.75, 0)])
n6 += [
    text("cr_h1", "That's the", 300, 150, 76, "#f4f4f4", weight=300),
    text("cr_h2", "weight", 230, 252, 76, "#f4f4f4", weight=300),
    text("cr_h3", "of", 122, 348, 76, "#f4f4f4", weight=300),
    path("cr_upar", 95, 492, ARROW_UP_D, LIME, stroke=2.5,
         rot=45),
    text("cr_cars", "Cars", 468, 570, 84, "#e8e8e8", weight=400),
    text("cr_cap1", "Cut on plastic use annualy", 672, 75, 14, "#dddddd",
         weight=400),
    text("cr_cap2", "from AirLinetk", 630, 94, 14, "#dddddd", weight=400),
    path("cr_dnar", 560, 125, ARROW_UP_D, KELLY, stroke=2.5, rot=225),
]
word_reveal("cr_h1", 1.4, stagger=0.12, rise=0)
word_reveal("cr_h2", 1.65, rise=0)
word_reveal("cr_h3", 1.85, rise=0)
fade_in("cr_upar", 2.1, 0.2)
fade_in("cr_cars", 2.3, 0.2)
fade_in("cr_cap1", 1.1, 0.2)
fade_in("cr_cap2", 1.2, 0.2)
fade_in("cr_dnar", 1.3, 0.2)
n6.append(text("cr_n1", "1,250", 200, 568, 84, LIME, weight=400))
n6.append(text("cr_n2", "1,300", 200, 568, 84, LIME, weight=400))
hardstep("cr_n1", [(2.2, 3.05)])
hardstep("cr_n2", [(3.05, None)])
CARS = [
    (1050, 148, "#3a3d3a", -6), (935, 200, LIME, 4),
    (1065, 232, "#3fae63", -3), (850, 268, "#e9e9e9", 5),
    (948, 335, "#2f9c55", -5), (1082, 305, LIME, 3),
    (828, 410, LIME, -4), (1058, 392, "#e9e9e9", 6),
    (878, 470, "#3fae63", -2), (1092, 465, "#494c49", 4),
    (820, 532, "#2f9c55", -5), (1038, 535, LIME, 3),
    (895, 597, "#e9e9e9", 2), (1118, 592, "#3fae63", -3),
]
for i, (x, y, fill, r0) in enumerate(CARS):
    nid = f"cr_c{i}"
    n6.append(path(nid, x, y, CAR_D, fill, rot=r0,
                   keys={"scale": [{"t": 0, "v": 0.9}]}))
    at = 1.0 + i * 0.18
    track(nid, at=at, opacity=[(0, 0), (0.05, 1)],
          y=[(0, -420), (0.4, 0, "outCubic")],
          rot=[(0, r0 - 14), (0.45, r0, "outCubic")])
n6 += [text("cr_lbl1", "Car", 742, 575, 13, "#cccccc", weight=400),
       text("cr_lbl2", "Car", 1200, 440, 13, "#cccccc", weight=400)]
fade_in("cr_lbl1", 3.2, 0.15)
fade_in("cr_lbl2", 3.4, 0.15)
scene("s6", "#0a0a0a", 4.0333, n6)

# ==================================== scene 9: a practical alternative
n7 = [
    rect("pa_blk", 263, 450, 424, 300, 0, "#161616"),
    rect("pa_lime", 625, 660, 302, 120, 0, LIME),
    rect("pa_bsq", 808, 569, 60, 60, 0, "#161616"),
    rect("pa_gsq1", 1225, 42, 110, 88, 0, "#c9cdcd"),
    rect("pa_gsq2", 1222, 660, 112, 120, 0, "#1d5c35"),
    path("pa_plane", 455, 345, PLANE_D, "#dde1e1", rot=90,
         keys={"scale": [{"t": 0, "v": 1.05}]}),
    rect("pa_br1", 870, 265, 150, 96, 18, "#b9bdb9"),
    rect("pa_br1b", 870, 233, 150, 22, 8, "#5c5f5c"),
    rect("pa_br2", 1043, 400, 150, 96, 18, "#a9ada9"),
    rect("pa_br2b", 1043, 368, 150, 22, 8, "#4c4f4c"),
    path("pa_ar1", 745, 230, ARROW_UP_D, "#ffffff", stroke=2.5),
    path("pa_ar2", 912, 375, ARROW_UP_D, "#ffffff", stroke=2.5, rot=45),
    path("pa_hex", 1157, 432, circle_d(13), LIME),
    text("pa_h1", "It's a practical", 115, 40, 26, "#ffffff"),
    text("pa_h2", "alternative", 92, 69, 26, "#ffffff"),
    text("pa_h3", "to other  efforts", 510, 68, 26, "#ffffff"),
    text("pa_l1", "Aircraft", 582, 437, 14, "#ffffff", weight=400),
    text("pa_l2", "Decarbonization", 742, 437, 24, "#ffffff"),
    text("pa_l3", "Efforts", 677, 466, 24, "#ffffff"),
    text("pa_cap1", "Sure, airlines can turn used cooking oil", 230, 640,
         14, "#eaf5ee", weight=400),
    text("pa_cap2", "and food waste into sustainable aviation fuel.", 250,
         660, 14, "#eaf5ee", weight=400),
]
word_reveal("pa_h1", 0.15, stagger=0.1, rise=0)
word_reveal("pa_h3", 0.6, stagger=0.12, rise=0)
track("pa_h2", opacity=[(0.4, 0), (0.55, 1)])
track("pa_blk", x=[(0, -450), (0.45, 0, "outCubic")])
track("pa_lime", y=[(0, 150), (0.5, 0, "outCubic")])
for nid, at in [("pa_plane", 0.3), ("pa_br1", 0.55), ("pa_br1b", 0.55),
                ("pa_br2", 0.7), ("pa_br2b", 0.7), ("pa_ar1", 0.85),
                ("pa_ar2", 0.9), ("pa_hex", 1.0), ("pa_bsq", 0.8),
                ("pa_gsq1", 0.4), ("pa_gsq2", 0.6)]:
    fade_in(nid, at, 0.2)
for nid, at in [("pa_l1", 1.0), ("pa_l2", 1.1), ("pa_l3", 1.2),
                ("pa_cap1", 1.5), ("pa_cap2", 1.65)]:
    fade_in(nid, at, 0.2)
drift("pa_plane", 6, 0, 4.0, rot0=90, drot=0)
scene("s7", KELLY, 2.8, n7)

# ================================== scene 10: sustainable aviation fuel
n8 = [
    rect("sf_grey", 646, 186, 407, 372, 0, "#e8eae8"),
    rect("sf_blue", 646, 546, 407, 348, 0, SKY),
    path("sf_cl1", 580, 500, CLOUD_D, "#ffffff",
         keys={"scale": [{"t": 0, "v": 0.9}]}),
    path("sf_cl2", 730, 620, CLOUD_D, "#f2f6f9",
         keys={"scale": [{"t": 0, "v": 0.8}]}),
    rect("sf_blue2", 1065, 420, 430, 600, 0, SKY),
    path("sf_cl3", 1100, 480, CLOUD_D, "#ffffff",
         keys={"scale": [{"t": 0, "v": 1.0}]}),
    rect("sf_blk", 221, 546, 443, 348, 0, "#141414"),
    path("sf_bottle", 640, 150, BOTTLE_D, "#2a2d2a", rot=115,
         keys={"scale": [{"t": 0, "v": 3.4}]}),
    rect("sf_stream", 888, 400, 5, 380, 0, "#dfe9f2"),
    path("sf_fin", 1120, 500, "M-160 280L40 -240C70 -290 120 -290 140 "
         "-240L160 280Z", "#1f1f1f"),
    path("sf_fin_s1", 1120, 470, "M-60 40L120 -60L120 -20L-60 80Z",
         "#e8e8e8"),
    path("sf_fin_s2", 1120, 580, "M-80 60L120 -40L120 0L-80 100Z",
         "#dadada"),
    text("sf_h1", "Sustainable", 135, 306, 26, "#ffffff"),
    text("sf_h2", "Aviation", 116, 346, 26, "#ffffff"),
    text("sf_h3", "Fuel", 95, 386, 26, "#ffffff"),
    path("sf_ar", 400, 640, ARROW_UP_D, "#ffffff", stroke=2.5, rot=225),
]
track("sf_grey", opacity=[(0, 0), (0.25, 1), (4.2, 1), (4.201, 0)])
fade_in("sf_blue", 0.35, 0.2)
fade_in("sf_blue2", 0.5, 0.2)
for nid, at in [("sf_cl1", 0.5), ("sf_cl2", 0.6), ("sf_cl3", 0.7)]:
    fade_in(nid, at, 0.25)
track("sf_blk", opacity=[(0, 0), (0.001, 0), (2.1, 0), (2.101, 1)])
fade_in("sf_bottle", 0.6, 0.25)
track("sf_stream", opacity=[(0.9, 0), (1.1, 0.9)],
      h=[(0.9, 0), (1.5, 380, "outCubic")])
track("sf_fin", y=[(0.4, 420), (1.1, 0, "outCubic")],
      opacity=[(0.4, 0), (0.5, 1)])
track("sf_fin_s1", y=[(0.4, 420), (1.1, 0, "outCubic")],
      opacity=[(0.4, 0), (0.5, 1)])
track("sf_fin_s2", y=[(0.4, 420), (1.1, 0, "outCubic")],
      opacity=[(0.4, 0), (0.5, 1)])
track("sf_h1", opacity=[(0.25, 0), (0.4, 1)])
track("sf_h2", opacity=[(0.55, 0), (0.7, 1), (2.1, 1), (2.3, 0)])
track("sf_h3", opacity=[(0.85, 0), (1.0, 1), (2.1, 1), (2.3, 0)])
fade_in("sf_ar", 3.6, 0.2)
SAF_STEPS = [("sf_s1", "S", 67), ("sf_s2", "SA", 115), ("sf_s3", "SAF", 162)]
for i, (nid, s, cx) in enumerate(SAF_STEPS):
    n8.append(text(nid, s, cx, 480, 190, "#f2f2f2", weight=400))
    t_on = 2.4 + i * 0.3
    t_off = 2.4 + (i + 1) * 0.3 if i < 2 else None
    hardstep(nid, [(t_on, t_off)])
scene("s8", KELLY, 5.1667, n8, kind="fade", tdur=0.2)

# ========================================= scene 11: the takeaway tarmac
n9 = [
    rect("tk_patch1", 300, 620, 700, 260, 0, "#878b8d"),
    rect("tk_patch2", 1000, 150, 620, 340, 0, "#9b9fa1"),
    rect("tk_ln1", 500, 160, 3, 340, 0, "#e6e6e6", rot=38),
    rect("tk_ln2", 940, 210, 3, 280, 0, "#e6e6e6", rot=-24),
    rect("tk_ln3", 210, 590, 3, 320, 0, "#dddddd", rot=14),
    rect("tk_veh1", 770, 92, 62, 36, 4, "#54585a", rot=-18),
    rect("tk_veh2", 985, 298, 70, 40, 4, "#5c6062", rot=68),
    rect("tk_veh3", 1140, 78, 46, 28, 4, "#65696b", rot=12),
    rect("tk_veh4", 1180, 105, 46, 28, 4, "#707476", rot=8),
    path("tk_plane", 648, 400, PLANE_D, "#eceff0",
         keys={"scale": [{"t": 0, "v": 1.95}]}),
    rect("tk_gsq1", 1038, 15, 160, 62, 0, KELLY),
    rect("tk_gsq2", 75, 268, 152, 162, 0, KELLY),
    rect("tk_gsq3", 1200, 527, 125, 120, 0, KELLY),
    rect("tk_gsq4", 1038, 697, 160, 46, 0, "#2f9c55"),
    rect("tk_wsq", 75, 432, 152, 156, 0, "#e9e9e9"),
    rect("tk_panel", 315, 190, 322, 320, 0, PANELBLUE),
    path("tk_pret", 260, 71, brackets_d(16, 9, "tl,br"), "#111111",
         stroke=2, keys={"scale": [{"t": 0, "v": 1.0}]}),
    text("tk_t0", "The Takeaway", 260, 71, 21, INK),
    text("tk_t1", "Rethinking", 272, 131, 28, INK),
    text("tk_t2", "what goes", 273, 180, 28, INK),
    text("tk_t3", "onto the plane", 300, 229, 28, INK),
    path("tk_arr", 420, 313, "M-18 0L18 0M4 -11L18 0L4 11", "#111111",
         stroke=2.5),
    rect("tk_bin", 235, 432, 160, 160, 0, "#161616"),
    rect("tk_foam", 225, 415, 90, 60, 8, "#d9d9d9", rot=-8),
    path("tk_cup", 275, 465, circle_d(22), "#bcbcbc"),
    rect("tk_bin2", 862, 595, 160, 150, 0, "#161616"),
    path("tk_fork2", 862, 598, FORK_D, "#d9dcdc",
         keys={"scale": [{"t": 0, "v": 0.85}]}),
    rect("tk_bsq", 878, 435, 160, 155, 0, "#a8c4e2"),
    path("tk_dnarr", 878, 435, "M0 -40L0 30M-22 8L0 30L22 8", "#111111",
         stroke=3),
]
# reticle brackets need to hug the panel title, not sit at panel corners
n9[16]["x"], n9[16]["y"] = 260, 71
track("tk_panel", x=[(0, -400), (0.4, 0, "outCubic")])
for nid, at in [("tk_pret", 0.35), ("tk_t0", 0.35), ("tk_arr", 1.3),
                ("tk_bin", 0.55), ("tk_foam", 0.6), ("tk_cup", 0.6),
                ("tk_bin2", 0.75), ("tk_fork2", 0.8), ("tk_bsq", 0.9),
                ("tk_dnarr", 0.95), ("tk_gsq1", 0.3), ("tk_gsq2", 0.5),
                ("tk_gsq3", 0.7), ("tk_gsq4", 0.85), ("tk_wsq", 0.6)]:
    fade_in(nid, at, 0.15)
word_reveal("tk_t1", 0.55, rise=0)
word_reveal("tk_t2", 0.8, stagger=0.12, rise=0)
word_reveal("tk_t3", 1.15, stagger=0.12, rise=0)
scene("s9", "#94989a", 2.1667, n9)

# ================================================== scene 12: the globe
n10 = [path("gl_e", 640, 360, circle_d(262), "#86b6e6")]
BLOBS = [(600, 200, 80, 42), (740, 320, 92, 52), (520, 420, 72, 46),
         (680, 520, 86, 40), (480, 280, 56, 36), (760, 190, 48, 30)]
for i, (cx, cy, rx, ry) in enumerate(BLOBS):
    n10.append(path(f"gl_b{i}", cx, cy, ellipse_d(rx, ry), "#eef3f7"))
    drift(f"gl_b{i}", 6 if i % 2 else -6, 0, 5.0)
track("gl_e", rot=[(0, 0), (1.667, 4)])
n10 += [
    rect("gl_pin", 648, 368, 105, 100, 0, LIME),
    path("gl_pin_o", 648, 368, BOTTLE_D, "#232623",
         keys={"scale": [{"t": 0, "v": 1.15}]}),
    rect("gl_pin2", 388, 380, 64, 64, 0, "#2f9c55"),
    path("gl_pin2_o", 388, 380, SPOON_D, "#e2e5e5",
         keys={"scale": [{"t": 0, "v": 0.32}]}),
    rect("gl_ph", 875, 230, 62, 62, 0, "#2a2d2a"),
    rect("gl_a1", 415, 520, 14, 14, 0, LIME),
    rect("gl_a2", 620, 625, 13, 13, 0, "#2f9c55"),
    rect("gl_a3", 917, 273, 12, 12, 0, "#2f9c55"),
    rect("gl_a4", 527, 396, 15, 15, 0, "#111111"),
    rect("gl_a5", 530, 190, 12, 12, 0, "#2f9c55"),
]
for nid, at in [("gl_pin", 0.15), ("gl_pin_o", 0.2), ("gl_pin2", 0.3),
                ("gl_pin2_o", 0.32), ("gl_ph", 0.4), ("gl_a1", 0.3),
                ("gl_a2", 0.4), ("gl_a3", 0.35), ("gl_a4", 0.45),
                ("gl_a5", 0.4)]:
    fade_in(nid, at, 0.15)
drift("gl_pin", 5, 3, 4.0)
drift("gl_pin_o", 5, 3, 4.0)
scene("s10", "#ededed", 1.6667, n10, kind="fade", tdur=0.25)

# =============================================== scene 13: the thesis
n11 = [
    rect("th_sq", 647, 380, 285, 285, 0, KELLY),
    path("th_fk", 585, 295, FORK_D, CHROME, rot=7,
         keys={"scale": [{"t": 0, "v": 1.55}]}),
    path("th_sp", 497, 395, SPOON_D, "#c4c9c9", rot=-16,
         keys={"scale": [{"t": 0, "v": 1.5}]}),
    path("th_kn", 795, 345, KNIFE_D, "#dadedd", rot=13,
         keys={"scale": [{"t": 0, "v": 1.6}]}),
    path("th_ret", 647, 380, brackets_d(170, 34), "#111111", stroke=3),
    text("th_t1", "Sometimes", 154, 362, 26, INK),
    text("th_t2", "the", 100, 391, 26, INK),
    text("th_t3", "simple solution", 254, 391, 26, INK),
    text("th_t4", "is the", 988, 365, 26, INK),
    text("th_t5", "most", 1114, 365, 26, INK),
    text("th_t6", "effective", 1090, 394, 26, INK),
]
track("th_sq", scale=[(0.3, 0.15), (0.85, 1.0, "outCubic")],
      opacity=[(0.3, 0), (0.4, 1)])
for nid, at in [("th_fk", 0.7), ("th_sp", 0.8), ("th_kn", 0.9)]:
    track(nid, at=at, opacity=[(0, 0), (0.25, 1)],
          y=[(0, 26), (0.35, 0, "outCubic")])
drift("th_fk", 4, 3, 4.5, rot0=7, drot=2)
drift("th_sp", -4, 3, 5.0, rot0=-16, drot=-2)
drift("th_kn", 3, -3, 4.2, rot0=13, drot=2)
track("th_ret", scale=[(2.6, 1.5), (2.95, 1.0, "outCubic")],
      opacity=[(2.6, 0), (2.8, 1)])
for nid, at in [("th_t1", 0.05), ("th_t2", 0.5), ("th_t4", 1.1),
                ("th_t5", 1.35)]:
    fade_in(nid, at, 0.12)
word_reveal("th_t3", 0.7, stagger=0.18, rise=0)
track("th_t3", opacity=[(0.65, 0), (0.7, 1)])
fade_in("th_t6", 1.55, 0.12)
scene("s11", GREY, 3.5, n11)

# ============================================ scene 14: quicksight logo
n12 = [
    path("lg_bl", 516, 383, "M0 -26L0 8L30 8", "#111111", stroke=5),
    path("lg_tr", 762, 338, "M-30 -8L0 -8L0 26", "#111111", stroke=5),
    text("lg_word", "Quicksight", 640, 360, 46, INK, weight=700),
]
fade_in("lg_bl", 0.1, 0.1)
fade_in("lg_tr", 0.1, 0.1)
tracks.append({"target": "lg_word", "at": 0.35, "reveal": {
    "unit": "type", "cadence": 0.05, "dur": 0.06, "caret": "block",
    "caret_typing": "hidden", "caret_blink": 0}})
scene("s12", "#f0f0f0", 2.9667, n12)

stage = {"fps": 30, "size": [W, H], "scenes": scenes,
         "audio": {"src": "/assets/audio/pad.m4a", "gain": 0.55,
                   "fade_out": 0.8}}
with open("docs/cuttlery.stage.json", "w") as f:
    json.dump(stage, f, indent=1)
with open("docs/cuttlery.anim.json", "w") as f:
    json.dump({"tracks": tracks}, f, indent=1)
total = sum(s["dur"] for s in scenes)
print("wrote docs/cuttlery.{stage,anim}.json,",
      sum(len(s["nodes"]) for s in scenes), "nodes,", len(tracks),
      f"tracks, {total:.2f}s")
