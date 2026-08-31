#!/usr/bin/env python3
"""
Give every scene a loaded hold.

MOTION.md, from 29 frame-precise teardowns: 24 of the 29 reference films carry
0.3-3 px/frame of drift through every hold, median 1, direction fixed per scene
and never reset. `conform` measured that we render 38% of the reference motion,
and `grammar.ts` found that this one pattern accounts for 331 of 380 findings
across our 31 films. We hold still; they never do.

Measured effect at 1 px/frame, rendering at the reference timestamps:

    rezonant   energy ratio 0.29 -> 0.45   dead frames 787 -> 21
    noscroll   energy ratio 0.29 -> 0.33   dead frames 750 -> 286

Timing correlation is undisturbed in both (+0.217 -> +0.219, +0.167 -> +0.174),
so this adds motion without damaging what was already right.

Two deliberate choices:

- The move is a translate with a little zoom headroom, not a zoom. A pure zoom
  is sub-pixel per frame and barely registers (measured 1.05x at 4% over a whole
  scene). A pure translate at 1.0 zoom would slide the canvas edge into shot.
- The travel is CLAMPED to that headroom. At 1 px/frame a scene longer than
  about five seconds drifts further than the margin can hide, and 107 of our 332
  scenes are that long — x-anim's 14.2s scene wants 214px against a 64px margin.
  Those scenes drift slower than the measured median rather than revealing the
  edge. Widening the headroom instead would crop content the author placed.
- Scenes that already own a camera are left alone. Nothing here tries to guess
  where a film wants EARNED stillness — `claude` drifts for its whole run so
  that its one locked hold lands, and that is an authoring decision, not a
  mechanical one.

    scripts/loaded-hold.py --apply            every film
    scripts/loaded-hold.py --apply whippan    one
    scripts/loaded-hold.py                    dry run
"""
import json, sys
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent / 'docs'
PX_PER_FRAME = 1.0
HEADROOM = 0.08

def has_camera(anim, scene_id):
    for t in anim.get('tracks', []):
        if t.get('target') != scene_id:
            continue
        if t.get('cam') or any(k.startswith('cam_') for k in (t.get('keys') or {})):
            return True
    return False

def load(slug):
    stage = json.loads((DOCS / f'{slug}.stage.json').read_text())
    anim = json.loads((DOCS / f'{slug}.anim.json').read_text())
    return stage, anim

def add(slug, apply):
    stage, anim = load(slug)
    fps = stage.get('fps', 30)
    added = 0
    for i, sc in enumerate(stage['scenes']):
        if has_camera(anim, sc['id']):
            continue
        dur = sc.get('dur', 3)
        # what the reference rate asks for, and what the headroom can hide
        want = PX_PER_FRAME * fps * dur
        margin = stage['size'][0] * (1 - 1 / (1 + HEADROOM))
        travel = min(want, margin * 0.9)
        # alternate direction so a long film does not creep one way forever
        sign = 1 if i % 2 == 0 else -1
        anim.setdefault('tracks', []).append({
            'target': sc['id'],
            'keys': {
                'cam_zoom': [{'t': 0.0, 'v': round(1 + HEADROOM, 4)},
                             {'t': round(dur, 4), 'v': round(1 + HEADROOM, 4)}],
                'cam_x': [{'t': 0.0, 'v': round(-sign * travel / 2, 2)},
                          {'t': round(dur, 4), 'v': round(sign * travel / 2, 2)}],
            },
        })
        added += 1
    if apply and added:
        # one space, matching how the anim docs are already written
        (DOCS / f'{slug}.anim.json').write_text(json.dumps(anim, indent=1) + '\n')
    return added, len(stage['scenes'])

def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    apply = '--apply' in sys.argv
    slugs = args or sorted(p.name[:-len('.stage.json')] for p in DOCS.glob('*.stage.json'))
    total = 0
    for slug in slugs:
        try:
            added, scenes = add(slug, apply)
        except Exception as e:
            print(f'{slug:<16} skipped: {e}')
            continue
        total += added
        if added:
            print(f'{slug:<16} {added:>3} of {scenes} scenes')
    print(f'\n{"applied" if apply else "would add"} a loaded hold to {total} scenes')

if __name__ == '__main__':
    main()
