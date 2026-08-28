// boards views a real whippan document: every scene becomes an artboard, the
// scene note is its caption, and the frame drawn into it comes from the engine.
import { docDur, sceneStarts } from './engine'
import type { Doc, Glow, Gradient, Transition } from './engine/types'

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
  /** node ids this scene shares with the previous one, which is what magic
   *  move pairs across the cut */
  carried: string[]
}

export function artboards(doc: Doc): Artboard[] {
  const starts = sceneStarts(doc.stage)
  const [w, h] = doc.stage.size
  return doc.stage.scenes.map((s, i) => {
    const prev = doc.stage.scenes[i - 1]
    const prevIds = new Set(prev?.nodes.map(n => n.id) ?? [])
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
}

export function findNode(doc: Doc, sel: Sel | null) {
  if (!sel) return null
  const scene = doc.stage.scenes.find(s => s.id === sel.scene)
  const node = scene?.nodes.find(n => n.id === sel.id)
  return node && scene ? { scene, node } : null
}

/** scene rows with their nodes underneath, for the layer tree */
export function tree(doc: Doc) {
  return doc.stage.scenes.map((s, i) => ({
    scene: s.id,
    label: `${i + 1}  ${s.id}`,
    nodes: s.nodes.map(n => ({
      id: n.id,
      kind: n.type,
      label: n.type === 'text' ? (n.text ?? n.id) : n.id,
    })),
  }))
}

export const filmTitle = (doc: Doc) =>
  `${doc.entry.title} — ${docDur(doc.stage).toFixed(1)}s`
