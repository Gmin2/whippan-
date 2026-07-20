#!/usr/bin/env python3
# reproduction of animations/radio/lucia.mp4 — lucia alonso's demo reel,
# compressed from 32.6s to ~16s. the reel's grammar is the anti-playbook:
# hard butt-cuts between deliberately clashing style cards. real montage
# footage is replaced with drawn style-worlds (paper collage, poster,
# storybook illo, cinematic title, vintage postcard...) that keep each
# clip's palette and type energy; cut rhythm follows the source ramp
# (long early cards, one slow chapter, 0.45-0.6s tail into the outro).
import json
import math
import os

W, H = 1280, 720
CREAM = "#f5e7cc"
INK = "#221f10"
ORANGE = "#f26d06"
OLIVE = "#64830a"
LEAF = "#5f7d1c"
K = 0.5523

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
scenes, tracks = [], []


def text(id, s, x, y, size, color=INK, weight=600, family=None, rot=None):
    n = {"id": id, "type": "text", "text": s, "x": x, "y": y, "color": color,
         "font": {"size": size, "weight": weight}}
    if family:
        n["font"]["family"] = family
    if rot is not None:
        n["rot"] = rot
    return n


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
    return (f"M{cx-r:.1f} {cy:.1f}C{cx-r:.1f} {cy-k:.1f} {cx-k:.1f} {cy-r:.1f} {cx:.1f} {cy-r:.1f}"
            f"C{cx+k:.1f} {cy-r:.1f} {cx+r:.1f} {cy-k:.1f} {cx+r:.1f} {cy:.1f}"
            f"C{cx+r:.1f} {cy+k:.1f} {cx+k:.1f} {cy+r:.1f} {cx:.1f} {cy+r:.1f}"
            f"C{cx-k:.1f} {cy+r:.1f} {cx-r:.1f} {cy+k:.1f} {cx-r:.1f} {cy:.1f}Z")


def track(nid, at=0.0, loop=False, **props):
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
        t["at"] = at
    if loop:
        t["loop"] = True
    tracks.append(t)


def scene(id, bg, dur, nodes, kind="cut", tdur=None):
    tr = {"kind": kind}
    if tdur:
        tr["dur"] = tdur
    scenes.append({"id": id, "bg": bg, "dur": round(dur, 3),
                   "transition": tr, "nodes": nodes})


def wobble(nid, amp_rot=2.0, amp_y=3.0, period=0.9, base_rot=0.0, phase=0.0):
    """gentle hand-set jitter so no card is fully static."""
    track(nid, at=phase, loop=True,
          rot=[(0, base_rot - amp_rot),
               (period / 2, base_rot + amp_rot, "inOutCubic"),
               (period, base_rot - amp_rot, "inOutCubic")],
          y=[(0, -amp_y), (period / 2, amp_y, "inOutCubic"),
             (period, -amp_y, "inOutCubic")])


# 1 ------------------------------------------------------ black cold open
scene("s_black", "#000000", 0.14, [])

# 2 ----------------------------------- olive credit card, scattered words
n = [
    text("cr1", "lucia alonso", 480, 220, 62, ORANGE, 600, rot=-2),
    text("cr2", "curly-haired", 720, 315, 62, ORANGE, 600, rot=3),
    text("cr3", "motion designer", 575, 405, 62, CREAM, 600, rot=-1),
    text("cr4", "demo reel", 830, 498, 62, ORANGE, 600, rot=4),
]
for i, nid in enumerate(["cr1", "cr2", "cr3", "cr4"]):
    track(nid, at=0.04 + i * 0.09,
          opacity=[(-0.02, 0), (0.02, 1)],
          scale=[(0, 0.7), (0.16, 1.0, "outCubic")])
    wobble(nid, amp_rot=1.5, amp_y=2.5, period=0.7 + i * 0.13,
           base_rot=[-2, 3, -1, 4][i])
scene("s_credit", OLIVE, 1.3, n)


# 3 ------------------------------------- kinetic REEL, orange squiggle
def squiggle_d(width=1500, amp=70, waves=3.0, step=22):
    pts = []
    n_pts = int(width / step)
    for i in range(n_pts + 1):
        x = -width / 2 + i * step
        y = amp * math.sin(i / n_pts * waves * 2 * math.pi)
        pts.append((x, y))
    d = f"M{pts[0][0]:.1f} {pts[0][1]:.1f}"
    for x, y in pts[1:]:
        d += f"L{x:.1f} {y:.1f}"
    return d


n = [
    path("sqg", 640, 480, squiggle_d(), ORANGE, stroke=26.0),
    text("krR", "R", 250, 300, 330, "#4b7fc4", 800, rot=-8),
    text("krE1", "E", 540, 420, 330, "#171512", 800, rot=5),
    text("krE2", "E", 820, 270, 330, "#171512", 800, rot=-4),
    text("krL", "L", 1070, 420, 330, "#171512", 800, rot=6),
]
# letters crash through frame, fast slides in opposite directions
track("krR", x=[(0, -520), (0.42, 40, "outCubic"), (1.0, 90)])
track("krE1", y=[(0, 560), (0.4, -20, "outCubic"), (1.0, -60)])
track("krE2", x=[(0, 560), (0.46, -30, "outCubic"), (1.0, -80)])
track("krL", y=[(0, -560), (0.44, 20, "outCubic"), (1.0, 70)])
# squiggle whips left to right under the letters
track("sqg", x=[(0, -900), (0.55, 120, "outCubic"), (1.0, 260)],
      y=[(0, 40), (0.5, -20, "inOutCubic"), (1.0, 10)])
scene("s_reel", CREAM, 1.0, n)

# 4 ------------------------- dark lockup: ghost REEL + multicolor lucia
n = [
    text("ghR", "R", 250, 300, 360, "#2a2a2a", 800, rot=-10),
    text("ghE1", "E", 520, 430, 360, "#262626", 800, rot=6),
    text("ghE2", "E", 860, 280, 360, "#2a2a2a", 800, rot=-5),
    text("ghL", "L", 1080, 430, 360, "#262626", 800, rot=8),
    text("lkl", "l", 465, 320, 120, "#7a9a28", 700, rot=-10),
    text("lku", "u", 540, 345, 120, "#7a9a28", 700, rot=6),
    text("lkc", "c", 625, 335, 120, ORANGE, 700, rot=-4),
    text("lki", "i", 692, 330, 120, ORANGE, 700, rot=3),
    text("lka", "a", 762, 350, 120, ORANGE, 700, rot=8),
    path("lkdot", 712, 262, circle_d(13), ORANGE),
    path("lkleaf", 745, 245, f"M-26 8C-14 -14 14 -18 26 -4C10 16 -14 18 -26 8Z",
         "#6f8f22", rot=-18),
    text("lkreel", "R E E L", 640, 435, 26, CREAM, 600),
]
for i, nid in enumerate(["lkl", "lku", "lkc", "lki", "lka", "lkdot", "lkleaf"]):
    track(nid, at=0.05 + i * 0.06,
          opacity=[(-0.02, 0), (0.03, 1)],
          scale=[(0, 0.4), (0.2, 1.0, "spring")])
track("lkreel", at=0.5, opacity=[(0, 0), (0.15, 1)])
scene("s_lockup", "#141414", 0.9, n)

# 5 ---------------------------- ravie: white caps + paper-square confetti
SQ_COLORS = ["#b52330", "#2d2ab5", "#ce3f9b", "#e8c53a", "#8a8a2a",
             "#1e5c46", "#b52330", "#2d2ab5", "#e8c53a", "#ce3f9b",
             "#1e5c46", "#8a8a2a", "#b52330", "#2d2ab5"]
n = []
rng_pos = [(120, 90), (330, 60), (560, 130), (800, 70), (1030, 110),
           (1180, 260), (90, 300), (250, 560), (480, 620), (720, 590),
           (960, 630), (1150, 540), (620, 300), (410, 420)]
for i, (x, y) in enumerate(rng_pos):
    sz = 55 + (i * 13) % 40
    n.append(rect(f"rvq{i}", x, y, sz, sz, 3, SQ_COLORS[i],
                  rot=(i * 37) % 40 - 20))
    track(f"rvq{i}", loop=True, at=i * 0.05,
          y=[(0, -7), (0.5, 7, "inOutCubic"), (1.0, -7, "inOutCubic")],
          rot=[(0, (i * 37) % 40 - 24), (0.5, (i * 37) % 40 - 16, "inOutCubic"),
               (1.0, (i * 37) % 40 - 24, "inOutCubic")])
n += [
    text("rv", "RAVIE", 640, 360, 220, "#f2ecdf", 900),
    text("rvc1", "AUSTIN BAUWENS", 360, 215, 22, "#f2ecdf", 700),
    text("rvc2", "WILL TAYLOR", 945, 215, 22, "#f2ecdf", 700),
    text("rvc3", "JACKSON REDFORD", 370, 510, 22, "#f2ecdf", 700),
    text("rvc4", "SAM ESSANOUSSI", 920, 510, 22, "#f2ecdf", 700),
]
wobble("rv", amp_rot=0.4, amp_y=2, period=0.85)
scene("s_ravie", "#0d0b09", 0.9, n)

# 6 -------------------------- blackmath: paper-cut caps + red tape curl
n = [
    text("bm", "BLACKMATH", 640, 330, 128, "#16130e", 800),
    path("bmtape", 640, 445,
         "M-260 0L120 0L120 -8L260 -8", "#b52330", stroke=16.0),
    path("bmcurl", 905, 425, "M-16 12a22 22 0 1 0 30 -14", "#b52330",
         stroke=14.0),
    text("bmc", "LOUIE JANNETTY", 640, 520, 20, "#4a443a", 600),
    rect("bmd1", 250, 180, 5, 5, 2, "#5a5348", rot=20),
    rect("bmd2", 1010, 240, 4, 4, 2, "#5a5348", rot=10),
    rect("bmd3", 880, 580, 5, 5, 2, "#5a5348", rot=30),
]
wobble("bm", amp_rot=0.35, amp_y=1.6, period=0.7)
scene("s_blackmath", "#e0dace", 0.5, n)

# 7 ---------------------- meister: riso seam, cream caps, falling kite
n = [
    rect("msband", 640, 120, 1500, 380, 0, "#ce3f9b", rot=-4),
    text("ms", "MEISTER", 640, 330, 150, "#f2e4cf", 800),
    path("mskite", 700, 300, "M0 -55L34 0L0 55L-34 0Z", "#2d2ab5", rot=12),
    path("mstally", 190, 560, "M-24 -18L-16 18M-8 -18L0 18M8 -18L16 18",
         "#e8c53a", stroke=6.0),
    text("msc", "CJ COOK", 1090, 620, 20, "#f2e4cf", 600),
]
track("mskite", y=[(0, -400), (0.6, 320, "inCubic")],
      rot=[(0, -30), (0.6, 60)])
wobble("ms", amp_rot=0.3, amp_y=1.5, period=0.65)
scene("s_meister", "#be3f36", 0.6, n)

# 8 -------------------- future proof 2026: cobalt poster + confetti dots
DOT_COLORS = ["#e0559a", "#1e5c46", "#b52330", "#e8c53a", "#8a8a2a",
              "#16130e", "#e8862e", "#ce3f9b", "#1e5c46", "#e8c53a"]
n = [
    text("fp1", "FUTURE", 560, 250, 150, "#f2ecdf", 800),
    text("fp2", "PROOF", 520, 420, 150, "#f2ecdf", 800),
    text("fp3", "20", 985, 355, 78, "#f2ecdf", 800),
    text("fp4", "26", 1005, 460, 78, "#f2ecdf", 800),
]
for i in range(10):
    x = 200 + (i * 173) % 900
    y = 130 + (i * 271) % 470
    n.append(path(f"fpd{i}", x, y, circle_d(10 + (i * 7) % 8), DOT_COLORS[i]))
    track(f"fpd{i}", loop=True, at=i * 0.04,
          y=[(0, -6), (0.4, 6, "inOutCubic"), (0.8, -6, "inOutCubic")])
wobble("fp1", amp_rot=0.3, amp_y=1.8, period=0.6)
wobble("fp2", amp_rot=0.3, amp_y=1.8, period=0.66, phase=0.1)
scene("s_futureproof", "#4b45cf", 0.6, n)

# 9 --------------- storybook illo: blue worm + green bug, warm paper
n = [
    # orange back scallops
    path("wmb1", 1030, 200, circle_d(60), "#e8a95c"),
    path("wmb2", 1085, 330, circle_d(55), "#e8a95c"),
    path("wmb3", 1110, 460, circle_d(58), "#e8a95c"),
    # worm body: thick bent capsule, head leaning left
    path("wmbody", 950, 470,
         "M-130 250C-150 60 -160 -140 -60 -215C30 -280 130 -240 140 -140"
         "C148 -40 120 120 120 250L-130 250Z", "#576aaf"),
    # face
    path("wmeye1", 880, 300, circle_d(26), "#f4f1e6"),
    path("wmeye2", 968, 295, circle_d(26), "#f4f1e6"),
    path("wmpup1", 888, 302, circle_d(9), "#171512"),
    path("wmpup2", 976, 297, circle_d(9), "#171512"),
    path("wmbrow1", 878, 265, "M-20 6L20 -6", "#171512", stroke=7.0),
    path("wmbrow2", 966, 258, "M-20 -4L20 2", "#171512", stroke=7.0),
    path("wmchk1", 852, 352, circle_d(14), "#c0574f"),
    path("wmchk2", 995, 345, circle_d(14), "#c0574f"),
    path("wmsmile", 925, 350, "M-28 0C-12 16 12 16 28 -2", "#171512",
         stroke=7.0),
    # bitten acorn mound at bottom
    path("wmnut", 560, 630, "M-180 60C-180 -40 180 -40 180 60Z", "#cf7a2e"),
    path("wmcap", 560, 608, "M-190 14L190 14L170 -20L-170 -20Z", "#6b3f1e"),
    # green acorn-bug
    path("wbug", 330, 400, circle_d(52), "#6a8a3a"),
    path("wbugl", 330, 460, "M-24 -6L-32 26M0 0L0 30M24 -6L32 26", "#171512",
         stroke=5.0),
    path("wbuge", 344, 388, circle_d(6), "#171512"),
    # hand-drawn motion ticks
    path("wtick1", 470, 120, "M-10 16L2 -12M8 18L20 -10", "#171512",
         stroke=5.0),
    path("wtick2", 690, 470, "M-10 16L2 -12M8 18L20 -10", "#171512",
         stroke=5.0),
    path("wspark", 760, 130, "M0 -16L0 16M-16 0L16 0", "#e8a03a", stroke=6.0),
]
# worm idle sway; bug hops
track("wmbody", loop=True,
      rot=[(0, -1.6), (0.65, 1.6, "inOutCubic"), (1.3, -1.6, "inOutCubic")])
for nid in ["wmeye1", "wmeye2", "wmpup1", "wmpup2", "wmbrow1", "wmbrow2",
            "wmchk1", "wmchk2", "wmsmile"]:
    track(nid, loop=True,
          x=[(0, -6), (0.65, 6, "inOutCubic"), (1.3, -6, "inOutCubic")])
track("wbug", loop=True,
      y=[(0, 0), (0.18, -26, "outCubic"), (0.38, 0, "inCubic"),
         (0.75, 0)])
track("wbugl", loop=True,
      y=[(0, 0), (0.18, -22, "outCubic"), (0.38, 0, "inCubic"), (0.75, 0)])
track("wbuge", loop=True,
      y=[(0, 0), (0.18, -26, "outCubic"), (0.38, 0, "inCubic"), (0.75, 0)])
scene("s_worm", "#f9dca2", 1.3, n)

# 10 -------------------- pinc: kids-marker scrawl + scribble burst
burst = ""
for i in range(14):
    a = i * 2 * math.pi / 14
    r0, r1 = 130, 240 + (i * 31) % 70
    burst += (f"M{r0*math.cos(a):.1f} {r0*math.sin(a):.1f}"
              f"L{r1*math.cos(a):.1f} {r1*math.sin(a):.1f}")
n = [
    path("pcburst", 640, 350, burst, "#171512", stroke=7.0),
    path("pcloop", 350, 180,
         "M-40 0a40 30 0 1 0 80 0a34 26 0 1 0 -60 -10", "#e0559a",
         stroke=8.0),
    text("pcP", "P", 460, 340, 200, "#3aa34a", 800, rot=-8),
    text("pcI", "I", 590, 330, 200, "#e0559a", 800, rot=5),
    text("pcN", "N", 710, 355, 200, "#e8b53a", 800, rot=-5),
    text("pcC", "C", 850, 335, 200, "#3aa34a", 800, rot=9),
]
for i, nid in enumerate(["pcP", "pcI", "pcN", "pcC"]):
    wobble(nid, amp_rot=3.5, amp_y=4, period=0.42 + i * 0.07,
           base_rot=[-8, 5, -5, 9][i])
track("pcburst", loop=True,
      scale=[(0, 0.94), (0.2, 1.04), (0.4, 0.94)],
      opacity=[(0, 1), (0.19, 1), (0.2, 0.6), (0.39, 0.6), (0.4, 1)])
scene("s_pinc", "#f7f4ec", 0.8, n)

# 11 ------------- technicolor opener: the one slow chapter (space field)
n = [
    path("tcp1", 300, 190, circle_d(44), "#6a5acd",
         glow={"sigma": 30, "opacity": 0.8}),
    path("tcp2", 1020, 480, circle_d(26), "#c47ab8",
         glow={"sigma": 24, "opacity": 0.7}),
    path("tcp3", 880, 150, circle_d(12), "#8fa8e8",
         glow={"sigma": 18, "opacity": 0.8}),
    rect("tcstreak", 640, 300, 900, 3, 1.5, "#dfe6ff",
         glow={"sigma": 16, "opacity": 0.9}),
    text("tck1", "A NEW GENERATION OF CREATIVES", 640, 360, 30,
         "#cfd6ff", 300),
    text("tck2", "SEE THE WORLD THROUGH THEIR EYES", 640, 360, 30,
         "#cfd6ff", 300),
]
track("tck1", opacity=[(0, 0), (0.25, 1, "outCubic"), (0.7, 1),
                       (0.9, 0, "inCubic")])
track("tck2", opacity=[(0, 0), (0.95, 0), (1.15, 1, "outCubic"), (1.5, 1)])
track("tcstreak", opacity=[(0, 0), (0.3, 0.9, "outCubic")],
      w=[(0, 200), (1.5, 1050, "outCubic")])
for i, nid in enumerate(["tcp1", "tcp2", "tcp3"]):
    track(nid, loop=True, at=i * 0.2,
          y=[(0, -5), (0.9, 5, "inOutCubic"), (1.8, -5, "inOutCubic")])
scene("s_space", "#0b0f2c", 1.5, n, kind="fade", tdur=0.4)

# 12 --------------------- "dreaming in TECHNICOLOR" chrome title card
CHROME = ["#7fd4e8", "#6db9e6", "#62a0e0", "#7fc9d8", "#9adf8a", "#d9e87f",
          "#e8cf6d", "#e8a95c", "#e88a6d", "#e87f8a", "#e8a0b0"]
word = "TECHNICOLOR"
n = [
    text("thpres", "RINGLING COLLEGE OF ART AND DESIGN PRESENTS", 640, 95,
         15, "#9aa3c4", 400),
    text("thdream1", "D R E A M I N G", 570, 240, 26, "#e8eaf4", 400),
    text("thdream2", "I N", 736, 240, 26, "#e8eaf4", 400),
    rect("thrule1", 640, 270, 760, 2, 1, "#8f97b8"),
    rect("thrule2", 640, 452, 760, 2, 1, "#8f97b8"),
    text("thyear", "2024 - 2025", 640, 480, 20, "#c9cfe6", 400),
    text("thawards", "TRUSTEE SCHOLAR AWARDS", 640, 620, 15, "#9aa3c4", 400),
]
lw = 72
x0 = 640 - lw * (len(word) - 1) / 2
for i, ch in enumerate(word):
    n.append(text(f"th{i}", ch, round(x0 + i * lw, 1), 360, 116,
                  CHROME[i], 600))
    # light sweep: each letter brightens then settles left to right
    track(f"th{i}", at=0.15 + i * 0.05,
          opacity=[(0, 0.75), (0.12, 1.0, "outCubic")],
          scale=[(0, 0.98), (0.15, 1.0, "outCubic")])
n.append(rect("thsweep", 640, 360, 20, 300, 10, "#ffffff", rot=18,
              blur=14.0))
track("thsweep", opacity=[(0, 0), (0.15, 0.12), (0.85, 0.12), (1.0, 0)],
      x=[(0, -500), (1.0, 500)])
scene("s_tech", "#0b0f2c", 1.2, n, kind="fade", tdur=0.3)

# 13 ------------------ giant: sunset poster, scattered display letters
n = [
    rect("gtbg", 640, 360, 1280, 720, 0, "#e8547a",
         gradient={"angle": 90, "stops": [{"at": 0, "color": "#e8547a"},
                                          {"at": 1, "color": "#e8862e"}]}),
    path("gtcl1", 120, 650, circle_d(150), "#f7f2e8"),
    path("gtcl2", 400, 700, circle_d(120), "#f7f2e8"),
    path("gtcl3", 1120, 640, circle_d(160), "#f7f2e8"),
    path("gtcl4", 880, 710, circle_d(110), "#f7f2e8"),
    path("gtblob1", 90, 30, circle_d(90), "#17130e"),
    path("gtblob2", 1180, 60, circle_d(100), "#17130e"),
    text("gtk1", "SUMMER - 2024", 640, 70, 22, "#f7f2e8", 500, "mono"),
    text("gtk2", "2D ANIMATION APPRENTICE", 640, 100, 22, "#f7f2e8", 500,
         "mono"),
    text("gtG", "G", 350, 250, 170, "#f7f2e8", 700, rot=-14),
    text("gtI", "I", 480, 290, 170, "#f7f2e8", 700, rot=8),
    text("gtA", "A", 610, 300, 170, "#f7f2e8", 700, rot=-6),
    text("gtN", "N", 700, 450, 190, "#f7f2e8", 700, rot=4),
    text("gtT", "T", 1040, 260, 170, "#f7f2e8", 700, rot=10),
]
for i, nid in enumerate(["gtG", "gtI", "gtA", "gtN", "gtT"]):
    wobble(nid, amp_rot=3, amp_y=5, period=0.5 + i * 0.06,
           base_rot=[-14, 8, -6, 4, 10][i])
scene("s_giant", "#e8703a", 0.55, n)

# 14 ------------- anastasia: flat vector mountain + blue outline caps
zig = "M-260 160L-260 60L-190 60L-190 -10L-120 -10L-120 -80L-60 -80" \
      "L-60 -150L60 -150L60 -80L120 -80L120 -10L190 -10L190 60L260 60" \
      "L260 160Z"
n = [
    path("anpk1", 260, 400, "M-200 220L0 -160L200 220Z", "#9ab0b8"),
    path("anpk2", 1030, 410, "M-190 210L0 -140L190 210Z", "#a8bcc4"),
    path("ansnow1", 260, 275, "M-58 55L0 -55L58 55Z", "#f2f4f4"),
    path("ansnow2", 1030, 300, "M-52 50L0 -48L52 50Z", "#f2f4f4"),
    path("anmtn", 640, 430, zig, "#4a8a4f"),
    text("an", "ANASTASIA", 640, 165, 92, "#2d5ac9", 800),
    path("anflag", 640, 258, "M0 22L0 -14L20 -8L0 -2", "#b52330",
         stroke=4.0),
]
wobble("an", amp_rot=0.4, amp_y=2, period=0.5)
scene("s_anastasia", "#cfe3e8", 0.45, n)

# 15 ------------------------ clock card: coral field, green-rim face
dashes = ""
for gy in range(6):
    for gx in range(9):
        x = -560 + gx * 140 + (gy % 2) * 70
        y = -280 + gy * 112
        dashes += f"M{x-14} {y}L{x+14} {y}"
n = [
    path("ckdash", 640, 360, dashes, "#3a55c9", stroke=6.0),
    rect("ckband", 250, 360, 150, 720, 0, "#e8c53a"),
    path("ckrim", 780, 360, circle_d(148), "#4a8a3f"),
    path("ckface", 780, 360, circle_d(128), "#f7f4ec"),
    rect("ckt12", 780, 250, 8, 26, 4, "#b52330"),
    rect("ckt6", 780, 470, 8, 26, 4, "#b52330"),
    rect("ckt3", 890, 360, 26, 8, 4, "#b52330"),
    rect("ckt9", 670, 360, 26, 8, 4, "#b52330"),
    path("ckhh", 780, 360, "M0 0L38 38", "#2d3ab5", stroke=10.0),
    path("ckmh", 780, 360, "M0 0L0 -92", "#2d3ab5", stroke=7.0),
    path("ckpin", 780, 360, circle_d(10), "#b52330"),
]
wobble("ckrim", amp_rot=0.8, amp_y=2, period=0.45)
wobble("ckface", amp_rot=0.8, amp_y=2, period=0.45)
scene("s_clock", "#e8705c", 0.45, n)

# 16 ------------ golden gate postcard: gold slab + red bridge + car
cable = "M-420 -70C-260 40 -100 40 0 -80C100 40 260 40 420 -70"
n = [
    text("gg", "GOLDEN GATE", 640, 260, 118, "#b8912e", 800),
    text("ggk1", "GREETINGS FROM", 250, 160, 24, "#8a6b28", 700),
    text("ggk2", "SAN FRANCISCO", 1030, 160, 24, "#8a6b28", 700),
    path("ggcable", 640, 470, cable, "#d13a2a", stroke=8.0),
    rect("ggtw1", 400, 480, 26, 220, 4, "#d13a2a"),
    rect("ggtw1b", 400, 420, 70, 14, 4, "#d13a2a"),
    rect("ggtw2", 880, 480, 26, 220, 4, "#d13a2a"),
    rect("ggtw2b", 880, 420, 70, 14, 4, "#d13a2a"),
    rect("ggdeck", 640, 570, 1280, 26, 0, "#d13a2a"),
    rect("ggcar", 590, 540, 110, 34, 12, "#b52330"),
    path("ggwh1", 560, 558, circle_d(11), "#17130e"),
    path("ggwh2", 622, 558, circle_d(11), "#17130e"),
    path("ggfig", 400, 395, circle_d(11), "#3a6ac9"),
]
track("ggcar", x=[(0, -260), (0.45, 260)])
track("ggwh1", x=[(0, -260), (0.45, 260)])
track("ggwh2", x=[(0, -260), (0.45, 260)])
wobble("gg", amp_rot=0.3, amp_y=1.5, period=0.5)
scene("s_goldengate", "#efe6d2", 0.5, n)


# 17 ------------------- nike excellence: radar grid + orange starburst
def star_d(n_sp=14, r0=95, r1=150):
    pts = []
    for i in range(n_sp * 2):
        r = r1 if i % 2 == 0 else r0
        a = i * math.pi / n_sp - math.pi / 2
        pts.append((r * math.cos(a), r * math.sin(a)))
    d = f"M{pts[0][0]:.1f} {pts[0][1]:.1f}"
    for x, y in pts[1:]:
        d += f"L{x:.1f} {y:.1f}"
    return d + "Z"


radials = ""
for i in range(12):
    a = i * math.pi / 6
    radials += (f"M{210*math.cos(a):.1f} {210*math.sin(a):.1f}"
                f"L{560*math.cos(a):.1f} {560*math.sin(a):.1f}")
n = [
    path("nkring1", 640, 380, circle_d(200), "#c9b58a", stroke=1.6),
    path("nkring2", 640, 380, circle_d(320), "#c9b58a", stroke=1.6),
    path("nkrad", 640, 380, radials, "#c9b58a", stroke=1.4),
    path("nkstar", 640, 400, star_d(), "#e8821e"),
    rect("nksole", 640, 428, 176, 12, 6, "#17130e"),
    path("nkshoe", 640, 400,
         "M-90 30C-80 -15 -30 -42 20 -38C60 -34 92 -8 95 18"
         "C60 34 -40 44 -90 30Z", "#f4f1ea"),
    path("nkswsh", 660, 405, "M-30 6C-8 -8 18 -12 34 -10C12 4 -8 10 -30 6Z",
         "#2d5ac9"),
    text("nkex", "EXCELLENCE", 640, 170, 62, "#2d5ac9", 700),
    text("nkkick", "NIKECOURT  -  AIR ZOOM VAPOR", 640, 610, 20,
         "#2d5ac9", 700),
    rect("nkd1", 250, 490, 34, 12, 3, "#2d5ac9", rot=32),
    rect("nkd2", 1040, 250, 34, 12, 3, "#2d5ac9", rot=-20),
    rect("nkd3", 1105, 470, 34, 12, 3, "#2d5ac9", rot=70),
    rect("nkd4", 190, 220, 34, 12, 3, "#2d5ac9", rot=-60),
]
track("nkstar", loop=True,
      rot=[(0, 0), (0.5, 6)])
wobble("nkex", amp_rot=0.4, amp_y=2, period=0.45)
scene("s_nike", "#f2ead8", 0.5, n)

# 18 --------------- meet the beatles: 60s comic caps on newspapers
n = [
    rect("btnp1", 640, 620, 620, 120, 4, "#e6ddc6", rot=-5),
    rect("btnp2", 660, 580, 600, 110, 4, "#d9cfb4", rot=3),
    rect("btnp3", 630, 545, 580, 100, 4, "#efe6d2", rot=-2),
    rect("btl1", 560, 545, 300, 6, 3, "#8a8270", rot=-2),
    rect("btl2", 590, 565, 340, 6, 3, "#8a8270", rot=-2),
    path("btbolt1", 250, 260, "M30 -60L-10 0L14 6L-30 60L2 10L-20 4Z",
         "#f2ecdf"),
    path("btbolt2", 1030, 250, "M30 -60L-10 0L14 6L-30 60L2 10L-20 4Z",
         "#f2ecdf", rot=14),
    text("bt1", "MEET THE", 640, 200, 84, "#3a5ac9", 800, rot=-3),
    text("bt2", "BEATLES!", 640, 330, 128, "#3a5ac9", 800, rot=-3),
    text("bt3", "the British Invasion", 640, 445, 30, "#f2ecdf", 400,
         rot=-3),
]
wobble("bt1", amp_rot=0.8, amp_y=2.5, period=0.4, base_rot=-3)
wobble("bt2", amp_rot=0.8, amp_y=2.5, period=0.44, base_rot=-3, phase=0.05)
scene("s_beatles", "#0d0d0d", 0.45, n)

# 19 -------------------- lucia outro: lockup, url shimmer, fade out
un = "LUCIAALONSO.COM"
usz = 22
ucw = usz * 0.6
uleft = 640 - len(un) * ucw / 2


def useg(i0, i1):
    s = un[i0:i1 + 1]
    cx = uleft + (i0 + len(s) / 2) * ucw
    return s, round(cx, 1)


s1, c1 = useg(0, 4)     # LUCIA
s2, c2 = useg(5, 10)    # ALONSO
s3, c3 = useg(11, 14)   # .COM
n = [
    text("otmark", "lucia", 640, 360, 104, INK, 700),
    path("otdot", 668, 292, circle_d(11), ORANGE),
    path("otleaf", 697, 276, "M-24 8C-13 -13 13 -17 24 -4C9 15 -13 17 -24 8Z",
         "#5f8a1e", rot=-22),
    text("oturl", un, 640, 452, usz, INK, 700, "mono"),
    text("oturl1", s1, c1, 452, usz, ORANGE, 700, "mono"),
    text("oturl2", s2, c2, 452, usz, "#5f8a1e", 700, "mono"),
    text("oturl3", s3, c3, 452, usz, ORANGE, 700, "mono"),
    rect("otfade", 640, 360, 1280, 720, 0, "#000000"),
]
# leaf/dot settle in the first frames (cut lands on the hold)
track("otdot", scale=[(0, 0.85), (0.15, 1.0, "outCubic")])
track("otleaf", scale=[(0, 0.85), (0.18, 1.0, "outCubic")])
# traveling accent wave over the url
track("oturl1", opacity=[(0, 0), (0.15, 0), (0.151, 1), (0.65, 1),
                         (0.9, 0)])
track("oturl2", opacity=[(0, 0), (0.7, 0), (0.701, 1), (1.2, 1),
                         (1.45, 0)])
track("oturl3", opacity=[(0, 0), (1.25, 0), (1.251, 1), (1.75, 1),
                         (1.95, 0)])
# fade to black over the last half second
track("otfade", opacity=[(0, 0), (1.6, 0), (2.1, 1, "inCubic"), (2.3, 1)])
scene("s_outro", CREAM, 2.3, n)

stage = {"fps": 30, "size": [W, H], "scenes": scenes,
         "audio": {"src": "/assets/audio/pad.m4a", "gain": 0.6,
                   "fade_out": 0.6}}
with open("docs/lucia.stage.json", "w") as f:
    json.dump(stage, f, indent=1)
with open("docs/lucia.anim.json", "w") as f:
    json.dump({"tracks": tracks}, f, indent=1)
total = sum(s["dur"] for s in scenes)
print("wrote docs/lucia.{stage,anim}.json,",
      sum(len(s["nodes"]) for s in scenes), "nodes,", len(tracks),
      f"tracks, {len(scenes)} scenes, {total:.2f}s")
