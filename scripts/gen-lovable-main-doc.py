#!/usr/bin/env python3
# reproduction of lovable-main.mp4 (51.2s, 1280x720) compressed to a ~39s
# arc. call-and-response grammar: black gradient text cards name an SEO
# capability, drawn product stand-ins cash each one out (browser, search
# montage, the Lovable editor, a results page, Property GPT, the Semrush
# table, the SEO review). the heart mark anchors: it assembles from a blob
# at the open (dseq), sits at the hub of the capability pills, and closes
# inside "Build something [heart] Findable -> Searchable -> Lovable".
# tokens from analysis/lovable-main/lovable-main.md.
import json
import os

W, H = 1280, 720
K = 0.5523

# palette (teardown section 1)
ORANGE = "#ed6b09"
RED = "#bc272b"
PURPLE = "#7369ff"
PINK = "#f0407a"
MAGENTA = "#ec0f5f"
BLUEG = "#8ab4f0"
AURORA_BLUE = "#5b8def"
AURORA_PINK = "#ee7fdd"
AURORA_ORANGE = "#f05a25"
PUBLISH = "#2563eb"
FIXALL = "#2f6fe0"
SEMRUSH = "#a586f5"
PANEL = "#1a1a1a"
CHAT = "#141414"

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
scenes, tracks = [], []


def text(id, s, x, y, size, color="#ffffff", weight=500):
    return {"id": id, "type": "text", "text": s, "x": round(x, 1),
            "y": round(y, 1), "color": color,
            "font": {"size": size, "weight": weight}}


def ltext(id, s, left, y, size, color="#ffffff", weight=400):
    # left-anchored inter line, center from the ~0.5em average advance
    return text(id, s, left + len(s) * size * 0.25, y, size, color, weight)


def rect(id, x, y, w, h, r, fill, **kw):
    n = {"id": id, "type": "rect", "x": round(x, 1), "y": round(y, 1),
         "w": round(w, 1), "h": round(h, 1), "radius": r, "fill": fill}
    n.update(kw)
    return n


def path(id, x, y, d, fill, **kw):
    n = {"id": id, "type": "path", "x": round(x, 1), "y": round(y, 1),
         "d": d, "fill": fill}
    n.update(kw)
    return n


def circle_d(r, cx=0, cy=0):
    k = r * K
    return (f"M{cx-r} {cy}C{cx-r} {cy-k} {cx-k} {cy-r} {cx} {cy-r}"
            f"C{cx+k} {cy-r} {cx+r} {cy-k} {cx+r} {cy}"
            f"C{cx+r} {cy+k} {cx+k} {cy+r} {cx} {cy+r}"
            f"C{cx-k} {cy+r} {cx-r} {cy+k} {cx-r} {cy}Z")


def heart_d(s=1.0):
    pts = [("M", 0, 58), ("C", -12, 48, -58, 24, -58, -12),
           ("C", -58, -40, -37, -54, -20, -54),
           ("C", -8, -54, 0, -46, 0, -37),
           ("C", 0, -46, 8, -54, 20, -54),
           ("C", 37, -54, 58, -40, 58, -12),
           ("C", 58, 24, 12, 48, 0, 58)]
    out = ""
    for p in pts:
        out += p[0] + " ".join(f"{v * s:.1f}" for v in p[1:])
    return out + "Z"


def heart(prefix, x, y, s):
    # three-piece stand-in for the gradient mark: purple body, orange
    # left lobe, red right lobe
    return [
        path(prefix + "_b", x, y, heart_d(s), PURPLE),
        path(prefix + "_l", x - 23 * s, y - 22 * s, circle_d(23 * s), ORANGE),
        path(prefix + "_r", x + 23 * s, y - 22 * s, circle_d(23 * s), RED),
    ]


MAG = ("M-3 -3m-8 0a8 8 0 1 0 16 0a8 8 0 1 0 -16 0M3 3L10 10")
SPARK = ("M0 -15C2.5 -5 5 -2.5 15 0C5 2.5 2.5 5 0 15C-2.5 5 -5 2.5 -15 0"
         "C-5 -2.5 -2.5 -5 0 -15Z")
SERVER = ("M-15 -12L15 -12L15 -2L-15 -2ZM-15 2L15 2L15 12L-15 12Z"
          "M-10 -7L-6 -7M-10 7L-6 7")
XMARK = "M-6 -6L6 6M6 -6L-6 6"
WARN = "M0 -9L10 8L-10 8Z"
COMET = "M-10 4C-2 6 8 2 12 -6C6 0 -2 0 -10 4Z"


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
    tracks.append({"target": nid, "at": at, "reveal": kw})


def scene(id, bg, dur, nodes, kind="fade", tdur=0.25, **kw):
    tr = {"kind": kind, "dur": tdur}
    tr.update(kw)
    scenes.append({"id": id, "bg": bg, "dur": round(dur, 3),
                   "transition": tr, "nodes": nodes})


def fade_in(nid, at, dur=0.15, rise=0):
    if rise:
        track(nid, at=at, opacity=[(0, 0), (dur, 1)],
              y=[(0, rise), (dur + 0.1, 0, "outCubic")])
    else:
        track(nid, at=at, opacity=[(0, 0), (dur, 1)])


def aurora(prefix, dur, dark_top=True):
    # the continuous back-half gradient: black -> blue -> pink -> magenta
    # -> orange, plus two blurred drifting pools
    ns = [
        rect(prefix + "_g", W / 2, H / 2, W, H, 0, "#06090f", gradient={
            "angle": 65, "stops": [
                {"at": 0.0, "color": "#05070c"},
                {"at": 0.32, "color": "#3f66c4"},
                {"at": 0.55, "color": AURORA_PINK},
                {"at": 0.78, "color": MAGENTA},
                {"at": 1.0, "color": AURORA_ORANGE}]}),
        rect(prefix + "_p1", 260, 640, 560, 380, 190, MAGENTA, blur=110),
        rect(prefix + "_p2", 1080, 160, 520, 340, 170, "#1b2f66", blur=120),
    ]
    track(prefix + "_p1", opacity=[(0, 0.5)],
          x=[(0, -30), (dur, 40, "inOutCubic")])
    track(prefix + "_p2", opacity=[(0, 0.55)],
          x=[(0, 30), (dur, -40, "inOutCubic")])
    if dark_top:
        ns.append(rect(prefix + "_veil", W / 2, H / 2, W, H, 0, "#000000"))
        track(prefix + "_veil", opacity=[(0, 0.42)])
    return ns


# ------------------------------------------------- s1: logo assemble + apps
# heart blob-morphs in, "Lovable" glyph-reveals beside it, then the lockup
# slides left and "apps" lands pink (color-cycle word)
n1 = heart("h1", 480, 360, 0.62)
n1[0]["dseq"] = [{"at": 0.0, "d": circle_d(8)},
                 {"at": 0.45, "d": heart_d(0.62), "ease": "outCubic"}]
n1 += [
    text("s1_word", "Lovable", 690, 360, 76, "#ffffff", weight=700),
    text("s1_apps", "apps", 924, 360, 76, PINK, weight=700),
]
reveal("s1_word", 0.25, unit="glyph", stagger=0.035, dur=0.22, rise=0,
       accent="#ffffff")
# lockup shift left for "apps"
SHIFT = [(1.7, 0), (2.05, -150, "inOutCubic")]
track("s1_word", x=SHIFT)
track("h1_b", x=SHIFT, opacity=[(0, 0), (0.1, 1)])
track("h1_l", x=SHIFT, opacity=[(0.3, 0), (0.5, 1)],
      scale=[(0.3, 0.4), (0.55, 1.0, "outCubic")])
track("h1_r", x=SHIFT, opacity=[(0.3, 0), (0.5, 1)],
      scale=[(0.3, 0.4), (0.55, 1.0, "outCubic")])
track("s1_apps", x=[(0, -150)], opacity=[(2.0, 0), (2.05, 0)])
reveal("s1_apps", 2.05, unit="glyph", stagger=0.03, dur=0.2, rise=0,
       accent=BLUEG, color_delay=0.1, color_dur=0.3)
track("s1_apps", at=2.0, opacity=[(0, 0), (0.05, 1)])
scene("s1", "#000000", 3.2, n1, kind="cut")

# --------------------------------------------- s2: "are built to be found"
n2 = [text("s2_line", "are built to be found", 640, 360, 64, "#ffffff",
           weight=700)]
reveal("s2_line", 0.15, unit="word", stagger=0.09, dur=0.26, rise=0,
       accent=PINK, color_delay=0.14, color_dur=0.3, keep=["found"])
scene("s2", "#000000", 1.8, n2)

# --------------------------------------------------- s3: browser typewriter
# dark browser chrome, lovable.dev tab chip, "found" typed in the field
n3 = [
    rect("s3_top", 640, 70, W, 140, 0, "#151515"),
    rect("s3_tab", 250, 45, 320, 54, 16, "#242424"),
    path("s3_fav", 120, 45, heart_d(0.16), MAGENTA),
    text("s3_tabt", "lovable.dev", 262, 45, 24, "#d9d9d9"),
    rect("s3_bar", 640, 400, 760, 120, 60, "#101010"),
    path("s3_re", 360, 400, "M-12 0a12 12 0 1 1 5 9.7M-7 12L-7 8L-11 6",
         "#7a7a7a", stroke=3.5),
    text("s3_q", "found", 560, 400, 56, "#f2f2f2"),
]
fade_in("s3_bar", 0.05, 0.12)
reveal("s3_q", 0.55, unit="type", cadence=0.14, dur=0.08, caret="bar",
       caret_blink=1.0, caret_typing="solid")
track("s3", cam_zoom=[(0, 1.06), (1.8, 1.0, "outCubic")],
      cam_y=[(0, 8), (1.8, 0, "outCubic")])
scene("s3", "#0b0b0b", 1.8, n3, kind="cut")

# ------------------------------------------- s4: search-engine Found montage
# google parody (white, rainbow letters) hard-swaps to a bing parody (blue)
GLETTERS = [("F", "#4285f4"), ("o", "#ea4335"), ("u", "#fbbc05"),
            ("n", "#4285f4"), ("d", "#34a853")]
n4 = []
lx = 478
for i, (ch, col) in enumerate(GLETTERS):
    n4.append(text(f"s4_g{i}", ch, lx, 290, 116, col, weight=600))
    lx += 82 if ch != "F" else 76
n4 += [
    rect("s4_gbar", 640, 430, 640, 58, 29, "#ffffff",
         glow={"sigma": 14, "opacity": 0.55, "color": "#c9c9c9"}),
    text("s4_gai", "AI Mode", 860, 430, 20, "#5f6368"),
    rect("s4_gmic", 790, 430, 14, 14, 7, "#4285f4"),
]
# bing overlay steps in at 0.85
n4 += [
    rect("s4_bg2", 640, 360, W, H, 0, "#1a5cc8", gradient={
        "angle": 115, "stops": [{"at": 0, "color": "#123c8f"},
                                {"at": 0.6, "color": "#2e6fd6"},
                                {"at": 1, "color": "#7db1ec"}]}),
    rect("s4_sq1", 596, 216, 26, 26, 4, "#f25022"),
    rect("s4_sq2", 626, 216, 26, 26, 4, "#7fba00"),
    rect("s4_sq3", 596, 246, 26, 26, 4, "#00a4ef"),
    rect("s4_sq4", 626, 246, 26, 26, 4, "#ffb900"),
    text("s4_bf", "Found", 764, 232, 74, "#ffffff", weight=300),
    rect("s4_bbar", 640, 420, 680, 58, 29, "#ffffff"),
    text("s4_bmic", "", 640, 420, 12, "#ffffff"),
]
for i in range(5):
    track(f"s4_g{i}", at=0.02 + i * 0.03, opacity=[(0, 0), (0.06, 1)])
for nid in ["s4_bg2", "s4_sq1", "s4_sq2", "s4_sq3", "s4_sq4", "s4_bf",
            "s4_bbar"]:
    track(nid, opacity=[(0, 0), (0.85, 0), (0.86, 1)])
scene("s4", "#ffffff", 1.6, n4, kind="cut")

# ------------------------------------------------- s5: the Lovable editor
# drawn stand-in: desktop gradient, dark chat panel with the plan bullets,
# white YourSpace preview; "Help users find my app" typed, send ripple
n5 = [
    rect("s5_bg", 640, 360, W, H, 0, "#587beb", gradient={
        "angle": 115, "stops": [{"at": 0, "color": "#587beb"},
                                {"at": 0.55, "color": "#a765c9"},
                                {"at": 1, "color": "#f2488f"}]}),
    rect("s5_win", 680, 367, 900, 578, 14, "#0d0d0d"),
    path("s5_wh", 258, 92, heart_d(0.12), MAGENTA),
    text("s5_wt", "YourSpace", 320, 92, 16, "#c9c9c9"),
    rect("s5_share", 1010, 92, 74, 28, 8, "#232323"),
    text("s5_sharet", "Share", 1010, 92, 14, "#c9c9c9"),
    rect("s5_pub", 1090, 92, 74, 28, 8, PUBLISH),
    text("s5_pubt", "Publish", 1090, 92, 14, "#ffffff", weight=600),
]
# chat panel
n5 += [
    rect("s5_chat", 372, 380, 268, 540, 10, "#161616"),
    rect("s5_uchip", 418, 140, 172, 40, 12, "#242424"),
    ltext("s5_ut1", "Create a rental property", 340, 132, 13, "#e2e2e2"),
    ltext("s5_ut2", "management app", 340, 150, 13, "#e2e2e2"),
    ltext("s5_th", "Thought for 34s", 252, 186, 12, "#8a8a8a"),
    ltext("s5_b1", "SEO-optimized architecture with", 252, 222, 12,
          "#9a9a9a"),
    ltext("s5_b2", "clean URLs, structured data, and", 252, 242, 12,
          "#9a9a9a"),
    ltext("s5_b3", "fast page indexing", 252, 262, 12, "#9a9a9a"),
    ltext("s5_b4", "High-performance backend with", 252, 298, 12, "#9a9a9a"),
    ltext("s5_b5", "scalable database design", 252, 318, 12, "#9a9a9a"),
    ltext("s5_edits", "10 edits made", 252, 354, 12, "#7a7a7a"),
    ltext("s5_show", "Show all", 440, 354, 12, "#6a6a6a"),
    rect("s5_input", 372, 596, 240, 74, 12, "#1e1e1e"),
    ltext("s5_ask", "Ask Lovable...", 264, 582, 13, "#6f6f6f"),
    text("s5_typed", "Help users find my app", 372, 582, 14, "#f0f0f0"),
    rect("s5_send", 470, 614, 22, 22, 11, FIXALL),
    path("s5_sarr", 470, 614, "M0 5L0 -5M-4 -1L0 -5L4 -1", "#ffffff",
         stroke=2.2),
    rect("s5_rip", 470, 614, 26, 26, 13, "#7a9bff"),
]
# preview
n5 += [
    rect("s5_prev", 830, 380, 580, 540, 10, "#ffffff"),
    ltext("s5_nav", "YourSpace   Home   How-it-Works   Testimonials", 570,
          132, 12, "#333333", weight=600),
    rect("s5_cta1", 1050, 132, 110, 26, 13, "#111111"),
    text("s5_cta1t", "Take the first step", 1050, 132, 10, "#ffffff"),
    rect("s5_av1", 780, 176, 18, 18, 9, "#c9a86d"),
    rect("s5_av2", 796, 176, 18, 18, 9, "#8aa5c9"),
    rect("s5_av3", 812, 176, 18, 18, 9, "#b58aae"),
    text("s5_20k", "20k+", 852, 176, 13, "#555555", weight=600),
    text("s5_hero", "YOUR SPACE", 830, 232, 52, "#b9d4ee", weight=800),
    text("s5_sub", "All-in-one platform to track tenants, payments,", 830,
         276, 13, "#7d99b5"),
    text("s5_sub2", "maintenance and performance.", 830, 294, 13, "#7d99b5"),
    rect("s5_cta2", 830, 330, 130, 30, 15, "#111111"),
    text("s5_cta2t", "Try 14 days free", 830, 330, 12, "#ffffff"),
    rect("s5_st1", 900, 400, 150, 62, 10, "#eef3ee"),
    ltext("s5_st1a", "Total Payment", 838, 388, 11, "#66766b"),
    ltext("s5_st1b", "$48,000", 838, 410, 18, "#1c2a20", weight=700),
    rect("s5_st2", 1040, 400, 140, 62, 10, "#f2f6f2"),
    ltext("s5_st2a", "Monthly Rent", 984, 388, 11, "#66766b"),
    ltext("s5_st2b", "$8,500", 984, 410, 18, "#1c2a20", weight=700),
    rect("s5_ph", 680, 470, 200, 160, 10, "#dbe4dd"),
    ltext("s5_pht", "Hudson Row Residences", 596, 528, 11, "#3a463d",
          weight=600),
    ltext("s5_php", "$250", 596, 546, 12, "#1c2a20", weight=700),
]
for i, bh in enumerate([46, 62, 40, 74, 56]):
    n5.append(rect(f"s5_bar{i}", 930 + i * 42, 560 - bh / 2, 26, bh, 5,
                   "#9ecf9a"))
# arrival: window fades up whole, camera pulls back
for n in n5:
    if n["id"] not in ("s5_bg", "s5_typed", "s5_rip"):
        track(n["id"], opacity=[(0.0, 0), (0.22, 1)])
track("s5", cam_zoom=[(0, 1.5), (0.9, 1.0, "outCubic"), (2.2, 1.0),
                      (3.2, 1.18, "inOutCubic")],
      cam_x=[(0, -120), (0.9, 0, "outCubic"), (2.2, 0),
             (3.2, -170, "inOutCubic")],
      cam_y=[(0, 60), (0.9, 0, "outCubic"), (2.2, 0),
             (3.2, 120, "inOutCubic")])
track("s5_ask", opacity=[(0.0, 0), (0.22, 1), (1.0, 1), (1.05, 0)])
reveal("s5_typed", 1.05, unit="type", cadence=0.045, cadence_end=0.03,
       dur=0.06, caret="bar", caret_typing="solid")
track("s5_typed", opacity=[(0, 0), (1.04, 0), (1.05, 1)])
track("s5_rip", opacity=[(0, 0), (2.55, 0), (2.62, 0.85), (3.0, 0)],
      scale=[(2.55, 0.6), (3.0, 2.6, "outCubic")])
track("s5_send", scale=[(2.55, 1.0), (2.62, 0.88), (2.75, 1.0, "outCubic")])
n5.append({"id": "s5_cur", "type": "cursor", "x": 760, "y": 690, "w": 24,
           "fill": "#111111"})
track("s5_cur", x=[(1.9, 0), (2.5, -278, "inOutCubic")],
      y=[(1.9, 0), (2.5, -66, "inOutCubic")],
      opacity=[(0, 0), (1.85, 0), (1.95, 1)])
scene("s5", "#587beb", 3.2, n5, kind="zoom", tdur=0.45)

# ---------------------------------------- s6: card "Auto optimize / for search"
n6 = [
    text("s6_l1", "Auto optimize", 640, 300, 78, "#ffffff", weight=700),
    text("s6_for", "for", 500, 420, 44, "#ffffff", weight=600),
    rect("s6_chip", 576, 420, 46, 46, 13, PINK),
    path("s6_mag", 578, 420, MAG, "#ffffff", stroke=3.0),
    text("s6_search", "search", 700, 420, 44, "#ffffff", weight=600),
]
reveal("s6_l1", 0.12, unit="glyph", stagger=0.028, dur=0.24, rise=0,
       accent=PINK, color_delay=0.12, color_dur=0.34, keep=["Auto"])
fade_in("s6_for", 0.75, 0.12)
for nid in ["s6_chip", "s6_mag"]:
    track(nid, at=0.9, opacity=[(0, 0), (0.1, 1)],
          scale=[(0, 0.6), (0.2, 1.0, "outCubic")])
reveal("s6_search", 1.05, unit="type", cadence=0.07, dur=0.06, caret="bar",
       caret_typing="solid")
track("s6_search", opacity=[(0, 0), (1.04, 0), (1.05, 1)])
scene("s6", "#000000", 2.0, n6, kind="cut")

# --------------------------------------------- s7: search results, ranked
n7 = [
    rect("s7_bar", 640, 74, 720, 50, 25, "#161616"),
    path("s7_mag", 330, 74, MAG, "#8a8a8a", stroke=2.6),
    ltext("s7_q", "bnb management software", 360, 74, 20, "#d9d9d9"),
    # row 1
    ltext("s7_r1t", "Rentra - Real Estate Management", 300, 170, 22,
          "#8ab4f8"),
    ltext("s7_r1u", "https://www.rentra.com", 300, 198, 14, "#9aa0a6"),
    ltext("s7_r1d", "Simplify and grow your vacation rental business",
          300, 222, 15, "#bdc1c6"),
    # yourspace card
    rect("s7_glow", 640, 330, 780, 130, 16, MAGENTA, blur=60),
    rect("s7_card", 640, 330, 780, 130, 16, "#101014"),
    rect("s7_fav", 300, 296, 26, 26, 13, "#2d3a52"),
    path("s7_favh", 300, 296, heart_d(0.11), "#8ab4f0"),
    ltext("s7_r2s", "BnB Management Software", 324, 290, 15, "#dadce0"),
    ltext("s7_r2u", "https://www.yourspace.com", 324, 310, 13, "#9aa0a6"),
    ltext("s7_r2t", "YourSpace | Real Estate Management Software", 288, 340,
          23, "#8ab4f8", weight=600),
    ltext("s7_r2d", "Scale your short-term rental business with our",
          288, 368, 15, "#bdc1c6"),
    # row 3
    ltext("s7_r3t", "Rentiq - Real Estate Management", 300, 460, 22,
          "#8ab4f8"),
    ltext("s7_r3u", "https://www.rentiq.com", 300, 488, 14, "#9aa0a6"),
    ltext("s7_r3d", "Build, manage, and optimize your rental business",
          300, 512, 15, "#bdc1c6"),
]
order = [("s7_bar", 0.05), ("s7_mag", 0.05), ("s7_q", 0.05),
         ("s7_r1t", 0.15), ("s7_r1u", 0.17), ("s7_r1d", 0.19),
         ("s7_card", 0.25), ("s7_fav", 0.28), ("s7_favh", 0.28),
         ("s7_r2s", 0.28), ("s7_r2u", 0.30), ("s7_r2t", 0.32),
         ("s7_r2d", 0.34), ("s7_r3t", 0.4), ("s7_r3u", 0.42),
         ("s7_r3d", 0.44)]
for nid, at in order:
    fade_in(nid, at, 0.14)
track("s7_glow", opacity=[(0, 0), (0.7, 0), (1.3, 0.55, "outCubic"),
                          (2.4, 0.45)])
track("s7", cam_y=[(0, 14), (2.4, -14)],
      cam_zoom=[(0, 1.04), (2.4, 1.08)])
scene("s7", "#050505", 2.4, n7, kind="cut")

# ------------------------------------------ s8: card "Ensure AI Readability"
n8 = [
    text("s8_l1", "Ensure", 640, 290, 84, "#ffffff", weight=700),
    text("s8_ai", "AI", 520, 420, 56, "#ffffff", weight=700),
    rect("s8_tile", 596, 420, 52, 52, 14, "#1e1e1e"),
    path("s8_spark", 596, 420, SPARK, PINK),
    text("s8_read", "Readability", 790, 420, 56, "#ffffff", weight=700),
]
reveal("s8_l1", 0.12, unit="glyph", stagger=0.03, dur=0.26, rise=0,
       accent=PINK, color_delay=0.16, color_dur=0.4, keep=["Ensure"])
fade_in("s8_ai", 0.7, 0.12)
for nid in ["s8_tile", "s8_spark"]:
    track(nid, at=0.8, opacity=[(0, 0), (0.1, 1)],
          scale=[(0, 0.6), (0.22, 1.0, "outCubic")])
reveal("s8_read", 0.9, unit="glyph", stagger=0.025, dur=0.2, rise=0,
       accent=BLUEG, color_delay=0.1, color_dur=0.3)
track("s8_read", opacity=[(0, 0), (0.89, 0), (0.9, 1)])
scene("s8", "#000000", 1.8, n8, kind="cut")

# --------------------------------------------------- s9: Property GPT
n9 = [
    ltext("s9_hdr", "Property GPT", 90, 50, 20, "#ececec", weight=600),
    rect("s9_login", 1150, 50, 90, 32, 16, PUBLISH),
    text("s9_logint", "Log in", 1150, 50, 14, "#ffffff"),
    rect("s9_qb", 880, 120, 480, 46, 23, "#2a2a2a"),
    text("s9_q", "How should I manage my rental property?", 880, 120, 18,
         "#f0f0f0"),
    path("s9_cup", 232, 208, "M-8 -9L8 -9L7 1C6 6 3 8 0 8C-3 8 -6 6 -7 1Z"
         "M-3 8L3 8M-5 12L5 12M-8 -7C-12 -7 -12 -1 -8 0M8 -7C12 -7 12 -1 8 0",
         "#f4b400", stroke=2.0),
    ltext("s9_a1", "Top 10 BnB Property Management Software", 268, 210, 26,
          "#f2f2f2", weight=700),
    ltext("s9_r1", "1.  YourSpace", 250, 290, 24, "#8ab4f0", weight=600),
    rect("s9_r1u", 358, 306, 118, 3, 1.5, "#8ab4f0"),
    ltext("s9_r1b", "-  All-in-One BnB Management Software", 440, 290, 22,
          "#e6e6e6"),
    ltext("s9_url", "https://www.yourspace.com", 288, 330, 18, "#9aa0a6"),
    ltext("s9_d1", "Scale your short-term rental business with our automated",
          288, 366, 17, "#bdc1c6"),
    ltext("s9_d2", "channel manager, guest inbox, and real-time calendar sync.",
          288, 392, 17, "#bdc1c6"),
    rect("s9_sep", 640, 440, 800, 2, 1, "#2c2c2c"),
    ltext("s9_r2", "2.  Avilo", 250, 490, 24, "#8ab4f0", weight=600),
    ltext("s9_r2b", "-  Get Your Rental Business Under Control", 420, 490,
          22, "#e6e6e6"),
]
reveal("s9_q", 0.1, unit="type", cadence=0.028, dur=0.05, caret="bar",
       caret_typing="solid")
track("s9_qb", opacity=[(0, 0), (0.1, 1)])
track("s9_q", opacity=[(0, 0), (0.09, 0), (0.1, 1)])
build = [("s9_cup", 1.35), ("s9_a1", 1.35), ("s9_r1", 1.6), ("s9_r1u", 1.7),
         ("s9_r1b", 1.72), ("s9_url", 1.85), ("s9_d1", 1.95), ("s9_d2", 2.05),
         ("s9_sep", 2.15), ("s9_r2", 2.25), ("s9_r2b", 2.32)]
for nid, at in build:
    fade_in(nid, at, 0.14, rise=10)
track("s9", cam_y=[(1.3, 0), (3.0, 8)])
scene("s9", "#0f0f0f", 3.0, n9, kind="cut")

# --------------------------------------- s10: "Chat with" + SEMRUSH logo
n10 = [
    text("s10_l1", "Chat with", 640, 280, 78, "#ffffff", weight=700),
    path("s10_comet", 486, 428, COMET, SEMRUSH,
         keys={"scale": [{"t": 0, "v": 1.6}]}),
    text("s10_sr", "SEMRUSH", 640, 430, 54, SEMRUSH, weight=800),
    text("s10_adobe", "An Adobe Company", 640, 500, 20, "#e6e6e6"),
]
reveal("s10_l1", 0.12, unit="word", stagger=0.1, dur=0.26, rise=0,
       accent=PINK, color_delay=0.14, color_dur=0.3, keep=["with"])
fade_in("s10_comet", 0.8, 0.15)
fade_in("s10_sr", 0.8, 0.15)
fade_in("s10_adobe", 1.0, 0.15)
scene("s10", "#000000", 1.8, n10, kind="cut")

# ----------------------------------------------- s11: the Semrush table
n11 = [
    rect("s11_qb", 900, 70, 480, 44, 22, "#262626"),
    ltext("s11_q1", "Hey", 690, 70, 18, "#f0f0f0"),
    ltext("s11_q2", "Semrush,", 732, 70, 18, SEMRUSH, weight=600),
    ltext("s11_q3", "how findable is my site?", 808, 70, 18, "#f0f0f0"),
    rect("s11_tile", 300, 150, 34, 34, 10, "#2b2440"),
    path("s11_ci", 300, 150, COMET, SEMRUSH),
    ltext("s11_sr", "Semrush", 328, 150, 22, "#c9c9c9", weight=600),
    ltext("s11_th", "Thought for 15s  >", 282, 196, 18, "#8a8a8a"),
    ltext("s11_lg", "Looking good! Here's the picture:", 282, 240, 22,
          "#f0f0f0"),
    ltext("s11_h1", "Market", 282, 300, 20, "#e6e6e6", weight=700),
    ltext("s11_h2", "Ranked Keywords", 460, 300, 20, "#e6e6e6", weight=700),
    ltext("s11_h3", "Estimated Traffic", 780, 300, 20, "#ef7fb2", weight=700),
]
ROWS11 = [("US", "#3c5a9a", "10", "10,000", 356),
          ("UK", "#7a3c5a", "4", "6,000", 420),
          ("CA", "#9a3c3c", "3", "4,000", 484),
          ("AU", "#3c7a5a", "3", "3,800", 548)]
for i, (cc, fcol, kw, tr, y) in enumerate(ROWS11):
    n11 += [
        rect(f"s11_f{i}", 296, y, 26, 18, 4, fcol),
        ltext(f"s11_c{i}", cc, 318, y, 20, "#e6e6e6"),
        ltext(f"s11_k{i}", kw, 470, y, 20, "#e6e6e6"),
        ltext(f"s11_t{i}", tr, 786, y, 20, "#f06a9e", weight=600),
        rect(f"s11_u{i}", 640, y + 30, 700, 3, 1.5, MAGENTA, gradient={
            "angle": 0, "stops": [{"at": 0, "color": PINK},
                                  {"at": 1, "color": MAGENTA}]}),
    ]
n11.append(ltext("s11_next",
                 "What I'd do next - run competitive analysis to find "
                 "keyword gaps you can win.", 282, 640, 21, "#f0f0f0"))
for nid, at in [("s11_qb", 0.08), ("s11_q1", 0.08), ("s11_q2", 0.08),
                ("s11_q3", 0.08), ("s11_tile", 0.25), ("s11_ci", 0.25),
                ("s11_sr", 0.25), ("s11_th", 0.35), ("s11_lg", 0.5),
                ("s11_h1", 0.65), ("s11_h2", 0.65), ("s11_h3", 0.65)]:
    fade_in(nid, at, 0.14)
for i in range(4):
    at = 0.75 + i * 0.18
    for c in ["f", "c", "k", "t"]:
        fade_in(f"s11_{c}{i}", at, 0.14)
    # gradient sweep: the underline grows left to right
    track(f"s11_u{i}", at=at + 0.05,
          opacity=[(0, 0), (0.05, 1)],
          w=[(0, 0), (0.45, 700, "outCubic")],
          x=[(0, -350), (0.45, 0, "outCubic")])
reveal("s11_next", 1.8, unit="word", stagger=0.065, dur=0.2, rise=0,
       accent=PINK, color_delay=0.12, color_dur=0.28, keep=["win."])
scene("s11", CHAT, 3.0, n11, kind="cut")

# ------------------------------------------------- s12: the Publish click
n12 = [
    rect("s12_bg", 640, 360, W, H, 0, "#587beb", gradient={
        "angle": 115, "stops": [{"at": 0, "color": "#587beb"},
                                {"at": 0.55, "color": "#a765c9"},
                                {"at": 1, "color": "#f2488f"}]}),
    rect("s12_win", 620, 420, 1000, 560, 16, "#0d0d0d"),
    rect("s12_prev", 640, 460, 820, 420, 12, "#ffffff"),
    text("s12_hero", "YOUR SPACE", 640, 400, 58, "#b9d4ee", weight=800),
    text("s12_sub", "All-in-one platform to track tenants, payments,", 640,
         450, 15, "#7d99b5"),
    rect("s12_share", 950, 170, 96, 40, 10, "#232323"),
    text("s12_sharet", "Share", 950, 170, 17, "#c9c9c9"),
    rect("s12_gh", 1030, 170, 40, 40, 10, "#232323"),
    path("s12_ghp", 1030, 170, circle_d(9), "#c9c9c9"),
    rect("s12_pub", 1140, 170, 120, 44, 10, PUBLISH,
         states={"pressed": {"scale": 0.94}}),
    text("s12_pubt", "Publish", 1140, 170, 19, "#ffffff", weight=600),
    rect("s12_rip", 1140, 170, 130, 54, 14, "#7a9bff"),
]
n12.append({"id": "s12_cur", "type": "cursor", "x": 700, "y": 560, "w": 26,
            "fill": "#111111"})
for n in n12:
    if n["id"] not in ("s12_bg", "s12_rip", "s12_cur"):
        track(n["id"], opacity=[(0, 0), (0.18, 1)])
track("s12_cur", x=[(0.25, 0), (0.9, 440, "inOutCubic")],
      y=[(0.25, 0), (0.9, -390, "inOutCubic")])
tracks.append({"target": "s12_pub", "at": 1.05, "state": "pressed"})
track("s12_rip", opacity=[(0, 0), (1.05, 0), (1.1, 0.8), (1.5, 0)],
      scale=[(1.05, 0.7), (1.5, 2.0, "outCubic")])
track("s12", cam_zoom=[(0, 1.0), (1.0, 1.28, "inOutCubic")],
      cam_x=[(0, 0), (1.0, 240, "inOutCubic")],
      cam_y=[(0, 0), (1.0, -130, "inOutCubic")])
scene("s12", "#587beb", 1.6, n12, kind="fade", tdur=0.3)

# --------------------------------------------------- s13: Your SEO review
n13 = aurora("s13a", 2.6, dark_top=True)
n13 += [
    rect("s13_panel", 640, 370, 880, 520, 22, PANEL),
    ltext("s13_hd", "Your SEO review", 250, 160, 36, "#ffffff", weight=700),
    rect("s13_fix", 990, 160, 120, 48, 12, FIXALL,
         states={"pressed": {"scale": 0.94}}),
    text("s13_fixt", "Fix all", 990, 160, 20, "#ffffff", weight=600),
    rect("s13_sep", 640, 210, 800, 2, 1, "#2a2a2a"),
]
ISSUES = [("x", "#e3133d", "Search results show truncated text", 280),
          ("w", "#e8a13c", "Homepage heading structure and body copy are "
           "sparse", 390),
          ("w2", "#e8a13c", "Social link previews are cluttered", 500)]
for i, (kind, col, label, y) in enumerate(ISSUES):
    icon_d = XMARK if kind == "x" else WARN
    n13 += [
        rect(f"s13_ic{i}", 300, y, 40, 40, 20, "#241418"),
        path(f"s13_ip{i}", 300, y, icon_d, col, stroke=2.6),
        ltext(f"s13_lb{i}", label, 340, y, 23, "#ececec"),
    ]
n13.append({"id": "s13_cur", "type": "cursor", "x": 700, "y": 620, "w": 26,
            "fill": "#111111"})
for nid in ["s13_panel", "s13_hd", "s13_fix", "s13_fixt", "s13_sep"]:
    fade_in(nid, 0.06, 0.18)
for i in range(3):
    at = 0.35 + i * 0.22
    for p in ["ic", "ip", "lb"]:
        track(f"s13_{p}{i}", at=at, opacity=[(0, 0), (0.16, 1)],
              y=[(0, 18), (0.28, 0, "outCubic")])
track("s13_cur", x=[(1.4, 0), (1.95, 290, "inOutCubic")],
      y=[(1.4, 0), (1.95, -460, "inOutCubic")],
      opacity=[(0, 0), (1.35, 0), (1.45, 1)])
tracks.append({"target": "s13_fix", "at": 2.1, "state": "pressed"})
track("s13_panel", rot=[(1.9, 0), (2.6, -2.0, "inOutCubic")])
scene("s13", "#050505", 2.6, n13, kind="cut")

# ------------------------------------------- s14/s15: the feature cards
n14 = aurora("s14a", 1.5)
n14 += [
    text("s14_l1", "Server-Side", 640, 280, 70, "#ffffff", weight=800),
    rect("s14_tile", 468, 380, 58, 58, 15, "#1e1e1e"),
    path("s14_srv", 468, 380, SERVER, AURORA_ORANGE, stroke=2.4),
    text("s14_l2", "Rendering", 692, 380, 70, "#ffffff", weight=800),
    text("s14_cap", "for new apps", 640, 470, 24, "#ffffff"),
]
reveal("s14_l1", 0.1, unit="glyph", stagger=0.02, dur=0.2, rise=0,
       accent="#ffffff")
for nid in ["s14_tile", "s14_srv"]:
    track(nid, at=0.25, opacity=[(0, 0), (0.12, 1)],
          scale=[(0, 0.6), (0.25, 1.0, "outCubic")])
reveal("s14_l2", 0.3, unit="glyph", stagger=0.02, dur=0.2, rise=0,
       accent="#ffffff")
track("s14_l2", opacity=[(0, 0), (0.29, 0), (0.3, 1)])
fade_in("s14_cap", 0.55, 0.15)
scene("s14", "#050505", 1.5, n14, kind="dissolve", tdur=0.35)

n15 = aurora("s15a", 1.5)
n15 += [
    rect("s15_tile", 408, 320, 58, 58, 15, "#1e1e1e"),
    path("s15_db", 408, 320, "M-12 -10a12 5 0 1 0 24 0a12 5 0 1 0 -24 0"
         "M-12 -10L-12 8a12 5 0 0 0 24 0L12 -10M2 -2L-4 4L2 4L-4 12",
         AURORA_ORANGE, stroke=2.2),
    text("s15_l1", "Pre-Rendering", 700, 320, 70, "#ffffff", weight=800),
    text("s15_cap", "for existing apps", 640, 420, 24, "#ffffff"),
]
for nid in ["s15_tile", "s15_db"]:
    track(nid, at=0.1, opacity=[(0, 0), (0.12, 1)],
          scale=[(0, 0.6), (0.25, 1.0, "outCubic")])
reveal("s15_l1", 0.15, unit="glyph", stagger=0.02, dur=0.2, rise=0,
       accent="#ffffff")
fade_in("s15_cap", 0.45, 0.15)
scene("s15", "#050505", 1.5, n15, kind="fade", tdur=0.3)

# --------------------------------------- s16: capability pills orbit the heart
n16 = heart("h16", 640, 360, 0.85)
n16[0]["dseq"] = [{"at": 0.0, "d": circle_d(12)},
                  {"at": 0.4, "d": heart_d(0.85), "ease": "outCubic"}]
for nid in ["h16_l", "h16_r"]:
    track(nid, opacity=[(0.25, 0), (0.45, 1)],
          scale=[(0.25, 0.4), (0.5, 1.0, "outCubic")])
PILLS = [
    (130, [("Sitemap", 250, 0), ("robots.txt", 520, 0),
           ("Chat with Semrush", 880, 0)], 46),
    (250, [("Optimize for search", 240, 1), ("Keyword analysis", 630, 1),
           ("Audit backlinks", 1010, 0)], -38),
    (360, [("Chat with Semrush data", 210, 0),
           ("Optimize for search", 1060, 0)], 30),
    (470, [("Audit backlinks", 230, 0), ("robots.txt", 540, 0),
           ("AI readability", 860, 1)], -46),
    (600, [("SSR", 380, 0), ("Pre-rendering", 640, 0),
           ("Keyword analysis", 980, 0)], 38),
]
pi = 0
for y, row, drift in PILLS:
    for label, x, bright in row:
        wv = len(label) * 22 * 0.52 + 56
        ink = "#f0f0f0" if bright else "#5c5c5c"
        rim = 0.5 if bright else 0.22
        n16 += [
            rect(f"s16_pr{pi}", x, y, wv + 3, 47, 24, PINK),
            rect(f"s16_p{pi}", x, y, wv, 44, 22, "#101010"),
            text(f"s16_pt{pi}", label, x, y, 22, ink),
        ]
        for suf in ["pr", "p", "pt"]:
            track(f"s16_{suf}{pi}", at=0.1 + (pi % 5) * 0.05,
                  opacity=[(0, 0), (0.2, 1 if suf != "pr" else rim)],
                  x=[(0, 0), (2.2, drift, "inOutCubic")])
        pi += 1
scene("s16", "#0a0a0a", 2.2, n16, kind="fade", tdur=0.3)

# --------------------------------------------------------- s17: end card
n17 = aurora("s17a", 3.4)
n17 += [
    text("s17_build", "Build something", 430, 360, 62, "#ffffff", weight=700),
    path("s17_h", 758, 358, heart_d(0.42), "#ffffff"),
    text("s17_find", "Findable", 950, 360, 62, "#ffffff", weight=700),
    text("s17_srch", "Searchable", 984, 360, 62, "#ffffff", weight=700),
    text("s17_lov", "Lovable", 934, 360, 62, "#ffffff", weight=700),
]
reveal("s17_build", 0.15, unit="word", stagger=0.1, dur=0.26, rise=0,
       accent="#ffffff")
track("s17_h", opacity=[(0.2, 0), (0.4, 1)],
      scale=[(0.2, 0.6), (0.5, 1.0, "outCubic")])
track("s17_find", opacity=[(0, 0), (0.5, 0), (0.51, 1), (1.05, 1),
                           (1.06, 0)])
track("s17_srch", opacity=[(0, 0), (1.06, 0), (1.07, 1), (1.6, 1),
                           (1.61, 0)])
track("s17_lov", opacity=[(0, 0), (1.61, 0), (1.62, 1)],
      scale=[(1.61, 1.1), (2.0, 1.0, "outCubic")])
scene("s17", "#050505", 3.4, n17, kind="fade", tdur=0.35)

stage = {"fps": 30, "size": [W, H], "scenes": scenes,
         "audio": {"src": "/assets/audio/pad.m4a", "gain": 0.6,
                   "fade_out": 0.9}}
with open("docs/lovable-main.stage.json", "w") as f:
    json.dump(stage, f, indent=1)
with open("docs/lovable-main.anim.json", "w") as f:
    json.dump({"tracks": tracks}, f, indent=1)
total = sum(s["dur"] for s in scenes)
print("wrote docs/lovable-main.{stage,anim}.json,",
      sum(len(s["nodes"]) for s in scenes), "nodes,", len(tracks),
      f"tracks, {total:.2f}s, {len(scenes)} scenes")
