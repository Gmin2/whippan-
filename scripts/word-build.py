"""Give headlines a word build.

23 of 29 torn-down films reveal their headlines one word at a time, but only
11% of our text nodes do. This promotes the ones that should: text that is
already large, already several words, and already fades in.

The thresholds come from the 248 nodes we already author this way, not from
taste: they sit at a median 66px and 3 words, against 30px and 1 word for
plain text. Stagger 0.09s is our own median and matches the 3 frames/word the
teardowns measured.

  compose  add the reveal, leave the existing keys alone
  own      let the reveal own the entrance, keeping any exit fade

The engine multiplies node opacity by the reveal's per-word opacity, so both
are safe; they differ in whether the whole block also fades as the words land.
"""
import json, sys, os, glob

MIN_PX = 40      # @1920, between plain median 30 and revealed median 66
MIN_WORDS = 3
STAGGER, DUR, RISE = 0.09, 0.3, 20

def entrance_only(keys):
    """True if this property just brings the node on and never takes it off."""
    return keys and keys[-1].get('v') == max(k.get('v', 0) for k in keys)

def promote(slug, mode, dest):
    stage = json.load(open(f'docs/{slug}.stage.json'))
    anim = json.load(open(f'docs/{slug}.anim.json'))
    W = stage['size'][0]
    scale = W / 1920
    nodes = {n['id']: n for sc in stage['scenes'] for n in sc['nodes']}
    # a node can carry several tracks; only its first may reveal, or the later
    # one silently replaces it and takes the rest of that track with it
    spoken = {t['target'] for t in anim['tracks'] if t.get('reveal')}
    done = 0
    for t in anim['tracks']:
        if t.get('reveal') or t.get('target') in spoken:
            continue
        n = nodes.get(t.get('target'))
        txt = n and n.get('text')
        if not isinstance(txt, str):
            continue
        keys = t.get('keys') or {}
        if 'opacity' not in keys and not t.get('enter'):
            continue
        size = (n.get('font') or {}).get('size', 0) / scale
        if size < MIN_PX or len(txt.split()) < MIN_WORDS:
            continue
        t['reveal'] = {'unit': 'word', 'stagger': STAGGER, 'dur': DUR,
                       'rise': round(RISE * scale)}
        spoken.add(t['target'])
        if mode == 'own':
            op = keys.get('opacity')
            if op:
                # hold it on from the first key; the reveal now does the arriving
                hold = [k for k in op if k.get('v', 0) >= 1]
                keys['opacity'] = [{'t': op[0]['t'], 'v': 1}] + \
                                  [k for k in op if k['t'] > (hold[0]['t'] if hold else op[0]['t'])]
            y = keys.get('y')
            if y and entrance_only(y) is False:
                pass
            elif y:
                del keys['y']          # rise owns the vertical now
            t.pop('enter', None)
        done += 1
    # one space, matching how the anim docs are already written
    open(dest, 'w').write(json.dumps(anim, indent=1) + '\n')
    return done

if __name__ == '__main__':
    slug, mode = sys.argv[1], sys.argv[2]
    dest = sys.argv[3] if len(sys.argv) > 3 else f'docs/{slug}.anim.json'
    print(f'{slug} [{mode}]: {promote(slug, mode, dest)} headlines promoted -> {dest}')
