#!/usr/bin/env python3
"""
Bring entering elements into focus, not just into position.

MOTION.md: 18 of the 29 reference films resolve elements from blur to sharp.
The element is at its final position from frame one and only its focus changes.
Whole panels rack over 25-35 frames, single objects ~7, glyphs 2-3.

It was unreachable until `blur` was made to work on every node kind (before
that only rects could defocus, so no word, icon or screenshot could use it).

Composes rather than replaces: `enter` presets write opacity, y and scale, this
writes only `blur`, so a node fades, rises AND sharpens the way the references
do. Contract rule 3 is respected by skipping any node whose blur is already
owned.

    scripts/blur-resolve.py --apply [slug ...]
"""
import json, sys
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent / 'docs'
RACK = {'panel': 30, 'object': 7, 'glyph': 3}

def rack_for(node, W, H):
    size = (node.get('font') or {}).get('size', 48)
    area = node.get('w', size * 6) * node.get('h', size * 1.4)
    share = area / (W * H)
    k = W / 1920
    if share > 0.15:   return RACK['panel'], round(18 * k)
    if share > 0.02:   return RACK['object'], round(10 * k)
    return RACK['glyph'], round(5 * k)

def add(slug, apply):
    stage = json.loads((DOCS / f'{slug}.stage.json').read_text())
    anim = json.loads((DOCS / f'{slug}.anim.json').read_text())
    W, H = stage['size']; fps = stage.get('fps', 30)
    owns_blur = {t.get('target') for t in anim['tracks'] if 'blur' in (t.get('keys') or {})}
    added = 0
    for sc in stage['scenes']:
        for n in sc['nodes']:
            if n.get('type') == 'group' or n['id'] in owns_blur:
                continue
            # only things that actually enter; a node already on screen has
            # nothing to resolve from
            entry = next((t for t in anim['tracks']
                          if t.get('target') == n['id']
                          and (t.get('enter') or 'opacity' in (t.get('keys') or {}))), None)
            if not entry:
                continue
            frames, sigma = rack_for(n, W, H)
            anim['tracks'].append({
                'target': n['id'],
                'at': round(entry.get('at', 0), 4),
                'keys': {'blur': [{'t': 0.0, 'v': sigma},
                                  {'t': round(frames / fps, 4), 'v': 0, 'ease': 'outCubic'}]},
            })
            owns_blur.add(n['id'])
            added += 1
    if apply and added:
        (DOCS / f'{slug}.anim.json').write_text(json.dumps(anim, indent=1) + '\n')
    return added

def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    apply = '--apply' in sys.argv
    slugs = args or sorted(p.name[:-len('.stage.json')] for p in DOCS.glob('*.stage.json'))
    total = 0
    for slug in slugs:
        try:
            n = add(slug, apply)
        except Exception as e:
            print(f'{slug:<16} skipped: {e}'); continue
        total += n
        if n: print(f'{slug:<16} {n:>4} nodes')
    print(f'\n{"applied" if apply else "would add"} a blur resolve to {total} nodes')

if __name__ == '__main__':
    main()
