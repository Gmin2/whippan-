#!/usr/bin/env python3
# launch film for solder, opening copied from lovable's brew film:
# "Today ->" / "it takes ->" / "a working prototype" / the sentence
# explodes into a collage of real part tiles / the dark "weeks." pill /
# "Meet" / glowing "Solder" -- then the product run (real homepage,
# typed prompt, job log, blueprint snaps), a three-slide benefit run,
# and the crab ending with the cursor clicking the real bar.
# beat-locked at 123bpm. overlay contract: scene-local `at`, unique ids
# per scene, one track per node per property, x/y keys are offsets.
import json
import os

from PIL import ImageFont

W, H = 1920, 1080
B = 60.0 / 123.0
BLUE = "#2d52f0"
CREAM = "#f7f8fd"
INK = "#16181d"
GREY = "#6b7280"
MONO_W = 0.6

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def text(id, s, x, y, size, color=INK, weight=400, family="inter", **kw):
    n = {"id": id, "type": "text", "text": s, "x": x, "y": y,
         "color": color, "font": {"size": size, "weight": weight,
                                  "family": family}}
    n.update(kw)
    return n


def rect(id, x, y, w, h, r, fill, **kw):
    n = {"id": id, "type": "rect", "x": x, "y": y, "w": w, "h": h,
         "radius": r, "fill": fill}
    n.update(kw)
    return n


def img(id, src, x, y, w, h, **kw):
    n = {"id": id, "type": "image", "src": src, "x": x, "y": y,
         "w": w, "h": h}
    n.update(kw)
    return n


def keyed(nid, **props):
    keys = {}
    for name, seq in props.items():
        out = []
        for k in seq:
            kk = {"t": k[0], "v": k[1]}
            if len(k) > 2:
                kk["ease"] = k[2]
            out.append(kk)
        keys[name] = out
    return {"target": nid, "keys": keys}


def step(pairs):
    ks = []
    for t, v in pairs:
        if ks:
            ks.append({"t": round(t - 0.001, 4), "v": ks[-1]["v"]})
        ks.append({"t": round(t, 4), "v": v})
    return ks


def measure(size, weight=650):
    f = ImageFont.truetype("assets/fonts/Inter-Variable.ttf", size)
    try:
        f.set_variation_by_axes([weight])
    except Exception:
        pass
    return f


CAL = 1.105


def emphline(p, segs, y, size, weight=650):
    """one centered line of colored segments, measured with the real
    font so the seams are invisible."""
    segs = [(t.strip(), c) for t, c in segs]
    f = measure(size, weight)
    sp = f.getlength(" ") * CAL
    widths = [f.getlength(t) * CAL for t, _ in segs]
    total = sum(widths) + sp * (len(segs) - 1)
    x = 960 - total / 2
    ns = []
    for i, ((t, col), w) in enumerate(zip(segs, widths)):
        ns.append(text(f"{p}seg{i}", t, round(x + w / 2, 1), y, size, col,
                       weight))
        x += w + sp
    return ns


CURSOR = "M0 0L0 17.9L4.2 14.2L7.0 20.6L10.1 19.2L7.3 12.9L12.8 12.4Z"

tracks = []
scenes = []


def scene(id, dur_beats, nodes, bg=CREAM, note=""):
    scenes.append({"id": id, "bg": bg, "dur": round(B * dur_beats, 3),
                   "nodes": nodes, "note": note})


MARK_RECTS = [
    (0, 0, 512, 512, 120, "#2d52f0"),
    (134, 192, 34, 24, 7, "#ffffff"), (344, 192, 34, 24, 7, "#ffffff"),
    (192, 134, 24, 34, 7, "#ffffff"), (192, 344, 24, 34, 7, "#ffffff"),
    (134, 244, 34, 24, 7, "#ffffff"), (344, 244, 34, 24, 7, "#ffffff"),
    (244, 134, 24, 34, 7, "#ffffff"), (244, 344, 24, 34, 7, "#ffffff"),
    (134, 296, 34, 24, 7, "#ffffff"), (344, 296, 34, 24, 7, "#ffffff"),
    (296, 134, 24, 34, 7, "#ffffff"), (296, 344, 24, 34, 7, "#ffffff"),
    (168, 168, 176, 176, 30, "#ffffff"),
    (208, 208, 96, 96, 18, "#2d52f0"),
    (214, 214, 24, 24, 12, "#ffffff"),
]
INK_BRAND = "#0d1017"


def lockup(p, cx, cy, size, text_color=INK_BRAND, mark_only=False,
           weight=700):
    """the real solder lockup: chip mark + Inter-bold wordmark, sized by
    the mark edge. text sits right of the mark like the brand svg."""
    k = size / 512.0
    ns = []
    for i, (x, y, w, h, r, fill) in enumerate(MARK_RECTS):
        ns.append(rect(f"{p}m{i}", round(cx - size / 2 + (x + w / 2) * k, 1),
                       round(cy - size / 2 + (y + h / 2) * k, 1),
                       round(w * k, 1), round(h * k, 1),
                       round(r * k, 1), fill))
    if not mark_only:
        tsize = round(size * 1.1)
        f = measure(tsize, weight)
        tw = f.getlength("Solder") * CAL
        ns.append(text(f"{p}wt", "Solder",
                       round(cx + size / 2 + size * 0.42 + tw / 2, 1), cy,
                       tsize, text_color, weight))
    return ns


def lockup_ids(p, with_text=True):
    ids = [f"{p}m{i}" for i in range(len(MARK_RECTS))]
    if with_text:
        ids.append(f"{p}wt")
    return ids


TRI_D = "M4 3C2 3 0.8 5.2 1.8 7L10 21C11 22.8 13.5 22.8 14.5 21L22.7 7C23.7 5.2 22.5 3 20.5 3Z"


POINTER = "M0 0L30 11L16 16L11 30Z"


def pointer(p, sx, sy, tx, ty, at, color, label, side=1):
    """agent-code labeled cursor: sleek pointer that flies in from
    (sx,sy), lands its tip on (tx,ty), label pill riding the tail."""
    lsize = 26
    f = measure(lsize, 650)
    lw = f.getlength(label) * CAL
    pw = lw + 44
    ns = [
        {"id": f"{p}ptr", "type": "path", "x": tx, "y": ty, "fill": color,
         "d": POINTER, "keys": {"scale": [{"t": 0, "v": 1.6}]}},
        rect(f"{p}tag", round(tx + side * (30 + pw / 2), 1),
             round(ty + 74, 1), round(pw, 1), 54, 27, color),
        text(f"{p}lb", label, round(tx + side * (30 + pw / 2), 1),
             round(ty + 74, 1), lsize, "#ffffff", 650),
    ]
    dx, dy = sx - tx, sy - ty
    trs = []
    for nid in (f"{p}ptr", f"{p}tag", f"{p}lb"):
        trs.append(keyed(nid,
                         opacity=[(at, 0), (at + 0.12, 1)],
                         x=[(at, dx), (at + 0.5, round(-dx * 0.045, 1),
                             "inOutCubic"),
                            (at + 0.68, 0, "outCubic")],
                         y=[(at, dy), (at + 0.5, round(-dy * 0.045, 1),
                             "inOutCubic"),
                            (at + 0.68, 0, "outCubic")]))
    trs.append({"target": f"{p}ptr", "at": at + 0.55, "state": "land"})
    return ns, trs


def arrow_chip(p, x, y, r=34):
    """the brew arrow chip: dark circle, white arrow."""
    return [
        rect(f"{p}chip", x, y, r * 2, r * 2, r, INK),
        {"id": f"{p}arr", "type": "path", "x": x - 11, "y": y - 8,
         "stroke": 4.4, "fill": "#ffffff",
         "d": "M0 8L18 8M11 1L19 8L11 15",
         "keys": {"scale": [{"t": 0, "v": 1.2}]}},
    ]


def word_slide(p, s, size, at=0.08, color=INK, chip=True, weight=650):
    """brew word slide: big line, arrow chip trailing it."""
    f = measure(size, weight)
    w = f.getlength(s) * CAL
    ns = [text(f"{p}t", s, 960 - (76 if chip else 0), 540, size, color,
               weight)]
    trs = [keyed(f"{p}t", opacity=[(at, 0), (at + 0.22, 1)],
                 y=[(at, 34), (at + 0.34, 0, "outCubic")])]
    if chip:
        cx = 960 - 76 + w / 2 + 88
        ns += arrow_chip(p, round(cx, 1), 540)
        for nid in (f"{p}chip", f"{p}arr"):
            trs.append(keyed(nid, opacity=[(at + 0.12, 0), (at + 0.3, 1)],
                             y=[(at + 0.12, 34),
                                (at + 0.44, 0, "outCubic")]))
    return ns, trs


# --------------------------------------------------- i1..i3: Today / it
ns, ts = word_slide("i1", "Today", 170, chip=True)
scene("i1", 2, ns, note="Brew opening copied: huge 'Today' with the "
                        "arrow chip. Three beats.")
tracks += ts
ns, ts = word_slide("i2", "it takes", 96, chip=True)
scene("i2", 2, ns, note="'it takes ->': the arrow chip inflates at the "
                        "end and swallows the slide, birthing the pill.")
tracks += ts
tracks.append(keyed("i2chip",
                    scale=[(B * 2 - 0.24, 1), (B * 2 - 0.02, 16,
                            "inCubic")]))
tracks.append(keyed("i2arr", opacity=[(B * 2 - 0.24, 1),
                                      (B * 2 - 0.14, 0)]))
ns, ts = word_slide("i3", "to prototype hardware", 96, chip=False)
scene("i3", 2, ns, note="'to prototype hardware' -- the sentence "
                        "resolves. Two beats.")
tracks += ts

# --------------------------- i4: what parts do I need? (plain card)
i4_nodes = emphline("c4", [("what", INK), ("parts", BLUE),
                           ("do I need?", INK)], 540, 96)
scene("i4", 2, i4_nodes,
      note="Question 1: what parts do I need? Two beats, word-rise; the "
           "BOM screen answers it later.")
for i in range(3):
    tracks.append(keyed(f"c4seg{i}",
                        opacity=[(0.06 + i * 0.08, 0),
                                 (0.3 + i * 0.08, 1)],
                        y=[(0.06 + i * 0.08, 30),
                           (0.36 + i * 0.08, 0, "outCubic")]))

# ------------------- i5: the lovable days counter, copied exactly:
# black slide, near-invisible ring capsule, warm blob behind the digit,
# cream digits swapping straight at ~100ms, the word arriving with the
# pill expansion at "3", landing pop on 8, shrink-exit.
CNT = [("1", 0.000), ("2", 0.067), ("3", 0.167), ("4", 0.267),
       ("5", 0.333), ("6", 0.433), ("7", 0.533), ("8", 0.633)]
DSZ = 330
fw = measure(DSZ, 600)
weeks_w = fw.getlength("weeks") * CAL
digit_w = fw.getlength("8") * CAL
GAPW = 78
PADW = 230
block = digit_w + GAPW + weeks_w
FULL_W = block + 2 * PADW
left = 960 - block / 2
DIGIT_X_C, DIGIT_X_E = 860, round(left + digit_w / 2, 1)
WORD_X = left + digit_w + GAPW + weeks_w / 2
EXP_AT, EXP_D = 0.167, 0.18
i5_nodes = [
    rect("ringo", 960, 540, 1000, 590, 295, "#242021"),
    rect("ringi", 960, 540, 992, 582, 291, "#000000"),
    rect("blob", DIGIT_X_C, 540, 660, 500, 250, "#3a2a26", blur=34,
         opacity=0.95),
]
for i, (d, at) in enumerate(CNT):
    i5_nodes.append(text(f"dg{i}", d, DIGIT_X_C, 540, DSZ, "#f1eade",
                         600, opacity=0))
i5_nodes.append(text("wkt", "weeks", round(WORD_X, 1), 540, DSZ,
                     "#dad7cf", 600, opacity=0))
scene("i5", 4, i5_nodes, bg="#000000",
      note="The lovable counter, pixel-copied: compact pill counts 1-2, "
           "expands on 3 as 'weeks' arrives, counts to 8, pops, holds, "
           "shrinks out.")
for nid, w0, w1 in (("ringo", 1000, round(FULL_W)),
                    ("ringi", 992, round(FULL_W) - 8)):
    tracks.append(keyed(nid, w=[(EXP_AT, w0), (EXP_AT + EXP_D, w1,
                                "outCubic")]))
dx = DIGIT_X_E - DIGIT_X_C
blob_e = round((960 - FULL_W / 2) + 44 + 330 - DIGIT_X_C, 1)
tracks.append(keyed("blob",
                    x=[(EXP_AT, 0), (EXP_AT + EXP_D, blob_e,
                        "outCubic")]))
tracks.append(keyed("wkt", opacity=[(EXP_AT + 0.04, 0),
                                    (EXP_AT + EXP_D, 1),
                                    (1.62, 1), (1.9, 0)]))
for i, (d, at) in enumerate(CNT):
    nxt = CNT[i + 1][1] if i + 1 < len(CNT) else None
    o = [{"t": at - 0.001, "v": 0}, {"t": at, "v": 1}] if at > 0 else         [{"t": 0, "v": 1}]
    if nxt is not None:
        o += [{"t": nxt - 0.001, "v": 1}, {"t": nxt, "v": 0}]
    else:
        o += [{"t": 1.62, "v": 1}, {"t": 1.9, "v": 0}]
    tr = {"target": f"dg{i}", "keys": {"opacity": o}}
    if at > EXP_AT:
        tr["keys"]["x"] = [{"t": 0, "v": dx}]
    elif nxt is not None and nxt > EXP_AT:
        tr["keys"]["x"] = [{"t": EXP_AT, "v": 0},
                           {"t": EXP_AT + EXP_D, "v": dx,
                            "ease": "outCubic"}]
    tracks.append(tr)
    if 0 < at <= 0.633:
        tracks.append({"target": f"dg{i}", "at": at, "state": "tick"})
tracks.append(keyed("dg7", scale=[(0.633, 1.0), (0.72, 1.07, "outCubic"),
                                  (0.86, 1.0, "outCubic")]))
for nid in ("ringo", "ringi"):
    tracks.append(keyed(nid, opacity=[(1.62, 1), (1.9, 0)]))
tracks.append(keyed("blob", opacity=[(0, 0.95), (1.62, 0.95), (1.9, 0)]))

# ------------------------------ iq: and how will it even look?
iq_nodes = emphline("iq", [("and how will it even", INK),
                           ("look?", BLUE)], 540, 88)
scene("iq", 2, iq_nodes,
      note="Question 2: how will it even look? Two beats, word-rise.")
for i in range(2):
    tracks.append(keyed(f"iqseg{i}",
                        opacity=[(0.06 + i * 0.1, 0), (0.3 + i * 0.1, 1)],
                        y=[(0.06 + i * 0.1, 30),
                           (0.36 + i * 0.1, 0, "outCubic")]))

# --------------------------------------------- i6/i7: Meet / Solder
ns, ts = word_slide("m", "Meet", 150, chip=False, color="#ffffff")
scene("i6", 2, ns, bg=BLUE, note="'Meet' white on solder blue.")
tracks += ts
i7_nodes = [rect("glow7", 960, 510, 980, 400, 200, "#5e7cf7", blur=130,
                 opacity=0.55)]
i7_nodes += lockup("l7", 700, 510, 150, text_color="#ffffff")
i7_nodes.append(text("sub7",
                     "the AI that turns a prompt into buildable hardware",
                     960, 690, 30, "#dfe6ff", 500))
scene("i7", 4, i7_nodes, bg=BLUE,
      note="The real lockup blooms on blue: chip mark + Solder, the "
           "promise line under it.")
tracks.append(keyed("glow7", opacity=[(0.05, 0), (0.4, 0.55)]))
for nid in lockup_ids("l7"):
    tracks.append(keyed(nid, opacity=[(0.05, 0), (0.32, 1)],
                        scale=[(0.05, 0.92), (0.5, 1.0, "outCubic")]))
tracks.append(keyed("sub7", opacity=[(B, 0), (B + 0.3, 1)],
                    y=[(B, 20), (B + 0.4, 0, "outCubic")]))

# --------------------------- s3: the real homepage, dive into the bar
scene("s3", 3, [
    img("hb2", "/assets/solder/home-blur.png", 960, 540, 1920, 1080),
    img("home", "/assets/solder/home.png", 960, 540, 1920, 1080,
        opacity=0),
], note="Focus snaps onto the real homepage; the camera crash-zooms "
        "into the input bar, cut mid-motion.")
tracks.append({"target": "home", "keys": {"opacity": step(
    [(0, 0), (B * 0.5, 1)])}})
tracks.append({"target": "s3", "at": B * 1, "cam": {
    "preset": "crash-zoom", "z": 3.1, "anchor": [960, 655], "dur": 0.7}})

# ------------------------- s4: typing at zoom, send click, whiteout cut
PROMPT = "a pocket utility tool with a screen"
send_at = B * 3.5
scene("s4", 5, [
    img("home2", "/assets/solder/home.png", 960, 540, 1920, 1080),
    rect("cover", 936, 655, 452, 40, 8, "#ffffff"),
    text("typed", PROMPT, round(723 + len(PROMPT) * 16 * 0.5 * 0.5, 1), 655,
         16, "#1d1d1d"),
    img("send", "/assets/solder/send.png", 1191, 654, 38, 38),
    rect("flash", 960, 540, 1920, 1080, 0, "#ffffff", opacity=0),
], note="Held on the real bar: the prompt types itself, send clicks on "
        "the beat, whiteout swallows the cut.")
tracks.append(keyed("s4", cam_zoom=[(0, 3.1)], cam_ax=[(0, 960)],
                    cam_ay=[(0, 655)]))
tracks.append({"target": "typed", "at": 0.24, "reveal": {
    "unit": "type", "cadence": 0.045, "dur": 0.04,
    "caret": "bar", "caret_typing": "solid"}})
tracks.append(keyed("send",
                    scale=[(send_at - 0.08, 1), (send_at, 0.85, "outCubic"),
                           (send_at + 0.12, 1, "outCubic")]))
tracks.append({"target": "send", "at": send_at, "state": "sent"})
tracks.append(keyed("flash", opacity=[(B * 4, 0), (B * 5 - 0.06, 1)]))

# ---------------- s5: the real wiring schematic, snaps across cards
# 3184x1160 capture fit to 1920x700, centered on the studio background.
scene("s5", 4, [
    rect("wflash", 960, 540, 1920, 1080, 0, "#ffffff"),
    img("wshot", "/assets/solder/wiring.png", 960, 540, 1920, 700),
], bg="#f5f7ff",
    note="The real wiring schematic slides in; dry snaps across the "
         "cards: esp32 board, the display, wide.")
tracks.append(keyed("wflash", opacity=[(0, 1), (0.16, 0)]))
tracks.append(keyed("wshot",
                    x=[(0, 340), (0.42, 0, "outCubic")],
                    opacity=[(0, 0), (0.14, 1), (B * 3.2, 1),
                             (B * 3.95, 0.08)]))
ns, trs = pointer("an5", 2120, 950, 1010, 565, B * 0.35, "#e2620c",
                  "how to wire it")
scenes[-1]["nodes"] += ns
tracks += trs
tracks.append({"target": "s5", "keys": {
    "cam_zoom": step([(0, 1.0), (B * 1.2, 1.75), (B * 2.4, 1.75),
                      (B * 3.4, 1.0)]),
    "cam_ax": step([(0, 960), (B * 1.2, 965), (B * 2.4, 1440),
                    (B * 3.4, 960)]),
    "cam_ay": step([(0, 540), (B * 1.2, 540), (B * 2.4, 420),
                    (B * 3.4, 540)]),
}})
tracks.append({"target": "wshot", "at": B * 2, "state": "snap1"})

# ------------------ s6: the assembly, exploded with callouts (real)
# 6368x3080 capture fit to 1920x929.
scene("s6", 6, [
    {"id": "ashot", "type": "seq", "src": "/assets/solder/asmseq/",
     "fps": 26, "count": 74, "x": 960, "y": 540, "w": 1920, "h": 756},
], bg="#f5f7ff",
    note="The real assembly ANIMATION plays inside the film: the build "
         "explodes apart, labels land, and it snaps back together. "
         "Gentle push while it performs.")
tracks.append(keyed("ashot", opacity=[(0, 0), (0.14, 1)]))
ns, trs = pointer("an6", 2150, 780, 1105, 500, B * 1.2, "#2a9d8f",
                  "how it looks")
scenes[-1]["nodes"] += ns
tracks += trs
tracks.append({"target": "s6", "keys": {
    "cam_zoom": [{"t": 0.3, "v": 1.08},
                 {"t": B * 5.5, "v": 1.3, "ease": "inOutCubic"}],
    "cam_ax": [{"t": 0, "v": 960}],
    "cam_ay": [{"t": 0, "v": 520}],
}})

# ------------------------- s6b: the BOM -- what to buy, where, how much
# just the table, then the ai-1 move: the screen dissolves away and the
# wordmark rises out of it, handing off to the end card as a match cut.
scene("s6b", 4, [
    img("bshot", "/assets/solder/bom-table.png", 960, 500, 1840, 408),
], bg="#f5f7ff",
    note="The BOM table: every part, ref, source, price. Dive onto the "
         "total row, the callout arrow lands on $13.72.")
tracks.append(keyed("bshot",
                    x=[(0, 340), (0.42, 0, "outCubic")],
                    opacity=[(0, 0), (0.14, 1)]))
tracks.append({"target": "s6b", "at": B * 1.5, "cam": {
    "preset": "zoom-promote", "z": 1.55, "anchor": [1600, 570],
    "dur": 0.7}})
tracks.append({"target": "bshot", "at": B * 1.5, "state": "dive"})
ns, trs = pointer("an7", 700, 1160, 1745, 545, B * 1.1, BLUE,
                  "what to buy", side=-1)
scenes[-1]["nodes"] += ns
tracks += trs

# --------------- cnet: the ai-1 network carrying the solution flow:
# solder checks -> what to buy -> how it looks -> how to wire -> and the
# flow COMPLETES in a buildable card. wires draw, capsules grow along
# them, the icon morphs, the graph drifts, the bloom rises.
CHECK = "M2 9L7 14L16 3"
SQ = "M0 0L20 0L20 20L0 20Z"
BLOB = ("M10 0C16 0 20 4 20 10C20 16 16 20 10 20C4 20 0 16 0 10"
        "C0 4 4 0 10 0Z")
ARROW = "M2 12L22 3L15 22L11 14Z"


def capsule(pid, seed_x, seed_y, grow_w, label, at):
    """seed chip that grows into a labeled capsule along its wire."""
    ns = [
        rect(pid, seed_x, seed_y, 76, 76, 38, BLUE),
        text(f"{pid}t", label, round(seed_x + 40 + grow_w / 2 - 20, 1),
             seed_y, 44, "#ffffff", 650, opacity=0),
    ]
    dxc = round((grow_w - 76) / 2, 1)
    trs = [
        keyed(pid, opacity=[(at, 0), (at + 0.1, 1)],
              w=[(at, 76), (at + 0.42, grow_w, "outCubic")],
              x=[(at, 0), (at + 0.42, dxc, "outCubic")]),
        keyed(f"{pid}t", opacity=[(at + 0.3, 0), (at + 0.48, 1)]),
        {"target": pid, "at": at + 0.1, "state": "grow"},
    ]
    return ns, trs


cnet_nodes = [
    rect("bloom", 1780, 120, 1500, 1200, 600, "#c4d2ff", blur=180,
         opacity=0),
] + lockup("nl", 250, 330, 52) + [
    {"id": "nw1", "type": "path", "x": 0, "y": 0, "stroke": 2.6,
     "fill": "#8fa5f2", "d": "M445 330L610 330"},
    rect("ncard", 680, 330, 120, 120, 26, "#ffffff",
         glow={"sigma": 26, "opacity": 0.22, "color": "#12206b"}),
    {"id": "nicon", "type": "path", "x": 656, "y": 306, "fill": BLUE,
     "dseq": [{"at": 0.0, "d": SQ}, {"at": 1.15, "d": BLOB},
              {"at": 1.6, "d": ARROW}, {"at": 2.05, "d": SQ}],
     "keys": {"scale": [{"t": 0, "v": 2.4}]}},
    text("nlab", "checks", 680, 415, 24, GREY, 550),
    {"id": "nw2", "type": "path", "x": 0, "y": 0, "stroke": 2.6,
     "fill": "#8fa5f2", "d": "M740 330L870 430"},
    {"id": "nw3", "type": "path", "x": 0, "y": 0, "stroke": 2.6,
     "fill": "#8fa5f2", "d": "M1090 470L1090 560"},
    {"id": "nw4", "type": "path", "x": 0, "y": 0, "stroke": 2.6,
     "fill": "#8fa5f2", "d": "M1320 600L1320 690"},
    {"id": "nw5", "type": "path", "x": 0, "y": 0, "stroke": 2.6,
     "fill": "#8fa5f2", "d": "M1650 690L1800 690"},
    rect("fcard", 1880, 690, 110, 110, 24, "#ffffff",
         glow={"sigma": 24, "opacity": 0.22, "color": "#12206b"}),
    {"id": "fcheck", "type": "path", "x": 1862, "y": 673, "stroke": 5,
     "fill": "#1d9e63", "d": CHECK,
     "keys": {"scale": [{"t": 0, "v": 2.0}]}},
    text("flab", "buildable", 1880, 768, 24, GREY, 550),
]
c1n, c1t = capsule("p1", 940, 430, 380, "what to buy", B * 1.5)
c2n, c2t = capsule("p2", 1160, 560, 400, "how it looks", B * 2.75)
c3n, c3t = capsule("p3", 1390, 690, 400, "how to wire", B * 4)
# chips riding the seeds
c1n.append({"id": "p1cur", "type": "path", "x": 925, "y": 414,
            "fill": "#ffffff", "d": CURSOR,
            "keys": {"scale": [{"t": 0, "v": 1.4}]}})
c2n.append({"id": "p2ar", "type": "path", "x": 1142, "y": 545,
            "fill": "#ffffff", "d": ARROW,
            "keys": {"scale": [{"t": 0, "v": 1.4}]}})
c3n.append({"id": "p3ck", "type": "path", "x": 1372, "y": 674,
            "stroke": 4.2, "fill": "#ffffff", "d": CHECK,
            "keys": {"scale": [{"t": 0, "v": 1.8}]}})
cnet_nodes += c1n + c2n + c3n
scene("cnet", 7, cnet_nodes,
      note="The solution flow as the ai-1 network: solder checks, then "
           "what to buy, how it looks, how to wire grow along their "
           "wires -- and the flow completes in a buildable card.")
tracks += c1t + c2t + c3t
tracks.append(keyed("bloom", opacity=[(0.3, 0), (B * 6, 0.5)]))
for nid in lockup_ids("nl"):
    tracks.append(keyed(nid, opacity=[(0.05, 0), (0.25, 1)]))
tracks.append(keyed("nw1", opacity=[(0.3, 0), (0.42, 1)]))
tracks.append(keyed("ncard",
                    opacity=[(0.42, 0), (0.56, 1)],
                    scale=[(0.42, 0.6), (0.62, 1.06, "outCubic"),
                           (0.78, 1.0, "outCubic")]))
tracks.append(keyed("nicon", opacity=[(0.5, 0), (0.64, 1)]))
tracks.append(keyed("nlab", opacity=[(0.56, 0), (0.7, 1)]))
tracks.append({"target": "ncard", "at": 0.45, "state": "pop"})
for wid, at in (("nw2", B * 1.5 - 0.16), ("nw3", B * 2.75 - 0.16),
                ("nw4", B * 4 - 0.16), ("nw5", B * 5 - 0.16)):
    tracks.append(keyed(wid, opacity=[(at, 0), (at + 0.12, 1)]))
for nid, at in (("p1cur", B * 1.5), ("p2ar", B * 2.75), ("p3ck", B * 4)):
    tracks.append(keyed(nid, opacity=[(at, 0), (at + 0.1, 1)]))
for nid in ("fcard", "fcheck", "flab"):
    tracks.append(keyed(nid,
                        opacity=[(B * 5, 0), (B * 5 + 0.16, 1)],
                        scale=[(B * 5, 0.6), (B * 5 + 0.3, 1.06,
                               "outCubic"),
                               (B * 5 + 0.46, 1.0, "outCubic")]))
tracks.append({"target": "fcard", "at": B * 5 + 0.1, "state": "done"})
tracks.append({"target": "cnet", "keys": {
    "cam_x": [{"t": B * 1.5, "v": 0}, {"t": B * 7, "v": 380,
               "ease": "inOutCubic"}],
    "cam_y": [{"t": B * 1.5, "v": 0}, {"t": B * 7, "v": 130,
               "ease": "inOutCubic"}],
}})

# ---------------- s7: the close -- clean, staged, and it completes.
# lockup lands, the real bar rises, the cursor clicks it, the caret
# starts blinking, both lines arrive, and the film HOLDS on the living
# bar while the music resolves.
BAR_W, BAR_H = 1044 * 0.62, 118 * 0.62
s7_nodes = lockup("el", 700, 400, 110) + [
    img("bar7", "/assets/solder/bar.png", 960, 620, round(BAR_W),
        round(BAR_H)),
    rect("caret7", round(960 - BAR_W / 2 + 34), 620, 3, 30, 1, INK,
         opacity=0),
    {"id": "cur", "type": "path", "x": 1500, "y": 950, "fill": "#16181d",
     "d": CURSOR, "keys": {"scale": [{"t": 0, "v": 2.2}]}},
    text("tag7", "Type it. Build it.", 960, 772, 44, INK, 650,
         opacity=0),
    text("sub7e", "Lovable for hardware.", 960, 836, 28, GREY, 500,
         opacity=0),
]
scene("s7", 8, s7_nodes,
      note="The close: lockup lands with a click, the real bar rises, "
           "the cursor glides in and clicks it, the caret blinks, both "
           "lines arrive -- and the film holds on the living bar while "
           "the music resolves.")
for nid in lockup_ids("el"):
    tracks.append(keyed(nid, opacity=[(0.08, 0), (0.3, 1)],
                        y=[(0.08, 30), (0.44, 0, "outCubic")]))
tracks.append({"target": "elm0", "at": 0.25, "state": "land"})
tracks.append(keyed("bar7", opacity=[(B, 0), (B + 0.25, 1)],
                    y=[(B, 34), (B + 0.4, 0, "outCubic")]))
cx_end, cy_end = round(960 - BAR_W / 2 + 60), 646
tracks.append(keyed("cur",
                    x=[(B * 1.5, 0), (B * 3, cx_end - 1500,
                        "inOutCubic")],
                    y=[(B * 1.5, 0), (B * 3, cy_end - 950,
                        "inOutCubic")],
                    opacity=[(B * 1.5 - 0.01, 0), (B * 1.5, 1)]))
tracks.append({"target": "bar7", "at": B * 3, "state": "focused"})
tracks.append({"target": "caret7", "keys": {"opacity": step(
    [(0, 0), (B * 3 + 0.05, 1), (B * 3 + 0.5, 0), (B * 3 + 0.95, 1),
     (B * 4 + 0.4, 0), (B * 4 + 0.85, 1), (B * 5 + 0.3, 0),
     (B * 5 + 0.75, 1), (B * 6 + 0.2, 0), (B * 6 + 0.65, 1),
     (B * 7 + 0.1, 0), (B * 7 + 0.55, 1)])}})
tracks.append(keyed("tag7", opacity=[(B * 3.5, 0), (B * 3.5 + 0.3, 1)],
                    y=[(B * 3.5, 26), (B * 3.5 + 0.45, 0, "outCubic")]))
tracks.append(keyed("sub7e", opacity=[(B * 4.5, 0), (B * 4.5 + 0.3, 1)],
                    y=[(B * 4.5, 20), (B * 4.5 + 0.45, 0, "outCubic")]))

total = sum(s["dur"] for s in scenes)
stage = {"fps": 30, "size": [W, H], "scenes": scenes,
         "audio": {"src": "/assets/audio/gen/solder.mp3", "gain": 0.85,
                   "fade_out": 0.35, "bpm": 123.0, "offset": 0.604,
                   "start": round(0.604 + 3 * B, 3)}}
anim = {"tracks": tracks}
json.dump(stage, open("docs/solder.stage.json", "w"), indent=1)
json.dump(anim, open("docs/solder.anim.json", "w"), indent=1)
print(f"wrote docs/solder.{{stage,anim}}.json, "
      f"{sum(len(s['nodes']) for s in scenes)} nodes, {len(tracks)} tracks, "
      f"{total:.2f}s")
