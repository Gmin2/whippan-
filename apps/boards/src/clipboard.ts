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
