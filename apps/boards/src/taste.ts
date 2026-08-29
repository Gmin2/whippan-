/**
 * The house style, as checks rather than prose.
 *
 * These numbers were measured off 29 real launch films. They spent a long time
 * as a paragraph at the bottom of the inspector, which is the weakest possible
 * form of teaching: a rule nobody reads. Here they are functions, so the value
 * that breaks one can say so at the moment it is typed.
 *
 * Nothing here blocks anything. A band is what the references do, not a law,
 * and a deliberate 600ms hold is a legitimate choice. The job is to make sure
 * you know you made it.
 */

export interface Note {
  /** warn is outside the band; note is inside it but worth knowing */
  level: 'warn' | 'note'
  text: string
}

export const BANDS = {
  /** in-scene motion; past `slow` it stops reading as motion and starts reading as a wait */
  move: { lo: 0.14, hi: 0.28, slow: 0.35 },
  /** an entrance eases out over this long, starting about 80ms in */
  enter: { lo: 0.2, hi: 0.28, delay: 0.08 },
  /** an exit eases in and is quicker than its entrance */
  exit: { hi: 0.15 },
  /** the gap between siblings starting the same move */
  stagger: { lo: 0.04, hi: 0.08 },
  /** how far text should travel; more and the eye follows the trip, not the arrival */
  travel: 40,
}

export function checkDuration(seconds: number): Note | null {
  if (!(seconds > 0)) return null
  const { lo, hi, slow } = BANDS.move
  if (seconds > slow) {
    return { level: 'warn', text: `past ${slow * 1000 | 0}ms reads slow in-scene` }
  }
  if (seconds > hi) return { level: 'note', text: `the films sit at ${lo * 1000 | 0}-${hi * 1000 | 0}ms` }
  if (seconds < lo) return { level: 'note', text: `under ${lo * 1000 | 0}ms can read as a jump` }
  return null
}

export function checkTravel(px: number): Note | null {
  const d = Math.abs(px)
  if (d <= BANDS.travel) return null
  return { level: 'warn', text: `text travel over ${BANDS.travel}px pulls the eye off the arrival` }
}

export function checkStagger(seconds: number): Note | null {
  if (!(seconds > 0)) return null
  const { lo, hi } = BANDS.stagger
  if (seconds >= lo && seconds <= hi) return null
  return {
    level: seconds > hi * 2 || seconds < lo / 2 ? 'warn' : 'note',
    text: `siblings read as one gesture at ${lo * 1000 | 0}-${hi * 1000 | 0}ms apart`,
  }
}

/** the colours a note paints its field, kept next to the rules that raise it */
export const TONE = {
  warn: { border: '#c98a2e', text: '#8a5d12', tint: 'rgba(201,138,46,0.10)' },
  note: { border: 'rgba(0,0,0,0.14)', text: 'rgba(0,0,0,0.45)', tint: 'transparent' },
}
