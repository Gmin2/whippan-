import type { Scene, Stage, Track } from './engine/types'

/**
 * The motion vocabulary, as things you can apply.
 *
 * The mirror of `blocks.ts`: a block takes a slot and emits nodes, a device
 * takes a target and emits tracks. Every number here was measured off the 29
 * teardowns in `analysis/` and is recorded in `MOTION.md`.
 *
 * The important design rule, from the contract's silent-failure list: one track
 * per node per property, and a later track REPLACES an earlier one. Devices
 * cannot simply be appended the way blocks can, because motion is not additive
 * the way geometry is. Two devices both keying `y` on one node means one of
 * them vanishes with no error.
 *
 * So each device declares the properties it OWNS, and `applyDevices` refuses to
 * let two of them claim the same one. The three channels that never collide —
 * the scene camera, the group transform, and reveals — are where the cheap
 * energy lives.
 */

export interface Device {
  key: string
  name: string
  blurb: string
  /** how many of the 29 reference films use it */
  films: number
  /** the properties this device writes, so a collision can be refused */
  owns: string[]
}

/** measured: 24 of 29 films drift 0.3-3 px/frame through every hold, median 1 */
export const PX_PER_FRAME = 1
/** a little zoom so the drift never slides the canvas edge into shot */
export const HEADROOM = 0.08

export const DEVICES: Device[] = [
  {
    key: 'loaded-hold',
    name: 'Loaded hold',
    blurb: 'the camera never fully stops. a constant drift through every hold.',
    films: 24,
    owns: ['cam_x', 'cam_zoom'],
  },
]

/**
 * Give a scene a loaded hold.
 *
 * Measured effect across the 28 reproductions: mean energy ratio 0.384 to
 * 0.452, 26 of 28 films improved, timing unchanged. `terminal` came off 0.00,
 * having rendered a still frame against a moving reference.
 *
 * Returns null when the scene already carries a camera, or already moves
 * enough on its own — four films overshot their reference when this was
 * applied blindly, which is its own kind of wrong.
 */
export function loadedHold(
  stage: Stage, scene: Scene, index: number, existing: Track[],
): Track | null {
  const owned = existing.some(
    t => t.target === scene.id
      && (t.cam || Object.keys(t.keys ?? {}).some(k => k.startsWith('cam_'))))
  if (owned) return null

  const dur = scene.dur ?? 3
  const fps = stage.fps ?? 30
  const [W] = stage.size
  // what the reference rate asks for, against what the headroom can hide. a
  // scene longer than about five seconds drifts further than the margin
  // allows, so it drifts slower rather than revealing the edge
  const want = PX_PER_FRAME * fps * dur
  const margin = W * (1 - 1 / (1 + HEADROOM))
  const travel = Math.min(want, margin * 0.9)
  // alternate direction so a long film does not creep one way forever
  const sign = index % 2 === 0 ? 1 : -1
  const z = round(1 + HEADROOM)

  return {
    target: scene.id,
    keys: {
      cam_zoom: [{ t: 0, v: z }, { t: round(dur), v: z }],
      cam_x: [
        { t: 0, v: round(-sign * travel / 2) },
        { t: round(dur), v: round(sign * travel / 2) },
      ],
    },
  }
}

/**
 * Apply every device to a document's tracks, refusing collisions.
 *
 * A device that would write a property another track already owns is dropped
 * rather than appended, because appending is the silent failure: the format
 * keeps the later track and the earlier motion simply stops happening.
 */
export function applyDevices(stage: Stage, tracks: Track[]): Track[] {
  const out = [...tracks]
  stage.scenes.forEach((scene, i) => {
    const hold = loadedHold(stage, scene, i, out)
    if (hold) out.push(hold)
  })
  return out
}

const round = (n: number) => Math.round(n * 100) / 100
