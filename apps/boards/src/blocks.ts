import type { Node, Stage } from './engine/types'
import { freshId } from './ops'

/**
 * The screen vocabulary, as things you can place.
 *
 * Every number here was measured off the 31 authored films rather than chosen;
 * BLOCKS.md records where each one comes from and how many films back it. The
 * point is that a block absorbs arithmetic the author would otherwise redo by
 * hand every time: a pill's label is 0.47 of its height, its radius is half its
 * height, and its side padding is 1.4 label-widths, so you supply a word and a
 * role and the geometry is already right.
 *
 * Blocks emit a `group` plus its members, so what lands is one selectable,
 * movable, animatable object. That is why groups had to exist first: a track
 * targeting the group animates the whole card as one.
 */

/** the type scale the corpus actually uses, at a 1920 canvas */
export const SCALE = [12, 16, 20, 22, 26, 30, 34, 40, 44, 52, 62, 84, 96, 130, 150]

/** more rigid than the size ladder: body, ui lead, buttons and headers, hero */
export const WEIGHT = { body: 400, lead: 500, strong: 600, hero: 700, mega: 800 }

/**
 * Ink is never pure black in the corpus; #000000 as a text colour appears in
 * exactly one film. Secondary text is always the mid-grey tier, never a tinted
 * grey and never the same colour at lower opacity.
 */
export const INK = '#161616'
export const GREY = '#8a8a8a'
export const PAPER = '#ffffff'
export const TINT = '#f1f1f0'

/** card radii cluster here; 18 is the most common non-zero value */
export const RADII = [0, 10, 13, 18, 20, 24, 26, 30]

export type Role = 'accent' | 'ink' | 'tint'

export interface Ctx {
  stage: Stage
  /** the film's one hue; about one text node in five carries it */
  accent: string
  /** where the block is dropped, in document units */
  x: number
  y: number
}

export interface Slot {
  key: string
  label: string
  kind: 'text' | 'lines' | 'role' | 'tier'
  /** for tier slots, the index into SCALE */
  def?: string | number | string[]
}

export interface Block {
  key: string
  name: string
  blurb: string
  slots: Slot[]
  make(ctx: Ctx, opts: Record<string, unknown>): Node[]
}

/** a block's numbers are authored at 1920 wide and scale with the canvas */
const k = (stage: Stage) => stage.size[0] / 1920
/**
 * A tier is an index into the measured scale. Anything that is not one falls
 * back rather than propagating: a live model once answered `tier: "hero"`,
 * and `Number('hero')` is NaN, which reached the renderer as a NaN font size
 * and drew nothing at all.
 */
const size = (stage: Stage, tier: number, fallback = 4) => {
  const i = Number.isFinite(tier) ? Math.round(tier) : fallback
  return Math.round(SCALE[Math.max(0, Math.min(SCALE.length - 1, i))] * k(stage))
}
const round = (n: number) => Math.round(n)

/**
 * Text advance, near enough to lay a pill out around a word.
 *
 * Only the renderer can shape text properly, so this is the same 0.52-per-em
 * approximation the inspector wraps with. A pill built from it is within a few
 * px, and it is a resizable rect afterwards.
 */
const advance = (text: string, fontSize: number) => text.length * fontSize * 0.52

const str = (o: Record<string, unknown>, key: string, fallback: string) =>
  typeof o[key] === 'string' && (o[key] as string).length ? (o[key] as string) : fallback

const lines = (o: Record<string, unknown>, key: string, fallback: string[]) => {
  const v = o[key]
  if (Array.isArray(v)) return v.map(String).filter(Boolean)
  if (typeof v === 'string' && v.trim()) return v.split('\n').map(s => s.trim()).filter(Boolean)
  return fallback
}

/** ids are unique across the whole stage, and a block hands out several at once */
function ids(stage: Stage, base: string, n: number): string[] {
  const taken = new Set(stage.scenes.flatMap(s => s.nodes.map(x => x.id)))
  const out: string[] = []
  let i = 1
  while (out.length < n) {
    const id = `${base}${i}`
    if (!taken.has(id)) { out.push(id); taken.add(id) }
    i++
  }
  return out
}

const container = (id: string, x: number, y: number): Node =>
  ({ id, type: 'group', x: round(x), y: round(y) })

const fillFor = (role: Role, accent: string) =>
  role === 'accent' ? accent : role === 'ink' ? INK : TINT

const labelFor = (role: Role) => (role === 'tint' ? INK : PAPER)

export const BLOCKS: Block[] = [
  {
    key: 'pill',
    name: 'Pill',
    blurb: 'button, chip or tag. label is 0.47 of the height, radius is half it.',
    slots: [
      { key: 'text', label: 'label', kind: 'text', def: 'Get started' },
      { key: 'role', label: 'fill', kind: 'role', def: 'accent' },
      { key: 'tier', label: 'size', kind: 'tier', def: 4 },
    ],
    make(ctx, o) {
      const { stage, x, y } = ctx
      const text = str(o, 'text', 'Get started')
      const role = str(o, 'role', 'accent') as Role
      const fs = size(stage, Number(o.tier ?? 4), 4)
      // the measured ratios: label 0.468h, side pad 1.37 label-widths, r = h/2
      const h = round(fs / 0.468)
      const w = round(advance(text, fs) + fs * 1.37 * 2)
      const [g, r, t] = ids(stage, 'pill', 3)
      return [
        container(g, x, y),
        {
          id: r, type: 'rect', x: round(x), y: round(y), w, h, radius: round(h / 2),
          fill: fillFor(role, ctx.accent), group: g,
          // pressable things carry this in 8 of the films, always this shape
          states: { pressed: { scale: 0.92 } },
        } as Node,
        {
          id: t, type: 'text', x: round(x), y: round(y), text,
          color: labelFor(role), font: { family: 'inter', weight: WEIGHT.strong, size: fs },
          group: g,
        },
      ]
    },
  },
  {
    key: 'title-sub',
    name: 'Title + sub',
    blurb: 'a line with a half-size line under it, 1.33 title-heights below.',
    slots: [
      { key: 'title', label: 'title', kind: 'text', def: 'Ship the film' },
      { key: 'sub', label: 'sub', kind: 'text', def: 'Two JSON files. One render.' },
      { key: 'tier', label: 'size', kind: 'tier', def: 9 },
    ],
    make(ctx, o) {
      const { stage, x, y } = ctx
      const big = size(stage, Number(o.tier ?? 9), 9)
      const small = round(big * 0.5)
      const dy = round(big * 1.33)
      const [g, a, b] = ids(stage, 'titlesub', 3)
      return [
        container(g, x, y + dy / 2),
        {
          id: a, type: 'text', x: round(x), y: round(y), text: str(o, 'title', 'Ship the film'),
          color: INK, font: { family: 'inter', weight: WEIGHT.hero, size: big }, group: g,
        },
        {
          id: b, type: 'text', x: round(x), y: round(y + dy),
          text: str(o, 'sub', 'Two JSON files. One render.'),
          color: GREY, font: { family: 'inter', weight: WEIGHT.body, size: small }, group: g,
        },
      ]
    },
  },
  {
    key: 'line-stack',
    name: 'Line stack',
    blurb: 'lines at one size and constant leading. 1.27 display, 1.55 ui copy.',
    slots: [
      { key: 'lines', label: 'lines', kind: 'lines', def: ['First line', 'Second line', 'Third line'] },
      { key: 'tier', label: 'size', kind: 'tier', def: 4 },
    ],
    make(ctx, o) {
      const { stage, x, y } = ctx
      const fs = size(stage, Number(o.tier ?? 4), 4)
      const rows = lines(o, 'lines', ['First line', 'Second line', 'Third line'])
      // leading tightens as type grows: display sets closer than ui copy does
      const lead = fs >= size(stage, 9) ? 1.27 : fs >= size(stage, 6) ? 1.47 : 1.55
      const dy = round(fs * lead)
      const top = y - (dy * (rows.length - 1)) / 2
      const [g, ...rest] = ids(stage, 'stack', rows.length + 1)
      return [
        container(g, x, y),
        ...rows.map((text, i) => ({
          id: rest[i], type: 'text', x: round(x), y: round(top + i * dy), text,
          color: INK, font: { family: 'inter', weight: WEIGHT.body, size: fs }, group: g,
        } as Node)),
      ]
    },
  },
  {
    key: 'label-value',
    name: 'Label + value',
    blurb: 'a small label with a value twice its size under it.',
    slots: [
      { key: 'label', label: 'label', kind: 'text', def: 'Rendered' },
      { key: 'value', label: 'value', kind: 'text', def: '4.2s' },
      { key: 'tier', label: 'size', kind: 'tier', def: 1 },
    ],
    make(ctx, o) {
      const { stage, x, y } = ctx
      const small = size(stage, Number(o.tier ?? 1), 1)
      const big = round(small * 1.94)
      const dy = round(small * 2)
      const [g, a, b] = ids(stage, 'stat', 3)
      return [
        container(g, x, y + dy / 2),
        {
          id: a, type: 'text', x: round(x), y: round(y), text: str(o, 'label', 'Rendered'),
          color: GREY, font: { family: 'inter', weight: WEIGHT.body, size: small }, group: g,
        },
        {
          id: b, type: 'text', x: round(x), y: round(y + dy), text: str(o, 'value', '4.2s'),
          color: INK, font: { family: 'inter', weight: WEIGHT.hero, size: big }, group: g,
        },
      ]
    },
  },
  {
    key: 'icon-tile',
    name: 'Icon tile',
    blurb: 'the app-icon squircle: square, radius exactly a quarter of the side.',
    slots: [
      { key: 'glyph', label: 'glyph', kind: 'text', def: 'a' },
      { key: 'role', label: 'fill', kind: 'role', def: 'ink' },
      { key: 'tier', label: 'size', kind: 'tier', def: 11 },
    ],
    make(ctx, o) {
      const { stage, x, y } = ctx
      const s = size(stage, Number(o.tier ?? 11), 11)
      const role = str(o, 'role', 'ink') as Role
      const [g, r, t] = ids(stage, 'tile', 3)
      return [
        container(g, x, y),
        {
          id: r, type: 'rect', x: round(x), y: round(y), w: s, h: s, radius: round(s / 4),
          fill: fillFor(role, ctx.accent), group: g,
        },
        {
          id: t, type: 'text', x: round(x), y: round(y), text: str(o, 'glyph', 'a'),
          color: labelFor(role),
          // the inner mark occupies the middle 40-50% of the tile
          font: { family: 'inter', weight: WEIGHT.strong, size: round(s * 0.45) }, group: g,
        },
      ]
    },
  },
  {
    key: 'glyph-label',
    name: 'Glyph + label',
    blurb: 'a dot or mark one em to the left of a label, sharing its baseline.',
    slots: [
      { key: 'text', label: 'label', kind: 'text', def: 'Ready' },
      { key: 'role', label: 'dot', kind: 'role', def: 'accent' },
      { key: 'tier', label: 'size', kind: 'tier', def: 4 },
    ],
    make(ctx, o) {
      const { stage, x, y } = ctx
      const fs = size(stage, Number(o.tier ?? 4), 4)
      const text = str(o, 'text', 'Ready')
      const role = str(o, 'role', 'accent') as Role
      // dot diameter equals the label size; the gap is 1.1 em
      const gap = round(fs * 1.1)
      const wide = advance(text, fs)
      const [g, d, t] = ids(stage, 'mark', 3)
      const dotX = x - wide / 2 - gap
      return [
        container(g, (dotX + x + wide / 2) / 2, y),
        {
          id: d, type: 'rect', x: round(dotX), y: round(y), w: fs, h: fs, radius: round(fs / 2),
          fill: fillFor(role, ctx.accent), group: g,
        },
        {
          id: t, type: 'text', x: round(x + fs / 2), y: round(y), text,
          color: INK, font: { family: 'inter', weight: WEIGHT.lead, size: fs }, group: g,
        },
      ]
    },
  },
  {
    key: 'swap-slot',
    name: 'Swap slot',
    blurb: 'stacked alternates at one point. counters and word swaps are authored this way, never as one animated node.',
    slots: [
      { key: 'lines', label: 'alternates', kind: 'lines', def: ['imagine', 'building', 'anything'] },
      { key: 'tier', label: 'size', kind: 'tier', def: 11 },
    ],
    make(ctx, o) {
      const { stage, x, y } = ctx
      const fs = size(stage, Number(o.tier ?? 11), 11)
      const words = lines(o, 'lines', ['imagine', 'building', 'anything'])
      const [g, ...rest] = ids(stage, 'swap', words.length + 1)
      return [
        container(g, x, y),
        ...words.map((text, i) => ({
          id: rest[i], type: 'text', x: round(x), y: round(y), text,
          color: INK, font: { family: 'inter', weight: WEIGHT.hero, size: fs },
          // only the first is up; the overlay flips the rest
          keys: i === 0 ? undefined : { opacity: [{ t: 0, v: 0 }] },
          group: g,
        } as Node)),
      ]
    },
  },
  {
    key: 'surface',
    name: 'Surface',
    blurb: 'an app window or product card. 0.57 x 0.60 of the canvas, centred.',
    slots: [
      { key: 'title', label: 'brand', kind: 'text', def: 'whippan' },
      { key: 'role', label: 'chrome', kind: 'role', def: 'tint' },
    ],
    make(ctx, o) {
      const { stage, x, y } = ctx
      const [W, H] = stage.size
      const w = round(W * 0.57)
      const h = round(H * 0.6)
      const r = round(18 * k(stage))
      const fs = size(stage, 2)
      const [g, card, bar, brand] = ids(stage, 'surface', 4)
      const role = str(o, 'role', 'tint') as Role
      // the top bar takes the first 15% of the surface, brand lockup at the left
      const barH = round(h * 0.15)
      return [
        container(g, x, y),
        { id: card, type: 'rect', x: round(x), y: round(y), w, h, radius: r, fill: PAPER, group: g },
        {
          id: bar, type: 'rect', x: round(x), y: round(y - h / 2 + barH / 2), w, h: barH,
          radius: round(r * 0.6), fill: fillFor(role, ctx.accent), group: g,
        },
        {
          id: brand, type: 'text', x: round(x - w / 2 + fs * 4), y: round(y - h / 2 + barH / 2),
          text: str(o, 'title', 'whippan'), color: labelFor(role),
          font: { family: 'inter', weight: WEIGHT.strong, size: fs }, group: g,
        },
      ]
    },
  },
]

export const blockByKey = (key: string) => BLOCKS.find(b => b.key === key)

/** the film's hue, taken from what it already uses rather than guessed */
export function filmAccent(stage: Stage): string {
  const tally = new Map<string, number>()
  for (const sc of stage.scenes) {
    for (const n of sc.nodes) {
      for (const c of [n.fill, n.color]) {
        if (!c || !/^#[0-9a-f]{6}$/i.test(c)) continue
        const r = parseInt(c.slice(1, 3), 16), g = parseInt(c.slice(3, 5), 16), b = parseInt(c.slice(5, 7), 16)
        const mx = Math.max(r, g, b), mn = Math.min(r, g, b)
        // achromatic marks are two thirds of the corpus; the accent is what is left
        if (mx === 0 || (mx - mn) / mx < 0.35) continue
        tally.set(c.toLowerCase(), (tally.get(c.toLowerCase()) ?? 0) + 1)
      }
    }
  }
  return [...tally.entries()].sort((a, b) => b[1] - a[1])[0]?.[0] ?? '#ff5c1a'
}

/** freshId is re-exported so callers do not need two imports to place a block */
export { freshId }
