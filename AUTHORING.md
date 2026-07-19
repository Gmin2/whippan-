# authoring whippan documents

this is the reference for writing a launch video as a whippan doc. it is
written for an agent (or a person) who has this file and nothing else. the
schema section says what the engine parses; the contract section says how
the pieces bind; the taste section says what separates a real launch video
from a slideshow. all of it was extracted from frame-level teardowns of 29
reference launch videos and verified by reproducing four of them
pixel-against-footage (terminal 2.3%, chatgpt 2.8%, atlas 4.7% mean diff).

## 1. the model

a video is TWO json files joined by node ids:

- `<name>.stage.json` — the static world: scenes, their nodes, their
  resting geometry. every scene must read as a finished frame on its own.
- `<name>.anim.json` — the motion overlay: tracks that key node
  properties over time, reveals, entrances, state flips, camera moves.

stage first, animation second. this is not a file convention, it is the
authoring method: lay out every scene as a still that could ship as a
poster, then decide how each element arrives, breathes, and leaves.

rendering is a pure function of (stage, anim, t). there is no hidden
state: frame 200 does not depend on frame 199. if you can say what time
something happens, you can author it.

## 2. stage schema

```json
{
  "fps": 30,
  "size": [1920, 1080],
  "audio": {"src": "/assets/audio/pad.m4a", "gain": 0.7, "fade_out": 0.8},
  "scenes": [
    {
      "id": "s1",
      "bg": "#f2f2f2",
      "dur": 3.4,
      "transition": {"kind": "cut"},
      "nodes": [ ... ]
    }
  ]
}
```

- `dur` is seconds this scene owns. total video length = sum of durs.
- `transition` describes how this scene ENTERS from the previous one.
- `audio` is optional; export trims the bed to the video length, applies
  gain and a tail fade.

### node types

every node: `{"id": "...", "type": "...", "x": .., "y": ..}` plus fields
by type. x,y is the CENTER of the node. ids must be unique across the
whole stage (see contract rule 2).

**text**
```json
{"id": "title", "type": "text", "text": "Ship faster",
 "x": 960, "y": 500, "color": "#161616",
 "font": {"size": 96, "weight": 600, "family": "inter"}}
```
families: `inter` (variable weight 100-900), `mono` (jetbrains, one
weight). text is engine-shaped: real metrics, per-word and per-glyph
positions. a text node is one line; multi-line copy = one node per line.

**rect**
```json
{"id": "card", "type": "rect", "x": 960, "y": 540, "w": 420, "h": 420,
 "radius": 56, "fill": "#0d0d0d"}
```
optional on rect:
- `gradient`: `{"angle": 90, "stops": [{"at": 0, "color": "#401eb1"},
  {"at": 1, "color": "#3f1ead"}]}` — linear, angle in degrees.
- `glow`: `{"sigma": 34, "opacity": 0.9, "color": "#a32a32", "dx": 0,
  "dy": 0}` — a blurred echo behind the body. color defaults to the fill
  (or mid gradient stop). use for lit pills, status dots, rim glows.
- `blur`: gaussian sigma on the body itself — defocus, soft light pools.
- `streak`: `{"samples": 5, "window": 0.06, "gain": 0.5}` — motion echo
  trail, only visible while the node moves. use on crash-ins and whips.
- `goo`: `"groupname"` — all nodes sharing a goo tag render through a
  metaball filter and fuse when close (blobs, liquid couplings).

**path** — raw svg outline
```json
{"id": "mark", "type": "path", "x": 200, "y": 300, "fill": "#417fd9",
 "d": "M0 0C130 62 290 72 420 40 ...Z"}
```
- filled by default; add `"stroke": 2.0` to draw the path as a stroked
  line (round caps) instead — icons, underlines, dashed arcs.
- d coordinates are local to (x,y). static scale via a stage key:
  `"keys": {"scale": [{"t": 0, "v": 0.9}]}`.

**image**
```json
{"id": "shot", "type": "image", "src": "/assets/demo/mark.png",
 "x": 960, "y": 540, "w": 800, "h": 500, "radius": 24}
```

**cursor** — a vector mac-style arrow with shadow and outline
```json
{"id": "cur", "type": "cursor", "x": 1200, "y": 700, "w": 26,
 "fill": "#111111"}
```

optional on any node:
- `rot`: degrees about the node center.
- `states`: named property overrides the overlay can flip to, lerped over
  0.12s: `"states": {"pressed": {"scale": 0.96, "fill": "#e8e8e8"}}`.
- `morph`: `{"from": "pill", "dur": 0.5, "ease": "spring"}` — this node
  begins life as the named node from the PREVIOUS scene and interpolates
  geometry, radius and fill into its own. state continuity across a cut.
- `keys`: same shape as overlay keys, evaluated in scene-local time. use
  for static transforms (icon scale); put real motion in the anim doc.

### transitions

`{"kind": "...", "dur": 0.4, "dir": "left|right|up|down", "ease": ...}`

| kind | what it does | when |
|---|---|---|
| `cut` | hard swap | chapter breaks, beat hits |
| `fade` | crossfade with bg mix | gentle chapter turns |
| `push` | whole scene slides in along dir | spatial sequences |
| `whip` | fast push with velocity blur | energy spikes |
| `dip` | dip to a color (`dir` holds the hex) | act boundaries |
| `zoom` | zoom-through into the next scene | diving into detail |
| `wipe` | clipped reveal along dir | editorial, data stories |
| `rise` `dissolve` `settle` `bloom` | phase-choreographed exits/enters (outgoing leaves ~44% ease-in, incoming arrives from ~22% ease-out) | polished soft families |

magic move: add `"morph": true` to any transition and nodes sharing an id
across the two scenes glide as full-opacity clones from old geometry to
new (morph runs 2.5x the fade dur by default; override with `morph_dur`,
`morph_ease`). unmatched nodes fade in place. morph is a promise that the
two scenes are the same world — use it for state continuity, one or two
per chapter, never decoration.

## 3. animation overlay schema

```json
{"tracks": [
  {"target": "title", "at": 0.4,
   "keys": {"y": [{"t": 0, "v": 0}, {"t": 0.5, "v": -40, "ease": "outCubic"}]}},
  {"target": "title", "at": 0.4, "reveal": {"unit": "word"}},
  {"target": "btn", "at": 2.1, "state": "pressed"},
  {"target": "pill", "loop": true, "keys": {"glow_opacity": [
    {"t": 0, "v": 0.8}, {"t": 0.7, "v": 1.0, "ease": "inOutCubic"},
    {"t": 1.45, "v": 0.8, "ease": "inOutCubic"}]}},
  {"target": "s2", "keys": {"cam_zoom": [{"t": 0, "v": 2.5},
    {"t": 1.4, "v": 1.0, "ease": "outCubic"}]}}
]}
```

- `target` is a node id, or a SCENE id for camera keys
  (`cam_x`, `cam_y`, `cam_zoom` — zoom is about canvas center; offset
  cam_x/cam_y to anchor it on a point that must not move).
- `at` shifts the whole track; key times are relative to it.
- `loop: true` repeats the keys forever from `at` (breathing, blinks).
- `state` flips the target to a named state at `at`.

keyable properties: `x` `y` (offsets — see contract), `w` `h` (absolute),
`scale` `rot` `opacity` `glow_sigma` `glow_opacity` (absolute), and
`blur` (rects only).

easing per key (eases INTO that key): `"outCubic"`, `"inCubic"`,
`"inOutCubic"`, `"spring"`, a cubic bezier `[0.22, 1, 0.36, 1]`, or a
custom spring `{"spring": [damping, cycles]}`. no ease = linear. two keys
1ms apart = a hard step (strobes, swaps, odometer flips).

### reveals

`"reveal": {...}` on a track animates the birth of a text node's pieces.

**word / glyph** — the accent ritual. pieces rise in with opacity
leading, born in the accent color, tempering to the node ink in reading
order:
```json
{"unit": "word", "stagger": 0.05, "dur": 0.27, "rise": 40,
 "accent": "#e8671f", "color_delay": 0.16, "color_dur": 0.3,
 "keep": ["faster"]}
```
`keep` lists words that stay accent-colored forever (the one emphasis
word). set `"rise": 0` for resolve-in-place. `unit: "glyph"` gives every
letter its own clock (letter sweeps, trailing-letter tempers).

**type** — typewriter:
```json
{"unit": "type", "cadence": 0.062, "cadence_end": 0.03, "dur": 0.1,
 "caret": "block", "caret_blink": 1.0, "caret_typing": "hidden"}
```
chars appear at keystroke times in the final layout, born dim and
sharpening. `cadence_end` ramps speed across the line (deceleration =
human, acceleration = machine). caret `bar` or `block`, blinks while
idle, `caret_typing` solid or hidden while typing.

**scramble** — decoder:
```json
{"unit": "scramble", "cadence": 0.05, "churn": 4}
```
chars lock left to right; the next `churn` slots cycle deterministic
junk glyphs every 34ms until they lock. the settle is the beat.

### enter presets

`"enter": "pop"` or `{"preset": "rise-fade", "dur": 0.5}` on a track —
measured entrance keyframes expanded at load: `pop`, `rise-fade`, `drop`,
`slide-left`, `slide-right`, `spring-in`, `fade`.

## 4. the contract (binding rules — violations fail silently)

1. **`at` is scene-local time.** every scene's clock starts at 0. a track
   for a node in scene 3 uses times within scene 3, not global time.
2. **a track applies to every scene containing its target id.** so give
   nodes unique ids across scenes (`title1`, `title2`) unless you are
   deliberately sharing a track — or pairing ids for a morph transition,
   which is the one place matching ids across scenes is the tool.
3. **one track per node per property.** a later track keying the same
   property REPLACES the earlier keys. put a node's whole timeline for a
   property in one track. different properties may live in different
   tracks (a keys track + a reveal track is fine).
4. **x and y keys are OFFSETS from the node's stage position.** v: -40
   means 40px left of home. everything else (`w`, `h`, `scale`, `rot`,
   `opacity`, `blur`) is absolute. before its first key a property holds
   the first key's value.

## 5. taste (what the 29 references actually do)

timing bands, measured:

- in-scene element motion: 140-280ms. exits lean ease-in (~150ms),
  entrances ease-out (200-280ms, often after an ~80ms delay). anything
  over 350ms in-scene reads slow; scene-level moves (camera pulls, gap
  closes) may run 0.5-1.2s with long asymptotic decel tails.
- translation magnitudes inside a scene: under ~40px for text, elements
  arrive within 12px of home for micro-moves. big travel belongs to
  entrances, exits and camera.
- typewriter cadences: 60-70ms/char deliberate, 15-45ms/char with decel
  for bursts. odometer digit rolls ~100-180ms. blink 0.5s on / 0.5s off.
- accent temper: born accent, cooling to ink over 10-14 frames, trailing
  letters last, one new word every ~3 frames.

the playbook:

1. **cuts punctuate, morphs narrate.** hard cuts land chapter breaks on
   the beat; inside a chapter everything is dissolve, morph, or physics.
   several great videos have two or zero hard cuts total.
2. **one color, hoarded.** a single brand hue does all accent work;
   grayscale carries everything else. foreign color only when it MEANS
   something (partner logo, success state, the one benchmark).
3. **the accent-word ritual.** emphasis words are born in the accent and
   temper to ink; at most one word per line keeps the accent forever.
4. **transitions carry causality.** the thing that leaves becomes the
   thing that arrives: word swaps for a live input, cards die into the
   hole the next line grows from, a blob becomes the logo. never move a
   thing you could transform.
5. **the ui arrives whole.** product surfaces materialize complete
   (staggered opacity cascades, a camera pull revealing a page already
   laid out around an anchor you were watching). no chart draw-ons, no
   element-by-element builds.
6. **energy is blur and decel, not springs.** punch comes from 1-2 frame
   pops, echo trails, velocity blur and long asymptotic settles.
   overshoot is reserved for moments selling physicality (a toy, a
   bounce) — once per video, if at all.
7. **holds are loaded.** nothing is ever fully static: sub-pixel drift,
   glow breathing, blink cycles, 1-2px orbital float. a real hold before
   a reveal is a wind-up, and scenes EXIT by picking up motion the next
   scene inherits.
8. **honest clocks sell speed.** counters tick real seconds. typing takes
   typing time. authenticity beats spectacle: real dates, plausible data,
   kept typos.
9. **structure as content.** showing the scaffolding (a storyboard bar, a
   canvas with layer names, spec sheets, the editor itself) IS a launch
   video move. the making-of is the pitch.
10. **music-led, sfx-sparse.** one bed, 90-160bpm, chapter cuts within
    ~90ms of the grid, near-zero per-event sfx. end cards land in
    silence after the bed fades.
11. **sign off small.** end on the wordmark or the url, static, held.
    lowercase confidence. no feature recap.

forbidden: full-width slides between elements, scale-pops with blur on
both layers, linear easing on anything visible, three simultaneous accent
colors, decorative morphs, springs on ui chrome.

## 6. fit budget (mechanical checks before you render)

pure arithmetic; do it while writing the stage doc:

- a text line's width ≈ char_count x size x 0.5 (inter) or x 0.6 (mono).
  it must fit inside size[0] minus margins (leave >= 8% each side).
- vertical: sum of (line size x 1.35) per stacked line + gaps must fit
  the content band (middle ~70% of size[1]).
- headline sizes at 1920x1080: hero 90-130, section 56-90, ui copy 22-30,
  micro-labels 14-18. scale linearly for other canvases.
- one thought per scene. if a scene needs three sentences it is two
  scenes.
- scene budget: a 15-25s launch video is 5-9 scenes. dwell 1.5-3.5s per
  content scene, 0.5-1.5s for punctuation beats, >= 2s for the end card.

## 7. workflow

1. **scope.** three questions before any json: what is the product's one
   verb? what single moment proves it (the state change to show)? what is
   the brand hue? then pick 5-9 scene roles: hook, problem or promise,
   the proof (product doing the thing once, end to end), 1-2 capability
   beats, the name.
2. **stage doc.** write every scene as a finished still. run the fit
   budget. wrong numbers here poison everything after.
3. **anim doc.** per scene: how does each node arrive (reveal, enter,
   keys), what breathes during the hold (loop tracks), how does the scene
   leave (wind-up keys, transition). motion DNA: pick ONE energy for the
   whole video (all-decel, or beat-strobe, or one-continuous-flow) and
   stay in it.
4. **render and look.**
   ```
   ./target/release/export docs/<name>.stage.json docs/<name>.anim.json out/<name>.mp4
   ```
   add an entry to `docs/examples/index.json` (group it, stage/anim
   paths) and it appears in the gallery
   (`http://localhost:8777/editor/gallery.html`) for scrubbing, and in
   the editor (`/editor/edit.html?doc=<slug>`) for direct polishing.
5. **judge like a reviewer.** scrub the boundaries: does every cut land
   on a beat? does anything move without a reason? is there exactly one
   accent color on screen? is the hold before the reveal loaded? fix the
   doc, not the render.
