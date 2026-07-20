#!/usr/bin/env python3
# reproduction of the bevel 3.0 launch video (80s -> ~39s arc). the whole
# film is one soft dissolve: periwinkle->black word rituals, "data" scaling
# to hero with metrics blooming around it, the connect-the-dots B glyph on
# the blue field, the mascot, drawn phone dashboards, and the single hard
# cut saved for the black "Sync your devices" beat. palette and timings
# from analysis/bevel/bevel.md.
import json
import math
import os

W, H = 1920, 1080
INK = "#1f2034"
PERI = "#7c8cf8"
PERI_SOFT = "#98a4f5"
BLUE_CORE = "#8da7fb"
BLUE_EDGE = "#bac5fb"
MASCOT = "#95b0fd"
LIME = "#b0fd00"
RING_GREEN = "#63d704"
MINT = "#edf7f6"
TEAL = "#216150"
DEV_BLACK = "#20232a"
DEV_GRAY = "#5e5e5e"
GRAY = "#9ca1a5"

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
scenes, tracks = [], []


def text(id, s, x, y, size, color=INK, weight=500):
    return {"id": id, "type": "text", "text": s, "x": x, "y": y,
            "color": color, "font": {"size": size, "weight": weight}}


def rect(id, x, y, w, h, r, fill, **kw):
    n = {"id": id, "type": "rect", "x": x, "y": y, "w": w, "h": h,
         "radius": r, "fill": fill}
    n.update(kw)
    return n


def path(id, x, y, d, fill, **kw):
    n = {"id": id, "type": "path", "x": x, "y": y, "d": d, "fill": fill}
    n.update(kw)
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
    r = {"unit": "word", "stagger": 0.24, "dur": 0.3, "rise": 0,
         "accent": PERI, "color_delay": 0.18, "color_dur": 0.3}
    r.update(kw)
    tracks.append({"target": nid, "at": at, "reveal": r})


def scene(id, bg, dur, nodes, kind="fade", tdur=0.5):
    scenes.append({"id": id, "bg": bg, "dur": round(dur, 3),
                   "transition": {"kind": kind, "dur": tdur}, "nodes": nodes})


def arc_d(r, deg0, deg1, steps=48):
    pts = []
    for i in range(steps + 1):
        a = math.radians(deg0 + (deg1 - deg0) * i / steps - 90)
        pts.append(f"{r * math.cos(a):.1f} {r * math.sin(a):.1f}")
    return "M" + "L".join(pts)


def circle_d(r):
    return arc_d(r, 0, 360)


def rise_in(nid, at, dy=26, dur=0.3):
    track(nid, at=at, opacity=[(0, 0), (dur * 0.7, 1)],
          y=[(0, dy), (dur, 0, "outCubic")])


# bevel B mark, two stacked lobes with rounded right ends and a slanted
# left edge. local coords roughly 200x220 about the optical center.
B_TOP = "M-95 -105L25 -105C82 -105 82 -12 25 -12L-72 -12Z"
B_BOT = "M-100 8L15 8C95 8 95 112 15 112L-78 112Z"
# vertex loops for the connect-the-dots constellation (local mark coords),
# one closed chain per lobe so no segment crosses the glyph
B_LOOPS = [
    [(-95, -105), (25, -105), (70, -58), (25, -12), (-72, -12)],
    [(-100, 8), (15, 8), (88, 60), (15, 112), (-78, 112)],
]


def ring(prefix, cx, cy, r, stroke, color, pct, base="#ececf0"):
    return [
        path(prefix + "_base", cx, cy, circle_d(r), base, stroke=stroke),
        path(prefix + "_arc", cx, cy, arc_d(r, 0, 360 * pct), color,
             stroke=stroke),
    ]


# 1 ------------------------------------------ "Most apps collect data" ->
# the word survives, scales to hero, metrics bloom around it
METRICS = [
    ("Lean body mass", "135.3 lbs", 400, 190),
    ("RHR", "55 bpm", 1050, 175),
    ("HRV", "48 ms", 620, 400),
    ("Body fat %", "15%", 1260, 420),
    ("Weight", "135.3 lbs", 480, 690),
    ("VO2max", "44.2", 1390, 700),
    ("Sleep", "9 hours", 620, 935),
    ("Strain", "67%", 1200, 950),
]
n1 = [text("line1", "Most apps collect data", 960, 540, 76)]
reveal("line1", 0.2)
track("line1", x=[(0, 0), (2.4, -140)], opacity=[(2.0, 1), (2.4, 0)])
n1.append(text("datahero", "data", 960, 540, 170, weight=600))
track("datahero", opacity=[(2.0, 0), (2.5, 1)],
      scale=[(2.0, 0.55), (2.6, 1.0, "outCubic")])
for i, (lab, val, mx, my) in enumerate(METRICS):
    lw = len(lab) * 34 * 0.5
    vw = len(val) * 34 * 0.5
    n1.append(text(f"m1l{i}", lab, mx, my, 34, INK, weight=500))
    n1.append(text(f"m1v{i}", val, round(mx + lw / 2 + vw / 2 + 34, 1), my,
                   34, PERI_SOFT))
    at = 2.7 + (i % 4) * 0.12
    rise_in(f"m1l{i}", at, dy=18)
    rise_in(f"m1v{i}", at + 0.05, dy=18)
track("s1", cam_zoom=[(2.4, 1.0), (4.6, 1.07)])
scene("s1", "#ffffff", 4.6, n1, kind="cut")

# 2 ------------------------------- "Bevel" + node dots, blue field blooms
DOTS2 = [(430, 300), (1450, 260), (620, 800), (1380, 830), (960, 210),
         (1560, 560)]
n2 = [rect("bluefield", 960, 540, 2300, 1500, 0, BLUE_CORE, blur=130,
           gradient={"angle": 90, "stops": [
               {"at": 0, "color": BLUE_CORE}, {"at": 1, "color": BLUE_EDGE}]})]
track("bluefield", opacity=[(1.2, 0), (2.5, 1)])
for i, (dx, dy) in enumerate(DOTS2):
    n2.append(path(f"dot2_{i}", dx, dy, circle_d(9), PERI))
    track(f"dot2_{i}", opacity=[(0.15 + i * 0.08, 0), (0.35 + i * 0.08, 1)])
n2.append(text("bevelword", "Bevel", 960, 540, 120, PERI, weight=600))
track("bevelword", opacity=[(0.2, 0), (0.6, 1), (1.7, 1), (2.3, 0)])
scene("s2", "#ffffff", 2.6, n2)

# 3 ----------------- "connects the dots" while the B constellation draws
n3 = [rect("bluefield3", 960, 540, 2300, 1500, 0, BLUE_CORE, blur=130,
           gradient={"angle": 90, "stops": [
               {"at": 0, "color": BLUE_CORE}, {"at": 1, "color": BLUE_EDGE}]})]
SC3 = 2.2
CX3, CY3 = 960, 520
di = si = 0
for loop in B_LOOPS:
    pts = [(CX3 + vx * SC3, CY3 + vy * SC3) for vx, vy in loop]
    for px, py in pts:
        n3.append(path(f"dot3_{di}", round(px, 1), round(py, 1), circle_d(8),
                       "#ffffff"))
        track(f"dot3_{di}", opacity=[(0.1 + di * 0.05, 0),
                                     (0.3 + di * 0.05, 0.9)])
        di += 1
    for i in range(len(pts)):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % len(pts)]
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        d = (f"M{x1 - mx:.1f} {y1 - my:.1f}L{x2 - mx:.1f} {y2 - my:.1f}")
        n3.append(path(f"seg3_{si}", round(mx, 1), round(my, 1), d, "#dfe6ff",
                       stroke=3.0))
        ta = 0.5 + si * 0.17
        track(f"seg3_{si}", opacity=[(ta, 0), (ta + 0.2, 0.85)])
        si += 1
for nid, d in [("bglass_t", B_TOP), ("bglass_b", B_BOT)]:
    n3.append(path(nid, CX3, CY3, d, "#ffffff",
                   keys={"scale": [{"t": 0, "v": SC3}]}))
    track(nid, opacity=[(2.3, 0), (3.1, 0.42)])
for i, (word, wa, wb) in enumerate([("connects", 0.2, 1.1), ("the", 1.1, 1.9),
                                    ("dots", 1.9, 3.3)]):
    n3.append(text(f"w3_{i}", word, 960, 540, 84, "#ffffff", weight=600))
    track(f"w3_{i}", opacity=[(wa, 0), (wa + 0.25, 1), (wb, 1),
                              (min(wb + 0.25, 3.4), 0)])
scene("s3", BLUE_CORE, 3.4, n3)

# 4 ------------- glassy B + "Bevel 3.0" lockup, mascot rises, whiteout
n4 = [rect("bluefield4", 960, 540, 2300, 1500, 0, BLUE_CORE, blur=130,
           gradient={"angle": 90, "stops": [
               {"at": 0, "color": BLUE_CORE}, {"at": 1, "color": BLUE_EDGE}]})]
for nid, d in [("b4_t", B_TOP), ("b4_b", B_BOT)]:
    n4.append(path(nid, 790, 540, d, "#ffffff",
                   keys={"scale": [{"t": 0, "v": 1.0}]}))
    track(nid, opacity=[(0, 0.42), (0.8, 0.55)],
          x=[(0, 170), (0.8, 0, "outCubic")])
n4.append(text("b30", "Bevel 3.0", 1130, 540, 72, "#f2f4ff", weight=500))
track("b30", opacity=[(0.5, 0), (0.9, 1)], x=[(0.5, -30), (0.95, 0,
                                                           "outCubic")])
n4.append(rect("mascot4", 960, 1010, 200, 200, 100, MASCOT, blur=14,
               glow={"sigma": 40, "opacity": 0.7}))
n4.append(rect("m4eyeL", 928, 1000, 34, 46, 17, "#ffffff"))
n4.append(rect("m4eyeR", 992, 1000, 34, 46, 17, "#ffffff"))
for nid in ["mascot4", "m4eyeL", "m4eyeR"]:
    track(nid, at=1.5, opacity=[(0, 0), (0.3, 1)],
          y=[(0, 120), (1.0, -160, "outCubic")])
n4.append(rect("whiteout", 960, 540, 2300, 1500, 0, "#ffffff", blur=120))
track("whiteout", opacity=[(2.3, 0), (3.0, 1)])
scene("s4", BLUE_CORE, 3.0, n4)

# 5 --------------------------- "Your connected health coach" + mascot
n5 = [rect("mascot5", 960, 360, 220, 220, 110, MASCOT, blur=12,
           glow={"sigma": 44, "opacity": 0.6}),
      rect("m5eyeL", 925, 350, 36, 50, 18, "#ffffff"),
      rect("m5eyeR", 995, 350, 36, 50, 18, "#ffffff")]
for nid in ["mascot5", "m5eyeL", "m5eyeR"]:
    tracks.append({"target": nid, "loop": True, "keys": {"y": [
        {"t": 0, "v": 0}, {"t": 1.1, "v": -10, "ease": "inOutCubic"},
        {"t": 2.2, "v": 0, "ease": "inOutCubic"}]}})
n5.append(text("coach", "Your connected health coach", 960, 660, 64))
reveal("coach", 0.3, stagger=0.28)
scene("s5", "#ffffff", 2.6, n5)

# 6 ------------------------------------- the home dashboard, drawn whole
n6 = [rect("dashwash", 960, 540, 2300, 1500, 0, "#e9e7f8", blur=110,
           gradient={"angle": 115, "stops": [
               {"at": 0, "color": "#efe9fa"}, {"at": 1, "color": "#dfe5fb"}]}),
      rect("phone6", 960, 560, 460, 900, 62, "#f7f7fa",
           glow={"sigma": 50, "opacity": 0.35, "color": "#7c8cf8"}),
      text("status6", "3:33", 790, 165, 22, INK, weight=600),
      rect("pill6", 860, 228, 210, 52, 26, "#ffffff"),
      path("rundot6", 782, 228, circle_d(14), "#2fd3a5"),
      text("active6", "Active", 878, 220, 20, INK, weight=600),
      text("until6", "Until changed", 890, 244, 13, GRAY),
      text("wx6", "72°F New York", 1105, 228, 17, GRAY),
      rect("ringcard6", 960, 385, 420, 210, 26, "#ffffff")]
RINGS = [("strain", 830, "#f0a24e", 0.40, "40%", "Strain"),
         ("recov", 960, "#a3e635", 0.41, "41%", "Recovery"),
         ("sleep", 1090, "#8ea1f8", 0.75, "75%", "Sleep")]
for key, rx, col, pct, val, lab in RINGS:
    n6 += ring("r6" + key, rx, 360, 44, 11, col, pct)
    n6.append(text(f"r6{key}_v", val, rx, 360, 24, INK, weight=600))
    n6.append(text(f"r6{key}_l", lab, rx, 442, 18, "#7d7f8e"))
n6 += [
    rect("gmcard6", 960, 590, 420, 170, 24, "#ffffff"),
    text("gm6", "Good morning, John", 895, 535, 21, INK, weight=600),
    text("gm6a", "You hit your sleep goal with solid deep", 950, 575, 15,
         "#8b8d9c"),
    text("gm6b", "and REM sleep. HRV is up, RHR is low —", 950, 600, 15,
         "#8b8d9c"),
    text("gm6c", "strong signs of recovery.", 880, 625, 15, "#8b8d9c"),
    rect("askpill6", 960, 810, 400, 64, 32, "#ffffff"),
    rect("askm6", 800, 810, 38, 38, 19, MASCOT),
    text("ask6", "Ask Bevel anything", 980, 810, 20, "#8b8d9c"),
    text("tabs6", "Home      Journal      Fitness      Biology", 960, 940,
         15, "#a0a2b0"),
]
order = ["phone6", "status6", "pill6", "rundot6", "active6", "until6",
         "wx6", "ringcard6"] + \
    [f"r6{k}_{s}" for k, *_ in RINGS for s in ("base", "arc", "v", "l")] + \
    ["gmcard6", "gm6", "gm6a", "gm6b", "gm6c", "askpill6", "askm6", "ask6",
     "tabs6"]
for i, nid in enumerate(order):
    rise_in(nid, 0.15 + i * 0.03, dy=34, dur=0.4)
track("s6", cam_zoom=[(0, 1.0), (3.6, 1.06)],
      cam_y=[(0, 20), (1.2, 0, "outCubic")])
scene("s6", "#e6e4f7", 3.6, n6)

# 7 --------------------- personalized insights: 41% recovered + cards
n7 = [rect("mintwash7", 960, 540, 2300, 1500, 0, "#d9f6ef", blur=120,
           gradient={"angle": 100, "stops": [
               {"at": 0, "color": "#ddf8f0"}, {"at": 1, "color": MINT}]}),
      text("ins7", "personalized insights", 960, 120, 44)]
reveal("ins7", 0.2, stagger=0.2)
n7 += ring("r7", 960, 330, 130, 26, LIME, 0.41, base="#e3e8e6")
n7 += [text("r7v", "41%", 960, 310, 64, "#5abf07", weight=700),
       text("r7l", "recovered", 960, 372, 30, "#8b8d9c")]
n7 += [
    rect("hrv7", 700, 640, 400, 150, 22, "#ffffff"),
    text("hrv7l", "Resting HRV", 645, 600, 22, "#6f7180", weight=500),
    text("hrv7v", "85 ms", 645, 668, 44, INK, weight=700),
    path("hrv7a", 850, 668, "M-14 8L0 -10L14 8Z", "#4a7df0"),
    rect("hr7", 1220, 640, 400, 150, 22, "#ffffff"),
    text("hr7l", "Resting HR", 1160, 600, 22, "#6f7180", weight=500),
    text("hr7v", "59 bpm", 1170, 668, 44, INK, weight=700),
    path("hr7a", 1370, 668, "M-14 -8L0 10L14 -8Z", "#f0764a"),
    rect("tip7", 960, 880, 820, 150, 22, "#ffffff"),
    text("tip7t", "Time to take it easy", 745, 845, 24, INK, weight=600),
    text("tip7a", "Your recovery is looking low today, and it's not just",
         920, 890, 17, "#8b8d9c"),
    text("tip7b", "a one-off. Your resting HRV is 31.3 ms.", 855, 917, 17,
         "#8b8d9c"),
]
for i, nid in enumerate(["r7_base", "r7_arc", "r7v", "r7l"]):
    rise_in(nid, 0.3 + i * 0.04, dy=26, dur=0.35)
for i, nid in enumerate(["hrv7", "hrv7l", "hrv7v", "hrv7a",
                         "hr7", "hr7l", "hr7v", "hr7a"]):
    rise_in(nid, 0.9 + (i // 4) * 0.15, dy=40, dur=0.4)
for i, nid in enumerate(["tip7", "tip7t", "tip7a", "tip7b"]):
    rise_in(nid, 1.5, dy=44, dur=0.45)
track("s7", cam_zoom=[(0, 1.0), (3.2, 1.05)])
scene("s7", MINT, 3.2, n7)

# 8 -------------- "understand ___ it" with stat cards falling in the gap
n8 = [text("u8a", "understand", 590, 540, 84),
      text("u8b", "it", 1450, 540, 84)]
reveal("u8a", 0.15, stagger=0.2)
reveal("u8b", 0.5, stagger=0.2)
CARDS8 = [
    ("c8a", "Strain Score", "40%", 1075, 460, -8),
    ("c8b", "Total Energy", "654 kCal", 1120, 555, 6),
    ("c8c", "Step Count", "7,384", 1060, 648, -4),
]
for cid, lab, val, cx, cy, rot in CARDS8:
    n8.append(rect(cid, cx, cy, 280, 84, 18, "#ffffff", rot=rot,
                   glow={"sigma": 22, "opacity": 0.25, "color": "#9aa4c8"}))
    n8.append(text(cid + "_l", lab, cx - 55, cy - 16, 19, "#8b8d9c"))
    n8.append(text(cid + "_v", val, cx - 62, cy + 16, 24, INK, weight=700))
for i, (cid, *_rest) in enumerate(CARDS8):
    at = 1.0 + i * 0.18
    for suff in ["", "_l", "_v"]:
        track(cid + suff, at=at, opacity=[(0, 0), (0.2, 1)],
              y=[(0, -240), (0.45, 0, "outCubic")])
scene("s8", "#ffffff", 3.0, n8)

# 9 ------------------- the one dark beat: "Sync your devices", hard cut
n9 = [text("sync1", "Sync your", 960, 460, 68, GRAY, weight=500),
      text("sync2", "devices", 960, 550, 68, GRAY, weight=500),
      path("check9", 960, 700, "M-40 0L-12 30L48 -34", LIME, stroke=11)]
track("sync1", opacity=[(0.05, 0), (0.25, 1)])
track("sync2", opacity=[(0.12, 0), (0.32, 1)])
track("check9", opacity=[(0.6, 0), (0.85, 1)],
      scale=[(0.6, 0.6), (0.95, 1.0, "outCubic")])
scene("s9", "#1e2124", 1.8, n9, kind="cut", tdur=0.1)

# 10 ------------- devices row + "Bevel catches what you'd miss", cut out
n10 = [
    # garmin: gray square watch with straps
    rect("gar_sU", 560, 350, 70, 110, 16, "#8a8a8a"),
    rect("gar_sD", 560, 610, 70, 110, 16, "#8a8a8a"),
    rect("gar_body", 560, 480, 170, 170, 46, DEV_GRAY),
    rect("gar_scr", 560, 480, 124, 124, 34, DEV_BLACK),
    path("gar_chk", 560, 480, "M-22 2L-7 17L26 -19", LIME, stroke=7),
    # apple watch: black rounded rect with straps
    rect("aw_sU", 960, 345, 76, 105, 16, "#3a3d44"),
    rect("aw_sD", 960, 615, 76, 105, 16, "#3a3d44"),
    rect("aw_body", 960, 480, 160, 190, 52, DEV_BLACK),
    path("aw_chk", 960, 480, "M-22 2L-7 17L26 -19", LIME, stroke=7),
    # oura-style ring with a floating check tag
    path("ring_body", 1360, 500, circle_d(70), DEV_BLACK, stroke=30),
    rect("ring_tag", 1360, 360, 64, 64, 32, "#ffffff",
         glow={"sigma": 18, "opacity": 0.3, "color": "#9aa4c8"}),
    path("ring_chk", 1360, 360, "M-15 1L-5 12L18 -13", LIME, stroke=6),
]
groups = [["gar_sU", "gar_sD", "gar_body", "gar_scr", "gar_chk"],
          ["aw_sU", "aw_sD", "aw_body", "aw_chk"],
          ["ring_body", "ring_tag", "ring_chk"]]
for gi, grp in enumerate(groups):
    for nid in grp:
        track(nid, at=0.15 + gi * 0.22, opacity=[(0, 0), (0.25, 1)],
              scale=[(0, 0.85), (0.4, 1.0, "outCubic")])
n10.append(text("miss10", "Bevel catches what you'd miss", 960, 830, 56))
reveal("miss10", 1.3, stagger=0.18)
scene("s10", "#ffffff", 3.2, n10, kind="cut", tdur=0.1)

# 11 ---------------------------------- Biological Age 27.0, number roll
n11 = [rect("mintwash11", 960, 540, 2300, 1500, 0, "#d1fbf7", blur=120,
            gradient={"angle": 100, "stops": [
                {"at": 0, "color": "#d6fbf4"}, {"at": 1, "color": "#e8f8ee"}]}),
       path("dial11", 960, 620, circle_d(330), "#b9d8ce", stroke=3),
       text("bio11", "Biological Age", 960, 300, 56, INK, weight=600),
       text("dates11", "Feb 16 - Feb 22", 960, 372, 30, "#8b8d9c"),
       text("age_a", "27.4", 960, 540, 130, TEAL, weight=700),
       text("age_b", "27.0", 960, 540, 130, TEAL, weight=700),
       text("younger11", "2.8 years younger", 960, 660, 40, "#2fae7d",
            weight=600),
       rect("wkpill11", 960, 750, 320, 56, 28, "#ffffff"),
       text("wk11", "-0.2 from last week", 960, 750, 22, INK, weight=500)]
track("dial11", opacity=[(0.3, 0), (0.8, 0.5)])
rise_in("bio11", 0.2, dy=24, dur=0.35)
rise_in("dates11", 0.3, dy=24, dur=0.35)
track("age_a", opacity=[(0.4, 0), (0.6, 1), (1.1, 1), (1.25, 0)],
      y=[(1.1, 0), (1.25, -34, "outCubic")])
track("age_b", opacity=[(1.1, 0), (1.25, 1)],
      y=[(1.1, 34), (1.25, 0, "outCubic")])
rise_in("younger11", 0.7, dy=24, dur=0.35)
rise_in("wkpill11", 0.9, dy=24, dur=0.35)
rise_in("wk11", 0.95, dy=24, dur=0.35)
track("s11", cam_zoom=[(0, 1.05), (3.2, 1.0)])
scene("s11", MINT, 3.2, n11)

# 12 --------------------------------------------------- "Working as one"
n12 = [text("work12", "Working as one", 960, 540, 84, INK, weight=700)]
reveal("work12", 0.15, stagger=0.16)
scene("s12", "#ffffff", 1.8, n12)

# 13 -------------------------------------------------- Bevel end card
n13 = []
for nid, d in [("b13_t", B_TOP), ("b13_b", B_BOT)]:
    n13.append(path(nid, 800, 540, d, INK,
                    keys={"scale": [{"t": 0, "v": 0.85}]}))
    track(nid, opacity=[(0.2, 0), (0.55, 1)])
n13.append(text("wordmark13", "Bevel", 1075, 545, 96, INK, weight=600))
track("wordmark13", opacity=[(0.6, 0), (1.0, 1)],
      x=[(0.6, -24), (1.05, 0, "outCubic")])
scene("s13", "#ffffff", 3.0, n13)

stage = {"fps": 30, "size": [W, H], "scenes": scenes,
         "audio": {"src": "/assets/audio/pad.m4a", "gain": 0.6,
                   "fade_out": 0.8}}
with open("docs/bevel.stage.json", "w") as f:
    json.dump(stage, f, indent=1)
with open("docs/bevel.anim.json", "w") as f:
    json.dump({"tracks": tracks}, f, indent=1)
total = sum(s["dur"] for s in scenes)
print("wrote docs/bevel.{stage,anim}.json,",
      sum(len(s["nodes"]) for s in scenes), "nodes,", len(tracks),
      f"tracks, {total:.2f}s")
