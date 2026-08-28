import type { NodeBox } from './measure'

export interface Guide {
  board: number
  axis: 'x' | 'y'
  /** position of the line on its axis, in document space */
  at: number
  /** the span the line is drawn across, on the other axis */
  from: number
  to: number
}

export interface Snapped {
  x: number
  y: number
  guides: Guide[]
}

/** how close, in document pixels, an edge has to be before it grabs */
const THRESHOLD = 6

interface Cand { at: number; from: number; to: number }

/**
 * Pull a moving box onto its neighbours. Edges and centres both snap, against
 * every sibling in the scene and against the artboard's own edges and centre,
 * which is what you actually reach for when centring a headline.
 *
 * `x` and `y` come in as the node's centre, since that is what the document
 * stores, and go back out the same way.
 */
export function snap(
  cx: number, cy: number, w: number, h: number,
  siblings: NodeBox[], canvas: [number, number], board: number,
  zoom: number,
): Snapped {
  const tol = THRESHOLD / Math.max(zoom, 0.01)
  const [cw, ch] = canvas

  const xs: Cand[] = [
    { at: 0, from: 0, to: ch }, { at: cw / 2, from: 0, to: ch }, { at: cw, from: 0, to: ch },
  ]
  const ys: Cand[] = [
    { at: 0, from: 0, to: cw }, { at: ch / 2, from: 0, to: cw }, { at: ch, from: 0, to: cw },
  ]
  for (const s of siblings) {
    xs.push({ at: s.x, from: s.y, to: s.y + s.h })
    xs.push({ at: s.x + s.w / 2, from: s.y, to: s.y + s.h })
    xs.push({ at: s.x + s.w, from: s.y, to: s.y + s.h })
    ys.push({ at: s.y, from: s.x, to: s.x + s.w })
    ys.push({ at: s.y + s.h / 2, from: s.x, to: s.x + s.w })
    ys.push({ at: s.y + s.h, from: s.x, to: s.x + s.w })
  }

  const guides: Guide[] = []
  let x = cx
  let y = cy

  // the three lines the moving box presents on each axis
  const pick = (edges: number[], cands: Cand[]) => {
    let best: { d: number; shift: number; c: Cand; edge: number } | null = null
    for (const edge of edges) {
      for (const c of cands) {
        const d = Math.abs(edge - c.at)
        if (d > tol) continue
        if (!best || d < best.d) best = { d, shift: c.at - edge, c, edge }
      }
    }
    return best
  }

  const hx = pick([cx - w / 2, cx, cx + w / 2], xs)
  if (hx) {
    x = cx + hx.shift
    guides.push({
      board, axis: 'x', at: hx.c.at,
      from: Math.min(hx.c.from, y - h / 2), to: Math.max(hx.c.to, y + h / 2),
    })
  }
  const hy = pick([cy - h / 2, cy, cy + h / 2], ys)
  if (hy) {
    y = cy + hy.shift
    guides.push({
      board, axis: 'y', at: hy.c.at,
      from: Math.min(hy.c.from, x - w / 2), to: Math.max(hy.c.to, x + w / 2),
    })
  }

  return { x, y, guides }
}
