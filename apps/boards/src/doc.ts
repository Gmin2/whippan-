// boards views a real whippan document: every scene becomes an artboard, the
// scene note is its caption, and the frame drawn into it comes from the engine.
import { docDur, sceneStarts } from './engine'
import type { Doc, Glow, Gradient, Streak, Transition } from './engine/types'

export type LayerKind = 'frame' | 'text'

export interface Layer {
  id: string
  name: string
  kind: LayerKind
}

/** the fields of a scene boards can edit */
export interface ScenePatch {
  id?: string
  dur?: number
  note?: string
  bg?: string
  /** null removes the transition, which the engine reads as a hard cut */
  transition?: Transition | null
}

export interface Artboard {
  id: string
  /** the number printed above each board */
  label: string
  name: string
  index: number
  w: number
  h: number
  dur: number
  start: number
  note: string
  bg?: string
  /** how this scene enters from the previous one */
  transition?: Transition
  /** node ids shared with the previous scene: what magic move pairs */
  carried: string[]
}

export function artboards(doc: Doc): Artboard[] {
  const starts = sceneStarts(doc.stage)
  const [w, h] = doc.stage.size
  return doc.stage.scenes.map((s, i) => {
    const prevIds = new Set(doc.stage.scenes[i - 1]?.nodes.map(n => n.id) ?? [])
    return {
      id: s.id,
      label: String(i + 1),
      name: s.id,
      index: i,
      w,
      h,
      dur: s.dur ?? 3,
      start: starts[i],
      note: s.note ?? '',
      bg: s.bg,
      transition: s.transition,
      carried: s.nodes.filter(n => prevIds.has(n.id)).map(n => n.id),
    }
  })
}

export function layers(doc: Doc): Layer[] {
  return doc.stage.scenes.map((s, i) => ({
    id: s.id,
    name: `${i + 1}  ${s.id}`,
    kind: 'frame' as const,
  }))
}

/** a node the editor is pointing at */
export interface Sel {
  scene: string
  id: string
}

export interface NodePatch {
  x?: number
  y?: number
  w?: number
  h?: number
  radius?: number
  rot?: number
  fill?: string
  color?: string
  text?: string
  fontSize?: number
  fontFamily?: string
  fontWeight?: number
  /** written as a static key, which is where the engine reads opacity from */
  opacity?: number
  blur?: number | null
  glow?: Glow | null
  gradient?: Gradient | null
  goo?: string | null
  streak?: Streak | null
}

export function findNode(doc: Doc, sel: Sel | null) {
  if (!sel) return null
  const scene = doc.stage.scenes.find(s => s.id === sel.scene)
  const node = scene?.nodes.find(n => n.id === sel.id)
  return node && scene ? { scene, node } : null
}

/** scene rows with their nodes underneath, for the layer tree */
export function tree(doc: Doc) {
  return doc.stage.scenes.map((s, i) => {
    const row = (n: (typeof s.nodes)[number], depth: number) => ({
      id: n.id,
      kind: n.type,
      label: n.type === 'text' ? (n.text ?? n.id) : n.id,
      depth,
    })
    // members are listed under their container. groups do not nest, so this is
    // one level and needs no recursion
    const nodes: ReturnType<typeof row>[] = []
    for (const n of s.nodes) {
      if (n.group) continue
      nodes.push(row(n, 0))
      if (n.type === 'group') {
        for (const m of s.nodes) if (m.group === n.id) nodes.push(row(m, 1))
      }
    }
    return { scene: s.id, label: `${i + 1}  ${s.id}`, nodes }
  })
}

export const filmTitle = (doc: Doc) =>
  `${doc.entry.title} — ${docDur(doc.stage).toFixed(1)}s`
