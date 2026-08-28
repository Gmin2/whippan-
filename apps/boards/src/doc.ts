// boards views a real whippan document: every scene becomes an artboard, the
// scene note is its caption, and the frame drawn into it comes from the engine.
import { docDur, sceneStarts } from './engine'
import type { Doc } from './engine/types'

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
}

export function artboards(doc: Doc): Artboard[] {
  const starts = sceneStarts(doc.stage)
  const [w, h] = doc.stage.size
  return doc.stage.scenes.map((s, i) => ({
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
  }))
}

export function layers(doc: Doc): Layer[] {
  return doc.stage.scenes.map((s, i) => ({
    id: s.id,
    name: `${i + 1}  ${s.id}`,
    kind: 'frame' as const,
  }))
}

export const filmTitle = (doc: Doc) =>
  `${doc.entry.title} — ${docDur(doc.stage).toFixed(1)}s`
