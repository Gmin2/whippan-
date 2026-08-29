import type { Artboard } from './doc'

/**
 * The wall is columns, not a row. One column per scene, a script card at the
 * top carrying the scene's note, then frames sampled down through the scene so
 * you can read the entrance, the settled state and the exit at a glance. That
 * is what a storyboard is for: the horizontal axis is the film, the vertical
 * axis is time inside a beat.
 *
 * All measurements are in document pixels, so the camera scales them.
 */
export const GAP_X = 260
export const GAP_Y = 210
/** height reserved above every column for its script card */
export const HEADER = 420
export const HEADER_GAP = 90

/** how many frames a scene earns: short beats get two, long ones up to five */
export function sampleCount(dur: number): number {
  return Math.max(2, Math.min(5, Math.round(dur / 0.9)))
}

/**
 * Absolute film times to sample a scene at. Pulled in from the very edges so
 * the first frame catches the entrance mid-flight rather than an empty stage,
 * and the last catches the exit before it has finished leaving.
 */
export function sampleTimes(b: Artboard): number[] {
  const n = sampleCount(b.dur)
  return Array.from({ length: n }, (_, k) => {
    const f = n === 1 ? 0.5 : 0.1 + (0.8 * k) / (n - 1)
    return b.start + b.dur * f
  })
}

export const columnX = (i: number, dw: number) => i * (dw + GAP_X)
export const rowY = (k: number, dh: number) => HEADER + HEADER_GAP + k * (dh + GAP_Y)

/** total wall size in document pixels, for fitting the camera */
export function wallSize(
  boards: Artboard[], dw: number, dh: number, mode: 'design' | 'motion' = 'design',
) {
  // motion mode is one frame per column, so the wall is a single row
  const rows = mode === 'motion'
    ? 1
    : Math.max(1, ...boards.map(b => sampleCount(b.dur)))
  return {
    w: boards.length * dw + Math.max(0, boards.length - 1) * GAP_X,
    h: HEADER + HEADER_GAP + rows * dh + (rows - 1) * GAP_Y,
  }
}

/**
 * Script card geometry.
 *
 * The card's copy is drawn in screen pixels so it stays legible at any zoom,
 * which means the card's height is a screen measurement too, not a scaled world
 * one. Both the overlay that draws the cards and the camera that has to leave
 * room for them need the same answer, so the rule lives here.
 */
export const CARD = {
  fs: 12,
  lh: 16,
  /** the number-and-duration line above the copy */
  title: 18,
  /** a long note must not build a tower over the wall */
  maxLines: 5,
  /** no room for the copy: the card becomes a label strip */
  slim: 17,
  /** narrower than this and even the label is noise */
  minW: 34,
  /** the copy needs at least this much width to be worth wrapping */
  textW: 104,
  /**
   * The film title and its subtitle sit above the tallest card, on baselines
   * 34 and 14 above it. 20px type needs its ascender clearing the top edge too,
   * so this is that stack plus a margin.
   */
  titleRoom: 70,
}

export const cardPad = (w: number) => Math.min(14, Math.max(6, w * 0.04))

/** naive word wrap, shared so the height and the drawing never disagree */
export function wrapNote(text: string, cols: number): string[] {
  if (cols < 8) return []
  const out: string[] = []
  let line = ''
  for (const word of text.split(/\s+/)) {
    if ((line + ' ' + word).trim().length > cols) { out.push(line.trim()); line = word }
    else line += ' ' + word
  }
  if (line.trim()) out.push(line.trim())
  return out
}

/** a card's height in screen pixels, and the lines it will actually show */
export function cardBox(note: string, w: number, motion: boolean) {
  if (motion) return { h: 22, lines: [] as string[], pad: 8 }
  if (w < CARD.minW) return { h: 0, lines: [] as string[], pad: 0 }
  const pad = cardPad(w)
  const cols = Math.floor((w - pad * 2) / (CARD.fs * 0.52))
  const lines = w > CARD.textW ? wrapNote(note, cols).slice(0, CARD.maxLines) : []
  if (!lines.length) return { h: CARD.slim, lines, pad }
  return { h: pad + CARD.title + lines.length * CARD.lh + pad - 4, lines, pad }
}
