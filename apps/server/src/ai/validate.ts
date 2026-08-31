/**
 * The AUTHORING contract, checked and where possible repaired.
 *
 * A JSON schema can say a track has a `keys` object. It cannot say that two
 * tracks keying the same property on the same node will silently erase each
 * other, which is contract rule 3 and the single most expensive mistake a
 * model makes here: the film renders, nothing errors, and half the motion is
 * simply gone. Every rule below is from AUTHORING section 4, "violations fail
 * silently" — so nothing here can be left to the model's care.
 */

export interface Key { t: number; v: number; ease?: unknown }
export interface Track {
  target?: string
  at?: number
  keys?: Record<string, Key[]>
  [k: string]: unknown
}

export interface Problem {
  rule: string
  detail: string
  /** true when this was corrected rather than only reported */
  fixed: boolean
}

export interface Ctx {
  /** canvas size, to spot absolute coordinates written as offsets */
  size?: [number, number]
  /** scene duration, to spot global time written as scene-local */
  dur?: number
}

/**
 * Fold every track for one node into one track per property.
 *
 * The engine keeps the LAST track that keys a property, so two tracks means
 * the earlier motion vanishes. Rebasing the later keys onto the first track's
 * `at` keeps both, which is what the author meant in every case we have seen.
 */
function foldByTarget(tracks: Track[], problems: Problem[]): Track[] {
  const out: Track[] = []
  const first = new Map<string, Track>()

  for (const t of tracks) {
    const id = t.target
    if (typeof id !== 'string' || !t.keys) { out.push(t); continue }
    const held = first.get(id)
    if (!held) { first.set(id, t); out.push(t); continue }

    const shift = (t.at ?? 0) - (held.at ?? 0)
    held.keys ??= {}
    for (const [prop, keys] of Object.entries({ ...t.keys })) {
      delete t.keys[prop]
      const rebased = keys.map(k => ({ ...k, t: round(k.t + shift) }))
      if (!held.keys[prop]) {
        held.keys[prop] = rebased
        continue
      }
      // Both tracks key it. Merging is only safe when the two runs do not
      // overlap in time: interleaving them would invent intermediate states
      // the author never wrote, which is the same silent change we are here
      // to prevent. When they overlap, say so and leave it to a person.
      const mine = held.keys[prop]
      const clear = last(mine) <= rebased[0].t || last(rebased) <= mine[0].t
      if (clear) {
        held.keys[prop] = [...mine, ...rebased].sort((a, b) => a.t - b.t)
        problems.push({
          rule: 'one track per node per property',
          detail: `${id} had two tracks keying ${prop}; merged in time order, or the later would have erased the earlier`,
          fixed: true,
        })
      } else {
        // put it back: we are not folding this one
        t.keys[prop] = keys
        problems.push({
          rule: 'one track per node per property',
          detail: `${id} has two overlapping tracks keying ${prop}; the engine will keep only the later one and the earlier motion will not render`,
          fixed: false,
        })
        continue
      }
    }
    // anything we could not fold stays on its own track
    if (!Object.keys(t.keys).length) delete t.keys
    if (Object.keys(t).every(k => k === 'target' || k === 'at')) continue  // nothing left
    out.push(t)
  }
  return out
}

/** x and y keys are offsets from home; a value the size of the canvas is a coordinate */
function checkOffsets(tracks: Track[], problems: Problem[], size?: [number, number]) {
  if (!size) return
  const [W, H] = size
  for (const t of tracks) {
    for (const prop of ['x', 'y'] as const) {
      const keys = t.keys?.[prop]
      if (!keys) continue
      const limit = (prop === 'x' ? W : H) * 0.5
      const big = keys.filter(k => Math.abs(k.v) > limit)
      if (big.length) {
        problems.push({
          rule: 'x and y keys are offsets',
          detail: `${t.target} keys ${prop} at ${big.map(k => k.v).join(', ')}, which reads as a stage coordinate rather than an offset from home`,
          fixed: false,
        })
      }
    }
  }
}

/** every scene clock starts at 0, so a track cannot start after its scene ends */
function checkSceneLocal(tracks: Track[], problems: Problem[], dur?: number) {
  if (!dur) return
  for (const t of tracks) {
    if ((t.at ?? 0) > dur) {
      problems.push({
        rule: 'at is scene-local',
        detail: `${t.target} starts at ${t.at}s in a ${dur}s scene, which reads as global time`,
        fixed: false,
      })
    }
  }
}

export function checkTracks(tracks: Track[], ctx: Ctx = {}):
    { tracks: Track[]; problems: Problem[] } {
  const problems: Problem[] = []
  const folded = foldByTarget(tracks.map(t => ({ ...t })), problems)
  checkOffsets(folded, problems, ctx.size)
  checkSceneLocal(folded, problems, ctx.dur)
  return { tracks: folded, problems }
}

/** scene ids must be unique or a track lands in two places at once */
export function checkScenes(scenes: { id: string }[]): Problem[] {
  const seen = new Set<string>()
  const problems: Problem[] = []
  for (const sc of scenes) {
    if (seen.has(sc.id)) {
      problems.push({
        rule: 'scene ids unique',
        detail: `two scenes share the id ${sc.id}; a track for either would apply to both`,
        fixed: false,
      })
    }
    seen.add(sc.id)
  }
  return problems
}

const round = (n: number) => Math.round(n * 10000) / 10000
const last = (keys: Key[]) => keys[keys.length - 1].t
