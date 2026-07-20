#!/usr/bin/env python3
# reproduction of animations/ravie.mp4 (google "tools that grow with you",
# 94.5s) compressed to a ~39s arc. the film's grammar, kept: the search-bar
# zoom device opens chapters (extreme close-up input, typewriter, pull-back
# into the product surface), green underglow = search, blue = gemini,
# blue+green underline = the dark account form, exactly two hard cuts and
# both bright<->dark. all product screens are flat stand-ins with the real
# layout/colors sampled from analysis/ravie/frames. same overlay contract
# as the other gen scripts: scene-local `at`, unique ids per scene, one
# track per node per prop, x/y keys are offsets.
import json
import os

W, H = 1138, 640
CX, CY = W / 2, H / 2
EM = 0.5  # inter average advance per char, em fraction

INK = "#202124"
GREY = "#9aa0a6"
BLUE = "#4285f4"
GBLUE = "#3c88e8"
DBLUE = "#3462ad"
GREEN = "#4ebc66"
RED = "#ea4335"
YELLOW = "#fbbc05"
LGREEN = "#34a853"
LAV = "#eaf3fc"
SHEETS = "#1e9e5a"
DARK = "#1e2223"
CELL_BLUE = "#1a73e8"

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def text(id, s, x, y, size, color, weight=400):
    return {"id": id, "type": "text", "text": s, "x": round(x, 1), "y": y,
            "color": color, "font": {"size": size, "weight": weight,
                                     "family": "inter"}}


def ltext(id, s, left, y, size, color, weight=400):
    return text(id, s, left + len(s) * size * EM / 2, y, size, color, weight)


def rect(id, x, y, w, h, r, fill, **kw):
    n = {"id": id, "type": "rect", "x": round(x, 1), "y": round(y, 1),
         "w": w, "h": h, "radius": r, "fill": fill}
    n.update(kw)
    return n


def path(id, x, y, d, fill, stroke=None, **kw):
    n = {"id": id, "type": "path", "x": round(x, 1), "y": round(y, 1),
         "d": d, "fill": fill}
    if stroke:
        n["stroke"] = stroke
    n.update(kw)
    return n


def circle_d(r):
    k = r * 0.5523
    return (f"M{-r} 0C{-r} {-k} {-k} {-r} 0 {-r}C{k} {-r} {r} {-k} {r} 0"
            f"C{r} {k} {k} {r} 0 {r}C{-k} {r} {-r} {k} {-r} 0Z")


def magnifier_d(r):
    h = r * 0.71
    return circle_d(r) + f"M{h} {h}L{r * 1.7} {r * 1.7}"


def spark_d(s):
    # gemini 4-point spark
    c = s * 0.14
    return (f"M0 {-s}C{c} {-c} {c} {-c} {s} 0C{c} {c} {c} {c} 0 {s}"
            f"C{-c} {c} {-c} {c} {-s} 0C{-c} {-c} {-c} {-c} 0 {-s}Z")


tracks = []


def keyed(nid, at=None, **props):
    keys = {}
    for name, seq in props.items():
        out = []
        for k in seq:
            kk = {"t": k[0], "v": k[1]}
            if len(k) > 2:
                kk["ease"] = k[2]
            out.append(kk)
        keys[name] = out
    t = {"target": nid, "keys": keys}
    if at is not None:
        t["at"] = at
    tracks.append(t)


def typed(nid, at, cadence, cadence_end=None, blink=1.0):
    r = {"unit": "type", "cadence": cadence, "dur": 0.08, "caret": "bar",
         "caret_blink": blink}
    if cadence_end:
        r["cadence_end"] = cadence_end
    tracks.append({"target": nid, "at": at, "reveal": r})


def fade_in(nid, at, dur=0.35, to=1.0):
    keyed(nid, opacity=[(at, 0), (at + dur, to)])


# ---------------------------------------------------------------- scene s1
# search-zoom "How much is rent in Seattle?": the homepage is staged whole,
# the camera starts at 2.9x framed on the search field (matches f0001),
# the query types, then a long-decel pull-back reveals the page (f0105).
s1 = []

# green underglow bleeding from the bar's bottom edge, pulses on submit
s1.append(rect("s1_glow", 569, 344, 700, 16, 8, GREEN, blur=16))
s1.append(rect("s1_bar", 569, 285, 1010, 108, 54, "#ffffff",
               glow={"sigma": 14, "opacity": 0.5, "color": "#c8d2d6",
                     "dy": 6}))
s1.append(path("s1_mag", 140, 283, magnifier_d(13), GREY, stroke=2.6))
s1.append(rect("s1_caret", 194, 285, 4, 50, 1, BLUE))
s1.append(ltext("s1_q", "How much is rent in Seattle?", 190, 285, 30, INK))
# mic, lens, AI Mode pill at the bar's right end
s1.append(rect("s1_mic", 880, 282, 11, 18, 5, BLUE))
s1.append(path("s1_mica", 880, 288, "M-8 -2a8 8 0 0 0 16 0M0 6L0 11",
               GREY, stroke=2.0))
s1.append(path("s1_lens", 928, 285, circle_d(9) + "M0 0", GREY, stroke=2.2))
s1.append(rect("s1_aipill", 1010, 285, 125, 60, 30, "#eef4fe"))
s1.append(path("s1_aisp", 972, 285, spark_d(9), BLUE))
s1.append(text("s1_ait", "AI Mode", 1024, 285, 19, BLUE, weight=500))
# wordmark + buttons live outside the close-up frame, revealed by the pull
for i, (ch, col, ax) in enumerate([("G", BLUE, 445), ("o", RED, 507),
                                   ("o", YELLOW, 563), ("g", BLUE, 619),
                                   ("l", LGREEN, 660), ("e", RED, 700)]):
    s1.append(text(f"s1_wm{i}", ch, ax, 128, 96, col, weight=500))
s1.append(rect("s1_b1", 465, 435, 180, 52, 10, "#f3f6f7"))
s1.append(text("s1_b1t", "Google Search", 465, 435, 17, "#3c4043"))
s1.append(rect("s1_b2", 680, 435, 196, 52, 10, "#f3f6f7"))
s1.append(text("s1_b2t", "I'm Feeling Lucky", 680, 435, 17, "#3c4043"))

# camera: framed so the magnifier sits at screen x~300 (f0001), pull-back
# is a long asymptotic decel. cam offsets shrink proportionally with z.
ZS = [(0.0, 2.9), (1.7, 2.9), (1.95, 2.35, "outCubic"),
      (2.25, 1.6, "outCubic"), (2.6, 1.22, "outCubic"),
      (2.95, 1.05, "outCubic"), (3.3, 1.0, "outCubic")]
keyed("s1", cam_zoom=ZS,
      cam_x=[(k[0], round(-336.2 * (k[1] - 1) / 1.9, 1), *k[2:])
             for k in ZS],
      cam_y=[(k[0], round(-35.0 * (k[1] - 1) / 1.9, 1), *k[2:])
             for k in ZS])
typed("s1_q", 0.35, 0.05, cadence_end=0.032)
keyed("s1_q", opacity=[(0, 0), (0.34, 0), (0.345, 1)])
keyed("s1_caret", opacity=[(0.0, 1), (0.34, 1), (0.35, 0)])
keyed("s1_glow", opacity=[(0.0, 0), (0.3, 0.4), (3.0, 0.4), (3.25, 0.75)])

# ---------------------------------------------------------------- scene s2
# the budget sheet (f0250): one highlighted row, salary then rent typed in.
s2 = []
for i, tx in enumerate([240, 310, 385, 460]):
    s2.append(rect(f"s2_tb{i}", tx, 40, 26, 26, 6, "#c8cdd1", blur=2))
for i, cx_ in enumerate([124, 336, 548, 761, 973]):
    s2.append(text(f"s2_col{i}", "FGHIJ"[i], cx_, 166, 16, "#80868b"))
for i, gx in enumerate([233, 444, 658, 870, 1080]):
    s2.append(rect(f"s2_gv{i}", gx, 320, 1, 640, 0, "#eceff1"))
s2.append(rect("s2_hline", 569, 190, 1138, 1, 0, "#e3e7e9"))
s2.append(rect("s2_band", 436, 342, 872, 46, 0, "#e8f0fe"))
s2.append(rect("s2_rline1", 569, 319, 1138, 1, 0, "#e3e7e9"))
s2.append(rect("s2_rline2", 569, 366, 1138, 1, 0, "#e3e7e9"))
HDR2 = [("Monthly Savings", 129), ("Monthly Expense", 351),
        ("Annual Salary", 580), ("Monthly Rent", 793)]
for i, (h, hx) in enumerate(HDR2):
    s2.append(text(f"s2_h{i}", h, hx, 297, 19, INK, weight=500))
s2.append(text("s2_v1", "$300", 175, 342, 20, INK))
s2.append(text("s2_v2", "$1,110", 398, 342, 20, INK))
s2.append(text("s2_sal", "$55,000", 595, 342, 20, INK))
s2.append(text("s2_rent", "$2,000", 792, 342, 20, INK))
s2.append(path("s2_cell", 548, 342, "M-105 -23L105 -23L105 23L-105 23Z",
               CELL_BLUE, stroke=2.4))
for tab, tx in [("Medical", 160), ("Allowance", 366), ("Activities", 584),
                ("Total", 826), ("Average", 1010)]:
    s2.append(text(f"s2_tab_{tab}", tab, tx, 607, 20, GREY))
    keyed(f"s2_tab_{tab}", opacity=[(0, 0.4)])
typed("s2_sal", 0.5, 0.07)
typed("s2_rent", 1.8, 0.075)
keyed("s2_rent", opacity=[(0, 0), (1.55, 0), (1.56, 1)])
keyed("s2_cell", x=[(1.5, 0), (1.501, 213)])
# the sheet breathes
tracks.append({"target": "s2", "loop": True, "keys": {"cam_zoom": [
    {"t": 0, "v": 1.0}, {"t": 1.6, "v": 1.007, "ease": "inOutCubic"},
    {"t": 3.2, "v": 1.0, "ease": "inOutCubic"}]}})

# ---------------------------------------------------------------- scene s3
# gemini "5 years" (f0430): lavender surface, prompt pill, analysis steps,
# white answer card, words born blue cooling to ink, "5 years" stays blue.
def gemini_scene(p, answer_mid, keep, pin=False, t0=0.45, dt=0.45):
    sc = []
    sc.append(rect(f"{p}_pill", 700, 52, 560, 76, 38, "#ffffff",
                   glow={"sigma": 10, "opacity": 0.4, "color": "#c5d4e8",
                         "dy": 4}))
    sc.append(text(f"{p}_pq", "How long until I can afford to buy?",
                   700, 52, 22, INK))
    sc.append(path(f"{p}_spark", 158, 112, spark_d(15), BLUE))
    sc.append(path(f"{p}_chev", 160, 207, "M-9 -4L0 5L9 -4", INK, stroke=2.4))
    sc.append(ltext(f"{p}_as", "Analysis steps", 210, 207, 24, INK,
                    weight=500))
    sc.append(rect(f"{p}_card", 570, 455, 892, 372, 22, "#ffffff"))
    lines = ["The time until you can afford to buy", answer_mid,
             "financial figures provided."]
    for i, ln in enumerate(lines):
        sc.append(ltext(f"{p}_l{i}", ln, 160, 337 + i * 62, 27, INK))
        rv = {"unit": "word", "stagger": 0.045, "dur": 0.3, "rise": 0,
              "accent": BLUE, "color_delay": 0.5, "color_dur": 0.5}
        if i == 1:
            rv["keep"] = keep
        tracks.append({"target": f"{p}_l{i}", "at": t0 + i * dt,
                       "reveal": rv})
    if pin:
        sc.append(rect(f"{p}_pinc", 1055, 80, 58, 58, 29, "#ffffff",
                       glow={"sigma": 9, "opacity": 0.45, "color": "#c5d4e8",
                             "dy": 3}))
        sc.append(path(f"{p}_pin", 1055, 76,
                       "M0 16C0 16 -12 3 -12 -5a12 12 0 0 1 24 0"
                       "C12 3 0 16 0 16Z", RED))
        sc.append(path(f"{p}_pind", 1055, 71, circle_d(4.6), "#ffffff"))
    for n in sc:
        nid = n["id"]
        if nid.endswith(("_card", "_spark", "_chev", "_as")):
            fade_in(nid, 0.12, 0.3)
    return sc


s3 = gemini_scene("s3", "is 5 years, based on the current",
                  ["5", "years,"])

# ---------------------------------------------------------------- scene s4
# search close-up, "How to get a promotion" (f0560/f0599): the device held
# in extreme close-up the whole scene, green underglow, then blur-dissolve.
def search_close(p, query, at, cadence):
    sc = []
    sc.append(rect(f"{p}_glow", 600, 482, 900, 28, 14, GREEN, blur=22))
    sc.append(rect(f"{p}_bar", 660, 320, 1240, 320, 160, "#eff3f4"))
    sc.append(rect(f"{p}_top", 725, 162, 950, 3, 1, BLUE, blur=1.5))
    sc.append(path(f"{p}_mag", 208, 316, magnifier_d(26), "#b0b6ba",
                   stroke=4.0))
    sc.append(rect(f"{p}_caret", 384, 320, 5, 80, 1, BLUE))
    sc.append(ltext(f"{p}_q", query, 380, 320, 56, INK))
    typed(f"{p}_q", at, cadence, cadence_end=cadence * 0.6)
    keyed(f"{p}_q", opacity=[(0, 0), (at - 0.02, 0), (at - 0.01, 1)])
    keyed(f"{p}_caret", opacity=[(0.0, 1), (at - 0.01, 1), (at, 0)])
    keyed(f"{p}_glow", opacity=[(0, 0.55)])
    keyed(f"{p}_top", opacity=[(0, 0.6)])
    return sc


s4 = search_close("s4", "How to get a promotion", 0.35, 0.055)

# ---------------------------------------------------------------- scene s5
# the work-week calendar (f0680): dense blue/green blocks, life reorganizes
# mid-scene. block = rect + title + time sharing one motion group.
CAL_TIME = "#dbe9fb"


def block(sc, p, title_lines, time_s, cx_, cy_, w, h, fill, tcol="#ffffff",
          mcol=None, streak=False):
    kw = {}
    if streak:
        kw["streak"] = {"samples": 5, "window": 0.045, "gain": 0.25}
    ids = [f"{p}_r"]
    sc.append(rect(f"{p}_r", cx_, cy_, w, h, 12, fill, **kw))
    left = cx_ - w / 2 + 18
    mcol = mcol or (CAL_TIME if tcol == "#ffffff" else tcol)
    if h < 60:
        sc.append(ltext(f"{p}_t", f"{title_lines[0]}, {time_s}", left, cy_,
                        18, tcol, weight=600))
        ids.append(f"{p}_t")
    else:
        for i, tl in enumerate(title_lines):
            sc.append(ltext(f"{p}_t{i}", tl, left, cy_ - h / 2 + 30 + i * 26,
                            20, tcol, weight=600))
            ids.append(f"{p}_t{i}")
        sc.append(ltext(f"{p}_m", time_s, left,
                        cy_ - h / 2 + 32 + len(title_lines) * 26, 16, mcol))
        ids.append(f"{p}_m")
    return ids


s5 = []
for i, gx in enumerate([32, 388, 742, 1096]):
    s5.append(rect(f"s5_gv{i}", gx, 320, 2, 640, 0, "#eef1f3"))
for i, gy in enumerate([90, 180, 270, 360, 450, 540]):
    s5.append(rect(f"s5_gh{i}", 569, gy, 1138, 1, 0, "#f1f4f5"))
B5 = [
    ("s5_b1", ["Project Work"], "2 - 4:30pm", 205, 195, 325, 255, GBLUE),
    ("s5_b2", ["Emails"], "5 - 6pm", 205, 417, 325, 95, DBLUE),
    ("s5_b3", ["Performance Review"], "4 - 5pm", 560, 315, 325, 95, GBLUE),
    ("s5_b4", ["Team Meeting"], "7 - 8pm", 560, 600, 325, 90, GBLUE),
    ("s5_b5", ["Client Call"], "1:30 - 2:30pm", 915, 62, 325, 105, "#f5f9ff",
     GBLUE),
    ("s5_b6", ["Lunch Sync"], "2:30pm", 915, 141, 325, 40, GBLUE),
    ("s5_b7", ["Get Takeout"], "3 - 4pm", 915, 219, 325, 85, GREEN),
    ("s5_b8", ["Data Entry"], "5:30pm", 915, 443, 325, 40, DBLUE),
]
groups5 = {}
for i, (p, tl, ts, bx, by, bw, bh, fill, *tc) in enumerate(B5):
    groups5[p] = block(s5, p, tl, ts, bx, by, bw, bh, fill,
                       *(tc or []))
    born = 0.1 + (i % 4) * 0.09
    if p == "s5_b7":
        born = 1.25
    for nid in groups5[p]:
        fade_in(nid, born, 0.3)
# the reorganize: performance review rises into its slot, data entry slides
# over from the middle column
for nid in groups5["s5_b3"]:
    keyed(nid, y=[(0.0, 140), (1.1, 140), (1.55, 0, "outCubic")])
for nid in groups5["s5_b8"]:
    keyed(nid, x=[(0.0, -354), (1.4, -354), (1.85, 0, "outCubic")])

# ---------------------------------------------------------------- scene s6
# the budget grows (f0751-1050 compressed): salary retyped 55k -> 75k,
# savings 300 -> 580, title retyped to "Joint Savings Plan", a green-ringed
# collaborator avatar appears.
s6 = []
s6.append(rect("s6_appicon", 60, 36, 30, 38, 6, SHEETS))
s6.append(path("s6_appgrid", 60, 38, "M-8 -8L8 -8M-8 0L8 0M-8 8L8 8",
               "#ffffff", stroke=2.0))
s6.append(ltext("s6_told", "Personal Savings Plan", 105, 36, 22, INK,
                weight=500))
s6.append(ltext("s6_tnew", "Joint Savings Plan", 105, 36, 22, INK,
                weight=500))
s6.append(path("s6_tbox", 230, 36, "M-135 -21L135 -21L135 21L-135 21Z",
               CELL_BLUE, stroke=2.0))
for i, cx_ in enumerate([124, 336, 548, 761, 973]):
    s6.append(text(f"s6_col{i}", "FGHIJ"[i], cx_, 166, 16, "#80868b"))
for i, gx in enumerate([233, 444, 658, 870, 1080]):
    s6.append(rect(f"s6_gv{i}", gx, 320, 1, 640, 0, "#eceff1"))
s6.append(rect("s6_band", 436, 342, 872, 46, 0, "#e8f0fe"))
s6.append(rect("s6_rline1", 569, 319, 1138, 1, 0, "#e3e7e9"))
s6.append(rect("s6_rline2", 569, 366, 1138, 1, 0, "#e3e7e9"))
for i, (h, hx) in enumerate(HDR2):
    s6.append(text(f"s6_h{i}", h, hx, 297, 19, INK, weight=500))
s6.append(text("s6_v300", "$300", 175, 342, 20, INK))
s6.append(text("s6_v580", "$580", 175, 342, 20, INK))
s6.append(text("s6_v2", "$1,110", 398, 342, 20, INK))
s6.append(text("s6_sal55", "$55,000", 595, 342, 20, INK))
s6.append(text("s6_sal75", "$75,000", 595, 342, 20, INK))
s6.append(text("s6_rent", "$2,000", 792, 342, 20, INK))
s6.append(path("s6_cell", 548, 342, "M-105 -23L105 -23L105 23L-105 23Z",
               CELL_BLUE, stroke=2.4))
s6.append(rect("s6_avring", 1080, 36, 40, 40, 20, GREEN,
               glow={"sigma": 7, "opacity": 0.5, "color": GREEN}))
s6.append(rect("s6_av", 1080, 36, 33, 33, 16.5, "#b9bec4"))
s6.append(path("s6_avhead", 1080, 32, circle_d(6), "#7d838a"))
s6.append(path("s6_avbody", 1080, 46,
               "M-10 4C-10 -6 10 -6 10 4L-10 4Z", "#7d838a"))
# salary retype
keyed("s6_sal55", opacity=[(0, 1), (0.5, 1), (0.55, 0)])
keyed("s6_sal75", opacity=[(0, 0), (0.65, 0), (0.66, 1)])
typed("s6_sal75", 0.66, 0.07)
# savings odometer flip
keyed("s6_v300", opacity=[(0, 1), (1.3, 1), (1.42, 0)],
      y=[(1.3, 0), (1.42, -14, "outCubic")])
keyed("s6_v580", opacity=[(0, 0), (1.3, 0), (1.42, 1)],
      y=[(1.3, 14), (1.42, 0, "outCubic")])
# title retype
keyed("s6_told", opacity=[(0, 1), (1.9, 1), (1.95, 0)])
keyed("s6_tnew", opacity=[(0, 0), (2.04, 0), (2.05, 1)])
typed("s6_tnew", 2.05, 0.042)
keyed("s6_tbox", opacity=[(0, 0), (1.75, 0), (1.85, 1)])
# collaborator lands
for nid in ("s6_avring", "s6_av", "s6_avhead", "s6_avbody"):
    tracks.append({"target": nid, "at": 2.35,
                   "enter": {"preset": "pop", "dur": 0.3}})
    fade_in(nid, 2.35, 0.2)

# ---------------------------------------------------------------- scene s7
# gemini re-run: same card, maps pin top right, the figure drops to
# "6 months". the payoff of the raise + joint savings.
s7 = gemini_scene("s7", "is 6 months, based on the current",
                  ["6", "months,"], pin=True, t0=0.3, dt=0.38)

# ---------------------------------------------------------------- scene s8
# search close-up, "Baby girl names": the tonal pivot.
s8 = search_close("s8", "Baby girl names", 0.3, 0.055)

# ---------------------------------------------------------------- scene s9
# AI overview baby names (f1601-1654): list resolves top-down, the cursor
# parks on Charlotte.
s9 = []
s9.append(path("s9_spark", 120, 90, spark_d(16), BLUE))
s9.append(ltext("s9_ait", "AI Overview", 155, 90, 26, "#5f6368"))
NAMES = [
    ("Amelia:", "Classic, elegant, and perennially popular."),
    ("Sophia/Sofia:", "Timeless and beloved."),
    ("Emma:", "A simple, strong classic."),
    ("Isabella:", "Graceful and enduring."),
    ("Charlotte:", "Royal and popular."),
]
for i, (nm, rest) in enumerate(NAMES):
    y = 170 + i * 62
    label = "• " + nm
    s9.append(ltext(f"s9_n{i}", label, 90, y, 24, INK, weight=600))
    s9.append(ltext(f"s9_d{i}", rest, 90 + len(label) * 12 + 12, y, 24,
                    "#3c4043"))
    born = 0.3 + i * 0.15
    keyed(f"s9_n{i}", opacity=[(born, 0), (born + 0.3, 1)],
          y=[(born, 10), (born + 0.35, 0, "outCubic")])
    keyed(f"s9_d{i}", opacity=[(born + 0.06, 0), (born + 0.36, 1)],
          y=[(born + 0.06, 10), (born + 0.41, 0, "outCubic")])
s9.append(rect("s9_glowbar", 569, 630, 1000, 22, 11, GREEN, blur=20))
keyed("s9_glowbar", opacity=[(0, 0.4)])
s9.append(rect("s9_pill", 930, 566, 300, 58, 29, "#ffffff",
               glow={"sigma": 10, "opacity": 0.4, "color": "#c5d4e8",
                     "dy": 4}))
s9.append(path("s9_psp", 812, 566, spark_d(10), BLUE))
s9.append(text("s9_pt", "Dive deeper in AI Mode", 948, 566, 19, INK))
for nid in ("s9_pill", "s9_psp", "s9_pt"):
    fade_in(nid, 0.9, 0.3)
s9.append({"id": "s9_cur", "type": "cursor", "x": 750, "y": 320, "w": 24,
           "fill": "#111111"})
keyed("s9_cur", x=[(1.1, 0), (1.65, -420, "outCubic")],
      y=[(1.1, 0), (1.65, 122, "outCubic")])

# --------------------------------------------------------------- scene s10
# Charlotte's birthdays (f1655-1809 compressed): one hard vertical scroll,
# year 2 out the top, year 18 in from below. streaks carry the motion blur.
s10 = []
for i, gx in enumerate([32, 388, 742, 1096]):
    s10.append(rect(f"s10_gv{i}", gx, 320, 2, 640, 0, "#eef1f3"))
for i, gy in enumerate([90, 180, 270, 360, 450, 540]):
    s10.append(rect(f"s10_gh{i}", 569, gy, 1138, 1, 0, "#f1f4f5"))
YA = [
    ("s10_a1", ["Quarterly Summary"], "3 - 4:30pm", 205, 100, 310, 105,
     GBLUE),
    ("s10_a2", ["Dinner w/ In-Laws"], "6 - 7pm", 205, 368, 310, 85, GREEN),
    ("s10_a3", ["Make Cupcakes"], "3 - 4pm", 560, 77, 310, 95, DBLUE),
    ("s10_a4", ["Dinner"], "4 - 5pm", 560, 172, 310, 90, GREEN),
    ("s10_a5", ["Charlotte's 2nd", "Birthday Party"], "5 - 7pm", 560, 318,
     310, 185, GBLUE),
    ("s10_a6", ["Pitch Review"], "3 - 4:30pm", 915, 100, 310, 105, GBLUE),
    ("s10_a7", ["Reunion @ Char House"], "5:30 - 7:30pm", 915, 372, 310,
     190, "#ffffff", GREEN),
]
YB = [
    ("s10_b1", ["Sales Overview Meeting"], "10 - 11am", 205, 120, 310, 95,
     GBLUE),
    ("s10_b2", ["Drive In-Laws to Airport"], "4 - 5pm", 205, 340, 310, 85,
     GREEN),
    ("s10_b3", ["Pick Up Birthday Cake"], "3 - 4pm", 560, 140, 310, 85,
     DBLUE),
    ("s10_b4", ["Charlotte's 18th", "Birthday Party"], "5 - 7pm", 560, 360,
     310, 185, GBLUE),
    ("s10_b5", ["Video Conference"], "2 - 3pm", 915, 130, 310, 95, GBLUE),
    ("s10_b6", ["Yearly Travel Planning"], "6 - 7pm", 915, 380, 310, 85,
     GREEN),
]
for spec in YA:
    p, tl, ts, bx, by, bw, bh, fill = spec[:8]
    ids = block(s10, p, tl, ts, bx, by, bw, bh, fill, *spec[8:],
                streak=True)
    for nid in ids:
        fade_in(nid, 0.1, 0.3)
        keyed(nid, y=[(0.9, 0), (1.5, -720, "inCubic")])
for spec in YB:
    p, tl, ts, bx, by, bw, bh, fill = spec[:8]
    ids = block(s10, p, tl, ts, bx, by, bw, bh, fill, *spec[8:],
                streak=True)
    for nid in ids:
        keyed(nid, y=[(0.0, 720), (1.05, 720), (1.75, 0, "outCubic")])

# --------------------------------------------------------------- scene s11
# HARD CUT to the dark account form (f1811-1954): First name "Charlotte",
# then Last name "Garcia". active field underline glows blue -> green.
s11 = []


def dark_field(p, cy_):
    s11.append(rect(f"{p}_o", 690, cy_, 940, 130, 12, "#4a5458"))
    s11.append(rect(f"{p}_i", 690, cy_, 936, 126, 10, DARK))
    s11.append(rect(f"{p}_u", 690, cy_ - 64, 936, 3, 1, None,
                    gradient={"angle": 0, "stops": [
                        {"at": 0, "color": BLUE},
                        {"at": 1, "color": GREEN}]},
                    glow={"sigma": 7, "opacity": 0.6, "color": GREEN}))
    s11[-1]["fill"] = BLUE


dark_field("s11_f1", 225)
s11.append(rect("s11_l1bg", 318, 161, 116, 24, 2, DARK))
s11.append(text("s11_l1", "First name", 318, 161, 20, "#8ab4f8"))
s11.append(ltext("s11_first", "Charlotte", 260, 225, 36, "#e8eaed"))
dark_field("s11_f2", 415)
s11.append(ltext("s11_ph2", "Last name (optional)", 260, 415, 36,
                 "#80868b"))
s11.append(ltext("s11_last", "Garcia", 260, 415, 36, "#e8eaed"))
typed("s11_first", 0.4, 0.08)
keyed("s11_f1_u", opacity=[(0, 1), (1.6, 1), (1.75, 0.2)])
keyed("s11_f2_u", opacity=[(0, 0), (1.6, 0), (1.75, 1)])
keyed("s11_ph2", opacity=[(0, 1), (1.62, 1), (1.74, 0)])
keyed("s11_last", opacity=[(0, 0), (1.74, 0), (1.75, 1)])
typed("s11_last", 1.75, 0.08)

# --------------------------------------------------------------- scene s12
# dark gmail (f2030-2206 compressed): the NYU acceptance rises in, then
# Dad's "Spreadsheet shared with you" lands above it with the green pill.
s12 = []
s12.append(ltext("s12_search", "Search mail", 70, 60, 22, "#80868b"))
s12.append(path("s12_ref", 46, 145, "M-8 0a8 8 0 1 0 3 -6.5M-5 -9L-5 -6.5"
                "L-2.5 -6.5", "#9aa0a6", stroke=2.0))
s12.append(path("s12_dots", 106, 145, "M0 -7L0 -7M0 0L0 0M0 7L0 7",
                "#9aa0a6", stroke=3.0))
s12.append(rect("s12_div", 569, 200, 1138, 1, 0, "#2a3134"))
s12.append(ltext("s12_nyu", "NYU Admissions", 30, 424, 26, "#e8eaed",
                 weight=600))
s12.append(ltext("s12_sub", "Welcome to NYU, Charlotte!", 360, 424, 26,
                 "#e8eaed", weight=600))
s12.append(ltext("s12_pre", "- You've been accepted to New Yo...", 720,
                 424, 24, GREY))
s12.append(rect("s12_sweep", 569, 458, 1138, 2, 1, None,
                gradient={"angle": 0, "stops": [
                    {"at": 0, "color": BLUE}, {"at": 1, "color": GREEN}]},
                glow={"sigma": 6, "opacity": 0.5, "color": GREEN}))
s12[-1]["fill"] = GREEN
for nid in ("s12_nyu", "s12_sub", "s12_pre"):
    keyed(nid, opacity=[(0.2, 0), (0.55, 1)],
          y=[(0.2, 44), (0.65, 0, "outCubic")])
keyed("s12_sweep", opacity=[(0.55, 0), (0.75, 1)],
      w=[(0.55, 0), (1.05, 1138, "outCubic")])
s12.append(ltext("s12_dad", "Dad", 48, 266, 26, "#d6f2db", weight=600))
s12.append(ltext("s12_share", "Spreadsheet shared with you:", 360, 266, 26,
                 "#e8eaed", weight=500))
s12.append(rect("s12_pillo", 590, 330, 434, 68, 34, "#3a5441"))
s12.append(rect("s12_pill", 590, 330, 430, 64, 32, "#232b2d"))
s12.append(rect("s12_shicon", 400, 330, 34, 34, 8, SHEETS,
                glow={"sigma": 9, "opacity": 0.8, "color": GREEN}))
s12.append(path("s12_shgrid", 400, 330, "M-8 -6L8 -6M-8 0L8 0M-8 6L8 6",
                "#ffffff", stroke=1.8))
s12.append(ltext("s12_pillt", "Copy of Joint Savings Plan", 428, 330, 24,
                 "#d6f2db"))
for i, nid in enumerate(("s12_dad", "s12_share", "s12_pillo", "s12_pill",
                         "s12_shicon", "s12_shgrid", "s12_pillt")):
    keyed(nid, opacity=[(1.45 + i * 0.03, 0), (1.8 + i * 0.03, 1)],
          y=[(1.45, 30), (1.95, 0, "outCubic")])

# --------------------------------------------------------------- scene s13
# HARD CUT to bright sheets (f2207-2625 compressed): the shared file opens,
# the title is retyped to Charlotte's own, and Dad's comment lands.
s13 = []
s13.append(rect("s13_appicon", 60, 38, 30, 38, 6, SHEETS))
s13.append(path("s13_appgrid", 60, 40, "M-8 -8L8 -8M-8 0L8 0M-8 8L8 8",
                "#ffffff", stroke=2.0))
s13.append(ltext("s13_told", "Copy of Joint Savings Plan", 105, 36, 22,
                 INK, weight=500))
s13.append(ltext("s13_tnew", "Charlotte's College Budgeting Plan", 105, 36,
                 22, INK, weight=500))
s13.append(path("s13_tbox", 300, 36, "M-205 -21L205 -21L205 21L-205 21Z",
                CELL_BLUE, stroke=2.0))
for i, cx_ in enumerate([13, 223, 436, 648, 859, 1070]):
    s13.append(text(f"s13_col{i}", "GHIJKL"[i], cx_, 166, 16, "#80868b"))
for i, gx in enumerate([118, 330, 542, 754, 966]):
    s13.append(rect(f"s13_gv{i}", gx, 320, 1, 640, 0, "#eceff1"))
s13.append(rect("s13_band", 378, 342, 756, 46, 0, "#e8f0fe"))
s13.append(rect("s13_rline1", 569, 319, 1138, 1, 0, "#e3e7e9"))
s13.append(rect("s13_rline2", 569, 366, 1138, 1, 0, "#e3e7e9"))
HDR13 = [("Scholarship", 53), ("Monthly Expenses", 233),
         ("Monthly Income", 455), ("Spending Money", 661)]
for i, (h, hx) in enumerate(HDR13):
    s13.append(text(f"s13_h{i}", h, hx, 297, 19, INK, weight=500))
for i, (v, vx) in enumerate([("$6,000", 66), ("-$900", 287), ("$720", 505),
                             ("$250", 716)]):
    s13.append(text(f"s13_v{i}", v, vx, 342, 20, INK))
s13.append(path("s13_cell", 444, 342, "M-105 -23L105 -23L105 23L-105 23Z",
                CELL_BLUE, stroke=2.4))
s13.append(rect("s13_como", 900, 343, 294, 56, 5, GREEN))
s13.append(rect("s13_comi", 900, 343, 288, 50, 3, "#ffffff"))
s13.append(rect("s13_dadtag", 1023, 311, 44, 22, 3, GREEN))
s13.append(text("s13_dadt", "Dad", 1023, 311, 13, "#ffffff", weight=600))
s13.append(ltext("s13_com", "Don't forget to have fun!", 768, 343, 20,
                 INK))
for tab, tx in [("Activities", 260), ("Total", 500), ("Average", 686)]:
    s13.append(text(f"s13_tab_{tab}", tab, tx, 607, 20, GREY))
    keyed(f"s13_tab_{tab}", opacity=[(0, 0.4)])
keyed("s13_told", opacity=[(0, 1), (0.65, 1), (0.7, 0)])
keyed("s13_tnew", opacity=[(0, 0), (0.79, 0), (0.8, 1)])
typed("s13_tnew", 0.8, 0.034)
for nid in ("s13_como", "s13_comi", "s13_dadtag", "s13_dadt"):
    fade_in(nid, 2.05, 0.25)
keyed("s13_com", opacity=[(0, 0), (2.28, 0), (2.29, 1)])
typed("s13_com", 2.3, 0.048)
tracks.append({"target": "s13", "loop": True, "keys": {"cam_zoom": [
    {"t": 0, "v": 1.0}, {"t": 1.9, "v": 1.006, "ease": "inOutCubic"},
    {"t": 3.8, "v": 1.0, "ease": "inOutCubic"}]}})

# --------------------------------------------------------------- scene s14
# "Tools that grow with you." blur-in: words born google-blue, cooling to
# near-black.
s14 = [text("s14_head", "Tools that grow with you.", CX, 318, 42, INK,
            weight=500)]
tracks.append({"target": "s14_head", "at": 0.15, "reveal": {
    "unit": "word", "stagger": 0.09, "dur": 0.4, "rise": 0, "accent": BLUE,
    "color_delay": 0.35, "color_dur": 0.5}})

# --------------------------------------------------------------- scene s15
# the Google G end card, blue leading the fade.
G_PATHS = [
    ("#4285f4", "M533.5 278.4c0-18.5-1.5-31.9-4.7-45.9H272.1v83.3h150.4"
     "c-3 25.2-19.4 63.2-55.8 88.7l81.3 63c48.7-45 76.5-111.2 76.5-189.1"),
    ("#ea4335", "M272.1 107.7c46.4 0 77.9 20 95.9 36.7l70-68.3"
     "C395.7 33.1 337.8 0 272.1 0 174.8 0 93 51 52.9 130.5l83.9 64.8"
     "c19-56.7 72.4-99.1 135.3-99.1"),
    ("#fbbc05", "M136.8 348.9c-5-14.9-7.9-30.8-7.9-47.2s2.9-32.3 7.7-47.2"
     "l-84-64.8c-16.5 32.9-26 69.9-26 112s9.5 79.1 26.1 112z"),
    ("#34a853", "M272.1 544.3c65.7 0 120.9-21.6 161.2-58.8l-81.3-63"
     "c-21.7 15.1-50.8 25.6-79.9 25.6-62.9 0-116.3-42.4-135.3-99.1"
     "l-83.9 64.8c40.1 79.5 121.9 130.5 219.2 130.5"),
]
s15 = []
for i, (col, d) in enumerate(G_PATHS):
    s15.append(path(f"s15_g{i}", CX - 45, 318 - 45, d, col,
                    keys={"scale": [{"t": 0, "v": 90 / 544}]}))
    fade_in(f"s15_g{i}", 0.12 + i * 0.06, 0.4)

stage = {
    "fps": 30,
    "size": [W, H],
    "audio": {"src": "/assets/audio/pad.m4a", "gain": 0.55,
              "fade_out": 0.8},
    "scenes": [
        {"id": "s1", "bg": "#f6f9fa", "dur": 3.4,
         "transition": {"kind": "cut"}, "nodes": s1},
        {"id": "s2", "bg": "#ffffff", "dur": 3.2,
         "transition": {"kind": "zoom", "dur": 0.5}, "nodes": s2},
        {"id": "s3", "bg": LAV, "dur": 2.6,
         "transition": {"kind": "dissolve", "dur": 0.45}, "nodes": s3},
        {"id": "s4", "bg": "#f6f9fa", "dur": 2.0,
         "transition": {"kind": "fade", "dur": 0.4}, "nodes": s4},
        {"id": "s5", "bg": "#fbfdfe", "dur": 2.4,
         "transition": {"kind": "zoom", "dur": 0.5}, "nodes": s5},
        {"id": "s6", "bg": "#ffffff", "dur": 3.2,
         "transition": {"kind": "dissolve", "dur": 0.45}, "nodes": s6},
        {"id": "s7", "bg": LAV, "dur": 2.4,
         "transition": {"kind": "dissolve", "dur": 0.45}, "nodes": s7},
        {"id": "s8", "bg": "#f6f9fa", "dur": 1.8,
         "transition": {"kind": "fade", "dur": 0.4}, "nodes": s8},
        {"id": "s9", "bg": "#fbfdfe", "dur": 2.2,
         "transition": {"kind": "zoom", "dur": 0.5}, "nodes": s9},
        {"id": "s10", "bg": "#fbfdfe", "dur": 2.6,
         "transition": {"kind": "dissolve", "dur": 0.45}, "nodes": s10},
        {"id": "s11", "bg": DARK, "dur": 2.8,
         "transition": {"kind": "cut"}, "nodes": s11},
        {"id": "s12", "bg": "#1b1f20", "dur": 2.6,
         "transition": {"kind": "fade", "dur": 0.4}, "nodes": s12},
        {"id": "s13", "bg": "#ffffff", "dur": 3.8,
         "transition": {"kind": "cut"}, "nodes": s13},
        {"id": "s14", "bg": "#ffffff", "dur": 1.8,
         "transition": {"kind": "dip", "dur": 0.4, "dir": "#ffffff"},
         "nodes": s14},
        {"id": "s15", "bg": "#ffffff", "dur": 2.0,
         "transition": {"kind": "fade", "dur": 0.5}, "nodes": s15},
    ],
}

with open("docs/ravie.stage.json", "w") as f:
    json.dump(stage, f, indent=1)
with open("docs/ravie.anim.json", "w") as f:
    json.dump({"tracks": tracks}, f, indent=1)
total = sum(s["dur"] for s in stage["scenes"])
print("wrote docs/ravie.{stage,anim}.json,",
      sum(len(s["nodes"]) for s in stage["scenes"]), "nodes,",
      len(tracks), "tracks,", round(total, 1), "s")
