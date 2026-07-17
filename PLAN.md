# whippan — build plan

the founding doc for the rebuild. written 2026-07, updated as we go.

---

## 0. what we are building

an app that makes launch-quality animated videos. you author a readable json,
and our own engine renders it to a finished mp4 that matches the craft of the
reference videos in `analysis/`. a figma-like editor sits on top for humans; an
ai can author the same json directly.

we are not building "after effects with a json file." the craft (how a senior
motion designer animates) lives *inside the engine*, so pro motion comes out by
default. we are replacing the whole figma -> after effects -> export chain with
one loop where the artifact is a readable document.

## 1. the bar (non-negotiable)

the engine is only good enough when it can reproduce the reference videos
**frame for frame**. the 29 teardowns in `analysis/` are not inspiration, they
are the **test suite**. every micro-detail — the orange-to-black word ritual,
glow breathing, motion-blur streaks, gooey pill morphs, per-glyph typewriters,
beat-locked cuts — is a capability the engine must have because a reference
uses it. mediocre is a failed test, not a taste call.

## 2. locked decisions

| area | decision | why |
|---|---|---|
| engine language | **Rust** | one source compiles native (fast export) AND wasm (live editor). one engine, two targets, no second renderer |
| paint backend | **Skia**, behind Rive's ~15-method renderer interface | proven rasterizer; our new code is everything above pixels; a custom/GPU renderer stays a clean future swap |
| layout | **Taffy** (rust flexbox) | pure rust, compiles into the wasm with no extra boundary |
| text | **own shaping + per-glyph** (skparagraph model) | browser text is nondeterministic; per-glyph outlines needed for reveals |
| editor | **TypeScript + React** around the wasm engine canvas | React does panels/inspectors, the engine draws the canvas |
| format | **clean json** (Lottie's idea, not Lottie's format) | declarative doc a player renders; we avoid Lottie's format sins |
| document model | **two layers: stage + animation overlay** | matches the figma->AE split; AI authors in two passes; restage without breaking motion |
| determinism | `render(doc, t)` is pure, O(1) seek, no wall clock | frame N depends only on N; scrub = export = same code |
| sequencing | **engine first, editor at step 5** | an editor on an unproven engine just builds mediocre faster |

what we are explicitly NOT doing: browser-as-renderer (Remotion/revideo/
motion-canvas screenshot chrome — the reference notes call it a dead end);
porting the old whippan engine or protocol; building our own rasterizer now.

## 3. the document model — two layers

**layer 1: the stage** — everything that exists, static, no time. this is the
figma file as data.

```json
{ "fps": 30, "size": [1920,1080],
  "scenes": [
    { "id": "s1", "bg": "#fafafa",
      "nodes": [
        { "id": "title", "type": "text", "text": "The fastest way to scale",
          "x": 960, "y": 540, "font": {"family":"grotesk","weight":600,"size":72},
          "color": "#161616" },
        { "id": "pill", "type": "rect", "x": 960, "y": 640, "w": 480, "h": 96,
          "radius": 48, "fill": "#ea752f" }
      ] } ] }
```

**layer 2: the animation overlay** — thin, references stage elements by id,
describes only motion. never re-describes an element.

```json
{ "tracks": [
    { "target": "title", "at": 0.0,
      "reveal": { "mode": "word", "stagger": 0.1 },
      "enter": { "preset": "rise-fade", "intensity": "snappy" } },
    { "target": "pill", "at": 1.1, "enter": { "preset": "pop" } }
  ] }
```

**three authoring depths, you go only as deep as needed:**
1. **stage** — arrange elements (the easy part, figma-like)
2. **choreograph** — attach intent (`reveal: word`, `enter: pop`); the engine
   expands intent into keyframes using the *measured numbers from the teardowns*
3. **raw keyframes** — the escape hatch for the last 10% and for exact
   reproduction; any track can drop to explicit keyframes with easing

**the contract:** intent compiles down into raw keyframes, so the engine only
ever plays keyframes (simple, exact). humans and the ai mostly author at the
intent level. stable element ids are the join between the two layers — the
engine merges stage + overlay at load (resolve each track onto its element),
then plays the merged result.

## 4. the monorepo

```
whippan/                  cargo + pnpm workspace
  engine/               ← the new core, Rust
    core/               doc types, the merge, the seek(t) evaluator, scene graph
    anim/               keyframes, easing (cubic-bezier), presets->keyframes
    layout/             taffy adapter
    text/               shaping, line-break state machine, per-glyph outlines
    render/             the ~15-method renderer trait (backend-agnostic)
    render-skia/        the renderer impl over skia
    wasm/               wasm-bindgen bindings the editor calls
    native/             native lib + export binary (frames -> ffmpeg)
  editor/               ← TS/React figma-like app, drives engine/wasm (step 5)
  schema/               the two-layer doc types, shared rust<->ts by codegen
  conform/              frame-diff harness: our render vs the real mp4 frames
  analysis/  (link)     the 29 teardowns = the craft spec + test suite
  reference/ (link)     the runtimes we steal shapes from
  PLAN.md               this file
```

## 5. the engine internals (the pipeline)

every serious engine studied (`reference/notes/`) converges on the same layered
shape. we adopt it:

```
document         two-layer json -> merged, compiled to animators
                 every animated property = pure f(t)          (skottie/remotion purity)
                 property = static | keyframes + cached ease   (rlottie Property<T>)
scene graph      retained nodes, dirty flags, damage           (sksg invalidate/revalidate)
                 transforms as their own composable nodes
layout pass      taffy behind a thin adapter
                 text measure callback -> skia metrics
text             shape once, re-break only on width change     (skparagraph state machine)
                 per-glyph outlines for reveals
paint            ~15-method Renderer trait over skia            (rive renderer.hpp)
                 nodes never touch the backend directly
media            seek keyframe, decode forward to pts, cached   (remotion rust compositor)
audio            offline pass from render-time events           (remotion filtergraphs)
export           raw rgba piped to long-lived ffmpeg in order   (no png round-trip)
```

cross-cutting rules (the determinism contract):
1. rendering frame N depends only on N — no wall clock, no accumulated deltas,
   seeded randomness only
2. seek is O(1) random access via pure evaluation (better than step-replay)
3. static elision — constant properties bake at compile; the animator list
   holds only what actually moves
4. one canonical time unit (seconds), everywhere
5. the four contracts pinned from the notes: `seek(t)->changed`, the keyframe
   interpolation, invalidate/revalidate damage, the text-layout state machine

## 6. the build sequence — each step run for real before the next

**step 0 — tracer bullet (the spine).** monorepo + Rust engine compiled to
wasm, drawing ONE text node from a stage json at time `t`, into a canvas in a
tiny React page with a scrubber. crudest paint (canvas2d) to prove the pipe.
*proof:* open the page, drag the scrubber, watch the title move. proves
doc -> evaluate -> wasm -> canvas -> scrub connect before any feature exists.

**step 1 — format + seek contract + Skia.** define the two-layer schema v0 and
the pure evaluator `render(merged, t)`. keyframes with hold/linear/cubic-bezier
easing (ported from skottie's interpolator + rive's cubic solver). swap the
crude canvas2d for the Skia backend behind the renderer trait.
*proof:* hand-write a stage+overlay with a box that moves and fades on
keyframes; scrub; the motion matches the numbers.

**step 2 — primitives, each gated by a reference beat.** build node types and
paint features in order of how load-bearing they are across the 29 videos, and
prove each by reproducing the exact reference moment that needs it:
- per-glyph/word text reveals + orange-to-black color temper -> ai-1 opening line
- gradients, glow/bloom, soft shadows -> terminal's glow-breathing pill
- rounded-rect pills, strokes, connectors -> a flow-diagram beat
- transforms, blur, directional motion-blur -> a crash-zoom / streak entrance
- masks/clips, gooey metaball morphs -> a logo-pill expansion
- taffy layout for auto-arranged nodes; images / video frames

**step 3 — reproduce a whole video, frame-diffed.** author a full reference's
json by hand from its teardown, render every frame, pixel-diff against the real
mp4 in `conform/`. order: terminal (4s, one artifact) -> launch-quick4 ->
spaces (multi-scene). *gate:* under a few percent per-frame difference.

**step 4 — export.** compile the same engine native, render frames headless,
pipe raw rgba to ffmpeg, mux audio (steal remotion's volume envelopes + aac
grid alignment). *proof:* export the terminal reproduction as a real mp4, play
it next to the original.

**step 5 — the figma-like editor.** now, on the proven engine: canvas of scenes
(stage mode), select/move/edit nodes writing back to the stage json, animate
mode for the overlay, inspector, timeline with draggable keyframes. every editor
action is just a json mutation the engine already renders, so it always previews
truthfully.

**step 6 — presets + AI authoring.** the measured choreography becomes the
preset library (intent -> keyframes); then an agent authors stage + overlay end
to end. "an agent writes the launch video first try," on an engine that provably
hits the bar.

## 7. reproduction as the test suite

- `conform/` renders any doc through the engine at the real timestamps and
  pixel-diffs against the extracted frames (we already have every frame + the
  diff technique from the old harness), red heatmaps for misses
- target order by difficulty: terminal -> launch-quick4 -> spaces -> claude ->
  ai-1. each new target surfaces the next missing primitive, which becomes the
  next work item
- conformance % is the honest progress metric, not vibes

## 8. milestones

- **M1 spine:** steps 0-1. a keyframed box, on Skia, scrubbable in the browser.
- **M2 first pixels match:** steps 2-3 through terminal reproduced under the gate.
- **M3 first export:** step 4. a real mp4 out, matching an original.
- **M4 authoring:** step 5. the editor drives the engine.
- **M5 agent-authored:** step 6. presets + ai first-draft.

## 9. open questions / risks

- Skia in wasm: use CanvasKit (official skia wasm) vs compiling skia-safe to
  wasm — decide at step 1 when we do the backend swap
- rust<->ts type sharing: codegen approach (ts-rs or schemars->json-schema->ts)
  — decide at step 1 when the schema stabilizes
- scope of ui-capture vs motion-graphics: aiming motion-graphics + ui-mockup
  first; real screen-capture ingestion is later, not core
- font strategy: pin a small set (a grotesk + a mono) for determinism, exactly
  as the old engine did
