# motion

The motion vocabulary, extracted from the 29 frame-precise teardowns in
`analysis/` rather than from mograph convention. 31,842 frames read, ~995 lines
of distilled grammar across the 29 "what to steal" sections.

Companion to `BLOCKS.md`. Blocks say what a frame contains. This says what
happens between two frames, and whether the engine can already say it.

Written because `conform/BASELINE.md` measured that we render **38% of the
reference motion**, and `grammar.ts` then found that one pattern — *the camera
never fully stops* — accounts for **331 of 380** findings across our 31 films.

## the corpus, before anything else

- **The reference set does not cut.** 8 of 29 films have **zero** hard cuts:
  `atlas-video`, `base-2`, `higgsfield-figma` (70s), `motion-main`, `replit`
  (76s), `survey`, `terminal`, `x-anim`. 12 have at most one; 20 have at most
  three. `ravie` spends 94.5s on two. We hard-cut between scenes. That is a
  grammar mismatch, not a tuning gap.
- **Nothing holds still.** 24 of 29 carry sub-pixel to 3px/frame drift through
  every hold. `skale-main` and `sunflower` measure a flat frame-diff hum of
  **8-10** across their whole runtime against cut spikes of 100-240 — a floor of
  ~4% of a cut, sustained on 100% of frames.
- **Zero springs.** Overshoot is a design choice in exactly one film (`crab`, a
  physics toy) plus one 3-frame micro-instance in `terminal`.
- **Opacity leads transform, always.** `ai-1` states it twice verbatim.
- **Our own baseline agrees.** The seven films scoring energy >= 0.5 are the
  ones whose grammar is discrete pops and snaps. The floor — `terminal` 0.00,
  `atlas` 0.12, `base44` 0.16, `replit` 0.17, `lovable` 0.18 — is exactly the
  continuous-camera, blur-resolve family. **We are failing at soft, not at hard.**

## the devices

Ranked by film count x runtime covered.

| device | films | what it is | engine |
| --- | --- | --- | --- |
| `loaded hold` | 24 | every hold drifts 0.3-3 px/frame; nothing is ever locked | already expressible |
| `word build` | 23 | line assembles token by token, accent cools to ink | expressible (`reveal`); applied to 70 headlines 2026-08-31 |
| `camera as edit` | 20 | crash-zoom, push, whip-pan replace cuts | **built but undocumented** |
| `blur resolve` | 18 | arrives in place, heavily blurred, racks to sharp | expressible; tried and measured no effect, see below |
| `typewriter` | 17 | chars at keystroke times, two-speed, live caret | already expressible |
| `cursor grammar` | 16 | bell velocity, long park, click = a state change | already expressible |
| `arrival cascade` | 15 | UI materialises whole, 2-4f offsets, one ~14f envelope | awkward: one track per node |
| `swap in place` | 12 | content flips, geometry survives | awkward: N stacked nodes |
| `chrome + playhead` | 12 | the film renders its own scaffolding, and it animates | already expressible |
| `polarity flip` | 11 | 1-frame canvas swap, one element rides across unchanged | already expressible |
| `scatter / reflow` | 10 | same elements translate between scatter and grid | awkward at scale |
| `overlap handoff` | 9 | exit and entrance share ~6 frames; no empty frame | awkward: transition only |
| `number roll` | 8 | odometer, 5-6f per digit. **4 films explicitly refuse it** | awkward: no clip |
| `blob birth / goo` | 7 | born as a soft blob that condenses; connection is shared goo | already expressible |

Below five films it is a signature, not a device.

## the numbers worth keeping

**loaded hold** — constant velocity, direction fixed per scene, never reset.
Measured 0.3-3 px/f across eight films; **median 1 px/frame = 30 px/s**, so a
3s hold slides the frame 90px. Then the asymptotic tail: `ai-1`'s carousel
decays 5 → 4 → 3 → 1 → <0.5 px/f, and creeps 30px over 54 frames *after* a zoom
has nominally settled. **The move is ~20% of the frames; the tail is ~80%.**

**word build** — a new word every **3 frames (100ms)**, range 2-6. Temper from
accent to ink over **~8 frames (267ms)**, range 3-15. Born 30-50px below
baseline, rising while settling over ~9 frames. Exactly one word per line keeps
the accent. Exits are usually instant, 1 frame, with survivors re-centring.

**camera as edit** — crash zoom 1.55x-2.4x in 3-4 frames, **peak velocity at
20-24% of the move** in three of four measured films, then a settle 3-4x the
length of the attack. Whip-pan is **3-6 frames** of pure horizontal blur.
Slow push ~10% over 30 frames.

**blur resolve** — whole panels rack over 25-35 frames, single objects over
~7, glyphs over 2-3. The element is at its final position from frame one and
only its focus changes.

> **Measured 2026-08-31 and not shipped.** A blur rack added to all 58
> entrances of `rezonant` moved nothing: mae 17.38 → 17.37 of 255, energy
> 0.407 → 0.403, timing +0.218 → +0.219. Dead frames rose 21 → 52, which is
> the tell — blur *smooths* detail, so it lowers frame-to-frame difference
> during the very frames it covers. Two readings, both worth keeping: the
> racks are short against a 1204-frame film and vanish at the 160×90
> measuring grid, and our corpus authors entrances as raw opacity keys
> (`enter` presets appear in 4 of 5962 tracks), so the device was *added to*
> a positional entrance rather than *replacing* it, which is not what the
> references do. Do not re-attempt without first making a film whose
> entrances are focus-only, and judge it by eye, not by conform.

**word build** — applied 2026-08-31 to the 70 headlines across 16 films that
were large enough and long enough to read as one and still only faded in.
Coverage went from 11% of text nodes to 14%. Thresholds were learned from the
248 nodes we already revealed this way rather than chosen: 40px @1920 and 3
words sits between the revealed median (66px, 3 words) and the plain one
(30px, 1 word).

> **conform cannot see this and that is expected.** Across 13 scored films
> energy, timing and mae all held to within hundredths. Only 32 of 1666 frames
> of `state-slim` differ from before, by at most 7.7 of 255. The reason is
> structural: the biggest promoted headline anywhere is 12% of the frame and a
> build lasts ~15 frames, so a mean over the whole film cannot move. Restricting
> the mean to the first 18 frames of each scene does not rescue it either.
>
> This is the general shape of it. **conform measures devices that are on
> screen continuously.** The loaded hold moved 0.384 to 0.452 because it
> touches every pixel of every frame. Entrance craft is invisible to it. Both
> kinds are worth shipping; only one kind is worth measuring this way, and a
> null result on an entrance device is not evidence against the device.

**typewriter** — **3 frames per character (100ms)**. Two-speed is real: rush the
sentence at 2-3 chars/frame, slow the payoff word to 1 char per 1-3 frames.
Caret blinks 30 on / 30 off.

**cursor** — bell velocity: accel 5 → 18 px/f over 8 frames, peak 20-30 for 8,
decel 18 → 1 over 21. Parks of 0.35-0.6s. **The cursor never clicks**; a click is
a state change on the target. `x-anim`: the hover halo vanishing in one frame
*is* the press.

## what happens between beats

This is the 62% we are missing.

1. **Constant drift, never reset.** 1 px/frame on the whole composition.
   `lovable-main` runs one drifting aurora across its entire back third, so
   three content swaps read as one held breath.
2. **The asymptotic tail after every move.** Nothing lands and stops.
3. **Light, not motion.** `terminal` holds a pill that never moves for 4.2s and
   is not dead for a frame: glow breathes on a **43-frame sine at ±12%**, a rim
   glint sweeps slaved to the cursor. Its rule: *if you animate light well
   enough you do not need motion.*
4. **Secondary objects on their own clocks.** A blinking caret, a spinner, a
   ticking scrubber, grain. One loop track each, running under everything.
5. **Overlap at the seam.** ~6 frames where exit and entrance coexist.
6. **And then, deliberately, nothing.** `x-anim` opens on 4.0s of pixel-diff
   zero; `design` flatlines 40 frames on purpose; `claude` drifts for its whole
   run so the final locked hold lands. **Stillness is a punctuation mark you
   earn, used once. We are using it as the default.**

## composition: which device owns which property

Contract rule 3 — one track per node per property, later silently replaces
earlier — decides whether a device library can compose at all.

- **`y` is over-subscribed by three devices**: the entrance rise, the hold
  drift, the wind-up exit. Written as three tracks, only the last survives.
  They must be **one key list** covering the node's whole life.
- **`enter` presets are not free.** They expand to keys at load: `pop` and
  `spring-in` write `opacity` + `scale`; `rise-fade` and `drop` write `opacity`
  + `y`; the slides write `x`. **A node gets an `enter` preset OR a hand-written
  life track, never both.**
- **Three channels never collide**, and are where the energy should live:
  - **the scene camera** — `cam_*` targets the scene id, so it composes with
    every node device, covers 100% of frames, and gets motion blur free
  - **the group transform** — a member's own key is applied first, then the
    group places it, so this is a genuine second channel per property
  - **reveals** — a `reveal` track and a `keys` track coexist by design

## what did not recur

One film each, and copying them makes our films look like that film: real
springs with overshoot (`crab`), invert-strobe chapter changes
(`launch-quick4`), the halftone dot engine (`blackbox`), hard-edged panel wipes
(`cuttlery`), the rim glint slaved to the cursor (`terminal`), fixed-cursor
moving-world (`x-anim`).

Two films each: multiplayer named cursors, iris wipe, gradient sweep across
glyphs, 3D perspective tilt, drift-left ticker.

**Count-up as the story** is used meaningfully by two films and **explicitly
refused by four** (`ai-1`, `ravie`, `x-anim`, `claude`). Rank the refusal above
the device.

The one thing that did not recur and should still be built: **delete and
retype**. Four films backspace on camera and `reveal: type` only runs forward.
