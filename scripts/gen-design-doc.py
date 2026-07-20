#!/usr/bin/env python3
# reproduction of radio/design (4.60s, 1080x1080, 60fps): the iPad text/motion
# design app demo. act A (one scene, camera-driven): editor at rest, crash zoom
# into the inspector, the 12-swatch color wheel blooms out of the swatch, the
# blue gradient sphere blooms from the wheel core. act B: hard cut to the
# messaging preview — hola/hello/bonjour typing in imessage bubbles, mirrored
# as grey ghosts in the rotated artboard frame, playhead scrubbing. act C: snap
# zoom into the keyframe curve editor, node drags reshape the bezier, snap
# zoom-out, ends mid-edit. all timings from the frame ledger (frame N at
# (N-1)/60 s).
import json
import os

W, H = 1080, 1080
F = 1 / 60
K = 0.5523

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

tracks = []


def node(nodes, id, type, x, y, **kw):
    n = {"id": id, "type": type, "x": round(x, 1), "y": round(y, 1)}
    n.update(kw)
    nodes.append(n)
    return n


def rect(nodes, id, x, y, w, h, r, fill, **kw):
    return node(nodes, id, "rect", x, y, w=round(w, 1), h=round(h, 1),
                radius=r, fill=fill, **kw)


def text(nodes, id, s, x, y, size, color, weight=600, **kw):
    return node(nodes, id, "text", x, y, text=s, color=color,
                font={"size": size, "weight": weight}, **kw)


def path(nodes, id, x, y, d, fill, **kw):
    return node(nodes, id, "path", x, y, d=d, fill=fill, **kw)


def track(nid, at=0.0, **props):
    keys = {}
    for name, seq in props.items():
        out = []
        for k in seq:
            kk = {"t": round(k[0], 4), "v": k[1]}
            if len(k) > 2:
                kk["ease"] = k[2]
            out.append(kk)
        keys[name] = out
    t = {"target": nid, "keys": keys}
    if at:
        t["at"] = at
    tracks.append(t)


def steps(pairs):
    out = []
    for tt, v in pairs:
        if out:
            out.append((round(tt - 0.001, 4), out[-1][1]))
        out.append((round(tt, 4), v))
    return out


def circle_d(r, cx=0, cy=0):
    k = r * K
    return (f"M{cx-r:.1f} {cy:.1f}C{cx-r:.1f} {cy-k:.1f} {cx-k:.1f} {cy-r:.1f} {cx:.1f} {cy-r:.1f}"
            f"C{cx+k:.1f} {cy-r:.1f} {cx+r:.1f} {cy-k:.1f} {cx+r:.1f} {cy:.1f}"
            f"C{cx+r:.1f} {cy+k:.1f} {cx+k:.1f} {cy+r:.1f} {cx:.1f} {cy+r:.1f}"
            f"C{cx-k:.1f} {cy+r:.1f} {cx-r:.1f} {cy+k:.1f} {cx-r:.1f} {cy:.1f}Z")


def rect_outline_d(hw, hh):
    return f"M{-hw} {-hh}L{hw} {-hh}L{hw} {hh}L{-hw} {hh}Z"


def checker_d(w, h, cell=16, sq=6):
    parts = []
    hw, hh = w / 2, h / 2
    ny, nx = int(h // cell), int(w // cell)
    for j in range(ny):
        for i in range(nx):
            if (i + j) % 2:
                continue
            x0 = -hw + i * cell + (cell - sq) / 2
            y0 = -hh + j * cell + (cell - sq) / 2
            parts.append(f"M{x0:.0f} {y0:.0f}L{x0+sq:.0f} {y0:.0f}"
                         f"L{x0+sq:.0f} {y0+sq:.0f}L{x0:.0f} {y0+sq:.0f}Z")
    return "".join(parts)


def blob_d(s=1.0):
    # black speech-bubble keyframe pill
    p = [(-17, -2), (-17, -13, -9, -17, 0, -17), (9, -17, 17, -13, 17, -2),
         (17, 8, 12, 14, 4, 15), (-4, 17, -12, 17, -14, 12), (-17, 8, -17, 3, -17, -2)]
    d = f"M{p[0][0]*s:.1f} {p[0][1]*s:.1f}"
    for seg in p[1:]:
        d += ("C" + " ".join(f"{v*s:.1f}" for v in seg))
    return d + "Z"


def blob_dot_d(s=1.0):
    return circle_d(5.2 * s) + f"M{-4*s:.1f} {3*s:.1f}L{-7.5*s:.1f} {7.5*s:.1f}L{-1*s:.1f} {5*s:.1f}Z"


def ribbon_d(pts, w=2.6):
    # closed thin band along a 2-segment cubic chain, so dseq morphing (which
    # closes paths) keeps it a clean single line
    o = w / 2
    up = [(x, y - o) for x, y in pts]
    dn = [(x, y + o) for x, y in pts]

    def seg(p):
        return (f"M{p[0][0]:.1f} {p[0][1]:.1f}"
                f"C{p[1][0]:.1f} {p[1][1]:.1f} {p[2][0]:.1f} {p[2][1]:.1f} {p[3][0]:.1f} {p[3][1]:.1f}"
                f"C{p[4][0]:.1f} {p[4][1]:.1f} {p[5][0]:.1f} {p[5][1]:.1f} {p[6][0]:.1f} {p[6][1]:.1f}")

    d = seg(up)
    rev = list(reversed(dn))
    d += (f"L{rev[0][0]:.1f} {rev[0][1]:.1f}"
          f"C{rev[1][0]:.1f} {rev[1][1]:.1f} {rev[2][0]:.1f} {rev[2][1]:.1f} {rev[3][0]:.1f} {rev[3][1]:.1f}"
          f"C{rev[4][0]:.1f} {rev[4][1]:.1f} {rev[5][0]:.1f} {rev[5][1]:.1f} {rev[6][0]:.1f} {rev[6][1]:.1f}Z")
    return d


def tail_d(side=1):
    # imessage bubble tail; side=1 points left, -1 points right
    pts = ("M2 -16L2 8C-4 14 -14 18 -25 17C-12 10 -6 2 -6 -16Z")
    if side == 1:
        return pts
    return "M-2 -16L-2 8C4 14 14 18 25 17C12 10 6 2 6 -16Z"


# ============================================================== scene ed
# editor at rest -> crash zoom -> color wheel bloom -> gradient sphere.
# one scene, all navigation is the camera. frames 1-98, dur 98/60.
ed = []
ED_END = 98 * F

node(ed, "e_bg", "rect", 540, 540, w=1084, h=1084, radius=0, fill="#59585e",
     gradient={"angle": 90, "stops": [
         {"at": 0.0, "color": "#535258"}, {"at": 0.06, "color": "#5d5c62"},
         {"at": 0.14, "color": "#717076"}, {"at": 0.23, "color": "#86858a"},
         {"at": 0.32, "color": "#96959a"}, {"at": 0.42, "color": "#8b8d8d"},
         {"at": 0.51, "color": "#515455"}, {"at": 0.60, "color": "#252929"},
         {"at": 0.69, "color": "#131314"}, {"at": 0.78, "color": "#050505"},
         {"at": 0.86, "color": "#000000"}, {"at": 1.0, "color": "#000000"}]})
rect(ed, "e_app", 540, 539, 920, 712, 26, "#d4d4d4")
rect(ed, "e_canvas", 538, 500, 503, 500, 6, "#ffffff")
text(ed, "e_hello", "hello", 540, 500, 156, "#1287ff", weight=800)
path(ed, "e_sel", 538.5, 497.5, rect_outline_d(205.5, 85.5), "#4a90f8",
     stroke=1.3)
for i, (hx, hy) in enumerate([(333, 412), (744, 412), (333, 583), (744, 583)]):
    rect(ed, f"e_h{i}", hx, hy, 7, 7, 1, "#1287ff")

# top bar
rect(ed, "e_plus", 301, 225, 22, 22, 7, "#dedede")
path(ed, "e_plusg", 301, 225, "M-5 0L5 0M0 -5L0 5", "#8a8a8a", stroke=1.6)
for i, tx in enumerate([706, 724, 743]):
    rect(ed, f"e_tb{i}", tx, 225, 13, 13, 3, "#c9c9c9")
rect(ed, "e_ratio", 776, 225, 26, 15, 4, "#dedede")
text(ed, "e_ratiot", "1:1", 776, 225, 8, "#777777")

# left inspector column
rect(ed, "e_lc1", 205, 394, 103, 17, 8, "#dedede")
text(ed, "e_lt1", "content", 205, 394, 10, "#8a8a8a")
rect(ed, "e_fld", 205, 424, 103, 30, 15, "#ffffff")
text(ed, "e_fldt", "hello", 205, 424, 13, "#555555")
rect(ed, "e_lc2", 205, 454, 103, 17, 8, "#dedede")
text(ed, "e_lt2", "color", 205, 454, 10, "#8a8a8a")
rect(ed, "e_ring", 205, 485, 40, 40, 20, "#ffffff")
rect(ed, "e_dot", 205, 485, 25, 25, 12.5, "#1287ff")
rect(ed, "e_lc3", 205, 514, 103, 17, 8, "#dedede")
text(ed, "e_lt3", "font", 205, 514, 10, "#8a8a8a")
rect(ed, "e_fc", 205, 570, 105, 92, 18, "#ffffff")
text(ed, "e_fct", "abc", 205, 569, 20, "#555555")
text(ed, "e_fpl", "<", 166, 570, 11, "#b8b8b8")
text(ed, "e_fpr", ">", 243, 570, 11, "#b8b8b8")

# right panel
rect(ed, "e_rc1", 870, 413, 105, 18, 9, "#dedede")
rect(ed, "e_tgl", 833, 413, 17, 11, 5, "#1287ff")
rect(ed, "e_tglk", 837, 413, 8, 8, 4, "#ffffff")
text(ed, "e_rt1", "animation", 876, 413, 8, "#777777")
rect(ed, "e_rc2", 870, 468, 100, 86, 18, "#ffffff")
text(ed, "e_rc2t", "abc", 870, 467, 20, "#555555")
text(ed, "e_rpl", "<", 836, 468, 10, "#b8b8b8")
text(ed, "e_rpr", ">", 905, 468, 10, "#b8b8b8")
rect(ed, "e_rc3", 870, 530, 105, 16, 8, "#dedede")
rect(ed, "e_rc3a", 833, 530, 12, 8, 3, "#8a8a8a")
rect(ed, "e_rc3b", 905, 530, 10, 8, 3, "#8a8a8a")
rect(ed, "e_rc4", 870, 556, 105, 15, 7, "#dedede")
rect(ed, "e_rc4d", 830, 556, 8, 8, 4, "#444444")
text(ed, "e_rt4", "camera", 873, 556, 8, "#777777")
rect(ed, "e_rc5", 870, 582, 105, 15, 7, "#dedede")
rect(ed, "e_rc5d", 830, 582, 8, 8, 4, "#444444")
text(ed, "e_rt5", "clear", 870, 582, 8, "#777777")

# bottom timeline
rect(ed, "e_tl", 539, 823, 574, 85, 20, "#fafafa")
for i in range(6):
    rect(ed, f"e_ts{i}", 380 + i * 72, 823, 36, 81, 0, "#f2f2f2")
rect(ed, "e_play", 274, 823, 34, 56, 11, "#ffffff")
path(ed, "e_playg", 271, 823, "M-6 -6L3 0L-6 6Z", "#141414")
path(ed, "e_playb", 280, 823, "M0 -6L0 6M4 -6L4 6", "#141414", stroke=2.0)
for i, tx in enumerate([419, 563, 705]):
    text(ed, f"e_tick{i}", str(i + 2), tx, 791, 8, "#b5b5b5", weight=400)
for i, (kx, ky) in enumerate([(434, 829), (478, 853), (575, 829), (649, 853)]):
    path(ed, f"e_kf{i}", kx, ky, blob_d(0.45), "#141414")
rect(ed, "e_ph", 358, 824, 2.5, 79, 1, "#ea6f34")
rect(ed, "e_phk", 358, 804, 15, 15, 7.5, "#d8da6c")
path(ed, "e_phr", 358, 804, circle_d(9), "#ea6f34", stroke=2.0)

# color wheel: blooms out of the dot f26-40. packed 14-swatch ring, muted
# designer palette, slightly right of and above the dot like the source
WCX, WCY = 210.5, 484
rect(ed, "e_disc", WCX, WCY, 127, 127, 63.5, "#ffffff",
     glow={"sigma": 5, "opacity": 0.15, "color": "#888888", "dy": 2})
track("e_disc", scale=[(24 * F, 0.0), (25 * F, 0.0), (33 * F, 1.0, "outCubic")],
      opacity=steps([(25 * F, 0), (25.5 * F, 1)]))
SWATCH = ["#b31217", "#37373a", "#eae8e5", "#6c6459", "#4a3a2c", "#5e2f96",
          "#1287f8", "#3f2bb0", "#2e7f2c", "#43a339", "#f0c14b", "#f5df9a",
          "#0a0a0a", "#a63c08"]
import math
for i, col in enumerate(SWATCH):
    a = -math.pi / 2 + i * 2 * math.pi / 14
    sx = WCX + 40 * math.cos(a)
    sy = WCY + 40 * math.sin(a)
    rect(ed, f"e_sw{i}", sx, sy, 25, 25, 12.5, col)
    t0 = (26 + i * 0.45) * F
    t1 = (34 + i * 0.45) * F
    track(f"e_sw{i}",
          x=[(t0, WCX - sx), (t1, 0, "outCubic")],
          y=[(t0, WCY - sy), (t1, 0, "outCubic")],
          scale=[(t0, 0.1), (t1, 1.0, "outCubic")],
          opacity=steps([(t0, 0), (t0 + 0.5 * F, 1)]))
rect(ed, "e_win", WCX, WCY, 34, 34, 17, "#f6f6f6")
path(ed, "e_drop", WCX, WCY,
     "M0 -6C3.4 -1.7 5.1 0.9 5.1 3.4C5.1 6.8 2.6 9.4 0 9.4"
     "C-2.6 9.4 -5.1 6.8 -5.1 3.4C-5.1 0.9 -3.4 -1.7 0 -6Z",
     "#3c3c3c")
for nid in ("e_win", "e_drop"):
    track(nid, scale=[(24 * F, 0.0), (25 * F, 0.0), (33 * F, 1.0, "outCubic")],
          opacity=steps([(25 * F, 0), (25.5 * F, 1)]))

# gradient sphere blooms in one frame at f57
rect(ed, "e_sph", 223, 524, 69, 69, 34.5, "#2b7cf0",
     gradient={"angle": 135, "stops": [
         {"at": 0.0, "color": "#72f7f4"}, {"at": 0.35, "color": "#2f8cf0"},
         {"at": 1.0, "color": "#0535df"}]},
     glow={"sigma": 8, "opacity": 0.3, "color": "#2255cc", "dy": 4})
track("e_sph", scale=[(55 * F, 0.0), (56 * F, 0.55), (58 * F, 1.0, "outCubic")],
      opacity=steps([(56 * F, 0), (56.5 * F, 1)]))
path(ed, "e_ringO", 212, 526, circle_d(3.8), "#ffffff", stroke=1.5)
track("e_ringO",
      opacity=steps([(56.5 * F, 0), (57 * F, 1)]),
      x=[(57 * F, 2), (70 * F, 0), (98 * F, -7)],
      y=[(57 * F, -3), (70 * F, 3), (98 * F, 0)])

# press ring on the color dot at f22
track("e_ring", opacity=steps([(0, 0), (21.5 * F, 1)]))

# cursor drifts from the canvas to the dot, presses, fades when sphere lands
node(ed, "e_cur", "cursor", 207.5, 499, w=26, fill="#111111")
track("e_cur",
      x=[(0, 37.5), (20 * F, 0, "outCubic")],
      y=[(0, 11), (20 * F, 0, "outCubic")],
      opacity=[(55 * F, 1), (58 * F, 0)])

# the camera: crash zoom f11-25 (blur peak f14), slow drift while the wheel
# is open, one-frame push when the sphere blooms
track("ed",
      cam_zoom=[(10 * F, 1.0), (14 * F, 1.9, "inCubic"),
                (25 * F, 2.88, "outCubic"), (56 * F, 3.46, "inOutCubic"),
                (58 * F, 5.0, "outCubic")],
      cam_x=[(10 * F, 0.0), (14 * F, -150, "inCubic"),
             (25 * F, -303, "outCubic"), (56 * F, -328.6, "inOutCubic"),
             (58 * F, -332.4, "outCubic")],
      cam_y=[(10 * F, 0.0), (14 * F, -21, "inCubic"),
             (25 * F, -42.8, "outCubic"), (56 * F, -47.5, "inOutCubic"),
             (58 * F, -50.4, "outCubic")])

# ============================================================== scene msg
# hard cut f99: full-bleed split preview. artboard + ghosts left, live
# bubbles right, scrolling keyframe track below. frames 99-196, dur 98/60.
mg = []
MG_END = 98 * F

# top bar
rect(mg, "m_plus", 107, 18, 30, 30, 9, "#e2e2e2")
path(mg, "m_plusg", 107, 18, "M-6 0L6 0M0 -6L0 6", "#8a8a8a", stroke=1.8)
rect(mg, "m_tb0", 852, 18, 26, 26, 7, "#e2e2e2")
rect(mg, "m_tb1", 881, 18, 26, 26, 7, "#e2e2e2")
rect(mg, "m_tb2", 912, 18, 26, 26, 7, "#d7e6fb")
rect(mg, "m_ratio", 968, 18, 46, 28, 8, "#e2e2e2")
text(mg, "m_ratiot", "9:16", 968, 18, 13, "#555555")

# left artboard with dot grid + rotated selection frame + ghosts
rect(mg, "m_board", 306, 453, 447, 792, 26, "#ececec")
path(mg, "m_grid", 306, 453, checker_d(440, 786), "#e2e2e2")
path(mg, "m_frame", 306, 500, rect_outline_d(125, 225), "#e0603a", stroke=1.6)
track("m_frame",
      scale=[(0, 0.68), (11 * F, 0.70), (56 * F, 1.05, "inOutCubic"),
             (91 * F, 0.92, "inOutCubic")],
      rot=[(0, -17), (11 * F, -16), (56 * F, -2, "inOutCubic"),
           (91 * F, 20, "inOutCubic")],
      x=[(0, -1), (56 * F, 18, "inOutCubic"), (91 * F, -8, "inOutCubic")],
      y=[(0, 150), (11 * F, 142), (56 * F, -17, "inOutCubic"),
         (91 * F, -26, "inOutCubic")])
rect(mg, "m_lock", 502, 823, 36, 36, 11, "#ffffff")
path(mg, "m_lockb", 502, 826, "M-7 -2L7 -2L7 10L-7 10Z", "#222222")
path(mg, "m_locks", 502, 826, "M-4 -2C-4 -12 4 -12 4 -2", "#222222", stroke=2.2)

# right live preview
rect(mg, "m_prev", 772, 453, 448, 792, 26, "#ffffff")

BLUE_G = {"angle": 90, "stops": [{"at": 0, "color": "#2e71e8"},
                                 {"at": 1, "color": "#164fd2"}]}
GREEN_G = {"angle": 90, "stops": [{"at": 0, "color": "#4fb245"},
                                  {"at": 1, "color": "#3c9834"}]}
ORANGE_G = {"angle": 90, "stops": [{"at": 0, "color": "#ef7a1a"},
                                   {"at": 1, "color": "#dd5f0c"}]}
GLOW = {"sigma": 14, "opacity": 0.3, "color": "#8a94a8", "dy": 8}

# hola (blue): typing at f99, complete ~f115, rises f122-130, gone by f151
holay = [(22 * F, 0), (31 * F, -137, "outCubic")]
holao = [(46 * F, 1), (51 * F, 0)]
rect(mg, "m_b1", 738, 547, 220, 119, 56, "#1d61da", gradient=BLUE_G, glow=GLOW)
track("m_b1", w=[(0, 150), (5 * F, 170), (16 * F, 220, "outCubic")],
      y=holay, opacity=holao)
path(mg, "m_b1t", 634, 585, tail_d(1), "#1a55d6")
track("m_b1t", x=[(0, 35), (16 * F, 0, "outCubic")], y=holay, opacity=holao)
text(mg, "m_b1x", "hola", 738, 547, 62, "#ffffff", weight=800)
track("m_b1x", y=holay, opacity=holao)
tracks.append({"target": "m_b1x", "reveal": {"unit": "type", "cadence": 0.08,
                                             "dur": 0.08}})

# hello (green): born f128 low, types f130-158, centers as hola exits
helloy = [(29 * F, 143), (50 * F, 0, "outCubic")]
hellox = [(29 * F, 33), (50 * F, 0, "outCubic")]
helloo = steps([(29 * F, 0), (29.5 * F, 1), (69 * F, 1), (74 * F, 0)])
rect(mg, "m_b2", 790, 452, 310, 140, 66, "#45a23b", gradient=GREEN_G, glow=GLOW)
track("m_b2", w=[(29 * F, 150), (40 * F, 220), (58 * F, 310, "outCubic")],
      y=helloy, x=hellox, opacity=helloo)
path(mg, "m_b2t", 931, 502, tail_d(-1), "#3c9834")
track("m_b2t", x=[(29 * F, -80), (58 * F, 0, "outCubic")], y=helloy,
      opacity=helloo)
text(mg, "m_b2x", "hello", 790, 452, 66, "#ffffff", weight=800)
track("m_b2x", y=helloy, x=hellox, opacity=helloo)
tracks.append({"target": "m_b2x", "at": 29 * F,
               "reveal": {"unit": "type", "cadence": 0.095, "dur": 0.08}})

# bonjour (orange): born f168, types f170-196, complete at the cut
bonjo = steps([(68.5 * F, 0), (69 * F, 1)])
rect(mg, "m_b3", 762, 458, 340, 118, 56, "#e66d12", gradient=ORANGE_G,
     glow=GLOW)
track("m_b3", w=[(69 * F, 150), (80 * F, 240), (97 * F, 340, "outCubic")],
      opacity=bonjo)
path(mg, "m_b3t", 600, 495, tail_d(1), "#dd5f0c")
track("m_b3t", x=[(69 * F, 95), (97 * F, 0, "outCubic")], opacity=bonjo)
text(mg, "m_b3x", "bonjour", 762, 458, 58, "#ffffff", weight=800)
track("m_b3x", opacity=bonjo)
tracks.append({"target": "m_b3x", "at": 69 * F,
               "reveal": {"unit": "type", "cadence": 0.062, "dur": 0.08}})

# grey ghost mirrors inside the artboard frame
rect(mg, "m_g1", 302, 590, 100, 52, 26, "#ababab", rot=-12)
track("m_g1", w=[(0, 70), (16 * F, 100, "outCubic")],
      y=[(0, 95), (11 * F, 93), (31 * F, -88, "outCubic")], opacity=holao)
text(mg, "m_g1x", "hola", 302, 590, 26, "#737373", weight=800, rot=-12)
track("m_g1x", y=[(0, 95), (11 * F, 93), (31 * F, -88, "outCubic")],
      opacity=holao)
tracks.append({"target": "m_g1x", "reveal": {"unit": "type", "cadence": 0.08,
                                             "dur": 0.08}})
rect(mg, "m_g2", 330, 500, 176, 82, 40, "#ababab", rot=-3)
track("m_g2", w=[(29 * F, 90), (58 * F, 176, "outCubic")],
      y=[(29 * F, 77), (50 * F, -13, "outCubic")], opacity=helloo)
text(mg, "m_g2x", "hello", 330, 500, 34, "#737373", weight=800, rot=-3)
track("m_g2x", y=[(29 * F, 77), (50 * F, -13, "outCubic")], opacity=helloo)
tracks.append({"target": "m_g2x", "at": 29 * F,
               "reveal": {"unit": "type", "cadence": 0.095, "dur": 0.08}})
rect(mg, "m_g3", 295, 477, 150, 52, 26, "#ababab", rot=-10)
track("m_g3", w=[(69 * F, 70), (97 * F, 150, "outCubic")], opacity=bonjo)
text(mg, "m_g3x", "bonjour", 295, 477, 26, "#737373", weight=800, rot=-10)
track("m_g3x", opacity=bonjo)
tracks.append({"target": "m_g3x", "at": 69 * F,
               "reveal": {"unit": "type", "cadence": 0.062, "dur": 0.08}})

# bottom keyframe timeline: pinned playhead, content scrolls left 226 px/s
rect(mg, "m_tl", 540, 963, 900, 134, 26, "#fdfdfd")
scroll = []
for i, sx in enumerate([434, 660, 886, 1112, 1338]):
    scroll.append(rect(mg, f"m_st{i}", sx + 56.5, 963, 113, 128, 0, "#f7f7f7"))
for i in range(5):
    scroll.append(text(mg, f"m_mk{i}", str(i + 1), 321 + i * 226, 903, 13,
                       "#a8a8a8", weight=400))
conns = [("m_l1", 352, 972, 98), ("m_l2", 497, 1011, 75),
         ("m_l3", 650, 933, 71), ("m_l4", 766, 1011, 54)]
for cid, cx, cy, hw in conns:
    scroll.append(path(mg, cid, cx, cy, f"M{-hw} 0L{hw} 0", "#c9c9c9",
                       stroke=2.0))
blobs = [("m_n0", 254, 973, "#d8da6c", None),
         ("m_n1", 450, 972, "#141414", 0.863),
         ("m_n2", 422, 1011, "#141414", 0.740),
         ("m_n3", 579, 933, "#141414", 1.433),
         ("m_n4", 721, 933, "#141414", None),
         ("m_n5", 572, 1011, "#141414", 1.402),
         ("m_n6", 712, 1011, "#141414", None),
         ("m_n7", 820, 1011, "#141414", None)]
for bid, bx, by, col, lit in blobs:
    scroll.append(path(mg, bid, bx, by, blob_d(1.0), col))
    if lit is not None:
        # state fill flips only work on rects, so light the pill olive with
        # an overlay path faded in as the playhead crosses it
        ov = path(mg, bid + "o", bx, by, blob_d(1.0), "#d8da6c")
        track(bid + "o", opacity=steps([(0, 0), (round(lit, 3), 1)]))
        scroll.append(ov)
    scroll.append(path(mg, bid + "d", bx, by, blob_dot_d(1.0), "#8a8a8a"))
chip = rect(mg, "m_chip", 838, 972, 26, 26, 8, "#1c1c1c")
scroll.append(chip)
scroll.append(path(mg, "m_chipg", 838, 972,
                   "M-5 -5L-2 -5M-5 -5L-5 -2M5 5L2 5M5 5L5 2"
                   "M5 -5L2 -5M5 -5L5 -2M-5 5L-2 5M-5 5L-5 -2",
                   "#ffffff", stroke=1.4))
for n in scroll:
    track(n["id"], x=[(0, 0), (MG_END, -226 * MG_END)])
rect(mg, "m_ph", 255, 963, 4, 122, 2, "#ea6f34")
rect(mg, "m_play", 123, 963, 58, 120, 26, "#ffffff")
path(mg, "m_playg", 119, 963, "M-7 -8L4 0L-7 8Z", "#1c1c1c")
path(mg, "m_playb", 129, 963, "M0 -8L0 8M5 -8L5 8", "#1c1c1c", stroke=2.4)

# ============================================================== scene cv
# snap zoom into the curve editor f197 (authored wide, camera panned right
# for the tight phase), snap out f228, node drags reshape the curve, hold.
cv = []
CV_END = 80 * F
SNAP = 31 * F

rect(cv, "c_board", 20, 318, 320, 795, 26, "#ececec")
path(cv, "c_grid", 20, 318, checker_d(314, 790), "#e2e2e2")
rect(cv, "c_prev", 563, 313, 706, 806, 26, "#ffffff")
rect(cv, "c_lock", 135, 675, 44, 44, 13, "#ffffff")
path(cv, "c_lockb", 135, 679, "M-8 -2L8 -2L8 12L-8 12Z", "#1c1c1c")
path(cv, "c_locks", 135, 679, "M-4 -2C-4 -13 6 -15 9 -7", "#1c1c1c",
     stroke=2.2)

rect(cv, "c_tl", 330, 900, 1160, 220, 26, "#fcfcfc")
for i in range(6):
    rect(cv, f"c_st{i}", -110 + i * 188, 900, 94, 214, 0, "#f6f6f6")
path(cv, "c_row1", 330, 868, "M-580 0L580 0", "#efefef", stroke=1.2)
path(cv, "c_row2", 330, 940, "M-580 0L580 0", "#efefef", stroke=1.2)
text(cv, "c_mk0", "0", -244, 803, 14, "#a8a8a8", weight=400)
for i, mx in enumerate([131, 507, 882]):
    text(cv, f"c_mk{i+1}", str(i + 1), mx, 803, 14, "#a8a8a8", weight=400)

# playhead parked at the 0 mark (only visible while zoomed in)
rect(cv, "c_ph", -253, 895, 14, 200, 7, "#ea6f34")
rect(cv, "c_phk", -253, 905, 10, 24, 4, "#1c1c1c")

# connectors (under the nodes)
path(cv, "c_cAB", 130, 849,
     "M0 0C70 8 120 30 150 45C180 58 200 62 215 62", "#b9b9b9", stroke=2.4)
cd1 = ribbon_d([(0, 0), (45, 10), (70, 60), (85, 90), (100, 120), (118, 140),
                (135, 145)])
cd2 = ribbon_d([(-49, 19), (0, 30), (40, 80), (60, 105), (85, 132), (115, 143),
                (135, 145)])
node(cv, "c_cCD", "path", 410, 830, fill="#b9b9b9", dseq=[
    {"at": 0.0, "d": cd1},
    {"at": round(8 * F, 3), "d": cd1},
    {"at": round(20 * F, 3), "d": cd2}])
eg1 = ribbon_d([(0, 0), (40, -10), (80, -30), (105, -40), (120, -46),
                (135, -52), (145, -56)])
eg2 = ribbon_d([(0, 70), (35, 45), (70, -10), (95, -35), (110, -48),
                (130, -54), (145, -56)])
node(cv, "c_cEG", "path", 650, 905, fill="#b9b9b9", dseq=[
    {"at": 0.0, "d": eg1},
    {"at": round(35 * F, 3), "d": eg1},
    {"at": round(53 * F, 3), "d": eg2}])
path(cv, "c_cF", 845, 975, "M-15 0L65 0", "#b9b9b9", stroke=2.4)

CVN = [("c_nA", 130, 849), ("c_nB", 345, 911), ("c_nC", 361, 849),
       ("c_nD", 545, 975), ("c_nE", 650, 975), ("c_nF", 780, 975),
       ("c_nG", 795, 849)]
for nid, nx, ny in CVN:
    path(cv, nid, nx, ny, blob_d(1.45), "#141414")
    path(cv, nid + "d", nx, ny, blob_dot_d(1.45), "#8a8a8a")
# node C dragged during the tight phase, node E pulled into the valley after
for nid in ("c_nC", "c_nCd"):
    track(nid, x=[(0, 49), (8 * F, 49), (20 * F, 0, "outCubic")],
          y=[(0, -19), (8 * F, -19), (20 * F, 0, "outCubic")])
for nid in ("c_nE", "c_nEd"):
    track(nid, y=[(0, -70), (35 * F, -70), (53 * F, 0, "outCubic")])

node(cv, "c_cur", "cursor", 670, 985, w=30, fill="#111111")
track("c_cur",
      x=[(0, -263), (8 * F, -263), (20 * F, -299, "outCubic"),
         (31 * F, -299), (38 * F, 0, "outCubic")],
      y=[(0, -123), (31 * F, -124), (38 * F, -78, "outCubic"),
         (53 * F, 0, "outCubic")])

# the one-frame reframes: pan right while tight, snap wide at f228
track("cv", cam_x=steps([(0, -288), (SNAP, 0)]))

stage = {
    "fps": 60,
    "size": [W, H],
    "scenes": [
        {"id": "ed", "bg": "#000000", "dur": round(ED_END, 4),
         "transition": {"kind": "cut"}, "nodes": ed},
        {"id": "mg", "bg": "#e9e9e9", "dur": round(MG_END, 4),
         "transition": {"kind": "cut"}, "nodes": mg},
        {"id": "cv", "bg": "#d2d2d2", "dur": round(CV_END, 4),
         "transition": {"kind": "cut"}, "nodes": cv},
    ],
}

with open("docs/design.stage.json", "w") as f:
    json.dump(stage, f, indent=1)
with open("docs/design.anim.json", "w") as f:
    json.dump({"tracks": tracks}, f, indent=1)
print("wrote docs/design.{stage,anim}.json,",
      sum(len(s["nodes"]) for s in stage["scenes"]), "nodes,",
      len(tracks), "tracks")
