# conform

How close a rendered film is to the video it reproduces.

PLAN.md §7 asks for this and calls conformance "the honest progress metric, not
vibes". Without it, "is this film good" is somebody's opinion about a
screenshot.

## running it

```
python3 -m venv conform/.venv
conform/.venv/bin/pip install -r conform/requirements.txt
cargo build --release -p whippan-engine --bin export

conform/.venv/bin/python conform/conform.py              # every film
conform/.venv/bin/python conform/conform.py claude       # one
conform/.venv/bin/python conform/conform.py --stride 3   # fast pass
conform/.venv/bin/python conform/conform.py --selftest   # check the measure
```

Results land in `out/conform/`: `results.json`, a `report.html` with heatmaps,
and the rendered frames (cached on doc mtime, so a re-run after an unrelated
edit is fast).

Covers the 28 films that have both a doc in `docs/` and extracted frames in
`analysis/`.

## what it measures

It renders the doc at the reference video's **own presentation timestamps**
(`analysis/<film>/pts.txt`), so frame N of ours and frame N of theirs are the
same instant, and then scores two independent things.

**timing** — pearson correlation of the two motion-energy curves. Do we move
when they move. It is brutally sensitive: on `claude`, aligned scores `r=0.616`
and a **one frame** offset collapses it to `0.002`.

**appearance** — mean absolute pixel error over the whole frame, 0-255. Does it
look like theirs. Monotonic in misalignment: `3.32` aligned, `6.52` ten frames
out, `16.98` sixty frames out.

Plus **energy ratio**, ours over theirs. Near zero means we render a still
against a moving reference, which correlation alone cannot tell you. `terminal`
scores `0.00` here: its only animation is a `glow_opacity` pulse that produces
no measurable change.

There is deliberately **no single blended percentage**. Timing and appearance
fail for different reasons and a blend would hide which one moved.

`best_lag` reports the frame offset that would score best. A film can be right
but late, and that is one `at` away from fixed rather than a rewrite.

## what was tried and rejected

**Whole-frame SSIM.** It does not work here, demonstrated rather than assumed.
On `terminal`:

| comparison | mean SSIM |
| --- | --- |
| aligned | 0.8768 |
| offset one second | 0.8777 |
| reference played backwards | 0.8768 |
| flat grey | 0.5211 |

Misaligned scores *higher* than aligned. SSIM is dominated by the static
majority of the frame, so it measures "both are mostly a dark terminal". A
harness built on it would report 0.88 forever and never move. Same result for
SSIM of temporal differences: two mostly-black difference images agree on the
black.

Do not reintroduce either without a control run proving it separates aligned
from offset.

## trusting the number

`--selftest` recomputes motion energy for the stored reference frames and
asserts it matches `analysis/<film>/motion-energy.txt`, which was produced by
`analysis/extract.sh`. Max absolute error is 0.0005. Our measure and the
extraction pipeline are the same measure, not two that happen to look alike.

The absolute values are not meaningful on their own. **What matters is that they
move.** Record a baseline, change something, run it again.
