#!/usr/bin/env python3
# reproduction of animations/ai-1.mp4 (datalyr, 66s) compressed to a ~35s
# arc. keeps the video's grammar per analysis/ai-1/ai-1.md: the orange->black
# word ritual on every line, blob-birth ui (blurred orange blobs condensing
# into white cards), metaball couplings (goo groups) for the stripe/shopify
# pills, the physics chip stack and the train-car chips, and a camera that
# never stops (drift keys on every scene). all screens are drawn stand-ins.
import json
import math
import os

W, H = 1920, 1080
INK = "#161616"
ORANGE = "#e8671f"
DEEP = "#ee5e05"
MID = "#ea752f"
CREAM = "#fcfcfc"
PEACH = "#fceae0"
END_BG = "#f2f1ed"
DARK = "#0f0802"
STRIPE = "#635bff"
SHOPIFY = "#7ab648"
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
    return (f"M{cx-r} {cy}C{cx-r} {cy-k} {cx-k} {cy-r} {cx} {cy-r}"
            f"C{cx+k} {cy-r} {cx+r} {cy-k} {cx+r} {cy}"
            f"C{cx+r} {cy+k} {cx+k} {cy+r} {cx} {cy+r}"
            f"C{cx-k} {cy+r} {cx-r} {cy+k} {cx-r} {cy}Z")


def hex_d(r):
    pts = []
    for i in range(6):
        a = math.pi / 6 + i * math.pi / 3
        pts.append(f"{r*math.cos(a):.1f} {r*math.sin(a):.1f}")
    return "M" + "L".join(pts) + "Z"


def track(nid, at=0.0, loop=False, **props):
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
    if loop:
        t["loop"] = True
    tracks.append(t)


def reveal(nid, at, **kw):
    t = {"target": nid, "reveal": kw}
    if at:
        t["at"] = at
    tracks.append(t)


def word_ritual(nid, at=0.0, stagger=0.1, rise=34, keep=None, dur=0.27):
    kw = {"unit": "word", "stagger": stagger, "dur": dur, "rise": rise,
          "accent": ORANGE, "color_delay": 0.16, "color_dur": 0.33}
    if keep:
        kw["keep"] = keep
    reveal(nid, at, **kw)


def scene(id, bg, dur, nodes, kind="cut", tdur=0.35, **tkw):
    tr = {"kind": kind}
    if kind != "cut":
        tr["dur"] = tdur
    tr.update(tkw)
    scenes.append({"id": id, "bg": bg, "dur": round(dur, 3),
                   "transition": tr, "nodes": nodes})


def drift(sid, dur, z0=1.0, z1=1.035, x=0.0, y=0.0):
    """the camera never stops: slow push/pull on every scene."""
    track(sid, cam_zoom=[(0, z0), (dur, z1, "inOutCubic")],
          cam_x=[(0, 0), (dur, x, "inOutCubic")],
          cam_y=[(0, 0), (dur, y, "inOutCubic")])


# scene 1 --------------------------------------------- hook (real f48-74)
n1 = [text("t1", "The fastest way to scale", 960, 540, 96, weight=600)]
word_ritual("t1", 0.12, stagger=0.06, keep=["scale"])
drift("s1", 2.2, 1.0, 1.045)
scene("s1", CREAM, 2.2, n1)

# scene 2 ----------------------------- orange takeover (real f102-136)
n2 = [
    rect("ow", 960, 540, 1920, 1080, 0, DEEP, gradient={
        "angle": 90, "stops": [{"at": 0, "color": "#f07a33"},
                               {"at": 0.5, "color": DEEP},
                               {"at": 1, "color": "#e04b00"}]}),
    text("t2", "Real time tracking", 960, 530, 92, "#ffffff", weight=600),
]
reveal("t2", 0.12, unit="word", stagger=0.1, dur=0.1, rise=0,
       accent="#ffffff")
drift("s2", 1.5, 1.02, 1.0)
scene("s2", DEEP, 1.5, n2, kind="bloom", tdur=0.4)

# scene 3 -------------------- "across" + platform wheel (real f137-279)
PILL_X, PILL_Y, PITCH = 1145, 533, 145
BRANDS = [("google", "#4285f4", "G"), ("instagram", "#d6249f", "Ig"),
          ("shopify", SHOPIFY, "S"), ("meta", "#0866ff", "M"),
          ("stripe", STRIPE, "S")]
LABELS = ["Google", "Instagram", "Shopify", "Meta", "Stripe"]
n3 = [
    text("across", "across", 780, 533, 76, "#ee7c2b", weight=600),
    path("globe", 610, 533,
         circle_d(26) + "M-26 0L26 0M-14 -21C-22 -8 -22 8 -14 21"
         "M14 -21C22 -8 22 8 14 21", "#ee7c2b", stroke=2.4),
]
track("across", x=[(0, 130), (0.45, 0, "outCubic")],
      opacity=[(0, 0), (0.3, 1)])
track("globe", opacity=[(0.1, 0), (0.4, 1)],
      loop=False, rot=[(0, 0), (3.0, 160)])
# wheel: shopify starts focused, two rolls land on stripe
ROLL_Y = [(0, 0), (0.7, 0), (1.0, -PITCH, "inOutCubic"),
          (1.5, -PITCH), (1.8, -2 * PITCH, "inOutCubic")]
STEPS = [(0, 0), (1.0, 1), (1.8, 2)]  # time -> focus index offset


def wheel_focus(k):
    """per-time opacity/blur for a pill whose home slot is k steps below
    focus at t=0."""
    ops, bls = [], []
    for t0, step in STEPS:
        d = abs(k - step)
        op = 1.0 if d == 0 else (0.32 if d == 1 else 0.1)
        bl = 0.0 if d == 0 else (7.0 if d == 1 else 11.0)
        if ops:
            ops.append((t0 - 0.12, ops[-1][1]))
            bls.append((t0 - 0.12, bls[-1][1]))
        ops.append((t0 + 0.18, op, "inOutCubic"))
        bls.append((t0 + 0.18, bl, "inOutCubic"))
    return ops, bls


for i, (bid, bcol, glyph) in enumerate(BRANDS):
    k = i - 2  # shopify (i=2) at focus slot
    y = PILL_Y + k * PITCH
    ops, bls = wheel_focus(k)
    under = rect(f"pw_{bid}_u", PILL_X, y, 404, 104, 52, "#e3e3e3")
    body = rect(f"pw_{bid}", PILL_X, y, 400, 100, 50, "#ffffff")
    icon = rect(f"pw_{bid}_i", PILL_X - 140, y, 52, 52, 13, bcol)
    gl = text(f"pw_{bid}_g", glyph, PILL_X - 140, y + 1, 30, "#ffffff",
              weight=700)
    lab = text(f"pw_{bid}_t", LABELS[i], PILL_X + 20, y, 34, "#2a2a2a",
               weight=500)
    n3 += [under, body, icon, gl, lab]
    for nid in [f"pw_{bid}_u", f"pw_{bid}", f"pw_{bid}_i", f"pw_{bid}_g",
                f"pw_{bid}_t"]:
        track(nid, y=ROLL_Y, opacity=ops)
    track(f"pw_{bid}", blur=bls)
# selection confirm halo on stripe once it reaches focus
n3.append(rect("halo", PILL_X, PILL_Y + 2 * PITCH, 420, 120, 60, "#f5b08c",
               glow={"sigma": 26, "opacity": 0.0, "color": "#f0a878"}))
track("halo", y=ROLL_Y, opacity=[(0, 0)],
      glow_opacity=[(2.1, 0), (2.4, 0.75, "outCubic"), (2.9, 0)])
track("halo", at=2.1, opacity=[(0, 0), (0.05, 0.35), (0.8, 0)])
n3.append({"id": "cur3", "type": "cursor", "x": 1500, "y": 755, "w": 26,
           "fill": "#111111"})
track("cur3", opacity=[(1.5, 0), (1.7, 1)],
      x=[(1.6, 0), (2.5, -205, "outCubic")],
      y=[(1.6, 0), (2.5, -168, "outCubic")])
drift("s3", 3.0, 1.0, 1.06)
scene("s3", "#faf9f7", 3.0, n3)

# scene 4 ------------------- dashboard materializes (real f272-350)
SBX = 430
n4 = [
    # workspace rail
    rect("rail", 150, 540, 130, 1080, 0, "#f4f1ee"),
    rect("rl1", 150, 210, 62, 62, 14, "#2b241e"),
    rect("rl2", 150, 292, 62, 62, 14, ORANGE),
    rect("rl3", 150, 374, 62, 62, 14, "#5b4bd8"),
    rect("rl4", 150, 456, 62, 62, 14, "#111111"),
    rect("rl5", 150, 538, 62, 62, 14, "#9aa39b"),
    rect("rl6", 150, 620, 62, 62, 14, "#8bc34a"),
    # sidebar
    rect("sbbg", SBX, 540, 430, 1080, 0, "#ffffff"),
    text("sb_an", "ANALYTICS", 320, 265, 20, "#9a938c", weight=600),
    rect("sb_ov_bg", 430, 336, 360, 64, 14, PEACH),
    rect("sb_ov_bar", 258, 336, 6, 64, 3, ORANGE),
    text("sb_ov", "Overview", 366, 336, 28, "#c2571b", weight=600),
    text("sb_rp", "Reports", 358, 409, 28, "#4a453f"),
    text("sb_ads", "Ads", 330, 481, 28, "#4a453f"),
    text("sb_ev", "Events", 352, 553, 28, "#4a453f"),
    text("sb_us", "Users", 344, 625, 28, "#4a453f"),
    text("sb_tl", "TOOLS", 302, 715, 20, "#9a938c", weight=600),
    text("sb_cr", "Create", 348, 786, 28, "#4a453f"),
    rect("sb_beta", 520, 786, 84, 40, 12, PEACH),
    text("sb_beta_t", "Beta", 520, 786, 22, "#c2571b", weight=600),
    text("sb_tr", "Track", 342, 858, 28, "#4a453f"),
    text("sb_cp", "Competitors", 396, 930, 28, "#4a453f"),
    # topbar + stat cards
    text("ov_h", "Overview", 800, 165, 40, INK, weight=600),
    rect("tabs", 1600, 165, 480, 60, 14, "#f2efec"),
    text("tabs_t", "Today   Yesterday   7D   30D", 1600, 165, 22, "#6b655f"),
    text("st1_l", "VISITORS", 905, 320, 22, "#8a837c", weight=600),
    text("st1_v", "121,935", 905, 378, 44, INK, weight=700),
    rect("st1_u", 905, 420, 170, 5, 2.5, ORANGE),
    text("st2_l", "PAGEVIEWS", 1190, 320, 22, "#8a837c", weight=600),
    text("st2_v", "1,044,436", 1200, 378, 44, INK, weight=700),
    text("st3_l", "INITIATE CHECKOUT", 1495, 320, 22, "#8a837c", weight=600),
    text("st3_v", "3,648", 1445, 378, 44, INK, weight=700),
    text("st4_l", "AD SPEND", 1745, 320, 22, "#8a837c", weight=600),
    text("st4_v", "$28,302", 1755, 378, 44, INK, weight=700),
    # chart: full spiky line present from first pixels, never draws on
    text("ax1", "6K", 880, 520, 20, "#9a938c"),
    text("ax2", "5K", 880, 650, 20, "#9a938c"),
    text("ax3", "3K", 880, 780, 20, "#9a938c"),
    text("ax4", "2K", 880, 910, 20, "#9a938c"),
    rect("gr1", 1420, 520, 1000, 2, 1, "#efece9"),
    rect("gr2", 1420, 650, 1000, 2, 1, "#efece9"),
    rect("gr3", 1420, 780, 1000, 2, 1, "#efece9"),
    rect("gr4", 1420, 910, 1000, 2, 1, "#efece9"),
    path("chart", 940, 900,
         "M0 0C60 -30 120 10 180 -20C240 -50 280 -60 330 -70"
         "C370 -78 395 -390 420 -390C445 -390 465 -80 520 -60"
         "C580 -40 640 -90 700 -70C760 -50 820 -110 880 -90"
         "C920 -80 960 -30 1000 -40", ORANGE, stroke=3.5),
    # sidebar lockup -> hero morph pair
    path("herobadge", 320, 168, hex_d(30), ORANGE),
    text("dl_word", "DATALYR", 475, 168, 34, INK, weight=700),
]
CASCADE = [
    (0.05, ["chart", "ax1", "ax2", "ax3", "ax4", "gr1", "gr2", "gr3", "gr4"]),
    (0.18, ["sbbg", "sb_an", "sb_ov_bg", "sb_ov_bar", "sb_ov", "sb_rp",
            "sb_ads", "sb_ev", "sb_us", "sb_tl", "sb_cr", "sb_beta",
            "sb_beta_t", "sb_tr", "sb_cp", "dl_word"]),
    (0.3, ["st1_l", "st1_v", "st1_u"]), (0.36, ["st2_l", "st2_v"]),
    (0.42, ["st3_l", "st3_v"]), (0.48, ["st4_l", "st4_v"]),
    (0.55, ["ov_h", "tabs", "tabs_t"]),
    (0.62, ["rail", "rl1", "rl2", "rl3", "rl4", "rl5", "rl6"]),
]
DISS = 2.7  # dissolve start; the lockup badge never fades (it un-docks)
for at, ids in CASCADE:
    for nid in ids:
        track(nid, opacity=[(at, 0), (at + 0.16, 1), (DISS, 1),
                            (DISS + 0.45, 0)])
n4.append({"id": "cur4", "type": "cursor", "x": 1100, "y": 700, "w": 26,
           "fill": "#111111"})
track("cur4", opacity=[(0.6, 0), (0.7, 1), (2.6, 1), (3.0, 0)],
      x=[(1.0, 0), (1.8, -700, "outCubic")],
      y=[(1.0, 0), (1.8, -510, "outCubic")])
track("s4", cam_zoom=[(0, 1.16), (0.8, 1.02, "outCubic"),
                      (3.2, 1.0, "outCubic")],
      cam_y=[(0, 40), (0.8, 4, "outCubic"), (3.2, 0)])
scene("s4", CREAM, 3.2, n4, kind="fade", tdur=0.35)

# scene 5 -------------- track node + flow build (real f404-540)
n5 = [
    rect("wall", 1560, 560, 1150, 1400, 0, MID, blur=90, opacity=0.0,
         gradient={"angle": 25, "stops": [{"at": 0, "color": "#f6c9a4"},
                                          {"at": 1, "color": "#ee6a2b"}]}),
    path("herobadge", 240, 538, hex_d(52), ORANGE),
    path("conn_lt", 300, 538, "M0 0L440 0", "#f5b08c", stroke=3),
    path("conn_ltd1", 306, 538, circle_d(6), "#f0925c"),
    path("conn_ltd2", 736, 538, circle_d(6), "#f0925c"),
    rect("tracknode", 800, 538, 150, 150, 36, "#ffffff",
         glow={"sigma": 24, "opacity": 0.5, "color": "#f0c090"}),
    path("track_eye", 800, 528,
         "M-26 0C-14 -16 14 -16 26 0C14 16 -14 16 -26 0Z" + circle_d(7),
         ORANGE, stroke=2.6),
    text("track_t", "Track", 800, 578, 24, INK, weight=600),
]
track("wall", opacity=[(0.1, 0), (0.5, 0.9)],
      x=[(0.1, 260), (0.6, 0, "outCubic")])
for nid, at in [("conn_lt", 0.25), ("conn_ltd1", 0.22), ("conn_ltd2", 0.3)]:
    track(nid, opacity=[(at, 0), (at + 0.15, 1)])
track("tracknode", opacity=[(0.3, 0), (0.55, 1)], blur=[(0.3, 12), (0.7, 0)])
track("track_eye", opacity=[(0.4, 0), (0.65, 1)])
track("track_t", opacity=[(0.5, 0), (0.75, 1)])
# the pill-birth mechanic: soft blob condenses, cap first, label last
FLOW = [
    ("fp1", "Every click", 640, 265, 640, 148, 0.9,
     "M-9 -11L7 -3L0 -1L4 7L0 9L-4 1L-9 5Z"),
    ("fp2", "Every Conversion", 900, 660, 700, 148, 1.7,
     "M0 -10L0 10M-7 5C-3 9 4 9 7 5M-7 -5C-3 -9 4 -9 7 -5"),
    ("fp3", "Dollar in real time", 1600, 480, 660, 140, 2.5,
     circle_d(9) + "M0 -5L0 5"),
]
ELBOWS = [("el1", 800, 420, "M0 43L0 -60C0 -78 -18 -78 -36 -78L-90 -78"),
          ("el2", 800, 640, "M0 -22L0 20L510 20"),
          ("el3", 1140, 560, "M0 -22L0 -80L280 -80")]
for eid, ex, ey, d in ELBOWS:
    n5.append(path(eid, ex, ey, d, "#f0925c", stroke=3))
for i, (pid, label, px, py, pw, ph, at, icon_d) in enumerate(FLOW):
    n5 += [
        rect(pid, px, py, pw, ph, ph / 2, MID, gradient={
            "angle": 15, "stops": [{"at": 0, "color": "#f29a60"},
                                   {"at": 1, "color": "#e8671f"}]}),
        rect(pid + "_cap", px - pw / 2 + ph / 2 + 6, py, ph - 22, ph - 22,
             (ph - 22) / 2, "#f2925a"),
        path(pid + "_ic", px - pw / 2 + ph / 2 + 6, py, icon_d, "#ffffff",
             stroke=2.6),
        text(pid + "_t", label, px + 50, py, 54, "#ffffff", weight=600),
    ]
    eid = ELBOWS[i][0]
    track(eid, opacity=[(at - 0.2, 0), (at - 0.02, 1)])
    track(pid, opacity=[(at, 0), (at + 0.12, 1)],
          blur=[(at, 26), (at + 0.42, 0, "outCubic")],
          x=[(at, -40), (at + 0.35, 0, "outCubic")])
    track(pid + "_cap", opacity=[(at + 0.08, 0), (at + 0.22, 1)])
    track(pid + "_ic", opacity=[(at + 0.12, 0), (at + 0.28, 1)])
    track(pid + "_t", opacity=[(at + 0.2, 0), (at + 0.4, 1)])
# camera: slow left pan, hard push-in, decelerating pan
track("s5", cam_zoom=[(0, 1.0), (2.3, 1.0), (2.55, 1.42, "outCubic"),
                      (3.8, 1.47)],
      cam_x=[(0, 0), (1.4, 40, "inOutCubic"), (2.55, 60, "outCubic"),
             (3.8, 120, "outCubic")],
      cam_y=[(0, 0), (2.55, -30, "outCubic"), (3.8, -20)])
scene("s5", "#fdf6f0", 3.8, n5, kind="fade", tdur=0.3)

# scene 6 ------- "Server side accuracy" / "Zero guessing" (real f541-601)
n6 = [
    text("acc", "Server side accuracy", 960, 500, 88, weight=600),
    text("zero", "Zero guessing", 960, 500, 88, weight=600),
    rect("warm", 960, 540, 1920, 1080, 0, PEACH, blur=80),
]
word_ritual("acc", 0.08, stagger=0.09, rise=0)
track("acc", opacity=[(0, 1), (1.18, 1), (1.2, 0)])
track("zero", opacity=[(0, 0), (1.2, 0), (1.22, 1)])
word_ritual("zero", 1.22, stagger=0.11, rise=0)
track("warm", opacity=[(0, 0), (1.9, 0), (2.4, 0.85)])
drift("s6", 2.4, 1.0, 1.04)
scene("s6", "#f7f5f2", 2.4, n6)

# scene 7 --------------- dark prompt + typewriter (real f931-1051)
n7 = [
    rect("lens", 1650, 120, 700, 500, 250, "#7a4018", blur=160, opacity=0.5),
    rect("prompt", 1350, 540, 2000, 470, 235, "#151011",
         glow={"sigma": 40, "opacity": 0.25, "color": "#3a2114"}),
    text("ptext", "Analyze ads", 810, 540, 150, "#f4efe9", weight=500),
    rect("subbtn", 1780, 540, 132, 132, 66, "#ffffff",
         states={"loaded": {"fill": ORANGE}}),
    path("subarrow", 1780, 540, "M-18 18L18 -18M18 -18L-2 -18M18 -18L18 2",
         ORANGE, stroke=5),
    path("subhex", 1780, 540, hex_d(34), "#ffffff"),
]
reveal("ptext", 0.35, unit="type", cadence=0.1, dur=0.1, caret="bar",
       caret_blink=1.0, caret_typing="hidden")
track("subbtn", opacity=[(1.55, 0), (1.7, 1)],
      x=[(1.55, 220), (1.9, 0, "outCubic")],
      glow_opacity=[(2.55, 0), (2.75, 0.7)],
      glow_sigma=[(2.55, 10), (2.9, 30)])
tracks.append({"target": "subbtn", "at": 2.6, "state": "loaded"})
track("subarrow", opacity=[(1.6, 0), (1.75, 1), (2.55, 1), (2.75, 0)],
      x=[(1.55, 220), (1.9, 0, "outCubic")])
track("subhex", opacity=[(0, 0), (2.62, 0), (2.85, 1)])
n7.append({"id": "cur7", "type": "cursor", "x": 1980, "y": 900, "w": 30,
           "fill": "#e8e2da"})
track("cur7", opacity=[(1.8, 0), (1.95, 1), (2.9, 1), (3.15, 0)],
      x=[(1.9, 0), (2.45, -140, "outCubic")],
      y=[(1.9, 0), (2.45, -300, "outCubic")])
track("s7", cam_zoom=[(0, 1.0), (1.6, 1.06, "inOutCubic"),
                      (2.3, 1.06), (3.4, 1.04)],
      cam_x=[(0, 0), (1.6, 0), (2.2, 330, "inOutCubic"), (3.4, 340)])
scene("s7", DARK, 3.4, n7)

# scene 8 --------- campaign cards materialize (real f1052-1124)
CARDS = [
    ("c_ugc", "UGC - All", "5.15x ROAS   $54,190", 540, 330, 0.15, -14, -8),
    ("c_best", "Best Sellers", "7.61x ROAS   $56,960", 1420, 280, 0.3, 12,
     -10),
    ("c_new", "New Arrivals Carousel", "3.75x ROAS   $15,000", 1180, 640,
     0.45, 8, 10),
    ("c_win", "Winter Collection - All", "3.21x ROAS   $28,390", 620, 720,
     0.55, -12, 8),
    ("c_men", "Men's Shoes - Images", "2.35x ROAS   $13,810", 1660, 760,
     0.65, 14, 8),
]
n8 = [
    rect("bloom8", 960, 540, 1500, 1100, 0, "#f2b98a", blur=200, opacity=0.5),
    rect("badge8", 960, 540, 190, 190, 95, ORANGE, gradient={
        "angle": 130, "stops": [{"at": 0, "color": "#f0a878"},
                                {"at": 1, "color": "#e04b00"}]},
        glow={"sigma": 34, "opacity": 0.7, "color": "#f0a878"}),
    path("badge8_h", 960, 540, hex_d(52), "#ffffff"),
]
for cid, title, stat, cx, cy, at, dx, dy in CARDS:
    n8 += [
        rect(cid, cx, cy, 430, 240, 24, "#ffffff",
             glow={"sigma": 18, "opacity": 0.18, "color": "#d9c6b4"}),
        text(cid + "_t", title, cx, cy - 70, 30, INK, weight=600),
        text(cid + "_s", stat, cx, cy - 14, 24, "#8a837c"),
        rect(cid + "_a", cx - 140, cy + 62, 120, 44, 22, "#e9f5e6"),
        text(cid + "_at", "Active", cx - 140, cy + 62, 22, "#3f9a4d",
             weight=600),
    ]
    track(cid, opacity=[(at, 0), (at + 0.25, 1)],
          blur=[(at, 22), (at + 0.85, 0, "outCubic")],
          x=[(at, 0), (2.4, dx, "outCubic")],
          y=[(at, 0), (2.4, dy, "outCubic")])
    for suf, d in [("_t", 0.15), ("_s", 0.2), ("_a", 0.1), ("_at", 0.12)]:
        track(cid + suf, opacity=[(at + d, 0), (at + d + 0.3, 1)],
              x=[(at, 0), (2.4, dx, "outCubic")],
              y=[(at, 0), (2.4, dy, "outCubic")])
track("bloom8", opacity=[(0, 0.55), (1.6, 0.3), (2.4, 0.2)])
track("s8", cam_zoom=[(0, 1.09), (2.4, 1.0, "outCubic")])
scene("s8", "#fbf1e8", 2.4, n8, kind="bloom", tdur=0.45)

# scene 9 -------- stripe + shopify gooey pills + "One" (real f1271-1317)
n9 = [
    rect("st_mark", 620, 480, 122, 122, 30, STRIPE, goo="stripegoo"),
    text("st_mark_t", "S", 620, 481, 64, "#ffffff", weight=700),
    rect("st_pill", 900, 480, 420, 120, 30, STRIPE, goo="stripegoo"),
    text("st_pill_t", "Stripe", 920, 480, 60, "#ffffff", weight=600),
    rect("sh_mark", 1330, 480, 122, 122, 30, "#ffffff", goo="shopgoo"),
    path("sh_bag", 1330, 480,
         "M-26 -18L26 -18L34 30L-34 30ZM-12 -18C-12 -34 12 -34 12 -18",
         SHOPIFY, stroke=3.4),
    rect("sh_pill", 1620, 480, 430, 120, 30, SHOPIFY, goo="shopgoo"),
    text("sh_pill_t", "Shopify", 1640, 480, 60, "#ffffff", weight=600),
    text("one", "One", 620, 700, 90, ORANGE, weight=600),
]
track("st_mark", opacity=[(0.05, 0), (0.07, 1)],
      x=[(0.07, 340), (0.4, 0, "outCubic")])
track("st_mark_t", opacity=[(0.05, 0), (0.07, 1)],
      x=[(0.07, 340), (0.4, 0, "outCubic")])
track("st_pill", opacity=[(0.3, 0), (0.36, 1)],
      w=[(0.3, 60), (0.75, 420, "outCubic")],
      x=[(0.3, -190), (0.75, 0, "outCubic")])
track("st_pill_t", opacity=[(0.5, 0), (0.8, 0.95)])
track("sh_mark", opacity=[(0.5, 0), (0.55, 1)])
track("sh_bag", opacity=[(0.5, 0), (0.55, 1)])
track("sh_pill", opacity=[(0.85, 0), (0.9, 1)],
      w=[(0.85, 60), (1.3, 430, "outCubic")],
      x=[(0.85, -195), (1.3, 0, "outCubic")])
track("sh_pill_t", opacity=[(1.05, 0), (1.35, 0.95)])
track("one", opacity=[(1.5, 0), (1.52, 1)])
track("s9", cam_zoom=[(0, 1.0), (2.2, 1.03)],
      cam_y=[(0, 0), (1.5, 0), (2.2, 30, "inOutCubic")])
scene("s9", "#000000", 2.2, n9)

# scene 10 ------- "Competitors" + physics chips (real f1354-1424)
n10 = [
    rect("corner10", 1700, 120, 900, 600, 0, "#f6c9a4", blur=140,
         opacity=0.6),
    text("comp", "Competitors", 40, 540, 84, weight=600),
    rect("ph_track", 620, 540, 660, 190, 48, ORANGE, goo="phys"),
    text("ph_track_t", "tracking", 620, 540, 64, "#ffffff", weight=600),
    rect("ph_paid", 1160, 390, 400, 190, 48, ORANGE, goo="phys"),
    text("ph_paid_t", "paid", 1160, 390, 64, "#ffffff", weight=600),
    rect("ph_org", 1220, 690, 610, 190, 48, ORANGE, goo="phys"),
    text("ph_org_t", "organic", 1220, 690, 64, "#ffffff", weight=600),
]
word_ritual("comp", 0.05, stagger=0.1, rise=0)
track("ph_track", opacity=[(0.1, 0), (0.16, 1)],
      scale=[(0.1, 0.94), (0.35, 1.0, "outCubic")])
track("ph_track_t", opacity=[(0.2, 0), (0.35, 1)])
track("ph_paid", opacity=[(0.5, 0), (0.54, 1)],
      y=[(0.5, -460), (0.85, 0, "outCubic")])
track("ph_paid_t", opacity=[(0.85, 0), (1.0, 1)],
      y=[(0.5, -460), (0.85, 0, "outCubic")])
track("ph_org", opacity=[(1.0, 0), (1.04, 1)],
      y=[(1.0, 460), (1.35, 0, "outCubic")])
track("ph_org_t", opacity=[(1.35, 0), (1.5, 1)],
      y=[(1.0, 460), (1.35, 0, "outCubic")])
track("s10", cam_zoom=[(0, 1.0), (0.55, 1.0), (0.75, 1.22, "outCubic"),
                       (2.2, 1.25)],
      cam_x=[(0, 0), (0.55, 0), (0.75, 60, "outCubic"), (2.2, 70)])
scene("s10", "#f2ede7", 2.2, n10)

# scene 11 ---------------- event-chain build (real f1498-1657)
CHAIN = [
    ("ch1", "New Visitor", 120, 0.2, -1),
    ("ch2", "Visitor Identified", 315, 0.75, 1),
    ("ch3", "User Signed Up", 510, 1.3, -1),
    ("ch4", "Subscription Started", 705, 1.85, 1),
    ("ch5", "Conversion Postback", 900, 2.4, -1),
]
n11 = []
for i, (cid, label, cy, at, side) in enumerate(CHAIN):
    orange_node = cid == "ch4"
    wv = 60 + len(label) * 19
    n11 += [
        rect(cid + "_b", 960, cy, wv, 100, 26, MID, blur=16,
             streak={"samples": 5, "window": 0.05, "gain": 0.6},
             gradient={"angle": 10,
                       "stops": [{"at": 0, "color": "#f29a60"},
                                 {"at": 1, "color": "#e8671f"}]}),
        rect(cid + "_u", 960, cy, wv, 100, 26, ORANGE),
        rect(cid, 960, cy, wv - 7, 93, 23,
             ORANGE if orange_node else "#ffffff"),
        rect(cid + "_i", 960 - wv / 2 + 62, cy, 56, 56, 14,
             "#8a76e8" if orange_node else "#f1ece6"),
        text(cid + "_it", "S" if orange_node else "◇",
             960 - wv / 2 + 62, cy + 1, 30,
             "#ffffff" if orange_node else "#b0a89e", weight=700),
        text(cid + "_t", label, 960 + 32, cy, 38,
             "#ffffff" if orange_node else ORANGE, weight=600),
    ]
    # blob slides in with motion blur, then the orange drains out
    track(cid + "_b", opacity=[(at, 0), (at + 0.06, 1), (at + 0.3, 1),
                               (at + 0.52, 0)],
          x=[(at, side * 460), (at + 0.34, 0, "outCubic")])
    for suf in ["_u", ""]:
        track(cid + suf, opacity=[(at + 0.28, 0), (at + 0.5, 1)])
    track(cid + "_i", opacity=[(at + 0.34, 0), (at + 0.54, 1)])
    track(cid + "_it", opacity=[(at + 0.34, 0), (at + 0.54, 1)])
    track(cid + "_t", opacity=[(at + 0.3, 0), (at + 0.52, 1)])
    if i < 4:
        # s-curving connector down to the next attach dot
        lat = 34 * (1 if i % 2 == 0 else -1)
        n11.append(path(f"chc{i}", 960, cy + 50,
                        f"M0 0C0 40 {lat} 55 {lat} 95",
                        "#f0925c", stroke=3))
        n11.append(path(f"chcd{i}", 960 + lat, cy + 145, circle_d(7),
                        "#ee7c40"))
        track(f"chc{i}", opacity=[(at + 0.4, 0), (at + 0.56, 1)])
        track(f"chcd{i}", opacity=[(at + 0.48, 0), (at + 0.62, 1)])
# platform squares under the postback node
for j, (pid, glyph, col) in enumerate([("pf_meta", "M", "#0866ff"),
                                       ("pf_tt", "T", "#111111"),
                                       ("pf_gg", "A", "#4285f4")]):
    px = 760 + j * 200
    n11 += [
        rect(pid, px, 1015, 108, 108, 26, "#ffffff"),
        rect(pid + "_u", px, 1015, 114, 114, 28, "#f0b184"),
        text(pid + "_t", glyph, px, 1016, 44, col, weight=700),
        path(f"pfc{j}", px, 952, "M0 -12L0 20", "#f0925c", stroke=3),
    ]
    for suf in ["_u", "", "_t"]:
        track(pid + suf, opacity=[(2.75, 0), (2.95, 1)],
              scale=[(2.75, 0.85), (3.0, 1.0, "outCubic")])
    track(f"pfc{j}", opacity=[(2.8, 0), (2.95, 1)])
# reorder: underlays behind bodies (u before body already handled by list
# order? bodies were appended after underlays inside the loop for chain;
# platform underlay appended after body -> fix by swapping z via re-sort)
n11 = sorted(n11, key=lambda n: 0 if n["id"].endswith("_u") else 1)
# camera: pan down with the build, near-snap pull-back at 3.0
track("s11", cam_zoom=[(0, 1.55), (2.6, 1.55), (3.0, 1.55),
                       (3.12, 1.02, "outCubic"), (3.8, 1.0)],
      cam_y=[(0, -390), (0.55, -390), (0.95, -215, "inOutCubic"),
             (1.5, -215), (1.9, -30, "inOutCubic"), (2.45, -30),
             (2.85, 220, "inOutCubic"), (3.0, 220),
             (3.12, 60, "outCubic"), (3.8, 55)])
scene("s11", "#f6efe9", 3.8, n11)

# scene 12 --------------- linked train-car chips (real f1657-1752)
n12 = []
# ghost of the chain at low opacity behind the chips
for i, (cid, label, cy, at, side) in enumerate(CHAIN):
    wv = 60 + len(label) * 19
    gy = 140 + i * 195
    n12.append(rect(f"gh{i}", 960, gy, wv, 100, 26, "#f0b184"))
    n12.append(text(f"gh{i}_t", label, 960 + 32, gy, 38, "#e5b18c"))
    track(f"gh{i}", opacity=[(0, 0.16)])
    track(f"gh{i}_t", opacity=[(0, 0.35)])
TRAIN = [("tc1", "Connects", 560, 380, 0.2),
         ("tc2", "Map Events", 990, 420, 0.75),
         ("tc3", "Send Postbacks", 1480, 520, 1.3)]
for tid, label, tx, twv, at in TRAIN:
    n12 += [rect(tid, tx, 540, twv, 130, 32, ORANGE, goo="train"),
            text(tid + "_t", label, tx, 540, 52, "#ffffff", weight=600)]
    track(tid, opacity=[(at, 0), (at + 0.1, 1)],
          blur=[(at, 18), (at + 0.4, 0, "outCubic")],
          w=[(at, twv * 0.3), (at + 0.45, twv, "outCubic")],
          x=[(at, -twv * 0.3), (at + 0.45, 0, "outCubic")])
    track(tid + "_t", opacity=[(at + 0.25, 0), (at + 0.45, 1)])
drift("s12", 2.2, 1.0, 1.035, x=-14)
scene("s12", "#f6efe9", 2.2, n12, kind="fade", tdur=0.35)

# scene 13 -------------------- end card (real f1753-1975 compressed)
n13 = [
    rect("blob13", 960, 400, 1400, 900, 450, "#f0a878", blur=220),
    rect("disc", 762, 505, 160, 160, 80, ORANGE, gradient={
        "angle": 130, "stops": [{"at": 0, "color": "#f0a878"},
                                {"at": 1, "color": "#e04b00"}]},
        glow={"sigma": 30, "opacity": 0.5, "color": "#f0a878"}),
    path("disc_h", 762, 505, hex_d(46), "#ffffff"),
    text("wordmark", "Datalyr", 1080, 505, 96, INK, weight=600),
    rect("ec1", 833, 645, 230, 56, 16, ORANGE, goo="endchips"),
    text("ec1_t", "Faster insights", 833, 645, 26, "#ffffff", weight=600),
    rect("ec2", 1092, 645, 250, 56, 16, ORANGE, goo="endchips"),
    text("ec2_t", "Better decisions", 1092, 645, 26, "#ffffff", weight=600),
    text("url", "Get started at Datalyr.com", 960, 960, 40, INK),
]
track("blob13", opacity=[(0, 0.55), (1.4, 0, "outCubic")])
track("disc", scale=[(0, 1.6), (0.5, 1.0, "outCubic")],
      opacity=[(0, 0), (0.15, 1)])
track("disc_h", scale=[(0, 1.6), (0.5, 1.0, "outCubic")],
      opacity=[(0, 0), (0.2, 1)])
reveal("wordmark", 0.4, unit="type", cadence=0.06, dur=0.08, caret="none")
track("ec1", opacity=[(1.2, 0), (1.3, 1)],
      blur=[(1.2, 14), (1.5, 0, "outCubic")])
track("ec1_t", opacity=[(1.35, 0), (1.5, 1)])
track("ec2", opacity=[(1.6, 0), (1.7, 1)],
      w=[(1.6, 80), (1.95, 250, "outCubic")],
      x=[(1.6, -85), (1.95, 0, "outCubic")])
track("ec2_t", opacity=[(1.8, 0), (1.95, 1)])
reveal("url", 2.05, unit="word", stagger=0.09, dur=0.25, rise=26,
       accent=ORANGE, color_delay=0.14, color_dur=0.3,
       keep=["Datalyr.com"])
drift("s13", 3.2, 1.01, 1.0)
scene("s13", END_BG, 3.2, n13, kind="dip", tdur=0.5, dir=DARK)

stage = {"fps": 30, "size": [W, H], "scenes": scenes,
         "audio": {"src": "/assets/audio/pad.m4a", "gain": 0.6,
                   "fade_out": 0.8}}
with open("docs/ai-1.stage.json", "w") as f:
    json.dump(stage, f, indent=1)
with open("docs/ai-1.anim.json", "w") as f:
    json.dump({"tracks": tracks}, f, indent=1)
total = sum(s["dur"] for s in scenes)
print("wrote docs/ai-1.{stage,anim}.json,",
      sum(len(s["nodes"]) for s in scenes), "nodes,", len(tracks),
      f"tracks, {total:.2f}s")
