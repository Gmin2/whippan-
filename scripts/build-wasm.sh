#!/bin/bash
# rebuild the wasm engine into packages/engine-web/pkg
set -e
cd "$(dirname "$0")/.."
export CARGO_HOME=${CARGO_HOME:-$(cd .. && pwd)/.cargo}
cargo build -p whippan-engine --target wasm32-unknown-unknown --release
"$CARGO_HOME/bin/wasm-bindgen" \
  target/wasm32-unknown-unknown/release/whippan_engine.wasm \
  --target web --out-dir packages/engine-web/pkg
echo "wasm -> packages/engine-web/pkg"
