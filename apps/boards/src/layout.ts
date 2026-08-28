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
export function wallSize(boards: Artboard[], dw: number, dh: number) {
  const rows = Math.max(1, ...boards.map(b => sampleCount(b.dur)))
  return {
    w: boards.length * dw + Math.max(0, boards.length - 1) * GAP_X,
    h: HEADER + HEADER_GAP + rows * dh + (rows - 1) * GAP_Y,
  }
}
