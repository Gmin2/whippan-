# whippan gallery — what the ui has to be

the public showcase for whippan films. separate app from the studio editor.
this doc is the contract for the rewrite: the plumbing below is inherited
and must keep working, the ui above it is being written from scratch.

---

## 1. the point of the page

every frame on this page is rendered live, in the browser, by the whippan
engine, out of a json document. that is the entire pitch and the ui exists
to make it undeniable. a visitor should not be able to mistake this for a
page of pre-rendered mp4s.

so the doc is not a detail hidden behind a link. the json that produced
what you are watching is part of the composition.

## 2. the films

registry is `/docs/examples/index.json`, 37 entries, each
`{ slug, title, dur, size, group, stage, anim }`. three groups:

- `films` (2) — whippan, solder. authored end to end here, our own work
- `reproductions` (31) — real launch videos rebuilt from json and frame
  checked against the original. terminal holds 2.26% mean, chatgpt 2.78%
- `primitives` (6) — reveal, click, goo, magic-move, transitions, camera.
  one engine capability each, one beat long

sizes vary hard (1080x1080, 2994x1618, 998x720) and durations run 1.7s to
55s. the layout has to survive both without looking ragged.

## 3. what the ui must do

**index** — the wall. every film present, grouped by the three groups above
with the groups visually distinct, not one flat list of 37. a poster frame
per film rendered by the engine, hover plays that film live in place.
posters rasterize lazily and one at a time; 37 docs at once on first paint
is not acceptable.

**film page** — the film large and playing, transport (play/pause, scrub,
time), sound on, and the doc readable. keyboard: space plays, arrows step.

**reproductions** — the comparison is the proof. our render against the
real mp4, same timestamp, scrubbing together.

**isolated route** — `?render=<slug>` gives the film full bleed on a plain
ground, no chrome. this is what frame capture and export tooling points at.
it must not regress.

## 4. inherited plumbing (port as-is, do not redesign)

**boot order**, all parallel, once per session:

- canvaskit from `<script src="/canvaskit/canvaskit.js">` in index.html,
  then `window.CanvasKitInit({ locateFile: f => '/canvaskit/' + f })`
- the wasm engine: `init(wasmUrl)` where wasmUrl is
  `@whippan/engine-web/pkg/whippan_engine_bg.wasm?url`
- fonts: fetch `/fonts/Inter-Variable.ttf` and
  `/fonts/JetBrainsMono-Regular.ttf`, hand both to `register_font` as
  `inter` and `mono`. the engine shapes its own text, so a missing font is
  a blank film, not a fallback
- the registry from `/docs/examples/index.json`

**rendering** — `render(stageJson, animJson, t)` returns draw commands,
`paintFrame(ck, canvas, paint, cmds, images)` from
`@whippan/engine-web/painter` puts them on a skia surface. that is the only
path to a pixel in this app. no dom or css reimplementation of a node type,
ever, for any reason.

**doc loading** — fetch stage + anim json, then walk `stage.scenes[].nodes`
and preload every image: `type: 'image'` uses `n.src`, `type: 'seq'` expands
to `n.src + 'fNNN.png'` for `n.count` frames. decode through
`CK.MakeImageFromEncoded` into a `Map` keyed by src, passed to paintFrame.

**duration** — `stage.scenes.reduce((a, s) => a + (s.dur ?? 3), 0)`.

**sound** — per loaded doc: the `stage.audio` bed through an `<audio>`
element (honour `src`, `gain`, `start`) plus engine-derived sfx events from
`sfx(stage, anim)` scheduled through webaudio. buffers warm on load so the
first play is on time. needs play/pause/seek/loop/dispose slaved to the same
clock the canvas uses. sfx files live at `/assets/sfx/`, tick and pop have
8 variants each.

**vite config** — `optimizeDeps.exclude: ['@whippan/engine-web']` (the wasm
glue must not be pre-bundled) and `server.fs.allow: ['../..']` (the public
symlinks point outside the app). port 8901.

**public symlinks** — recreate all four, they are how the app sees the repo
assets without a copy step:

```
public/assets    -> ../../../assets
public/canvaskit -> ../../../assets/canvaskit
public/docs      -> ../../../docs
public/fonts     -> ../../../assets/fonts
```

**workspace** — the app is a pnpm workspace member under `apps/*` and takes
`"@whippan/engine-web": "workspace:*"`.

## 5. constraints

- canvaskit needs a gpu surface, so headless screenshots come back blank
  unless the shot is taken through a real gpu path. verify visually in a
  real browser, not only in automation
- a film is rasterized once per session and cached. switching films must
  not re-cut posters
- no screen in this app may read as generic. specific nouns, real numbers,
  the actual film names. see the reference grammar in `analysis/`
