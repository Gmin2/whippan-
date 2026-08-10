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
scene("i1", 3, ns, note="Brew opening copied: huge 'Today' with the "
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
scene("i7", 4, [
    rect("glow7", 960, 520, 900, 380, 190, "#5e7cf7", blur=130,
         opacity=0.55),
    text("wm7i", "Solder", 960, 520, 170, "#ffffff", 600, "playfair"),
    text("sub7", "the AI that turns a prompt into buildable hardware",
         960, 680, 30, "#dfe6ff", 500),
], bg=BLUE,
    note="The glowing wordmark, brew-style: 'Solder' blooms white on "
         "blue, the promise line under it.")
tracks.append(keyed("glow7", opacity=[(0.05, 0), (0.4, 0.55)]))
tracks.append(keyed("wm7i", opacity=[(0.05, 0), (0.32, 1)],
                    scale=[(0.05, 0.92), (0.5, 1.0, "outCubic")]))
tracks.append(keyed("sub7", opacity=[(B, 0), (B + 0.3, 1)],
                    y=[(B, 20), (B + 0.4, 0, "outCubic")]))

# --------------------------- s3: the real homepage, dive into the bar
scene("s3", 4, [
    img("hb2", "/assets/solder/home-blur.png", 960, 540, 1920, 1080),
    img("home", "/assets/solder/home.png", 960, 540, 1920, 1080,
        opacity=0),
], note="Focus snaps onto the real homepage; the camera crash-zooms "
        "into the input bar, cut mid-motion.")
tracks.append({"target": "home", "keys": {"opacity": step(
    [(0, 0), (B * 0.5, 1)])}})
tracks.append({"target": "s3", "at": B * 1.5, "cam": {
    "preset": "crash-zoom", "z": 3.1, "anchor": [960, 655], "dur": 0.7}})

# ------------------------- s4: typing at zoom, send click, whiteout cut
PROMPT = "a pocket utility tool with a screen"
send_at = B * 4
scene("s4", 6, [
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
tracks.append(keyed("flash", opacity=[(B * 5, 0), (B * 6 - 0.06, 1)]))

# ---------------- s5: the real wiring schematic, snaps across cards
# 3184x1160 capture fit to 1920x700, centered on the studio background.
scene("s5", 5, [
    rect("wflash", 960, 540, 1920, 1080, 0, "#ffffff"),
    img("wshot", "/assets/solder/wiring.png", 960, 540, 1920, 700),
], bg="#f5f7ff",
    note="The real wiring schematic slides in; dry snaps across the "
         "cards: esp32 board, the display, wide.")
tracks.append(keyed("wflash", opacity=[(0, 1), (0.16, 0)]))
tracks.append(keyed("wshot",
                    x=[(0, 340), (0.42, 0, "outCubic")],
                    opacity=[(0, 0), (0.14, 1)]))
tracks.append({"target": "s5", "keys": {
    "cam_zoom": step([(0, 1.0), (B * 2, 1.75), (B * 3.5, 1.75),
                      (B * 4.5, 1.0)]),
    "cam_ax": step([(0, 960), (B * 2, 965), (B * 3.5, 1440),
                    (B * 4.5, 960)]),
    "cam_ay": step([(0, 540), (B * 2, 540), (B * 3.5, 420),
                    (B * 4.5, 540)]),
}})
tracks.append({"target": "wshot", "at": B * 2, "state": "snap1"})

# ------------------ s6: the assembly, exploded with callouts (real)
# 6368x3080 capture fit to 1920x929.
scene("s6", 5, [
    img("ashot", "/assets/solder/asm.png", 960, 540, 1920, 929),
], bg="#f5f7ff",
    note="Skipper transition: the exploded assembly rises in; slow "
         "push toward the stack, then wide.")
tracks.append(keyed("ashot",
                    y=[(0, 320), (0.45, 0, "outCubic")],
                    opacity=[(0, 0), (0.16, 1)]))
tracks.append({"target": "s6", "keys": {
    "cam_zoom": [{"t": 0.5, "v": 1.0},
                 {"t": B * 4.5, "v": 1.35, "ease": "inOutCubic"}],
    "cam_ax": [{"t": 0, "v": 960}],
    "cam_ay": [{"t": 0, "v": 520}],
}})

# ------------------------- s6b: the BOM -- what to buy, where, how much
scene("s6b", 5, [
    img("bshot", "/assets/solder/bom.png", 960, 540, 1920, 1080),
], bg="#f5f7ff",
    note="The BOM screen: every part, its ref, its source, its price -- "
         "$13.72 total. Slide in, then dive onto the total row.")
tracks.append(keyed("bshot",
                    x=[(0, 340), (0.42, 0, "outCubic")],
                    opacity=[(0, 0), (0.14, 1)]))
tracks.append({"target": "s6b", "at": B * 2.5, "cam": {
    "preset": "zoom-promote", "z": 1.8, "anchor": [1180, 390],
    "dur": 0.8}})
tracks.append({"target": "bshot", "at": B * 2.5, "state": "dive"})

# ----------------------------------- c1..c3: the benefit run, brew-style
ns, ts = word_slide("b1", "prototype hardware", 104, chip=False)
scene("c1", 1, ns, note="Closer: prototype hardware.")
tracks += ts
ns, ts = word_slide("b2", "fast and easy.", 110, chip=False, color="#ffffff")
scene("c2", 1, ns, bg=INK, note="Closer inverted: fast and easy.")
tracks += ts
ns, ts = word_slide("b3", "checked against physics", 96, chip=False,
                    color="#ffffff")
scene("c3", 2, ns, bg=BLUE, note="Closer on blue: checked against "
                                 "physics.")
tracks += ts

# ---------------- s7: crab ending -- the cursor comes back to the bar
BAR_W, BAR_H = 1044 * 0.62, 118 * 0.62
scene("s7", 6, [
    img("f1", "/assets/solder/home-blur.png", 260, 170, 850, 478,
        opacity=0),
    img("f2", "/assets/solder/quad-blur.png", 1700, 830, 780, 532,
        opacity=0),
    text("wm7", "Solder", 960, 380, 120, BLUE, 600, "playfair"),
    img("bar7", "/assets/solder/bar.png", 960, 570, round(BAR_W),
        round(BAR_H)),
    rect("caret7", round(960 - BAR_W / 2 + 34), 570, 3, 30, 1, INK,
         opacity=0),
    {"id": "cur", "type": "path", "x": 1400, "y": 900, "fill": "#16181d",
     "d": CURSOR, "keys": {"scale": [{"t": 0, "v": 2.2}]}},
    text("tag7", "Lovable for hardware.", 960, 700, 40, GREY, 500),
], note="Crab ending: blurred screens in the corners, the real bar "
        "under the wordmark, the cursor clicks it, the caret blinks on "
        "after the music stops.")
tracks.append(keyed("f1", opacity=[(0.1, 0), (0.5, 0.55)],
                    y=[(0.1, 30), (0.6, 0, "outCubic")]))
tracks.append(keyed("f2", opacity=[(0.2, 0), (0.6, 0.55)],
                    y=[(0.2, 30), (0.7, 0, "outCubic")]))
tracks.append(keyed("wm7", opacity=[(0.05, 0), (0.35, 1)],
                    y=[(0.05, 26), (0.45, 0, "outCubic")]))
tracks.append(keyed("bar7", opacity=[(B, 0), (B + 0.25, 1)],
                    y=[(B, 34), (B + 0.4, 0, "outCubic")]))
cx_end, cy_end = round(960 - BAR_W / 2 + 60), 596
tracks.append(keyed("cur",
                    x=[(B, 0), (B * 3, cx_end - 1400, "inOutCubic")],
                    y=[(B, 0), (B * 3, cy_end - 900, "inOutCubic")],
                    opacity=[(B - 0.01, 0), (B, 1)]))
tracks.append({"target": "bar7", "at": B * 3, "state": "focused"})
tracks.append({"target": "caret7", "keys": {"opacity": step(
    [(0, 0), (B * 3 + 0.05, 1), (B * 3 + 0.45, 0), (B * 3 + 0.85, 1),
     (B * 4 + 0.35, 0), (B * 4 + 0.75, 1), (B * 5 + 0.25, 0),
     (B * 5 + 0.65, 1)])}})
tracks.append({"target": "tag7", "at": B * 3.5, "reveal": {
    "unit": "scramble", "dur": 0.6, "churn": 4, "accent": "#6b7280"}})

# ref order: it takes -> the counter pill -> to create... the pill
# follows the chip inflation directly
order = {sc["id"]: sc for sc in scenes}
scenes = [order[k] for k in ["i1", "i2", "i5", "i3", "i4", "iq", "i6",
                             "i7", "s3", "s4", "s5", "s6", "s6b", "c1",
                             "c2", "c3", "s7"]]
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
