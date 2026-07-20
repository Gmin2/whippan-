#!/usr/bin/env python3
# reproduction of analysis/higgsfield-figma (70s, 1138x640) compressed to a
# ~38s arc. one figma-grey canvas world; three named cursors (CalmLama blue,
# Demius green, Jagan96 magenta) race a fake one-hour deadline building the
# HiggsWatch site with the higgsfield plugin. scenes are regions of the
# board joined by whip-pans, never cuts. all real imagery is substituted
# with flat drawn blocks in the teardown palette. chapter map:
#   s1  cold-open "In progress" card          (teardown sc 1)
#   s2  Higgsfield for Figma lockup           (sc 2-3)
#   s3  canvas brief: photo + chat + deadline (sc 4)
#   s4  plugin prompt -> cook -> watch render (sc 5-7)
#   s5  HiggsWatch lime hero types in         (sc 8)
#   s6  multi-ref prompt -> 2x2 photoshoot    (sc 11-12)
#   s7  "Built for the distance" editorial    (sc 13)
#   s8  Apps menu -> Angles thumbnails        (sc 14-16)
#   s9  GUYS UPDATE -> Mockup Studio billboard(sc 18-21)
#   s10 video prompt with @mentions -> FILM   (sc 24-26)
#   s11 Well done team -> full page scroll    (sc 27-29)
#   s12 end card                              (sc 30)
import json
import os
import re

W, H = 1138, 640
LIME = "#d3fe24"
INK = "#161616"
PANEL = "#0d0d10"
SEL = "#4a9bff"
BG = "#e5e3e6"
BLUE = "#23bef6"
BLUE_CHIP = "#81eaff"
GREEN = "#31ffa9"
MAG = "#e6249f"
MAG_CHIP = "#f96fdc"

NUCLEO = "/Users/mintu/coding/portfolio/ui/tools/icons"

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

tracks = []


def text(id, s, x, y, size, color, weight=400, family="inter"):
    return {"id": id, "type": "text", "text": s, "x": round(x, 1),
            "y": round(y, 1), "color": color,
            "font": {"size": size, "weight": weight, "family": family}}


def ltext(id, s, left, y, size, color, weight=400, family="inter"):
    adv = 0.6 if family == "mono" else 0.5
    return text(id, s, left + len(s) * size * adv / 2, y, size, color,
                weight, family)


def rect(id, x, y, w, h, r, fill, **kw):
    n = {"id": id, "type": "rect", "x": round(x, 1), "y": round(y, 1),
         "w": w, "h": h, "radius": r, "fill": fill}
    n.update(kw)
    return n


def path(id, x, y, d, color, stroke=None, **kw):
    n = {"id": id, "type": "path", "x": round(x, 1), "y": round(y, 1),
         "d": d, "fill": color}
    if stroke:
        n["stroke"] = stroke
    n.update(kw)
    return n


def track(nid, at=None, **props):
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
    if at is not None:
        t["at"] = at
    tracks.append(t)


def reveal(nid, at, **kw):
    r = {"unit": "type", "cadence": 0.03, "dur": 0.08, "caret": "none"}
    r.update(kw)
    tracks.append({"target": nid, "at": at, "reveal": r})


def gate(nid, t_in, t_out=None, hi=1.0, fade=0.12):
    ks = [(0, 0), (t_in, 0), (t_in + fade, hi)]
    if t_out is not None:
        ks += [(t_out, hi), (t_out + fade, 0)]
    track(nid, opacity=ks)


def icon(id, svg_file, cx, cy, size, color, stroke=2.0, filled=False):
    src = open(f"{NUCLEO}/{svg_file}").read()
    vb = float(re.search(r'viewBox="0 0 (\d+)', src).group(1))
    parts = []
    for m in re.finditer(r'<path[^>]*? d="([^"]+)"', src):
        parts.append(m.group(1))
    for m in re.finditer(r'<line[^>]*?x1="([\d.]+)"[^>]*?y1="([\d.]+)"[^>]*?x2="([\d.]+)"[^>]*?y2="([\d.]+)"', src):
        x1, y1, x2, y2 = m.groups()
        parts.append(f"M{x1} {y1}L{x2} {y2}")
    for m in re.finditer(r'<circle[^>]*?cx="([\d.]+)"[^>]*?cy="([\d.]+)"[^>]*?r="([\d.]+)"', src):
        x, y, r = (float(v) for v in m.groups())
        parts.append(f"M{x - r} {y}a{r} {r} 0 1 0 {2 * r} 0"
                     f"a{r} {r} 0 1 0 {-2 * r} 0")
    for m in re.finditer(r'<polyline[^>]*?points="([^"]+)"', src):
        parts.append("M" + "L".join(m.group(1).split()))
    k = size / vb
    n = {"id": id, "type": "path", "x": round(cx - size / 2, 1),
         "y": round(cy - size / 2, 1), "fill": color, "d": "".join(parts),
         "keys": {"scale": [{"t": 0, "v": k}]}}
    if not filled:
        n["stroke"] = stroke
    return n


def actor(p, name, arrow, chipfill, tcol, x, y, nodes, moves=None,
          t_in=None, t_out=None):
    """cursor + name-tag chip. moves = [(t, dx, dy, ease), ...] applied to
    all three nodes (offsets from home)."""
    tagw = round(len(name) * 5.8 + 14)
    ids = [p + "c", p + "t", p + "n"]
    nodes.append({"id": p + "c", "type": "cursor", "x": x, "y": y,
                  "w": 17, "fill": arrow})
    nodes.append(rect(p + "t", x + 22 + tagw / 2, y + 30, tagw, 18, 9,
                      chipfill))
    nodes.append(text(p + "n", name, x + 22 + tagw / 2, y + 30, 10, tcol,
                      weight=600))
    for nid in ids:
        if moves:
            track(nid,
                  x=[(t, dx, e) for (t, dx, dy, *rest) in moves
                     for e in [rest[0] if rest else None]],
                  y=[(t, dy, e) for (t, dx, dy, *rest) in moves
                     for e in [rest[0] if rest else None]])
        if t_in is not None or t_out is not None:
            gate(nid, t_in or 0, t_out)


def selbox(p, cx, cy, w, h, nodes, t_in, t_out=None, tag=None):
    d = (f"M{-w/2} {-h/2}L{w/2} {-h/2}L{w/2} {h/2}L{-w/2} {h/2}Z")
    ids = []
    nodes.append(path(p + "bx", cx, cy, d, SEL, stroke=1.6))
    ids.append(p + "bx")
    for j, (hx, hy) in enumerate([(-w/2, -h/2), (w/2, -h/2),
                                  (w/2, h/2), (-w/2, h/2)]):
        nodes.append(rect(f"{p}hb{j}", cx + hx, cy + hy, 8, 8, 1, SEL))
        nodes.append(rect(f"{p}hw{j}", cx + hx, cy + hy, 5, 5, 1, "#ffffff"))
        ids += [f"{p}hb{j}", f"{p}hw{j}"]
    if tag:
        tw = len(tag) * 4.4 + 10
        nodes.append(rect(p + "tg", cx - w/2 + tw/2, cy - h/2 - 12, tw, 14,
                          3, SEL))
        nodes.append(text(p + "tt", tag, cx - w/2 + tw/2, cy - h/2 - 12, 8,
                          "#ffffff", weight=600))
        ids += [p + "tg", p + "tt"]
    for nid in ids:
        gate(nid, t_in, t_out, fade=0.08)


def cook(p, cx, cy, w, h, t0, t1, nodes, cols=8, rows=4):
    """lime dot-particle generation shimmer over a dark card."""
    for i in range(cols * rows):
        gx = cx - w/2 + (i % cols + 0.5) * w / cols + ((i * 37) % 9 - 4)
        gy = cy - h/2 + (i // cols + 0.5) * h / rows + ((i * 53) % 9 - 4)
        nodes.append(rect(f"{p}d{i}", gx, gy, 4, 4, 2, LIME))
        ph = t0 + ((i * 13) % 10) * 0.04
        ks, tt, on = [(0, 0), (ph, 0)], ph + 0.05, True
        while tt < t1 - 0.12:
            ks.append((tt, 0.95 if on else 0.2))
            on = not on
            tt += 0.11 + ((i * 7) % 4) * 0.02
        ks.append((t1, 0))
        track(f"{p}d{i}", opacity=ks)


def watch(p, cx, cy, s, nodes, straps=True, ring="#3c3c42", lime_hand=True):
    """flat drawn hero watch: angled straps, round case, dark face,
    white hands, lime second hand."""
    k = s / 180.0
    if straps:
        nodes.append(rect(p + "sl", cx - 114*k, cy + 60*k, 150*k, 60*k,
                          30*k, "#26262b", rot=35))
        nodes.append(rect(p + "sr", cx + 121*k, cy - 60*k, 150*k, 60*k,
                          30*k, "#26262b", rot=35))
    nodes.append(rect(p + "cs", cx, cy, s, s, s/2, ring))
    nodes.append(rect(p + "fc", cx, cy, s*0.82, s*0.82, s*0.41, "#101014"))
    nodes.append(path(p + "hh", cx, cy,
                      f"M0 2L{0.26*s} {-0.16*s}M0 2L{-0.07*s} {-0.26*s}",
                      "#e8e8ea", stroke=max(2.0, s * 0.022)))
    if lime_hand:
        nodes.append(path(p + "sh", cx, cy,
                          f"M{0.06*s} {-0.24*s}L{-0.13*s} {0.3*s}",
                          LIME, stroke=max(1.2, s * 0.012)))


def photo_street(p, cx, cy, s, nodes):
    """the client's phone snapshot: watch on a wrist on a street."""
    k = s / 200.0
    nodes.append(rect(p + "b", cx, cy, s, s, 12*k, "#c9cdc9"))
    nodes.append(rect(p + "rd", cx, cy + 55*k, s, 70*k, 8*k, "#b0b4b0"))
    nodes.append(rect(p + "sv", cx - 38*k, cy - 8*k, 92*k, 112*k, 32*k,
                      "#cfe0cd", rot=25))
    nodes.append(rect(p + "wr", cx + 20*k, cy + 6*k, 112*k, 46*k, 23*k,
                      "#d9b9a0", rot=-18))
    nodes.append(rect(p + "wc", cx + 24*k, cy - 2*k, 36*k, 36*k, 18*k,
                      "#17171b"))
    nodes.append(rect(p + "wf", cx + 24*k, cy - 2*k, 22*k, 22*k, 11*k,
                      "#2e2e34"))


def photo_portrait(p, cx, cy, s, nodes):
    """the model headshot: plain studio bg, head, dark tank."""
    k = s / 200.0
    nodes.append(rect(p + "b", cx, cy, s, s, 12*k, "#d8cfc8"))
    nodes.append(rect(p + "sh", cx, cy + 74*k, 132*k, 88*k, 40*k, "#202024"))
    nodes.append(rect(p + "hd", cx, cy - 22*k, 62*k, 74*k, 30*k, "#c9a189"))
    nodes.append(rect(p + "hr", cx, cy - 52*k, 70*k, 34*k, 16*k, "#3a2e28"))


def runner_tile(p, cx, cy, w, h, nodes, base="#7d8a7d", wide=False):
    """volcanic-ridge running shot as flat blocks."""
    nodes.append(rect(p + "b", cx, cy, w, h, 8, base))
    rw = w * (1.1 if wide else 0.9)
    nodes.append(path(p + "rg", cx, cy + h*0.22,
                      f"M{-rw/2} {h*0.28}L{-w*0.1} {-h*0.12}L{w*0.16} {h*0.06}"
                      f"L{rw/2} {-h*0.2}L{rw/2} {h*0.28}Z", "#4d564d"))
    fx = cx - w*0.08
    fy = cy - h*0.08
    nodes.append(rect(p + "fb", fx, fy, w*0.05, h*0.16, 3, "#e8e4de", rot=12))
    nodes.append(rect(p + "fh", fx + 1, fy - h*0.12, w*0.04, w*0.04,
                      w*0.02, "#c9a189"))


def macro_tile(p, cx, cy, w, h, nodes, dx=0, dy=0, ws=None):
    """watch macro on dark as flat blocks."""
    ws = ws or h * 0.52
    nodes.append(rect(p + "b", cx, cy, w, h, 8, "#17171b"))
    nodes.append(rect(p + "c", cx + dx, cy + dy, ws, ws, ws/2, "#33333a"))
    nodes.append(rect(p + "f", cx + dx, cy + dy, ws*0.76, ws*0.76,
                      ws*0.38, "#0d0d10"))
    nodes.append(path(p + "mh", cx + dx, cy + dy,
                      f"M0 0L{ws*0.2} {-ws*0.14}M0 0L{-ws*0.04} {-ws*0.24}",
                      "#d8d8dc", stroke=max(1.2, ws * 0.03)))
    nodes.append(path(p + "h", cx + dx, cy + dy,
                      f"M0 0L{-ws*0.05} {ws*0.26}", LIME,
                      stroke=max(1.0, ws * 0.018)))


def deadline(p, nodes, cx, cy, prefix, d_from, d_to, t_swap, t_in=0.15,
             t_out=None):
    """dark chip, DEADLINE label, lime mono countdown; last digit swaps."""
    nodes.append(rect(p + "bg", cx, cy, 172, 32, 16, "#141418"))
    nodes.append(ltext(p + "lb", "DEADLINE", cx - 74, cy, 9, "#8a8a92",
                       weight=600))
    left = cx + 4
    nodes.append(ltext(p + "tm", prefix, left, cy, 15, LIME, weight=600,
                       family="mono"))
    dxp = left + len(prefix) * 15 * 0.6 + 15 * 0.3
    nodes.append(text(p + "da", d_from, dxp, cy, 15, LIME, weight=600,
                      family="mono"))
    nodes.append(text(p + "db", d_to, dxp, cy, 15, LIME, weight=600,
                      family="mono"))
    for nid in (p + "bg", p + "lb", p + "tm"):
        gate(nid, t_in, t_out, fade=0.15)
    da_ops = [(0, 0), (t_in, 0), (t_in + 0.15, 1),
              (t_swap, 1), (t_swap + 0.1, 0)]
    db_ops = [(0, 0), (t_swap, 0), (t_swap + 0.1, 1)]
    if t_out:
        db_ops += [(t_out, 1), (t_out + 0.15, 0)]
    track(p + "da", opacity=da_ops,
          y=[(t_swap, 0), (t_swap + 0.1, -9, "outCubic")])
    track(p + "db", opacity=db_ops,
          y=[(t_swap, 9), (t_swap + 0.1, 0, "outCubic")])


def plugin_header(p, nodes, px, py):
    """lime logo square + wordmark, top-left inside a panel."""
    nodes.append(rect(p + "lg", px, py, 14, 14, 4, LIME))
    nodes.append(path(p + "lq", px, py, "M-4 2C-2 -3 0 -3 1 0C2 3 4 3 5 -2",
                      "#101014", stroke=1.6))
    nodes.append(ltext(p + "lt", "Higgsfield", px + 12, py, 10, "#8a8a92",
                       weight=500))


def submit_btn(p, nodes, cx, cy, r=22, glyph="arrow"):
    nodes.append(rect(p + "sb", cx, cy, r*2, r*2, r, LIME,
                      states={"pressed": {"scale": 0.88}}))
    if glyph == "arrow":
        d = f"M0 {r*0.36}L0 {-r*0.36}M{-r*0.27} {-r*0.09}L0 {-r*0.36}L{r*0.27} {-r*0.09}"
    else:
        d = (f"M0 {-r*0.4}L{r*0.11} {-r*0.11}L{r*0.4} 0L{r*0.11} {r*0.11}"
             f"L0 {r*0.4}L{-r*0.11} {r*0.11}L{-r*0.4} 0L{-r*0.11} {-r*0.11}Z")
    nodes.append(path(p + "sg", cx, cy, d, "#101014",
                      stroke=2.4 if glyph == "arrow" else None))


scenes = []

# ---------------------------------------------------------------- s1: cold open
n1 = []
n1.append(rect("s1_card", 300, 320, 150, 200, 10, "#101014",
               glow={"sigma": 18, "opacity": 0.25, "color": "#909096",
                     "dy": 6}))
n1.append(rect("s1_dot", 238, 238, 5, 5, 2.5, LIME))
n1.append(ltext("s1_prog", "In progress", 248, 238, 9, LIME))
track("s1_card", scale=[(0, 1.0), (1.2, 1.035, "inOutCubic")])
tracks.append({"target": "s1_dot", "loop": True, "keys": {"opacity": [
    {"t": 0, "v": 1}, {"t": 0.35, "v": 0.4, "ease": "inOutCubic"},
    {"t": 0.7, "v": 1, "ease": "inOutCubic"}]}})
scenes.append({"id": "s1", "bg": BG, "dur": 1.2,
               "transition": {"kind": "cut"}, "nodes": n1})

# ---------------------------------------------------------------- s2: lockup
n2 = []
n2.append(path("s2_squig", 295, 320,
               "M-26 8C-18 -14 -7 -14 0 0C7 14 18 14 26 -8", INK, stroke=7))
n2.append(ltext("s2_name", "Higgsfield", 340, 320, 42, INK, weight=700))
reveal("s2_name", 0.15, cadence=0.05)
n2.append(text("s2_for", "for", 600, 328, 26, "#44444a", weight=500))
gate("s2_for", 1.7, fade=0.25)
FIGMA = [("s2_fg0", 688, 304, "#f24e1e"), ("s2_fg1", 688, 320, "#a259ff"),
         ("s2_fg2", 688, 336, "#0acf83"), ("s2_fg3", 704, 304, "#ff7262"),
         ("s2_fg4", 704, 320, "#1abcfe")]
for i, (nid, gx, gy, col) in enumerate(FIGMA):
    n2.append(rect(nid, gx, gy, 15, 15, 7.5, col,
                   streak={"samples": 4, "window": 0.05, "gain": 0.5}))
    t0 = 0.9 + i * 0.07
    gate(nid, t0, fade=0.06)
    track(nid, x=[(t0, 300 + i * 30), (t0 + 0.35, 0, "outCubic")])
n2.append(ltext("s2_figt", "Figma", 736, 320, 42, INK, weight=700))
reveal("s2_figt", 1.35, cadence=0.06)
# teammate cursors streak across during assembly
actor("s2_dm", "Demius", GREEN, GREEN, "#083c26", 200, 430, n2,
      moves=[(0.8, -500, 60), (1.25, 620, -30, "outCubic")],
      t_in=0.8, t_out=1.3)
actor("s2_jg", "Jagan96", MAG, MAG_CHIP, "#ffffff", 800, 220, n2,
      moves=[(1.0, 500, -40), (1.5, -700, 30, "outCubic")],
      t_in=1.0, t_out=1.55)
track("s2", cam_zoom=[(0.9, 1.0), (2.6, 1.06, "inOutCubic")])
scenes.append({"id": "s2", "bg": BG, "dur": 2.6,
               "transition": {"kind": "fade", "dur": 0.3}, "nodes": n2})

# ---------------------------------------------------------------- s3: the brief
n3 = []
photo_street("s3_ph", 205, 360, 200, n3)
for nid in ("s3_phb", "s3_phrd", "s3_phsv", "s3_phwr", "s3_phwc", "s3_phwf"):
    gate(nid, 0.25, fade=0.1)
    track(nid, x=[(0.25, -140), (0.7, 0, "outCubic")],
          y=[(0.25, -170), (0.7, 0, "outCubic")])
CHAT = ["Guys, new client", "Watch landing page", "One-hour deadline",
        "This photo is all we got"]
for i, line in enumerate(CHAT):
    n3.append(ltext(f"s3_ch{i}", line, 520, 270 + i * 36, 26, INK,
                    weight=700))
    reveal(f"s3_ch{i}", 0.9 + i * 0.6, cadence=0.028)
selbox("s3_sel", 676, 324, 332, 148, n3, 0.85, t_out=3.3)
actor("s3_cl", "CalmLama", BLUE, BLUE_CHIP, "#0a3a4a", 60, 598, n3,
      moves=[(0.4, 0, 0), (1.4, 20, -18, "outCubic")], t_in=0.35)
actor("s3_dm", "Demius", GREEN, GREEN, "#083c26", 170, 578, n3,
      moves=[(0.5, -60, 60), (1.1, 0, 0, "outCubic"),
             (2.6, 18, -12, "outCubic")], t_in=0.5)
actor("s3_jg", "Jagan96", MAG, MAG_CHIP, "#ffffff", 312, 268, n3,
      moves=[(0.25, -140, -170), (0.7, 0, 0, "outCubic"), (0.9, 0, 0),
             (1.4, 548, 136, "outCubic")], t_in=0.25)
deadline("s3_dl", n3, 1000, 50, "59:5", "8", "7", 3.3, t_in=2.85)
track("s3", cam_zoom=[(0, 1.05), (0.5, 1.0, "outCubic"),
                      (3.6, 1.03, "inOutCubic")])
scenes.append({"id": "s3", "bg": BG, "dur": 3.6,
               "transition": {"kind": "whip", "dur": 0.32, "dir": "left"},
               "nodes": n3})

# ------------------------------------------------- s4: plugin, cook, the render
n4 = []
n4.append(rect("s4_panel", 569, 300, 880, 460, 22, PANEL,
               glow={"sigma": 26, "opacity": 0.3, "color": "#9a9aa0",
                     "dy": 8}))
plugin_header("s4_hd", n4, 175, 105)
photo_street("s4_th", 205, 195, 84, n4)
n4.append(ltext("s4_prompt", "Make professional product photography of a watch",
                170, 330, 21, "#f2f2f2"))
reveal("s4_prompt", 0.5, cadence=0.03, caret="bar", caret_blink=0.8)
submit_btn("s4_", n4, 955, 480)
prompt_ids = ["s4_thb", "s4_thrd", "s4_thsv", "s4_thwr", "s4_thwc",
              "s4_thwf", "s4_sb", "s4_sg", "s4_prompt"]
for nid in prompt_ids:
    track(nid, opacity=[(0, 1), (2.3, 1), (2.5, 0)])
actor("s4_jg", "Jagan96", MAG, MAG_CHIP, "#ffffff", 650, 600, n4,
      moves=[(1.5, 0, 0), (2.05, 295, -110, "outCubic")], t_out=2.45)
tracks.append({"target": "s4_sb", "at": 2.2, "state": "pressed"})
n4.append(ltext("s4_prog", "In progress", 170, 140, 10, LIME))
gate("s4_prog", 2.35, 3.35)
cook("s4_ck", 569, 300, 700, 280, 2.4, 3.4, n4)
watch("s4_w", 569, 300, 180, n4)
for nid in ("s4_wsl", "s4_wsr", "s4_wcs", "s4_wfc", "s4_whh", "s4_wsh"):
    gate(nid, 3.4, fade=0.15)
    track(nid, scale=[(3.4, 1.07), (3.7, 1.0, "outCubic")])
selbox("s4_sel", 569, 300, 560, 330, n4, 3.6, tag="Render.png")
deadline("s4_dl", n4, 1000, 50, "52:1", "4", "3", 2.0)
track("s4", cam_zoom=[(0, 1.14), (0.55, 1.0, "outCubic"), (3.4, 1.0),
                      (4.2, 1.05, "inOutCubic")])
scenes.append({"id": "s4", "bg": BG, "dur": 4.2,
               "transition": {"kind": "whip", "dur": 0.3, "dir": "right"},
               "nodes": n4})

# ---------------------------------------------------------------- s5: the hero
n5 = []
n5.append(rect("s5_nav", 569, 92, 700, 34, 6, "#ffffff"))
n5.append(ltext("s5_nvl", "HiggsWatch", 240, 92, 12, INK, weight=700))
n5.append(text("s5_nvm", "GALLERY      DETAILS      FEATURES      FAQ",
               569, 92, 8, "#55555a"))
n5.append(rect("s5_nvp", 862, 92, 66, 18, 9, LIME))
n5.append(text("s5_nvpt", "Pre-order", 862, 92, 8, INK, weight=600))
n5.append(rect("s5_hero", 569, 282, 700, 340, 2, LIME))
watch("s5_w", 569, 298, 150, n5)
n5.append(text("s5_h1", "HiggsWatch", 569, 172, 56, INK, weight=800))
reveal("s5_h1", 0.5, cadence=0.055)
selbox("s5_hsel", 569, 172, 330, 72, n5, 0.45, t_out=2.3)
n5.append(rect("s5_glass", 569, 390, 360, 66, 10, "#ffffff"))
track("s5_glass", opacity=[(0.3, 0), (0.6, 0.6)])
n5.append(text("s5_gc1", "A clinical-grade sensor array on an aerospace-titanium body.",
               569, 380, 8, "#333338"))
n5.append(text("s5_gc2", "It reads your body 24/7 - and tells you what actually matters.",
               569, 392, 8, "#333338"))
n5.append(rect("s5_gp", 512, 412, 118, 16, 8, INK))
n5.append(text("s5_gpt", "Pre-order - from $399", 512, 412, 7, "#ffffff"))
n5.append(text("s5_gwt", "What it tracks", 630, 412, 7, "#333338"))
n5.append(rect("s5_tick", 569, 470, 700, 24, 2, "#131316"))
n5.append(text("s5_tkt", "BLOOD OXYGEN  ·  SKIN TEMPERATURE  ·  SLEEP STAGES  ·  30-HOUR BATTERY  ·  100M WATER-RATED  ·  GRADE-5 TITANIUM",
               569, 470, 8, "#d9d9de", family="mono"))
for nid, d in [("s5_nav", 0.15), ("s5_nvl", 0.2), ("s5_nvm", 0.2),
               ("s5_nvp", 0.25), ("s5_nvpt", 0.25), ("s5_hero", 0.0),
               ("s5_gc1", 0.65), ("s5_gc2", 0.7), ("s5_gp", 0.75),
               ("s5_gpt", 0.75), ("s5_gwt", 0.8), ("s5_tick", 0.3),
               ("s5_tkt", 0.4)]:
    gate(nid, d, fade=0.2)
for nid in ("s5_wsl", "s5_wsr", "s5_wcs", "s5_wfc", "s5_whh", "s5_wsh"):
    gate(nid, 0.1, fade=0.2)
actor("s5_cl", "CalmLama", BLUE, BLUE_CHIP, "#0a3a4a", 330, 245, n5,
      moves=[(0.6, -50, -30), (1.3, 0, 0, "outCubic"),
             (2.8, 24, 16, "outCubic")], t_in=0.55)
actor("s5_jg", "Jagan96", MAG, MAG_CHIP, "#ffffff", 772, 468, n5,
      moves=[(0.9, 60, 60), (1.5, 0, 0, "outCubic"),
             (3.0, -20, 14, "outCubic")], t_in=0.85)
deadline("s5_dl", n5, 1000, 50, "44:0", "7", "6", 1.6)
track("s5", cam_zoom=[(0, 1.06), (0.5, 1.0, "outCubic"),
                      (3.4, 1.04, "inOutCubic")])
scenes.append({"id": "s5", "bg": BG, "dur": 3.4,
               "transition": {"kind": "whip", "dur": 0.3, "dir": "left"},
               "nodes": n5})

# ------------------------------------------ s6: multi-ref prompt -> 2x2 grid
n6 = []
n6.append(rect("s6_panel", 285, 300, 430, 320, 18, PANEL))
plugin_header("s6_hd", n6, 105, 175)
photo_street("s6_t1", 165, 235, 66, n6)
photo_portrait("s6_t2", 245, 235, 66, n6)
n6.append(ltext("s6_p1", "Woman running across volcanic rocks,",
                122, 310, 15, "#f2f2f2"))
n6.append(ltext("s6_p2", "watch on wrist. Pro sportswear photoshoot.",
                122, 334, 15, "#f2f2f2"))
reveal("s6_p1", 0.25, cadence=0.02)
reveal("s6_p2", 0.95, cadence=0.02)
submit_btn("s6_", n6, 452, 420, r=18)
actor("s6_cl", "CalmLama", BLUE, BLUE_CHIP, "#0a3a4a", 330, 560, n6,
      moves=[(0.9, 0, 0), (1.45, 118, -132, "outCubic"), (2.1, 118, -132),
             (2.6, 660, -110, "outCubic")])
tracks.append({"target": "s6_sb", "at": 1.55, "state": "pressed"})
cook("s6_ck", 800, 300, 380, 270, 1.65, 2.1, n6, cols=6, rows=4)
runner_tile("s6_g0", 703, 231, 180, 125, n6)
macro_tile("s6_g1", 897, 231, 180, 125, n6, dx=20, dy=6)
runner_tile("s6_g2", 703, 369, 180, 125, n6, base="#9aa5a0", wide=True)
macro_tile("s6_g3", 897, 369, 180, 125, n6, dx=-24, dy=-4, ws=80)
grid_ids = [n["id"] for n in n6 if n["id"].startswith("s6_g")]
for j, nid in enumerate(grid_ids):
    tile = int(nid[4])
    gate(nid, 2.1 + tile * 0.06, fade=0.1)
    track(nid, scale=[(2.1 + tile * 0.06, 1.06),
                      (2.4 + tile * 0.06, 1.0, "outCubic")])
selbox("s6_sel", 800, 300, 400, 290, n6, 2.25)
deadline("s6_dl", n6, 1000, 50, "37:2", "5", "4", 1.0)
track("s6", cam_zoom=[(0, 1.05), (0.45, 1.0, "outCubic"), (2.55, 1.0),
                      (3.0, 1.05, "inCubic")],
      cam_x=[(2.55, 0), (3.0, 40, "inCubic")])
scenes.append({"id": "s6", "bg": BG, "dur": 3.0,
               "transition": {"kind": "whip", "dur": 0.3, "dir": "right"},
               "nodes": n6})

# ------------------------------------------------ s7: built for the distance
n7 = []
n7.append(rect("s7_mk", 302, 120, 5, 5, 2.5, LIME))
n7.append(ltext("s7_ml", "IN THE WILD", 312, 120, 9, "#7a7a80", weight=600))
n7.append(ltext("s7_h", "Built for the distance", 310, 160, 34, INK,
                weight=800))
reveal("s7_h", 0.2, cadence=0.03)
runner_tile("s7_lp", 455, 350, 310, 220, n7)
n7.append(text("s7_lc", "Engineered for those who move.", 510, 438, 9,
               "#ffffff", weight=600))
macro_tile("s7_rp", 785, 350, 310, 220, n7, dx=30, dy=-10, ws=120)
n7.append(ltext("s7_rt1", "Always", 655, 290, 20, "#ffffff", weight=800))
n7.append(ltext("s7_rt2", "on alert", 655, 316, 20, "#ffffff", weight=800))
n7.append(rect("s7_band", 569, 600, 660, 70, 8, "#101014"))
n7.append(text("s7_bt", "Every detail, engineered to be felt.", 569, 598,
               12, "#ffffff", weight=600))
for nid, d, ry in [("s7_lpb", 0.35, 14), ("s7_lprg", 0.4, 14),
                   ("s7_lpfb", 0.45, 14), ("s7_lpfh", 0.45, 14),
                   ("s7_lc", 0.55, 10), ("s7_rpb", 0.5, 14),
                   ("s7_rpc", 0.55, 14), ("s7_rpf", 0.55, 14),
                   ("s7_rph", 0.55, 14), ("s7_rt1", 0.65, 10),
                   ("s7_rt2", 0.7, 10), ("s7_band", 0.9, 18),
                   ("s7_bt", 1.0, 12), ("s7_mk", 0.1, 0), ("s7_ml", 0.1, 0)]:
    gate(nid, d, fade=0.18)
    if ry:
        track(nid, y=[(d, ry), (d + 0.4, 0, "outCubic")])
actor("s7_dm", "Demius", GREEN, GREEN, "#083c26", 430, 258, n7,
      moves=[(0.5, -70, -40), (1.1, 0, 0, "outCubic"),
             (2.2, 30, 30, "outCubic")], t_in=0.45)
actor("s7_jg", "Jagan96", MAG, MAG_CHIP, "#ffffff", 388, 420, n7,
      moves=[(0.7, -60, 70), (1.3, 0, 0, "outCubic")], t_in=0.65)
actor("s7_cl", "CalmLama", BLUE, BLUE_CHIP, "#0a3a4a", 872, 452, n7,
      moves=[(0.8, 90, 60), (1.4, 0, 0, "outCubic"),
             (2.3, -30, -20, "outCubic")], t_in=0.75)
deadline("s7_dl", n7, 1000, 50, "33:4", "2", "1", 1.4)
track("s7", cam_zoom=[(0, 1.04), (0.45, 1.0, "outCubic"),
                      (2.6, 1.03, "inOutCubic")])
scenes.append({"id": "s7", "bg": BG, "dur": 2.6,
               "transition": {"kind": "whip", "dur": 0.3, "dir": "left"},
               "nodes": n7})

# ------------------------------------------------- s8: apps menu -> angles
n8 = []
n8.append(rect("s8_ph", 300, 290, 280, 280, 14, "#fafafa"))
n8.append(rect("s8_wr", 300, 316, 210, 92, 46, "#d9b9a0", rot=-20))
n8.append(rect("s8_wc", 300, 282, 92, 92, 46, "#26262b"))
n8.append(rect("s8_wf", 300, 282, 70, 70, 35, "#101014"))
n8.append(path("s8_wh", 300, 282, "M0 0L14 -10M0 0L-4 18", "#e8e8ea",
               stroke=2))
n8.append(path("s8_wl", 300, 282, "M4 -16L-9 20", LIME, stroke=1.3))
selbox("s8_sel", 300, 290, 292, 292, n8, 0.3)
n8.append(rect("s8_panel", 795, 300, 360, 480, 16, PANEL))
plugin_header("s8_hd", n8, 655, 88)
for lbl, cx, active in [("Image", 700, False), ("Video", 760, False),
                        ("Apps", 822, True)]:
    if active:
        n8.append(rect("s8_tbp", cx, 120, 52, 20, 10, "#232327"))
    n8.append(text(f"s8_tb_{lbl}", lbl, cx, 120, 10,
                   "#ffffff" if active else "#77777d",
                   weight=600 if active else 400))
n8.append(ltext("s8_at", "Apps", 645, 150, 13, "#ffffff", weight=600))
n8.append(ltext("s8_as", "Choose what to create next", 645, 168, 8,
                "#77777d"))
TILES = [("Image generation", "High-quality images", "core/image.svg"),
         ("Video generation", "Generate epic videos",
          "micro-bold/laptop-video.svg"),
         ("Mockup Studio", "Product mockups", "core/cubes-2.svg"),
         ("Remove background", "Cut out the subject",
          "micro-bold/layers-2.svg"),
         ("Color Grading", "Cinematic color grade",
          "micro-bold/pen-sparkle.svg"),
         ("Relight", "Change the lighting", "micro-bold/desk-lamp.svg"),
         ("Expand", "Extend and reframe", "micro-bold/expand-2.svg"),
         ("Angles", "New camera angles",
          "micro-bold/rotate-obj-clockwise.svg")]
n8.append(rect("s8_hl", 885, 428, 168, 52, 10, "#1f1f24"))
gate("s8_hl", 1.5, fade=0.1)
for i, (name, desc, svg) in enumerate(TILES):
    colx = 705 if i % 2 == 0 else 885
    rowy = 210 + (i // 2) * 72
    n8.append(icon(f"s8_ti{i}", svg, colx - 66, rowy - 6, 13, "#c9c9cf",
                   stroke=2.4))
    n8.append(ltext(f"s8_tn{i}", name, colx - 52, rowy - 8, 10, "#f0f0f2",
                    weight=600))
    n8.append(ltext(f"s8_td{i}", desc, colx - 52, rowy + 7, 7, "#6f6f75"))
actor("s8_jg", "Jagan96", MAG, MAG_CHIP, "#ffffff", 700, 560, n8,
      moves=[(0.9, 0, 0), (1.5, 190, -128, "outCubic")])
for i in range(4):
    xs = 205 + i * 115
    macro_tile(f"s8_a{i}", xs, 575, 105, 78, n8,
               dx=(i - 1.5) * 14, dy=(i % 2) * 8 - 4, ws=44 + i * 6)
    for suf in ("b", "c", "f", "h"):
        nid = f"s8_a{i}{suf}"
        gate(nid, 2.0 + i * 0.07, fade=0.1)
        track(nid, scale=[(2.0 + i * 0.07, 1.08),
                          (2.3 + i * 0.07, 1.0, "outCubic")])
selbox("s8_asel", 377, 575, 480, 100, n8, 2.2)
deadline("s8_dl", n8, 1000, 50, "26:1", "5", "4", 1.2)
track("s8", cam_zoom=[(0, 1.05), (0.5, 1.0, "outCubic"),
                      (3.2, 1.03, "inOutCubic")])
scenes.append({"id": "s8", "bg": BG, "dur": 3.2,
               "transition": {"kind": "whip", "dur": 0.3, "dir": "right"},
               "nodes": n8})

# --------------------------------- s9: GUYS UPDATE -> mockup studio billboard
n9 = []
n9.append(rect("s9_bub", 400, 230, 400, 86, 20, MAG))
n9.append(text("s9_bl1", "GUYS, UPDATE! Client wants to", 400, 214, 16,
               "#ffffff", weight=600))
n9.append(text("s9_bl2", "announce their first marathon", 400, 246, 16,
               "#ffffff", weight=600))
for nid in ("s9_bub", "s9_bl1", "s9_bl2"):
    gate(nid, 0.15, fade=0.1)
    track(nid, scale=[(0.15, 0.85), (0.45, 1.0, "outCubic")])
n9.append(rect("s9_rb", 330, 330, 130, 44, 18, BLUE))
n9.append(text("s9_rbt", "I'll do it!", 330, 330, 16, "#ffffff", weight=600))
for nid in ("s9_rb", "s9_rbt"):
    gate(nid, 0.9, fade=0.1)
    track(nid, scale=[(0.9, 0.85), (1.15, 1.0, "outCubic")])
actor("s9_dm", "Demius", GREEN, GREEN, "#083c26", 560, 320, n9,
      moves=[(0.3, 40, 30), (0.9, 0, 0, "outCubic")])
actor("s9_jg", "Jagan96", MAG, MAG_CHIP, "#ffffff", 620, 180, n9,
      moves=[(0.2, -30, -20), (0.8, 0, 0, "outCubic")])
# mockup studio panel lives 680px to the right on the same board
n9.append(rect("s9_mp", 1250, 300, 430, 520, 18, PANEL))
n9.append(ltext("s9_mt", "Mockup Studio", 1060, 80, 14, "#ffffff",
                weight=700))
n9.append(ltext("s9_ms", "Pick a preset", 1060, 98, 8, "#77777d"))
PRESETS = [("s9_pa", 1120, 185, 120, 110, "#8f9aa5", "BILLBOARD"),
           ("s9_pb", 1380, 185, 120, 110, "#c9c2b2", "NEWSPAPER"),
           ("s9_pc", 1120, 330, 120, 140, "#d8d8d8", "LAPTOP"),
           ("s9_pd", 1380, 330, 120, 140, "#99b4c9", "CUP"),
           ("s9_pe", 1120, 470, 120, 90, "#cfc9bf", "TOTE"),
           ("s9_pf", 1380, 470, 120, 90, "#b5a9a0", "CARDS")]
for nid, cx, cy, w, h, col, lbl in PRESETS:
    n9.append(rect(nid, cx, cy, w, h, 8, col))
    n9.append(text(nid + "t", lbl, cx, cy, 7, "#ffffff", weight=700))
# the chosen billboard tile, center
n9.append(rect("s9_bt", 1250, 300, 170, 230, 8, "#6f7a85"))
n9.append(rect("s9_bs", 1250, 210, 170, 50, 0, "#55606b"))
n9.append(rect("s9_bb", 1250, 292, 132, 112, 4, "#17171b"))
n9.append(text("s9_bb1", "MOCKUP BOARD", 1250, 288, 10, "#d8d8dc",
               weight=800))
n9.append(rect("s9_rw", 1250, 400, 170, 30, 0, "#3c434a"))
for i in range(3):
    n9.append(rect(f"s9_rn{i}", 1206 + i * 42, 398, 5, 12, 2, "#d8d0c4"))
# generate button + the render swap
n9.append(rect("s9_gen", 1250, 448, 122, 28, 14, LIME,
               states={"pressed": {"scale": 0.9}}))
n9.append(text("s9_gent", "GENERATE", 1250, 448, 10, "#101014", weight=800))
for nid in ("s9_gen", "s9_gent"):
    gate(nid, 2.2, fade=0.12)
tracks.append({"target": "s9_gen", "at": 3.0, "state": "pressed"})
n9.append(rect("s9_flash", 1250, 300, 430, 520, 18, "#ffffff"))
track("s9_flash", opacity=[(0, 0), (3.15, 0), (3.18, 0.4), (3.45, 0)])
n9.append(text("s9_hw", "HIGGSWATCH", 1250, 268, 6, LIME, weight=700))
n9.append(text("s9_pp", "PURE PRECISION", 1250, 288, 10, "#ffffff",
               weight=800))
n9.append(text("s9_pp2", "SCULPTED IN TITANIUM", 1250, 302, 5, "#9a9aa0"))
track("s9_bb1", opacity=[(0, 1), (3.2, 1), (3.3, 0)])
for nid in ("s9_hw", "s9_pp", "s9_pp2"):
    gate(nid, 3.25, fade=0.1)
actor("s9_cl", "CalmLama", BLUE, BLUE_CHIP, "#0a3a4a", 1050, 540, n9,
      moves=[(2.1, -80, 40), (2.7, 0, 0, "outCubic"),
             (2.75, 0, 0), (3.0, 208, -80, "outCubic")], t_in=2.05)
deadline("s9_dl", n9, 1000, 50, "18:3", "2", "1", 0.8)
deadline("s9_dr", n9, 1690, 50, "17:5", "8", "7", 3.4, t_in=2.0)
track("s9", cam_x=[(0, 0), (1.5, 0), (1.75, 430, "inCubic"),
                   (2.05, 681, "outCubic")])
scenes.append({"id": "s9", "bg": BG, "dur": 3.8,
               "transition": {"kind": "whip", "dur": 0.3, "dir": "left"},
               "nodes": n9})

# ------------------------------------------------ s10: the video generation
n10 = []
n10.append(rect("s10_panel", 569, 290, 840, 430, 20, PANEL))
plugin_header("s10_hd", n10, 195, 105)
n10.append(text("s10_tab", "Video", 880, 105, 10, "#ffffff", weight=600))
macro_tile("s10_t1", 215, 200, 74, 74, n10, ws=40)
photo_portrait("s10_t2", 300, 200, 74, n10)
n10.append(text("s10_tg1", "@image1", 215, 248, 8, LIME, weight=600))
n10.append(text("s10_tg2", "@image2", 300, 248, 8, LIME, weight=600))
n10.append(ltext("s10_p1", "Create high quality commercial video with",
                 175, 320, 17, "#f2f2f2"))
reveal("s10_p1", 0.3, cadence=0.02, caret="bar")
SEG = [("s10_s1", "my character ", "#f2f2f2", 1.15),
       ("s10_s2", "@image2", LIME, 1.35),
       ("s10_s3", " and my product ", "#f2f2f2", 1.55),
       ("s10_s4", "@image1", LIME, 1.8)]
segleft = 175
for nid, s, col, at in SEG:
    n10.append(ltext(nid, s, segleft, 350, 17, col,
                     weight=600 if col == LIME else 400))
    gate(nid, at, fade=0.08)
    segleft += len(s) * 17 * 0.5
n10.append(ltext("s10_mdl", "Seedance 2.0   ·   16:9   ·   1080p", 175, 445,
                 10, "#8a8a90"))
submit_btn("s10_", n10, 930, 452, r=21, glyph="spark")
prompt10 = ["s10_sb", "s10_sg", "s10_p1", "s10_s1", "s10_s2", "s10_s3",
            "s10_s4", "s10_mdl", "s10_tg1", "s10_tg2", "s10_t1b", "s10_t1c",
            "s10_t1f", "s10_t1h", "s10_t2b", "s10_t2sh", "s10_t2hd",
            "s10_t2hr"]
actor("s10_dm", "Demius", GREEN, GREEN, "#083c26", 700, 580, n10,
      moves=[(1.5, 0, 0), (2.0, 222, -122, "outCubic")], t_out=2.4)
tracks.append({"target": "s10_sb", "at": 2.1, "state": "pressed"})
for nid in prompt10:
    if nid in ("s10_s1", "s10_s2", "s10_s3", "s10_s4"):
        # fold the death into the birth gate
        for t in tracks:
            if t["target"] == nid and "opacity" in t.get("keys", {}):
                t["keys"]["opacity"] += [{"t": 2.2, "v": 1}, {"t": 2.4, "v": 0}]
    else:
        track(nid, opacity=[(0, 1), (2.2, 1), (2.4, 0)])
cook("s10_ck", 569, 290, 640, 260, 2.25, 2.85, n10)
n10.append(rect("s10_vc", 569, 290, 580, 310, 14, "#101014",
                glow={"sigma": 22, "opacity": 0.0, "color": LIME}))
n10.append(rect("s10_vs", 569, 240, 260, 120, 40, "#cfe0cd", rot=10))
n10.append(rect("s10_vw", 569, 300, 200, 80, 40, "#d9b9a0", rot=-8))
n10.append(rect("s10_vwc", 569, 290, 72, 72, 36, "#26262b"))
n10.append(rect("s10_vwf", 569, 290, 54, 54, 27, "#101014"))
n10.append(path("s10_vwh", 569, 290, "M0 0L11 -8M0 0L-3 14", "#e8e8ea",
                stroke=1.8))
n10.append(path("s10_vwl", 569, 290, "M3 -12L-7 16", LIME, stroke=1.2))
n10.append(rect("s10_pbar", 569, 425, 520, 3, 1.5, "#3a3a40"))
n10.append(rect("s10_phd", 309, 425, 6, 6, 3, "#ffffff"))
for nid in ("s10_vc", "s10_vs", "s10_vw", "s10_vwc", "s10_vwf", "s10_vwh",
            "s10_vwl", "s10_pbar", "s10_phd"):
    gate(nid, 2.85, fade=0.15)
track("s10_vc", glow_opacity=[(2.85, 0), (3.1, 0.75, "outCubic"),
                              (3.4, 0.5, "inOutCubic"),
                              (3.6, 0.7, "inOutCubic")])
track("s10_phd", x=[(2.9, 0), (3.6, 180)])
selbox("s10_sel", 569, 290, 596, 326, n10, 3.0, tag="FILM")
deadline("s10_dl", n10, 1000, 50, "09:4", "8", "7", 1.0)
track("s10", cam_zoom=[(0, 1.06), (0.5, 1.0, "outCubic"), (2.9, 1.0),
                       (3.6, 1.06, "inOutCubic")])
scenes.append({"id": "s10", "bg": BG, "dur": 3.6,
               "transition": {"kind": "whip", "dur": 0.3, "dir": "right"},
               "nodes": n10})

# ------------------------------------- s11: well done team -> the page scroll
n11 = []
n11.append(text("s11_wd", "Well done, team!", 569, 300, 46, INK, weight=800))
reveal("s11_wd", 0.2, cadence=0.04)
actor("s11_cl", "CalmLama", BLUE, BLUE_CHIP, "#0a3a4a", 350, 218, n11,
      moves=[(0.3, -120, -40), (0.9, 0, 0, "outCubic")])
actor("s11_dm", "Demius", GREEN, GREEN, "#083c26", 770, 372, n11,
      moves=[(0.4, 130, 50), (1.0, 0, 0, "outCubic")])
actor("s11_jg", "Jagan96", MAG, MAG_CHIP, "#ffffff", 520, 420, n11,
      moves=[(0.5, -60, 120), (1.05, 0, 0, "outCubic")])
deadline("s11_dl", n11, 1000, 50, "00:1", "2", "1", 0.6)

# the finished page, one tall column at world x 1750
PX = 1750
n11.append(rect("s11_nav", PX, 60, 620, 30, 5, "#ffffff"))
n11.append(ltext("s11_nvl", "HiggsWatch", PX - 290, 60, 11, INK, weight=700))
n11.append(rect("s11_nvp", PX + 262, 60, 58, 16, 8, LIME))
n11.append(text("s11_nvpt", "Pre-order", PX + 262, 60, 7, INK, weight=600))
n11.append(rect("s11_hero", PX, 250, 620, 330, 2, LIME))
n11.append(text("s11_h1", "HiggsWatch", PX, 155, 44, INK, weight=800))
watch("s11_w", PX, 268, 130, n11)
n11.append(rect("s11_gl", PX, 352, 300, 46, 8, "#ffffff"))
track("s11_gl", opacity=[(0, 0.55)])
n11.append(text("s11_glt", "A clinical-grade sensor array. Pre-order - from $399",
                PX, 352, 7, "#333338"))
n11.append(rect("s11_tk", PX, 428, 620, 20, 2, "#131316"))
n11.append(text("s11_tkt", "BLOOD OXYGEN · SLEEP STAGES · 30-HOUR BATTERY · 100M WATER-RATED",
                PX, 428, 7, "#d9d9de", family="mono"))
n11.append(ltext("s11_el", "IN THE WILD", PX - 190, 505, 8, "#7a7a80",
                 weight=600))
n11.append(ltext("s11_eh", "Built for the distance", PX - 190, 532, 22, INK,
                 weight=800))
runner_tile("s11_ep1", PX - 150, 640, 280, 160, n11)
macro_tile("s11_ep2", PX + 150, 640, 280, 160, n11, dx=26, dy=-8, ws=90)
n11.append(text("s11_ec", "Engineered for those who move.", PX - 150, 700,
                8, "#ffffff", weight=600))
n11.append(rect("s11_db", PX, 830, 620, 190, 8, "#101014"))
n11.append(text("s11_dt", "Every detail, engineered to be felt.", PX, 780,
                16, "#ffffff", weight=700))
n11.append(text("s11_pr", "$399", PX - 90, 838, 22, LIME, weight=800))
n11.append(rect("s11_ab", PX + 70, 838, 120, 26, 13, LIME))
n11.append(text("s11_abt", "Add to bag", PX + 70, 838, 10, "#101014",
                weight=700))
n11.append(text("s11_dm2", "Free shipping · 30-day returns · Pay in 4", PX,
                885, 8, "#9a9aa0"))
n11.append(rect("s11_cta", PX, 990, 620, 110, 8, LIME))
n11.append(text("s11_ct1", "Be first on the wrist.", PX, 978, 24, INK,
                weight=800))
n11.append(text("s11_ct2", "Pre-order opens soon", PX, 1010, 9, "#333338"))
n11.append(text("s11_fq", "Good questions.", PX, 1120, 26, INK, weight=800))
FAQ = ["Is HiggsWatch a medical device?", "Which phones does it work with?",
       "Can I swim and dive with it?"]
for i, q in enumerate(FAQ):
    yq = 1168 + i * 36
    n11.append(ltext(f"s11_f{i}", q, PX - 200, yq, 11, "#333338"))
    n11.append(text(f"s11_fp{i}", "+", PX + 205, yq, 13, "#333338"))
    n11.append(rect(f"s11_fd{i}", PX, yq + 18, 430, 1.5, 0.5, "#c9c7ca"))
n11.append(rect("s11_ft", PX, 1330, 620, 110, 8, "#dcdadd"))
n11.append(ltext("s11_ftt", "Stay in the loop.", PX - 280, 1300, 13, INK,
                 weight=700))
n11.append(rect("s11_nm", PX - 235, 1330, 90, 24, 12, "#161616"))
n11.append(text("s11_nmt", "Notify me", PX - 235, 1330, 9, "#ffffff",
                weight=600))
n11.append(text("s11_fc", "PRODUCT        COMPANY        SUPPORT", PX + 150,
                1310, 8, "#55555a", weight=600))
n11.append(text("s11_cp", "© 2026 Higgswatch", PX + 150, 1345, 8, "#8a8a90"))
# the distilled cta: lime pre-order pill, glow pulsing
n11.append(rect("s11_pill", PX, 1560, 150, 44, 22, LIME,
                glow={"sigma": 26, "opacity": 0.5, "color": LIME}))
n11.append(text("s11_pt", "Pre-order", PX, 1560, 15, INK, weight=700))
track("s11_pill",
      glow_opacity=[(3.9, 0.35), (4.25, 0.9, "inOutCubic"),
                    (4.6, 0.35, "inOutCubic")])
actor("s11_jp", "Jagan96", MAG, MAG_CHIP, "#ffffff", PX + 88, 1588, n11,
      moves=[(3.9, 40, 30), (4.4, 0, 0, "outCubic")], t_in=3.85)
track("s11", cam_x=[(0, 0), (1.3, 0), (1.55, 760, "inCubic"),
                    (1.9, 1181, "outCubic")],
      cam_y=[(2.05, 0), (3.35, 780, "inOutCubic"),
             (4.15, 1240, "inOutCubic")])
scenes.append({"id": "s11", "bg": BG, "dur": 4.6,
               "transition": {"kind": "whip", "dur": 0.32, "dir": "left"},
               "nodes": n11})

# ---------------------------------------------------------------- s12: end card
n12 = []
n12.append(text("s12_t", "HIGGSFIELD PLUGINS FOR FIGMA AVAILABLE NOW ON HIGGSFIELD.AI",
                569, 320, 19, INK, weight=600))
gate("s12_t", 0.35, fade=0.35)
scenes.append({"id": "s12", "bg": "#e9e7ea", "dur": 2.0,
               "transition": {"kind": "fade", "dur": 0.4}, "nodes": n12})

stage = {
    "fps": 30,
    "size": [W, H],
    "audio": {"src": "/assets/audio/pad.m4a", "gain": 0.6, "fade_out": 0.8},
    "scenes": scenes,
}

with open("docs/higgsfield.stage.json", "w") as f:
    json.dump(stage, f, indent=1)
with open("docs/higgsfield.anim.json", "w") as f:
    json.dump({"tracks": tracks}, f, indent=1)
print("wrote docs/higgsfield.{stage,anim}.json:",
      sum(len(s["nodes"]) for s in scenes), "nodes,", len(tracks), "tracks,",
      round(sum(s["dur"] for s in scenes), 1), "s")
