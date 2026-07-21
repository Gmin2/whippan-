#!/bin/bash
# push the current engine build, painter and docs into the two app repos.
# run after any engine rebuild or new doc: ./scripts/sync-apps.sh
set -e
cd "$(dirname "$0")/.."
for app in ../whippan-studio ../whippan-gallery; do
  [ -d "$app" ] || continue
  cp -r editor/src/engine-pkg/* "$app/vendor/engine-pkg/"
  cp editor/src/painter.js "$app/vendor/painter.js"
  cp docs/*.json "$app/public/docs/" 2>/dev/null || true
  mkdir -p "$app/public/assets/audio" "$app/public/assets/sfx"
  cp assets/audio/*.m4a "$app/public/assets/audio/" 2>/dev/null || true
  mkdir -p "$app/public/assets/audio/refs"
  cp assets/audio/refs/*.m4a "$app/public/assets/audio/refs/" 2>/dev/null || true
  cp assets/sfx/*.wav "$app/public/assets/sfx/" 2>/dev/null || true
  cp docs/examples/*.json "$app/public/docs/examples/"
  echo "synced $app"
done
