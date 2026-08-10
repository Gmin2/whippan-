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
scene("i2", 2, ns, note="'it takes ->', two beats.")
tracks += ts
ns, ts = word_slide("i3", "a working prototype", 96, chip=False)
scene("i3", 2, ns, note="'a working prototype', two beats.")
tracks += ts

# ------------------------- i4: the sentence explodes into real parts
f96 = measure(96)
segs = ["a", "working", "prototype"]
widths = [f96.getlength(s) * CAL for s in segs]
gap = 168
total = sum(widths) + gap * 2
x = 960 - total / 2
i4_nodes = []
seg_x = []
for i, (s, w) in enumerate(zip(segs, widths)):
    seg_x.append(x + w / 2)
    i4_nodes.append(text(f"c{i}", s, round(x + w / 2, 1), 540, 96, INK,
                         650))
    x += w + gap
CHIPS = [
    ("t0", "/assets/solder/tile0.png",
     round(seg_x[0] + widths[0] / 2 + gap / 2, 1), 540, -8),
    ("t1", "/assets/solder/tile1.png",
     round(seg_x[1] + widths[1] / 2 + gap / 2, 1), 540, 7),
    ("t2", "/assets/solder/tile2.png", 640, 350, -6),
    ("t3", "/assets/solder/tile3.png", 1300, 730, 9),
]
for cid, src, cx, cy, rot in CHIPS:
    i4_nodes.append(rect(f"{cid}s", cx, cy, 132, 132, 26, "#ffffff",
                         glow={"sigma": 26, "opacity": 0.22,
                               "color": "#0a1030"}, rot=rot))
    i4_nodes.append(img(cid, src, cx, cy, 124, 124, radius=22, rot=rot))
i4_nodes.append(rect("warn", 1290, 360, 260, 74, 16, "#ffffff",
                     glow={"sigma": 22, "opacity": 0.18,
                           "color": "#0a1030"}, rot=-5))
i4_nodes.append(text("warnt", "3V3 on 5V!", 1290, 360, 27, "#e2620c", 650,
                     rot=-5))
scene("i4", 4, i4_nodes,
      note="The sentence explodes, brew-style: real part tiles pop in "
           "between the words on consecutive half-beats, a warning card "
           "crashes the party.")
for k, (cid, *_r) in enumerate(CHIPS):
    at = 0.1 + k * B * 0.5
    for nid in (f"{cid}s", cid):
        tracks.append(keyed(nid,
                            opacity=[(at, 0), (at + 0.12, 1)],
                            scale=[(at, 0.5), (at + 0.22, 1.08, "outCubic"),
                                   (at + 0.36, 1.0, "outCubic")]))
for nid in ("warn", "warnt"):
    at = 0.1 + 4 * B * 0.5
    tracks.append(keyed(nid,
                        opacity=[(at, 0), (at + 0.12, 1)],
                        scale=[(at, 0.5), (at + 0.22, 1.08, "outCubic"),
                               (at + 0.36, 1.0, "outCubic")]))

# ------------------- i5: the lovable days-counter pill, copied exactly:
# outlined capsule on black, a soft dark blob behind the digit, and the
# number rolling up like time piling on -- 2, 4, 6, 8 weeks.
DIGITS = ["2", "4", "6", "8"]
i5_nodes = [
    rect("ring", 960, 540, 760, 210, 105, "#2e2b29"),
    rect("ringin", 960, 540, 748, 198, 99, "#050505"),
    rect("blob", 800, 540, 330, 176, 88, "#2b211c", blur=16),
]
for i, d in enumerate(DIGITS):
    i5_nodes.append(text(f"dg{i}", d, 800, 540, 92, "#efe9df", 600,
                         opacity=0))
i5_nodes.append(text("wkt", "weeks", 1075, 540, 92, "#efe9df", 600))
scene("i5", 4, i5_nodes, bg="#050505",
      note="The lovable counter pill: outlined capsule, soft blob "
           "behind the digit, the number rolls 2-4-6-8 weeks.")
for nid in ("ring", "ringin", "blob"):
    tracks.append(keyed(nid,
                        opacity=[(0.05, 0), (0.2, 1)],
                        scale=[(0.05, 0.82), (0.32, 1.03, "outCubic"),
                               (0.48, 1.0, "outCubic")]))
tracks.append(keyed("wkt", opacity=[(0.15, 0), (0.3, 1)]))
for i, d in enumerate(DIGITS):
    at = 0.42 + i * B * 0.75
    last = i == len(DIGITS) - 1
    if last:
        tracks.append(keyed(f"dg{i}",
                            opacity=[(at, 0), (at + 0.1, 1)],
                            y=[(at, 30), (at + 0.2, 0, "outCubic")],
                            scale=[(at + 0.2, 1.0),
                                   (at + 0.32, 1.12, "outCubic"),
                                   (at + 0.48, 1.0, "outCubic")]))
        tracks.append({"target": f"dg{i}", "at": at + 0.2,
                       "state": "landed"})
    else:
        nxt = 0.42 + (i + 1) * B * 0.75
        tracks.append(keyed(f"dg{i}",
                            opacity=[(at, 0), (at + 0.1, 1),
                                     (nxt - 0.06, 1), (nxt, 0)],
                            y=[(at, 30), (at + 0.2, 0, "outCubic"),
                               (nxt - 0.06, 0), (nxt, -30)]))

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
PROMPT = "a palm sized quadcopter drone"
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
    "unit": "type", "cadence": 0.05, "dur": 0.04,
    "caret": "bar", "caret_typing": "solid"}})
tracks.append(keyed("send",
                    scale=[(send_at - 0.08, 1), (send_at, 0.85, "outCubic"),
                           (send_at + 0.12, 1, "outCubic")]))
tracks.append({"target": "send", "at": send_at, "state": "sent"})
tracks.append(keyed("flash", opacity=[(B * 5, 0), (B * 6 - 0.06, 1)]))

# ----------------------------- s5: the job log and the repair pill
LOG = [
    ("g1", "composing plan", "#c9ccd6", 0.10),
    ("g2", "picked 9 parts from the catalog", "#8a8f9c", 0.35),
    ("g3", "wired 14 nets", "#8a8f9c", 0.60),
    ("g4", "checking against physics", "#8a8f9c", 0.85),
]
log_nodes = [rect("lflash", 960, 540, 1920, 1080, 0, "#ffffff")]
for i, (gid, sline, col, _) in enumerate(LOG):
    x = 560 + len(sline) * 26 * MONO_W / 2
    log_nodes.append(text(gid, sline, round(x, 1), 300 + i * 54, 26, col,
                          family="mono"))
log_nodes += [
    rect("pill1", 960, 640, 980, 150, 75, "#221a16",
         glow={"sigma": 30, "opacity": 0.5, "color": "#7a3a12"}),
    text("pt1", "3V3 pin on a 5V net", 960, 640, 52, "#ff9d55", 600),
    rect("pill2", 960, 640, 980, 150, 75, "#12291f", opacity=0,
         glow={"sigma": 30, "opacity": 0.6, "color": "#1d6b47"}),
    text("pt2", "repaired.", 960, 640, 56, "#3ddc97", 650, opacity=0),
]
scene("s5", 6, log_nodes, bg="#0e1116",
      note="The log prints fast, then the fault capsule slams in orange "
           "and flips to 'repaired.' green on the beat. Camera dives in.")
tracks.append(keyed("lflash", opacity=[(0, 1), (0.16, 0)]))
for gid, sline, col, at in LOG:
    tracks.append(keyed(gid, opacity=[(at, 0), (at + 0.07, 1)]))
tracks.append(keyed("pill1",
                    opacity=[(B * 2, 0), (B * 2 + 0.1, 1), (B * 4, 1),
                             (B * 4 + 0.06, 0)],
                    scale=[(B * 2, 0.7), (B * 2 + 0.3, 1.04, "outCubic"),
                           (B * 2 + 0.5, 1.0, "outCubic")]))
tracks.append(keyed("pt1", opacity=[(B * 2, 0), (B * 2 + 0.12, 1),
                                    (B * 4, 1), (B * 4 + 0.06, 0)]))
tracks.append(keyed("pill2",
                    opacity=[(B * 4, 0), (B * 4 + 0.08, 1)],
                    scale=[(B * 4, 0.92), (B * 4 + 0.22, 1.05, "outCubic"),
                           (B * 4 + 0.4, 1.0, "outCubic")]))
tracks.append(keyed("pt2", opacity=[(B * 4, 0), (B * 4 + 0.1, 1)]))
tracks.append({"target": "pill2", "at": B * 4, "state": "clean"})
tracks.append({"target": "s5", "at": B * 5, "cam": {
    "preset": "zoom-promote", "z": 2.0, "anchor": [960, 640], "dur": 0.55}})

# ------------------- s6: the blueprint, snap reframes onto the parts
scene("s6", 6, [
    img("quad", "/assets/solder/quad.png", 960, 540, 1585, 1080),
], note="The real blueprint arrives, then dry snap reframes onto the "
        "part callouts: flight controller, motor corner, wide.")
tracks.append(keyed("quad",
                    opacity=[(0.0, 0), (0.1, 1)],
                    scale=[(0.0, 1.06), (0.4, 1.0, "outCubic")]))
tracks.append({"target": "s6", "keys": {
    "cam_zoom": step([(0, 1.0), (B * 2, 1.9), (B * 3.5, 1.9),
                      (B * 5, 1.0)]),
    "cam_ax": step([(0, 960), (B * 2, 1330), (B * 3.5, 700),
                    (B * 5, 960)]),
    "cam_ay": step([(0, 540), (B * 2, 420), (B * 3.5, 660),
                    (B * 5, 540)]),
}})

# ----------------------------------- c1..c3: the benefit run, brew-style
ns, ts = word_slide("b1", "real parts", 110, chip=False)
scene("c1", 1, ns, note="Benefit slide: real parts.")
tracks += ts
ns, ts = word_slide("b2", "real wiring", 110, chip=False, color="#ffffff")
scene("c2", 1, ns, bg=INK, note="Benefit slide inverted: real wiring.")
tracks += ts
ns, ts = word_slide("b3", "checked against physics", 96, chip=False,
                    color="#ffffff")
scene("c3", 2, ns, bg=BLUE, note="Benefit slide on blue: checked "
                                 "against physics.")
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
    text("tag7", "Cursor for hardware.", 960, 700, 40, GREY, 500),
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

total = sum(s["dur"] for s in scenes)
stage = {"fps": 30, "size": [W, H], "scenes": scenes,
         "audio": {"src": "/assets/audio/gen/solder.mp3", "gain": 0.85,
                   "fade_out": 0.35, "bpm": 123.0, "offset": 0.604,
                   "start": round(0.604 + 7 * B, 3)}}
anim = {"tracks": tracks}
json.dump(stage, open("docs/solder.stage.json", "w"), indent=1)
json.dump(anim, open("docs/solder.anim.json", "w"), indent=1)
print(f"wrote docs/solder.{{stage,anim}}.json, "
      f"{sum(len(s['nodes']) for s in scenes)} nodes, {len(tracks)} tracks, "
      f"{total:.2f}s")
