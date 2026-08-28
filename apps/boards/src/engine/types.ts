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

export interface Font {
  family?: string
  size?: number
  weight?: number
}

export interface Glow {
  sigma?: number
  opacity?: number
  color?: string
  dx?: number
  dy?: number
}

export interface GradientStop { at: number; color: string }

export interface Gradient {
  angle?: number
  stops: GradientStop[]
}

export interface Streak {
  samples?: number
  window?: number
  gain?: number
}

export interface Key { t: number; v: number; ease?: unknown }

export interface Node {
  id: string
  type: string
  src?: string
  count?: number
  /** seq nodes play their folder's frames at this rate */
  fps?: number
  /** x,y is the CENTRE of the node, per the document contract */
  x?: number
  y?: number
  w?: number
  h?: number
  radius?: number
  rot?: number
  fill?: string
  color?: string
  text?: string
  font?: Font
  blur?: number
  glow?: Glow
  gradient?: Gradient
  stroke?: number
  /** path nodes: svg outline data, local to (x, y) */
  d?: string
  goo?: string
  streak?: Streak
  /** static property values live here; the overlay keys the same names */
  keys?: Record<string, Key[]>
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

export interface Asset {
  src: string
  bytes: number
}

export interface SfxEvent {
  t: number
  kind: string
  variant: number
  gain?: number
}
