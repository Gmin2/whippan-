/** the three things the prompt bar can be asked to make */
export type AiKind = 'motion' | 'image' | 'vector' | 'screen'

export interface ModelOption {
  id: string
  label: string
  note?: string
}

export interface Capability {
  kind: AiKind
  /** false when the provider's key is missing, which the UI says out loud */
  ready: boolean
  provider: string
  models: ModelOption[]
  /** why it is not ready, shown in place of the prompt bar's button */
  reason?: string
}

export interface MotionRequest {
  prompt: string
  model?: string
  /** the nodes the motion is for, with enough shape for the model to judge */
  nodes: { id: string; type: string; text?: string; x?: number; y?: number; w?: number; h?: number }[]
  scene: { id: string; dur: number; index: number; total: number }
  /** the tracks those nodes already have, so the model edits rather than guesses */
  tracks: unknown[]
}

export interface MotionProposal {
  /** replacement tracks, one per node per property, ready to merge */
  tracks: Record<string, unknown>[]
  /** one line on what it did, shown above the accept button */
  note: string
}

export interface ImageRequest {
  prompt: string
  model?: string
  /** width:height, passed through to the provider */
  aspect?: string
}

export interface ScreenRequest {
  prompt: string
  model?: string
  /** canvas size, so the model can reason about the centre line and margins */
  size: [number, number]
  /** the film's one hue, taken from what it already uses */
  accent: string
  /** the block names and slots the client can actually materialise */
  blocks: { key: string; name: string; blurb: string; slots: string[] }[]
}

export interface ScreenProposal {
  note: string
  bg?: string
  /** block placements, not nodes; the block library owns the geometry */
  place: { block: string; x: number; y: number; opts: Record<string, unknown> }[]
}

export interface VectorRequest {
  prompt: string
  model?: string
  instructions?: string
}
