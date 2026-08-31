# baseline

> **2026-08-31, after the loaded hold.** mean energy ratio **0.384 -> 0.452**,
> 26 of 28 films improved, timing unchanged (+0.199 -> +0.201), mae +0.71.
> `terminal` came off 0.00. See the bottom of this file for what it cost.

Recorded 2026-08-30, before any conformance work. This is the mark to beat;
`out/conform/` is gitignored, so the numbers live here to be compared against.

```
film              timing   lag     mae   energy  scenes worth opening
replit            -0.037   -12   14.07     0.17  s2 s3 s4 s5
lucia             -0.023     8  118.54     0.19  s_black s_credit s_reel s_lockup
lovable           -0.004   -12   58.77     0.18  s1 s2 s3 s6
ravie             -0.003     2   56.43     0.38  s1 s2 s3 s4
bevel             -0.001    12   20.49     0.21  s1 s2 s3 s4
terminal          +0.000     0    4.22     0.00  pill
base44            +0.003   -11   54.73     0.16  s1 s2 s3 s4
skale             +0.004    -7  118.63     0.27  s1 s3 s5 s6
ai-1              +0.011    -8   56.65     0.49  s1 s2 s4 s5
higgsfield        +0.029    -7   67.08     0.22  s1 s2 s3 s4
base-2            +0.032    -1    2.61     0.54  s1
lovable-main      +0.034    -8   47.19     0.26  s1 s2 s3 s4
sunflower         +0.103    -9   22.99     0.31  s
blackbox          +0.120     2   17.27     0.29  s1 s3 s4 s5
state-slim        +0.132     0   56.61     0.36  s1a s1b s1c s2b
noscroll          +0.167    -1   38.82     0.29  s2 s3 s4 s5
atlas             +0.206    -1   22.79     0.12  
rezonant          +0.217    -2   17.04     0.29  s1 s2 s3 s4
crab              +0.239    -1   15.75     0.60  s2
motion-main       +0.278     0   24.77     0.33  
radio-main        +0.405     0   33.39     0.82  
survey            +0.409     2   17.25     0.79  s2 s3
cuttlery          +0.421     0   25.67     0.47  s2 s4 s5 s6
x-anim            +0.434     4    6.51     0.99  
launch-quick4     +0.468     0   50.81     0.28  
claude            +0.616     0    3.32     0.74  s1 s3 s4 s5
chatgpt           +0.658     0   41.52     0.31  s5
design            +0.665     0   11.86     0.70  mg

mean timing +0.199   mean mae 36.63   over 28 films
```

## what it says

**We render 38% of the reference motion on average.** 21 of 28 films are under
half. That is the headline, and it is an authoring gap rather than a rendering
bug: the stills are often close (median mae 25) while the movement is not there.

Energy ratio correlates **+0.62** with timing. The films that move enough are
the films that move right, which is what you would hope and what makes the
energy column the one to work on first.

Twelve films score a timing correlation under 0.05, meaning their motion has no
measurable relationship to the reference at all. Eight clear 0.4.

`terminal` renders completely static (energy 0.00) against a moving reference.
Its only animation is a `glow_opacity` pulse that produces no measurable change.

`lucia` and `skale` sit at mae ~118, far above the median of 25. Something
systemic is wrong with those two, not a matter of degree.

## how to use it

Change something, re-run `conform/conform.py`, and compare. The absolute values
do not mean much on their own; the movement does.


## after the loaded hold (2026-08-31)

`scripts/loaded-hold.py` added a 1 px/frame drift, clamped to a zoom headroom,
to 257 scenes that had no camera of their own. Measured against this baseline:

```
mean energy ratio  0.384 -> 0.452   (+0.068)
mean timing        +0.199 -> +0.201  (+0.002)
mean mae            36.63 -> 37.34   (+0.71)
films improved on energy: 26 of 28
```

Biggest movers: `base-2` 0.54 -> 0.96, `claude` 0.74 -> 1.06, `x-anim` 0.99 ->
1.13, `terminal` **0.00 -> 0.13** (it had been rendering a still frame),
`cuttlery` 0.47 -> 0.60, `rezonant` 0.29 -> 0.41, `replit` 0.17 -> 0.29.

**What it cost.** mae rose 2% on average, worst on `motion-main` (+5.4),
`claude` (+3.4) and `replit` (+2.4). Moving the camera necessarily moves every
pixel away from where the reference has it, so some appearance error is the
price of the motion. Timing was unaffected, which is the important part: the
drift adds energy without disturbing what was already correct.

**Known overshoot.** Four films now sit at or above parity — `x-anim` 1.13,
`claude` 1.06, `base-2` 0.96 — meaning they move MORE than their reference. The
tool skips scenes that already own a camera, but not scenes that are already
moving enough by other means. Making it mass-aware is the obvious next
refinement and should be measured the same way.
