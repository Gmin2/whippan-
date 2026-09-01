/**
 * How close a screen sits to the corpus, measured.
 *
 * `fit.ts` catches a screen that is broken: text off the canvas, a stack taller
 * than the band. It cannot catch one that is merely bland, which is the way a
 * generated screen actually fails. These checks are the other half — every
 * target below is a number BLOCKS.md measured across 332 scenes and 6298 nodes,
 * not a convention borrowed from web design.
 *
 * Scores are reported as a vector, never blended into one percentage. A mean
 * lets a screen with perfect colour and no structure sit level with a mediocre
 * one, which is the same error conform's film-level energy mean was making.
 */
import { SCALE } from './blocks'
import type { Node } from './engine/types'

export interface Check {
  key: string
  /** 0 to 1, where 1 sits inside the corpus */
  score: number
  detail: string
}

/** the corpus, as targets */
export const CORPUS = {
  centreShare: 0.127,     // of all nodes, exactly on x = W/2
  achromatic: 0.67,       // of colour marks
  marginW: 0.20,          // median
  marginH: 0.24,
  radii: [0, 10, 13, 18, 20, 24, 26, 30],
  accentText: 0.2,        // about one text node in five
}

const hex = (c?: string) => (typeof c === 'string' && /^#[0-9a-f]{6}$/i.test(c) ? c.toLowerCase() : null)

function rgb(c: string) {
  return [parseInt(c.slice(1, 3), 16), parseInt(c.slice(3, 5), 16), parseInt(c.slice(5, 7), 16)]
}

/** achromatic when saturation is under the corpus line of 0.35 */
function chroma(c: string): number {
  const [r, g, b] = rgb(c)
  const mx = Math.max(r, g, b), mn = Math.min(r, g, b)
  return mx === 0 ? 0 : (mx - mn) / mx
}

/** which 20-degree bucket a colour's hue falls in */
function bucket(c: string): number {
  const [r, g, b] = rgb(c).map(v => v / 255)
  const mx = Math.max(r, g, b), mn = Math.min(r, g, b), d = mx - mn
  if (!d) return -1
  const h = mx === r ? ((g - b) / d + 6) % 6 : mx === g ? (b - r) / d + 2 : (r - g) / d + 4
  return Math.floor((h * 60) / 20)
}

/** 1 when v sits at target, falling off linearly over tol */
const near = (v: number, target: number, tol: number) =>
  Math.max(0, 1 - Math.abs(v - target) / tol)

const median = (a: number[]) => {
  const s = [...a].sort((x, y) => x - y)
  return s[Math.floor(s.length / 2)]
}

/** WCAG relative luminance, so contrast is measured not eyeballed */
function luminance(c: string): number {
  const [r, g, b] = rgb(c).map(v => {
    const x = v / 255
    return x <= 0.03928 ? x / 12.92 : ((x + 0.055) / 1.055) ** 2.4
  })
  return 0.2126 * r + 0.7152 * g + 0.0722 * b
}

const contrastRatio = (a: string, b: string) => {
  const [x, y] = [luminance(a), luminance(b)].sort((m, n) => n - m)
  return (x + 0.05) / (y + 0.05)
}

export function scoreScreen(nodes: Node[], size: [number, number], bg?: string): Check[] {
  const [W, H] = size
  const kk = W / 1920
  const out: Check[] = []
  const texts = nodes.filter(n => n.type === 'text')
  const rects = nodes.filter(n => n.type === 'rect')
  const marks = nodes.filter(n => n.type !== 'group')
  // block origins, when the screen was composed from the library
  const groups = nodes.filter(n => n.type === 'group')

  // The strongest positional fact in the corpus, but it is a fact about the
  // corpus, not about every scene: a screenshot beat legitimately centres
  // nothing. What a scene must not do is align to nothing at all.
  //
  // Measured over BLOCKS, not over every mark. A pill's own rect and label
  // share an x by construction, so counting marks scored a deliberately
  // scattered layout at a perfect 1.00. What matters is whether the blocks
  // line up with each other.
  // A hand-authored film is a flat node list, so "which marks form one unit"
  // is unanswerable and the bar has to be the corpus share rather than the
  // half-of-blocks a composed screen should manage.
  const composed = groups.length > 0
  const units = composed ? groups : marks
  const bar = composed ? 0.5 : CORPUS.centreShare
  // a column or a row: three stat blocks side by side share a y, not an x,
  // and the corpus is full of both
  const sharedOn = (axis: 'x' | 'y') => {
    const m = new Map<number, number>()
    for (const n of units) {
      const v = Math.round(n[axis] ?? 0)
      m.set(v, (m.get(v) ?? 0) + 1)
    }
    // one unit is not an alignment, however small the scene
    return Math.max(0, ...[...m.values()].filter(v => v > 1))
  }
  const aligned = Math.max(sharedOn('x'), sharedOn('y'))
  const axis = sharedOn('y') > sharedOn('x') ? 'y' : 'x'
  const share = units.length ? aligned / units.length : 0
  const centred = units.filter(n => Math.abs((n.x ?? 0) - W / 2) < 1).length
  out.push({
    key: 'alignment',
    // a lone block cannot align with anything, so it is not penalised
    score: units.length < 2 ? 1 : Math.min(1, share / bar),
    detail: `${aligned} of ${units.length} ${groups.length ? 'blocks' : 'marks'} share ${
      axis === 'y' ? 'a y' : 'an x'}` + (centred ? `, ${centred} on the centre line` : ''),
  })

  // Text over a panel is the corpus pattern; text from one block landing on
  // text from another never is. This is the check the library cannot satisfy
  // for us, because it is a property of where the model put things.
  //
  // Only counted BETWEEN blocks. A `swap slot` stacks its alternates at one
  // point on purpose (70 instances across 25 films) and a block that hides
  // its own members with an opacity key is doing the same, so neither is a
  // collision.
  const boxes = texts
    .filter(n => (n.keys?.opacity?.[0]?.v ?? 1) > 0)
    .map(n => {
      const fs = n.font?.size ?? 24
      return {
        x: n.x ?? 0, y: n.y ?? 0,
        w: (n.text?.length ?? 6) * fs * 0.52, h: fs * 1.2,
        group: n.group ?? n.id,
      }
    })
  let collisions = 0
  for (let i = 0; i < boxes.length; i++) {
    for (let j = i + 1; j < boxes.length; j++) {
      const a = boxes[i], b = boxes[j]
      if (a.group === b.group) continue
      if (Math.abs(a.x - b.x) < (a.w + b.w) / 2 && Math.abs(a.y - b.y) < (a.h + b.h) / 2) {
        collisions++
      }
    }
  }
  // Text on a background it cannot be read against is the one defect that
  // makes a frame worthless, and nothing else here catches it: a generated
  // film put its own wordmark in #55586b on #000000, a ratio of 1.9.
  /**
   * What a given text node actually sits on.
   *
   * The scene background is not it. A film sets "your next adventure" in
   * #ffffff on a page of #eeebe4, and it reads perfectly because the words are
   * on a dark card. Comparing every node to the page flagged a fifth of the
   * corpus as unreadable when almost none of it is. So: the topmost opaque
   * rect that contains the node, else a full-bleed rect, else the scene bg.
   */
  const behind = (n: Node): string | null => {
    const under = nodes.filter(r =>
      r.type === 'rect' && hex(r.fill) && (r.opacity ?? 1) > 0.9 &&
      Math.abs((n.x ?? 0) - (r.x ?? 0)) <= (r.w ?? 0) / 2 &&
      Math.abs((n.y ?? 0) - (r.y ?? 0)) <= (r.h ?? 0) / 2)
    // last drawn wins, and the smallest of those is the nearest surface
    if (under.length) {
      const top = under.reduce((a, r) =>
        (r.w ?? 0) * (r.h ?? 0) <= (a.w ?? 0) * (a.h ?? 0) ? r : a)
      return hex(top.fill)
    }
    return hex(bg)
  }

  if (hex(bg)) {
    const paper = hex(bg)!
    // Weighted by ink area, not by node count. A film put its 84px wordmark in
    // #161616 on #0a0a0a, a ratio of 1.06, and a per-node count scored that
    // 0.75 because three small readable labels outvoted it. The headline IS
    // the frame.
    const BAR = Number(globalThis.process?.env?.WHIPPAN_CONTRAST_BAR) || 3
    const lit = texts.filter(n => (n.keys?.opacity?.[0]?.v ?? n.opacity ?? 1) > 0.5)
    const dark = lit.filter(n => {
      const c = hex(n.color)
      const under = behind(n) ?? paper
      return c && contrastRatio(c, under) < BAR
    })
    // and the largest type on the frame is the message: if THAT cannot be
    // read the frame is dead however much small readable copy surrounds it.
    // A 39-character subtitle out-areas a six-letter wordmark twice its size,
    // which let an unreadable "Solder" through at 0.64.
    const biggest = Math.max(0, ...lit.map(n => n.font?.size ?? 0))
    const headlineLost = dark.some(n => (n.font?.size ?? 0) >= biggest)
    // Only the largest type is scored. Muted low-contrast text is a real
    // corpus pattern — four films keep persistent chrome at 55-70% toward the
    // background — so penalising every dim node flagged 19% of the corpus even
    // at a 2.5 bar. What is never deliberate is a headline you cannot read.
    out.push({
      key: 'contrast',
      score: headlineLost ? 0 : 1,
      detail: headlineLost
        ? `the largest type (${biggest}px) is under ${BAR}:1 on ${paper}`
        : dark.length
          ? `readable headline, ${dark.length} dim nodes below it`
          : `all text reads on ${paper}`,
    })
  }

  // A caption laid over a product screenshot competes with whatever the shot
  // already says. The corpus puts the caption in the margin instead.
  const shots = nodes.filter(n => n.type === 'image' && (n.w ?? 0) > W * 0.4)
  if (shots.length) {
    const over = texts.filter(t => shots.some(im =>
      Math.abs((t.x ?? 0) - (im.x ?? 0)) < (im.w ?? 0) / 2 &&
      Math.abs((t.y ?? 0) - (im.y ?? 0)) < (im.h ?? 0) / 2))
    out.push({
      key: 'caption clear',
      score: !texts.length ? 1 : Math.max(0, 1 - over.length / texts.length),
      detail: over.length ? `${over.length} text nodes sit over the product shot`
                          : 'captions clear of the shot',
    })
  }

  out.push({
    key: 'collision',
    // two blocks' text on top of each other is never right, so this falls
    // away fast rather than averaging out over a busy screen. On a flat
    // document there are no blocks to be between, so it cannot be judged.
    score: !composed ? 1 : collisions === 0 ? 1 : collisions === 1 ? 0.4 : 0,
    detail: !composed ? 'not composed from blocks, so not judged'
          : collisions ? `${collisions} text pairs collide across blocks`
                       : 'no text collides across blocks',
  })

  // sizes cluster hard rather than spreading smoothly
  const sizes = texts.map(n => n.font?.size).filter((s): s is number => !!s)
  const onScale = sizes.filter(s =>
    SCALE.some(v => Math.abs(s - v * kk) <= Math.max(1, v * kk * 0.06))).length
  out.push({
    key: 'type scale',
    score: sizes.length ? onScale / sizes.length : 1,
    detail: `${onScale} of ${sizes.length} sizes on the ladder`,
  })

  // 67% of colour marks are achromatic
  const cols = marks.flatMap(n => [hex(n.fill), hex(n.color)]).filter((c): c is string => !!c)
  const grey = cols.filter(c => chroma(c) < 0.35).length
  const got = cols.length ? grey / cols.length : 1
  out.push({
    key: 'achromatic',
    // more grey than the corpus is restraint, not a fault
    score: got >= CORPUS.achromatic ? 1 : near(got, CORPUS.achromatic, CORPUS.achromatic),
    detail: `${(got * 100).toFixed(0)}% achromatic, corpus 67%`,
  })

  // Each film CONCENTRATES its chromatic marks in one 20-degree bucket. That
  // is a share, not a count: a second hue used once is a highlight, and two
  // near-identical oranges can straddle a bucket edge without being two hues.
  const chromatic = cols.filter(c => chroma(c) >= 0.35)
  const tally = new Map<number, number>()
  for (const c of chromatic) tally.set(bucket(c), (tally.get(bucket(c)) ?? 0) + 1)
  const top = Math.max(0, ...tally.values())
  const conc = chromatic.length ? top / chromatic.length : 1
  out.push({
    key: 'one hue',
    score: conc,
    detail: chromatic.length
      ? `${(conc * 100).toFixed(0)}% of colour in one hue bucket`
      : 'achromatic throughout',
  })

  // ink is never pure black: it appears as a text colour in exactly one film
  const pure = texts.filter(n => hex(n.color) === '#000000').length
  out.push({
    key: 'ink',
    score: pure ? 0 : 1,
    detail: pure ? `${pure} text nodes at pure #000000` : 'ink is off-black',
  })

  // radius is the real grid: a pill, or one of the eight card values
  const radii = rects.filter(n => (n.w ?? 0) > 0 && (n.h ?? 0) > 0)
  const onGrid = radii.filter(n => {
    const r = n.radius ?? 0
    const short = Math.min(n.w ?? 0, n.h ?? 0)
    if (r >= short * 0.45) return true                     // pill or circle
    return CORPUS.radii.some(v => Math.abs(r - v * kk) <= Math.max(1, kk * 2))
  }).length
  out.push({
    key: 'radius',
    score: radii.length ? onGrid / radii.length : 1,
    detail: `${onGrid} of ${radii.length} rects on the radius grid`,
  })

  // Posters with a UI in the middle, not dense pages. Full-bleed rects are
  // backgrounds, veils and letterbox bands: they are supposed to touch the
  // edge, so measuring the closest mark would score every scene by its paper.
  const content = marks.filter(n => (n.w ?? 0) < W * 0.9)
  const insets = content.map(n => Math.min(
    (n.x ?? 0) - (n.w ?? 0) / 2, W - ((n.x ?? 0) + (n.w ?? 0) / 2)))
  const inset = insets.length ? median(insets) : W * CORPUS.marginW
  out.push({
    key: 'margin',
    score: Math.min(1, Math.max(0, inset) / (W * CORPUS.marginW)),
    detail: `median mark ${(inset / W).toFixed(2)}W in, corpus 0.20W`,
  })

  return out
}

/** how many checks a screen is actually failing, which a mean would hide */
export const failing = (checks: Check[], bar = 0.6) => checks.filter(c => c.score < bar).length
