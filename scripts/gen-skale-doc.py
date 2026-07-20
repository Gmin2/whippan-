#!/usr/bin/env python3
# reproduction of skale-main.mp4 (Aside AI browser, 87.6s @ 1280x720),
# compressed to a ~39s arc. dark problem act on the one kinetic-type
# engine (live-colored word cooling to ink), gradient-wall "Aside"
# reveal, white product act stitched by a dseq-grown connector thread
# the camera pans down (command bar -> plan -> chase -> subagents ->
# refund), black iris into the one saturated benchmark frame (#2fd6f6
# bar streaking in), then the dark/light value-prop montage and the
# aside.com end card. timings from the frame teardown, dwell kept.
import json
import os

W, H = 1280, 720
DARK = "#262626"
PILL = "#333333"
INK = "#1c1c1c"
GREY = "#8a8a8a"
CYAN = "#2fd6f6"
TYPEBLUE = "#4e92dd"
TEAL = "#356279"
STEEL = "#7a94a3"
THREAD = "#0e86c0"
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


def star4_d(r):
    # the compass 4-point star
    s = r * 0.24
    return (f"M0 {-r}L{s} {-s}L{r} 0L{s} {s}L0 {r}L{-s} {s}L{-r} 0"
            f"L{-s} {-s}Z")


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


def reveal(nid, at, **r):
    tracks.append({"target": nid, "at": at, "reveal": r})


def scene(id, bg, dur, nodes, kind="fade", tdur=0.3, **kw):
    tr = {"kind": kind, "dur": tdur}
    tr.update(kw)
    scenes.append({"id": id, "bg": bg, "dur": round(dur, 3),
                   "transition": tr, "nodes": nodes})


def born(nid, at, rise=12, dur=0.2):
    track(nid, at=at, opacity=[(0, 0), (dur * 0.7, 1)],
          y=[(0, rise), (dur, 0, "outCubic")])


# 1 ------------------------------------- dark search bar, "We killed"
n1 = [
    rect("sb", 640, 360, 1040, 300, 90, PILL,
         glow={"sigma": 60, "opacity": 0.0, "color": CYAN}),
    text("sb_ph", "Search for...", 420, 360, 44, "#6d6d6d"),
    text("wk", "We killed", 470, 360, 84, "#f2f2f2", weight=600),
    rect("decoy", 830, 360, 88, 88, 24, "#ffffff",
         gradient={"angle": 135, "stops": [
             {"at": 0, "color": "#5aa2e8"}, {"at": 0.55, "color": "#e8a24f"},
             {"at": 1, "color": "#e85a8f"}]}),
]
track("s1", cam_zoom=[(0, 0.85), (2.8, 1.32, "outCubic")])
track("sb", glow_opacity=[(0.7, 0), (1.2, 0.14)])
track("sb_ph", opacity=[(0, 0.9), (0.85, 0.9), (1.0, 0)])
track("wk", opacity=[(0, 0), (0.88, 0), (0.9, 1)])
reveal("wk", 0.9, unit="glyph", stagger=0.09, dur=0.12, rise=0,
       accent=TYPEBLUE, color_delay=0.12, color_dur=0.28)
track("decoy", opacity=[(2.0, 0), (2.1, 1)],
      scale=[(2.0, 0.4), (2.25, 1.0, "outCubic")])
scene("s1", DARK, 3.0, n1, kind="cut")

# 2 ---------------------------- "They promised us to do the work" + bin
n2 = [text("tp", "They promised us to do the work", 640, 300, 56,
           "#efefef", weight=600)]
# killed icons half-buried, then the bin over them
for i, (dx, fill, rot) in enumerate([(-34, "#e8a24f", -14),
                                     (2, "#5aa2e8", 8),
                                     (36, "#e85a8f", 20)]):
    n2.append(rect(f"bi{i}", 640 + dx, 508, 52, 52, 14, fill, rot=rot))
n2.append(rect("bin", 640, 552, 128, 104, 16, "#1a1a1a"))
n2.append(rect("bin_rim", 640, 500, 148, 14, 7, "#141414"))
reveal("tp", 0.2, unit="word", stagger=0.12, dur=0.26, rise=16,
       accent=TYPEBLUE, color_delay=0.16, color_dur=0.3)
for i in range(3):
    born(f"bi{i}", 0.1 + i * 0.1, rise=-20)
scene("s2", DARK, 2.6, n2)

# 3 -------------------------- refusal stack, sweep-off, "Introducing"
n3 = [text("ts_t", "Then, they stop when it gets real", 640, 180, 50,
           "#efefef", weight=600)]
reveal("ts_t", 0.15, unit="word", stagger=0.1, dur=0.24, rise=14,
       accent="#a48fe0", color_delay=0.16, color_dur=0.3)
REFUSALS = [("rf0", "I can't do that", 0.9),
            ("rf1", "Please approve action", 1.35),
            ("rf2", "I can't sign in to websites", 1.8)]
for i, (nid, label, b) in enumerate(REFUSALS):
    wv = len(label) * 26 * 0.5 + 56
    y = 300 + i * 74
    n3.append(rect(nid, 640, y, round(wv, 1), 54, 27, PILL))
    n3.append(text(nid + "_t", label, 640, y, 26, "#d9d9d9"))
    for c in (nid, nid + "_t"):
        track(c, opacity=[(b, 0), (b + 0.15, 1), (2.55, 1), (2.9, 0)],
              y=[(b, 16), (b + 0.22, 0, "outCubic"), (2.5, 0),
                 (2.9, -220, "inCubic")],
              x=[(2.5, 0), (2.9, 1300, "inCubic")],
              rot=[(2.5, 0), (2.9, 18 + i * 5, "inCubic")])
track("ts_t", at=2.5, opacity=[(0, 1), (0.35, 0)],
      x=[(0, 0), (0.4, 1300, "inCubic")])
n3.append(text("intro", "Introducing", 640, 380, 58, "#f2f2f2", weight=600))
track("intro", opacity=[(0, 0), (2.6, 0), (2.62, 1)])
reveal("intro", 2.62, unit="type", cadence=0.055, dur=0.08, caret="bar")
scene("s3", DARK, 3.4, n3)

# 4 ------------------------------------ gradient wall + "Aside" hero
n4 = [rect("wall", 640, 360, 1280, 720, 0, "#038fb2",
           gradient={"angle": 90, "stops": [
               {"at": 0, "color": "#99c3d1"}, {"at": 0.4, "color": "#0a84a8"},
               {"at": 1, "color": "#020b12"}]})]
for i in range(9):
    n4.append(rect(f"slat{i}", 96 + i * 136, 360, 3, 720, 0, "#ffffff"))
    track(f"slat{i}", opacity=[(0, 0.07)])
n4.append(text("aside_hero", "Aside", 640, 360, 150, "#d7e6ec", weight=600))
reveal("aside_hero", 0.3, unit="glyph", stagger=0.08, dur=0.55, rise=0,
       accent="#eef7fa", color_delay=0.2, color_dur=0.4)
track("s4", cam_zoom=[(0, 1.0), (2.2, 1.05, "inOutCubic")])
scene("s4", "#0b2a38", 2.2, n4, kind="push", dir="up", tdur=0.5)

# 5 ------------------- white flip: the claim + thread draws the frame
n5 = [
    path("mk5_c", 372, 300, circle_d(40), STEEL, stroke=7.0),
    path("mk5_s", 372, 300, star4_d(30), STEEL, rot=24),
    text("cl1", "A browser that gets", 712, 290, 52, "#93a5ad", weight=600),
    text("cl2", "complex work done", 660, 368, 52, "#93a5ad", weight=600),
    path("th5", 180, 600,
         "M0 0L0 -6L0 0Z", THREAD, stroke=3.0),
    rect("dot5", 180, 600, 10, 10, 5, THREAD,
         glow={"sigma": 8, "opacity": 0.6, "color": THREAD}),
]
n5[4]["dseq"] = [
    {"at": 0.5, "d": "M0 0L0 -6L0 0Z"},
    {"at": 1.7, "d": ("M0 0L0 -220C0 -244 12 -256 36 -256"
                      "L120 -256L36 -256C12 -256 0 -244 0 -220L0 0Z")},
    {"at": 2.3, "d": ("M0 0L0 -220C0 -244 12 -256 36 -256"
                      "L430 -256L36 -256C12 -256 0 -244 0 -220L0 0Z")},
]
for c in ("mk5_c", "mk5_s"):
    track(c, opacity=[(0.1, 0), (0.4, 1)])
reveal("cl1", 0.3, unit="word", stagger=0.14, dur=0.28, rise=14,
       accent="#5d8290", color_delay=0.18, color_dur=0.32)
reveal("cl2", 0.9, unit="word", stagger=0.14, dur=0.28, rise=14,
       accent="#6fb7c9", color_delay=0.18, color_dur=0.32, keep=["done"])
track("dot5", opacity=[(0.4, 0), (0.5, 1)],
      y=[(0.5, 0), (1.6, -252, "inOutCubic")],
      x=[(1.6, 0), (1.72, 120), (2.3, 420, "outCubic")])
scene("s5", "#ffffff", 2.6, n5, kind="dissolve", tdur=0.5)

# 6 --------------------------------- command bar, the task typed in
n6 = [
    path("wm_c", 640, 208, circle_d(46), "#e8e8e8", stroke=7.0),
    path("wm_s", 640, 208, star4_d(34), "#e6e6e6", rot=24),
    rect("bar", 640, 340, 1080, 78, 26, "#ffffff",
         glow={"sigma": 22, "opacity": 0.55, "color": "#c9ced1", "dy": 6}),
    text("task", "cancel all unused subscriptions and request refunds",
         448, 340, 25, "#3c3c3c"),
    rect("tab_c", 800, 340, 46, 30, 8, "#f0f0f0"),
    text("tab_t", "Tab", 800, 340, 15, "#7a7a7a"),
    text("tosw", "to switch", 872, 341, 15, "#9a9a9a"),
    text("srch", "Search", 952, 340, 19, "#9a9a9a"),
    rect("askp", 1058, 340, 104, 46, 23, "#ffffff",
         glow={"sigma": 10, "opacity": 0.6, "color": "#d5d9dc", "dy": 3}),
    text("askp_t", "Ask AI", 1058, 340, 19, "#161616", weight=600),
    text("tools_l", "+    Local    Guard", 250, 404, 18, "#a3a3a3"),
    text("tools_r", "GPT-5.5    High", 1040, 404, 18, "#a3a3a3"),
]
track("task", opacity=[(0, 0), (0.48, 0), (0.5, 1)])
reveal("task", 0.5, unit="type", cadence=0.04, dur=0.08, caret="bar",
       caret_blink=1.0)
track("s6", cam_zoom=[(0, 1.02), (2.9, 1.07, "inOutCubic")])
scene("s6", "#ffffff", 3.0, n6)

# 7 ------------- THE demo: one shot down the connector thread (pan)
n7 = []
# the thread spine: a stroked path grown by dseq, out-and-back so the
# resampler's implicit close is invisible


def spine(ln):
    return f"M0 0L0 {ln}L0 0Z"


th = path("th7", 150, 330, spine(8), "#c7dde6", stroke=3.0)
th["dseq"] = [
    {"at": 0.3, "d": spine(8)},
    {"at": 1.4, "d": spine(240)},
    {"at": 2.8, "d": spine(700)},
    {"at": 4.2, "d": spine(1050)},
    {"at": 5.6, "d": spine(1180)},
    {"at": 6.6, "d": spine(1330)},
]
n7.append(th)
# user bubble
n7.append(rect("ub", 880, 300, 580, 60, 30, "#f1f3f4"))
n7.append(text("ub_t", "Cancel unused subscriptions and request refunds",
               880, 300, 21, "#3c3c3c"))
born("ub", 0.15, rise=14)
track("ub_t", at=0.15, opacity=[(0, 0), (0.15, 1)],
      y=[(0, 14), (0.2, 0, "outCubic")])
# streamed plan line
n7.append(text("plan", "First, I'll check your credit card statement.",
               500, 400, 24, INK))
reveal("plan", 0.7, unit="word", stagger=0.09, dur=0.2, rise=10,
       accent=TEAL, color_delay=0.14, color_dur=0.26)
# step 1: searching browsing history
n7.append(path("st1_i", 218, 505, circle_d(15) + "M0 0L0 -9M0 0L6 4",
               INK, stroke=2.4))
n7.append(text("st1", "searching browsing history", 465, 505, 30, INK,
               weight=600))
track("st1_i", opacity=[(1.5, 0), (1.65, 1)])
reveal("st1", 1.5, unit="word", stagger=0.12, dur=0.22, rise=8,
       accent=TEAL, color_delay=0.2, color_dur=0.3, keep=["browsing"])
n7.append(rect("d1", 150, 505, 12, 12, 6, THREAD))
track("d1", opacity=[(1.5, 0), (1.6, 1)])
# result rows
n7.append(text("rr1", "MEMORY.md   User's bank and credit card is Chase.",
               485, 575, 18, GREY))
n7.append(text("rr2", "Jun's Chase   Passkey", 300, 618, 18, GREY))
born("rr1", 2.0, rise=8)
born("rr2", 2.15, rise=8)
# step 2: open chase.com
n7.append(path("st2_i", 218, 720,
               "M-16 -12L16 -12L16 12L-16 12L-16 -12M-16 -5L16 -5",
               INK, stroke=2.4))
n7.append(text("st2", "Open Chase.com", 360, 720, 30, INK, weight=600))
track("st2_i", opacity=[(2.5, 0), (2.65, 1)])
reveal("st2", 2.5, unit="word", stagger=0.12, dur=0.22, rise=8,
       accent=TEAL, color_delay=0.2, color_dur=0.3)
n7.append(rect("d2", 150, 720, 12, 12, 6, THREAD))
track("d2", opacity=[(2.5, 0), (2.6, 1)])
# chase page stand-in
n7.append(rect("ch_card", 430, 955, 540, 340, 16, "#ffffff",
               glow={"sigma": 26, "opacity": 0.5, "color": "#c8d4da",
                     "dy": 8}))
n7.append(text("ch_logo", "CHASE", 250, 812, 20, "#117aca", weight=700))
n7.append(text("ch_nav", "Checking    Savings    Credit cards", 520, 812,
               14, "#9fb4c4"))
n7.append(rect("ch_hero", 430, 990, 540, 240, 8, "#dfeaf3",
               gradient={"angle": 120, "stops": [
                   {"at": 0, "color": "#dbe8f3"},
                   {"at": 1, "color": "#f4f8fb"}]}))
n7.append(text("ch_400", "Enjoy $400", 350, 925, 40, "#8fb3cd", weight=700))
n7.append(text("ch_sub", "New Chase checking customers", 388, 968, 16,
               "#a8bfd0"))
n7.append(rect("ch_f1", 340, 1020, 280, 34, 8, "#ffffff"))
n7.append(rect("ch_f2", 340, 1062, 280, 34, 8, "#ffffff"))
n7.append(rect("ch_btn", 340, 1104, 280, 34, 17, "#117aca"))
n7.append(text("ch_btn_t", "Sign in", 340, 1104, 15, "#ffffff", weight=600))
for i, nid in enumerate(["ch_card", "ch_logo", "ch_nav", "ch_hero",
                         "ch_400", "ch_sub", "ch_f1", "ch_f2", "ch_btn",
                         "ch_btn_t"]):
    track(nid, at=2.9 + i * 0.05, opacity=[(0, 0), (0.25, 1)])
# step 3: sign in with passkey
n7.append(path("st3_i", 218, 1195, circle_d(9, -6, 0) + "M3 0L20 0M14 -6L14 0",
               INK, stroke=2.4))
n7.append(text("st3", "Sign in with Jun's Chase Passkey", 505, 1195, 28,
               INK, weight=600))
track("st3_i", opacity=[(4.1, 0), (4.25, 1)])
reveal("st3", 4.1, unit="word", stagger=0.1, dur=0.2, rise=8,
       accent=TEAL, color_delay=0.18, color_dur=0.28)
n7.append(rect("d3", 150, 1195, 12, 12, 6, THREAD))
track("d3", opacity=[(4.1, 0), (4.2, 1)])
# step 4: spawning subagents
n7.append(text("st4", "Spawning subagents in parallel", 470, 1280, 28,
               INK, weight=600))
reveal("st4", 4.7, unit="word", stagger=0.1, dur=0.2, rise=8,
       accent=TEAL, color_delay=0.18, color_dur=0.28)
n7.append(rect("d4", 150, 1280, 12, 12, 6, THREAD))
track("d4", opacity=[(4.7, 0), (4.8, 1)])
# three brand subagent lanes
GHOST = ("M-13 9C-13 -8 13 -8 13 9L13 9L8 5L4 9L0 5L-4 9L-8 5L-13 9Z")
SUBS = [("li", "#0a66c2", "in", "#ffffff", "Checking LinkedIn usage", 5.1),
        ("nf", "#141414", "N", "#e50914", "Checking Netflix usage", 5.3),
        ("am", "#232f3e", "a", "#ff9900", "Checking Amazon Prime usage", 5.5)]
for i, (pid, fill, ch, chc, label, b) in enumerate(SUBS):
    y = 1370 + i * 78
    n7.append(path(f"{pid}_g", 220, y, GHOST, "#c9cdd0"))
    n7.append(text(f"{pid}_s", "Spawned subagent", 340, y, 20, "#b9bfc4"))
    n7.append(rect(f"{pid}_b", 478, y, 42, 42, 10, fill))
    n7.append(text(f"{pid}_bt", ch, 478, y, 21, chc, weight=700))
    n7.append(text(f"{pid}_l", label, 520 + len(label) * 5.7, y, 22, INK,
                   weight=600))
    for nid in (f"{pid}_g", f"{pid}_s", f"{pid}_b", f"{pid}_bt", f"{pid}_l"):
        track(nid, at=b, opacity=[(0, 0), (0.18, 1)],
              y=[(0, 12), (0.24, 0, "outCubic")])
# the payoff
n7.append(text("payoff", "Your $120 refund will be processed this week!",
               520, 1660, 28, INK, weight=600))
reveal("payoff", 6.3, unit="word", stagger=0.1, dur=0.22, rise=10,
       accent=TEAL, color_delay=0.2, color_dur=0.3, keep=["$120"])
n7.append(rect("d5", 150, 1660, 12, 12, 6, THREAD))
track("d5", opacity=[(6.3, 0), (6.4, 1)])
# black iris out, centered on the final camera view
n7.append(path("iris", 640, 1670, circle_d(30), DARK))
track("iris", opacity=[(0, 0), (7.25, 0), (7.28, 1)],
      scale=[(7.28, 0.1), (7.8, 32, "inCubic")])
# the continuous pan
track("s7", cam_y=[(0, 0), (1.4, 30), (2.8, 420, "inOutCubic"),
                   (4.2, 760, "inOutCubic"), (5.6, 1080, "inOutCubic"),
                   (7.0, 1290, "inOutCubic"), (7.8, 1310)])
scene("s7", "#ffffff", 7.8, n7)

# 8 ---------------------- the benchmark: all the saturation, one frame
n8 = [
    text("bm_t", "Browsing Agent Benchmark", 288, 150, 23, "#f0f0f0",
         weight=600),
    text("bm_s", "Online-Mind2Web - 300 tasks - Including impossible tasks",
         416, 188, 19, "#9aa0a6"),
]
track("bm_t", opacity=[(0, 0), (0.78, 0), (0.8, 1)])
reveal("bm_t", 0.8, unit="type", cadence=0.03, dur=0.06, caret="none")
track("bm_s", opacity=[(0, 0), (1.18, 0), (1.2, 1)])
reveal("bm_s", 1.2, unit="type", cadence=0.018, dur=0.05, caret="none")
ROWS = [("Aside GPT 5.5", 880, "99%", 250),
        ("Browser use", 805, "97%", 324),
        ("GPT 5.4 | Computer use", 680, "92%", 398),
        ("Claude Opus 4.7", 495, "86%", 472),
        ("ChatGPT Atlas", 210, "70%", 546)]
for i, (label, wv, val, y) in enumerate(ROWS):
    cx = 150 + wv / 2
    if i == 0:
        n8.append(rect("bb0", cx, y, wv, 52, 12, CYAN,
                       glow={"sigma": 16, "opacity": 0.55, "color": CYAN},
                       streak={"samples": 5, "window": 0.06, "gain": 0.6}))
        n8.append(text("bl0", label, 240, y, 21, "#0d3a46", weight=600))
        n8.append(text("bv0", val, 1095, y, 26, CYAN, weight=600))
        track("bb0", opacity=[(0.05, 0), (0.12, 1)],
              x=[(0.1, -1350), (0.62, 0, "outCubic")])
        tracks.append({"target": "bb0", "loop": True, "at": 1.5, "keys": {
            "glow_opacity": [{"t": 0, "v": 0.85},
                             {"t": 0.8, "v": 1.0, "ease": "inOutCubic"},
                             {"t": 1.6, "v": 0.85, "ease": "inOutCubic"}]}})
        track("bl0", opacity=[(0.55, 0), (0.7, 1)])
        track("bv0", opacity=[(0.66, 0), (0.68, 1)])
    else:
        n8.append(rect(f"bb{i}", cx, y, wv, 52, 12,
                       "#3a3a3a" if i % 2 else "#383838"))
        n8.append(text(f"bl{i}", label, 175 + len(label) * 5.5, y, 21,
                       "#cfcfcf", weight=600))
        n8.append(text(f"bv{i}", val, 1095, y, 24, "#e4e4e4", weight=600))
        b = 1.0 + i * 0.16
        for nid, dl in ((f"bb{i}", 0.0), (f"bl{i}", 0.06)):
            track(nid, at=b + dl, opacity=[(0, 0), (0.22, 1)],
                  x=[(0, -36), (0.3, 0, "outCubic")])
        track(f"bv{i}", opacity=[(b + 0.28, 0), (b + 0.3, 1)])
scene("s8", DARK, 4.4, n8, kind="cut")

# 9 ------------------------------------------ dark value-prop montage
n9 = [
    text("m1", "Anything you can do in a browser", 640, 330, 46,
         "#f0f0f0", weight=600),
    path("mk9_c", 408, 340, circle_d(30), STEEL, stroke=5.5),
    path("mk9_s", 408, 340, star4_d(22), STEEL, rot=24),
    text("m2", "Aside can do it for you", 700, 340, 52, "#f0f0f0",
         weight=600),
    text("m3", "sign in  ·  payments  ·  documents  ·  presentations",
         640, 434, 20, "#7a7a7a"),
]
reveal("m1", 0.15, unit="word", stagger=0.1, dur=0.24, rise=12,
       accent=CYAN, color_delay=0.16, color_dur=0.3)
track("m1", at=1.3, opacity=[(0, 1), (0.2, 0)])
for c in ("mk9_c", "mk9_s"):
    track(c, opacity=[(1.5, 0), (1.7, 1)])
track("m2", opacity=[(0, 0), (1.53, 0), (1.55, 1)])
reveal("m2", 1.55, unit="word", stagger=0.1, dur=0.24, rise=12,
       accent=CYAN, color_delay=0.16, color_dur=0.3, keep=["Aside"])
track("m3", opacity=[(2.35, 0), (2.6, 0.85)])
scene("s9", DARK, 3.0, n9, tdur=0.4)

# 10 ----------------------------------- white flip: private, on-device
n10 = [
    path("lock_b", 362, 268, "M-11 -2L11 -2L11 14L-11 14Z", TEAL),
    path("lock_s", 362, 258, "M-7 8C-7 -8 7 -8 7 8", TEAL, stroke=3.0),
    text("p1", "everything is private", 660, 262, 46, INK, weight=600),
    text("p2", "Data never leaves your device", 640, 348, 28, "#6a6a6a"),
    text("p3a", "Everything runs locally,", 570, 428, 28, INK),
    text("p3b", "encrypted", 812, 428, 28, TEAL, weight=600),
]
for c in ("lock_b", "lock_s"):
    track(c, opacity=[(0.3, 0), (0.5, 1)])
reveal("p1", 0.1, unit="word", stagger=0.12, dur=0.24, rise=12,
       accent=TEAL, color_delay=0.18, color_dur=0.3, keep=["private"])
reveal("p2", 0.9, unit="word", stagger=0.1, dur=0.22, rise=10,
       accent=TEAL, color_delay=0.16, color_dur=0.28)
track("p2", opacity=[(0, 0), (0.88, 0), (0.9, 1)])
reveal("p3a", 1.5, unit="word", stagger=0.1, dur=0.22, rise=10,
       accent=TEAL, color_delay=0.16, color_dur=0.28)
track("p3a", opacity=[(0, 0), (1.48, 0), (1.5, 1)])
track("p3b", opacity=[(0, 0), (1.88, 0), (1.9, 1)])
reveal("p3b", 1.9, unit="scramble", cadence=0.05, churn=4)
scene("s10", "#ffffff", 2.8, n10, kind="cut")

# 11 ------------------------------- dark flip: bring your own model
n11 = [text("byo", "Bring your own subscription", 640, 300, 44,
            "#f0f0f0", weight=600)]
reveal("byo", 0.1, unit="word", stagger=0.11, dur=0.24, rise=12,
       accent=CYAN, color_delay=0.16, color_dur=0.3)
GEM = ("M0 -16C4 -6 6 -4 16 0C6 4 4 6 0 16C-4 6 -6 4 -16 0"
       "C-6 -4 -4 -6 0 -16Z")
SPARK = ("M0 -15L4 -4L15 0L4 4L0 15L-4 4L-15 0L-4 -4Z")
PROVIDERS = [
    ("pv0", "#333333", [path("pv0_c", 0, 0, circle_d(16), STEEL, stroke=3.5),
                        path("pv0_s", 0, 0, star4_d(12), STEEL, rot=24)]),
    ("pv1", "#ffffff", [path("pv1_g", 0, 0, GEM, "#5093fe")]),
    ("pv2", "#333333", [path("pv2_k", 0, 0, SPARK, "#d97757")]),
    ("pv3", "#333333", [path("pv3_o", 0, 0, circle_d(14), "#10a37f",
                             stroke=3.5)]),
    ("pv4", "#333333", [path("pv4_l", 0, 0,
                             "M0 14C-14 6 -12 -10 0 -14C12 -10 14 6 0 14Z",
                             "#8a9a8a")]),
]
for i, (pid, fill, inner) in enumerate(PROVIDERS):
    x = 448 + i * 96
    tile = rect(pid, x, 432, 62, 62, 15, fill)
    n11.append(tile)
    members = [pid]
    for nd in inner:
        nd["x"], nd["y"] = x, 432
        n11.append(nd)
        members.append(nd["id"])
    b = 0.75 + i * 0.12
    for nid in members:
        track(nid, at=b, opacity=[(0, 0), (0.2, 1)],
              y=[(0, 18), (0.28, 0, "outCubic")])
scene("s11", DARK, 2.2, n11, kind="cut")

# 12 ----------------------------------------------- aside.com end card
n12 = [text("url", "aside.com", 640, 360, 66, "#f4f4f4", weight=500)]
track("url", opacity=[(0, 0), (0.38, 0), (0.4, 1)])
reveal("url", 0.4, unit="scramble", cadence=0.06, churn=4)
scene("s12", DARK, 2.4, n12, tdur=0.4)

stage = {"fps": 30, "size": [W, H], "scenes": scenes,
         "audio": {"src": "/assets/audio/pad.m4a", "gain": 0.6,
                   "fade_out": 0.8}}
with open("docs/skale.stage.json", "w") as f:
    json.dump(stage, f, indent=1)
with open("docs/skale.anim.json", "w") as f:
    json.dump({"tracks": tracks}, f, indent=1)
total = sum(s["dur"] for s in scenes)
print("wrote docs/skale.{stage,anim}.json,",
      sum(len(s["nodes"]) for s in scenes), "nodes,", len(tracks),
      f"tracks, {total:.2f}s")
