#!/bin/bash
# render every gallery example to out/<slug>.mp4
set -e
cd "$(dirname "$0")/.."
export CARGO_HOME="${CARGO_HOME:-/Users/mintu/coding/startup/json-edit/.cargo}"
cargo build --release -p whippan-engine --bin export 2>/dev/null
mkdir -p out
python3 - <<'EOF' | while read -r slug stage anim; do ./target/release/export "$stage" "$anim" "out/$slug.mp4"; done
import json
for e in json.load(open('docs/examples/index.json')):
    stage = e.get('stage', f"docs/examples/{e['slug']}.stage.json").lstrip('/')
    anim = e.get('anim', f"docs/examples/{e['slug']}.anim.json").lstrip('/')
    print(e['slug'], stage, anim)
EOF
ls -la out/
