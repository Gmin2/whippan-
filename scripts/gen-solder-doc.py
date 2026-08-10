#!/usr/bin/env python3
# launch film for solder -- cursor for hardware. cut from the grammar of
# crab (soft-blurred real screens, a cursor with a life of its own, crisp
# cards floating over blur) and design (scramble reveals, dry 1-frame
# snaps, question -> answer rhythm). the spine is the three questions a
# prototyper actually has: where do i start / how do i build it / how
# will it look. every scene is a whole number of beats at 123bpm and
# every screen is a real capture.
# overlay contract: scene-local `at`, unique ids per scene, one track per
# node per property, x/y keys are offsets.
import json
import os

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


# macOS pointer, tip at local (0,0)
CURSOR = "M0 0L0 17.9L4.2 14.2L7.0 20.6L10.1 19.2L7.3 12.9L12.8 12.4Z"

tracks = []
scenes = []


def scene(id, dur_beats, nodes, bg=CREAM, note=""):
    scenes.append({"id": id, "bg": bg, "dur": round(B * dur_beats, 3),
                   "nodes": nodes, "note": note})


from PIL import ImageFont


def emphline(p, segs, y, size, weight=650):
    """one centered line of colored segments (lovable's word emphasis),
    measured with the real font so the seams are invisible."""
    segs = [(t.strip(), c) for t, c in segs]
    f = ImageFont.truetype("assets/fonts/Inter-Variable.ttf", size)
    try:
        f.set_variation_by_axes([weight])
    except Exception:
        pass
    # engine shaping runs ~10.5% wider than PIL at the same px size
    CAL = 1.105
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


# ------------------------------------------------ s1: scramble cold open
scene("s1", 4, [
    text("t1", "you want to build hardware.", 960, 500, 92, INK, 600,
         "playfair"),
    text("t2", "not fight it.", 960, 620, 92, BLUE, 600, "playfair"),
], note="Design-style cold open: the line scrambles into place, the "
        "kicker snaps in on beat 2. Four beats.")
tracks.append({"target": "t1", "at": 0.08, "reveal": {
    "unit": "scramble", "dur": 0.8, "churn": 5, "accent": "#16181d"}})
tracks.append({"target": "t2", "keys": {"opacity": step([(0, 0), (B * 2, 1)])}})

# --------------------------------- q1: where do you even start? (cream)
scene("q1", 2, emphline("q", [("where do you even", INK),
                              ("start?", BLUE)], 540, 88),
      note="Question card 1 on flat cream: word-rise entrance, hard cut "
           "out. Two beats.")
for i in range(2):
    tracks.append(keyed(f"qseg{i}",
                        opacity=[(0.06 + i * 0.1, 0), (0.3 + i * 0.1, 1)],
                        y=[(0.06 + i * 0.1, 30),
                           (0.36 + i * 0.1, 0, "outCubic")]))

# --------------------------- s3: focus lands, then dive into the bar
scene("s3", 4, [
    img("hb2", "/assets/solder/home-blur.png", 960, 540, 1920, 1080),
    img("home", "/assets/solder/home.png", 960, 540, 1920, 1080,
        opacity=0),
], note="The answer: focus snaps to the real homepage -- start with a "
        "sentence. Camera crash-zooms into the input bar, cut "
        "mid-motion.")
tracks.append({"target": "home", "keys": {"opacity": step([(0, 0), (B * 0.5, 1)])}})
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

# ------------------------------ q2: how do you even build it? (ink)
q2_nodes = emphline("b", [("how do you even", "#f5f5f7"),
                          ("build", "#7c93ff"), ("it?", "#f5f5f7")],
                    540, 88)
scene("q2", 2, q2_nodes, bg=INK,
      note="Question card 2 inverted on ink: the line slides in from "
           "the left with overshoot. Two beats.")
for i in range(3):
    tracks.append(keyed(f"bseg{i}",
                        x=[(0.05 + i * 0.05, -120),
                           (0.32 + i * 0.05, 14, "outCubic"),
                           (0.45 + i * 0.05, 0, "outCubic")],
                        opacity=[(0.05 + i * 0.05, 0),
                                 (0.28 + i * 0.05, 1)]))

# ----------------------------- s5: the job log answers "how to build"
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
# the lovable pill: fault capsule flips to the repaired capsule
log_nodes += [
    rect("pill1", 960, 640, 980, 150, 75, "#221a16",
         glow={"sigma": 30, "opacity": 0.5, "color": "#7a3a12"}),
    text("pt1", "3V3 pin on a 5V net", 960, 640, 52, "#ff9d55", 600),
    rect("pill2", 960, 640, 980, 150, 75, "#12291f", opacity=0,
         glow={"sigma": 30, "opacity": 0.6, "color": "#1d6b47"}),
    text("pt2", "repaired.", 960, 640, 56, "#3ddc97", 650, opacity=0),
]
scene("s5", 6, log_nodes, bg="#0e1116",
      note="The log prints fast up top, then the lovable pill: the fault "
           "capsule slams in orange and flips to 'repaired.' green on "
           "the beat. Camera dives into the pill.")
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

# ------------------------------ sq: the second question card, two beats
scq_nodes = emphline("k", [("and how will it", "#ffffff"),
                           ("look?", "#bcd0ff")], 540, 84)
scene("sq", 2, scq_nodes, bg=BLUE,
      note="Question card 3 on flat solder blue: scale-settle pop. Two "
           "beats.")
for i in range(2):
    tracks.append(keyed(f"kseg{i}",
                        opacity=[(0.05 + i * 0.08, 0),
                                 (0.26 + i * 0.08, 1)],
                        scale=[(0.05 + i * 0.08, 0.85),
                               (0.34 + i * 0.08, 1.04, "outCubic"),
                               (0.48 + i * 0.08, 1.0, "outCubic")]))

# --------------------------- s6: the blueprint arrives, wide and calm
scene("s6", 4, [
    img("quad", "/assets/solder/quad.png", 960, 540, 1585, 1080),
], note="The answer: the real blueprint fills the frame with a slow "
        "drift. Four beats.")
tracks.append(keyed("quad",
                    opacity=[(0.0, 0), (0.1, 1)],
                    scale=[(0.0, 1.06), (0.4, 1.0, "outCubic")]))
tracks.append({"target": "s6", "keys": {
    "cam_zoom": [{"t": 0.4, "v": 1.0}, {"t": B * 4, "v": 1.05}]}})

# ------------------------- q4: and what parts do you buy? (cream)
q4_nodes = emphline("d", [("and what", INK), ("parts", BLUE),
                          ("do you buy?", INK)], 540, 84)
scene("q4", 2, q4_nodes,
      note="Question card 4 back on cream: scramble entrance. Two "
           "beats.")
tracks.append({"target": "dseg0", "at": 0.05, "reveal": {
    "unit": "scramble", "dur": 0.4, "churn": 4, "accent": "#16181d"}})
tracks.append({"target": "dseg1", "at": 0.15, "reveal": {
    "unit": "scramble", "dur": 0.4, "churn": 4, "accent": "#2d52f0"}})
tracks.append({"target": "dseg2", "at": 0.25, "reveal": {
    "unit": "scramble", "dur": 0.4, "churn": 4, "accent": "#16181d"}})

# ------------------- s6b: the parts answer -- snap onto the callouts
scene("s6b", 4, [
    img("quad2", "/assets/solder/quad.png", 960, 540, 1585, 1080),
], note="The answer is on the drawing: dry snap reframes onto the part "
        "callouts -- flight controller, then the motor corner, then "
        "wide. Every label is a real catalog part.")
tracks.append({"target": "s6b", "keys": {
    "cam_zoom": step([(0, 1.0), (B, 1.9), (B * 2.5, 1.9), (B * 3.5, 1.0)]),
    "cam_ax": step([(0, 960), (B, 1330), (B * 2.5, 700), (B * 3.5, 960)]),
    "cam_ay": step([(0, 540), (B, 420), (B * 2.5, 660), (B * 3.5, 540)]),
}})

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
], note="Crab ending, entirely new: blurred screens drift in the "
        "corners, the real input bar floats center under the wordmark, "
        "the cursor glides in and clicks it, the caret starts blinking, "
        "the tagline scrambles in. Music stops; the caret keeps going.")
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
