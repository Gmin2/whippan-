# blocks

The screen vocabulary, extracted from the 31 authored films rather than invented
from web-design convention. 332 scenes, 6298 nodes.

A launch video shows the product's own UI, not a marketing page. Standard site
furniture — testimonials, pricing tables, logo walls, footers, feature grids —
does not appear anywhere in the corpus. That absence is the point of extracting.

## the corpus, before anything else

- 2536 rect, 2320 text, 1382 path, 52 cursor, 7 image, 1 seq, **0 group**.
  Everything is drawn from primitives. A generator emits a flat node list.
- **12.7% of all nodes sit exactly on x = W/2**, 8.1% exactly on y = H/2. That
  is the strongest positional fact in the corpus by an order of magnitude.
- There is **no column grid**. There is a centre line and per-scene column
  anchors. Median margins are 0.20W and 0.24H: these are posters with a UI in
  the middle, not dense pages.
- **Radius is the real grid.** 36% of rects are a pill or circle
  (radius >= 0.45 of the short side). Card radii cluster at 0, 10, 13, 18, 20,
  24, 26, 30 @1920, with 18 the most common non-zero value.

## the blocks worth building

Ranked by how tight the underlying ratio is, not by raw instance count. These
six hold across 20+ films rather than being carried by two.

| block | films | n | the invariant |
| --- | --- | --- | --- |
| `glyph+label` | 28 | 444 | gap = **1.1 em**, glyph box ≈ label size, shared y |
| `pill` | 28 | 203 | label = **0.47 h**, radius = **h/2**, side pad = 1.4 × label |
| `title+sub` | 26 | 225 | sub = **0.5 ×** title, dy = **1.33 ×** title size |
| `line stack` | 23 | 265 | leading **1.27** display, 1.47 section, **1.55** UI copy |
| `icon tile` | 22 | 86 | square, radius = **w/4** (p25 0.240, p75 0.283) |
| `swap slot` | 25 | 70 | N texts, same font, same y, revealed one at a time |

Then, in descending confidence: `hero line` (27 films, y = 0.5H in 68 of 120),
`surface` (20 films, 0.57W × 0.60H median, centred), `disc` (18 films,
radius = w/2), `label+value` (18 films, value = **2 ×** label), `copy block`
(19 films, code leading **2.1 ×** size), `row list` (19 films, fixed pitch and
fixed column anchors), `letterbox band`, `veil`, `aurora` (blur sigma ≈ 0.05-0.1W).

## type scale

Normalised to a 1920 canvas. Sizes cluster hard rather than smoothly; peaks in
order are 26, 20, 24, 16, 30, 34, 22, 44, 32, 40, 28.

```
12  16  20  22  26  30  34  40  44  52  62  84  96  130  150
```

Below 40 the step is +4; above it roughly ×1.2.

The weight ladder is more rigid than the size ladder: **400** body, **500** UI
lead, **600** buttons and headers, **700-800** hero and mega. 300 appears 11
times, 200 twice, both in single films. `mono` is 10% of text and is reserved
for code, terminal output and timestamps.

## colour

- **67% of colour marks are achromatic.**
- Each film concentrates its chromatic marks in **one 20-degree hue bucket**.
  The disciplined ones are extreme: `higgsfield` uses #d3fe24 157 times as the
  only colour on screen; `ai-1` 81% #e8671f; `solder` 80% #2d52f0.
- Backgrounds are #ffffff (53 scenes) or #000000 (49). Everything else is one
  film committing to a single tinted paper.
- **Ink is never pure black.** #161616, #111111, #1a1a1a, #1c1c1e, #101010.
  Pure #000000 as a text colour appears in exactly one film.
- The mid-grey tier is standardised: **#8a8a8a**, **#9a9a9a**, #8f8f8f, #c9c9c9.
  Secondary text is always this tier, never a tinted grey, never lower opacity.
- About **one text node in five** carries the accent.

## four things that surprised the extraction

**The swap slot is a first-class primitive.** 70 instances in 25 films.
Counters, rolling numbers, alternating headlines and live typing results are all
authored as **N stacked text nodes at the same y**, flipped by the overlay,
never as one node with animated content. `cuttlery` cycles 8 nodes at 200px;
`blackbox` cycles 12 at 50px. A generator that does not know this emits
something the anim layer cannot animate.

**Duplicate-for-state.** "Active" and "selected" are drawn as the same rect
twice, once neutral and once tinted, at identical geometry, with opacity flipped
in the overlay.

**The outer-plus-inner rim.** `rect` has no stroke, so an edge is a pair: outer
rect, inner rect inset 4-30px with radius reduced proportionally.
`noscroll:ec_pill_o` 740×112 r56 over `ec_pill_i` 730×102 r51.

**Persistent film chrome.** Four films keep a node at identical coordinates in
every scene, muted 55-70% toward the background.

## what deliberately has no block

Checked because they look like blocks, and are not:

- **Charts.** One bar chart in the entire corpus. Zero line, sparkline, pie or
  donut. This matches the playbook's "no chart draw-ons".
- **macOS traffic lights.** One film. Every other "browser" is a plain rect.
- **Tab strips.** One real instance across 31 films.
- **Phone frames.** Five devices, no two agreeing on aspect (0.40-0.58) or
  radius (0.06-0.21). A recipe, not a block.
- **Nav bars.** Drawn as a *single text node with padded spaces*. Nobody
  positions individual nav links.
- **Toggles** (3 films), **selection handles** (1 film), **message bubbles**
  (2 films), **multiplayer cursors** (2 films, an accessory to `cursor`).
