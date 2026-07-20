#!/usr/bin/env python3
# reproduction of animations/x-anim (14.24s, 2274x1168): the fixed-cursor
# X promo. the cursor is pinned for all 418 frames; install card -> plus
# circle -> avatar sphere -> composer -> typed caption + icon ring -> crash
# zoom onto Post -> whip out to the published tweet -> reply thread ->
# whiteout -> headline -> CTA -> X icon. one scene, zero cuts: the camera
# is faked as per-node world transforms so the cursor stays put.
# timings in seconds from the VFR teardown ledger.
import json
import math
import os

W, H = 2274, 1168
CURSOR = (1146, 594)          # parked all video
POST_ANCHOR = (1815, 1005)    # the crash zoom aims here
K = 0.5523

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def text(id, s, x, y, size, color, weight=400, family="inter"):
    return {"id": id, "type": "text", "text": s, "x": x, "y": y,
            "color": color, "font": {"size": size, "weight": weight,
                                     "family": family}}


def rect(id, x, y, w, h, r, fill, **kw):
    n = {"id": id, "type": "rect", "x": x, "y": y, "w": w, "h": h,
         "radius": r, "fill": fill}
    n.update(kw)
    return n


def path(id, x, y, d, fill, stroke=None, **kw):
    n = {"id": id, "type": "path", "x": x, "y": y, "d": d, "fill": fill}
    if stroke:
        n["stroke"] = stroke
    n.update(kw)
    return n


def circle_d(r):
    k = r * K
    return (f"M{-r} 0C{-r} {-k} {-k} {-r} 0 {-r}C{k} {-r} {r} {-k} {r} 0"
            f"C{r} {k} {k} {r} 0 {r}C{-k} {r} {-r} {k} {-r} 0Z")


def star_d(r=11):
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.42
        pts.append((rr * math.cos(a), rr * math.sin(a)))
    return "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in pts) + "Z"


def x_glyph_d(s=44):
    """the X logotype as a bold two-stroke path."""
    w = s * 0.16
    return (f"M{-s/2} {-s/2}L{-s/2+w*1.6} {-s/2}L{s/2} {s/2}L{s/2-w*1.6} {s/2}Z"
            f"M{s/2-w*1.6} {-s/2}L{s/2} {-s/2}L{-s/2+w*1.6} {s/2}L{-s/2} {s/2}Z")


def avatar_d(r=40):
    """grey silhouette: head circle + shoulders dome, clipped look."""
    return (f"M{-r*0.32} {-r*0.25}a{r*0.32} {r*0.32} 0 1 0 {r*0.64} 0"
            f"a{r*0.32} {r*0.32} 0 1 0 {-r*0.64} 0"
            f"M{-r*0.62} {r*0.72}C{-r*0.62} {r*0.15} {r*0.62} {r*0.15} {r*0.62} {r*0.72}"
            f"L{-r*0.62} {r*0.72}Z")


tracks = []
nodes = []


def track(nid, **props):
    keys = {}
    for name, seq in props.items():
        out = []
        for k in seq:
            kk = {"t": k[0], "v": k[1]}
            if len(k) > 2:
                kk["ease"] = k[2]
            out.append(kk)
        keys[name] = out
    tracks.append({"target": nid, "keys": keys})


def steps(pairs):
    ks = []
    for tt, v in pairs:
        if ks:
            ks.append({"t": round(tt - 0.001, 3), "v": ks[-1]["v"]})
        ks.append({"t": round(tt, 3), "v": v})
    return ks


def opacity_steps(nid, pairs):
    tracks.append({"target": nid, "keys": {"opacity": steps(pairs)}})


# ------------------------------------------------ scene 1+2: install card
CARD = (1134, 623)
card_members = []


def member(n, gx, gy):
    """a node that lives at card-relative (gx,gy) and shares card motion."""
    n["x"], n["y"] = CARD[0] + gx, CARD[1] + gy
    card_members.append(n["id"])
    nodes.append(n)
    return n


member(rect("ic_card", 0, 0, 924, 210, 26, "#e9e8ec"), 0, 0)
member(rect("ic_icon", 0, 0, 150, 150, 40, "#0f1419"), -350, 0)
member(path("ic_x", 0, 0, x_glyph_d(74), "#ffffff"), -350, 0)
member(text("ic_title", "X", 0, 0, 44, "#111111", weight=700), -230, -40)
member(text("ic_sub", "Breaking News & Social Media", 0, 0, 27, "#8a8a8a"),
       -60, 8)
for i in range(5):
    member(path(f"ic_star{i}", 0, 0, star_d(), "#6f6f6f"), -256 + i * 30, 52)
member(rect("ic_open", 0, 0, 152, 64, 32, "#4185f0"), 322, 0)
member(text("ic_open_t", "Open", 0, 0, 28, "#ffffff", weight=600), 322, 0)

# hold 0-4.06, shrink wind-up 4.10-4.31 (scale about the card center),
# gone in one frame at 4.34
for nid in card_members:
    n = next(x for x in nodes if x["id"] == nid)
    gx, gy = n["x"] - CARD[0], n["y"] - CARD[1]
    track(nid,
          x=[(4.10, 0), (4.31, round(gx * 0.91 - gx, 1), "inCubic")],
          y=[(4.10, 0), (4.31, round(gy * 0.91 - gy, 1), "inCubic")],
          scale=[(4.10, 1), (4.31, 0.91, "inCubic")])
    opacity_steps(nid, [(0, 1), (4.335, 0)])

# ------------------------------------------------ plus circle -> avatar
nodes.append(rect("plus_c", 1138, 626, 208, 208, 104, "#50a0e0",
                  streak={"samples": 4, "window": 0.05, "gain": 0.5}))
nodes.append(path("plus_g", 1138, 626, "M-30 0L30 0M0 -30L0 30", None,
                  stroke=9.0))
nodes[-1]["fill"] = "#e9f9fa"
nodes.append(rect("av_c", 1138, 626, 208, 208, 104, "#b9bec4"))
nodes.append(path("av_s", 1138, 626, avatar_d(84), "#7d838a"))

opacity_steps("plus_c", [(0, 0), (4.335, 1), (4.70, 1), (4.90, 0)])
track("plus_c", scale=[(4.335, 1.38), (4.54, 1.0, "outCubic")])
opacity_steps("plus_g", [(0, 0), (4.335, 1), (4.66, 0)])
track("plus_g", scale=[(4.335, 1.38), (4.54, 1.0, "outCubic")])
# avatar sphere crossfades in, then flies up-left to the composer slot
for nid, k in [("av_c", 1.0), ("av_s", 1.0)]:
    opacity_steps(nid, [(0, 0), (4.58, 0), (4.70, 1)])
    track(nid,
          x=[(4.75, 0), (4.90, -320, "inCubic"), (5.05, -578, "outCubic")],
          y=[(4.75, 0), (4.90, -104, "inCubic"), (5.05, -163, "outCubic")],
          scale=[(4.75, 1), (5.05, 0.53, "outCubic")])

# ------------------------------------------------ the composer
comp_members = []


def comp(n):
    comp_members.append(n["id"])
    nodes.append(n)
    return n


comp(rect("cp_chip", 812, 463, 190, 56, 28, "#eaf5fd"))
comp(text("cp_chip_t", "Everyone ˅", 812, 463, 24, "#4185f0", weight=500))
comp(text("cp_ph", "Whats's happening?", 1090, 560, 40, "#9aa0a6"))
comp(text("cp_reply", "Everyone can reply", 880, 900, 24, "#4185f0"))
comp(path("cp_globe", 762, 900,
          circle_d(13) + "M-13 0L13 0M0 -13C7 -7 7 7 0 13M0 -13C-7 -7 -7 7 0 13",
          None, stroke=2.0))
comp_globe = nodes[-1]
comp_globe["fill"] = "#4185f0"
for i in range(8):
    comp(rect(f"cp_tool{i}", 700 + i * 62, 1005, 34, 34, 9, "#c3c9cf"))
comp(rect("cp_plus2", 1660, 1005, 52, 52, 26, "#4185f0"))
comp(rect("cp_post", 1815, 1005, 150, 62, 31, "#0f1419"))
comp(text("cp_post_t", "Post", 1815, 1005, 27, "#ffffff", weight=600))
for nid in comp_members:
    opacity_steps(nid, [(0, 0), (5.0, 0), (5.28, 1)])
# the placeholder dies as the caret arrives
opacity_steps("cp_ph", [(0, 0), (5.05, 0), (5.18, 0.9), (5.30, 0.9), (5.47, 0)])

# caption, two speeds: rush then punch
cap1 = comp(text("cap1", "Creators are replacing entire workflows", 1090, 560,
                 40, "#3a3f45"))
cap2 = comp(text("cap2", "with AI.", 1560, 560, 40, "#3a3f45"))
tracks.append({"target": "cap1", "at": 5.47, "reveal": {
    "unit": "type", "cadence": 0.012, "dur": 0.05, "caret": "bar",
    "caret_blink": 0.6}})
tracks.append({"target": "cap2", "at": 6.02, "reveal": {
    "unit": "type", "cadence": 0.055, "dur": 0.05, "caret": "bar",
    "caret_blink": 0.6}})
opacity_steps("cap1", [(0, 0), (5.47, 1)])
opacity_steps("cap2", [(0, 0), (6.02, 1)])

# icon-ring attachment: indigo border card, 9 badges on a dotted ring with
# the empty center exactly under the parked cursor
att_members = []


def att(n):
    att_members.append(n["id"])
    comp_members.append(n["id"])
    nodes.append(n)
    return n


ATT = (1146, 594)   # ring center = the cursor
att(rect("at_card", ATT[0], ATT[1] + 120, 985, 500, 40, "#f8f8f8"))
att(path("at_border", ATT[0], ATT[1] + 120,
         f"M{-985/2+2} {-500/2+2}L{985/2-2} {-500/2+2}L{985/2-2} {500/2-2}"
         f"L{-985/2+2} {500/2-2}Z", "#361bb3", stroke=3.0))
BADGES = ["#4b32c3", "#111111", "#ffd02f", "#1e1e1e", "#7b45e0",
          "#e04b2f", "#10a37f", "#12224d", "#2f6fe0"]
for i, col in enumerate(BADGES):
    a = -math.pi / 2 + i * 2 * math.pi / 9
    bx = ATT[0] + 300 * math.cos(a)
    by = ATT[1] + 120 + 165 * math.sin(a)
    att(rect(f"at_b{i}", round(bx, 1), round(by, 1), 78, 78, 20, col))
    da = a + math.pi / 9
    att(rect(f"at_d{i}", round(ATT[0] + 300 * math.cos(da), 1),
             round(ATT[1] + 120 + 165 * math.sin(da), 1), 10, 10, 5,
             "#c9c2ef"))
for nid in att_members:
    born = 5.90 if not nid.startswith("at_border") else 6.10
    opacity_steps(nid, [(0, 0), (born, 0), (born + 0.20, 1)])

# the layout is alive: caption band and chrome ride up as the card lands
for nid in ["cp_ph", "cap1", "cap2", "cp_chip", "cp_chip_t"]:
    track(nid, y=[(5.70, 0), (6.07, -248, "outCubic")])
for nid in att_members:
    track(nid, y=[(5.70, 95), (6.07, -102, "outCubic")])
# avatar sits in the top-left slot and rides with the header
for nid in ["av_c", "av_s"]:
    track(nid, y=[(5.70, 0), (6.07, -95, "outCubic")])
    # (relative on top of the flight offsets; engine sums? no — same prop
    # would clobber. flight y ended at -163; fold the ride into that track
    # instead, so skip here)
tracks = [t for t in tracks if not (t["target"] in ("av_c", "av_s")
                                    and list(t.get("keys", {}).keys()) == ["y"])]

# ------------------------------------------------ crash zoom + click
# world-zoom about the Post button: every composer-era node gets computed
# transform keys. z timeline: 1 -> 3 (in by 7.63), hold, whip back to 1.
ZP = [(6.63, 1.0, None), (7.14, 2.45, "inCubic"), (7.63, 3.0, "outCubic"),
      (7.99, 3.0, None), (8.15, 1.9, "inCubic"), (8.33, 1.0, "outCubic")]


def zoomed(px, py, z):
    return (POST_ANCHOR[0] + (px - POST_ANCHOR[0]) * z,
            POST_ANCHOR[1] + (py - POST_ANCHOR[1]) * z)


world = comp_members + ["av_c", "av_s"]
for nid in world:
    n = next(x for x in nodes if x["id"] == nid)
    # where earlier motion left the node, as offsets from its stage base
    left_x = left_y = 0.0
    left_s = 1.0
    priors = [t for t in tracks if t["target"] == nid and "keys" in t]
    for t in priors:
        if "x" in t["keys"] and t["keys"]["x"]:
            left_x = t["keys"]["x"][-1]["v"]
        if "y" in t["keys"] and t["keys"]["y"]:
            left_y = t["keys"]["y"][-1]["v"]
        if "scale" in t["keys"] and t["keys"]["scale"]:
            left_s = t["keys"]["scale"][-1]["v"]
    rx, ry = n["x"] + left_x, n["y"] + left_y
    xk, yk, sk = [], [], []
    for (tt, z, ez) in ZP:
        zx, zy = zoomed(rx, ry, z)
        e = {"ease": ez} if ez else {}
        xk.append({"t": tt, "v": round(zx - n["x"], 1), **e})
        yk.append({"t": tt, "v": round(zy - n["y"], 1), **e})
        sk.append({"t": tt, "v": round(z * left_s, 3), **e})
    # append into existing tracks per prop; leftovers get one new track
    leftovers = {}
    for prop, merged in (("x", xk), ("y", yk), ("scale", sk)):
        host = next((t for t in priors if prop in t["keys"] and t["keys"][prop]), None)
        if host:
            host["keys"][prop] += merged
        else:
            leftovers[prop] = merged
    if leftovers:
        tracks.append({"target": nid, "keys": leftovers})

# hover halo behind Post: inflate 9 frames, vanish in one = the click
nodes.append(rect("halo", POST_ANCHOR[0], POST_ANCHOR[1], 150, 62, 31,
                  "#d9d9d9"))
track("halo", w=[(7.30, 190), (7.55, 420, "outCubic")],
      h=[(7.30, 84), (7.55, 190, "outCubic")])
opacity_steps("halo", [(0, 0), (7.30, 0.55), (7.58, 0.55), (7.60, 0)])
# composer dies mid-whip: append into each node's existing opacity track
# (a fresh track would replace the earlier fade-in gate — contract rule 3)
for nid in world:
    for t in tracks:
        if t["target"] == nid and "opacity" in t.get("keys", {}) \
                and t.get("at", 0) == 0:
            ks = t["keys"]["opacity"]
            last = ks[-1]["v"]
            ks += [{"t": 8.24, "v": last}, {"t": 8.309, "v": last},
                   {"t": 8.31, "v": 0}]
            break

# ------------------------------------------------ the published tweet
tw_members = []


def tw(n, dx, dy):
    n["x"], n["y"] = 889 + dx, 520 + dy
    tw_members.append((n["id"], dx, dy))
    nodes.append(n)
    return n


tw(rect("tw_av", 0, 0, 96, 96, 48, "#b9bec4"), -420, -130)
tw(path("tw_avs", 0, 0, avatar_d(40), "#7d838a"), -420, -130)
tw(text("tw_name", "Alex Hormozi", 0, 0, 30, "#202020", weight=700), -256, -152)
tw(rect("tw_badge", 0, 0, 26, 26, 13, "#4185f0"), -122, -152)
tw(path("tw_check", 0, 0, "M-6 0L-2 5L7 -6", None, stroke=2.6), -122, -152)
nodes[-1]["fill"] = "#ffffff"
tw(text("tw_handle", "@alexhormozi · 21h", 0, 0, 26, "#8a9096"), 42, -150)
tw(text("tw_cap", "Creators are replacing entire workflows with AI", 0, 0,
        31, "#202020"), -66, -88)
tw(rect("tw_card", 0, 0, 700, 356, 30, "#f8f8f8"), -10, 130)
tw(path("tw_cardb", 0, 0,
        "M-348 -176L348 -176L348 176L-348 176Z", "#361bb3", stroke=2.4), -10, 130)
for i, col in enumerate(BADGES):
    a = -math.pi / 2 + i * 2 * math.pi / 9
    tw(rect(f"tw_b{i}", 0, 0, 54, 54, 14, col),
       round(-10 + 212 * math.cos(a), 1), round(130 + 118 * math.sin(a), 1))
ENG = [("165", -380), ("244", -180), ("1.7K", 30), ("19.3K", 240)]
for i, (count, dx) in enumerate(ENG):
    tw(rect(f"tw_ei{i}", 0, 0, 26, 26, 8, "#c3c9cf"), dx, 330)
    tw(text(f"tw_ec{i}", count, 0, 0, 23, "#8a9096"), dx + 55, 330)
for nid, dx, dy in tw_members:
    opacity_steps(nid, [(0, 0), (8.29, 0), (8.42, 1)])
    # settle left, then shrink slightly to make room for the reply
    track(nid,
          x=[(8.42, 0), (9.33, -196, "outCubic")],
          y=[(9.33, 0), (10.50, -40, "outCubic")],
          scale=[(9.33, 1), (10.50, 0.91, "outCubic")])

# thread line + reply
nodes.append(rect("th_line", 273, 640, 3, 10, 1, "#d5d9dd"))
track("th_line", h=[(9.75, 10), (10.10, 210, "outCubic")],
      y=[(9.75, 0), (10.10, 100, "outCubic")])
opacity_steps("th_line", [(0, 0), (9.75, 1), (10.94, 1), (11.30, 0)])
rp = [
    rect("rp_av", 273, 880, 80, 80, 40, "#e8c9e0"),
    path("rp_avs", 273, 880, avatar_d(34), "#a06090"),
    text("rp_name", "Sanzxcreates", 438, 862, 27, "#202020", weight=700),
    rect("rp_badge", 552, 862, 24, 24, 12, "#4185f0"),
    text("rp_handle", "@sanzxcreates · 21h", 730, 864, 24, "#8a9096"),
    text("rp_text", "agree with you Hormozi", 480, 922, 28, "#202020"),
]
for n in rp:
    nodes.append(n)
born = {"rp_av": 10.13, "rp_avs": 10.13, "rp_name": 10.20, "rp_badge": 10.22,
        "rp_handle": 10.24, "rp_text": 10.30}
for nid, at in born.items():
    opacity_steps(nid, [(0, 0), (at, 0), (at + 0.10, 1)])
tracks.append({"target": "rp_text", "at": 10.30, "reveal": {
    "unit": "word", "stagger": 0.06, "dur": 0.16, "rise": 12,
    "accent": "#202020"}})

# ------------------------------------------------ whiteout + headline + CTA
# leaving = rising: append exit keys into each node's EXISTING tracks so
# nothing clobbers the earlier fade-ins (one track per node per prop).
exit_nodes = [nid for nid, _, _ in tw_members] + list(born.keys()) + ["th_line"]
for j, nid in enumerate(exit_nodes):
    stagger = (j % 5) * 0.06
    for t in tracks:
        if t["target"] != nid or "keys" not in t:
            continue
        if "opacity" in t["keys"] and t.get("at", 0) == 0:
            t["keys"]["opacity"] += [
                {"t": 11.24 + stagger, "v": 1}, {"t": 11.75 + stagger, "v": 0}]
        if "y" in t["keys"]:
            last = t["keys"]["y"][-1]["v"]
            t["keys"]["y"] += [
                {"t": 10.94, "v": last},
                {"t": 11.89, "v": last - 280, "ease": "inCubic"}]
    if nid in born and not any(t["target"] == nid and "y" in t.get("keys", {})
                               for t in tracks):
        track(nid, y=[(10.94, 0), (11.89, -280, "inCubic")])

HEAD = [("hw1", "Built", 800), ("hw2", "for", 950), ("hw3", "modern", 1135),
        ("hw4", "creators", 1400)]
for i, (nid, word, x) in enumerate(HEAD):
    nodes.append(text(nid, word, x, 610 + i * 14, 64, "#26292c", weight=600))
    at = 11.83 + i * 0.07
    tracks.append({"target": nid, "at": at, "keys": {
        "opacity": [{"t": 0, "v": 0}, {"t": 0.30, "v": 1},
                    {"t": 13.185 - at, "v": 1}, {"t": 13.19 - at, "v": 0}],
        "y": [{"t": 0, "v": 90}, {"t": 0.55, "v": -(i * 14), "ease": "outCubic"}]}})

nodes.append(text("cta", "Request a project!", 1134, 610, 64, "#26292c",
                  weight=600))
opacity_steps("cta", [(0, 0), (13.19, 1), (14.025, 1), (14.03, 0)])
nodes.append(rect("xi_sq", 1140, 655, 200, 200, 52, "#0f1419", rot=-15,
                  glow={"sigma": 18, "opacity": 0.35, "color": "#9aa0a6",
                        "dy": 14}))
nodes.append(path("xi_x", 1140, 655, x_glyph_d(96), "#ffffff", rot=-15))
for nid in ("xi_sq", "xi_x"):
    opacity_steps(nid, [(0, 0), (14.03, 1)])

# the cursor: parked, immortal
nodes.append({"id": "cursor", "type": "cursor", "x": CURSOR[0],
              "y": CURSOR[1], "w": 30, "fill": "#111111"})

stage = {
    "fps": 30,
    "size": [W, H],
    "scenes": [
        {"id": "s", "bg": "#ffffff", "dur": 14.24,
         "transition": {"kind": "cut"}, "nodes": nodes},
    ],
}

with open("docs/x-anim.stage.json", "w") as f:
    json.dump(stage, f, indent=1)
with open("docs/x-anim.anim.json", "w") as f:
    json.dump({"tracks": tracks}, f, indent=1)
print("wrote docs/x-anim.{stage,anim}.json,", len(nodes), "nodes,",
      len(tracks), "tracks")
