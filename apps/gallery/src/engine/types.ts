// the shapes the gallery reads out of a whippan document. the engine owns
// the full schema — this types only the fields the ui touches, so adding a
// node property in rust never breaks the build here.

export type Group = 'films' | 'reproductions' | 'primitives'

export interface Entry {
  slug: string
  title: string
  dur: number
  size: [number, number]
  group: Group
  stage?: string
  anim?: string
  /** time in seconds to cut the poster frame at, default 40% through */
  poster?: number
}

export interface Node {
  id: string
  type: string
  src?: string
  count?: number
}

export interface Scene {
  id: string
  bg?: string
  dur?: number
  note?: string
  nodes: Node[]
}

export interface Audio {
  src?: string
  gain?: number
  start?: number
}

export interface Stage {
  fps: number
  size: [number, number]
  audio?: Audio
  scenes: Scene[]
}

export interface Anim {
  tracks: unknown[]
}

export interface Doc {
  entry: Entry
  stage: Stage
  anim: Anim
  images: Map<string, unknown>
}

export interface SfxEvent {
  t: number
  kind: string
  variant: number
  gain?: number
}
