import type { NodeBox } from './measure'

/**
 * Corners only, clockwise from the top-left. Paper draws exactly four handles
 * and no edge midpoints — measured off its overlay canvas, four clusters of
 * white pixels and nothing on the edges. Edge resizing still works by dragging
 * the outline itself.
 */
export const HANDLES = ['nw', 'ne', 'se', 'sw'] as const
export type Handle = (typeof HANDLES)[number]

export interface ScreenRect { x: number; y: number; w: number; h: number }

export function handlePoints(r: ScreenRect): [number, number][] {
  return [
    [r.x, r.y], [r.x + r.w, r.y], [r.x + r.w, r.y + r.h], [r.x, r.y + r.h],
  ]
}

/** which handle is under a screen point, if any. the grab area is larger than
 *  the drawn square so small nodes stay resizable */
export function handleAt(r: ScreenRect, px: number, py: number, grab = 9): Handle | null {
  const pts = handlePoints(r)
  for (let i = 0; i < pts.length; i++) {
    const [hx, hy] = pts[i]
    if (Math.abs(px - hx) <= grab && Math.abs(py - hy) <= grab) return HANDLES[i]
  }
  return null
}

export const CURSORS: Record<Handle, string> = {
  nw: 'nwse-resize', se: 'nwse-resize',
  ne: 'nesw-resize', sw: 'nesw-resize',
}

/** just outside a corner is the rotate zone, the way paper does it */
export function rotateAt(r: ScreenRect, px: number, py: number, band = 16): Handle | null {
  const h = handleAt(r, px, py, band)
  if (!h) return null
  return handleAt(r, px, py, 9) ? null : h
}

export interface Geo { x: number; y: number; w: number; h: number }

/**
 * Apply a handle drag to a node's resting geometry. x,y is the centre, so an
 * edge drag moves the centre by half the size change — dragging the right edge
 * must not shift the left one.
 */
export function resize(
  start: Geo, handle: Handle, dx: number, dy: number,
  keepAspect: boolean, fromCentre = false,
): Geo {
  const east = handle.includes('e')
  const west = handle.includes('w')
  const south = handle.includes('s')
  const north = handle.includes('n')

  let w = start.w + (east ? dx : 0) - (west ? dx : 0)
  let h = start.h + (south ? dy : 0) - (north ? dy : 0)
  w = Math.max(1, w)
  h = Math.max(1, h)

  if (keepAspect && (east || west) && (north || south)) {
    const k = Math.max(w / start.w, h / start.h)
    w = start.w * k
    h = start.h * k
  }

  // alt resizes about the centre: the origin does not move and the size
  // changes by twice the drag
  if (fromCentre) {
    return {
      x: start.x,
      y: start.y,
      w: Math.max(1, start.w + 2 * (w - start.w)),
      h: Math.max(1, start.h + 2 * (h - start.h)),
    }
  }

  return {
    w,
    h,
    x: start.x + (east ? (w - start.w) / 2 : 0) - (west ? (w - start.w) / 2 : 0),
    y: start.y + (south ? (h - start.h) / 2 : 0) - (north ? (h - start.h) / 2 : 0),
  }
}

/** a text node has no w/h, so its corners scale the type instead */
export function scaleType(startSize: number, box: NodeBox, dx: number, dy: number): number {
  const base = Math.hypot(box.w, box.h)
  const now = Math.hypot(Math.max(4, box.w + dx), Math.max(4, box.h + dy))
  return Math.max(4, Math.round((startSize * now) / base))
}
