#!/usr/bin/env python3
# reproduction of rezonant.mp4 (40.1s, 1138x640): the voice-to-work promo.
# one dictated sentence carried across color-chapter scenes: mint intro
# with rotating capability chips, the backspacing @mention gag, a website
# and a mountain hero (drawn stand-ins for the two real screens), code
# chips melting into an amber plan blob (goo), the collaboration beats,
# the scattered-letter build, the chip stack, the lotus end card. cuts on
# the ~112bpm onset grid per the ledger.
import json
import math
import os

W, H = 1138, 640
INK = "#1b1b1b"
MINT = "#e8f7f4"
TEAL = "#2fb99f"
AMBER = "#efb549"
VERM = "#df5c2e"
GREEN = "#3ca968"
K = 0.5523

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


def circle_d(r, cx=0, cy=0):
    k = r * K
    return (f"M{cx-r} {cy}C{cx-r} {cy-k} {cx-k} {cy-r} {cx} {cy-r}"
            f"C{cx+k} {cy-r} {cx+r} {cy-k} {cx+r} {cy}"
            f"C{cx+r} {cy+k} {cx+k} {cy+r} {cx} {cy+r}"
            f"C{cx-k} {cy+r} {cx-r} {cy+k} {cx-r} {cy}Z")


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


def fade_out(nid, at, dur=0.2):
    track(nid, at=at, opacity=[(0, 1), (dur, 0)])


def scene(id, bg, dur, nodes, kind="fade", tdur=0.25):
    scenes.append({"id": id, "bg": bg, "dur": round(dur, 3),
                   "transition": {"kind": kind, "dur": tdur}, "nodes": nodes})


def chip(id, label, x, y, fill, ink="#ffffff", w=None, size=26):
    wv = w or (len(label) * size * 0.55 + 44)
    return [rect(id, x, y, round(wv, 1), size * 1.9, size * 0.95, fill),
            text(id + "_t", label, x, y + 1, size, ink, weight=600)]


def waveform(prefix, cx, cy, n=9, color="#ffffff"):
    out = []
    for i in range(n):
        b = rect(f"{prefix}{i}", cx + (i - n // 2) * 16, cy, 7, 18, 3.5, color)
        out.append(b)
        tracks.append({"target": f"{prefix}{i}", "loop": True, "keys": {"h": [
            {"t": 0, "v": 12 + (i * 7) % 20},
            {"t": 0.3, "v": 34 - (i * 5) % 18, "ease": "inOutCubic"},
            {"t": 0.6, "v": 12 + (i * 7) % 20, "ease": "inOutCubic"}]}})
    return out


# 1 ------------------------------------------------------------ mint intro
n1 = [
    text("q1", "What if you could", 380, 250, 46),
    text("q2", "as fast as you talk?", 430, 330, 46),
]
for wa, word in [(0.3, "q1"), (0.5, "q2")]:
    tracks.append({"target": word, "at": wa, "reveal": {
        "unit": "word", "stagger": 0.07, "dur": 0.3, "rise": 26,
        "accent": GREEN, "color_delay": 0.25, "color_dur": 0.35,
        "keep": ["could", "talk?"]}})
for i, (label, fill, at) in enumerate([("spec", AMBER, 1.1),
                                       ("PRD", GREEN, 2.4),
                                       ("a plan", VERM, 3.7)]):
    cs = chip(f"cc{i}", label, 745, 248, fill)
    n1 += cs
    for c in cs:
        end = at + 1.25 if i < 2 else 4.9
        track(c["id"], at=at, opacity=[(-0.05, 0), (0.05, 1), (end - at, 1),
                                       (end - at + 0.1, 0)],
              y=[(-0.05, 14), (0.15, 0, "outCubic")])
scene("s1", MINT, 5.2, n1)

# 2 ---------------------------------------------------------- teal chapter
n2 = [text("wr", "With Rezonant", 569, 270, 58, "#ffffff", weight=700),
      text("sim", "simply", 569, 360, 34, "#dff5ef")]
tracks.append({"target": "wr", "reveal": {
    "unit": "word", "stagger": 0.09, "dur": 0.3, "rise": 30,
    "accent": "#ffffff"}})
track("sim", at=0.9, opacity=[(0, 0), (0.2, 1)])
n2 += waveform("wv1_", 569, 440)
scene("s2", TEAL, 1.87, n2)

# 3 ------------------------------------------- the backspacing @mention gag
n3 = [
    text("sm1", "simply", 400, 300, 44),
    text("sm2", "@mention", 610, 300, 44, "#d97740", weight=600),
    text("sm3", "type", 585, 300, 44, "#d97740", weight=600),
]
tracks.append({"target": "sm2", "at": 0.15, "reveal": {
    "unit": "type", "cadence": 0.055, "dur": 0.06, "caret": "bar",
    "untype_at": 1.0}})
track("sm3", at=0, opacity=[(0, 0)])
tracks.append({"target": "sm3", "at": 1.62, "reveal": {
    "unit": "type", "cadence": 0.07, "dur": 0.06, "caret": "bar"}})
track("sm3", at=1.6, opacity=[(0, 0), (0.02, 1)])
scene("s3", "#f5e8df", 2.1, n3)

# 4 ----------------------------------------------- drawn website stand-in
n4 = [
    rect("wb_bar", 569, 90, 980, 60, 14, "#f2f2f2"),
    rect("wb_dot", 130, 90, 26, 26, 13, VERM),
    text("wb_menu", "products    docs    pricing    login", 800, 90, 18,
         "#8a8a8a"),
    text("wb_hero", "PLATFORM", 569, 240, 64, "#111111", weight=800),
    rect("wb_b1", 420, 380, 300, 130, 16, "#ececec"),
    rect("wb_b2", 740, 380, 300, 130, 16, "#e2e2e2"),
    rect("wb_cta", 569, 520, 200, 54, 27, "#111111"),
]
n4 += chip("tt1", "over your product", 700, 300, VERM, size=22)
for c in ["tt1", "tt1_t"]:
    track(c, at=0.25, opacity=[(0, 0), (0.15, 1)],
          y=[(0, 12), (0.2, 0, "outCubic")])
scene("s4", "#ffffff", 1.2, n4, kind="cut")

# 5 --------------------------------------------- drawn mountain hero card
n5 = [
    rect("mt_sky", 569, 320, 1138, 640, 0, "#9ab8d8",
         gradient={"angle": 90, "stops": [{"at": 0, "color": "#8fb0d4"},
                                          {"at": 1, "color": "#eef2f7"}]}),
    path("mt_sun", 890, 150, circle_d(48), "#f6e3b0"),
    path("mt_m1", 400, 470, "M-320 170L0 -220L320 170Z", "#5c7a9e"),
    path("mt_m2", 800, 500, "M-300 140L0 -170L300 140Z", "#728fb3"),
    text("mt_h", "Work better, together", 569, 250, 54, "#ffffff", weight=700),
]
tracks.append({"target": "mt_h", "at": 0.3, "reveal": {
    "unit": "word", "stagger": 0.08, "dur": 0.3, "rise": 26,
    "accent": "#ffffff"}})
n5 += chip("tt2", "let's improve the signup flow", 660, 420, "#ffffff",
           ink=INK, size=22)
for c in ["tt2", "tt2_t"]:
    track(c, at=1.1, opacity=[(0, 0), (0.18, 1)],
          y=[(0, 14), (0.25, 0, "outCubic")])
scene("s5", "#8fb0d4", 3.1, n5, kind="cut")

# 6 -------------------------------------------- thinking -> code scatter
n6 = [text("th1", "and your thinking", 480, 240, 44),
      text("th2", "turns into", 500, 240, 44)]
tracks.append({"target": "th1", "reveal": {
    "unit": "word", "stagger": 0.08, "dur": 0.28, "rise": 22,
    "accent": "#d97740", "keep": ["thinking"]}})
track("th1", at=1.5, opacity=[(0, 1), (0.25, 0)])
track("th2", at=0, opacity=[(0, 0)])
tracks.append({"target": "th2", "at": 1.7, "reveal": {
    "unit": "word", "stagger": 0.08, "dur": 0.28, "rise": 22,
    "accent": "#d97740"}})
track("th2", at=1.68, opacity=[(0, 0), (0.02, 1)])
CODES = [("fn()", "#39a79c"), ("<div>", VERM), ("api", AMBER),
         ("db", GREEN), ("{ }", "#6c5ce7")]
for i, (label, fill) in enumerate(CODES):
    a = i * 2 * math.pi / 5 - math.pi / 2
    cx, cy = 569 + 190 * math.cos(a), 400 + 95 * math.sin(a)
    cs = chip(f"cd{i}", label, round(cx, 1), round(cy, 1), fill, size=20)
    n6 += cs
    for c in cs:
        track(c["id"], at=0.5 + i * 0.12,
              opacity=[(0, 0), (0.15, 1)],
              y=[(0, 60), (0.35, 0, "outCubic")],
              x=[(1.6, 0), (2.3, round((569 - cx) * 0.75, 1), "inOutCubic")])
scene("s6", "#fbf5e7", 2.8, n6, kind="cut")

# 7 -------------------------------------------------- the amber plan blob
n7 = [
    path("bl_main", 500, 300, circle_d(120), AMBER, goo="plan"),
    path("bl_s1", 640, 260, circle_d(52), AMBER, goo="plan"),
    path("bl_s2", 620, 380, circle_d(40), AMBER, goo="plan"),
    path("bl_s3", 400, 380, circle_d(34), AMBER, goo="plan"),
    text("bl_t", "a plan", 520, 300, 48, "#ffffff", weight=700),
    rect("prd", 569, 330, 560, 300, 22, "#ffffff"),
    text("prd_t", "PRD: Signup Redesign", 569, 240, 32, INK, weight=700),
    rect("prd_l1", 569, 310, 420, 14, 7, "#e6e6e6"),
    rect("prd_l2", 569, 350, 460, 14, 7, "#ececec"),
    rect("prd_l3", 569, 390, 380, 14, 7, "#e6e6e6"),
]
for nid, d in [("bl_main", 0.0), ("bl_s1", 0.15), ("bl_s2", 0.3),
               ("bl_s3", 0.45)]:
    track(nid, at=d, scale=[(0, 0.2), (0.6, 1.0, "outCubic")],
          opacity=[(0, 0), (0.1, 1), (1.7 - d, 1), (2.0 - d, 0)])
track("bl_t", opacity=[(0.4, 0), (0.6, 1), (1.7, 1), (1.95, 0)])
for nid in ["prd", "prd_t", "prd_l1", "prd_l2", "prd_l3"]:
    track(nid, at=1.9, opacity=[(0, 0), (0.25, 1)],
          y=[(0, 40), (0.4, 0, "outCubic")])
scene("s7", "#fbf5e7", 3.2, n7)

# 8 ------------------------------------------------------- let others in
n8 = [text("lo1", "let others", 430, 260, 46),
      text("lo2", "into the conversation", 540, 260, 46)]
n8 += chip("jk", "Jack", 640, 258, "#ffffff", ink=VERM, size=26)
n8[-2]["radius"] = 30
tracks.append({"target": "lo1", "reveal": {
    "unit": "word", "stagger": 0.08, "dur": 0.28, "rise": 22, "accent": GREEN}})
for c in ["jk", "jk_t"]:
    track(c, at=0.6, opacity=[(0, 0), (0.15, 1), (1.4, 1), (1.6, 0)],
          y=[(0, 12), (0.2, 0, "outCubic")])
track("lo1", at=1.5, opacity=[(0, 1), (0.25, 0)])
track("lo2", at=0, opacity=[(0, 0)])
tracks.append({"target": "lo2", "at": 1.75, "reveal": {
    "unit": "word", "stagger": 0.08, "dur": 0.28, "rise": 22, "accent": GREEN,
    "keep": ["conversation"]}})
track("lo2", at=1.73, opacity=[(0, 0), (0.02, 1)])
n8 += chip("cj", "Check @Jira", 569, 380, GREEN, size=22)
for c in ["cj", "cj_t"]:
    track(c, at=2.3, opacity=[(0, 0), (0.2, 1)],
          y=[(0, 14), (0.25, 0, "outCubic")])
n8 += waveform("wv2_", 569, 480, color="#9fd9cb")
scene("s8", MINT, 3.8, n8)

# 9 ------------------------------------------- alongside your tools (goo)
n9 = [text("at_l", "alongside your tools", 569, 170, 44)]
tracks.append({"target": "at_l", "reveal": {
    "unit": "word", "stagger": 0.08, "dur": 0.28, "rise": 22,
    "accent": "#d97740", "keep": ["tools"]}})
n9.append(path("tg_core", 569, 380, circle_d(95), AMBER, goo="tools"))
TOOLS = [("Figma", "#a259ff"), ("Lovable", VERM), ("Jira", "#2684ff"),
         ("Linear", "#5e6ad2")]
for i, (label, fill) in enumerate(TOOLS):
    a = i * 2 * math.pi / 4 + math.pi / 4
    ox, oy = 230 * math.cos(a), 120 * math.sin(a)
    n9.append(path(f"tg_{i}", round(569 + ox, 1), round(380 + oy, 1),
                   circle_d(42), AMBER, goo="tools"))
    n9.append(text(f"tg_{i}t", label, round(569 + ox, 1),
                   round(380 + oy - 62, 1), 20, INK, weight=600))
    track(f"tg_{i}", at=0.8 + i * 0.25,
          opacity=[(0, 0), (0.15, 1)],
          x=[(0, ox * 0.5), (2.2, 0, "inOutCubic")],
          y=[(0, oy * 0.5), (2.2, 0, "inOutCubic")])
    track(f"tg_{i}t", at=0.8 + i * 0.25,
          opacity=[(0, 0), (0.15, 1), (2.0, 1), (2.3, 0)])
track("tg_core", opacity=[(0.4, 0), (0.7, 1)])
n9 += chip("sca", "Send to coding agent", 569, 560, "#1b1b1b", size=22)
for c in ["sca", "sca_t"]:
    track(c, at=4.6, opacity=[(0, 0), (0.25, 1)],
          y=[(0, 16), (0.3, 0, "outCubic")])
scene("s9", MINT, 6.7, n9)

# 10 ------------------------------------------------------- building hold
n10 = [text("bld", "Building...", 569, 320, 44)]
tracks.append({"target": "bld", "reveal": {
    "unit": "type", "cadence": 0.08, "dur": 0.06, "caret": "bar"}})
scene("s10", MINT, 1.2, n10)

# 11 -------------------------------------------- scattered-letter build
n11 = [text("fm", "From messy inspiration", 569, 300, 52, weight=600)]
tracks.append({"target": "fm", "at": 0.2, "reveal": {
    "unit": "glyph", "stagger": 0.045, "dur": 0.5, "rise": 150,
    "accent": GREEN, "color_delay": 0.4, "color_dur": 0.4,
    "keep": ["inspiration"]}})
scene("s11", "#ffffff", 3.8, n11, kind="cut")

# 12 -------------------------------------------------- the shipped stack
n12 = [text("ts", "to shaped shippable work", 569, 220, 52, weight=600)]
tracks.append({"target": "ts", "reveal": {
    "unit": "word", "stagger": 0.09, "dur": 0.3, "rise": 26, "accent": VERM,
    "keep": ["shippable"]}})
for i, (label, fill) in enumerate([("Tasks", VERM), ("Code", "#39a79c"),
                                   ("PRD", AMBER)]):
    cs = chip(f"st{i}", label, 569, 340 + i * 66, fill, size=24)
    n12 += cs
    for c in cs:
        track(c["id"], at=0.8 + i * 0.2, opacity=[(0, 0), (0.2, 1)],
              y=[(0, 26), (0.3, 0, "outCubic")])
scene("s12", "#ffffff", 2.1, n12)

# 13 ------------------------------------------------------- teal end card
petals = ""
for i in range(5):
    a = -math.pi / 2 + (i - 2) * 0.55
    cxp, cyp = 46 * math.cos(a), 46 * math.sin(a) + 8
    petals += circle_d(22, cxp, cyp)
n13 = [
    path("lotus", 569, 250, petals, "#ffffff"),
    text("rz", "Rezonant", 569, 380, 56, "#ffffff", weight=700),
]
track("lotus", scale=[(0.2, 0.2), (0.8, 1.0, "spring")],
      opacity=[(0.1, 0), (0.4, 1)])
tracks.append({"target": "rz", "at": 0.7, "reveal": {
    "unit": "word", "stagger": 0.1, "dur": 0.35, "rise": 24,
    "accent": "#ffffff"}})
scene("s13", TEAL, 3.0, n13)

stage = {"fps": 30, "size": [W, H], "scenes": scenes,
         "audio": {"src": "/assets/audio/pad.m4a", "gain": 0.6,
                   "fade_out": 0.8}}
with open("docs/rezonant.stage.json", "w") as f:
    json.dump(stage, f, indent=1)
with open("docs/rezonant.anim.json", "w") as f:
    json.dump({"tracks": tracks}, f, indent=1)
total = sum(s["dur"] for s in scenes)
print("wrote docs/rezonant.{stage,anim}.json,",
      sum(len(s["nodes"]) for s in scenes), "nodes,", len(tracks),
      f"tracks, {total:.2f}s")
