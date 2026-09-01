import type { Scene, Stage, Track } from './engine/types'
import { LIVELY, motionMass } from './grammar'

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

/**
 * Measured: whole panels rack over 25-35 frames, single objects over ~7,
 * glyphs over 2-3. The element is at its final position from frame one and
 * only its focus changes.
 */
export const RACK = { panel: 30, object: 7, glyph: 3 }

/**
 * Which text is a headline, learned from the 248 nodes we already reveal this
 * way: they sit at a median 66px and 3 words against 30px and 1 word for plain
 * text, so the line falls between. Stagger is our own median and matches the
 * 3 frames per word the teardowns measured.
 */
export const WORD = { minPx: 40, minWords: 3, stagger: 0.09, dur: 0.3, rise: 20 }

export const DEVICES: Device[] = [
  {
    key: 'blur-resolve',
    name: 'Blur resolve',
    blurb: 'arrives already in place, heavily blurred, and racks to sharp.',
    films: 18,
    owns: ['blur'],
  },
  {
    key: 'word-build',
    name: 'Word build',
    blurb: 'a headline arrives a word at a time, about three frames apart.',
    films: 23,
    owns: ['reveal'],
  },
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
 * enough on its own: `mass` is the scene's motion mass from `grammar.ts`, and
 * the LIVELY line is the same one `checkCamera` uses to decide a scene needs
 * a camera at all. The two now agree.
 */
export function loadedHold(
  stage: Stage, scene: Scene, index: number, existing: Track[], mass: number,
): Track | null {
  const owned = existing.some(
    t => t.target === scene.id
      && (t.cam || Object.keys(t.keys ?? {}).some(k => k.startsWith('cam_'))))
  if (owned) return null
  // a scene that already carries itself does not want a push. applying this
  // blind took `x-anim` to 1.13 and `claude` to 1.06 against their references,
  // which is as wrong as sitting still
  if (mass >= LIVELY) return null

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
 * Bring a node into focus rather than into position.
 *
 * The reference set's second most common device, and it was unreachable until
 * `blur` was made to work on every node kind: for a long time only rects could
 * defocus, so no word, icon or screenshot could use it.
 *
 * It composes with an entrance rather than replacing one. `enter` presets write
 * `opacity`, `y` and `scale`; this writes only `blur`, so the two coexist and
 * the node fades, rises AND sharpens the way the references do. Returns null
 * when something already owns the node's blur.
 *
 * Kept but NOT applied by `applyDevices`. Measured on all 58 entrances of
 * `rezonant`: mae 17.38 to 17.37 of 255, energy 0.407 to 0.403, timing flat.
 * Blur smooths detail, so it lowers frame-to-frame difference over the very
 * frames it covers. See MOTION.md before wiring it back in.
 */
export function blurResolve(
  node: { id: string; type: string; w?: number; h?: number; font?: { size?: number } },
  stage: Stage, at: number, existing: Track[],
): Track | null {
  if (existing.some(t => t.target === node.id && 'blur' in (t.keys ?? {}))) return null

  const [W, H] = stage.size
  const k = W / 1920
  // how long the rack runs, and how far out of focus it starts, both scale with
  // how much of the frame the thing occupies
  const area = (node.w ?? (node.font?.size ?? 48) * 6) * (node.h ?? (node.font?.size ?? 48) * 1.4)
  const share = area / (W * H)
  const frames = share > 0.15 ? RACK.panel : share > 0.02 ? RACK.object : RACK.glyph
  const sigma = Math.round((share > 0.15 ? 18 : share > 0.02 ? 10 : 5) * k)
  const fps = stage.fps ?? 30

  return {
    target: node.id,
    at: round(at),
    keys: {
      blur: [
        { t: 0, v: sigma },
        { t: round(frames / fps), v: 0, ease: 'outCubic' },
      ],
    },
  }
}

/**
 * Build a headline one word at a time.
 *
 * 23 of 29 torn-down films do this and only 11% of our text nodes did. The
 * engine multiplies node opacity by the reveal's per-word opacity, so this
 * composes with an existing fade rather than replacing it.
 *
 * Returns null unless the node is large enough and long enough to read as a
 * headline, and null if anything already reveals it: the format keeps only
 * the last reveal on a node, so a second one would silently drop the first
 * track's other motion with it.
 */
export function wordBuild(
  node: { id: string; type: string; text?: string; font?: { size?: number } },
  stage: Stage, track: Track, existing: Track[],
): Track | null {
  if (typeof node.text !== 'string') return null
  if (existing.some(t => t.target === node.id && t.reveal)) return null

  const k = stage.size[0] / 1920
  if ((node.font?.size ?? 0) / k < WORD.minPx) return null
  if (node.text.trim().split(/\s+/).length < WORD.minWords) return null

  track.reveal = {
    unit: 'word',
    stagger: WORD.stagger,
    dur: WORD.dur,
    rise: Math.round(WORD.rise * k),
  }
  return track
}

/** what a device changed, so a caller can say it rather than swallow it */
export interface Note {
  rule: string
  detail: string
  fixed: boolean
}

/** two frames at 30fps: enough that frame zero has ink, not enough to lose the move */
export const OPEN_LEAD = 0.06

/**
 * Stop the film opening on an empty frame.
 *
 * Measured: at t=0 a generated film had ink 0.00, a literally blank frame,
 * because every entrance in the first scene starts at exactly zero with
 * opacity zero. That is the poster frame, and it was nothing. The corpus
 * authors around it by putting the first key slightly before zero, so the
 * film opens on something already arriving.
 *
 * Only the first scene, and only tracks that start at or before zero: a beat
 * deliberately held empty later in the film is an authoring choice.
 */
export function openWithInk(tracks: Track[], firstScene: string): Note[] {
  const notes: Note[] = []
  for (const t of tracks) {
    if (t.scene !== firstScene) continue
    if (!(t.enter || t.keys)) continue
    if ((t.at ?? 0) > 0) continue
    t.at = round(-OPEN_LEAD)
    notes.push({ rule: 'open with ink', detail: String(t.target), fixed: true })
  }
  return notes
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
  // the poster frame must not be empty
  const first = stage.scenes[0]?.id
  if (first) openWithInk(out, first)
  const mass = new Map(
    motionMass({ stage, anim: { tracks: out } }).map(m => [m.scene, m.mass]))
  stage.scenes.forEach((scene, i) => {
    const hold = loadedHold(stage, scene, i, out, mass.get(scene.id) ?? 0)
    if (hold) out.push(hold)
    // a headline that fades in should build instead
    for (const node of scene.nodes) {
      if (node.type === 'group') continue
      const enters = out.find(t => t.target === node.id && (t.enter || t.keys?.opacity))
      if (enters) wordBuild(node, stage, enters, out)
    }
  })
  return out
}

const round = (n: number) => Math.round(n * 100) / 100
