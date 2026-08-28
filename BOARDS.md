# boards — the editor plan

what we are building, in what order, and what has to change in the engine to
allow it. written 2026-08 against the state where boards renders one PNG per
scene and nothing below scene level can be touched.

---

## 0. the shape of the thing

the document is two layers. the app is two modes. they map one to one:

| layer | file | mode | analogy |
|---|---|---|---|
| the static world | `stage.json` | **Design** | figma |
| the motion overlay | `anim.json` | **Motion** | after effects |

so the segmented control in the left panel is `Design ｜ Motion`. it is not a
cosmetic label, it is the format's own seam. PLAN.md chose the two-layer model
because it "matches the figma -> AE split"; this is that decision reaching the
ui.

and the build order follows the authoring order AUTHORING.md already
prescribes: *lay out every scene as a still that could ship as a poster, then
decide how each element arrives*. screens first. motion on top. a motion editor
built over screens you cannot edit is a motion editor built on sand.

---

## 1. why nothing is editable today

boards draws each scene to a PNG and puts it in an `<img>`. a PNG has no parts.

but the deeper reason is in the engine. it exposes exactly four functions:
`render`, `sfx`, `init_font`, `register_font`. it computes the resolved
position of every node at time t in order to draw it, and then throws that
away. **the draw commands are anonymous**: the painter receives
`{op, x, y, w, h, color, ...}` with no idea which node produced it.

the existing studio editor works around this and the workaround is broken by
design. `Stage.jsx:373` computes a node's box by reading `n.x` / `n.y`
straight out of the static json and guessing text width as
`text.length * font.size * 0.5`. so the moment a node is animated at all —
keyframed, revealed, morphed, rotated, moved by a camera — the selection box
sits somewhere the node is not. fine for a tracer. not a foundation.

---

## 2. engine changes

### 2.1 tag every draw command with its source  ← the unlock

add `id` and `scene` to each emitted command, plus a `part` discriminator for
sub-pieces (glyph index on text, `echo` on glow and streak, `clone` on morph).

this is the whole ballgame, and it is deliberately *not* a separate
`measure()` implementation, because:

- **no duplicated maths.** geometry comes out of exactly the code that painted
  it, so it can never drift from what you see. a parallel measure path would
  drift the first week
- **text becomes exact.** glyphs are already emitted as path commands, so real
  shaped extents replace the `length * size * 0.5` guess
- **rotation, scale, morph clones, camera transforms and goo come out right
  for free**, because they are already baked into the commands
- it honours the standing rule that both renderers change together: there is
  only one place to change

cost: one string field per command, roughly 15% on the render payload.

### 2.2 `measure(stage, anim, t)`

```
-> [{scene, id, kind, x, y, w, h, rot, opacity, z}]
```

walk the tagged commands, union bounds per id, keep paint order for z. done in
rust rather than js so the native export path and the conform harness get it
too. ~80 lines over the existing path.

### 2.3 `hit(stage, anim, t, x, y)`

```
-> {scene, id} | null
```

topmost by z. bounding box for rect and image, real point-in-path coverage for
path and glyph outlines. `flatten_path` (lib.rs:200) already exists, so
coverage testing is nearly free.

### 2.4 `timeline(stage, anim)`

```
-> [{scene, id, prop, spans: [{t0, t1, kind}]}]
```

what the merged doc actually does over time, **after** presets expand. motion
mode cannot read the timeline off raw `anim.json`, because `enter: "pop"` is
one word that `merge` / `preset_keys` turns into six keyframes at load. the ui
has to show the expanded truth while letting you edit back at the intent level.

### 2.5 `validate(stage, anim)`

the contract in AUTHORING.md §4 fails **silently** when violated: `at` is
scene-local, one track per node per property (a later track replaces an
earlier one), `x`/`y` keys are offsets not absolutes, ids unique per scene. an
editor that lets you break those produces a doc that renders wrong with no
error anywhere. so the engine returns issues and the ui surfaces them.

### 2.6 persistence

`POST /api/doc/:slug` in the vite dev server, writing `stage.json` and
`anim.json` back. nothing persists today, not even in memory across a reload.

**2.1 is the only rust work the entire Design half needs.** everything in
section 3 below is typescript on top of it.

---

## 3. Design mode — the screens

### 3.1 one live surface for the wall

boards stop being images. one engine surface draws every scene at its offset
through a single camera transform; pan and zoom become camera moves. one GL
surface rather than fifteen, and an edit is visible the instant it lands.

each board renders at its **settled** time by default, not the midpoint, so
you are composing the finished poster the way AUTHORING asks. a per-board
"still at" lets you compose on the moment that actually matters.

### 3.2 selection chrome

an svg layer over the surface, drawn in canvas space so it tracks zoom:
selection box, eight resize handles, rotate targets outside the corners,
radius nub on rects, hover outline. fed by `measure`, so unlike studio it is
correct on animated nodes.

### 3.3 direct manipulation

move with snap guides and distance badges against siblings and scene edges,
resize (corners scale the type on text nodes), rotate with magnetic 0/90,
radius drag. remember x,y is the node **centre**.

### 3.4 typed edit ops

every mutation is an op (`move`, `resize`, `rotate`, `setText`, `setFill`,
`reorder`, `addNode`, `deleteNode`) against a snapshot, with undo and redo,
rather than freeform object mutation. TODO.md already argues for this.

### 3.5 text edited in place

double click, retype, engine reshapes live. one text node is one line by
spec, so Enter offers to split into a second node rather than silently
producing something the engine will not lay out.

### 3.6 the tool rail becomes real

frame creates a scene, rect/text/pen/image create nodes in the active scene.

### 3.7 the layer tree becomes the node tree

today it lists scenes. it should nest scene > nodes, with drag to reorder
(that is z order), rename, hide, lock.

### 3.8 the inspector becomes a property panel

every field the `Node` struct carries, by type: geometry, radius, rot, blur,
fill, gradient editor, glow, font family/size/weight/colour, image src, path
`d`, goo tag, named states.

---

## 4. Motion mode — the film

this is the half that is whippan rather than a figma clone. the storyboard is
the right surface for motion precisely because motion lives *between* screens.

### 4.0 two levels, and how much of after effects we actually want

motion mode is not one screen, it is two, and you move between them by zoom:

**the wall** (zoomed out) — the storyboard. seams between boards, morph
threads, a stagger strip under each column. this level does not exist in after
effects at all, and it is the reason to build this rather than use theirs:
motion *between* screens is a first-class object you can see and click.

**inside a scene** (double click a board, or zoom past a threshold) — a real
timeline dock at the bottom. this is the after-effects-shaped part: one lane
per node, keyframe diamonds per property, playhead, scrub, play with audio, a
graph editor for easing.

what we take from after effects:

- the timeline: layer lanes, property rows, keyframes you drag to retime
- a graph / curve editor for easing on the selected property
- playhead scrub and true playback, with the audio bed and derived sfx
- preview that plays the actual output, not an approximation

what we deliberately do **not** take:

- the effects kitchen sink. our whole effect vocabulary is what the engine has:
  glow, blur, streak, goo, gradient, camera. that is the point, not a gap
- compositions nested in compositions. scenes are flat
- an expression language. the document *is* the expression language
- keyframing every property by hand as the primary gesture. ours is intent
  presets first, raw keys as the escape hatch — AUTHORING's three authoring
  depths, in that order of prominence

what we have that after effects does not:

- the seam and morph threads above
- intent chips (`enter: pop`, `reveal: {unit: word}`) that compile to keys, so
  a first draft is minutes not hours
- the taste rails: 140-280ms in-scene, under ~40px translation, >350ms reads
  slow. the tool tells you when you leave the measured bands
- the artifact is readable json an agent can author and diff

### 4.1 the seam is the control

the gap between board N and N+1 holds `transition: {kind, dur, dir, ease}`.
click it and choose from the eleven kinds (cut, fade, push, whip, dip, zoom,
wipe, rise, dissolve, settle, bloom), set duration and easing, toggle magic
move. the seam **draws what it is**: an arrow for a push direction, a diamond
for a morph, a hard bar for a cut.

### 4.2 morph threads

magic move pairs nodes by id across a cut. draw those as literal connector
lines from a node on one board to its twin on the next; show unmatched nodes
as fading in place; let you break a pair or force one with `morph: {from}`.

`ui-func.md` asked for exactly this and it has never been built. it is the
most legible idea in the whole app: you can *see* what carries.

### 4.3 scrub inside a board

drag across an artboard to move that scene's local clock. cheapest large win
on this list — it turns a wall of stills into a film you can feel, and it is
worth doing before anything else in this section.

### 4.4 motion at intent depth

selecting a node in motion mode offers `enter` presets with intensity,
`reveal` for text (word / glyph / type / scramble, with stagger, accent and
keep-list), `state` flips, `loop`. chips, not keyframe soup — the format's
thesis is that intent compiles down to keyframes, so the ui should author
intent and show the compiled result.

### 4.5 stagger strip per board

a mini per-scene timeline under each column: one lane per node, when it enters
and for how long, draggable to restagger. per-column rather than one global
27-second timeline, because that is how a storyboard reads.

### 4.6 camera

`cam_x` / `cam_y` / `cam_zoom` target a scene id. draw a camera rect on the
board you can drag and scale, keyframed on the strip.

### 4.7 raw keys, the escape hatch

any track can drop to explicit keyframes with easing, with a small curve
editor for the selected property. the last 10% and exact reproduction work
lives here.

### 4.8 taste rails

AUTHORING §5 carries measured bands: in-scene motion 140-280ms, translation
under ~40px, anything over 350ms reads slow. the motion ui shows these as soft
rails and says so when you leave them. the craft belongs in the tool, not only
in the renderer.

---

## 5. order of work

**engine**

0. tag commands with id/scene, then `measure` and `hit`

**design mode**

1. live engine wall replacing the PNGs, one surface, camera pan/zoom
2. selection and hover chrome from `measure`
3. move / resize / rotate / radius, snap guides, typed ops, undo
4. node tree and full inspector, create tools
5. text edited in place
6. save to disk

*screens are now editable. this is the milestone.*

**motion mode**

7. the `Design ｜ Motion` toggle
8. scrub inside a board
9. seam transition controls
10. morph threads
11. per-node presets and the reveal editor
12. stagger strip and camera
13. `timeline` + raw keys and the curve editor

---

## 6. open questions

1. ~~does boards replace studio?~~ **decided: no.** studio (the older dark
   editor on 8900) stays as its own thing for now. boards is built alongside
   it. the three apps are: **gallery** (8901, the public wall of films),
   **studio** (8900, the old editor), **boards** (8902, this one).
2. **design mode still time** — settled state per scene (recommended) or t=0.
3. **motion timeline shape** — per-column stagger strips (recommended, matches
   the storyboard) or one global timeline like studio has today.
