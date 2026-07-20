#!/usr/bin/env python3
# reproduction of lovable.mp4 (brew.new launch film), compressed to ~33s at
# 1280x720. the film is one chopped sentence: cream/white/orange word beats
# with a single orange accent word per line, alternating with product proofs
# drawn as flat stand-ins (prompt pill -> builder tablet, contacts table).
# includes the toggle-counter gag (2 -> 8 days, knob widens as the count
# climbs) and the brew end lockup. tokens from the frame teardown.
import json
import os

W, H = 1280, 720
CREAM = "#fdf9ee"
WHITE = "#ffffff"
INK = "#3a2b28"
ORANGE = "#eb6a34"
DEEP = "#f06129"
LIGHT = "#f5aa6a"
SUBMIT = "#ec5a34"
MAUVE = "#8a6a6a"
METAL = "#efe9dc"
K = 0.5523

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
scenes, tracks = [], []


def text(id, s, x, y, size, color=INK, weight=600, family=None):
    f = {"size": size, "weight": weight}
    if family:
        f["family"] = family
    return {"id": id, "type": "text", "text": s, "x": x, "y": y,
            "color": color, "font": f}


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
    return (f"M{cx-r} {cy}C{cx-r} {cy-k} {cx-k} {cy-r} {cx} {cy-r}"
            f"C{cx+k} {cy-r} {cx+r} {cy-k} {cx+r} {cy}"
            f"C{cx+r} {cy+k} {cx+k} {cy+r} {cx} {cy+r}"
            f"C{cx-k} {cy+r} {cx-r} {cy+k} {cx-r} {cy}Z")


SPARK = ("M0 -16C2 -5 5 -2 16 0C5 2 2 5 0 16"
         "C-2 5 -5 2 -16 0C-5 -2 -2 -5 0 -16Z")
STEAM_TOP = "M20 -70C-40 -46 46 -32 -16 -8"
STEAM_BOT = "M20 4C-40 28 46 42 -16 66"


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


def scene(id, bg, dur, nodes, kind="fade", tdur=0.25):
    scenes.append({"id": id, "bg": bg, "dur": round(dur, 3),
                   "transition": {"kind": kind, "dur": tdur}, "nodes": nodes})


_ofn = [0]


def ofield():
    _ofn[0] += 1
    return rect(f"of{_ofn[0]}", W / 2, H / 2, W, H, 0, DEEP, gradient={
        "angle": 135, "stops": [{"at": 0, "color": LIGHT},
                                {"at": 1, "color": DEEP}]})


def cascade(ids, at=0.25, step=0.04, rise=0):
    for i, nid in enumerate(ids):
        a = at + i * step
        if rise:
            track(nid, at=a, opacity=[(0, 0), (0.2, 1)],
                  y=[(0, rise), (0.3, 0, "outCubic")])
        else:
            track(nid, at=a, opacity=[(0, 0), (0.2, 1)])


# 1 ------------------------------------------- cream intro: Today / it takes
n1 = [
    text("t_today", "Today", 580, 360, 150, INK, weight=700),
    text("t_takes", "it takes", 580, 360, 150, INK, weight=700),
    path("btn1", 1120, 400, circle_d(45), "#2a1f1c"),
    path("btn1_a", 1120, 400, "M-11 0L11 0M3 -8L11 0L3 8", ORANGE, stroke=4.5),
]
tracks.append({"target": "t_today", "reveal": {
    "unit": "glyph", "stagger": 0.05, "dur": 0.3, "rise": 44,
    "accent": INK}})
track("t_today", at=1.05, opacity=[(0, 1), (0.18, 0)])
track("t_takes", opacity=[(0, 0), (1.23, 0), (1.25, 1)])
tracks.append({"target": "t_takes", "at": 1.25, "reveal": {
    "unit": "word", "stagger": 0.06, "dur": 0.28, "rise": 34, "accent": INK}})
cascade(["btn1", "btn1_a"], at=0.3, step=0.0)
track("s1", cam_zoom=[(0, 1.0), (2.2, 1.0), (2.55, 1.5, "inCubic")])
scene("s1", CREAM, 2.55, n1, kind="cut")

# 2 -------------------------------- black toggle counter: 2 days -> 8 days
n2 = [
    rect("tg_out", 640, 360, 1010, 430, 215, "#2f2b28"),
    rect("tg_in", 640, 360, 986, 406, 203, "#000000"),
    rect("tg_knob", 350, 360, 370, 370, 185, "#241b17"),
    text("tg_days", "days", 760, 360, 190, METAL, weight=600),
]
for k in range(2, 9):
    n2.append(text(f"tg_d{k}", str(k), 340, 360, 210, METAL, weight=600))
t0, step = 0.25, 0.24
wk = lambda k: 370 + (k - 2) * 65
knob_w = [(0, 370)]
knob_x = [(0, 0)]
for k in range(3, 9):
    tk = t0 + (k - 2) * step
    knob_w.append((tk, wk(k), "outCubic"))
    knob_x.append((tk, (wk(k) - 370) / 2, "outCubic"))
track("tg_knob", w=knob_w, x=knob_x)
for k in range(2, 9):
    on = 0 if k == 2 else t0 + (k - 2) * step
    off = t0 + (k - 1) * step
    seq = []
    if k > 2:
        seq += [(0, 0), (on, 0), (on + 0.002, 1)]
    else:
        seq += [(0, 1)]
    if k < 8:
        seq += [(off, 1), (off + 0.002, 0)]
    track(f"tg_d{k}", opacity=seq)
track("tg_days", opacity=[(0, 0), (t0 + step, 0), (t0 + step + 0.002, 1)])
track("tg_out", opacity=[(0, 0), (0.12, 1)])
track("tg_in", opacity=[(0, 0), (0.12, 1)])
track("tg_knob", at=0, scale=[(0, 0.9), (0.25, 1.0, "outCubic")])
scene("s2", "#000000", 2.55, n2, kind="cut", tdur=0.1)

# 3 --------------------------- black code scene: to {{create}} in monospace
n3 = [
    text("c_to", "to", 442, 360, 60, WHITE, weight=500, family="mono"),
    text("c_b1", "{{", 550, 362, 60, MAUVE, weight=500, family="mono"),
    text("c_cr", "create", 694, 360, 60, WHITE, weight=500, family="mono"),
    text("c_b2", "}}", 838, 362, 60, MAUVE, weight=500, family="mono"),
]
tracks.append({"target": "c_to", "at": 0.1, "reveal": {
    "unit": "type", "cadence": 0.07, "dur": 0.08}})
tracks.append({"target": "c_b1", "at": 0.4, "reveal": {
    "unit": "type", "cadence": 0.06, "dur": 0.08}})
tracks.append({"target": "c_cr", "at": 0.55, "reveal": {
    "unit": "type", "cadence": 0.05, "dur": 0.08, "caret": "bar",
    "caret_typing": "hidden"}})
tracks.append({"target": "c_b2", "at": 0.95, "reveal": {
    "unit": "type", "cadence": 0.06, "dur": 0.08}})
scene("s3", "#000000", 1.53, n3, kind="fade", tdur=0.2)

# 4 ------------------------------------------------- cream: an email flash
n4 = [text("t_anemail", "an email", 640, 360, 120, INK, weight=700)]
tracks.append({"target": "t_anemail", "at": 0.05, "reveal": {
    "unit": "word", "stagger": 0.08, "dur": 0.26, "rise": 38, "accent": INK}})
scene("s4", CREAM, 1.02, n4, kind="cut", tdur=0.1)

# 5 ------------------------- white: Let's change that ("change" orange)
n5 = [
    text("l_lets", "Let's", 400, 360, 72, "#2e2624", weight=600),
    text("l_change", "change", 634, 360, 72, ORANGE, weight=600),
    text("l_that", "that", 850, 360, 72, "#2e2624", weight=600),
    path("l_sp1", 700, 288, SPARK, ORANGE),
    path("l_sp2", 748, 262, SPARK, ORANGE),
]
tracks.append({"target": "l_lets", "at": 0.15, "reveal": {
    "unit": "type", "cadence": 0.06, "dur": 0.08}})
tracks.append({"target": "l_change", "at": 0.55, "reveal": {
    "unit": "type", "cadence": 0.06, "dur": 0.08}})
tracks.append({"target": "l_that", "at": 1.0, "reveal": {
    "unit": "type", "cadence": 0.06, "dur": 0.08, "caret": "bar",
    "caret_typing": "hidden"}})
for nid, a, sc in [("l_sp1", 0.95, 0.9), ("l_sp2", 1.1, 0.6)]:
    track(nid, at=a, opacity=[(0, 0), (0.12, 1)],
          scale=[(0, 0.2), (0.3, sc, "outCubic")])
scene("s5", WHITE, 2.04, n5, kind="fade", tdur=0.2)

# 6 ------------------------------------------------ orange takeover: Meet
n6 = [ofield(), text("t_meet", "Meet", 640, 360, 160, WHITE, weight=700)]
tracks.append({"target": "t_meet", "at": 0.1, "reveal": {
    "unit": "word", "stagger": 0.06, "dur": 0.3, "rise": 42,
    "accent": WHITE}})
scene("s6", DEEP, 1.02, n6, kind="bloom", tdur=0.35)

# 7 -------------------------------------------- orange: Brew logo reveal
n7 = [
    ofield(),
    path("bw_m1", 480, 330, STEAM_TOP, WHITE, stroke=18),
    path("bw_m2", 480, 330, STEAM_BOT, WHITE, stroke=18),
    text("bw_word", "Brew", 720, 360, 130, WHITE, weight=700),
]
track("bw_m1", opacity=[(0.1, 0), (0.3, 1)],
      scale=[(0.1, 0.6), (0.55, 1.0, "outCubic")])
track("bw_m2", opacity=[(0.22, 0), (0.42, 1)],
      scale=[(0.22, 0.6), (0.65, 1.0, "outCubic")])
track("bw_word", at=0.35, opacity=[(0, 0), (0.25, 1)],
      y=[(0, 22), (0.4, 0, "outCubic")])
scene("s7", DEEP, 1.53, n7, kind="fade", tdur=0.3)

# 8 --------------------------- cream: Faster than ever before ("ever")
n8 = [text("t_faster", "Faster than ever before", 640, 360, 76, INK,
           weight=700)]
tracks.append({"target": "t_faster", "at": 0.15, "reveal": {
    "unit": "word", "stagger": 0.09, "dur": 0.3, "rise": 34,
    "accent": ORANGE, "color_delay": 0.18, "color_dur": 0.3,
    "keep": ["ever"]}})
scene("s8", CREAM, 2.04, n8, kind="dissolve", tdur=0.3)

# 9 ----------------- orange: prompt pill "Make a launch email for LiveFlow"
n9 = [
    ofield(),
    rect("p1_pill", 640, 350, 960, 130, 65, WHITE,
         glow={"sigma": 30, "opacity": 0.35, "color": "#ffffff"}),
    path("p1_sp1", 215, 342, SPARK, SUBMIT),
    path("p1_sp2", 248, 312, SPARK, SUBMIT),
    text("p1_ta", "Make a launch email for", 472, 350, 30, "#4a3b34",
         weight=500),
    text("p1_tb", "LiveFlow", 708, 350, 30, ORANGE, weight=500),
    rect("p1_sub", 1055, 350, 76, 76, 38, SUBMIT,
         states={"pressed": {"scale": 0.92, "fill": "#f0b13c"}}),
    path("p1_ar", 1055, 350, "M0 9L0 -9M-7 -2L0 -9L7 -2", WHITE, stroke=4.5),
    {"id": "p1_cur", "type": "cursor", "x": 1090, "y": 435, "w": 30,
     "fill": "#111111"},
]
cascade(["p1_pill", "p1_sp1", "p1_sp2", "p1_sub", "p1_ar"], at=0.05,
        step=0.03, rise=16)
track("p1_sp2", at=0.1, scale=[(0, 0.6)])
tracks.append({"target": "p1_ta", "at": 0.25, "reveal": {
    "unit": "type", "cadence": 0.045, "dur": 0.07}})
tracks.append({"target": "p1_tb", "at": 1.4, "reveal": {
    "unit": "type", "cadence": 0.055, "dur": 0.07, "caret": "bar",
    "caret_typing": "hidden"}})
track("p1_cur", at=1.75, x=[(0, 0), (0.4, -30, "outCubic")],
      y=[(0, 0), (0.4, -50, "outCubic")])
tracks.append({"target": "p1_sub", "at": 2.25, "state": "pressed"})
track("s9", cam_zoom=[(0, 1.0), (2.3, 1.0), (2.55, 1.15, "inCubic")])
scene("s9", DEEP, 2.55, n9, kind="fade", tdur=0.25)

# 10 ------------------- builder tablet proof (flat stand-in, camera pan)
n10 = [
    ofield(),
    rect("dv", 640, 370, 1040, 590, 26, WHITE,
         glow={"sigma": 44, "opacity": 0.35, "color": "#7a2f0e", "dy": 20}),
    rect("dv_rail", 176, 370, 56, 560, 18, "#f7f3ec"),
    rect("dv_logo", 176, 118, 30, 30, 9, ORANGE),
    rect("dv_ic1", 176, 170, 22, 22, 6, "#d9d2c7"),
    rect("dv_ic2", 176, 208, 22, 22, 6, "#d9d2c7"),
    rect("dv_ic3", 176, 246, 22, 22, 6, "#d9d2c7"),
    rect("dv_bub", 452, 140, 310, 48, 14, "#f6f1e9"),
    text("dv_bub_t", "Launch email for LiveFlow", 452, 140, 16, INK,
         weight=500),
    text("dv_ck1", "Finding examples", 358, 212, 17, "#5a4b42", weight=500),
    text("dv_ck2", "Generating images", 364, 260, 17, "#5a4b42", weight=500),
    text("dv_ck3", "Creating email", 348, 308, 17, "#5a4b42", weight=500),
]
for i, y in [(1, 212), (2, 260), (3, 308)]:
    n10.append(rect(f"dv_cc{i}", 590, y, 22, 22, 11, "#f5a95e"))
    n10.append(path(f"dv_cm{i}", 590, y, "M-5 0L-1 4L6 -4", WHITE, stroke=3))
n10 += [
    rect("dv_ch1", 365, 532, 172, 40, 12, "#f4efe7"),
    text("dv_ch1_t", "Include Upsale Offer", 365, 532, 13, "#6b5c52",
         weight=500),
    rect("dv_ch2", 565, 532, 200, 40, 12, "#f4efe7"),
    text("dv_ch2_t", "Add Link to Billing Page", 565, 532, 13, "#6b5c52",
         weight=500),
    rect("dv_inp", 452, 600, 370, 48, 16, "#faf6ef"),
    text("dv_inp_t", "Type your message...", 400, 600, 15, "#a3968a",
         weight=500),
    rect("dv_send", 610, 600, 32, 32, 16, SUBMIT),
    rect("pv", 890, 370, 420, 540, 18, "#fbfaf8"),
    text("pv_logo", "liveflow", 890, 132, 24, "#1b2a4a", weight=700),
    rect("pv_hero", 890, 252, 370, 180, 12, "#0b3987", gradient={
        "angle": 120, "stops": [{"at": 0, "color": "#0b3987"},
                                {"at": 1, "color": "#2ab6c9"}]}),
    text("pv_h1", "Meet the upgraded", 890, 224, 22, WHITE, weight=600),
    text("pv_h2", "Liveflow Lite", 890, 254, 22, WHITE, weight=700),
    rect("pv_btn", 890, 302, 122, 34, 17, "#3f68a8"),
    text("pv_btn_t", "Learn more", 890, 302, 13, WHITE, weight=500),
    text("pv_hl1", "Big news — Liveflow Lite", 890, 392, 20, "#1d1d1f",
         weight=700),
    text("pv_hl2", "just got better.", 890, 420, 20, "#1d1d1f", weight=700),
    rect("pv_b1", 890, 458, 340, 10, 5, "#e8e4dd"),
    rect("pv_b2", 890, 478, 300, 10, 5, "#e8e4dd"),
]
for i, y in [(1, 530), (2, 576)]:
    n10 += [
        rect(f"pv_r{i}", 890, y, 370, 38, 10, "#f4f2ee"),
        text(f"pv_r{i}_t", "Annual Budget 2025", 800, y, 13, "#3c342e",
             weight=500),
        rect(f"pv_r{i}_d", 885, y, 10, 10, 5, "#5cae62"),
        rect(f"pv_r{i}_a", 1010, y, 64, 26, 13, "#123c8c"),
        text(f"pv_r{i}_at", "Accept", 1010, y, 12, WHITE, weight=500),
    ]
track("dv", opacity=[(0, 0), (0.25, 1)],
      scale=[(0, 0.94), (0.55, 1.0, "outCubic")])
kids10 = [n["id"] for n in n10 if n["id"] not in ("of4", "dv")
          and not n["id"].startswith("dv_cm")]
cascade(kids10, at=0.28, step=0.025)
for i, a in [(1, 1.0), (2, 1.4), (3, 1.8)]:
    track(f"dv_cm{i}", opacity=[(0, 0), (a, 0), (a + 0.05, 1)])
track("s10", cam_zoom=[(0, 1.14), (3.2, 1.0, "outCubic")],
      cam_x=[(0, 55), (3.2, 0, "outCubic")],
      cam_y=[(0, -25), (3.2, 0, "outCubic")])
scene("s10", DEEP, 3.57, n10, kind="zoom", tdur=0.45)

# 11 -------------------------------------- cream: Always on brand
n11 = [
    text("t_always", "Always on brand", 640, 360, 92, INK, weight=700),
    path("aw_sp1", 350, 280, SPARK, ORANGE),
    path("aw_sp2", 940, 270, SPARK, ORANGE),
]
tracks.append({"target": "t_always", "at": 0.15, "reveal": {
    "unit": "word", "stagger": 0.09, "dur": 0.3, "rise": 34,
    "accent": ORANGE, "color_delay": 0.18, "color_dur": 0.3,
    "keep": ["on", "brand"]}})
for nid, a, sc in [("aw_sp1", 0.55, 0.8), ("aw_sp2", 0.7, 0.6)]:
    track(nid, at=a, opacity=[(0, 0), (0.12, 1)],
          scale=[(0, 0.2), (0.3, sc, "outCubic")])
scene("s11", CREAM, 1.53, n11, kind="dissolve", tdur=0.3)

# 12 --------------- white: prompt pill "Contacts in the United States"
n12 = [
    rect("p2_pill", 640, 350, 960, 130, 65, WHITE,
         glow={"sigma": 28, "opacity": 0.5, "color": "#f0a568"}),
    path("p2_sp1", 215, 342, SPARK, SUBMIT),
    text("p2_ta", "Contacts in the", 442, 350, 30, "#4a3b34", weight=500),
    text("p2_tb", "United States", 668, 350, 30, ORANGE, weight=500),
    rect("p2_sub", 1055, 350, 76, 76, 38, SUBMIT,
         states={"pressed": {"scale": 0.92, "fill": "#f0b13c"}}),
    path("p2_ar", 1055, 350, "M0 9L0 -9M-7 -2L0 -9L7 -2", WHITE, stroke=4.5),
    {"id": "p2_cur", "type": "cursor", "x": 1090, "y": 435, "w": 30,
     "fill": "#111111"},
]
cascade(["p2_pill", "p2_sp1", "p2_sub", "p2_ar"], at=0.05, step=0.03,
        rise=16)
tracks.append({"target": "p2_ta", "at": 0.2, "reveal": {
    "unit": "type", "cadence": 0.05, "dur": 0.07}})
tracks.append({"target": "p2_tb", "at": 1.0, "reveal": {
    "unit": "type", "cadence": 0.05, "dur": 0.07, "caret": "bar",
    "caret_typing": "hidden"}})
track("p2_cur", at=1.45, x=[(0, 0), (0.35, -30, "outCubic")],
      y=[(0, 0), (0.35, -50, "outCubic")])
tracks.append({"target": "p2_sub", "at": 1.8, "state": "pressed"})
track("s12", cam_zoom=[(0, 1.0), (1.85, 1.0), (2.04, 1.12, "inCubic")])
scene("s12", WHITE, 2.04, n12, kind="fade", tdur=0.25)

# 13 -------------------- contacts table proof (peach field, five rows)
ROWS = [
    ("james.park@design.co", "Subscribed", "San Diego, CA"),
    ("emma@startup.io", "Subscribed", "Boston, MA"),
    ("maya@agency.com", "Unsubscribed", "Seattle, WA"),
    ("david.kim@enterprise.com", "Subscribed", "Chicago, IL"),
    ("alex.r@techcorp.com", "Unsubscribed", "Los Angeles, CA"),
]
n13 = [
    rect("ct_hd", 640, 110, 1000, 70, 18, "#fffdf6"),
    text("ct_hd_t", "Contacts in the United States", 330, 110, 22, INK,
         weight=500),
    rect("ct_hd_b", 1100, 110, 40, 40, 20, SUBMIT),
    path("ct_hd_a", 1100, 110, "M0 6L0 -6M-5 -1L0 -6L5 -1", WHITE,
         stroke=3.5),
]
for i, (email, status, city) in enumerate(ROWS):
    y = 212 + i * 96
    sub = status == "Subscribed"
    chip_bg = "#e9f4e3" if sub else "#fbe7e0"
    chip_ink = "#55934f" if sub else "#cf6f52"
    cw = 128 if sub else 150
    n13 += [
        rect(f"ct_r{i}", 640, y, 1000, 82, 16, "#fffcf4"),
        text(f"ct_r{i}_e", email, 200 + len(email) * 5.5, y, 20, "#3c2f28",
             weight=500),
        rect(f"ct_r{i}_c", 620, y, cw, 34, 17, chip_bg),
        text(f"ct_r{i}_ct", status, 620, y, 15, chip_ink, weight=500),
        text(f"ct_r{i}_l", city, 840, y, 18, "#6b5c52", weight=500),
        text(f"ct_r{i}_a", "Active", 1040, y, 16, "#7fa3cf", weight=500),
    ]
cascade(["ct_hd", "ct_hd_t", "ct_hd_b", "ct_hd_a"], at=0.1, step=0.02)
for i in range(5):
    a = 0.35 + i * 0.13
    for suf in ("", "_e", "_c", "_ct", "_l", "_a"):
        track(f"ct_r{i}{suf}", at=a, opacity=[(0, 0), (0.22, 1)],
              y=[(0, 26), (0.35, 0, "outCubic")])
track("s13", cam_zoom=[(0, 1.06), (2.9, 1.0, "outCubic")],
      cam_y=[(0, 18), (2.9, 0, "outCubic")])
scene("s13", "#fdf0dd", 3.06, n13, kind="zoom", tdur=0.4)

# 14 ---------------------------------------- orange: Now it's your turn
n14 = [ofield(), text("t_turn", "Now it's your turn", 640, 360, 88, WHITE,
                      weight=700)]
tracks.append({"target": "t_turn", "at": 0.1, "reveal": {
    "unit": "word", "stagger": 0.08, "dur": 0.28, "rise": 34,
    "accent": WHITE}})
scene("s14", DEEP, 1.02, n14, kind="bloom", tdur=0.35)

# 15 --------------------------- white: What will you brew? ("you" big)
n15 = [
    text("wy_1", "What will", 385, 372, 80, "#2e2624", weight=600),
    text("wy_2", "you", 730, 360, 118, ORANGE, weight=800),
    text("wy_3", "brew?", 990, 372, 80, "#2e2624", weight=600),
]
tracks.append({"target": "wy_1", "at": 0.15, "reveal": {
    "unit": "word", "stagger": 0.08, "dur": 0.28, "rise": 30,
    "accent": "#2e2624"}})
tracks.append({"target": "wy_2", "at": 0.42, "reveal": {
    "unit": "word", "stagger": 0.08, "dur": 0.32, "rise": 46,
    "accent": ORANGE}})
tracks.append({"target": "wy_3", "at": 0.6, "reveal": {
    "unit": "word", "stagger": 0.08, "dur": 0.28, "rise": 30,
    "accent": "#2e2624"}})
scene("s15", WHITE, 2.04, n15, kind="cut", tdur=0.1)

# 16 ------------------------------- orange end lockup: Brew + brew.new
n16 = [
    ofield(),
    path("en_m1", 460, 330, STEAM_TOP, WHITE, stroke=20,
         keys={"scale": [{"t": 0, "v": 1.25}]}),
    path("en_m2", 460, 330, STEAM_BOT, WHITE, stroke=20,
         keys={"scale": [{"t": 0, "v": 1.25}]}),
    text("en_word", "Brew", 725, 340, 130, WHITE, weight=700),
    rect("en_pill", 640, 520, 240, 64, 32, "#f9bd92"),
    text("en_url", "brew.new", 640, 520, 26, WHITE, weight=600),
]
track("en_m1", opacity=[(0.12, 0), (0.3, 1)])
track("en_m2", opacity=[(0.28, 0), (0.46, 1)])
track("en_word", at=0.4, opacity=[(0, 0), (0.28, 1)],
      y=[(0, 20), (0.42, 0, "outCubic")])
track("en_pill", at=0.95, opacity=[(0, 0), (0.3, 0.85)])
track("en_url", at=1.0, opacity=[(0, 0), (0.3, 1)])
scene("s16", DEEP, 2.55, n16, kind="bloom", tdur=0.4)

stage = {"fps": 30, "size": [W, H], "scenes": scenes,
         "audio": {"src": "/assets/audio/pad.m4a", "gain": 0.6,
                   "fade_out": 0.8}}
with open("docs/lovable.stage.json", "w") as f:
    json.dump(stage, f, indent=1)
with open("docs/lovable.anim.json", "w") as f:
    json.dump({"tracks": tracks}, f, indent=1)
total = sum(s["dur"] for s in scenes)
print("wrote docs/lovable.{stage,anim}.json,",
      sum(len(s["nodes"]) for s in scenes), "nodes,", len(tracks),
      f"tracks, {total:.2f}s")
