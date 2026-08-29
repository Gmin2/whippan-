import type { Anim, Doc, Key } from './engine/types'

/**
 * Reading the animation overlay as lanes.
 *
 * The contract from AUTHORING: `at` shifts a whole track and defaults to 0, key
 * times are relative to `at`, and a track applies to every scene containing its
 * target id. So a lane is scene-local, and the same track can legitimately
 * appear under several scenes.
 */

export interface Span {
  prop: string
  /** scene-local seconds */
  t0: number
  t1: number
  keys: Key[]
  kind: 'keys' | 'reveal' | 'state' | 'enter' | 'cam'
  looped: boolean
}

export interface Lane {
  /** node id, or the scene id for camera tracks */
  target: string
  kind: string
  spans: Span[]
}

interface RawTrack {
  target?: string
  at?: number
  loop?: boolean
  keys?: Record<string, Key[]>
  reveal?: { unit?: string; stagger?: number; dur?: number }
  enter?: unknown
  state?: string
  cam?: unknown
}

const tracksOf = (anim: Anim): RawTrack[] => (anim.tracks as RawTrack[]) ?? []

function spansOfTrack(tr: RawTrack): Span[] {
  const at = tr.at ?? 0
  const out: Span[] = []
  const looped = !!tr.loop

  for (const [prop, keys] of Object.entries(tr.keys ?? {})) {
    if (!keys.length) continue
    const ts = keys.map(k => k.t)
    out.push({
      prop,
      t0: at + Math.min(...ts),
      t1: at + Math.max(...ts),
      keys,
      kind: 'keys',
      looped,
    })
  }

  if (tr.reveal) {
    // a reveal has no keys of its own: its length is the stagger across the
    // pieces plus one piece's duration, which we cannot know without shaping
    // the text, so this is the floor rather than the true end
    const r = tr.reveal
    const dur = (r.dur ?? 0.27) + (r.stagger ?? 0.05) * 4
    out.push({ prop: `reveal:${r.unit ?? 'word'}`, t0: at, t1: at + dur, keys: [], kind: 'reveal', looped })
  }
  if (tr.enter) {
    out.push({ prop: 'enter', t0: at, t1: at + 0.4, keys: [], kind: 'enter', looped })
  }
  if (tr.state) {
    out.push({ prop: `state:${tr.state}`, t0: at, t1: at + 0.12, keys: [], kind: 'state', looped })
  }
  if (tr.cam) {
    out.push({ prop: 'camera', t0: at, t1: at + 1, keys: [], kind: 'cam', looped })
  }
  return out
}

/** every lane in one scene, in the scene's own node order */
export function lanesOf(doc: Doc, sceneId: string): Lane[] {
  const scene = doc.stage.scenes.find(s => s.id === sceneId)
  if (!scene) return []
  const tracks = tracksOf(doc.anim)

  const lanes: Lane[] = []
  for (const node of scene.nodes) {
    const spans = tracks
      .filter(t => t.target === node.id)
      .flatMap(spansOfTrack)
      .sort((a, b) => a.t0 - b.t0)
    lanes.push({ target: node.id, kind: node.type, spans })
  }

  // camera tracks target the scene itself
  const cam = tracks.filter(t => t.target === sceneId).flatMap(spansOfTrack)
  if (cam.length) lanes.unshift({ target: sceneId, kind: 'camera', spans: cam })

  return lanes
}

/** which scene a global film time falls in, and how far into it */
export function sceneAt(doc: Doc, t: number): { index: number; id: string; local: number } {
  let acc = 0
  const scenes = doc.stage.scenes
  for (let i = 0; i < scenes.length; i++) {
    const dur = scenes[i].dur ?? 3
    if (t < acc + dur || i === scenes.length - 1) {
      return { index: i, id: scenes[i].id, local: Math.max(0, t - acc) }
    }
    acc += dur
  }
  return { index: 0, id: scenes[0]?.id ?? '', local: 0 }
}

/** colour a span by what it does, so a lane reads at a glance */
export function spanColor(kind: Span['kind']): string {
  if (kind === 'reveal') return '#e8671f'
  if (kind === 'state') return '#79c979'
  if (kind === 'cam') return '#9F50D3'
  if (kind === 'enter') return '#5e92f4'
  return '#5e92f4'
}
