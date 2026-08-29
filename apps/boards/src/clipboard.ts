import type { Anim, Doc, Node, Stage, Track } from './engine/types'
import type { Sel } from './doc'
import { freshId } from './ops'

/**
 * Copy and paste.
 *
 * A node without its motion is half a node, so the clipboard carries the
 * tracks that target it too. Ids are unique across the whole stage (a track
 * finds its node by id alone), so paste renames every node it brings in and
 * retargets its tracks to match.
 *
 * The clipboard is a module value rather than the system one: reading the
 * system clipboard needs a permission prompt, and a paste that stalls behind a
 * dialog is worse than one that does not survive a reload.
 */
export interface Clip {
  nodes: Node[]
  tracks: Track[]
  /** where the copies came from, so a paste into the same scene can offset */
  scene: string
}

let held: Clip | null = null

export const clipboard = {
  get(): Clip | null { return held },
  has(): boolean { return !!held?.nodes.length },
}

export function copyNodes(doc: Doc, sels: Sel[]): Clip | null {
  if (!sels.length) return null
  const nodes: Node[] = []
  const ids = new Set<string>()
  for (const s of sels) {
    const node = doc.stage.scenes.find(x => x.id === s.scene)?.nodes.find(n => n.id === s.id)
    if (node && !ids.has(node.id)) { nodes.push(structuredClone(node)); ids.add(node.id) }
  }
  if (!nodes.length) return null
  const tracks = (doc.anim.tracks ?? [])
    .filter(t => typeof t.target === 'string' && ids.has(t.target))
    .map(t => structuredClone(t))
  held = { nodes, tracks, scene: sels[0].scene }
  return held
}

/** nudge a paste into its own scene so the copy is not hidden under the original */
const OFFSET = 24

export function pasteNodes(
  stage: Stage, anim: Anim, sceneId: string, clip: Clip,
): { stage: Stage; anim: Anim; ids: string[] } | null {
  const scene = stage.scenes.find(s => s.id === sceneId)
  if (!scene) return null

  const rename = new Map<string, string>()
  // freshId reads the stage, so it has to see the names handed out so far
  let taken: Stage = stage
  const copies: Node[] = []
  const shift = clip.scene === sceneId ? OFFSET : 0

  for (const node of clip.nodes) {
    const id = freshId(taken, node.type === 'text' ? 'text' : node.type)
    rename.set(node.id, id)
    const copy: Node = { ...structuredClone(node), id }
    if (shift) {
      copy.x = (copy.x ?? 0) + shift
      copy.y = (copy.y ?? 0) + shift
    }
    copies.push(copy)
    taken = {
      ...taken,
      scenes: taken.scenes.map(s =>
        s.id === sceneId ? { ...s, nodes: [...s.nodes, copy] } : s),
    }
  }

  const tracks: Track[] = []
  for (const t of clip.tracks) {
    const target = rename.get(t.target as string)
    if (target) tracks.push({ ...structuredClone(t), target })
  }

  return {
    stage: taken,
    anim: tracks.length ? { ...anim, tracks: [...(anim.tracks ?? []), ...tracks] } : anim,
    ids: copies.map(n => n.id),
  }
}

/**
 * Styles, copied without geometry.
 *
 * Copying a style should not move or resize anything, so this carries only
 * what a node looks like: its paint, its type and its effects. `null` in a
 * field means the source had none, which has to be pasted as a removal rather
 * than skipped, or a glow would be impossible to clear by example.
 */
export interface Style {
  fill?: string | null
  color?: string | null
  radius?: number | null
  stroke?: number | null
  font?: Node['font'] | null
  blur?: number | null
  glow?: Node['glow'] | null
  gradient?: Node['gradient'] | null
  goo?: string | null
  streak?: Node['streak'] | null
}

const STYLE_FIELDS = [
  'fill', 'color', 'radius', 'stroke', 'font', 'blur', 'glow', 'gradient',
  'goo', 'streak',
] as const

let heldStyle: Style | null = null

export const styleClip = {
  get(): Style | null { return heldStyle },
  has(): boolean { return !!heldStyle },
}

export function copyStyle(doc: Doc, sel: Sel): Style | null {
  const node = doc.stage.scenes.find(s => s.id === sel.scene)?.nodes.find(n => n.id === sel.id)
  if (!node) return null
  const out: Style = {}
  for (const f of STYLE_FIELDS) {
    const v = (node as unknown as Record<string, unknown>)[f]
    ;(out as Record<string, unknown>)[f] = v === undefined ? null : structuredClone(v)
  }
  heldStyle = out
  return out
}

export function applyStyle(stage: Stage, sels: Sel[], style: Style): Stage {
  return {
    ...stage,
    scenes: stage.scenes.map(s => {
      const here = sels.filter(p => p.scene === s.id)
      if (!here.length) return s
      return {
        ...s,
        nodes: s.nodes.map(n => {
          if (!here.some(p => p.id === n.id)) return n
          const next: Node = { ...n }
          for (const f of STYLE_FIELDS) {
            const v = (style as Record<string, unknown>)[f]
            const bag = next as unknown as Record<string, unknown>
            if (v === null || v === undefined) delete bag[f]
            else bag[f] = structuredClone(v)
          }
          return next
        }),
      }
    }),
  }
}

/**
 * Motion, copied without the node.
 *
 * This is the smallest useful version of a motion preset: tune one entrance,
 * then put the same timing on the next four nodes. The tracks arrive retargeted,
 * replacing whatever the destination had, because the format allows only one
 * track per node per property and a second one would silently win.
 */
let heldMotion: Track[] | null = null

export const motionClip = {
  get(): Track[] | null { return heldMotion },
  has(): boolean { return !!heldMotion?.length },
}

export function copyMotion(doc: Doc, sel: Sel): Track[] | null {
  const tracks = (doc.anim.tracks ?? []).filter(t => t.target === sel.id)
  if (!tracks.length) return null
  heldMotion = structuredClone(tracks)
  return heldMotion
}

export function applyMotion(anim: Anim, sels: Sel[], tracks: Track[]): Anim {
  const targets = new Set(sels.map(s => s.id))
  const kept = (anim.tracks ?? []).filter(t => !targets.has(t.target as string))
  const added: Track[] = []
  for (const id of targets) {
    for (const t of tracks) added.push({ ...structuredClone(t), target: id })
  }
  return { ...anim, tracks: [...kept, ...added] }
}

export function clearMotion(anim: Anim, sels: Sel[]): Anim {
  const targets = new Set(sels.map(s => s.id))
  return { ...anim, tracks: (anim.tracks ?? []).filter(t => !targets.has(t.target as string)) }
}
