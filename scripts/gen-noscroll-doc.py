#!/usr/bin/env python3
# reproduction of radio/noscroll (45.5s, 1920x1080), compressed to ~41.8s.
# the ai feed-digest narrative: dark satire feed -> painting headline ->
# "It monitors [X]" slot machine -> compose input -> imessage thread ->
# typing dots burst into a black news scatter -> count-up bubble -> digest
# builds -> lock screen push -> "Lives where you already are" -> "No App /
# Just texts" -> avatar centers into the pixel wordmark -> end card with
# tagline cycle. two voices: mono = brand, inter = the phone.
import json
import math
import os

W, H = 1920, 1080
INK = "#1c1c1e"
GREY = "#8a9096"
LIME = "#bdf4a1"
LIME_FEED = "#8ab484"
BLUE = "#0d86f9"
BUBBLE = "#ededed"
K = 0.5523

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
scenes, tracks = [], []

IN_W = 0.5   # inter px per char per size unit
MO_W = 0.6   # mono


def text(id, s, x, y, size, color=INK, weight=400, family="inter", **kw):
    n = {"id": id, "type": "text", "text": s, "x": round(x, 1),
         "y": round(y, 1), "color": color,
         "font": {"size": size, "weight": weight, "family": family}}
    n.update(kw)
    return n


def ltext(id, s, left, y, size, color=INK, weight=400, family="inter"):
    f = MO_W if family == "mono" else IN_W
    return text(id, s, left + len(s) * size * f / 2, y, size, color,
                weight, family)


def rect(id, x, y, w, h, r, fill, **kw):
    n = {"id": id, "type": "rect", "x": round(x, 1), "y": round(y, 1),
         "w": round(w, 1), "h": round(h, 1), "radius": r, "fill": fill}
    n.update(kw)
    return n


def path(id, x, y, d, fill, stroke=None, **kw):
    n = {"id": id, "type": "path", "x": round(x, 1), "y": round(y, 1),
         "d": d, "fill": fill}
    if stroke:
        n["stroke"] = stroke
    n.update(kw)
    return n


def circle_d(r, cx=0, cy=0):
    k = r * K
    return (f"M{cx-r} {cy}C{cx-r} {cy-k} {cx-k} {cy-r} {cx} {cy-r}"
            f"C{cx+k} {cy-r} {cx+r} {cy-k} {cx+r} {cy}"
            f"C{cx+r} {cy+k} {cx+k} {cy+r} {cx} {cy+r}"
            f"C{cx-k} {cy+r} {cx-r} {cy+k} {cx-r} {cy}Z")


def heart_d(s=1.0):
    return (f"M0 {14*s}C{-16*s} 0 {-24*s} {-8*s} {-18*s} {-18*s}"
            f"C{-13*s} {-25*s} {-3*s} {-23*s} 0 {-14*s}"
            f"C{3*s} {-23*s} {13*s} {-25*s} {18*s} {-18*s}"
            f"C{24*s} {-8*s} {16*s} 0 0 {14*s}Z")


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


def scene(id, bg, dur, nodes, kind="fade", tdur=0.3):
    scenes.append({"id": id, "bg": bg, "dur": round(dur, 3),
                   "transition": {"kind": kind, "dur": tdur}, "nodes": nodes})


def avatar(prefix, x, y, r):
    """the green no-gesture avatar chip: lime circle, head, crossed arms."""
    return [
        path(f"{prefix}_bg", x, y, circle_d(r), LIME),
        path(f"{prefix}_hd", x, y - r * 0.38, circle_d(r * 0.2), "#ecc19c"),
        rect(f"{prefix}_a1", x, y + r * 0.16, r * 1.15, r * 0.26, r * 0.13,
             "#4a69c8", rot=38),
        rect(f"{prefix}_a2", x, y + r * 0.16, r * 1.15, r * 0.26, r * 0.13,
             "#4a69c8", rot=-38),
    ]


def rise_in(ids, at, dy=50, dur=0.3):
    for nid in ids:
        track(nid, at=at, opacity=[(0, 0), (0.18, 1)],
              y=[(0, dy), (dur, 0, "outCubic")])


def pop_in(ids, at, s0=0.7):
    for nid in ids:
        track(nid, at=at, opacity=[(0, 0), (0.1, 1)],
              scale=[(0, s0), (0.32, 1.0, {"spring": [0.6, 1]})])


# 1 --------------------------------------------------- dark doomscroll feed
n1 = [
    path("f_av1", 410, -30, circle_d(26), "#7a4fd0"),
    ltext("f_nm1", "rowy · @rowy · 2h", 470, -36, 24, GREY),
    ltext("f_b1a", "DEVS ARE COOKED! OpenAI just dropped GPT-5.4 with full",
          470, 6, 27, "#e7e9ea"),
    ltext("f_b1b", "autonomous coding. built a production app in 4 minutes.",
          470, 44, 27, "#e7e9ea"),
    ltext("f_e1", "342      1.2K      4.8K      127K", 470, 92, 22,
          "#71767b"),
    rect("f_sep1", 960, 140, 1200, 2, 1, "#2f3336"),

    path("f_av2", 410, 200, circle_d(26), "#2f8f5b"),
    ltext("f_nm2", "pieter.ship · @pietership · 4h", 470, 194, 24, GREY),
    ltext("f_b2a", "shipped 14 products with ai in 6 weeks. 11 failed.",
          470, 236, 27, "#e7e9ea"),
    ltext("f_b2b", "1 doing $40k/mo. stop learning frameworks. start shipping.",
          470, 274, 27, "#e7e9ea"),
    ltext("f_e2", "847      2.1K      8.4K      312K", 470, 322, 22,
          "#71767b"),
    rect("f_sep2", 960, 370, 1200, 2, 1, "#2f3336"),

    path("f_av3", 410, 430, circle_d(26), "#d0a02f"),
    ltext("f_nm3", "moon_chad · @moonchad · 5h", 470, 424, 24, GREY),
    ltext("f_b3a", "BITCOIN IS ABOUT TO EXPLODE", 470, 466, 27, "#e7e9ea",
          weight=600),
    rect("f_chart", 830, 560, 720, 130, 16, "#16181c"),
    rect("f_sep3", 960, 648, 1200, 2, 1, "#2f3336"),

    rect("f_nsav", 414, 712, 64, 64, 16, LIME_FEED),
    path("f_nshd", 414, 700, circle_d(11), "#ecc19c"),
    rect("f_nsa1", 414, 726, 38, 9, 4.5, "#4a69c8", rot=38),
    rect("f_nsa2", 414, 726, 38, 9, 4.5, "#4a69c8", rot=-38),
    ltext("f_nsnm", "noscroll", 470, 700, 28, "#e7e9ea", weight=700),
    path("f_badge", 620, 700, circle_d(13), "#f7c22d"),
    path("f_check", 620, 700, "M-5 0L-1 5L6 -5", None, stroke=2.4),
    ltext("f_nshdl", "@noscroll · 1m", 660, 702, 24, GREY),
    ltext("f_tw1", "There's more to life than scrolling the feeds.",
          470, 752, 30, "#ffffff"),
    ltext("f_tw2", "Look up from your phone.", 470, 796, 30, "#ffffff"),
    ltext("f_ens", "1.2K      347      2.8K      412K", 470, 846, 22,
          "#71767b"),
    rect("f_paint", 960, 1040, 1200, 300, 28, "#47818f",
         gradient={"angle": 100, "stops": [{"at": 0, "color": "#3d7488"},
                                           {"at": 1, "color": "#7fae8f"}]}),
]
next(n for n in n1 if n["id"] == "f_check")["fill"] = "#ffffff"
# candles inside the chart card
for i in range(14):
    up = i % 3 != 1
    n1.append(rect(f"f_c{i}", 520 + i * 46, 560 + (i % 4) * 6 - 9,
                   14, 46 + (i * 13) % 34, 3,
                   "#2ea36c" if up else "#d9503f"))
# feed auto-scroll: camera settles down onto the noscroll tweet
track("s1", cam_y=[(0, -300), (1.3, 0, "outCubic")])
for nid, at, cad in [("f_tw1", 1.5, 0.026), ("f_tw2", 2.5, 0.032)]:
    track(nid, opacity=[(0, 0), (at, 0), (at + 0.01, 1)])
    tracks.append({"target": nid, "at": at, "reveal": {
        "unit": "type", "cadence": cad, "dur": 0.06, "caret": "bar",
        "caret_typing": "hidden"}})
scene("s1", "#000000", 4.0, n1, kind="cut")

# 2 ------------------------------------------- painting + typed headline
n2 = [
    rect("p_sky", 960, 540, 1920, 1080, 0, "#7fb4c9",
         gradient={"angle": 90, "stops": [{"at": 0, "color": "#6aa7bf"},
                                          {"at": 1, "color": "#d9ecf0"}]}),
    path("p_m1", 700, 660, "M-420 220L0 -260L420 220Z", "#57879b"),
    path("p_m2", 1250, 690, "M-380 190L0 -220L380 190Z", "#6d9cae"),
    rect("p_sea", 960, 940, 1920, 420, 0, "#47818f"),
    rect("p_arl", 140, 540, 300, 1080, 0, "#c4b096"),
    rect("p_arr", 1780, 540, 300, 1080, 0, "#c4b096"),
    rect("p_art", 960, 40, 1920, 160, 0, "#c4b096"),
]
flow = [("#e8a0a8", 250, 300), ("#e9d27f", 200, 430), ("#7fa06a", 290, 380),
        ("#e8a0a8", 160, 560), ("#e9d27f", 260, 640), ("#7fa06a", 210, 720),
        ("#e8a0a8", 1690, 320), ("#e9d27f", 1760, 420), ("#7fa06a", 1710, 500),
        ("#e8a0a8", 1780, 600), ("#e9d27f", 1700, 690), ("#7fa06a", 1760, 780),
        ("#e8a0a8", 900, 30), ("#e9d27f", 1100, 60), ("#7fa06a", 700, 60)]
for i, (col, fx, fy) in enumerate(flow):
    n2.append(path(f"p_fl{i}", fx, fy, circle_d(26 + (i * 7) % 18), col))
n2 += [
    rect("p_ph_o", 960, 1010, 310, 640, 46, "#d9dcde"),
    rect("p_ph_i", 960, 1016, 282, 616, 38, "#101214"),
    rect("p_ph_l1", 960, 900, 190, 10, 5, "#3a3f45"),
    rect("p_ph_l2", 960, 930, 150, 10, 5, "#2c3036"),
    ltext("p_h1", "noscroll_ reads the feed", 220, 400, 62, "#ffffff",
          family="mono"),
    ltext("p_h2", "so you can live your life", 220, 500, 62, "#ffffff",
          family="mono"),
]
# camera continues the pull-back from the feed, then winds up before the cut
track("s2", cam_zoom=[(0, 1.5), (1.1, 1.0, "outCubic"), (2.95, 1.0),
                      (3.4, 1.14, "inCubic")])
for nid, at in [("p_h1", 0.35), ("p_h2", 1.55)]:
    track(nid, opacity=[(0, 0), (at, 0), (at + 0.01, 1)])
    tracks.append({"target": nid, "at": at, "reveal": {
        "unit": "type", "cadence": 0.042, "dur": 0.06, "caret": "block",
        "caret_typing": "hidden"}})
scene("s2", "#7fb4c9", 3.4, n2, kind="fade", tdur=0.5)

# 3 ------------------------------- "It monitors [X] so you don't have to"
MS = 52          # active sentence size
GS = 46          # ghost list size
COL = 540        # noun column left edge
T = [0.0, 1.15, 2.3, 3.45]
TOPICS = ["reality TV", "oil shipping", "AI news", "korean skincare",
          "SCOTUS opinions", "the situation", "prediction markets",
          "GPU rigs"]
n3 = [ltext("m_it", "It monitors", 160, 540, MS, INK, family="mono")]
for i, top in enumerate(TOPICS):
    n3.append(ltext(f"m_g{i}", top, COL, 540 + (i - 2) * 96, GS, "#b9bdc1",
                    family="mono"))
    yk = [(0, 0)]
    ok = []
    for k, tk in enumerate(T):
        a = 2 + k
        d = abs(i - a)
        v = 0.0 if d == 0 else (0.35 if d == 1 else (0.15 if d == 2 else 0.06))
        if k == 0:
            ok.append((0, v))
        else:
            yk += [(tk, -(k - 1) * 96), (tk + 0.35, -k * 96, "outCubic")]
            ok += [(tk, ok[-1][1]), (tk + 0.35, v)]
    track(f"m_g{i}", y=yk, opacity=ok)
NOUNS = ["AI news", "korean skincare", "SCOTUS opinions", "the situation"]
for k, noun in enumerate(NOUNS):
    line = noun + " so you don't have to"
    nid = f"m_a{k}"
    n3.append(ltext(nid, line, COL, 540, MS, INK, family="mono"))
    start = 0.0 if k == 0 else T[k] + 0.12
    end = (T[k + 1] + 0.2) if k < 3 else 99.0
    ok = [(0, 0), (start, 0), (start + 0.18, 1)]
    if end < 99:
        ok += [(end, 1), (end + 0.1, 0)]
    track(nid, opacity=ok, y=[(start, 14), (start + 0.3, 0, "outCubic")])
tracks.append({"target": "m_it", "reveal": {
    "unit": "word", "stagger": 0.06, "dur": 0.25, "rise": 20,
    "accent": INK}})
scene("s3", "#ffffff", 4.6, n3, kind="cut")

# 4 ----------------------------------------------------- compose close-up
n4 = [
    path("c_plus_c", 250, 540, circle_d(56), "#ececec"),
    path("c_plus_g", 250, 540, "M-24 0L24 0M0 -24L0 24", None, stroke=6.0),
    rect("c_pill_o", 1050, 540, 1360, 150, 75, "#e2e2e2"),
    rect("c_pill_i", 1050, 540, 1348, 138, 69, "#ffffff"),
    ltext("c_ph", "tell it what you care about", 480, 540, 40, "#9aa0a6"),
    ltext("c_typ", "crypto alpha. not the price. the real stuff", 480, 540,
          40, INK),
    path("c_send", 1620, 540, circle_d(46), BLUE),
    path("c_arr", 1620, 540, "M0 16L0 -16M-11 -5L0 -16L11 -5", None,
         stroke=6.0),
]
n4[1]["fill"] = "#8a8a8a"
n4[-1]["fill"] = "#ffffff"
track("c_ph", opacity=[(0, 0), (0.15, 0.6), (0.6, 0.6), (0.75, 0)])
track("c_typ", opacity=[(0, 0), (0.65, 0), (0.66, 1)])
tracks.append({"target": "c_typ", "at": 0.65, "reveal": {
    "unit": "type", "cadence": 0.034, "dur": 0.06, "caret": "bar",
    "caret_blink": 0.9}})
pop_in(["c_send", "c_arr"], 2.05)
scene("s4", "#ffffff", 3.0, n4, kind="fade", tdur=0.25)

# 5 --------------------------------------------------------- imessage thread
n5 = [
    rect("im_ph_o", 960, 590, 830, 1520, 116, "#c9ccd0"),
    rect("im_ph_i", 960, 590, 792, 1482, 100, "#ffffff"),
    path("im_chev", 640, 150, "M10 -18L-8 0L10 18", None, stroke=4.5),
    path("im_bdg", 700, 150, circle_d(24), "#3a3a3c"),
    text("im_bdg_t", "2", 700, 151, 26, "#ffffff", weight=600),
]
n5[2]["fill"] = "#8a8a8a"
n5 += avatar("im_av", 960, 140, 62)
n5 += [
    text("im_lbl", "noscroll ›", 960, 236, 30, INK, weight=600),
    rect("im_fc", 1268, 150, 44, 30, 9, "#c9ccd0"),
    path("im_fc_t", 1300, 150, "M0 -9L14 -16L14 16L0 9Z", "#c9ccd0"),

    rect("im_blue", 1130, 400, 560, 132, 40, "#38b9ff",
         gradient={"angle": 90, "stops": [{"at": 0, "color": "#3fbdff"},
                                          {"at": 1, "color": "#1f8ef7"}]}),
    ltext("im_bl1", "crypto alpha. not the price.", 880, 376, 30, "#ffffff"),
    ltext("im_bl2", "the real stuff.", 880, 424, 30, "#ffffff"),

    path("im_tb", 830, 322, circle_d(36), "#e4e4e6"),
    path("im_tb_d", 866, 362, circle_d(9), "#e4e4e6"),
    rect("im_th1", 826, 330, 22, 14, 5, "#f5c33b"),
    rect("im_th2", 838, 314, 9, 20, 4, "#f5c33b", rot=-30),

    rect("im_grey", 810, 660, 640, 216, 40, BUBBLE),
    ltext("im_g1", "say less. onchain moves,", 520, 590, 30, INK),
    ltext("im_g2", "governance, whale wallets,", 520, 636, 30, INK),
    ltext("im_g3", "exploits. i'll be your", 520, 682, 30, INK),
    ltext("im_g4", "research desk", 520, 728, 30, INK),

    rect("im_dots", 640, 920, 176, 92, 46, BUBBLE),
    path("im_dt1", 660, 990, circle_d(11), "#d8d8dc"),
    path("im_dt2", 636, 1014, circle_d(6), "#d8d8dc"),
]
for i in range(3):
    n5.append(path(f"im_d{i}", 600 + i * 40, 920, circle_d(11), "#b8bcc2"))
rise_in(["im_blue", "im_bl1", "im_bl2"], 0.25, dy=70)
pop_in(["im_tb", "im_tb_d", "im_th1", "im_th2"], 1.25)
rise_in(["im_grey", "im_g1", "im_g2", "im_g3", "im_g4"], 1.7, dy=60)
for nid in ["im_dots", "im_dt1", "im_dt2"]:
    track(nid, at=2.8, opacity=[(0, 0), (0.12, 1)],
          scale=[(0, 0.6), (0.3, 1.0, {"spring": [0.6, 1]})])
for i in range(3):
    track(f"im_d{i}", at=2.95, opacity=[(0, 0), (0.05, 1)])
    track(f"im_d{i}", at=3.0 + i * 0.13, loop=True,
          y=[(0, 0), (0.2, -12, "outCubic"), (0.42, 0, "inOutCubic"),
             (0.95, 0)])
# wind-up: camera dives onto the typing dots, then zoom-cut to the scatter
track("s5", cam_zoom=[(0, 1.0), (3.95, 1.0), (4.4, 1.7, "inCubic")],
      cam_x=[(0, 0), (3.95, 0), (4.4, -132, "inCubic")],
      cam_y=[(0, 0), (3.95, 0), (4.4, 157, "inCubic")])
scene("s5", "#ffffff", 4.4, n5, kind="rise", tdur=0.4)

# 6 ----------------------------------------------- black news card scatter
CARDS = [
    ("sc_a", 1150, 240, 470, 210, -4,
     ["SEC charges exec in $16M crypto", "fraud over 'insured' token scheme"],
     "#26292c", 22, 600),
    ("sc_b", 300, 170, 330, 150, 3,
     ["MARKET SENTIMENT", "Fear & Greed Index: 26 (Fear)"], "#26292c", 20, 0),
    ("sc_c", 1660, 200, 380, 210, -2,
     ["Weekly ETF Flows", "BlackRock IBIT", "Morgan Stanley MSBT",
      "Fidelity FBTC"], "#26292c", 19, 0),
    ("sc_d", 560, 520, 450, 150, 2,
     ["Arkham Intel", "Strategy wallet just moved", "13,927 BTC ($1.02B)"],
     "#26292c", 20, 0),
    ("sc_e", 1560, 590, 440, 190, 3,
     ["r/cryptocurrency", "Saylor bought another", "13,927 BTC"],
     "#26292c", 20, 0),
    ("sc_f", 1040, 800, 430, 160, -3,
     ["The cheapest bitcoin ETF yet:", "Morgan Stanley uses 0.14% fee"],
     "#26292c", 20, 700),
    ("sc_g", 330, 850, 360, 200, -2,
     ["coindesk", "Bitcoin, Ethereum approach", "two-month highs"],
     "#26292c", 20, 0),
    ("sc_h", 830, 90, 420, 140, 2,
     ["Ether-bitcoin ratio bounces", "from 2026 lows"], "#26292c", 20, 0),
]
n6 = []
for ci, (cid, cx, cy, cw, ch, rot, lines, ink, fs, coin) in enumerate(CARDS):
    ids = [cid]
    n6.append(rect(cid, cx, cy, cw, ch, 18, "#f7f7f5", rot=rot))
    top = cy - (len(lines) - 1) * (fs + 12) / 2
    for li, ln in enumerate(lines):
        tid = f"{cid}_l{li}"
        col = "#c8452e" if ln == "MARKET SENTIMENT" else \
              ("#e0762f" if ln == "r/cryptocurrency" else ink)
        wgt = 700 if li == 0 and len(lines) > 2 else 500
        n6.append(text(tid, ln, cx, top + li * (fs + 12), fs, col,
                       weight=wgt, rot=rot))
        ids.append(tid)
    if coin:
        gid = f"{cid}_coin"
        n6.append(path(gid, coin, cy + ch / 2 - 34, circle_d(26), "#e2a72e",
                       rot=rot))
        ids.append(gid)
    s0 = 0.05 + ci * 0.07
    for nid in ids:
        nn = next(x for x in n6 if x["id"] == nid)
        track(nid,
              opacity=[(0, 0), (s0, 0), (s0 + 0.1, 1), (2.5, 1), (2.85, 0)],
              scale=[(s0, 1.45), (s0 + 0.3, 1.0, "outCubic"), (2.25, 1.0),
                     (2.85, 0.2, "inCubic")],
              x=[(2.25, 0), (2.85, round((960 - nn["x"]) * 0.85, 1),
                  "inCubic")],
              y=[(0, 26), (s0 + 0.45, 0, "outCubic"), (2.25, 0),
                 (2.85, round((560 - nn["y"]) * 0.85, 1), "inCubic")])
scene("s6", "#000000", 3.0, n6, kind="zoom", tdur=0.35)

# 7 ------------------------------------------------- the count-up bubble
n7 = [
    rect("ct_bub", 760, 560, 900, 230, 60, BUBBLE),
    path("ct_t1", 340, 660, circle_d(26), BUBBLE),
    path("ct_t2", 300, 700, circle_d(12), BUBBLE),
    path("ct_tb", 1240, 430, circle_d(52), BLUE),
    path("ct_tbd", 1292, 486, circle_d(12), BLUE),
    text("ct_ex", "!!", 1240, 432, 44, "#ffb3af", weight=800),
    ltext("ct_txt", "sources scrolled.", 520, 510, 44, INK),
    ltext("ct_l2", "3 things worth your time.", 400, 590, 44, INK),
]
NUMS = ["94", "125", "167", "199", "214"]
SW = [0.54, 0.89, 1.24, 1.59]
for i, num in enumerate(NUMS):
    nid = f"ct_n{i}"
    n7.append(text(nid, num, 450, 510, 44, INK, weight=600))
    start = 0.3 if i == 0 else SW[i - 1]
    ok = [(0, 0), (start, 0), (start + 0.08, 1)]
    yk = [(start, 12 if i else 0), (start + 0.12, 0, "outCubic")]
    if i < 4:
        ok += [(SW[i], 1), (SW[i] + 0.08, 0)]
        yk += [(SW[i], 0), (SW[i] + 0.08, -12, "outCubic")]
    track(nid, opacity=ok, y=yk)
for nid in ["ct_bub", "ct_t1", "ct_t2", "ct_txt"]:
    track(nid, at=0.1, opacity=[(0, 0), (0.15, 1)],
          scale=[(0, 0.92), (0.3, 1.0, "outCubic")])
track("ct_l2", opacity=[(0, 0), (0.4, 0), (0.55, 1)],
      y=[(0.4, 14), (0.65, 0, "outCubic")])
pop_in(["ct_tb", "ct_tbd", "ct_ex"], 1.75)
scene("s7", "#ffffff", 2.4, n7, kind="fade", tdur=0.3)

# 8 -------------------------------------------------------- digest builds
n8 = [
    rect("dg_ph_o", 960, 590, 830, 1520, 116, "#c9ccd0"),
    rect("dg_ph_i", 960, 590, 792, 1482, 100, "#ffffff"),
    rect("dg_isl", 960, 90, 240, 64, 32, "#111111"),
    text("dg_clk", "9:41", 700, 90, 30, INK, weight=600),
]
n8 += avatar("dg_av", 960, 230, 56)
n8.append(text("dg_lbl", "noscroll ›", 960, 318, 28, INK, weight=600))


def bubble(prefix, cx, cy, w, lines, size=26, y0=None):
    lh = size + 12
    h = len(lines) * lh + 46
    out = [rect(prefix, cx, cy, w, h, 34, BUBBLE)]
    top = cy - (len(lines) - 1) * lh / 2
    left = cx - w / 2 + 34
    for i, ln in enumerate(lines):
        out.append(ltext(f"{prefix}_l{i}", ln, left, top + i * lh, size))
    return out


b1 = bubble("dg_b1", 810, 440, 620, ["214 sources scrolled.",
                                     "3 things worth your time."])
b2 = bubble("dg_b2", 810, 630, 620, ["aave just took a hit. kelp's",
                                     "bridge was exploited for $292m,",
                                     "used to borrow ~$190m on aave"])
b3 = bubble("dg_b3", 810, 820, 620, ["morgan stanley's bitcoin ETF",
                                     "pulled $100M in week one."])
b4 = bubble("dg_b4", 810, 1000, 620, ["goldman sachs just filed for a",
                                      "bitcoin ETF. the TradFi",
                                      "floodgates are officially open."])
n8 += b1 + b2 + b3 + b4
n8 += [path("dg_hb", 1150, 230, circle_d(40), BLUE),
       path("dg_hbd", 1190, 274, circle_d(10), BLUE),
       path("dg_heart", 1150, 232, heart_d(1.1), "#ff5b9f")]
for grp, at in [(b1, 0.3), (b2, 1.2), (b3, 2.1), (b4, 3.0)]:
    rise_in([n["id"] for n in grp], at, dy=50)
pop_in(["dg_hb", "dg_hbd", "dg_heart"], 3.6)
scene("s8", "#ffffff", 4.2, n8, kind="rise", tdur=0.4)

# 9 ---------------------------------------------------- lock-screen push
n9 = [
    rect("lk_ph_o", 960, 540, 900, 1500, 120, "#d0d3d6"),
    rect("lk_wall", 960, 540, 860, 1460, 106, "#8fa88a",
         gradient={"angle": 115, "stops": [{"at": 0, "color": "#7f9c7c"},
                                           {"at": 1, "color": "#c9d8bf"}]}),
    rect("lk_bl1", 760, 300, 300, 220, 110, "#68855f", blur=48),
    rect("lk_bl2", 1180, 760, 340, 260, 130, "#5c7a58", blur=54),
    rect("lk_bl3", 820, 920, 260, 200, 100, "#7d9a6e", blur=44),

    rect("lk_ban", 960, 460, 760, 190, 44, "#f4f6f2"),
    rect("lk_tile", 680, 460, 92, 92, 24, LIME),
    path("lk_hd", 680, 440, circle_d(13), "#ecc19c"),
    rect("lk_a1", 680, 476, 50, 12, 6, "#4a69c8", rot=38),
    rect("lk_a2", 680, 476, 50, 12, 6, "#4a69c8", rot=-38),
    ltext("lk_nm", "noscroll", 750, 412, 30, INK, weight=700),
    text("lk_tm", "9:41 AM", 1240, 412, 24, GREY),
    ltext("lk_t1", "Saylor just bought 13,927 more BTC.", 750, 462, 27, INK),
    ltext("lk_t2", "guy is not slowing down.", 750, 502, 27, INK),

    path("lk_fl", 700, 1000, circle_d(54), "#e8ebe6"),
    path("lk_cam", 1220, 1000, circle_d(54), "#e8ebe6"),
    rect("lk_fli", 700, 1000, 16, 34, 5, "#3c4a38"),
    rect("lk_cami", 1220, 1000, 34, 26, 8, "#3c4a38"),
    rect("lk_home", 960, 1046, 260, 10, 5, "#f0f2ee"),
]
for nid in ["lk_ban", "lk_tile", "lk_hd", "lk_a1", "lk_a2", "lk_nm",
            "lk_tm", "lk_t1", "lk_t2"]:
    track(nid, at=0.25, opacity=[(0, 0), (0.18, 1)],
          y=[(0, -90), (0.4, 0, "outCubic")])
scene("s9", "#f2f4ef", 2.0, n9, kind="rise", tdur=0.4)

# 10 ------------------------------------------ "Lives where you already are"
n10 = [
    rect("lv_bg", 960, 540, 1920, 1080, 0, "#e0e9d6",
         gradient={"angle": 120, "stops": [{"at": 0, "color": "#e6eeda"},
                                           {"at": 1, "color": "#d2e0cd"}]}),
    rect("lv_bub", 960, 560, 1000, 170, 52, "#ffffff"),
    path("lv_tl", 490, 640, circle_d(24), "#ffffff"),
    ltext("lv_txt", "Lives where you already are", 540, 548, 44, INK),
    text("lv_tm", "10:15 AM", 1320, 612, 22, GREY),
]
n10 += avatar("lv_av", 1420, 300, 56)
n10 += [
    text("lv_lbl", "noscroll", 1420, 392, 26, INK, weight=600),
    path("lv_hb", 1500, 460, circle_d(44), BLUE),
    path("lv_hbd", 1544, 508, circle_d(10), BLUE),
    path("lv_heart", 1500, 462, heart_d(1.2), "#ff5b9f"),
]
for nid in ["lv_bub", "lv_tl", "lv_txt", "lv_tm"]:
    track(nid, at=0.15, opacity=[(0, 0), (0.15, 1)],
          scale=[(0, 0.92), (0.32, 1.0, "outCubic")])
for nid in ["lv_av_bg", "lv_av_hd", "lv_av_a1", "lv_av_a2", "lv_lbl"]:
    track(nid, at=1.15, opacity=[(0, 0), (0.2, 1)],
          y=[(0, 18), (0.3, 0, "outCubic")])
pop_in(["lv_hb", "lv_hbd", "lv_heart"], 1.55)
scene("s10", "#e0e9d6", 2.4, n10, kind="cut")

# 11 ------------------------------------------------- "No App / Just texts"
n11 = [rect("na_edge", 575, 540, 34, 1400, 16, "#d0d3d6")]
n11 += avatar("na_av", 1560, 160, 70)
n11 += [
    text("na_lbl", "noscroll ›", 1560, 272, 34, INK, weight=600),
    rect("na_b1", 880, 480, 340, 130, 46, BUBBLE),
    text("na_b1t", "No App", 880, 482, 42, INK),
    rect("na_b2", 930, 660, 440, 130, 46, BUBBLE),
    text("na_b2t", "Just texts", 930, 662, 42, INK),
    path("na_hb", 1090, 370, circle_d(56), BLUE),
    path("na_hbd", 1150, 432, circle_d(13), BLUE),
    path("na_heart", 1090, 372, heart_d(1.5), "#ff5b9f"),
]
rise_in(["na_b1", "na_b1t"], 0.3, dy=50)
rise_in(["na_b2", "na_b2t"], 0.7, dy=50)
pop_in(["na_hb", "na_hbd", "na_heart"], 1.15)
scene("s11", "#ffffff", 2.2, n11, kind="fade", tdur=0.3)

# 12 ------------------------------------------ avatar centers -> wordmark
n12 = avatar("wm_av", 960, 360, 74)
n12.append(text("wm_mark", "noscroll", 960, 560, 110, "#111111",
                family="mono"))
for nid in ["wm_av_bg", "wm_av_hd", "wm_av_a1", "wm_av_a2"]:
    track(nid, scale=[(0, 1.9), (0.5, 1.0, "outCubic")],
          y=[(0, -70), (0.5, 0, "outCubic")],
          opacity=[(0, 0), (0.12, 1)])
track("wm_mark", opacity=[(0, 0), (0.5, 0), (0.51, 1)])
tracks.append({"target": "wm_mark", "at": 0.5, "reveal": {
    "unit": "type", "cadence": 0.07, "dur": 0.06, "caret": "block",
    "caret_typing": "solid"}})
scene("s12", "#ffffff", 1.8, n12, kind="fade", tdur=0.3)

# 13 --------------------------------------------------------- end card
n13 = avatar("ec_av", 960, 290, 80)
n13 += [
    text("ec_mark", "noscroll", 960, 500, 150, "#111111", family="mono"),
    text("ec_caret", "_", 1360, 520, 150, "#111111", family="mono"),
    rect("ec_pill_o", 960, 730, 740, 112, 56, "#e2e2e2"),
    rect("ec_pill_i", 960, 730, 730, 102, 51, "#ffffff"),
    ltext("ec_t1", "doomscrolls so you don't have to", 640, 730, 34,
          INK),
    ltext("ec_t2", "text the agent today for free!", 640, 730, 34, INK),
    path("ec_send", 1250, 730, circle_d(36), BLUE),
    path("ec_arr", 1250, 730, "M0 13L0 -13M-9 -4L0 -13L9 -4", None,
         stroke=5.0),
    rect("ec_url", 960, 960, 310, 78, 39, "#d7f2bf"),
    text("ec_url_t", "noscroll.com", 960, 962, 28, "#2e5a1f", weight=600),
]
n13[-3]["fill"] = "#ffffff"
track("ec_caret", loop=True, at=0.2,
      opacity=[(0, 1), (0.499, 1), (0.5, 0), (0.999, 0), (1.0, 1)])
track("ec_t1", opacity=[(0, 0), (0.45, 0), (0.46, 1), (2.0, 1), (2.1, 0)])
tracks.append({"target": "ec_t1", "at": 0.45, "reveal": {
    "unit": "type", "cadence": 0.03, "dur": 0.05, "caret": "bar",
    "caret_typing": "hidden"}})
track("ec_t2", opacity=[(0, 0), (2.25, 0), (2.26, 1)])
tracks.append({"target": "ec_t2", "at": 2.25, "reveal": {
    "unit": "type", "cadence": 0.035, "dur": 0.05, "caret": "bar",
    "caret_blink": 0.9}})
for nid in ["ec_url", "ec_url_t"]:
    track(nid, at=0.8, opacity=[(0, 0), (0.2, 1)],
          y=[(0, 20), (0.3, 0, "outCubic")])
scene("s13", "#ffffff", 4.4, n13, kind="fade", tdur=0.3)

stage = {"fps": 30, "size": [W, H], "scenes": scenes,
         "audio": {"src": "/assets/audio/pad.m4a", "gain": 0.6,
                   "fade_out": 0.8}}
with open("docs/noscroll.stage.json", "w") as f:
    json.dump(stage, f, indent=1)
with open("docs/noscroll.anim.json", "w") as f:
    json.dump({"tracks": tracks}, f, indent=1)
total = sum(s["dur"] for s in scenes)
print("wrote docs/noscroll.{stage,anim}.json,",
      sum(len(s["nodes"]) for s in scenes), "nodes,", len(tracks),
      f"tracks, {total:.2f}s")
