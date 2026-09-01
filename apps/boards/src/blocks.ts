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
  /**
   * The scene background. Blocks used to set ink unconditionally, which put
   * `#161616` on a `#0a0a0a` scene at a contrast ratio of 1.06 in a real
   * generated film. Ink follows the paper.
   */
  paper?: string
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
const advance = (text: string, fontSize: number) => {
  // Caps are materially wider than the 0.52 mixed-case mean, and launch films
  // set pill labels in caps constantly. A generated film ran "CATALOG 01" past
  // the end of its own pill because one coefficient covered both.
  const caps = text.replace(/[^A-Za-z]/g, '')
  const upper = caps ? caps.replace(/[^A-Z]/g, '').length / caps.length : 0
  return text.length * fontSize * (0.52 + 0.11 * upper)
}

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

/** true when the scene sits on dark paper, by WCAG relative luminance */
function onDark(paper?: string): boolean {
  if (!paper || !/^#[0-9a-f]{6}$/i.test(paper)) return false
  const [r, g, b] = [1, 3, 5].map(i => parseInt(paper.slice(i, i + 2), 16) / 255)
    .map(x => (x <= 0.03928 ? x / 12.92 : ((x + 0.055) / 1.055) ** 2.4))
  return 0.2126 * r + 0.7152 * g + 0.0722 * b < 0.2
}

/**
 * Ink and secondary text for a given paper, taken from the corpus rather than
 * inverted arithmetically: dark scenes set text in #ffffff / #fcfcfc with the
 * same #8a8a8a secondary tier, light scenes in #161616.
 */
const inkOn = (paper?: string) => (onDark(paper) ? '#fcfcfc' : INK)
const dimOn = (paper?: string) => (onDark(paper) ? '#c9c9c9' : GREY)

const labelFor = (role: Role) => (role === 'tint' ? INK : PAPER)


/** mix a hex toward white (k>0) or black (k<0), for building a lit ramp */
function shade(hex: string, k: number): string {
  const m = /^#([0-9a-f]{6})$/i.exec(hex)
  if (!m) return hex
  const n = parseInt(m[1], 16)
  const mix = (c: number) =>
    Math.round(k >= 0 ? c + (255 - c) * k : c * (1 + k))
      .toString(16).padStart(2, '0')
  return '#' + mix((n >> 16) & 255) + mix((n >> 8) & 255) + mix(n & 255)
}

/**
 * A lit ramp from one hue: hot core, the hue itself, then a fall to near black.
 * Four stops rather than two because a two-stop sphere reads as a flat disc
 * with a gradient on it; the third stop is what gives it a terminator.
 */
const litStops = (hue: string) => [
  { at: 0, color: shade(hue, 0.72) },
  { at: 0.38, color: hue },
  { at: 0.75, color: shade(hue, -0.62) },
  { at: 1, color: shade(hue, -0.88) },
]

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
          color: inkOn(ctx.paper), font: { family: 'inter', weight: WEIGHT.hero, size: big }, group: g,
        },
        {
          id: b, type: 'text', x: round(x), y: round(y + dy),
          text: str(o, 'sub', 'Two JSON files. One render.'),
          color: dimOn(ctx.paper), font: { family: 'inter', weight: WEIGHT.body, size: small }, group: g,
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
          color: inkOn(ctx.paper), font: { family: 'inter', weight: WEIGHT.body, size: fs }, group: g,
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
          color: dimOn(ctx.paper), font: { family: 'inter', weight: WEIGHT.body, size: small }, group: g,
        },
        {
          id: b, type: 'text', x: round(x), y: round(y + dy), text: str(o, 'value', '4.2s'),
          color: inkOn(ctx.paper), font: { family: 'inter', weight: WEIGHT.hero, size: big }, group: g,
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
          color: inkOn(ctx.paper), font: { family: 'inter', weight: WEIGHT.lead, size: fs }, group: g,
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
          color: inkOn(ctx.paper), font: { family: 'inter', weight: WEIGHT.hero, size: fs },
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
  {
    key: 'lit-field',
    name: 'Lit field',
    blurb: 'the backdrop for a dark scene: a radial pool of light and a drifting speck field.',
    slots: [
      { key: 'hue', label: 'light', kind: 'text', def: '' },
      { key: 'tier', label: 'density', kind: 'tier', def: 8 },
    ],
    make(ctx, o) {
      const { stage, x, y } = ctx
      const [W, H] = stage.size
      const hue = str(o, 'hue', '') || ctx.accent
      // density rides the tier ladder so it tunes like everything else
      const count = Math.round(40 + Number(o.tier ?? 8) * 22)
      const [g, pool, dust] = ids(stage, 'field', 3)
      return [
        container(g, x, y),
        {
          id: pool, type: 'rect', x: round(x), y: round(y), w: W, h: H,
          gradient: {
            kind: 'radial', radius: 0.85,
            stops: [
              { at: 0, color: shade(hue, -0.72) },
              { at: 0.55, color: shade(hue, -0.9) },
              { at: 1, color: '#05060a' },
            ],
          },
          group: g,
        } as Node,
        {
          id: dust, type: 'particles', x: round(x), y: round(y), w: W, h: H,
          fill: shade(hue, 0.7),
          particles: { count, size: round(3.4 * k(stage)), speed: 14, depth: 0.8, twinkle: true },
          group: g,
        } as Node,
      ]
    },
  },
  {
    key: 'lit-subject',
    name: 'Lit subject',
    blurb: 'a glowing sphere with a halo, a churned interior and a rim. the thing a dark scene is about.',
    slots: [
      { key: 'hue', label: 'colour', kind: 'text', def: '' },
      { key: 'title', label: 'name', kind: 'text', def: '' },
      { key: 'sub', label: 'under', kind: 'text', def: '' },
      { key: 'tier', label: 'size', kind: 'tier', def: 12 },
    ],
    make(ctx, o) {
      const { stage, x, y } = ctx
      const hue = str(o, 'hue', '') || ctx.accent
      // the sphere is sized off the type ladder so it sits in the same system
      const d = round(size(stage, Number(o.tier ?? 12), 12) * 2.6)
      const title = str(o, 'title', '')
      const sub = str(o, 'sub', '')
      const [g, halo, orb, rim, tt, ss] = ids(stage, 'subject', 6)
      const out: Node[] = [
        container(g, x, y),
        {
          id: halo, type: 'rect', x: round(x), y: round(y), w: round(d * 2.6), h: round(d * 2.6),
          radius: round(d * 1.3),
          gradient: { kind: 'radial', radius: 0.5, stops: [
            { at: 0, color: hue }, { at: 1, color: '#05060a' }] },
          opacity: 0.45, blur: round(d * 0.22), group: g,
        } as Node,
        {
          id: orb, type: 'rect', x: round(x), y: round(y), w: d, h: d, radius: round(d / 2),
          // the highlight sits up and to the left, which is where light comes
          // from in every one of the reference frames
          gradient: { kind: 'radial', cx: 0.36, cy: 0.28, stops: litStops(hue) },
          noise: { kind: 'turbulence', freq: 0.014, octaves: 4, opacity: 0.5, blend: 'overlay' },
          glow: { sigma: round(d * 0.28), opacity: 0.6, color: hue },
          group: g,
        } as Node,
        {
          id: rim, type: 'rect', x: round(x), y: round(y), w: d, h: d, radius: round(d / 2),
          stroke: 1.2, stroke_color: shade(hue, 0.75), opacity: 0.45, group: g,
        } as Node,
      ]
      if (title) {
        const fs = size(stage, 6, 6)
        out.push({
          id: tt, type: 'text', x: round(x), y: round(y + d * 0.78), text: title,
          color: inkOn('#05060a'),
          font: { family: 'inter', weight: WEIGHT.lead, size: fs }, group: g,
        } as Node)
        if (sub) {
          out.push({
            id: ss, type: 'text', x: round(x), y: round(y + d * 0.78 + fs * 1.05), text: sub,
            color: dimOn('#05060a'),
            font: { family: 'inter', weight: WEIGHT.body, size: round(fs * 0.5) }, group: g,
          } as Node)
        }
      }
      return out
    },
  },
  {
    key: 'glass-panel',
    name: 'Glass panel',
    blurb: 'a translucent card with a lit edge. the row you stack to make a list.',
    slots: [
      { key: 'title', label: 'label', kind: 'text', def: 'Call Router' },
      { key: 'hue', label: 'dot', kind: 'text', def: '' },
      { key: 'tier', label: 'size', kind: 'tier', def: 4 },
    ],
    make(ctx, o) {
      const { stage, x, y } = ctx
      const hue = str(o, 'hue', '') || ctx.accent
      const fs = size(stage, Number(o.tier ?? 4), 4)
      const h = round(fs * 2.6)
      const w = round(h * 6.4)
      const [g, card, dot, tt] = ids(stage, 'glass', 4)
      const padL = round(h * 0.72)
      return [
        container(g, x, y),
        {
          id: card, type: 'rect', x: round(x), y: round(y), w, h, radius: round(h / 2),
          fill: shade(hue, -0.82), opacity: 0.72,
          stroke: 1, stroke_color: shade(hue, 0.35), group: g,
        } as Node,
        {
          id: dot, type: 'rect', x: round(x - w / 2 + padL), y: round(y),
          w: round(h * 0.52), h: round(h * 0.52), radius: round(h * 0.26),
          gradient: { kind: 'radial', cx: 0.35, cy: 0.3, stops: litStops(hue) },
          glow: { sigma: round(h * 0.3), opacity: 0.7, color: hue }, group: g,
        } as Node,
        {
          id: tt, type: 'text', x: round(x - w / 2 + padL * 2.1 + fs * 2.2), y: round(y),
          text: str(o, 'title', 'Call Router'), color: inkOn('#05060a'),
          font: { family: 'inter', weight: WEIGHT.body, size: fs }, group: g,
        } as Node,
      ]
    },
  },
  {
    key: 'meter',
    name: 'Meter',
    blurb: 'a live voice or level waveform, with an optional label beside it.',
    slots: [
      { key: 'title', label: 'label', kind: 'text', def: '' },
      { key: 'hue', label: 'colour', kind: 'text', def: '' },
      { key: 'tier', label: 'size', kind: 'tier', def: 6 },
    ],
    make(ctx, o) {
      const { stage, x, y } = ctx
      const hue = str(o, 'hue', '') || ctx.accent
      const fs = size(stage, Number(o.tier ?? 6), 6)
      const w = round(fs * 9)
      const h = round(fs * 1.5)
      const title = str(o, 'title', '')
      const [g, bars, tt] = ids(stage, 'meter', 3)
      // with a label the meter sits to its left, the way a voice chip reads
      const bx = title ? round(x - w * 0.62) : round(x)
      const out: Node[] = [
        container(g, x, y),
        {
          id: bars, type: 'bars', x: bx, y: round(y), w, h, fill: hue,
          bars: { count: 52, gap: 0.5, speed: 1.3, taper: true }, group: g,
        } as Node,
      ]
      if (title) {
        out.push({
          id: tt, type: 'text', x: round(x + w * 0.34), y: round(y), text: title,
          color: inkOn(ctx.paper),
          font: { family: 'inter', weight: WEIGHT.lead, size: fs }, group: g,
        } as Node)
      }
      return out
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
