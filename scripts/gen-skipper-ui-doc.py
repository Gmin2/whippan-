#!/usr/bin/env python3
# reproduction of radio/skipper-ui.mp4 (21.37s, 3840x2160 -> 1920x1080):
# the skiper-ui launch. black title beats (grid intro, typed headline),
# a frenetic product-shot montage (gallery, spec sheet, wireframe, code,
# dock, serif typo, fluid badge, hands), the "beyond default shadcn/ui"
# mantra, a browser rise, the 3d demo card with red display words and the
# 72+ components card, the command mantra type/backspace/retype, a second
# even faster montage of component demos, and the gallery end card.
# real screens are drawn stand-ins; every cut lands on the measured grid.
import json
import os

W, H = 1920, 1080
INK = "#161616"
RED = "#e92241"
PINK = "#e33c67"
DK = "#292929"
K = 0.5523

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
scenes, tracks = [], []


def text(id, s, x, y, size, color="#ffffff", weight=500, family=None):
    n = {"id": id, "type": "text", "text": s, "x": x, "y": y,
         "color": color, "font": {"size": size, "weight": weight}}
    if family:
        n["font"]["family"] = family
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


def circle_d(r, cx=0, cy=0, ccw=False):
    k = r * K
    if not ccw:
        return (f"M{cx-r} {cy}C{cx-r} {cy-k} {cx-k} {cy-r} {cx} {cy-r}"
                f"C{cx+k} {cy-r} {cx+r} {cy-k} {cx+r} {cy}"
                f"C{cx+r} {cy+k} {cx+k} {cy+r} {cx} {cy+r}"
                f"C{cx-k} {cy+r} {cx-r} {cy+k} {cx-r} {cy}Z")
    return (f"M{cx-r} {cy}C{cx-r} {cy+k} {cx-k} {cy+r} {cx} {cy+r}"
            f"C{cx+k} {cy+r} {cx+r} {cy+k} {cx+r} {cy}"
            f"C{cx+r} {cy-k} {cx+k} {cy-r} {cx} {cy-r}"
            f"C{cx-k} {cy-r} {cx-r} {cy-k} {cx-r} {cy}Z")


SPHERE_GRAD = {"angle": 45, "stops": [
    {"at": 0.0, "color": "#0f0f0f"},
    {"at": 0.35, "color": "#12327a"},
    {"at": 1.0, "color": "#27c9f6"}]}


def sphere(id, x, y, r):
    return rect(id, x, y, 2 * r, 2 * r, r, "#1a52b0", gradient=SPHERE_GRAD)


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


def show(nid, at, dur=0.12, rise=0):
    if rise:
        track(nid, at=at, opacity=[(0, 0), (dur, 1)],
              y=[(0, rise), (dur + 0.08, 0, "outCubic")])
    else:
        track(nid, at=at, opacity=[(0, 0), (dur, 1)])


def swap(nid, t_on, t_off=None):
    """hard visibility window."""
    keys = [(0, 0), (t_on, 0), (t_on + 0.001, 1)]
    if t_off is not None:
        keys += [(t_off, 1), (t_off + 0.001, 0)]
    track(nid, opacity=keys)


def scene(id, bg, dur, nodes):
    scenes.append({"id": id, "bg": bg, "dur": round(dur, 3),
                   "transition": {"kind": "cut"}, "nodes": nodes})


# ---------------------------------------------------------------- builders
def gallery(p):
    """the white component gallery still (scenes 3 and 16)."""
    n = []
    # backing cards, clockwise from top-left
    n.append(rect(p + "c1b", 398, 250, 505, 330, 16, "#f7f6f2"))
    n.append(rect(p + "c1", 398, 248, 470, 262, 12, "#0d0d0d"))
    n.append(text(p + "c1t", "Vercel's one-day", 285, 305, 17, "#cfcfcf", 500))
    n.append(text(p + "c1u", "event for developers", 302, 328, 17, "#cfcfcf"))
    n.append(text(p + "c1l", "Vercel Liquid simulation", 275, 405, 16,
                  "#5a5a5a"))
    n.append(rect(p + "c2b", 1740, 175, 430, 130, 14, "#f7f6f2"))
    n.append(rect(p + "c2", 1718, 90, 390, 215, 12, "#ef1660"))
    n.append(text(p + "c2l", "Drawing cursor effect", 1636, 233, 17,
                  "#3c3c3c"))
    n.append(rect(p + "c3", 195, 682, 400, 335, 14, "#fdfdfc"))
    n.append(path(p + "c3g", 160, 655, circle_d(26), "#8bd968"))
    n.append(rect(p + "c3p", 115, 715, 52, 52, 8, "#9fe8dd"))
    n.append(text(p + "c3l", "cursor trail", 48, 818, 16, "#5a5a5a"))
    n.append(rect(p + "c4", 1644, 610, 494, 345, 14, "#fdfdfc"))
    n.append(rect(p + "c4t", 1656, 604, 175, 32, 16, "#2e2e2e"))
    n.append(rect(p + "c4s", 1600, 563, 76, 24, 12, "#1d1d1d"))
    n.append(text(p + "c4l", "Vercel Tooltip", 1487, 752, 17, "#3c3c3c"))
    n.append(rect(p + "c5", 398, 1030, 470, 170, 12, "#141414"))
    n.append(rect(p + "c5r", 400, 1075, 170, 90, 4, RED))
    n.append(rect(p + "c5w", 230, 1035, 90, 110, 4, "#e8e8e8"))
    n.append(rect(p + "c6", 1493, 1010, 500, 220, 14, "#fdfdfc"))
    # center tile + pill
    n.append(rect(p + "tile", 960, 531, 400, 400, 84, "#f2f2ec"))
    n.append(sphere(p + "sph", 959, 529, 98))
    n.append(rect(p + "pill", 1131, 345, 190, 62, 31, "#141414"))
    n.append(text(p + "pillt", "Skiper-UI", 1131, 345, 27, "#ffffff", 600))
    return n


def spec_nodes(p):
    n = [sphere(p + "sph", 960, 540, 96)]
    for y in (432, 580):
        n.append(rect(p + f"h{y}", 960, y, 1920, 1, 0, "#3a3a3a"))
    for x in (845, 1035):
        n.append(rect(p + f"v{x}", x, 540, 1, 1080, 0, "#3a3a3a"))
    n.append(text(p + "l1", "30PX", 956, 330, 15, "#888888"))
    n.append(text(p + "l2", "30PX", 745, 542, 15, "#888888"))
    n.append(text(p + "l3", "30PX", 1176, 542, 15, "#888888"))
    n.append(text(p + "l4", "30PX", 956, 758, 15, "#888888"))
    return n


def fluid_badge(p):
    curtain = ("M-215 -540L130 -540"
               "C255 -160 660 130 960 260L960 540L-960 540L-960 260"
               "C-660 130 -260 -160 -215 -540Z")
    n = [
        path(p + "cur", 960, 540, curtain, "#16f4f9"),
        rect(p + "fl1", 620, 960, 900, 320, 160, "#2a9ded", blur=70,
             opacity=0.75),
        rect(p + "fl2", 1450, 1010, 900, 300, 150, "#1c62c9", blur=80,
             opacity=0.6),
        path(p + "ring1", 958, 538, circle_d(214), "#ffffff", stroke=3.0),
        path(p + "ring2", 958, 538, circle_d(186), "#ffffff", stroke=2.5),
        sphere(p + "sph", 958, 538, 100),
        text(p + "bt", "S K I P E R P R O", 958, 425, 19, "#ffffff", 600),
    ]
    return n


# 1 ------------------------------------------------------------ grid intro
n1 = [
    rect("g_v1", 693, 540, 2, 1080, 0, "#e8e8e8"),
    rect("g_v2", 1225, 540, 2, 1080, 0, "#d0d0d0"),
    rect("g_h1", 960, 477, 1920, 2, 0, "#dcdcdc"),
    rect("g_h2", 960, 598, 1920, 2, 0, "#c4c4c4"),
    text("g_t", "Skiper-UI", 960, 538, 50, "#ffffff", 500),
]
track("g_v1", x=[(0, 260), (1.3, 0, "outCubic")],
      h=[(0, 640), (1.2, 1080, "outCubic")])
track("g_v2", x=[(0, -120), (1.4, 0, "outCubic")],
      h=[(0, 780), (1.3, 1080, "outCubic")])
track("g_h1", x=[(0, -180), (1.3, 0, "outCubic")],
      w=[(0, 1150), (1.2, 1920, "outCubic")])
track("g_h2", x=[(0, 240), (1.4, 0, "outCubic")],
      w=[(0, 1400), (1.3, 1920, "outCubic")])
track("g_t", opacity=[(0.55, 0), (0.9, 1)])
scene("s1", "#000000", 1.73, n1)

# 2 ------------------------------------------------------- headline typing
n2 = [text("hl", "A whole new era of UI components", 960, 540, 54,
           "#f2f2f2", 500)]
tracks.append({"target": "hl", "at": 0.02, "reveal": {
    "unit": "type", "cadence": 0.019, "cadence_end": 0.032, "dur": 0.05}})
scene("s2", "#000000", 0.94, n2)

# 3 ------------------------------------------------------------ gallery
scene("s3", "#ffffff", 0.40, gallery("ga_"))

# 4 ---------------------------------------------------------- spec sheet
scene("s4", "#1c1c1c", 0.23, spec_nodes("sp_"))

# 5 ----------------------------------------------------------- wireframe
n5 = [
    path("wf_p1", 330, 520, "M-370 -215L330 -215C352 -215 370 -197 370 -175"
         "L370 130C370 152 352 170 330 170L-370 170", "#b8b8b8",
         stroke=2.0),
    path("wf_p2", 1390, 530, "M-530 -160C-530 -182 -512 -200 -490 -200"
         "L530 -200L530 165L-490 165C-512 165 -530 147 -530 125Z",
         "#b8b8b8", stroke=2.0),
    path("wf_p3", 1450, 830, "M-470 -95C-470 -117 -452 -135 -430 -135"
         "L470 -135L470 100L-470 100Z", "#b8b8b8", stroke=2.0),
    path("wf_d1", 188, 495, circle_d(30), "#f2595e"),
    path("wf_d2", 341, 495, circle_d(30), "#f8c43d"),
    path("wf_d3", 488, 495, circle_d(30), "#40e54b"),
    sphere("wf_sph", 921, 528, 94),
    text("wf_t", "Skiper-UI", 1365, 530, 88, "#111111", 600),
]
scene("s5", "#ebebeb", 0.17, n5)

# 6 --------------------------------------------------------- code editor
CODE = [
    "  useMotionValue,",
    "  useScroll,",
    "  useTransform,",
    '} from "framer-motion";',
    "",
    'import React, { useEffect, useMemo, useRef, useState } from "react";',
    'import useMeasure from "react-use-measure";',
    "",
    'import { cn } from "@/lib/utils";',
    "",
    "// Sample content for each section",
    "const sectionContent = [",
    '  { title: "Who we are", code: `const home = "Welcome";` },',
    '  { title: "What we do", code: `const about = "Our Story";` },',
    '  { title: "How we do it", showCard: true },',
    '  { title: "Our projects", code: `const portfolio = projects.map();` },',
    '  { title: "Our team", code: `const team = members.join();` },',
    '  { title: "Pricing", code: `const pricing = plans.reduce();` },',
]
n6 = []
for i, line in enumerate(CODE):
    if line:
        n6.append({"id": f"cd_l{i}", "type": "text", "text": line,
                   "x": 640, "y": 60 + i * 58, "color": "#585858",
                   "font": {"size": 24, "weight": 400, "family": "mono"}})
n6.append(sphere("cd_sph", 1000, 560, 100))
scene("s6", "#1c1c1c", 0.16, n6)

# 7 ------------------------------------------------------------ dock zoom
n7 = [
    rect("dk_fl", 1520, 900, 1100, 420, 200, "#1b74d8", blur=90,
         opacity=0.7),
    rect("dk_fl2", 1750, 560, 700, 300, 150, "#25c4f5", blur=80,
         opacity=0.5),
    rect("dk_bar", 585, 525, 1230, 500, 60, "#2d2d2d"),
    rect("dk_t1", 105, 530, 260, 260, 56, "#c9c9c9"),
    path("dk_gear", 105, 530, circle_d(88) + circle_d(40, ccw=True),
         "#8f8f8f"),
    rect("dk_t2", 505, 530, 205, 205, 48, "#181818"),
    rect("dk_f1", 487, 468, 42, 42, 12, "#f24e1e"),
    rect("dk_f2", 530, 468, 42, 42, 21, "#ff7262"),
    rect("dk_f3", 487, 512, 42, 42, 21, "#a259ff"),
    path("dk_f4", 551, 533, circle_d(21), "#1abcfe"),
    path("dk_f5", 508, 576, circle_d(21), "#0acf83"),
    rect("dk_t3", 960, 530, 205, 205, 48, "#101010"),
    sphere("dk_sph", 960, 530, 66),
]
scene("s7", "#141414", 0.14, n7)

# 8 ----------------------------------------------------- serif typography
n8 = [
    text("sf_a", "SKIPE", 760, 240, 330, "#3a3a3a", 300),
    text("sf_b", "PRD", 900, 800, 330, "#333333", 300),
    rect("sf_fl", 960, 1010, 1500, 260, 130, "#1b74d8", blur=85,
         opacity=0.8),
    rect("sf_fl2", 620, 920, 700, 200, 100, "#25c4f5", blur=70,
         opacity=0.5),
    sphere("sf_sph", 945, 540, 52),
]
scene("s8", "#1f1f1f", 0.20, n8)

# 9 ----------------------------------------------------------- fluid badge
scene("s9", "#000000", 0.36, fluid_badge("fb_"))

# 10 --------------------------------------------------------------- hands
n10 = [
    rect("hd_l1", 220, 745, 940, 215, 107, "#9a9a9a", rot=-14, blur=5,
         gradient={"angle": 0, "stops": [{"at": 0, "color": "#232323"},
                                         {"at": 1, "color": "#cfcfcf"}]}),
    rect("hd_l2", 745, 800, 260, 56, 28, "#efefef", rot=-16, blur=3),
    rect("hd_l3", 620, 905, 56, 140, 28, "#e6e6e6", rot=-10, blur=3),
    rect("hd_l4", 700, 912, 52, 130, 26, "#dddddd", rot=-4, blur=3),
    rect("hd_r1", 1700, 480, 940, 210, 105, "#9a9a9a", rot=-12, blur=5,
         gradient={"angle": 180, "stops": [{"at": 0, "color": "#232323"},
                                           {"at": 1, "color": "#dfdfdf"}]}),
    rect("hd_r2", 1215, 420, 260, 54, 27, "#f2f2f2", rot=-22, blur=3),
    rect("hd_r3", 1330, 610, 54, 140, 27, "#e3e3e3", rot=18, blur=3),
    rect("hd_r4", 1405, 630, 50, 130, 25, "#d8d8d8", rot=10, blur=3),
    path("hd_ring1", 960, 540, circle_d(102), "#cfcfcf", stroke=2.5),
    path("hd_ring2", 960, 540, circle_d(86), "#cfcfcf", stroke=2.0),
    sphere("hd_sph", 960, 540, 50),
    text("hd_bt", "S K I P E R P R O", 960, 483, 11, "#cfcfcf", 600),
]
track("hd_l1", x=[(0, -30), (0.7, 0, "outCubic")])
track("hd_l2", x=[(0, -30), (0.7, 0, "outCubic")])
track("hd_r1", x=[(0, 30), (0.7, 0, "outCubic")])
track("hd_r2", x=[(0, 30), (0.7, 0, "outCubic")])
scene("s10", "#000000", 0.70, n10)

# 11 ------------------------------------------------------- beyond typing
n11 = [
    text("by1", "beyond", 960, 540, 60, "#f2f2f2", 500),
    text("by2", "beyond default", 960, 540, 60, "#f2f2f2", 500),
    text("by3", "beyond default shadcn/ui", 960, 540, 60, "#f2f2f2", 500),
]
swap("by1", 0.0, 0.55)
swap("by2", 0.55, 1.05)
swap("by3", 1.05)
scene("s11", "#000000", 1.50, n11)

# 12 -------------------------------------------------------- browser rise
n12 = [
    rect("br_wc2", 990, 155, 1160, 380, 26, "#2a2a2a"),
    rect("br_wc", 960, 185, 1150, 400, 26, "#ffffff"),
    text("br_wt1", "MOVE YOUR", 960, 200, 12, "#9a9a9a"),
    text("br_wt2", "MOUSE TO SEE", 960, 217, 12, "#9a9a9a"),
    text("br_wt3", "THE TRAIL", 960, 234, 12, "#9a9a9a"),
    rect("br_body", 960, 990, 1730, 1060, 22, "#333333"),
    rect("br_tab", 630, 500, 930, 82, 26, "#3f3f3f"),
    path("br_d1", 200, 497, circle_d(15), "#f2595e"),
    path("br_d2", 258, 497, circle_d(15), "#f8c43d"),
    path("br_d3", 316, 497, circle_d(15), "#40e54b"),
    sphere("br_fav", 442, 497, 15),
    text("br_tabt", "Skiper UI — Crazy Componen...", 740, 497, 26,
         "#f0f0f0", 500),
    text("br_x", "x", 1045, 495, 26, "#cccccc"),
    text("br_plus", "+", 1152, 495, 34, "#cccccc"),
    rect("br_sb", 1160, 618, 1500, 74, 37, "#4a4a4a"),
    text("br_g", "G", 540, 617, 30, "#ffffff", 700),
    text("br_st", "Search Google or type a URL", 890, 618, 28, "#e2e2e2"),
    text("br_bk", "<-", 200, 617, 30, "#cfcfcf"),
    text("br_fw", "->", 300, 617, 30, "#8a8a8a"),
    path("br_tri", 235, 782, "M0 -22L24 20L-24 20Z", "#ffffff"),
    text("br_slash1", "/", 330, 782, 30, "#777777"),
    path("br_gd", 420, 782, circle_d(21), "#5ee36b"),
    text("br_proj", "gxuri's projects", 610, 782, 30, "#f0f0f0", 500),
    rect("br_hob", 855, 782, 120, 46, 10, "#3d3d3d"),
    text("br_hobt", "Hobby", 855, 782, 24, "#cccccc"),
    text("br_slash2", "/", 1090, 782, 30, "#777777"),
    sphere("br_pd", 1175, 782, 18),
    text("br_demo", "skiper-ui-demo", 1370, 782, 30, "#f0f0f0", 500),
    text("br_nav", "Overview     Deployments     Analytics"
         "     Speed Insights     Logs     Observability",
         900, 915, 26, "#9a9a9a"),
    rect("br_ul", 328, 962, 210, 3, 0, "#ffffff"),
]
track("s12", cam_y=[(0, -240), (1.44, 0, "outCubic")])
scene("s12", "#000000", 1.44, n12)

# 13 ------------------------------------------------------- 3d demo card
THUMBS = ["#7a7468", "#8a5a48", "#d8d8d2", "#6a7a5a", "#111111",
          "#b09a78", "#222222", "#4a4a4a", "#8a6a6a"]
n13 = [rect("dc_card", 960, 540, 1560, 890, 42, "#1e1e1e")]
for i, c in enumerate(THUMBS):
    n13.append(rect(f"dc_th{i}", 700 + i * 68, 400, 48, 48, 10, c))
n13 += [
    path("dc_cur", 772, 462, circle_d(58), RED),
    path("dc_cura", 772, 462, "M-10 10L10 -10M10 -10L10 4M10 -10L-4 -10",
         "#ffffff", stroke=3.5),
    text("dc_w1", "FAFFA", 960, 650, 230, RED, 800),
    text("dc_w2", "ATT", 960, 650, 230, RED, 800),
    text("dc_w3", "KHATAM", 960, 650, 200, RED, 800),
    rect("dc_glow", 1240, 985, 380, 4, 2, "#ffffff", glow={
        "sigma": 8, "opacity": 0.8, "color": "#ffffff"}),
    # white components card (enters phase 2)
    rect("wc_card", 1490, 780, 980, 830, 42, "#ffffff", gradient={
        "angle": 250, "stops": [{"at": 0, "color": "#ffffff"},
                                {"at": 1, "color": "#cfcfcf"}]}),
    path("wc_sp", 1105, 470, "M0 -34C4 -12 12 -4 34 0C12 4 4 12 0 34"
         "C-4 12 -12 4 -34 0C-12 -4 -4 -12 0 -34Z", "#111111"),
    text("wc_h", "72+ Components", 1490, 480, 62, "#1a1a1a", 600),
    text("hdr", "npx shadcn add @skiper-ui", 960, 120, 56, "#f4f4f4", 500),
]
for i, label in enumerate(["12+ Components collections",
                           "23+ Free Components", "49+ Pro Components",
                           "Shadcn/ui Compatible"]):
    y = 620 + i * 122
    n13.append(rect(f"wc_p{i}", 1480, y, 830, 96, 46, "#f4f4f3"))
    n13.append(path(f"wc_s{i}", 1135, y, "M0 -15C2 -5 5 -2 15 0C5 2 2 5 "
                    "0 15C-2 5 -5 2 -15 0C-5 -2 -2 -5 0 -15Z", "#111111"))
    n13.append(text(f"wc_pt{i}", label, 1470, y, 31, "#222222"))
swap("dc_w1", 0.0, 0.85)
swap("dc_w2", 0.85, 1.9)
swap("dc_w3", 1.9)
# phase 2: card shrinks left, white card + header arrive
track("dc_card", at=2.0, scale=[(0, 1.0), (0.55, 0.6, "inOutCubic")],
      x=[(0, 0), (0.55, -500, "inOutCubic")],
      y=[(0, 0), (0.55, 160, "inOutCubic")])
track("dc_w3", at=2.0, scale=[(0, 1.0), (0.55, 0.6, "inOutCubic")],
      x=[(0, 0), (0.55, -430, "inOutCubic")],
      y=[(0, 0), (0.55, 120, "inOutCubic")])
for i in range(len(THUMBS)):
    track(f"dc_th{i}", at=2.0,
          x=[(0, 0), (0.55, -500 - (700 + i * 68 - 960) * 0.4,
              "inOutCubic")],
          y=[(0, 0), (0.55, 100, "inOutCubic")],
          scale=[(0, 1.0), (0.55, 0.6, "inOutCubic")])
track("dc_cur", at=2.0, x=[(0, 0), (0.55, -560, "inOutCubic")],
      y=[(0, 0), (0.55, 120, "inOutCubic")],
      scale=[(0, 1.0), (0.55, 0.6, "inOutCubic")])
track("dc_cura", at=2.0, x=[(0, 0), (0.55, -560, "inOutCubic")],
      y=[(0, 0), (0.55, 120, "inOutCubic")])
track("dc_glow", opacity=[(0, 0.9), (2.0, 0.9), (2.3, 0)])
track("wc_card", at=2.05, opacity=[(0, 0), (0.001, 1)],
      x=[(0, 900), (0.6, 0, "outCubic")])
for nid in ["wc_sp", "wc_h"]:
    track(nid, at=2.05, opacity=[(0, 0), (0.3, 0), (0.45, 1)],
          x=[(0, 500), (0.6, 0, "outCubic")])
for i in range(4):
    show(f"wc_p{i}", 2.35 + i * 0.2, dur=0.15, rise=26)
    show(f"wc_s{i}", 2.35 + i * 0.2, dur=0.15, rise=26)
    show(f"wc_pt{i}", 2.35 + i * 0.2, dur=0.15, rise=26)
show("hdr", 2.1, dur=0.2, rise=20)
scene("s13", "#000000", 3.56, n13)

# 14 ------------------------------------------------------ command mantra
n14 = [
    text("cm1", "npx shadcn add @skiper-ui", 960, 540, 66, "#f4f4f4", 500),
    text("cm2", "@skiper-ui", 960, 540, 66, "#f4f4f4", 500),
    text("cm3", "https://skiper-ui.com", 960, 540, 66, "#f4f4f4", 500),
]
swap("cm1", 0.0, 1.35)
swap("cm2", 1.35, 2.35)
track("cm3", opacity=[(0, 0), (2.35, 0), (2.351, 1)])
tracks.append({"target": "cm3", "at": 2.35, "reveal": {
    "unit": "type", "cadence": 0.02, "dur": 0.04}})
scene("s14", "#000000", 3.40, n14)

# 15a ----------------------------------------------------------- cli 3.0
n15a = [
    rect("cl_chip", 854, 187, 80, 80, 24, "#f6f6f6"),
    path("cl_sl", 854, 187, "M-14 12L-2 -12M2 12L14 -12", "#111111",
         stroke=3.0),
    text("cl_ct", "Available with shadcn CLI 3.0", 1240, 187, 30,
         "#6f6f6f"),
    rect("cl_pill", 1560, 525, 1560, 470, 115, "#e2e2e2"),
    sphere("cl_sph", 965, 525, 100),
    text("cl_t1", "npx shadcn", 1560, 462, 92, "#8c8c8c", 500),
    text("cl_t2", "add @skiper-ui/", 1700, 605, 92, "#8c8c8c", 500),
]
scene("s15a", "#ebebeb", 0.17, n15a)

# 15b/c ------------------------------------------- fluid + spec flashes
scene("s15b", "#000000", 0.17, fluid_badge("f2_"))
scene("s15c", "#1c1c1c", 0.16, spec_nodes("s2_"))

# 15d ----------------------------------------------------------- toolbar
n15d = [rect("tb_pill", 965, 584, 730, 175, 88, "#2e2e2e")]
xs = [700, 806, 912, 1018, 1124, 1230]
n15d += [
    path("tb_i0", xs[0], 584, circle_d(26), "#ffffff", stroke=3.0),
    rect("tb_i1", xs[1], 584, 52, 44, 8, "#2e2e2e"),
    path("tb_i1s", xs[1], 584, "M-26 -22L26 -22L26 22L-26 22Z"
         "M-26 6L-10 6L-4 14L4 14L10 6L26 6", "#ffffff", stroke=3.0),
    path("tb_i2", xs[2], 584, "M-28 0C-28 -14 -16 -22 0 -22"
         "C16 -22 28 -14 28 0C28 14 16 22 0 22C-16 22 -28 14 -28 0Z"
         + circle_d(10), "#ffffff", stroke=3.0),
    path("tb_i3", xs[3], 584, "M-30 0C-14 -20 14 -20 30 0"
         "C14 20 -14 20 -30 0Z" + circle_d(8), "#ffffff", stroke=3.0),
    path("tb_i4", xs[4], 584, "M0 14L0 -18M0 -18L-10 -8M0 -18L10 -8"
         "M-18 8L-18 20L18 20L18 8", "#ffffff", stroke=3.0),
    path("tb_i5", xs[5], 584, "M-20 -12L20 -12M-20 0L20 0M-20 12L8 12",
         "#ffffff", stroke=3.0),
    path("tb_b1", 830, 562, circle_d(7), "#29b6f6"),
    path("tb_b2", 1252, 562, circle_d(7), "#29b6f6"),
    path("tb_cur", 653, 816, "M0 0L0 30L8 22L14 34L20 30L14 20L24 18Z",
         "#111111"),
]
scene("s15d", "#ffffff", 0.17, n15d)

# 15e ----------------------------------------------------- theme toggles
n15e = [
    path("tg_c1", 725, 538, circle_d(47), "#ffffff"),
    path("tg_c1h", 725, 538, "M0 -34C18 -34 34 -18 34 0C34 18 18 34 0 34Z",
         "#141414"),
    path("tg_c2", 840, 538, circle_d(47), "#101010"),
    path("tg_c2m", 852, 528, circle_d(22), "#ffffff"),
    path("tg_c2m2", 862, 520, circle_d(20), "#101010"),
    path("tg_c3", 955, 538, circle_d(47), "#101010"),
    path("tg_c3m", 950, 532, circle_d(26), "#ffffff"),
    path("tg_c3m2", 964, 522, circle_d(24), "#101010"),
    path("tg_c4", 1075, 538, circle_d(47), "#ffffff"),
    path("tg_c4b", 1075, 534, circle_d(15), "#111111", stroke=2.5),
    path("tg_c4l", 1075, 556, "M-7 0L7 0M-5 6L5 6", "#111111", stroke=2.0),
    path("tg_c5", 1190, 538, circle_d(47), "#ffffff"),
    path("tg_c5d", 1190, 538, circle_d(20), "#111111"),
    path("tg_cur", 733, 585, "M0 0L0 26L7 19L12 30L17 26L12 18L21 16Z",
         "#ffffff"),
]
scene("s15e", DK, 0.60, n15e)

# 15f ----------------------------------------------------------- bonjour
n15f = [
    text("bj", "bonjour", 960, 540, 62, "#595959", 600),
    path("bj_cur", 1490, 811, "M0 0L0 26L7 19L12 30L17 26L12 18L21 16Z",
         "#111111"),
]
scene("s15f", "#ffffff", 0.13, n15f)

# 15g ---------------------------------------------------- shuffle number
n15g = [
    text("sh_l1", "SHUFFLE THE", 960, 212, 17, "#7a7a7a"),
    text("sh_l2", "NUMBER", 960, 240, 17, "#7a7a7a"),
    rect("sh_vl", 960, 335, 2, 130, 0, "#5a5a5a"),
    text("sh_n", "+39,843%", 957, 595, 108, "#f2f2f2", 700),
    rect("sh_btn", 960, 810, 245, 74, 37, "#1f1f1f"),
    path("sh_ic", 893, 810, "M-10 -6C-4 -14 8 -14 12 -4M10 6C4 14 -8 14 "
         "-12 4M12 -4L12 -14M12 -4L2 -4M-12 4L-12 14M-12 4L-2 4",
         "#ffffff", stroke=2.5),
    text("sh_bt", "Shuffle", 985, 810, 28, "#ffffff", 500),
]
scene("s15g", DK, 0.40, n15g)

# 15h ------------------------------------------------------- text slider
LOREM = [
    "soluta veritatis aspernatur odit assumenda odio sit, expedita",
    "culpa?  Quia  delectus  doloremque  iste  porro  obcaecati",
    "tempore ab molestiae blanditiis nam ducimus labore, mollitia",
    "quae  unde  animi  quis  iusto  omnis  sequi  libero  commodi.",
    "Quos enim quam nihil. Quis, nobis illo nam dolore ut labore",
    "distinctio  odio  fuga  alias  error  repudiandae  animi  nihil",
    "voluptatibus  voluptates  dolorem  delectus  sequi  pariatur",
    "laudantium, voluptate est corrupti sunt voluptatibus sed!",
]
n15h = [rect("sl_card", 960, 540, 1130, 640, 28, "#1f1f1f")]
for i, line in enumerate(LOREM):
    n15h.append(text(f"sl_l{i}", line, 960, 285 + i * 73, 27, "#6f6f6f"))
n15h += [
    rect("sl_bar", 960, 690, 660, 62, 31, "#282828"),
    rect("sl_h", 655, 690, 14, 46, 7, PINK),
]
scene("s15h", DK, 0.80, n15h)

# 15i ------------------------------------------------------ crowd canvas
n15i = [
    text("cw_l1", "CROUD", 960, 70, 16, "#9a9a9a"),
    text("cw_l2", "CANVAS", 960, 92, 16, "#9a9a9a"),
    rect("cw_vl", 960, 145, 1, 60, 0, "#bbbbbb"),
]
heads = [(45, 900, 34, "#111111"), (145, 865, 38, "#ffffff"),
         (245, 905, 32, "#111111"), (340, 878, 36, "#111111"),
         (435, 920, 30, "#ffffff"), (525, 885, 35, "#111111"),
         (615, 925, 32, "#111111"), (715, 890, 38, "#ffffff"),
         (810, 922, 32, "#111111"), (905, 878, 36, "#111111"),
         (1000, 918, 32, "#ffffff"), (1095, 870, 38, "#111111"),
         (1190, 912, 34, "#111111"), (1285, 880, 36, "#ffffff"),
         (1380, 918, 34, "#111111"), (1475, 872, 37, "#111111"),
         (1570, 915, 33, "#ffffff"), (1665, 878, 36, "#111111"),
         (1760, 918, 33, "#111111"), (1860, 885, 36, "#111111")]
for i, (x, y, r, c) in enumerate(heads):
    if c == "#ffffff":
        n15i.append(path(f"cw_h{i}o", x, y, circle_d(r), "#111111",
                         stroke=3.0))
    else:
        n15i.append(path(f"cw_h{i}", x, y, circle_d(r), c))
    n15i.append(rect(f"cw_b{i}", x, y + r + 68, r * 2.7, 130, 30,
                     "#111111" if i % 3 else "#1a1a1a"))
for i, (x, y, r, c) in enumerate(heads):
    nid = f"cw_h{i}o" if c == "#ffffff" else f"cw_h{i}"
    track(nid, y=[(0, 170), (0.3, 0, "outCubic")])
    track(f"cw_b{i}", y=[(0, 170), (0.3, 0, "outCubic")])
scene("s15i", "#ffffff", 0.47, n15i)

# 15i2 ------------------------------------- scroll-effect-with-gsap mosaic
n15i2 = [
    text("mo_l1", "SCROLL", 960, 40, 16, "#8a8a8a"),
    text("mo_l2", "EFFECT WITH", 960, 62, 16, "#8a8a8a"),
    text("mo_l3", "GSAP", 960, 84, 16, "#8a8a8a"),
    rect("mo_vl", 960, 140, 1, 60, 0, "#6a6a6a"),
]
TILES = [(360, 828, 280, 260, "#5a55c8"), (660, 660, 280, 260, "#c8d8ee"),
         (960, 532, 280, 255, "#b8d4e8"), (1260, 662, 280, 260, "#f4f2ee"),
         (1560, 828, 280, 255, "#8a8a86"), (660, 945, 280, 260, "#e8c8b0"),
         (960, 815, 280, 260, "#d8e4f0"), (1260, 945, 280, 255, "#f0ead8"),
         (360, 1075, 280, 200, "#3838a8"), (1560, 1075, 280, 200,
                                            "#d8d84a")]
for i, (x, y, w, h, c) in enumerate(TILES):
    n15i2.append(rect(f"mo_t{i}", x, y, w, h, 10, c))
    track(f"mo_t{i}", y=[(0, 260), (0.32, 0, "outCubic")])
scene("s15i2", DK, 0.33, n15i2)

# 15j -------------------------------------------------------- ascii site
n15j = [
    rect("as_panel", 960, 400, 1880, 645, 6, "#0a0a0a"),
    {"id": "as_a1", "type": "text", "text":
     ".:=—+****:—..:::::+++*++..—++*=+-—+%%@@@%—****++:—+++.*=%=*",
     "x": 900, "y": 330, "color": "#777777",
     "font": {"size": 22, "weight": 400, "family": "mono"}},
    {"id": "as_a2", "type": "text", "text":
     ":—%%*——*:—.—..—..—:...——..—+..%*+—:..——..+—.::%%==—:..—:*=",
     "x": 900, "y": 390, "color": "#666666",
     "font": {"size": 22, "weight": 400, "family": "mono"}},
    {"id": "as_a3", "type": "text", "text":
     ".:—%%+**++++++++—+.*....::==—:++++++—+%@:.**——+—.—*=——",
     "x": 880, "y": 450, "color": "#5a5a5a",
     "font": {"size": 22, "weight": 400, "family": "mono"}},
    {"id": "as_nav", "type": "text", "text": "HOME  ABOUT  PRICING  FAQ",
     "x": 215, "y": 36, "color": "#e8e8e6",
     "font": {"size": 19, "weight": 500, "family": "mono"}},
    {"id": "as_si", "type": "text", "text": "SIGN IN", "x": 1640, "y": 36,
     "color": "#e8e8e6", "font": {"size": 19, "weight": 500,
                                  "family": "mono"}},
    rect("as_reg", 1822, 36, 165, 52, 4, "#111111"),
    {"id": "as_regt", "type": "text", "text": "REGISTER >", "x": 1822,
     "y": 36, "color": "#f2f2ed", "font": {"size": 17, "weight": 500,
                                           "family": "mono"}},
    text("as_wm", "skiperui.com", 960, 855, 205, "#111111", 800),
    {"id": "as_f1", "type": "text", "text": "PUNJAB, INDIA", "x": 150,
     "y": 1018, "color": "#333333", "font": {"size": 17, "family": "mono"}},
    {"id": "as_f2", "type": "text", "text": "SEP 1, 2025", "x": 335,
     "y": 1018, "color": "#333333", "font": {"size": 17, "family": "mono"}},
    {"id": "as_f3", "type": "text", "text": "ONILNE  FREE", "x": 1590,
     "y": 1018, "color": "#333333", "font": {"size": 17, "family": "mono"}},
    {"id": "as_f4", "type": "text", "text": "IN PERSON  $600", "x": 1790,
     "y": 1018, "color": "#333333", "font": {"size": 17, "family": "mono"}},
]
scene("s15j", "#f2f2ed", 0.67, n15j)

# 15k -------------------------------------------------------- gsap scroll
n15k = [
    text("gs_l1", "GSAP", 960, 26, 16, "#8a8a8a"),
    text("gs_l2", "PERSPECTIVE", 960, 48, 16, "#8a8a8a"),
    text("gs_l3", "SCROLL", 960, 70, 16, "#8a8a8a"),
    text("gs_l4", "EFFECT", 960, 92, 16, "#8a8a8a"),
    rect("gs_vl", 960, 150, 1, 70, 0, "#6a6a6a"),
    rect("gs_c1", 820, 550, 235, 275, 10, "#565149"),
    rect("gs_c2", 1100, 548, 240, 285, 10, "#b98a4e"),
    rect("gs_c3", 805, 940, 250, 305, 10, "#a03040"),
    rect("gs_c4", 1110, 945, 255, 300, 10, "#6b6560"),
    path("gs_cur", 1785, 965, "M0 0L0 30L8 22L14 34L20 30L14 20L24 18Z",
         "#ffffff"),
]
for nid in ("gs_c1", "gs_c2", "gs_c3", "gs_c4"):
    track(nid, y=[(0, 60), (0.13, 0, "outCubic")])
scene("s15k", DK, 0.13, n15k)

# 15k2 --------------------------------------------------- pink draw scene
n15k2 = [
    rect("dr_tip", 250, 22, 520, 44, 4, "#f2aac4"),
    {"id": "dr_tipt", "type": "text",
     "text": "lick: add cube Shift + Click: remove cube",
     "x": 255, "y": 22, "color": "#7c1035",
     "font": {"size": 17, "weight": 500, "family": "mono"}},
    text("dr_w", "Draw", 990, 875, 195, "#8b1f38", 800),
    text("dr_h1", "click on the grid to start adding", 1115, 778, 20,
         "#a82040"),
    text("dr_h2", "blocks to the canvas", 1160, 802, 20, "#a82040"),
    rect("dr_c1", 680, 685, 66, 62, 6, "#8f2a33", rot=-8),
    rect("dr_c2", 1170, 540, 58, 56, 6, "#8f2a33", rot=10),
    rect("dr_c3", 1305, 695, 60, 58, 6, "#8f2a33", rot=-6),
    rect("dr_c4", 1478, 452, 50, 48, 6, "#8f2a33", rot=12),
    text("dr_p1", "Lorem ipsum dolor sit amet consectetur adipisicing"
         " elit. Maiores quia beatae cum nisi labe ipsam", 995, 1018, 19,
         "#a11c48"),
    text("dr_p2", "diaboribus possimus architecto, incidunt error, totam"
         " itaque exercitationem? Aliquam maiores pariatur", 995, 1042, 19,
         "#a11c48"),
    path("dr_cur", 1732, 962, "M0 0L0 30L8 22L14 34L20 30L14 20L24 18Z",
         "#ffffff"),
]
scene("s15k2", "#dc0f60", 0.47, n15k2)

# 15l ----------------------------------------------------------- live now
n15l = [
    rect("ln_page", 960, 226, 1892, 452, 10, "#f6f7f2"),
    text("ln_d", "07.09.2025", 778, 306, 44, "#111111", 600),
    text("ln_h", "Skiper ui is live now", 853, 352, 46, "#111111", 600),
    text("ln_p1", "Lorem ipsum dolor sit amet consectetur adipisicing"
         " elit. Nihil, ex", 943, 425, 24, "#3a3a3a"),
    text("ln_p2", "eligendi veniam praesentium temporibus natus quae"
         " laborum nemo", 950, 455, 24, "#3a3a3a"),
    text("ln_p3", "repellendus cum!", 745, 492, 24, "#3a3a3a"),
    text("ln_p4", "Lorem ipsum dolor sit amet consectetur adipisicing"
         " elit. Nihil, ex", 943, 535, 24, "#8a8a8a"),
    text("ln_p5", "eligendi veniam praesentium temporibus natus quae"
         " laborum nemo", 950, 565, 24, "#8a8a8a"),
    text("ln_p6", "repellendus cum!  Lorem ipsum dolor sit amet"
         " consectetur adipisicing.", 965, 640, 24, "#8a8a8a"),
    rect("ln_opt", 1527, 450, 260, 100, 18, "#fbfbf9"),
    text("ln_optt", "Options", 1585, 428, 21, "#8a8a8a"),
    text("ln_sh", "shape :   circle  circle-blur", 1520, 470, 19,
         "#9a9a9a"),
    text("ln_t1", "CLICK TO", 960, 782, 15, "#8a8a8a"),
    text("ln_t2", "TOGGLE THE", 960, 803, 15, "#8a8a8a"),
    text("ln_t3", "THEME", 960, 824, 15, "#8a8a8a"),
    rect("ln_vl", 960, 872, 1, 60, 0, "#6a6a6a"),
    path("ln_tog", 960, 932, circle_d(26), "#ffffff"),
    path("ln_bf", 958, 932, "M-12 -4C-4 -14 6 -12 8 -2C14 -8 20 0 12 8"
         "C4 14 -8 12 -12 -4Z", "#111111"),
]
scene("s15l", DK, 0.53, n15l)

# 15m --------------------------------------------------- code flash again
n15m = []
for i, line in enumerate(CODE):
    if line:
        n15m.append({"id": f"c2_l{i}", "type": "text", "text": line,
                     "x": 640, "y": 60 + i * 58, "color": "#585858",
                     "font": {"size": 24, "weight": 400, "family": "mono"}})
n15m.append(sphere("c2_sph", 1000, 560, 100))
scene("s15m", "#1c1c1c", 0.34, n15m)

# 16 --------------------------------------------------------- end gallery
scene("s16", "#ffffff", 0.90, gallery("ge_"))

stage = {"fps": 30, "size": [W, H], "scenes": scenes}
with open("docs/skipper-ui.stage.json", "w") as f:
    json.dump(stage, f, indent=1)
with open("docs/skipper-ui.anim.json", "w") as f:
    json.dump({"tracks": tracks}, f, indent=1)
total = sum(s["dur"] for s in scenes)
print("wrote docs/skipper-ui.{stage,anim}.json,",
      sum(len(s["nodes"]) for s in scenes), "nodes,", len(tracks),
      f"tracks, {total:.2f}s")
