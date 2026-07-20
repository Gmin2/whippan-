#!/bin/bash
# register a finished reproduction in the gallery and sync the apps:
# ./scripts/add-repro.sh <slug> <dur> <w> <h>
set -e
cd "$(dirname "$0")/.."
python3 - "$1" "$2" "$3" "$4" <<'PY'
import json, sys
slug, dur, w, h = sys.argv[1], float(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
p = 'docs/examples/index.json'
reg = json.load(open(p))
if not any(e['slug'] == slug for e in reg):
    idx = max(i for i, e in enumerate(reg) if e.get('group') == 'reproductions') + 1
    reg.insert(idx, {"slug": slug, "title": f"{slug} (repro)", "dur": dur,
                     "size": [w, h], "group": "reproductions",
                     "stage": f"/docs/{slug}.stage.json",
                     "anim": f"/docs/{slug}.anim.json"})
    json.dump(reg, open(p, 'w'), indent=1)
    print(f"registered {slug}")
else:
    print(f"{slug} already registered")
PY
./scripts/sync-apps.sh
