import type { Transition } from './engine/types'

/**
 * The eleven ways one scene can become the next, with what each is actually
 * for. The blurbs are the measured notes from the reference teardowns, not
 * decoration: "cuts punctuate, morphs narrate" is the rule the whole library
 * follows, and a picker that only lists names would lose it.
 */
export interface Kind {
  key: string
  name: string
  blurb: string
  /** push, whip and wipe travel; dip carries a colour instead */
  needsDir?: boolean
  needsColor?: boolean
}

export const KINDS: Kind[] = [
  { key: 'cut', name: 'Cut', blurb: 'hard swap. chapter breaks, beat hits.' },
  { key: 'fade', name: 'Fade', blurb: 'crossfade with a background mix. gentle chapter turns.' },
  { key: 'push', name: 'Push', blurb: 'the whole scene slides in. spatial sequences.', needsDir: true },
  { key: 'whip', name: 'Whip', blurb: 'a fast push with velocity blur. energy spikes.', needsDir: true },
  { key: 'dip', name: 'Dip', blurb: 'dip through a colour. act boundaries.', needsColor: true },
  { key: 'zoom', name: 'Zoom', blurb: 'zoom through into the next scene. diving into detail.' },
  { key: 'wipe', name: 'Wipe', blurb: 'a clipped reveal along a direction. editorial, data stories.', needsDir: true },
  { key: 'rise', name: 'Rise', blurb: 'phase-choreographed: outgoing leaves, incoming arrives after.' },
  { key: 'dissolve', name: 'Dissolve', blurb: 'the soft family. outgoing eases out at ~44%.' },
  { key: 'settle', name: 'Settle', blurb: 'the soft family, arriving from ~22% with a long tail.' },
  { key: 'bloom', name: 'Bloom', blurb: 'the soft family, opening out of light.' },
]

export const DIRS = ['left', 'right', 'up', 'down'] as const

export const EASES = ['outCubic', 'inCubic', 'inOutCubic', 'spring'] as const

export const kindOf = (t?: Transition): string => t?.kind ?? 'cut'
export const findKind = (key: string) => KINDS.find(k => k.key === key)

/**
 * Switch kind while keeping what is orthogonal to it. Magic move can ride any
 * transition, and a duration you have already tuned should survive picking a
 * different kind — only the direction is genuinely kind-specific.
 */
export function withKind(key: string, prev?: Transition): Transition {
  const k = findKind(key)
  const t: Transition = { kind: key, dur: prev?.dur ?? 0.4 }
  if (prev?.ease !== undefined) t.ease = prev.ease
  if (prev?.morph) {
    t.morph = true
    if (prev.morph_dur !== undefined) t.morph_dur = prev.morph_dur
    if (prev.morph_ease !== undefined) t.morph_ease = prev.morph_ease
  }
  if (k?.needsDir) t.dir = prev?.dir && !prev.dir.startsWith('#') ? prev.dir : 'left'
  if (k?.needsColor) t.dir = prev?.dir?.startsWith('#') ? prev.dir : '#000000'
  return t
}

/** a cut with no duration is the document's default, so it needs no entry */
export const isDefault = (t?: Transition) =>
  !t || (t.kind === 'cut' && !t.morph && t.dur === undefined)

/** a one-glyph mark so a seam reads at a glance without hovering */
export function glyph(t?: Transition): string {
  if (t?.morph) return '◇'
  switch (kindOf(t)) {
    case 'fade': return '◐'
    case 'push': return '⇥'
    case 'whip': return '⇛'
    case 'dip': return '▼'
    case 'zoom': return '⊙'
    case 'wipe': return '▤'
    case 'rise': return '↑'
    case 'dissolve': return '∴'
    case 'settle': return '↓'
    case 'bloom': return '✳'
    default: return '│'
  }
}
