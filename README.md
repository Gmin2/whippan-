# whippan

json in, launch film out. a json-native motion format plus its own rust/skia
engine that turns a readable, agent-authorable document into a finished
launch-video mp4. see PLAN.md for the full plan.

## layout

- `engine/` — rust core. schema, overlay merge, keyframe evaluator, wasm export
- `editor/` — plain html tracer page for now (react editor comes at step 5)
- `editor/vendor/canvaskit/` — canvaskit-wasm 0.40.0 (skia), vendored
- `editor/assets/fonts/` — pinned Inter-Variable.ttf
- `analysis`, `reference` — local symlinks to the private teardown research
  (frame-precise analyses of 29 reference launch videos) and cloned reference
  runtimes. never committed; the teardowns are the craft spec and acceptance
  suite but live outside the repo

## build

`~/.cargo` is not writable on this machine, so cargo uses a workspace-local
home. every cargo command needs:

```sh
export CARGO_HOME=/Users/mintu/coding/startup/json-edit/.cargo
```

test the engine:

```sh
cargo test -p whippan-engine
```

build for the browser (wasm-bindgen CLI 0.2.126 lives in $CARGO_HOME/bin and
must match the crate version pinned in engine/Cargo.toml):

```sh
cargo build --target wasm32-unknown-unknown -p whippan-engine
$CARGO_HOME/bin/wasm-bindgen target/wasm32-unknown-unknown/debug/whippan_engine.wasm \
  --target web --out-dir editor/src/engine-pkg
```

run the tracer page:

```sh
python3 -m http.server 8777   # from the repo root
# gallery:  http://localhost:8777/editor/gallery.html
# tracer:   http://localhost:8777/editor/index.html
# conform:  http://localhost:8777/editor/conform.html
```

## engine features so far

two-layer json doc (static stage + animation overlay joined by node id),
keyframes with named and cubic-bezier easing, looped tracks, engine-owned
text (shaping, variable weight, glyph outline paths), word and per-glyph
reveals, glow emission with keyable breath, linear gradient fills. rendering
is a pure function of (doc, t) — same inputs, same frame, always.
