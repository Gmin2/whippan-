#!/usr/bin/env python3
# reproduction of animations/survey (8.90s, 1080x1080): the desktop.fm
# "party" onboarding survey screen recording. one continuous take, zero
# cuts: landing in an iphone mockup -> crash zoom through the bezel ->
# genre bubbles -> typewriter youtube search -> results -> preview player
# -> "you added 3 tracks" stack -> email typewriter -> request access ->
# spinner -> indigo "sent!" -> the page rotate-slides out -> "ok!".
# timings in seconds from the 60fps teardown ledger (frame N = (N-1)/60).
# album art / photos are drawn stand-ins, layout kept exact.
import json
import math
import os

W, H = 1080, 1080
F = 1 / 60
K = 0.5523
INK = "#131313"
GREY_T = "#a9aeb1"
APP_BG = "#e7ecef"
INDIGO = "#4250ee"
ORANGE = "#e76d24"

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

tracks = []
keyacc = {}          # (nid, prop) -> [key dicts]
scene_nodes = {}     # scene id -> node list


def key(nid, prop, seq):
    out = keyacc.setdefault((nid, prop), [])
    for k in seq:
        kk = {"t": round(k[0], 3), "v": k[1]}
        if len(k) > 2 and k[2]:
            kk["ease"] = k[2]
        out.append(kk)


def opacity_steps(nid, pairs):
    ks = []
    for tt, v in pairs:
        if ks and v != ks[-1][1]:
            ks.append((round(tt - 0.001, 3), ks[-1][1]))
        ks.append((tt, v))
    key(nid, "opacity", ks)


def make(scene, n):
    scene_nodes[scene].append(n)
    return n


def text(scene, id, s, x, y, size, color, weight=700, **kw):
    n = {"id": id, "type": "text", "text": s, "x": x, "y": y,
         "color": color, "font": {"size": size, "weight": weight}}
    n.update(kw)
    return make(scene, n)


def rect(scene, id, x, y, w, h, r, fill, **kw):
    n = {"id": id, "type": "rect", "x": x, "y": y, "w": w, "h": h,
         "radius": r, "fill": fill}
    n.update(kw)
    return make(scene, n)


def path(scene, id, x, y, d, fill, stroke=None, **kw):
    n = {"id": id, "type": "path", "x": x, "y": y, "d": d, "fill": fill}
    if stroke:
        n["stroke"] = stroke
    n.update(kw)
    return make(scene, n)


def ellipse_d(rx, ry, cx=0, cy=0):
    kx, ky = rx * K, ry * K
    return (f"M{cx-rx} {cy}C{cx-rx} {cy-ky} {cx-kx} {cy-ry} {cx} {cy-ry}"
            f"C{cx+kx} {cy-ry} {cx+rx} {cy-ky} {cx+rx} {cy}"
            f"C{cx+rx} {cy+ky} {cx+kx} {cy+ry} {cx} {cy+ry}"
            f"C{cx-kx} {cy+ry} {cx-rx} {cy+ky} {cx-rx} {cy}Z")


def circle_d(r, cx=0, cy=0):
    return ellipse_d(r, r, cx, cy)


CHECK = "M-8 1L-3 6L8 -7"
CHEV_L = "M3 -6L-3 0L3 6"
PLUS = "M-8 0L8 0M0 -8L0 8"
XMARK = "M-7 -7L7 7M7 -7L-7 7"
PLAY = "M-12 -15L17 0L-12 15Z"
PLANE = "M-12 4L14 -9L1 11L-2 5Z"
IBEAM = "M-6 -15L6 -15M0 -15L0 15M-6 15L6 15"


def ticks_d(r0=8, r1=13, n=8):
    d = ""
    for i in range(n):
        a = i * 2 * math.pi / n
        d += (f"M{r0*math.cos(a):.1f} {r0*math.sin(a):.1f}"
              f"L{r1*math.cos(a):.1f} {r1*math.sin(a):.1f}")
    return d


def star_d(r=9):
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((rr * math.cos(a), rr * math.sin(a)))
    return "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in pts) + "Z"


def hand_d():
    """simplified pointing-hand cursor, ~46px tall."""
    return ("M-3 -22L3 -22L3 -4L7 -5L15 -3C19 -2 20 1 19 5L16 15"
            "C15 19 12 21 8 21L-6 21C-10 21 -13 19 -14 15L-16 6"
            "C-17 2 -15 -1 -11 -2L-3 -4Z")


def blond_cover(scene, prefix, cx, cy, s, r):
    """stand-in for the Blond album photo: grey field, green hair, figure."""
    rect(scene, f"{prefix}_bg", cx, cy, s, s, r, "#ccd2cb")
    path(scene, f"{prefix}_hair", cx, cy - s * 0.26,
         circle_d(s * 0.20), "#5d7742")
    path(scene, f"{prefix}_body", cx, cy + s * 0.10,
         circle_d(s * 0.15, 0, -s * 0.08)
         + f"M{-s*0.28} {s*0.42}C{-s*0.28} {s*0.02} {s*0.28} {s*0.02} "
         f"{s*0.28} {s*0.42}L{-s*0.28} {s*0.42}Z", "#b98a63")
    return [f"{prefix}_bg", f"{prefix}_hair", f"{prefix}_body"]


# ================================================================ scene 1
# phone world: landing "music nerd?" -> crash zoom -> "party / choose one"
# f1-95, dur 1.5667. camera does everything; page swap under the dive.
S1 = "s1"
scene_nodes[S1] = []

rect(S1, "ph_body", 539, 540, 448, 912, 96, "#23262b")
rect(S1, "ph_screen", 539, 540, 416, 880, 80, APP_BG)
rect(S1, "ph_notch", 539, 127, 160, 34, 17, "#0b0d0f")
rect(S1, "ph_home", 539, 953, 130, 5, 2, "#16181a")

landing = []
landing.append(rect(S1, "l_icon", 539, 189, 36, 36, 18, "#111111"))
landing.append(path(S1, "l_icon_g", 539, 189, star_d(9), "#ffffff"))
landing.append(text(S1, "l_h1", "music", 514, 400, 116, INK, weight=800))
landing.append(text(S1, "l_h2", "nerd?", 583, 492, 112, INK, weight=800))
landing.append(text(S1, "l_s1", "i am building an app to discover",
                    539, 586, 22, "#bec4c4", weight=600))
landing.append(text(S1, "l_s2", "music and hang out with friends.",
                    539, 613, 22, "#bec4c4", weight=600))
landing.append(text(S1, "l_s3", "want to join the beta?",
                    539, 640, 22, "#16181a", weight=800))
landing.append(rect(S1, "l_btn", 539, 707, 164, 48, 24, "#101010",
                    states={"pressed": {"fill": "#3f3f42"}}))
landing.append(path(S1, "l_btn_c", 495, 707,
                    "M-6 0L-2 4L6 -5", None, stroke=2.2))
scene_nodes[S1][-1]["fill"] = "#cfcfcf"
landing.append(text(S1, "l_btn_t", "let's go!", 551, 707, 19, "#ffffff",
                    weight=700))
landing.append(text(S1, "l_foot",
                    "built with passion by xavier (jack) at desktop.fm",
                    539, 926, 12, "#b7bcbe", weight=500))
for n in landing:
    opacity_steps(n["id"], [(0, 1), (0.62, 1), (0.76, 0)])
tracks.append({"target": "l_btn", "at": 0.55, "state": "pressed"})

# party page inside the phone (world coords derived from the f75 framing)
party = []
party.append(rect(S1, "p_pill", 539, 187, 302, 46, 23, "#ffffff"))
party.append(rect(S1, "p_back", 474, 187, 52, 22, 11, "#16181a"))
party.append(text(S1, "p_back_t", "back", 477, 187, 10, "#ffffff",
                  weight=700))
party.append(text(S1, "p_logo", "party", 539, 186, 22, "#16181a",
                  weight=800))
party.append(rect(S1, "p_cntc", 628, 187, 42, 22, 11, "#16181a"))
cnt0 = text(S1, "p_cnt0", "0 - 3", 628, 187, 10, "#ffffff", weight=700)
cnt1 = text(S1, "p_cnt1", "1 - 3", 628, 187, 10, "#ffffff", weight=700)
party.append(text(S1, "p_choose", "choose one...", 556, 356, 22, "#1a1a1a",
                  weight=800))
BUBBLES = [
    ("p_b1", 562, 436, 62, 43, [("APHEX", 15, -9), ("TWIN", 15, 9)]),
    ("p_b2", 467, 508, 60, 40, [("GORILLAZ", 14, 0)]),
    ("p_b3", 608, 531, 75, 50, [("PC", 17, -11), ("MUSIC", 17, 11)]),
    ("p_b4", 455, 592, 65, 40, [("DIEGLING", 13, 0)]),
    ("p_b5", 588, 618, 58, 38, [("A.G. COOK", 12, 0)]),
    ("p_b6", 487, 660, 60, 38, [("SOPHIE", 13, 0)]),
]
for bid, bx, by, rx, ry, labels in BUBBLES:
    party.append(path(S1, bid, bx, by, ellipse_d(rx, ry), "#141416"))
    for j, (lab, sz, dy) in enumerate(labels):
        party.append(text(S1, f"{bid}_t{j}", lab, bx, by + dy, sz,
                          "#ffffff", weight=800))
for n in party:
    opacity_steps(n["id"], [(0, 0), (0.72, 0), (0.86, 1)])
# tap: counter 0-3 -> 1-3 at f92
opacity_steps("p_cnt0", [(0, 0), (0.72, 0), (0.86, 1), (1.517, 0)])
opacity_steps("p_cnt1", [(0, 0), (1.517, 1)])

# camera: slow creep, crash dive into the headline, pull back onto the
# party page top, hold, then punch through the bezel into scene 2
key(S1, "cam_zoom", [(0, 1.0), (0.55, 1.07), (0.68, 2.9, "inOutCubic"),
                     (0.98, 1.95, "outCubic"), (1.50, 2.02),
                     (1.567, 3.4, "inCubic")])
key(S1, "cam_y", [(0, 0), (0.55, 4), (0.68, -90, "inOutCubic"),
                  (0.98, -240, "outCubic"), (1.50, -244),
                  (1.567, -320, "inCubic")])

# ================================================================ scene 2
# full-bleed search: title + typewriter query -> results -> preview player
# f95-225, dur 2.1667, local t = (N-95)/60
S2 = "s2"
scene_nodes[S2] = []

path(S2, "q_ring1", 540, 540, circle_d(500), "#dde3e7", stroke=1.5)
path(S2, "q_ring2", 540, 540, circle_d(660), "#dde3e7", stroke=1.5)

rect(S2, "q_pill", 539, 118, 470, 76, 38, "#ffffff")
rect(S2, "q_back", 367, 118, 104, 44, 22, "#16181a")
path(S2, "q_back_ch", 332, 118, CHEV_L, None, stroke=2.2)
scene_nodes[S2][-1]["fill"] = "#8a8f94"
text(S2, "q_back_t", "back", 375, 117, 20, "#ffffff")
text(S2, "q_logo", "party", 539, 117, 40, "#16181a", weight=800)
rect(S2, "q_cntc", 719, 118, 82, 44, 22, "#16181a")
text(S2, "q_cnt", "1 - 3", 719, 117, 17, "#ffffff")

t1 = text(S2, "q_t1", "your favorite", 540, 492, 112, INK, weight=800)
t2 = text(S2, "q_t2", "frank ocean track", 540, 630, 108, GREY_T,
          weight=700)
# list build: the big titles hand off to small copies riding up (text
# scale keys spread the word layout, so this is a crossfade instead)
opacity_steps("q_t1", [(0, 1), (0.95, 1), (1.10, 0)])
opacity_steps("q_t2", [(0, 1), (0.95, 1), (1.10, 0)])
key("q_t1", "y", [(0.95, 0), (1.12, -110, "outCubic")])
key("q_t2", "y", [(0.95, 0), (1.12, -140, "outCubic")])
text(S2, "q_t1s", "your favorite", 540, 248, 56, INK, weight=800)
text(S2, "q_t2s", "frank ocean track", 540, 311, 54, GREY_T, weight=700)
opacity_steps("q_t1s", [(0, 0), (0.98, 0), (1.12, 1)])
opacity_steps("q_t2s", [(0, 0), (0.98, 0), (1.12, 1)])
key("q_t1s", "y", [(0.98, 30), (1.18, 0, "outCubic"),
                   (1.60, 0), (1.85, -45, "outCubic")])
key("q_t2s", "y", [(0.98, 30), (1.18, 0, "outCubic"),
                   (1.60, 0), (1.85, -27, "outCubic")])

rect(S2, "q_field", 539, 821, 590, 100, 50, "#ffffff")
key("q_field", "y", [(0.95, 0), (1.20, -390, "outCubic")])
key("q_field", "w", [(0.95, 590), (1.20, 524, "outCubic")])
key("q_field", "h", [(0.95, 100), (1.20, 90, "outCubic")])
text(S2, "q_ph", "search track in youtube...", 467, 819, 28, "#b9bfc2",
     weight=500)
opacity_steps("q_ph", [(0, 1), (0.05, 0)])
q = text(S2, "q_query", "frank ocean blonded", 435, 821, 30, "#16181a")
tracks.append({"target": "q_query", "at": 0.033, "reveal": {
    "unit": "type", "cadence": 0.047, "dur": 0.06, "caret": "bar",
    "caret_blink": 0.9}})
key("q_query", "y", [(0.95, 0), (1.20, -390, "outCubic")])
key("q_query", "x", [(0.95, 0), (1.20, 13, "outCubic")])
key("q_query", "scale", [(0.95, 1.0), (1.20, 0.91, "outCubic")])
# field spinner while typing
path(S2, "q_fspin", 786, 821, ticks_d(), None, stroke=2.6)
scene_nodes[S2][-1]["fill"] = "#c3c9cc"
opacity_steps("q_fspin", [(0, 0), (0.07, 0.9), (0.93, 0.9), (0.97, 0)])
tracks.append({"target": "q_fspin", "loop": True,
               "keys": {"rot": [{"t": 0, "v": 0}, {"t": 0.8, "v": 360}]}})

# results list (final, post-shift geometry; rows are born after the shift)
list_ids = []
list_ids.append(rect(S2, "q_panel", 540, 813, 486, 586, 30,
                     "#ffffff")["id"])
ROWS = [("blonde tribute", 593), ("pink + white", 740),
        ("godspeed", 887), ("self control", 1034)]
for i, (name, ry) in enumerate(ROWS):
    if i == 0:
        list_ids.append(rect(S2, f"q_r{i}_th", 364, ry, 92, 92, 14,
                             "#1c1c1e")["id"])
        list_ids.append(text(S2, f"q_r{i}_bl", "blond", 364, ry + 18, 15,
                             "#e0a43c")["id"])
    else:
        list_ids += blond_cover(S2, f"q_r{i}_th", 364, ry, 92, 14)
    list_ids.append(text(S2, f"q_r{i}_l", "frank ocean", 492, ry - 22, 20,
                         "#8a8a8a", weight=600)["id"])
    nx = 437 + len(name) * 27 * 0.25
    list_ids.append(text(S2, f"q_r{i}_n", name, round(nx), ry + 8, 27, INK,
                         weight=800)["id"])
    list_ids.append(rect(S2, f"q_r{i}_p", 727, ry, 44, 44, 22,
                         INK)["id"])
    pp = path(S2, f"q_r{i}_pp", 727, ry, PLUS, None, stroke=3.0)
    pp["fill"] = "#ffffff"
    list_ids.append(pp["id"])
for nid in list_ids:
    row = 0
    if nid[3].isdigit():
        row = int(nid[3])
    born = 0.95 + row * 0.05
    opacity_steps(nid, [(0, 0), (born, 0), (born + 0.12, 1),
                        (1.58, 1), (1.70, 0)])
    key(nid, "y", [(born, 40), (born + 0.22, 0, "outCubic")])
# field chrome dies with the list when the player takes over
opacity_steps("q_field", [(0, 1), (1.58, 1), (1.70, 0)])
opacity_steps("q_query", [(0, 0), (0.033, 1), (1.58, 1), (1.70, 0)])

# youtube preview player, gooey-expands at its final spot
player = []
player.append(rect(S2, "v_card", 540, 558, 616, 366, 44, "#ffffff"))
player.append(rect(S2, "v_art", 540, 575, 264, 300, 6, "#d8d3cc"))
player.append(path(S2, "v_hair", 540, 500, circle_d(48), "#5d7742"))
player.append(path(S2, "v_body", 540, 600,
                   "M-70 75C-70 -25 70 -25 70 75L-70 75Z", "#b98a63"))
player.append(path(S2, "v_av", 287, 433, circle_d(32), "#a8ad9c"))
player.append(path(S2, "v_avr", 287, 433, circle_d(22), None, stroke=2.0))
scene_nodes[S2][-1]["fill"] = "#7d8272"
player.append(text(S2, "v_wm", "blond", 541, 408, 28, "#8d938d",
                   weight=700))
player.append(text(S2, "v_title", "Frank Ocean - Pink + White", 538, 436,
                   24, "#4a4e52", weight=600))
player.append(path(S2, "v_kebab", 783, 436,
                   circle_d(2.6, 0, -8) + circle_d(2.6) + circle_d(2.6, 0, 8),
                   "#6a6f73"))
player.append(rect(S2, "v_play", 540, 558, 96, 68, 20, "#f10000"))
player.append(path(S2, "v_playt", 543, 558, PLAY, "#ffffff"))
player.append(path(S2, "v_bc", 540, 712,
                   "".join(f"M{x} -9L{x} 9" for x in range(-24, 25, 6)),
                   None, stroke=2.0))
scene_nodes[S2][-1]["fill"] = "#1a1a1a"
# remove / ok bar
player.append(rect(S2, "v_rm", 403, 841, 280, 90, 45, "#e4e7ea"))
player.append(path(S2, "v_rm_x", 310, 841, XMARK, None, stroke=2.6))
scene_nodes[S2][-1]["fill"] = "#55595c"
player.append(text(S2, "v_rm_t", "remove", 428, 841, 26, "#55595c"))
okg = rect(S2, "v_okg", 690, 841, 254, 90, 45, "#a9aeb2")
player.append(okg)
okb = rect(S2, "v_okb", 690, 841, 254, 90, 45, INK)
player.append(path(S2, "v_ok_c", 648, 841, "M-7 1L-2 6L7 -6", None,
                   stroke=2.6))
scene_nodes[S2][-1]["fill"] = "#ffffff"
player.append(text(S2, "v_ok_t", "ok", 703, 841, 26, "#ffffff"))
PC = (540, 640)   # player group scale-in center
for n in player:
    nid = n["id"]
    opacity_steps(nid, [(0, 0), (1.62, 0), (1.78, 1)])
    dx, dy = (PC[0] - n["x"]) * 0.15, (PC[1] - n["y"]) * 0.15
    key(nid, "x", [(1.62, round(dx, 1)), (1.80, 0, "outCubic")])
    key(nid, "y", [(1.62, round(dy, 1)), (1.80, 0, "outCubic")])
    key(nid, "scale", [(1.62, 0.85), (1.80, 1.0, "outCubic")])
# "ok" arms once the preview loads: grey fades, black underneath
opacity_steps("v_okb", [(0, 0), (1.95, 0), (2.12, 1)])

# cursor: on the field, eases down to the pink+white row, then the player
n = make(S2, {"id": "q_cur", "type": "cursor", "x": 540, "y": 872,
              "w": 40, "fill": "#111111"})
opacity_steps("q_cur", [(0, 0), (0.03, 1)])
key("q_cur", "x", [(1.10, 0), (1.45, -10, "inOutCubic"),
                   (1.75, 5, "inOutCubic")])
key("q_cur", "y", [(1.10, 0), (1.45, -117, "inOutCubic"),
                   (1.75, -172, "inOutCubic")])

# residual drift
key(S2, "cam_zoom", [(0, 1.03), (0.9, 1.0, "outCubic"), (2.167, 1.02)])
key(S2, "cam_y", [(0, -8), (2.167, 6)])

# ================================================================ scene 3
# "you added 3 tracks" + email + request access -> sent
# f225-465, dur 4.0, local t = (N-225)/60
S3 = "s3"
scene_nodes[S3] = []

path(S3, "a_ring1", 540, 540, circle_d(500), "#dde3e7", stroke=1.5)
path(S3, "a_ring2", 540, 540, circle_d(660), "#dde3e7", stroke=1.5)

rect(S3, "a_pill", 540, 97, 420, 66, 33, "#ffffff")
rect(S3, "a_back", 393, 97, 84, 36, 18, "#16181a")
path(S3, "a_back_ch", 365, 97, CHEV_L, None, stroke=2.0)
scene_nodes[S3][-1]["fill"] = "#8a8f94"
text(S3, "a_back_t", "back", 400, 96, 17, "#ffffff")
text(S3, "a_logo", "party", 540, 96, 34, "#16181a", weight=800)
rect(S3, "a_cntc", 692, 97, 72, 36, 18, "#16181a")
text(S3, "a_cnt", "3 - 3", 692, 96, 15, "#ffffff")

text(S3, "a_title", "you added 3 tracks:", 540, 345, 52, INK, weight=800)

# fanned chip stack: channel orange / nostalgia ultra bmw / pink + white
rect(S3, "a_c1", 365, 512, 215, 132, 62, "#ffffff", rot=-5)
rect(S3, "a_c1_art", 350, 508, 88, 88, 24, ORANGE, rot=-5)
text(S3, "a_c1_t", "channel ORANGE", 350, 507, 9, "#ffffff", weight=600,
     rot=-5)
rect(S3, "a_c2", 462, 515, 215, 132, 62, "#ffffff", rot=-2)
rect(S3, "a_c2_art", 447, 512, 88, 88, 20, "#97a06b", rot=-2)
path(S3, "a_c2_car", 447, 514,
     "M-32 12C-32 0 -25 -6 -13 -8L13 -8C25 -6 32 0 32 12L32 17L-32 17Z"
     "M-11 -7L11 -7L15 1L-15 1Z", "#d8501e", rot=-2)
path(S3, "a_c2_wh", 447, 530, circle_d(6, -18, 0) + circle_d(6, 18, 0),
     "#1a1a1a", rot=-2)
rect(S3, "a_c3", 630, 510, 322, 132, 62, "#ffffff")
blond_cover(S3, "a_c3_art", 543, 509, 88, 30)
text(S3, "a_c3_l", "frank ocean", 658, 494, 20, "#727272", weight=600)
text(S3, "a_c3_n", "pink + white", 668, 524, 27, INK, weight=800)

rect(S3, "a_field", 540, 722, 490, 84, 42, "#ffffff")
text(S3, "a_ph", "your email...", 441, 722, 26, "#b9bfc2", weight=500)
opacity_steps("a_ph", [(0, 1), (1.05, 1), (1.13, 0)])
text(S3, "a_mail", "xavier@desktop.fm", 455, 722, 27, "#16181a")
tracks.append({"target": "a_mail", "at": 1.083, "reveal": {
    "unit": "type", "cadence": 0.115, "dur": 0.08, "caret": "bar",
    "caret_blink": 0.9}})
opacity_steps("a_mail", [(0, 0), (1.083, 1)])

rect(S3, "a_btn", 540, 843, 294, 74, 37, INK)
path(S3, "a_btn_c", 448, 843, "M-6 1L-2 5L7 -6", None, stroke=2.4)
scene_nodes[S3][-1]["fill"] = "#cfcfcf"
text(S3, "a_btn_t", "request access", 562, 843, 24, "#ffffff")
for nid in ["a_btn", "a_btn_c", "a_btn_t"]:
    opacity_steps(nid, [(0, 1), (3.317, 0)])
# loading state
rect(S3, "a_btng", 540, 843, 294, 74, 37, "#dfe3e6")
opacity_steps("a_btng", [(0, 0), (3.317, 1), (3.60, 0)])
path(S3, "a_spin", 540, 843, ticks_d(7, 12), None, stroke=2.6)
scene_nodes[S3][-1]["fill"] = "#9aa0a3"
opacity_steps("a_spin", [(0, 0), (3.35, 1), (3.58, 0)])
tracks.append({"target": "a_spin", "loop": True,
               "keys": {"rot": [{"t": 0, "v": 0}, {"t": 0.7, "v": 360}]}})
# sent state
rect(S3, "a_sent", 541, 840, 200, 66, 33, INDIGO)
path(S3, "a_sent_p", 470, 839, PLANE, "#ffffff")
text(S3, "a_sent_t", "sent!", 560, 839, 24, "#ffffff", weight=800)
for nid in ["a_sent", "a_sent_p", "a_sent_t"]:
    opacity_steps(nid, [(0, 0), (3.60, 1)])

# cursors: arrow -> i-beam glued to the caret -> pointing hand
make(S3, {"id": "a_cur", "type": "cursor", "x": 760, "y": 875, "w": 40,
          "fill": "#111111"})
key("a_cur", "x", [(0.30, 0), (0.95, -310, "inOutCubic")])
key("a_cur", "y", [(0.30, 0), (0.95, -138, "inOutCubic")])
opacity_steps("a_cur", [(0, 1), (1.05, 1), (1.10, 0)])
path(S3, "a_ib", 340, 738, IBEAM, None, stroke=2.4)
scene_nodes[S3][-1]["fill"] = "#2a2d30"
opacity_steps("a_ib", [(0, 0), (1.02, 1), (3.10, 1), (3.16, 0)])
key("a_ib", "x", [(1.083, 0), (3.05, 230)])
path(S3, "a_hand_o", 545, 858, hand_d(), "#1a1a1a")
scene_nodes[S3][-1]["keys"] = {"scale": [{"t": 0, "v": 1.14}]}
path(S3, "a_hand", 545, 858, hand_d(), "#ffffff")
for nid in ["a_hand_o", "a_hand"]:
    opacity_steps(nid, [(0, 0), (3.16, 1)])
    key(nid, "y", [(3.30, 0), (3.34, 4), (3.40, 0)])

# camera: settle, slow push onto the form (header rides out), typing hold,
# pull back for the sent flip
key(S3, "cam_zoom", [(0.083, 1.0), (1.05, 1.38, "inOutCubic"),
                     (3.15, 1.40), (3.55, 1.0, "outCubic")])
key(S3, "cam_y", [(0.083, 0), (1.05, 64, "inOutCubic"), (3.15, 70),
                  (3.55, 0, "outCubic")])

# rotate-slide exit: the whole page tilts like a physical card before the
# whip carries it away. computed rotation about the page center.
EXIT_T0, EXIT_T1, THETA = 3.73, 4.0, -9.0
th = math.radians(THETA)
CXY = (540, 600)
for n in scene_nodes[S3]:
    nid = n["id"]
    px, py = n["x"], n["y"]
    # start from wherever earlier keys left the node
    bx = keyacc.get((nid, "x"), [])
    by = keyacc.get((nid, "y"), [])
    x0 = bx[-1]["v"] if bx else 0.0
    y0 = by[-1]["v"] if by else 0.0
    wx, wy = px + x0, py + y0
    rx = CXY[0] + (wx - CXY[0]) * math.cos(th) - (wy - CXY[1]) * math.sin(th)
    ry = CXY[1] + (wx - CXY[0]) * math.sin(th) + (wy - CXY[1]) * math.cos(th)
    key(nid, "x", [(EXIT_T0, x0), (EXIT_T1, round(rx - px - 30, 1),
                                   "inCubic")])
    key(nid, "y", [(EXIT_T0, y0), (EXIT_T1, round(ry - py - 70, 1),
                                   "inCubic")])
    base_rot = n.get("rot", 0)
    key(nid, "rot", [(EXIT_T0, base_rot), (EXIT_T1, base_rot + THETA,
                                           "inCubic")])

# ================================================================ scene 4
# "ok!" success, slides up under the whip, settles, slow push-in
# f465-530, dur 1.1667
S4 = "s4"
scene_nodes[S4] = []

path(S4, "k_ring1", 540, 540, circle_d(500), "#dde3e7", stroke=1.5)
path(S4, "k_ring2", 540, 540, circle_d(660), "#dde3e7", stroke=1.5)

rect(S4, "k_pill", 540, 97, 280, 64, 32, "#ffffff")
text(S4, "k_t", "request sent", 505, 96, 22, "#16181a")
rect(S4, "k_badge", 646, 97, 42, 42, 21, "#7377f4")
path(S4, "k_check", 646, 97, "M-7 1L-2 6L7 -6", None, stroke=2.4)
scene_nodes[S4][-1]["fill"] = "#ffffff"

text(S4, "k_ok", "ok!", 548, 485, 250, INK, weight=800)
text(S4, "k_s1", "will send you an email", 537, 700, 42, INK, weight=800)
text(S4, "k_s2", "for a listening party", 536, 752, 42, INK, weight=800)
rect(S4, "k_rt", 533, 845, 275, 56, 28, "#e2e6e9")
path(S4, "k_rt_g", 428, 845, circle_d(8) + "M4 -8L9 -11L10 -4", None,
     stroke=1.8)
scene_nodes[S4][-1]["fill"] = "#8a9096"
text(S4, "k_rt_t", "retake the survey", 548, 845, 20, "#8a9096",
     weight=600)
path(S4, "k_hand_o", 545, 852, hand_d(), "#1a1a1a")
scene_nodes[S4][-1]["keys"] = {"scale": [{"t": 0, "v": 1.14}]}
path(S4, "k_hand", 545, 852, hand_d(), "#ffffff")

# arrive dim (the real page deblurs grey -> black), settle to full ink
for n in scene_nodes[S4]:
    if n["id"].startswith("k_ring"):
        continue
    opacity_steps(n["id"], [(0, 0.55), (0.20, 0.55), (0.45, 1)])
key(S4, "cam_zoom", [(0, 1.0), (0.45, 1.0), (1.167, 1.08)])

# ============================================================== assemble
for (nid, prop), ks in keyacc.items():
    ks.sort(key=lambda k: k["t"])
    tracks.append({"target": nid, "keys": {prop: ks}})

# merge tracks that share a target so each node keeps one keys track per
# property but different properties can ride together
merged = {}
final_tracks = []
for t in tracks:
    if "keys" in t and "at" not in t and not t.get("loop"):
        tgt = t["target"]
        if tgt in merged:
            merged[tgt]["keys"].update(t["keys"])
            continue
        merged[tgt] = t
    final_tracks.append(t)

stage = {
    "fps": 30,
    "size": [W, H],
    "scenes": [
        {"id": "s1", "bg": "#ffffff", "dur": 1.5667,
         "transition": {"kind": "cut"}, "nodes": scene_nodes["s1"]},
        {"id": "s2", "bg": APP_BG, "dur": 2.1667,
         "transition": {"kind": "zoom", "dur": 0.28},
         "nodes": scene_nodes["s2"]},
        {"id": "s3", "bg": APP_BG, "dur": 4.0,
         "transition": {"kind": "rise", "dur": 0.2},
         "nodes": scene_nodes["s3"]},
        {"id": "s4", "bg": APP_BG, "dur": 1.1667,
         "transition": {"kind": "whip", "dur": 0.33, "dir": "up"},
         "nodes": scene_nodes["s4"]},
    ],
}

with open("docs/survey.stage.json", "w") as f:
    json.dump(stage, f, indent=1)
with open("docs/survey.anim.json", "w") as f:
    json.dump({"tracks": final_tracks}, f, indent=1)
nn = sum(len(v) for v in scene_nodes.values())
print("wrote docs/survey.{stage,anim}.json,", nn, "nodes,",
      len(final_tracks), "tracks")
