#!/usr/bin/env python3
"""
Take the loaded hold back off scenes the reference holds still.

`loaded-hold.py` applied a drift to every scene without a camera and said so
in its own docstring: "Nothing here tries to guess where a film wants EARNED
stillness." Per-scene scoring made that guess unnecessary. 51 of 281 scenes now
move MORE than their reference, and the worst of them are scenes the reference
simply holds: `state-slim` s28a renders 14.30 against 0.09, `ravie` s11 renders
2.30 against 0.06.

A scene counts as held when its reference energy is under a quarter of that
film's own mean, so the test adapts to a busy film and a calm one alike.

This needs conform's numpy, so run it with that interpreter:

    conform/.venv/bin/python scripts/prune-still.py           dry run
    conform/.venv/bin/python scripts/prune-still.py --apply
"""
import sys, json, glob
from pathlib import Path
from importlib.machinery import SourceFileLoader

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'conform'))
from conform import load, energy, scene_spans, films        # noqa: E402

lh = SourceFileLoader('lh', str(ROOT / 'scripts' / 'loaded-hold.py')).load_module()
DOCS = ROOT / 'docs'
QUIET = 0.25          # a scene under this share of its film's mean is a hold

def prune(slug, adir, apply):
    # the analysis dir is not always named after the doc, so take the pairing
    # from conform rather than assuming it
    ref = load(sorted(glob.glob(str(Path(adir) / 'frames' / 'f*.jpg'))))
    re_ = energy(ref)
    times = [float(x) for x in open(Path(adir) / 'pts.txt') if x.strip()]
    path = DOCS / f'{slug}.anim.json'
    anim = json.loads(path.read_text())
    bar = re_.mean() * QUIET
    drop = []
    for sid, lo, hi in scene_spans(slug, times):
        hi = min(hi, len(re_))
        if hi - lo < 3 or re_[lo:hi].mean() >= bar:
            continue
        drop += [id(t) for t in anim['tracks'] if lh.is_our_hold(t, sid)]
    if drop:
        anim['tracks'] = [t for t in anim['tracks'] if id(t) not in set(drop)]
        if apply:
            path.write_text(json.dumps(anim, indent=1) + '\n')
    return len(drop)

def main():
    apply = '--apply' in sys.argv
    only = [a for a in sys.argv[1:] if not a.startswith('--')]
    avail = films()
    total = 0
    for slug in sorted(only or avail):
        try:
            n = prune(slug, avail[slug], apply)
        except Exception as e:
            print(f'{slug:<16} skipped: {e}')
            continue
        total += n
        if n:
            print(f'{slug:<16} {n:>3} held scenes')
    print(f'\n{"removed" if apply else "would remove"} the hold from {total} scenes')

if __name__ == '__main__':
    main()
