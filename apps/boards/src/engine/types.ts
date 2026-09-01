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
  /** linear only; degrees, 0 = left to right */
  angle?: number
  /** "linear" (default) or "radial" */
  kind?: string
  /** radial only: centre as a fraction of the box, reach against its half-diagonal */
  cx?: number
  cy?: number
  radius?: number
  stops: GradientStop[]
}

/** perlin laid over the body as its own blended layer */
export interface Noise {
  kind?: string
  freq?: number
  octaves?: number
  seed?: number
  opacity?: number
  blend?: string
}

/** a generative column meter: voice waveform, level, equaliser */
export interface Bars {
  count?: number
  gap?: number
  speed?: number
  floor?: number
  seed?: number
  taper?: boolean
}

/** a drifting field of specks: dust, stars, depth */
export interface Particles {
  count?: number
  size?: number
  speed?: number
  seed?: number
  depth?: number
  twinkle?: boolean
}

/** a directional reveal over one node, keyed through its `wipe` property */
export interface Wipe {
  dir?: string
  w?: number
  h?: number
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
  /** rect rims: the stroke colour, defaulting to the fill */
  stroke_color?: string
  noise?: Noise
  /** `bars` nodes */
  bars?: Bars
  /** `particles` nodes */
  particles?: Particles
  wipe?: Wipe
  opacity?: number
  /** path nodes: svg outline data, local to (x, y) */
  d?: string
  goo?: string
  streak?: Streak
  /** static property values live here; the overlay keys the same names */
  keys?: Record<string, Key[]>
  /** the id of a `group` node this belongs to; groups own members by id */
  group?: string
}

/** how a scene enters from the one before it */
export interface Transition {
  kind?: string
  dur?: number
  /** push/whip/wipe direction, or the colour for a dip */
  dir?: string
  ease?: unknown
  /** magic move: nodes sharing an id across the cut glide instead of fading */
  morph?: boolean
  morph_dur?: number
  morph_ease?: unknown
}

export interface Scene {
  id: string
  bg?: string
  dur?: number
  note?: string
  transition?: Transition
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

export interface Track {
  target?: string
  /** scene-local, shifts the whole track; key times are relative to it */
  at?: number
  loop?: boolean
  keys?: Record<string, Key[]>
  reveal?: Record<string, unknown>
  enter?: unknown
  state?: string
  cam?: unknown
  [k: string]: unknown
}

export interface Anim {
  tracks: Track[]
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
