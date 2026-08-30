import type { Node, Scene, Track } from './engine/types'

/**
 * The prompt bar's client. Every call goes to our own server, which holds the
 * provider keys; nothing here knows an API key exists.
 */
const API = import.meta.env.VITE_API_BASE ?? ''

export type AiKind = 'motion' | 'image' | 'vector' | 'screen'

export interface ModelOption {
  id: string
  label: string
  note?: string
}

export interface Capability {
  kind: AiKind
  ready: boolean
  provider: string
  models: ModelOption[]
  reason?: string
}

export interface MotionProposal {
  note: string
  tracks: Track[]
}

async function post<T>(kind: AiKind, body: unknown): Promise<T> {
  const res = await fetch(`${API}/api/ai/${kind}`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(body),
  })
  const out = await res.json().catch(() => ({})) as Record<string, unknown>
  if (!res.ok) throw new Error(typeof out.error === 'string' ? out.error : `ai ${res.status}`)
  return out as T
}

export async function capabilities(): Promise<Capability[]> {
  const res = await fetch(`${API}/api/ai`)
  if (!res.ok) throw new Error(`ai ${res.status}`)
  return await res.json() as Capability[]
}

/** what the model needs to see: the nodes themselves, not the whole document */
export function motionContext(scene: Scene, nodes: Node[], tracks: Track[], index: number, total: number) {
  return {
    scene: { id: scene.id, dur: scene.dur ?? 3, index, total },
    nodes: nodes.map(n => ({
      id: n.id, type: n.type,
      ...(n.text ? { text: n.text } : {}),
      ...(n.x != null ? { x: n.x } : {}), ...(n.y != null ? { y: n.y } : {}),
      ...(n.w != null ? { w: n.w } : {}), ...(n.h != null ? { h: n.h } : {}),
    })),
    tracks,
  }
}

export interface ScreenProposal {
  note: string
  bg?: string
  place: { block: string; x: number; y: number; opts: Record<string, unknown> }[]
}

export const askScreen = (body: unknown) => post<ScreenProposal>('screen', body)
export const askMotion = (body: unknown) => post<MotionProposal>('motion', body)
export const askImage = (body: unknown) => post<{ dataUrl: string; mime: string }>('image', body)
export const askVector = (body: unknown) => post<{ svg: string }>('vector', body)
