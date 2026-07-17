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
cd editor && python3 -m http.server 8777
# open http://localhost:8777/index.html
```

## status

- step 0 done — tracer bullet: json -> rust(wasm) -> draw commands -> canvas -> scrubber
- step 1 done — two-layer doc (stage + overlay merged by id, per-track `at`),
  cubic-bezier easing, paint swapped to skia (canvaskit)
- step 2 in progress — primitives gated by reference beats:
  - text owned by the engine: rustybuzz shaping, weight axis, glyph outlines
    as paths, word + per-glyph reveal with the accent temper (vs ai-1 f0048-56)
  - glow: blurred echo emission with `glow_sigma`/`glow_opacity` keyable,
    looped tracks for the breath (vs terminal f0027)
- next fidelity targets: gradient fills + directional glow offset (terminal's
  lit-tube pill, 1.6x top-heavy bloom), mono font support, multi-scene timing
