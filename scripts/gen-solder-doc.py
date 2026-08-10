#!/usr/bin/env python3
# launch film for solder, cut in the reference grammar (radio-main /
# design / lq4 / lovable): every scene lasts a whole number of beats at
# 123bpm, cuts are hard and land on the grid, the camera moves ARE the
# transitions (crash-zoom into the bar, whiteout on send, snap reframes
# across the blueprint), typography punches between product screens.
# screens are real captures: the homepage from localhost:5260, the
# settled quadcopter diagram from the vector-hardware harness.
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
    """hard-stepped keys: hold the previous value until the next instant."""
    ks = []
    for t, v in pairs:
        if ks:
            ks.append({"t": round(t - 0.001, 4), "v": ks[-1]["v"]})
        ks.append({"t": round(t, 4), "v": v})
    return ks


tracks = []
scenes = []


def scene(id, dur_beats, nodes, bg=CREAM, note=""):
    scenes.append({"id": id, "bg": bg, "dur": round(B * dur_beats, 3),
                   "nodes": nodes, "note": note})


# ---------------------------------------------- s1: cold open typography
scene("s1", 4, [
    text("t1a", "You know what you want to build.", 960, 470, 82, INK, 600,
         "playfair"),
    text("t1b", "The wiring is where it dies.", 960, 590, 82, BLUE, 600,
         "playfair"),
], note="Cold open, serif on cream: word-by-word slam, second line in "
        "solder blue. Four beats.")
tracks.append({"target": "t1a", "at": 0.10, "reveal": {
    "unit": "word", "stagger": 0.07, "dur": 0.22, "rise": 26,
    "accent": "#16181d"}})
tracks.append({"target": "t1b", "at": B * 2, "reveal": {
    "unit": "word", "stagger": 0.07, "dur": 0.22, "rise": 26,
    "accent": "#2d52f0"}})

# ------------------------------------------- s2: three punch cards, 1 beat
scene("p1", 1, [text("w1", "datasheets.", 960, 540, 110, INK, 700,
                     "playfair")],
      note="Punch card 1, one beat: datasheets.")
scene("p2", 1, [text("w2", "pinouts.", 960, 540, 110, CREAM, 700,
                     "playfair")], bg=INK,
      note="Punch card 2, inverted, one beat: pinouts.")
scene("p3", 1, [text("w3", "a 5V pin on a 3.3V net.", 960, 540, 84,
                     "#ffffff", 700, "playfair")], bg=BLUE,
      note="Punch card 3, solder blue, one beat: the killer mistake.")

# ------------------------------- s3: the real homepage, then dive at beat 3
scene("s3", 5, [
    {"id": "home", "type": "image", "src": "/assets/solder/home.png",
     "x": 960, "y": 540, "w": 1920, "h": 1080},
], note="The real homepage slams in and settles fast; on beat 3 the "
        "camera crash-zooms into the input bar. Cut mid-motion.")
tracks.append(keyed("home",
                    opacity=[(0.0, 0), (0.12, 1)],
                    scale=[(0.0, 1.07), (0.38, 1.0, "outCubic")]))
tracks.append({"target": "s3", "at": B * 3, "cam": {
    "preset": "crash-zoom", "z": 3.1, "anchor": [960, 655], "dur": 0.75}})

# ------------------------- s4: typing at zoom, send click, whiteout cut
PROMPT = "a palm sized quadcopter drone"
CAD = 0.05
type_at = 0.24
send_at = B * 4
scene("s4", 6, [
    {"id": "home2", "type": "image", "src": "/assets/solder/home.png",
     "x": 960, "y": 540, "w": 1920, "h": 1080},
    rect("cover", 936, 655, 452, 40, 8, "#ffffff"),
    text("typed", PROMPT, round(723 + len(PROMPT) * 16 * 0.5 * 0.5, 1), 655,
         16, "#1d1d1d"),
    {"id": "send", "type": "image", "src": "/assets/solder/send.png",
     "x": 1191, "y": 654, "w": 38, "h": 38},
    rect("flash", 960, 540, 1920, 1080, 0, "#ffffff", opacity=0),
], note="Held zoomed on the bar: the prompt types itself, the send "
        "button clicks on the beat, whiteout swallows the screen.")
tracks.append(keyed("s4", cam_zoom=[(0, 3.1)], cam_ax=[(0, 960)],
                    cam_ay=[(0, 655)]))
tracks.append({"target": "typed", "at": type_at, "reveal": {
    "unit": "type", "cadence": CAD, "dur": 0.04,
    "caret": "bar", "caret_typing": "solid"}})
tracks.append(keyed("send",
                    scale=[(send_at - 0.08, 1), (send_at, 0.85, "outCubic"),
                           (send_at + 0.12, 1, "outCubic")]))
tracks.append({"target": "send", "at": send_at, "state": "sent"})
tracks.append(keyed("flash", opacity=[(B * 5, 0), (B * 6 - 0.06, 1)]))

# ----------------------------- s5: the job log, full-bleed, prints fast
LOG = [
    ("g1", "composing plan", "#c9ccd6", 0.10),
    ("g2", "picked 9 parts from the catalog", "#8a8f9c", 0.35),
    ("g3", "wired 14 nets", "#8a8f9c", 0.60),
    ("g4", "checking against physics", "#8a8f9c", 0.85),
    ("g5", "!  IMU 3V3 pin found on a 5V net", "#ff8a3d", B * 3),
    ("g6", "repaired -- second pass clean", "#3ddc97", B * 4),
]
log_nodes = [rect("lflash", 960, 540, 1920, 1080, 0, "#ffffff")]
for i, (gid, s, col, _) in enumerate(LOG):
    x = 560 + len(s) * 30 * MONO_W / 2
    log_nodes.append(text(gid, s, round(x, 1), 380 + i * 66, 30, col,
                          family="mono"))
log_nodes.append(rect("lcaret", 566, 380 + 5 * 66 + 66, 16, 34, 1,
                      "#3ddc97"))
scene("s5", 6, log_nodes, bg="#0e1116",
      note="Whiteout decays into the job log, full-bleed: lines print on "
           "the grid, the fault hits orange on beat 3, the repair lands "
           "green on beat 4. Camera dives into the green line.")
tracks.append(keyed("lflash", opacity=[(0, 1), (0.16, 0)]))
for gid, s, col, at in LOG:
    tracks.append(keyed(gid, opacity=[(at, 0), (at + 0.07, 1)]))
tracks.append({"target": "g6", "at": B * 4, "state": "clean"})
tracks.append(keyed("lcaret",
                    opacity=[(0, 0), (B * 4, 0), (B * 4 + 0.02, 1),
                             (B * 4 + 0.4, 1), (B * 4 + 0.42, 0),
                             (B * 4 + 0.8, 0), (B * 4 + 0.82, 1)]))
tracks.append({"target": "s5", "at": B * 5, "cam": {
    "preset": "zoom-promote", "z": 2.3, "anchor": [820, 776], "dur": 0.55}})

# ------------------- s6: the blueprint, full-bleed, snap reframes on beats
# label positions in film coords (3992x2720 capture fit to 1585x1080)
scene("s6", 8, [
    {"id": "quad", "type": "image", "src": "/assets/solder/quad.png",
     "x": 960, "y": 540, "w": 1585, "h": 1080},
], note="The real blueprint fills the frame. Snap reframes on the grid: "
        "flight controller, then the motor corner, then wide. Dry cuts, "
        "design-style.")
tracks.append(keyed("quad",
                    opacity=[(0.0, 0), (0.1, 1)],
                    scale=[(0.0, 1.06), (0.4, 1.0, "outCubic")]))
tracks.append({"target": "s6", "keys": {
    "cam_zoom": step([(0, 1.0), (B * 3, 1.85), (B * 5, 1.85),
                      (B * 7, 1.0)]),
    "cam_ax": step([(0, 960), (B * 3, 1330), (B * 5, 700), (B * 7, 960)]),
    "cam_ay": step([(0, 540), (B * 3, 420), (B * 5, 660), (B * 7, 540)]),
}})

# --------------------------------------------------- s7: end card, brand
scene("s7", 5, [
    text("wm", "Solder", 960, 470, 200, BLUE, 600, "playfair"),
    text("tag", "Type it. Build it.", 960, 650, 42, INK, 600),
    text("sub", "The AI that turns a prompt into buildable hardware.",
         960, 716, 26, GREY),
    rect("ecaret", 1206, 655, 4, 40, 1, INK, opacity=0),
], note="Brand close on cream: blue serif wordmark, the tagline types, "
        "the caret keeps blinking after the music stops.")
tracks.append(keyed("wm", opacity=[(0.05, 0), (0.3, 1)],
                    y=[(0.05, 36), (0.42, 0, "outCubic")]))
tracks.append({"target": "tag", "at": B * 1, "reveal": {
    "unit": "type", "cadence": 0.045, "dur": 0.04, "caret": "none"}})
tracks.append(keyed("sub", opacity=[(B * 2, 0), (B * 2 + 0.3, 1)]))
tracks.append(keyed("ecaret",
                    opacity=[(B * 1 + 0.045 * 18, 1), (B * 3, 1),
                             (B * 3 + 0.02, 0), (B * 3 + 0.42, 0),
                             (B * 3 + 0.44, 1), (B * 4, 1),
                             (B * 4 + 0.02, 0), (B * 4 + 0.44, 0),
                             (B * 4 + 0.46, 1)]))

total = sum(s["dur"] for s in scenes)
# bed starts so film t=0 sits on the track's beat grid
stage = {"fps": 30, "size": [W, H], "scenes": scenes,
         "audio": {"src": "/assets/audio/gen/solder.mp3", "gain": 0.85,
                   "fade_out": 0.35, "bpm": 123.0, "offset": 0.604,
                   "start": round(0.604 + 7 * B, 3)}}
anim = {"tracks": tracks}
json.dump(stage, open("docs/solder.stage.json", "w"), indent=1)
json.dump(anim, open("docs/solder.anim.json", "w"), indent=1)
print(f"wrote docs/solder.{{stage,anim}}.json, "
      f"{sum(len(s['nodes']) for s in scenes)} nodes, {len(tracks)} tracks, "
      f"{total:.2f}s, beat {B:.4f}")
