import type { Node } from './engine/types'

/**
 * The fit budget from AUTHORING §6, as arithmetic.
 *
 * These are the checks that can be done before rendering, and they are the ones
 * a generated screen fails: text wider than the canvas, a stack taller than the
 * content band, a headline set at a size no film uses. Pure functions so the
 * prompt path can run them on a proposal before it is ever shown.
 */

export interface Fit {
  level: 'warn' | 'note'
  node: string
  text: string
}

/** inter advances about 0.5 em, mono about 0.6 */
export const lineWidth = (text: string, size: number, family?: string) =>
  text.length * size * (family === 'mono' ? 0.6 : 0.5)

/** leave at least 8% each side, per the budget */
const MARGIN = 0.08
/** stacked content belongs in the middle ~70% */
const BAND = 0.7

/** the headline bands, given at 1920x1080 and scaled linearly */
const TIERS: [string, number, number][] = [
  ['hero', 90, 130],
  ['section', 56, 90],
  ['ui copy', 22, 30],
  ['micro label', 14, 18],
]

export function checkFit(nodes: Node[], size: [number, number]): Fit[] {
  const [W, H] = size
  const k = W / 1920
  const out: Fit[] = []

  const usable = W * (1 - MARGIN * 2)
  for (const n of nodes) {
    if (n.type !== 'text' || !n.text) continue
    const fs = n.font?.size ?? 48
    const w = lineWidth(n.text, fs, n.font?.family)
    if (w > usable) {
      out.push({
        level: 'warn', node: n.id,
        text: `"${n.text.slice(0, 24)}" is ${Math.round(w)}px wide; ${Math.round(usable)}px fits inside the margins`,
      })
    }
    // a size between the bands is not wrong, but a size far outside them all is
    const norm = fs / k
    if (norm > 0 && norm < TIERS[3][1] * 0.7) {
      out.push({ level: 'note', node: n.id, text: `${Math.round(norm)}px is below the micro-label band` })
    } else if (norm > TIERS[0][2] * 1.6) {
      out.push({ level: 'note', node: n.id, text: `${Math.round(norm)}px is above anything in the corpus` })
    }
  }

  // vertical: how much of the content band the stacked text actually claims
  const texts = nodes.filter(n => n.type === 'text' && n.text)
  if (texts.length) {
    const top = Math.min(...texts.map(n => n.y ?? 0))
    const bot = Math.max(...texts.map(n => n.y ?? 0))
    const claimed = bot - top + (texts[0].font?.size ?? 48) * 1.35
    if (claimed > H * BAND) {
      out.push({
        level: 'warn', node: '',
        text: `the copy spans ${Math.round(claimed)}px; the content band is ${Math.round(H * BAND)}px`,
      })
    }
  }

  // anything placed outside the canvas is a straightforward mistake
  for (const n of nodes) {
    const x = n.x ?? 0
    const y = n.y ?? 0
    if (x < 0 || x > W || y < 0 || y > H) {
      out.push({ level: 'warn', node: n.id, text: `sits outside the canvas at ${Math.round(x)},${Math.round(y)}` })
    }
  }

  return out
}

/** one thought per scene: three sentences of body copy is two scenes */
export function checkDensity(nodes: Node[]): Fit | null {
  const sentences = nodes
    .filter(n => n.type === 'text' && n.text)
    .reduce((a, n) => a + (n.text!.match(/[.!?](\s|$)/g)?.length ?? 0), 0)
  return sentences > 2
    ? { level: 'note', node: '', text: 'three sentences is two scenes; one thought per scene' }
    : null
}
