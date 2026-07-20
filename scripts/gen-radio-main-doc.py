#!/usr/bin/env python3
# reproduction of animations/radio-main (9.5s, square): screen recording of
# the Radio kinetic-typography editor playing its own comp. editor chrome
# (floating window on lit desktop, canvas, tool dock, gizmo, transport,
# pinned-playhead timeline with clips lighting active-blue) around a comp:
# 3-2-1 countdown wipes, let's go -> goooo, fade it in slider, slide it up
# toggle, wooh + cartoon alien, scale it up, SPIN IT ROUND drum, every/every
# line rolls, move them all around, hard zoom to full-bleed, scrub finale.
# ledger frame N = (N-1)/60 s. authored at 1080x1080 (source is 2160).
import json
import os

W, H = 1080, 1080
K = 0.5523

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

nodes, tracks = [], []


def rect(id, x, y, w, h, r, fill, **kw):
    n = {"id": id, "type": "rect", "x": round(x, 1), "y": round(y, 1),
         "w": round(w, 1), "h": round(h, 1), "radius": r, "fill": fill}
    n.update(kw)
    nodes.append(n)
    return n


def text(id, s, x, y, size, color, weight=700, **kw):
    n = {"id": id, "type": "text", "text": s, "x": round(x, 1),
         "y": round(y, 1), "color": color,
         "font": {"size": size, "weight": weight}}
    n.update(kw)
    nodes.append(n)
    return n


def path(id, x, y, d, fill, stroke=None, **kw):
    n = {"id": id, "type": "path", "x": round(x, 1), "y": round(y, 1),
         "d": d, "fill": fill}
    if stroke:
        n["stroke"] = stroke
    n.update(kw)
    nodes.append(n)
    return n


def track(nid, at=0.0, loop=False, **props):
    keys = {}
    for name, seq in props.items():
        out = []
        for k in seq:
            kk = {"t": round(k[0], 3), "v": k[1]}
            if len(k) > 2 and k[2]:
                kk["ease"] = k[2]
            out.append(kk)
        keys[name] = out
    t = {"target": nid, "keys": keys}
    if at:
        t["at"] = at
    if loop:
        t["loop"] = True
    tracks.append(t)


def state_at(nid, t, name):
    tracks.append({"target": nid, "at": round(t, 3), "state": name})


def windows(nid, wins):
    ks = []
    if wins[0][0] > 0.01:
        ks.append((0, 0))
    for a, b in wins:
        ks += [(a - 0.02, 0), (a, 1), (b, 1), (b + 0.04, 0)]
    track(nid, opacity=ks)


def circle_d(r, cx=0, cy=0):
    k = r * K
    return (f"M{cx-r:.1f} {cy}C{cx-r:.1f} {cy-k:.1f} {cx-k:.1f} {cy-r:.1f} {cx} {cy-r:.1f}"
            f"C{cx+k:.1f} {cy-r:.1f} {cx+r:.1f} {cy-k:.1f} {cx+r:.1f} {cy}"
            f"C{cx+r:.1f} {cy+k:.1f} {cx+k:.1f} {cy+r:.1f} {cx} {cy+r:.1f}"
            f"C{cx-k:.1f} {cy+r:.1f} {cx-r:.1f} {cy+k:.1f} {cx-r:.1f} {cy}Z")


def ellipse_d(rx, ry, cx=0, cy=0, rev=False):
    kx, ky = rx * K, ry * K
    if not rev:
        return (f"M{cx-rx:.1f} {cy}C{cx-rx:.1f} {cy-ky:.1f} {cx-kx:.1f} {cy-ry:.1f} {cx} {cy-ry:.1f}"
                f"C{cx+kx:.1f} {cy-ry:.1f} {cx+rx:.1f} {cy-ky:.1f} {cx+rx:.1f} {cy}"
                f"C{cx+rx:.1f} {cy+ky:.1f} {cx+kx:.1f} {cy+ry:.1f} {cx} {cy+ry:.1f}"
                f"C{cx-kx:.1f} {cy+ry:.1f} {cx-rx:.1f} {cy+ky:.1f} {cx-rx:.1f} {cy}Z")
    return (f"M{cx-rx:.1f} {cy}C{cx-rx:.1f} {cy+ky:.1f} {cx-kx:.1f} {cy+ry:.1f} {cx} {cy+ry:.1f}"
            f"C{cx+kx:.1f} {cy+ry:.1f} {cx+rx:.1f} {cy+ky:.1f} {cx+rx:.1f} {cy}"
            f"C{cx+rx:.1f} {cy-ky:.1f} {cx+kx:.1f} {cy-ry:.1f} {cx} {cy-ry:.1f}"
            f"C{cx-kx:.1f} {cy-ry:.1f} {cx-rx:.1f} {cy-ky:.1f} {cx-rx:.1f} {cy}Z")


def ring_d(rx, ry, th):
    return ellipse_d(rx, ry) + ellipse_d(rx - th, ry - th * 1.6, rev=True)


# ------------------------------------------------------------ geometry
CX, CY = 521, 320            # canvas center
CV_L, CV_R, CV_T, CV_B = 40, 1002, 92, 548
PPS = 104                    # timeline px per second (static phase)
SCROLL_END = 2.5
SCROLL_PX = 230


def xb(T):
    # base x of ruler time T (before the phase-1 scroll track shifts -230)
    return 69 + (T - 2) * PPS + SCROLL_PX


scroll_ids = []   # nodes that ride the phase-1 horizontal scroll
vroll_ids = []    # clip rows that ride the vertical track scroll

# ------------------------------------------------------------ desktop
rect("desk", 540, 540, 1082, 1082, 0, "#3a3a3a",
     gradient={"angle": 135, "stops": [
         {"at": 0.0, "color": "#cac6c7"}, {"at": 0.38, "color": "#767475"},
         {"at": 1.0, "color": "#262626"}]})
rect("win_rim", 524, 522, 988, 876, 26, "#4a4a4a")
rect("win", 524, 522, 984, 872, 24, "#111111")

# ------------------------------------------------------------ canvas bg
cbg = rect("canvas_bg", CX, CY, 962, 456, 6, "#c2c2c2",
           states={"black": {"fill": "#060606"},
                   "white": {"fill": "#ffffff"},
                   "grey": {"fill": "#c2c2c2"}})
for t, s in [(0.40, "black"), (0.96, "grey"), (1.53, "black"),
             (3.12, "white"), (3.50, "grey"), (4.28, "black"),
             (4.70, "grey"), (5.81, "black"), (6.90, "grey")]:
    state_at("canvas_bg", t, s)

# ------------------------------------------------------------ comp: wipes


def wipe(id, fill, t0, t1, anchor):
    # rect that grows across the canvas with one edge pinned
    if anchor == "left":
        n = rect(id, CV_L + 1, CY, 2, 456, 0, fill)
        track(id, w=[(t0, 2), (t1, 964, "outCubic")],
              x=[(t0, 0), (t1, 481, "outCubic")])
    else:
        n = rect(id, CV_R - 1, CY, 2, 456, 0, fill)
        track(id, w=[(t0, 2), (t1, 964, "outCubic")],
              x=[(t0, 0), (t1, -481, "outCubic")])
    windows(id, [(t0 - 0.01, t1 + 0.03)])
    return n


wipe("wipeA", "#060606", 0.28, 0.42, "left")
wipe("wipeB", "#c2c2c2", 0.85, 0.97, "left")
wipe("wipeC", "#060606", 1.42, 1.54, "left")
wipe("wipeW", "#ffffff", 2.92, 3.13, "right")

# ------------------------------------------------------------ countdown
text("n3", "3", CX, 338, 440, "#c6c6c6", 900)
track("n3", scale=[(0.36, 1.22), (0.56, 1.0, "outCubic")])
windows("n3", [(0.36, 0.96)])

text("n2", "2", CX, 338, 440, "#101010", 900)
track("n2", scale=[(0.94, 1.22), (1.13, 1.0, "outCubic")])
windows("n2", [(0.94, 1.54)])
path("gh3_band", CX, 366, "M-140 -46L140 -46L140 46L-140 46Z", "#060606",
     rot=-14)
text("gh3", "3", CX, 366, 52, "#c2c2c2", 800)
for nid in ("gh3_band", "gh3"):
    windows(nid, [(0.96, 1.24)])

text("n1", "1", CX, 338, 440, "#c6c6c6", 900)
track("n1",
      scale=[(1.50, 1.22), (1.69, 1.0, "outCubic"), (1.90, 1.0),
             (2.06, 0.26, "inCubic")],
      x=[(1.90, 0), (2.06, -90, "outCubic")])
windows("n1", [(1.50, 2.10)])
text("gh2", "2", CX, 366, 52, "#9a9a9a", 800)
windows("gh2", [(1.56, 1.84)])

# ------------------------------------------------------------ let's go(oo)
text("w_lets", "let's", 385, 320, 105, "#9a9a9a", 800)
track("w_lets", y=[(1.98, 30), (2.16, 0, "outCubic")],
      scale=[(2.50, 1.0), (2.64, 2.1, "inCubic")])
windows("w_lets", [(1.98, 2.60)])
text("w_go", "go", 565, 320, 105, "#d9d9d9", 800)
track("w_go", y=[(2.10, 26), (2.26, 0, "outCubic")],
      scale=[(2.50, 1.0), (2.64, 2.3, "inCubic")])
windows("w_go", [(2.10, 2.60)])

OVALS = [(120, 90, "#262626"), (235, 120, "#323232"), (352, 155, "#3f3f3f"),
         (472, 195, "#585858"), (595, 240, "#7c7c7c"),
         (725, 290, "#adadad"), (868, 200, "#dedede")]
for i, (ox, ry, col) in enumerate(OVALS):
    rx = max(28, ry * 0.34)
    path(f"oval{i}", ox, 320, ring_d(rx, ry, max(14, rx * 0.55)), col)
    t0 = 2.48 + (6 - i) * 0.05
    track(f"oval{i}", scale=[(t0, 0.5), (t0 + 0.18, 1.0, "outCubic")])
    windows(f"oval{i}", [(t0, 3.18)])

# ------------------------------------------------------------ fade it in
text("t_fade", "fade it in", CX, 298, 82, "#141414", 800)
tracks.append({"target": "t_fade", "at": 3.08,
               "reveal": {"unit": "word", "stagger": 0.05, "dur": 0.18,
                          "rise": 26, "accent": "#141414"}})
windows("t_fade", [(3.08, 3.52)])
rect("sl_line", 469, 352, 266, 5, 2.5, "#606de0")
rect("sl_thumb", 339, 352, 22, 22, 11, "#ffffff",
     glow={"sigma": 5, "opacity": 0.35, "color": "#555555", "dy": 2})
track("sl_thumb", x=[(3.12, 0), (3.34, 262, "outCubic")])
for nid in ("sl_line", "sl_thumb"):
    windows(nid, [(3.10, 3.52)])

# ------------------------------------------------------------ slide it up
# window 1 is the comp scene, window 2 the full-bleed scrub finale
SW1, SW2 = (3.48, 4.26), (8.52, 9.5)
rect("tog_pill", 320, 320, 40, 64, 20, "#613ff3")
rect("tog_knob", 320, 336, 30, 30, 15, "#ffffff")
track("tog_knob",
      y=[(3.55, 0), (3.90, -32, "outCubic"), (8.515, -32), (8.53, 0),
         (8.95, -32, "outCubic")])
windows("tog_pill", [SW1, SW2])
windows("tog_knob", [SW1, SW2])

text("s_slide", "slide", 480, 320, 82, "#141414", 800)
track("s_slide", y=[(3.52, -46), (3.82, 0, "outCubic"), (8.515, 0),
                    (8.53, -46), (8.84, 0, "outCubic")])
windows("s_slide", [SW1, SW2])
text("s_it", "it", 616, 320, 82, "#141414", 800, rot=7)
track("s_it", y=[(3.58, -40), (3.88, 0, "outCubic"), (8.515, 0),
                 (8.59, -40), (8.90, 0, "outCubic")])
windows("s_it", [SW1, SW2])
text("s_up_g", "up", 700, 322, 82, "#a9a9a9", 800, rot=-6)
windows("s_up_g", [(3.60, 4.06), (8.60, 8.99)])
text("s_up_b", "up", 700, 320, 82, "#141414", 800)
windows("s_up_b", [(4.04, 4.26), (8.97, 9.5)])
text("s_gh1", "slide", 480, 262, 82, "#b7b7b7", 800)
track("s_gh1", y=[(3.52, 0), (3.95, 26, "outCubic"), (8.515, 0), (8.53, 0),
                  (8.96, 26, "outCubic")])
windows("s_gh1", [(3.52, 3.96), (8.53, 8.97)])
text("s_gh2", "slide", 480, 230, 82, "#d2d2d2", 800)
windows("s_gh2", [(3.52, 3.84), (8.53, 8.85)])
text("s_gh3", "it up", 660, 268, 82, "#c4c4c4", 800)
windows("s_gh3", [(3.58, 3.98), (8.59, 8.99)])

# ------------------------------------------------------------ wooh + alien
text("t_wooh", "wooh!", CX, 330, 300, "#c2c2c2", 900, rot=-3)
track("t_wooh", scale=[(4.28, 1.16), (4.44, 1.0, "outCubic")])
windows("t_wooh", [(4.28, 4.70)])

AX, AY = 815, 448
path("al_head", AX, AY, ellipse_d(70, 80), "#ccd4d1")
path("al_eye_l", AX - 29, AY - 8, ellipse_d(20, 31), "#0c0c0c", rot=18)
path("al_eye_r", AX + 29, AY - 8, ellipse_d(20, 31), "#0c0c0c", rot=-18)
path("al_sp_l", AX - 36, AY - 20, circle_d(4.5), "#e8eeec")
path("al_sp_r", AX + 22, AY - 20, circle_d(4.5), "#e8eeec")
path("al_mouth", AX, AY + 44, "M-10 0C-3 6 3 6 10 0", "#2a2f2d", stroke=3.0)
for nid in ("al_head", "al_eye_l", "al_eye_r", "al_sp_l", "al_sp_r",
            "al_mouth"):
    windows(nid, [(4.32, 4.70)])
    track(nid, y=[(4.32, -70), (4.52, 0, "outCubic")])
track("al_head", at=4.32, loop=True,
      rot=[(0, -6), (0.4, 6, "inOutCubic"), (0.8, -6, "inOutCubic")])

# ------------------------------------------------------------ scale it up
SA = (521, 318)
sc_members = []


def sc(n, gx, gy):
    sc_members.append((n["id"], gx, gy))
    return n


sc(text("sc_scale", "scale", 521, 245, 130, "#141414", 800), 0, -73)
sc(text("sc_it", "it", 448, 382, 130, "#141414", 800), -73, 64)
sc(text("sc_up", "up", 618, 384, 130, "#b9b9b9", 800), 97, 66)
bw, bh = 700, 330
sc(path("sc_box", 521, 318,
        f"M{-bw/2} {-bh/2}L{bw/2} {-bh/2}L{bw/2} {bh/2}L{-bw/2} {bh/2}Z",
        "#606de0", stroke=2.0), 0, 0)
for i, (hx, hy) in enumerate([(-bw/2, -bh/2), (bw/2, -bh/2),
                              (bw/2, bh/2), (-bw/2, bh/2)]):
    sc(rect(f"sc_h{i}", 521 + hx, 318 + hy, 10, 10, 2, "#606de0"), hx, hy)
for nid, gx, gy in sc_members:
    track(nid,
          scale=[(4.72, 0.55), (5.18, 1.0, "outCubic")],
          x=[(4.72, round(gx * -0.45, 1)), (5.18, 0, "outCubic")],
          y=[(4.72, round(gy * -0.45, 1)), (5.18, 0, "outCubic")])
    windows(nid, [(4.70, 5.28)])
nodes.append({"id": "sc_cur", "type": "cursor", "x": 878, "y": 158, "w": 24,
              "fill": "#111111"})
track("sc_cur", x=[(4.72, -160), (5.18, 0, "outCubic"), (5.26, 6)],
      y=[(4.72, 72), (5.18, 0, "outCubic"), (5.26, -3)])
windows("sc_cur", [(4.70, 5.28)])

# ------------------------------------------------------------ spin drum
SPIN_W = [(5.28, 5.80), (7.60, 8.52)]
SPIN_ROWS = [("T ROUND SPIN", 168), ("D SPIN IT RO", 262),
             ("IT ROUND SP", 356), ("ND SPIN IT", 450)]
for i, (s, y) in enumerate(SPIN_ROWS):
    text(f"spin_g{i}", "SPIN IT ROUND", CX, y + 47, 78, "#b8b8b8", 900)
    track(f"spin_g{i}", at=5.28, loop=True,
          x=[(0, 38 * (1 if i % 2 else -1)),
             (0.575, -38 * (1 if i % 2 else -1), "inOutCubic"),
             (1.15, 38 * (1 if i % 2 else -1), "inOutCubic")])
    windows(f"spin_g{i}", [SPIN_W[0], SPIN_W[1]])
for i, (s, y) in enumerate(SPIN_ROWS):
    text(f"spin_r{i}", s, CX, y, 92, "#161616", 900)
    amp = 52 * (1 if i % 2 == 0 else -1)
    track(f"spin_r{i}", at=5.28, loop=True,
          x=[(0, -amp), (0.575, amp, "inOutCubic"),
             (1.15, -amp, "inOutCubic")])
    windows(f"spin_r{i}", [SPIN_W[0], SPIN_W[1]])
nodes.append({"id": "spin_cur", "type": "cursor", "x": 640, "y": 430,
              "w": 26, "fill": "#111111"})
track("spin_cur", x=[(7.7, 0), (8.1, -60, "inOutCubic"), (8.45, 30, "inOutCubic")],
      y=[(7.7, 0), (8.1, 40, "inOutCubic"), (8.45, -10, "inOutCubic")])
windows("spin_cur", [(7.62, 8.50)])

# ------------------------------------------------------------ every rolls
text("ev_one", "every", CX, 320, 110, "#f2f2f2", 900)
track("ev_one", x=[(5.98, 0), (6.08, -108, "outCubic")])
windows("ev_one", [(5.80, 6.19)])
text("ev_word", "word", 700, 320, 110, "#f2f2f2", 900)
windows("ev_word", [(6.02, 6.19)])

EV_COLS = ["#4a4a4a", "#7a7a7a", "#ababab", "#ffffff", "#c4c4c4",
           "#8a8a8a", "#5a5a5a"]
LN_COLS = ["#6a6a6a", "#9a9a9a", "#cccccc", "#ffffff", "#d4d4d4",
           "#a0a0a0", "#707070"]
for i in range(7):
    y = 320 + (i - 3) * 64
    text(f"ev_r{i}", "every", CX, y, 84, EV_COLS[i], 900)
    track(f"ev_r{i}",
          x=[(6.18, 0), (6.48, 0), (6.56, -155, "outCubic")])
    track(f"ev_r{i}", at=6.18, loop=True, y=[(0, 30), (0.55, -30)])
    windows(f"ev_r{i}", [(6.18, 6.88)])
    text(f"ln_r{i}", "line", CX + 155, y, 84, LN_COLS[i], 900)
    track(f"ln_r{i}", at=6.18, loop=True, y=[(0, 30), (0.55, -30)])
    windows(f"ln_r{i}", [(6.48, 6.88)])

# ------------------------------------------------------------ move around
text("mv_move", "move", 405, 288, 88, "#141414", 800)
track("mv_move", x=[(6.92, -120), (7.18, 0, "outCubic")])
windows("mv_move", [(6.92, 7.585)])
text("mv_them", "them", 665, 288, 88, "#141414", 800)
track("mv_them", x=[(6.95, 150), (7.25, 0, "outCubic")],
      y=[(6.95, 110), (7.25, 0, "outCubic")])
windows("mv_them", [(6.95, 7.585)])
text("mv_all", "all", 408, 352, 88, "#141414", 800)
track("mv_all", x=[(7.00, -170), (7.30, 0, "outCubic")],
      y=[(7.00, 180), (7.30, 0, "outCubic")])
windows("mv_all", [(7.00, 7.585)])
text("mv_around", "around", 622, 352, 88, "#141414", 800)
track("mv_around", x=[(7.05, 90), (7.42, 0, "outCubic")],
      y=[(7.05, 330), (7.42, 0, "outCubic")])
windows("mv_around", [(7.05, 7.585)])


def sel_box(id, x, y, w, h, wins):
    path(id, x, y, f"M{-w/2} {-h/2}L{w/2} {-h/2}L{w/2} {h/2}L{-w/2} {h/2}Z",
         "#606de0", stroke=1.8)
    for j, (hx, hy) in enumerate([(-w/2, -h/2), (w/2, -h/2), (w/2, h/2),
                                  (-w/2, h/2)]):
        rect(f"{id}_h{j}", x + hx, y + hy, 8, 8, 2, "#606de0")
        windows(f"{id}_h{j}", wins)
    windows(id, wins)


sel_box("box_them", 665, 288, 220, 92, [(7.15, 7.36)])
sel_box("box_all", 408, 352, 150, 84, [(7.25, 7.46)])
sel_box("box_around", 622, 352, 280, 92, [(7.30, 7.585)])
nodes.append({"id": "mv_cur1", "type": "cursor", "x": 764, "y": 330,
              "w": 24, "fill": "#111111"})
track("mv_cur1", x=[(7.0, 96), (7.3, 0, "outCubic")],
      y=[(7.0, 100), (7.3, 0, "outCubic")])
windows("mv_cur1", [(6.98, 7.38)])
nodes.append({"id": "mv_cur2", "type": "cursor", "x": 768, "y": 396,
              "w": 24, "fill": "#111111"})
track("mv_cur2", x=[(7.1, 130), (7.5, 0, "outCubic")],
      y=[(7.1, 170), (7.5, 0, "outCubic")])
windows("mv_cur2", [(7.08, 7.585)])

# ------------------------------------------------------------ chrome masks
rect("mask_tl", 524, 753, 984, 410, 24, "#111111")
rect("mask_tl2", 524, 574, 976, 52, 0, "#111111")
rect("mask_l", 36, 320, 8, 456, 0, "#111111")
rect("mask_r", 1009, 320, 14, 456, 0, "#111111")
rect("mask_t", 524, 89, 984, 6, 0, "#111111")

# ------------------------------------------------------------ timeline
for gi in range(11):
    n = rect(f"grid{gi}", xb(gi), 782, 1, 336, 0, "#1d1d1d")
    scroll_ids.append(n["id"])
for gi in range(11):
    n = text(f"rul{gi}", f"{gi}.00", xb(gi), 606, 12, "#9a9a9a", 500)
    scroll_ids.append(n["id"])
n = rect("end_chip", xb(9.0), 606, 12, 15, 3, "#3d4370")
scroll_ids.append("end_chip")

CLIPS = [
    ("3", 0.00, 1.61), ("2", 0.00, 2.39), ("1", 0.00, 3.12),
    ("lets", 2.31, 4.35), ("go", 2.52, 4.66), ("BG", 2.52, 4.66),
    ("fade it in", 2.52, 3.91), ("Slider", 2.52, 3.92),
    ("Switch", 3.47, 6.05), ("slide it up", 3.47, 6.05),
    ("Bg 2", 4.62, 5.66), ("Alien", 4.62, 5.68),
    ("Instance 13", 4.66, 5.64), ("Bright BG", 5.03, 6.22),
    ("Scale it up", 5.03, 5.94), ("Cursor", 5.03, 5.94),
    ("Scale Rect", 5.03, 5.94), ("Spin Text", 5.32, 6.26),
    ("Black bg", 6.20, 7.37), ("ev...", 6.20, 6.56), ("", 6.34, 6.57),
    ("every", 6.56, 7.37), ("line", 6.83, 7.37),
    ("Bg", 6.91, 9.09), ("Cursor ...", 6.91, 7.50), ("move", 6.91, 9.09),
    ("Cursor (t...", 6.91, 7.58), ("them", 6.91, 9.09),
    ("Cursor (all)", 6.91, 7.69), ("all", 6.91, 9.09),
    ("Cursor (around)", 6.91, 8.02), ("around", 6.91, 9.09),
]

VKEYS = [(2.5, 0), (4.5, -110), (5.0, -167), (5.5, -180), (6.2, -340),
         (6.7, -460), (7.2, -480), (7.3, -500)]


def v_at(t):
    if t <= VKEYS[0][0]:
        return 0
    for (t0, v0), (t1, v1) in zip(VKEYS, VKEYS[1:]):
        if t <= t1:
            return v0 + (v1 - v0) * (t - t0) / (t1 - t0)
    return VKEYS[-1][1]


def v_cross(vth):
    # when the vertical scroll passes vth (vth negative)
    if vth >= 0:
        return None
    for (t0, v0), (t1, v1) in zip(VKEYS, VKEYS[1:]):
        if v1 <= vth < v0:
            return t0 + (t1 - t0) * (vth - v0) / (v1 - v0)
    return None


def fade_time(i):
    # when row i scrolls under the transport band
    return v_cross(-(7 + 25.4 * i))


def enter_time(i):
    # when row i scrolls up into the viewport from below the lanes
    return v_cross(266 - 25.4 * i)


for i, (name, s, e) in enumerate(CLIPS):
    y = 629 + 25.4 * i
    w = (e - s) * PPS
    cx = (xb(s) + xb(e)) / 2
    pid = f"clip{i}"
    rect(pid, cx, y, w, 20, 10, "#232323",
         states={"on": {"fill": "#606de0"}, "off": {"fill": "#232323"}})
    ids = [pid]
    if name:
        lw = len(name) * 11 * 0.55
        path(f"{pid}_tri", xb(s) + 13, y, "M-2.5 -4L3.5 0L-2.5 4Z",
             "#cfcfcf")
        text(f"{pid}_lb", name, xb(s) + 24 + lw / 2, y, 11, "#e8e8e8", 500)
        ids += [f"{pid}_tri", f"{pid}_lb"]
    a0, a1 = max(0.0, s - 0.37), e - 0.37
    if a1 > 0.05:
        state_at(pid, a0, "on")
        state_at(pid, a1, "off")
    ft = fade_time(i)
    et = enter_time(i)
    ks = []
    if et:
        ks += [(0, 0), (et - 0.03, 0), (et + 0.05, 1)]
    if ft:
        if not ks:
            ks.append((0, 1))
        ks += [(ft - 0.06, 1), (ft + 0.04, 0)]
    for nid in ids:
        scroll_ids.append(nid)
        vroll_ids.append(nid)
        if ks:
            track(nid, opacity=list(ks))

# orange keyframe lane + diamonds
n = rect("kf_lane", (xb(0) + xb(7.55)) / 2, 907, 7.55 * PPS, 7, 3,
         "#cf7030")
scroll_ids.append("kf_lane")
DIA = [0.5, 2.2, 2.45, 2.6, 3.0, 3.35, 3.5, 3.75, 4.3, 4.5, 4.65, 4.9,
       5.1, 5.35, 5.55, 5.8, 6.15, 6.5, 6.8, 7.05, 7.3, 7.52]
for i, T in enumerate(DIA):
    n = rect(f"dia{i}", xb(T), 907, 7, 7, 1, "#ffffff", rot=45)
    scroll_ids.append(n["id"])

# green audio waveform
n = rect("wave", (xb(0) + xb(8.9)) / 2, 937, 8.9 * PPS, 16, 8, "#0f8b40")
scroll_ids.append("wave")
import random
random.seed(7)
for i in range(44):
    T = 0.1 + i * 0.2
    hgt = 4 + (i * 37 % 9)
    col = "#0b6e33" if i % 3 else "#14a852"
    n = rect(f"wb{i}", xb(T), 937, 3, hgt, 1, col)
    scroll_ids.append(n["id"])

for nid in scroll_ids:
    track(nid, x=[(0, 0), (SCROLL_END, -SCROLL_PX)])
for nid in vroll_ids:
    track(nid, y=list(VKEYS))

# playhead (pinned during scroll, then travels, then scrubbed)
rect("playhead", 129, 775, 2.5, 340, 1, "#5560d8")
track("playhead",
      x=[(0, 0), (2.5, 30), (7.583, 561), (7.66, 322, "outCubic"),
         (8.50, 401), (8.62, 176, "outCubic"), (9.5, 239)])

# desktop strips over the timeline overflow left/right/below the window
rect("strip_l", 16, 540, 32, 1082, 0, "#232323",
     gradient={"angle": 90, "stops": [
         {"at": 0.0, "color": "#4c4a4b"}, {"at": 1.0, "color": "#1c1c1c"}]})
rect("strip_r", 1048, 540, 64, 1082, 0, "#8a8888",
     gradient={"angle": 90, "stops": [
         {"at": 0.0, "color": "#cac6c7"}, {"at": 1.0, "color": "#4a4a4a"}]})
rect("strip_b", 540, 1019, 1082, 122, 0, "#3a3a3a",
     gradient={"angle": 0, "stops": [
         {"at": 0.0, "color": "#181818"}, {"at": 1.0, "color": "#565454"}]})

# ------------------------------------------------------------ transport
rect("tp_pause", 65, 576, 26, 26, 7, "#1c1c1c")
rect("tp_b1", 61, 576, 3, 11, 1, "#e8e8e8")
rect("tp_b2", 69, 576, 3, 11, 1, "#e8e8e8")
rect("tp_spk", 618, 576, 30, 22, 6, "#262647")
path("tp_spk_g", 616, 576, "M-5 -3L-1 -3L4 -7L4 7L-1 3L-5 3Z", "#aeb4ff")
rect("tp_ai", 655, 576, 30, 22, 6, "#262647")
path("tp_ai_g", 655, 576, "M0 -7L2 -2L7 0L2 2L0 7L-2 2L-7 0L-2 -2Z",
     "#aeb4ff")
rect("tp_track", 742, 576, 110, 4, 2, "#f0f0f0")
rect("tp_fill", 693, 576, 12, 4, 2, "#606de0")
rect("tp_thumb", 696, 576, 14, 14, 7, "#606de0")
text("tp_start", "Start", 816, 576, 12, "#8a8a8a", 500)
rect("tp_f1", 868, 576, 56, 22, 5, "#1c1c1c")
text("tp_f1t", "0,01", 866, 576, 12, "#d0d0d0", 500)
text("tp_end", "End", 916, 576, 12, "#8a8a8a", 500)
rect("tp_f2", 966, 576, 56, 22, 5, "#1c1c1c")
text("tp_f2t", "8,90", 964, 576, 12, "#d0d0d0", 500)

# ------------------------------------------------------------ float chrome
rect("bt1", 63, 117, 24, 24, 7, "#232323")
path("bt1_g", 63, 117,
     "M-4 6C-6 2 -6 -2 -5 -4M-2 -6L-2 2M1 -6L1 2M4 -4L4 3C4 6 1 8 -2 8",
     "#d5d5d5", stroke=1.4)
rect("bt2", 94, 117, 30, 24, 7, "#3c3c3e")
path("bt2_g", 94, 117,
     "M-8 -4L1 -4C2 -4 2 -3 2 0C2 3 2 4 1 4L-8 4C-9 4 -9 -4 -8 -4ZM4 -1L8 -4L8 4L4 1",
     "#f0f0f0", stroke=1.4)
rect("bt3", 128, 118, 24, 24, 7, "#232323")
path("bt3_g", 128, 118, "M-5 -5L5 -5L5 5L-5 5ZM0 -5L0 5M-5 0L5 0",
     "#d5d5d5", stroke=1.3)

# gizmo disc
rect("gz_disc", 960, 142, 70, 70, 35, "#141414")
path("gz_arm_v", 960, 131, "M0 11L0 -11", "#b0b0b0", stroke=2.0)
path("gz_arm_h", 969, 142, "M-9 0L9 0", "#b0b0b0", stroke=2.0)
path("gz_top", 960, 120, circle_d(4.5), "#35c46b")
path("gz_bot", 960, 163, circle_d(4), "#35c46b")
path("gz_right", 978, 142, circle_d(4.5), "#e0447c")
path("gz_left", 942, 141, circle_d(4), "#cf4040")
path("gz_mid", 960, 142, circle_d(5), "#5a7df0")

# tool dock
rect("dock", 521, 511, 200, 34, 9, "#141414",
     glow={"sigma": 10, "opacity": 0.4, "color": "#000000", "dy": 4})
rect("dock_sel", 438, 511, 26, 26, 7, "#606de0")
nodes.append({"id": "dock_cur", "type": "cursor", "x": 435, "y": 507,
              "w": 13, "fill": "#ffffff"})
path("dock_ch1", 462, 511, "M-3 -2L0 2L3 -2", "#9a9a9a", stroke=1.6)
path("dock_cube", 492, 511,
     "M0 -8L7 -4L7 4L0 8L-7 4L-7 -4ZM-7 -4L0 0L7 -4M0 0L0 8",
     "#cfcfcf", stroke=1.3)
text("dock_t", "T", 521, 511, 17, "#cfcfcf", 500)
path("dock_img", 549, 511,
     "M-8 -7L8 -7L8 7L-8 7ZM-8 3L-3 -2L2 3M3 -2L8 3", "#cfcfcf",
     stroke=1.3)
path("dock_rect", 577, 511, "M-7 -7L7 -7L7 7L-7 7Z", "#cfcfcf", stroke=1.3)
path("dock_ch2", 600, 511, "M-3 -2L0 2L3 -2", "#9a9a9a", stroke=1.6)

# ------------------------------------------------------------ camera zoom
track("s", cam_zoom=[(0, 1.0), (7.583, 1.0), (7.617, 2.2, "outCubic")],
      cam_y=[(0, 0), (7.583, 0), (7.617, -110, "outCubic")])

stage = {
    "fps": 30,
    "size": [W, H],
    "audio": {"src": "/assets/audio/pad.m4a", "gain": 0.55, "fade_out": 0.7},
    "scenes": [
        {"id": "s", "bg": "#2e2e2e", "dur": 9.5,
         "transition": {"kind": "cut"}, "nodes": nodes},
    ],
}

with open("docs/radio-main.stage.json", "w") as f:
    json.dump(stage, f, indent=1)
with open("docs/radio-main.anim.json", "w") as f:
    json.dump({"tracks": tracks}, f, indent=1)
print("wrote docs/radio-main.{stage,anim}.json,", len(nodes), "nodes,",
      len(tracks), "tracks")
