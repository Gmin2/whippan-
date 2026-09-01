#!/usr/bin/env python3
"""
Swap a film's `surface` blocks for real product screenshots.

The block library can draw an app window; it cannot draw the product. A launch
film that shows a generic card where the product should be is the failure mode
the whole corpus avoids, so the generated film leaves those beats sparse and
this puts the real capture in.

The image inherits the surface group, so every track the generator wrote for
that block keeps working: one track on the group still animates the whole
thing.

    scripts/place-shots.py <slug> <scene>=<image> [<scene>=<image> ...]
"""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SHOTS = ROOT / 'apps/boards/public/assets/solder26'



def block_box(nodes, gid):
    """the ink extent of one block, so two of them can be kept apart"""
    ks = [n for n in nodes if n.get('group') == gid]
    if not ks:
        return None
    def span(n):
        if n.get('h'):
            return n['y'] - n['h'] / 2, n['y'] + n['h'] / 2
        fs = (n.get('font') or {}).get('size', 24)
        return n['y'] - fs * 0.7, n['y'] + fs * 0.7
    tops, bots = zip(*(span(n) for n in ks if n.get('y') is not None))
    return min(tops), max(bots)


def unstack(sc, H):
    """Push overlapping blocks apart.

    The model places a block by its centre and cannot know how tall the library
    will draw it, so an icon tile and a wordmark asked for adjacent centres end
    up on top of each other. The library owns geometry, so the library resolves
    this rather than the prompt.
    """
    groups = [n for n in sc['nodes'] if n.get('type') == 'group']
    boxes = [(g, block_box(sc['nodes'], g['id'])) for g in groups]
    boxes = [(g, b) for g, b in boxes if b]
    boxes.sort(key=lambda gb: gb[1][0])
    pad = round(H * 0.02)
    moved = 0
    for i in range(1, len(boxes)):
        (_, prev), (g, cur) = boxes[i - 1], boxes[i]
        if cur[0] >= prev[1] + pad:
            continue
        dy = round(prev[1] + pad - cur[0])
        for n in sc['nodes']:
            if n.get('group') == g['id'] or n is g:
                n['y'] += dy
        boxes[i] = (g, (cur[0] + dy, cur[1] + dy))
        moved += 1
    return moved

def over_key(over):
    """the same units, in reading order, without disturbing the caller's list"""
    return sorted(over, key=lambda u: min(k['y'] for k in u[1]))


def clear_below(sc, W, H, floor):
    """Stack every block that overlaps the shot underneath it, on the centre.

    Moving nodes individually scattered them and broke both alignment and the
    collision check. A block is a unit: shift the whole group by one offset so
    its internal layout survives, and put every moved group on the same x.
    """
    groups = [n for n in sc['nodes'] if n.get('type') == 'group']
    kids = {g['id']: [n for n in sc['nodes'] if n.get('group') == g['id']] for g in groups}
    loose = [n for n in sc['nodes']
             if n.get('type') not in ('group', 'image') and not n.get('group')]
    units = [(g, kids[g['id']]) for g in groups if kids[g['id']]] + [(n, [n]) for n in loose]
    over = [u for u in units if any(k.get('y') is not None and k['y'] < floor for k in u[1])]
    if not over:
        return 0
    # reading order, then stacked with the corpus gap between blocks
    # Blocks that sit at different x on the same row are a row: three stats
    # side by side. Forcing those to the centre line stacks them on top of one
    # another, which is how a clean layout turned into three text collisions.
    rows = {}
    for head, ks in over_key(over):
        rows.setdefault(round(min(k['y'] for k in ks) / 60), []).append(head)
    in_row = {h['id'] for hs in rows.values() if len(hs) > 1 for h in hs}

    over.sort(key=lambda u: min(k['y'] for k in u[1]))
    gap = round(H * 0.055)
    stack = sum(max(k['y'] for k in ks) - min(k['y'] for k in ks) for _, ks in over) \
        + gap * max(0, len(over) - 1)
    # never push content off the bottom: if the stack will not fit under the
    # shot, lift the whole stack rather than let it run past the frame
    y = floor + round(H * 0.045)
    bottom = round(H * 0.94)
    if y + stack > bottom:
        y = max(round(H * 0.06), bottom - stack)
    for head, ks in over:
        span = max(k['y'] for k in ks) - min(k['y'] for k in ks)
        dy = y - min(k['y'] for k in ks)
        centre = head['id'] not in in_row
        for k in ks:
            k['y'] += dy
            if centre:
                k['x'] = W // 2
        if head is not ks[0] or len(ks) > 1:
            head['y'] = round(sum(k['y'] for k in ks) / len(ks))
            if centre:
                head['x'] = W // 2
        # a row shares one band, so it advances once rather than per block
        if centre or head is over[-1][0]:
            y += span + gap
    return len(over)

def main():
    slug = sys.argv[1]
    mapping = dict(a.split('=', 1) for a in sys.argv[2:])
    stage = json.loads((ROOT / f'docs/{slug}.stage.json').read_text())
    W, H = stage['size']
    done = 0
    for sc in stage['scenes']:
        shot = mapping.get(sc['id'])
        if not shot:
            continue
        surf = next((n for n in sc['nodes'] if n['id'].startswith('surface') and n.get('type') == 'group'), None)
        if not surf:
            # No surface block on this beat, so the film would play a text card
            # where the product should be. Put the capture in the upper two
            # thirds and move the caption clear of it, which is what the corpus
            # does: product above, one line under.
            top, w2 = 400, round(W * 0.66)
            h2 = round(w2 * 806 / 1920)
            moved = clear_below(sc, W, H, top + h2 // 2)
            sc['nodes'].insert(0, {
                'id': f'shot_{sc["id"]}', 'type': 'image',
                'src': f'/assets/solder26/{shot}',
                'x': W // 2, 'y': top, 'w': w2, 'h': h2, 'radius': 14,
            })
            done += 1
            print(f'  {sc["id"]:<5} <- {shot}  {w2}x{h2} above, {moved} blocks moved clear')
            continue
        # the capture is 1920x806; hold that ratio and sit it at 78% of frame
        w = round(W * 0.78)
        h = round(w * 806 / 1920)
        sc['nodes'] = [n for n in sc['nodes'] if n.get('group') != surf['id']]
        moved = clear_below(sc, W, H, surf['y'] + h // 2)
        sc['nodes'].insert(0, {
            'id': f'shot_{sc["id"]}', 'type': 'image',
            'src': f'/assets/solder26/{shot}',
            'x': surf['x'], 'y': surf['y'], 'w': w, 'h': h,
            'radius': 14, 'group': surf['id'],
        })
        done += 1
        print(f'  {sc["id"]:<5} <- {shot}  {w}x{h} at {surf["x"]},{surf["y"]}'
              + (f', {moved} blocks moved clear' if moved else ''))

    # every scene, not only the ones that took a screenshot
    apart = sum(unstack(sc, H) for sc in stage['scenes'])
    if apart:
        print(f'pushed {apart} overlapping blocks apart')
    (ROOT / f'docs/{slug}.stage.json').write_text(json.dumps(stage, indent=1) + '\n')
    print(f'placed {done} screenshots')

if __name__ == '__main__':
    main()
